import sys
import os

# --- CORREÇÃO DO CAMINHO ---
# Pega o caminho absoluto da pasta atual e sobe um nível ('..')
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# Adiciona a raiz do projeto ao sys.path para o Python achar a pasta 'src'
sys.path.append(project_root)
# ---------------------------

import numpy as np
import matplotlib.pyplot as plt
from src.battery_model import BatteryModel

# 1. Configuração
battery = BatteryModel()
dt = 1.0              # Passo de 1 segundo
total_time = 3600     # 1 hora de simulação
steps = int(total_time / dt)

# Arrays para guardar os dados para o gráfico
time_history = []
voltage_history = []
soc_history = []
current_history = []

# 2. Criar um perfil de corrente (Ex: Um carro acelerando e parando)
# Vamos descarregar a 2.5A (1C) constante para teste simples
current_profile = np.ones(steps) * 2.5 

# Parando o carro
current_profile[1800:] = 0

# 3. Loop de Simulação
print("Iniciando simulação...")
for k in range(steps):
    current = current_profile[k]
    
    # Roda a física da bateria
    voltage = battery.update(current, dt)
    
    # Salva dados
    time_history.append(k * dt)
    voltage_history.append(voltage)
    soc_history.append(battery.soc)
    current_history.append(current)

# 4. Plotagem e Salvamento
fig, ax1 = plt.subplots(figsize=(10, 6))

ax1.set_xlabel('Tempo (s)')
ax1.set_ylabel('Tensão (V)', color='tab:blue')
ax1.plot(time_history, voltage_history, color='tab:blue', label='Tensão')
ax1.tick_params(axis='y', labelcolor='tab:blue')
ax1.grid(True, alpha=0.3)

ax2 = ax1.twinx()  # Eixo Y secundário para o SoC
ax2.set_ylabel('SoC (0-1)', color='tab:orange')
ax2.plot(time_history, soc_history, color='tab:orange', linestyle='--', label='SoC Real')
ax2.tick_params(axis='y', labelcolor='tab:orange')

plt.title('Simulação de Descarga da Bateria (Dados Sintéticos)')

# --- MUDANÇA AQUI: Em vez de show(), usamos savefig() ---
output_file = 'simulacao_bateria.png'
plt.savefig(output_file, dpi=300)
print(f"Gráfico salvo com sucesso em: {output_file}")
# plt.show() # Comentamos essa linha para não travar