# scripts/ver_loss_insana.py
import torch
import os
import matplotlib.pyplot as plt
from pathlib import Path

def ver_loss_insana():
    """Visualiza a curva de aprendizado da IA INSANA (dos arquivos .pt)"""
    
    pt_path = Path("data/mentes_pytorch")
    arquivos = sorted(pt_path.glob("*.pt"))
    
    if not arquivos:
        print("Nenhum arquivo .pt encontrado!")
        return
    
    # Mostra todas as IAs disponíveis
    print("IAs INSANA disponíveis:")
    for i, arq in enumerate(arquivos):
        dados = torch.load(arq, map_location='cpu')
        geracao = dados.get('geracao', 0)
        print(f"  {i+1}. {arq.name} (geração {geracao})")
    
    # Escolhe qual IA analisar
    escolha = input("\nDigite o número da IA para analisar (ou Enter para a mais recente): ")
    
    if escolha:
        idx = int(escolha) - 1
        arquivo = arquivos[idx]
    else:
        arquivo = max(arquivos, key=lambda x: x.stat().st_mtime)  # Mais recente
    
    print(f"\n📊 Analisando {arquivo.name}...")
    
    dados = torch.load(arquivo, map_location='cpu')
    historico_loss = dados.get('historico_loss', [])
    
    if not historico_loss:
        print("❌ Nenhum histórico de loss encontrado")
        return
    
    # Prepara dados para o gráfico
    timestamps = list(range(len(historico_loss)))
    losses = historico_loss
    
    plt.figure(figsize=(14, 7))
    
    # Plot do loss
    plt.subplot(1, 2, 1)
    plt.plot(timestamps, losses, 'b-', alpha=0.5, linewidth=0.5)
    plt.plot(timestamps, losses, 'b.', markersize=1)
    plt.xlabel('Passos de Aprendizado (Geração)')
    plt.ylabel('Loss (Erro)')
    plt.title(f'Curva de Aprendizado - {arquivo.name}')
    plt.grid(True, alpha=0.3)
    
    # Média móvel
    window = min(10, len(losses) // 10 or 1)
    if len(losses) > window:
        moving_avg = [sum(losses[i:i+window])/window for i in range(len(losses)-window)]
        plt.plot(range(window//2, len(losses)-window//2), moving_avg, 'r-', linewidth=2, label=f'Média móvel ({window})')
    
    plt.legend()
    
    # Plot da acurácia por horizonte
    plt.subplot(1, 2, 2)
    n_acertos = dados.get('n_acertos', [0,0,0,0])
    n_erros = dados.get('n_erros', [0,0,0,0])
    horizontes = ['5s', '15s', '30s', '60s']
    accuracies = []
    
    for i in range(4):
        total = n_acertos[i] + n_erros[i]
        acc = (n_acertos[i] / total * 100) if total > 0 else 0
        accuracies.append(acc)
    
    cores = ['#00e676' if a >= 80 else '#f59e0b' if a >= 60 else '#ff3d57' for a in accuracies]
    bars = plt.bar(horizontes, accuracies, color=cores)
    plt.ylim(0, 105)
    plt.ylabel('Acurácia (%)')
    plt.title('Acurácia por Horizonte')
    
    # Adiciona valores nas barras
    for bar, acc in zip(bars, accuracies):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                f'{acc:.1f}%', ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    plt.show()
    
    # Estatísticas
    print("\n📈 ESTATÍSTICAS FINAIS:")
    print(f"   Total de passos: {dados.get('geracao', 0)}")
    print(f"   Loss final: {historico_loss[-1]:.4f}")
    print(f"   Loss médio: {sum(historico_loss)/len(historico_loss):.4f}")
    print(f"   Loss mínimo: {min(historico_loss):.4f}")
    
    for i, (a, e) in enumerate(zip(n_acertos, n_erros)):
        total = a + e
        acc = (a / total * 100) if total > 0 else 0
        print(f"   {horizontes[i]}: {acc:.1f}% ({a:.1f}/{total:.1f})")

if __name__ == "__main__":
    ver_loss_insana()