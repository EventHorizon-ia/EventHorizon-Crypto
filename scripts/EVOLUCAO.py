import json
import os
import shutil
import time
from datetime import datetime

def tirar_snapshot(label):
    """Copia os JSONs de verificação para uma pasta de snapshot"""
    pasta = f"data/snapshots/{label}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(pasta, exist_ok=True)
    
    if os.path.exists("data/verificacoes"):
        for arq in os.listdir("data/verificacoes"):
            shutil.copy(f"data/verificacoes/{arq}", f"{pasta}/{arq}")
    
    print(f"📸 Snapshot '{label}' salvo em {pasta}")
    return pasta

def comparar_snapshots(pasta_antes, pasta_depois):
    """Compara dois snapshots e mostra a evolução"""
    print("\n" + "="*70)
    print("📊 EVOLUÇÃO DA ACURÁCIA REAL")
    print("="*70)
    
    for arq in os.listdir(pasta_antes):
        if not arq.endswith(".json"):
            continue
        
        moeda = arq.replace(".json", "")
        arq_antes = f"{pasta_antes}/{arq}"
        arq_depois = f"{pasta_depois}/{arq}"
        
        if not os.path.exists(arq_depois):
            continue
        
        with open(arq_antes) as f:
            antes = json.load(f)
        with open(arq_depois) as f:
            depois = json.load(f)
        
        print(f"\n💰 {moeda}")
        print(f"   {'Horizonte':<8} {'ANTES':<12} {'DEPOIS':<12} {'Delta':<10} {'Trades+':<10}")
        print(f"   {'-'*52}")
        
        for h in ['5','15','30','60','300','900','1800','3600']:
            a = antes.get(h, {"acertos":0,"erros":0,"total":0})
            d = depois.get(h, {"acertos":0,"erros":0,"total":0})
            
            acc_antes = (a['acertos']/a['total']*100) if a['total'] > 0 else 0
            acc_depois = (d['acertos']/d['total']*100) if d['total'] > 0 else 0
            delta = acc_depois - acc_antes
            trades_novos = d['total'] - a['total']
            
            bar_antes = "█"*int(acc_antes/10) + "░"*(10-int(acc_antes/10))
            bar_depois = "█"*int(acc_depois/10) + "░"*(10-int(acc_depois/10))
            
            print(f"   {h:>6}s  {bar_antes} {acc_antes:5.1f}%  {bar_depois} {acc_depois:5.1f}%  {delta:+.1f}%     +{trades_novos}")

if __name__ == "__main__":
    print("📸 Tire um snapshot AGORA (ANTES do treino)")
    input("Pressione ENTER quando estiver pronto...")
    antes = tirar_snapshot("antes")
    
    print("\n⏳ Deixe o sistema treinar por algumas horas...")
    print("Pressione ENTER quando quiser tirar o snapshot DEPOIS")
    input()
    depois = tirar_snapshot("depois")
    
    comparar_snapshots(antes, depois)