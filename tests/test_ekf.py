import sys
import os
import numpy as np

# Hack para encontrar a pasta src
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from src.battery_model import BatteryModel
from src.ekf import EKF
from src.utils import plot_results, load_drive_cycle # <--- Importando nossas ferramentas!

# 1. Configuração e Carga de Dados
DATA_FILE = os.path.join(project_root, 'data', 'drive_cycle.csv')

try:
    time_data, current_data = load_drive_cycle(DATA_FILE)
except Exception as e:
    print(e)
    sys.exit(1)

# Detecta o passo de tempo automaticamente pelo CSV
dt = time_data[1] - time_data[0]
steps = len(time_data)

# 2. Inicialização dos Modelos
real_battery = BatteryModel(Q_Ah=3.0)
ekf = EKF(R0=0.01, R1=0.005, C1=3000, Q_Ah=3.0, dt=dt)

# Cenário de Teste: Erro de Inicialização
real_battery.soc = 0.8  # Bateria real tem 80%
ekf.x[0] = 0.5          # EKF "acha" que tem 50%

# Listas para guardar histórico
est_soc = []
true_soc = []
voltage_meas = []

# 3. Loop de Simulação
print("🔄 Rodando teste de EKF com dados do CSV...")
for k in range(steps):
    current = current_data[k]
    
    # A. Mundo Físico (Bateria Real)
    v = real_battery.update(current, dt)
    v_noisy = v + np.random.normal(0, 0.01) # Adiciona ruído de sensor
    
    # B. Algoritmo (EKF)
    ekf.predict(current)
    s_est = ekf.update(v_noisy, current)
    
    # C. Armazenamento
    est_soc.append(s_est)
    true_soc.append(real_battery.soc)
    voltage_meas.append(v_noisy)

# 4. Resultados (Usando o Utils)
output_path = os.path.join(project_root, 'images', 'teste_ekf_padronizado.png')
plot_results(time_data, true_soc, est_soc, voltage_meas, current_data, save_path=output_path)