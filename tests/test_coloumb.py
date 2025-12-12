import sys
import os
import numpy as np
import matplotlib.pyplot as plt

# Hack para encontrar a pasta src
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from src.battery_model import BatteryModel
from src.ekf import EKF
from src.utils import load_drive_cycle

# 1. Configuração
DATA_FILE = os.path.join(project_root, 'data', 'drive_cycle.csv')

# Carrega dados
try:
    time_data, current_data = load_drive_cycle(DATA_FILE)
except:
    print("Erro: Gere os dados com 'python generate_data.py' primeiro.")
    sys.exit(1)

dt = time_data[1] - time_data[0]
steps = len(time_data)

# Parâmetros da Bateria
Q_Ah = 3.0
Q_total = Q_Ah * 3600 # Capacidade em Coulombs

# 2. Inicialização
real_battery = BatteryModel(Q_Ah=Q_Ah)
ekf = EKF(R0=0.01, R1=0.005, C1=3000, Q_Ah=Q_Ah, dt=dt)

# --- O CENÁRIO DE ERRO ---
real_battery.soc = 0.80  # Real: 80%
initial_guess = 0.50     # Chute: 50%

ekf.x[0] = initial_guess # EKF começa errado
soc_cc = initial_guess   # Coulomb Counting começa errado

# Listas
history_real = []
history_ekf = []
history_cc = []

print("⚔️  Rodando Batalha: EKF vs Coulomb Counting...")

# 3. Loop
for k in range(steps):
    current = current_data[k]
    
    # A. Bateria Real (Gera Tensão)
    v = real_battery.update(current, dt)
    v_noisy = v + np.random.normal(0, 0.01) # Ruído
    
    # B. Método 1: Coulomb Counting (Simples Integração)
    # SoC_new = SoC_old - (I * dt / Q)
    soc_cc = soc_cc - (current * dt / Q_total)
    
    # C. Método 2: EKF (Fusão de Sensores)
    ekf.predict(current)
    ekf.update(v_noisy, current)
    
    # Salvar
    history_real.append(real_battery.soc)
    history_cc.append(soc_cc)
    history_ekf.append(ekf.x[0,0])

# 4. Plotagem Focada
plt.figure(figsize=(10, 6))

plt.plot(time_data, history_real, 'g-', linewidth=2, label='Real SoC (Referência)')
plt.plot(time_data, history_cc, 'b:', linewidth=2, label='Coulomb Counting (Sem correção)')
plt.plot(time_data, history_ekf, 'r--', linewidth=2, label='EKF (Com correção)')

plt.title('Por que usar EKF? Comparação de Robustez')
plt.ylabel('SoC (0-1)')
plt.xlabel('Tempo (s)')
plt.legend()
plt.grid(True, alpha=0.3)

# Salvar
output_file = os.path.join(project_root, 'images', 'ekf_vs_cc.png')
plt.savefig(output_file, dpi=300)
print(f"✅ Gráfico comparativo salvo em: {output_file}")