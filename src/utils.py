import pandas as pd
import matplotlib.pyplot as plt
import os

def load_drive_cycle(filepath):
    """
    Carrega o perfil de condução (tempo e corrente) de um arquivo CSV.
    Retorna: (time_array, current_array)
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Arquivo não encontrado: {filepath}. Rode 'python generate_data.py' primeiro.")
    
    df = pd.read_csv(filepath)
    return df['time'].values, df['current'].values

def plot_results(time, true_soc, est_soc, voltage, current, save_path=None):
    """
    Gera e salva/mostra o dashboard com 3 gráficos: Tensão, Corrente e SoC.
    """
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 12), sharex=True)
    
    # Gráfico 1: Tensão
    ax1.plot(time, voltage, color='tab:blue', label='Tensão Medida (V)')
    ax1.set_ylabel('Tensão [V]')
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper right')
    ax1.set_title('BMS SoC Estimation Results')

    # Gráfico 2: Corrente
    ax2.plot(time, current, color='tab:gray', label='Corrente (A)')
    ax2.set_ylabel('Corrente [A]')
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='upper right')

    # Gráfico 3: SoC
    ax3.plot(time, true_soc, color='tab:green', linewidth=2, label='SoC Real')
    ax3.plot(time, est_soc, color='tab:red', linestyle='--', linewidth=2, label='SoC Estimado (EKF)')
    ax3.set_ylabel('SoC [0-1]')
    ax3.set_xlabel('Tempo [s]')
    ax3.grid(True, alpha=0.3)
    ax3.legend(loc='upper right')

    plt.tight_layout()
    
    if save_path:
        # Garante que a pasta existe antes de salvar
        directory = os.path.dirname(save_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            
        plt.savefig(save_path, dpi=300)
        print(f"📊 Gráfico salvo em: {save_path}")
        plt.close() # Fecha a figura da memória
    else:
        plt.show()