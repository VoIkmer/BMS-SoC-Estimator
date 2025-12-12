import numpy as np

class BatteryModel:
    """
    Simula uma bateria de Li-Ion usando o modelo de Circuito Equivalente de Thevenin (1ª Ordem).
    Inclui simulação de OCV (Open Circuit Voltage) não-linear.
    """
    
    def __init__(self, R0=0.01, R1=0.005, C1=3000, Q_Ah=2.5):
        """
        Inicializa os parâmetros da bateria.
        
        Args:
            R0 (float): Resistência Ohmica interna (Ohms).
            R1 (float): Resistência de polarização (Ohms).
            C1 (float): Capacitância de polarização (Farads).
            Q_Ah (float): Capacidade total da bateria em Ampere-hora.
        """
        self.R0 = R0
        self.R1 = R1
        self.C1 = C1
        self.Q_capacity = Q_Ah * 3600  # Convertendo Ah para Coulombs (As)
        
        # Estados Iniciais
        self.soc = 1.0        # Começa 100% cheia (0.0 a 1.0)
        self.v_c1 = 0.0       # Tensão no capacitor começa em 0
        
    def _get_ocv(self, soc):
        """
        Retorna a Tensão de Circuito Aberto (OCV) baseada no SoC.
        Aproximei uma curva típica de Li-Ion usando um polinômio.
        """
        # Essa equação gera aquela curva em "S" característica das baterias de Lítio
        # Valores aproximados para uma célula NMC (Nominal 3.7V)
        ocv = 3.0 + (soc * 1.2)  # Base linear
        
        # Adicionando não-linearidades nas pontas (bateria cheia e vazia)
        if soc > 0.9:
            ocv += 0.15 * (soc - 0.9)  # Pico exponencial no final da carga
        if soc < 0.1:
            ocv -= 0.15 * (0.1 - soc)  # Queda abrupta no final da descarga
            
        return ocv

    def update(self, current, dt):
        """
        Atualiza o estado da bateria dado uma corrente e um intervalo de tempo.
        
        Args:
            current (float): Corrente em Amperes (Positivo = Descarga, Negativo = Carga).
            dt (float): Passo de tempo em segundos.
            
        Returns:
            float: Tensão nos terminais (V) simulada.
        """
        # 1. Atualizar SoC (Integração da Corrente)
        # Se current > 0 (descarga), SoC diminui.
        self.soc = self.soc - (current * dt) / self.Q_capacity
        
        # Trava de segurança para simulação física (0% a 100%)
        self.soc = np.clip(self.soc, 0.0, 1.0)

        # 2. Atualizar Tensão no Capacitor (Dinâmica RC discretizada)
        # Constante de tempo tau = R1 * C1
        tau = self.R1 * self.C1
        exp_factor = np.exp(-dt / tau)
        
        self.v_c1 = (self.v_c1 * exp_factor) + (self.R1 * current * (1 - exp_factor))

        # 3. Calcular Tensão de Saída (Equação de Kirchoff)
        v_ocv = self._get_ocv(self.soc)
        v_terminal = v_ocv - self.v_c1 - (current * self.R0)
        
        return v_terminal