import numpy as np

class EKF:
    """
    Extended Kalman Filter para estimativa de SoC.
    Estado (x): [SoC, V_c1] (Vetor 2x1)
    Entrada (u): [Corrente]
    Saída (z): [Tensão Terminal]
    """
    def __init__(self, R0, R1, C1, Q_Ah, dt):
        self.R0 = R0
        self.R1 = R1
        self.C1 = C1
        self.Q_capacity = Q_Ah * 3600 # Em Coulombs
        self.dt = dt

        # Estado Inicial [SoC, Vc1]
        # Começamos chutando que a bateria está 100% (1.0) e relaxada (0.0)
        self.x = np.array([[1.0], 
                           [0.0]])

        # Matriz de Covariância do Estado (P)
        # Indica o quão "incertos" estamos sobre nosso chute inicial.
        # Valores altos = alta incerteza.
        self.P = np.diag([0.1, 0.1])

        # Matriz de Ruído do Processo (Q)
        # O quanto confiamos no nosso modelo matemático?
        # Valores baixos = confiamos muito no modelo.
        self.Q = np.diag([1e-5, 1e-4])

        # Matriz de Ruído da Medição (R)
        # O quanto confiamos no voltímetro?
        # Se o sensor for ruim, aumente este valor.
        self.R = np.array([[0.1]]) # 0.1 Volts de variância

    def _get_ocv_derivative(self, soc):
        """
        Calcula a derivada d(OCV)/d(SoC).
        Isso é crucial para o EKF saber o quão sensível a tensão é em relação à carga.
        Aproximação baseada na curva linear que usamos no battery_model.py
        """
        # Derivada da parte linear (3.0 + 1.2*soc) é 1.2
        d_ocv = 1.2 
        
        # Adicionando derivadas das partes exponenciais (simplificado para o projeto)
        if soc > 0.9:
            d_ocv += 2.0 # A curva fica íngreme no final da carga
        if soc < 0.1:
            d_ocv += 2.0 # A curva fica íngreme no final da descarga
            
        return d_ocv

    def predict(self, current):
        """
        Passo 1: Predição (Time Update)
        Estima o estado futuro baseado apenas no modelo físico.
        """
        # --- A. Predição do Estado (x_k|k-1) ---
        # SoC_new = SoC_old - (I * dt / Q)
        self.x[0] = self.x[0] - (current * self.dt / self.Q_capacity)
        
        # Vc1_new = Vc1_old * e^(-dt/RC) + R * I * (1 - e^(-dt/RC))
        tau = self.R1 * self.C1
        alpha = np.exp(-self.dt / tau)
        self.x[1] = self.x[1] * alpha + self.R1 * current * (1 - alpha)

        # --- B. Predição da Covariância (P_k|k-1) ---
        # Jacobiana do Processo (A) - Linearização das equações de estado
        # A = [1, 0]
        #     [0, alpha]
        A = np.array([[1.0, 0.0],
                      [0.0, alpha]])
        
        self.P = A @ self.P @ A.T + self.Q

    def update(self, voltage_measured, current):
        """
        Passo 2: Correção (Measurement Update)
        Corrige a estimativa comparando a tensão prevista com a medida.
        """
        # --- C. Calcular Ganho de Kalman (K) ---
        # Precisamos da Jacobiana da Medição (H)
        # V_term = OCV(SoC) - V_c1 - I*R0
        # dV/dSoC = dOCV/dSoC
        # dV/dVc1 = -1
        
        d_ocv = self._get_ocv_derivative(self.x[0,0])
        H = np.array([[d_ocv, -1.0]]) # Matriz 1x2

        # S = H*P*H' + R (Inovação da covariância)
        S = H @ self.P @ H.T + self.R
        
        # K = P*H' * inv(S)
        K = self.P @ H.T @ np.linalg.inv(S)

        # --- D. Atualizar Estado (x_k|k) ---
        # Tensão esperada pelo modelo (z_hat)
        # Precisamos da OCV atual (vamos reusar a lógica simplificada ou importar do modelo)
        # Para simplificar aqui no EKF, vou replicar a eq simples:
        # (Idealmente, isso viria de uma tabela compartilhada)
        soc_est = self.x[0,0]
        ocv_est = 3.0 + (1.2 * soc_est) # Versão simplificada da OCV
        if soc_est > 0.9: ocv_est += 0.15 * (soc_est - 0.9)
        if soc_est < 0.1: ocv_est -= 0.15 * (0.1 - soc_est)
        
        z_hat = ocv_est - self.x[1,0] - (current * self.R0)
        
        # Inovação (Erro) = Medido - Estimado
        y = voltage_measured - z_hat
        
        # x_new = x_pred + K * y
        self.x = self.x + K * y

        # --- E. Atualizar Covariância (P_k|k) ---
        # P_new = (I - K*H) * P_pred
        I = np.eye(2)
        self.P = (I - K @ H) @ self.P

        return self.x[0,0] # Retorna o SoC estimado