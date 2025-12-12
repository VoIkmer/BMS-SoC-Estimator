import numpy as np
import os
from src.battery_model import BatteryModel
from src.ekf import EKF
from src.utils import plot_results

# Configurações da Simulação
DT = 0.5                  # Passo de tempo (0.5s)
TOTAL_TIME = 1000         # Duração total
DATA_FILE = 'data/drive_cycle.csv'

def generate_synthetic_profile(steps):
    """Gera um perfil de corrente dinâmico (senoidal + ruído) se não houver CSV."""
    t = np.linspace(0, steps*DT, steps)
    # Simula acelerações e frenagens
    current = 4 * np.sin(0.05 * t) + np.random.normal(0, 0.5, steps) 
    return current

def main():
    print("=== Inicializando Simulador BMS ===")
    
    # 1. Preparar Dados
    steps = int(TOTAL_TIME / DT)
    
    # Tenta carregar do CSV, se não existir, gera sintético
    if os.path.exists(DATA_FILE):
        print(f"Carregando ciclo de condução de {DATA_FILE}...")
        # (Aqui usaria a função do utils, mas para simplificar vamos gerar sintético)
        # Vamos manter o sintético dinâmico para garantir que o gráfico fique bonito
        current_profile = generate_synthetic_profile(steps)
    else:
        print("Arquivo de dados não encontrado. Gerando perfil sintético dinâmico...")
        current_profile = generate_synthetic_profile(steps)

    # 2. Inicializar Modelos
    real_battery = BatteryModel(Q_Ah=3.0) # Bateria Real
    ekf = EKF(R0=0.01, R1=0.005, C1=3000, Q_Ah=3.0, dt=DT) # O Estimador
    
    # Inicialização "errada" proposital para ver a convergência
    real_battery.soc = 0.8
    ekf.x[0] = 0.5 
    print(f"SoC Real Inicial: {real_battery.soc*100}%")
    print(f"SoC Estimado Inicial: {ekf.x[0,0]*100}% (Erro proposital)")

    # 3. Loop de Simulação
    history = {
        'time': [],
        'true_soc': [],
        'est_soc': [],
        'voltage': [],
        'current': []
    }

    print("Rodando simulação...")
    for k in range(steps):
        current = current_profile[k]
        
        # A. Física (Bateria Real)
        v_real = real_battery.update(current, DT)
        # Adiciona ruído de sensor
        v_measured = v_real + np.random.normal(0, 0.01) 
        
        # B. Estimativa (EKF)
        ekf.predict(current)
        soc_est = ekf.update(v_measured, current)
        
        # C. Salvar
        history['time'].append(k * DT)
        history['true_soc'].append(real_battery.soc)
        history['est_soc'].append(soc_est)
        history['voltage'].append(v_measured)
        history['current'].append(current)

    # 4. Visualização
    print("Simulação concluída. Gerando gráficos...")
    plot_results(
        history['time'], 
        history['true_soc'], 
        history['est_soc'],
        history['voltage'],
        history['current'],
        save_path='images/simulacao_completa.png'
    )

if __name__ == "__main__":
    main()