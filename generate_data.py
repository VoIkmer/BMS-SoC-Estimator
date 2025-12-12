import numpy as np
import pandas as pd
import os

# Configurações do Ciclo
DT = 0.5
TOTAL_TIME = 2000 # 2000 segundos
steps = int(TOTAL_TIME / DT)
t = np.linspace(0, TOTAL_TIME, steps)

# 1. Criar perfil de corrente "Cidade"
# Senoide lenta (topografia) + Ruído (vibração)
current = 4 * np.sin(0.01 * t) + np.random.normal(0, 0.2, steps)

# Adicionar eventos de alta demanda (Acelerações bruscas)
# A cada 200s, dá um pico de 15A
for i in range(0, steps, 400):
    current[i:i+20] = 15.0

# Adicionar paradas (Semáforos - Corrente Zero)
current[1000:1200] = 0 
current[1500:1600] = 0

# 2. Salvar em CSV
df = pd.DataFrame({
    'time': t, 
    'current': current
})

if not os.path.exists('data'):
    os.makedirs('data')

file_path = 'data/drive_cycle.csv'
df.to_csv(file_path, index=False)
print(f"✅ Arquivo gerado com sucesso: {file_path}")
print(f"   Duração: {TOTAL_TIME}s | Passos: {steps}")