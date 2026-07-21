# calcular_rr.py
import json
import glob
import os

def calcular_risk_reward():
    """Calcula o Risk/Reward real baseado nos dados de verificação"""
    
    print("\n" + "=" * 70)
    print("📊 ANÁLISE DE RISK/REWARD — TRADER AI")
    print("=" * 70)
    
    arquivos = glob.glob("data/verificacoes/*.json")
    
    if not arquivos:
        print("❌ Nenhum arquivo de verificação encontrado.")
        print("💡 Execute o sistema com moedas carregadas primeiro.")
        return
    
    total_geral_acertos = 0
    total_geral_erros = 0
    
    for arquivo in arquivos:
        moeda = os.path.basename(arquivo).replace(".json", "")
        
        with open(arquivo) as f:
            dados = json.load(f)
        
        print(f"\n💰 {moeda.replace('USDT', '')}")
        print(f"{'─' * 70}")
        print(f"{'Horizonte':<8} {'Trades':<8} {'Acertos':<8} {'Erros':<8} {'Acurácia':<10} {'R/R Mín':<10} {'Lucro 1:2?':<12}")
        print(f"{'─' * 70}")
        
        for h in ['5', '15', '30', '60', '300', '900', '1800', '3600']:
            if h in dados and dados[h]['total'] > 10:
                d = dados[h]
                acertos = d['acertos']
                erros = d['erros']
                total = d['total']
                acuracia = round(acertos / total * 100, 1) if total > 0 else 0
                
                # R/R mínimo para empatar
                if acertos > 0:
                    rr_minimo = round(erros / acertos, 2)
                else:
                    rr_minimo = 999
                
                # Com R/R 1:2, lucra? (precisa > 33.3%)
                lucro_1_2 = "✅ SIM" if acuracia > 33.3 else "❌ NÃO"
                
                # Nome do horizonte
                h_int = int(h)
                if h_int < 60:
                    nome_h = f"{h_int}s"
                elif h_int < 3600:
                    nome_h = f"{h_int//60}min"
                else:
                    nome_h = f"{h_int//3600}h"
                
                print(f"{nome_h:<8} {total:<8} {acertos:<8} {erros:<8} {acuracia}%{'':<5} 1:{rr_minimo}{'':<6} {lucro_1_2:<12}")
                
                total_geral_acertos += acertos
                total_geral_erros += erros
    
    # Resumo geral
    total_geral = total_geral_acertos + total_geral_erros
    if total_geral > 0:
        acuracia_geral = round(total_geral_acertos / total_geral * 100, 1)
        rr_geral = round(total_geral_erros / total_geral_acertos, 2) if total_geral_acertos > 0 else 999
        
        print(f"\n{'=' * 70}")
        print(f"🌍 GLOBAL (todos horizontes, todas moedas):")
        print(f"{'=' * 70}")
        print(f"   Trades Totais: {total_geral}")
        print(f"   Acertos: {total_geral_acertos} | Erros: {total_geral_erros}")
        print(f"   Acurácia Média: {acuracia_geral}%")
        print(f"   R/R Mínimo Global: 1:{rr_geral}")
        
        # Explicação
        print(f"\n📈 O QUE ISSO SIGNIFICA:")
        print(f"{'─' * 70}")
        print(f"Com {acuracia_geral}% de acurácia:")
        
        if rr_geral < 1:
            print(f"   ✅ Você já LUCRA com R/R 1:1!")
            print(f"   Ex: 100 trades, R$100 por trade = +R${(total_geral_acertos - total_geral_erros) * 100}")
        elif rr_geral < 2:
            print(f"   ✅ Você lucra com R/R 1:{rr_geral}")
            print(f"   Ex: Arriscar R$100 pra ganhar R${rr_geral * 100}")
        else:
            print(f"   ⚠️ Você precisa de R/R 1:{rr_geral} para empatar")
            print(f"   Com R/R 1:2, seu lucro esperado é POSITIVO!")
        
        print(f"\n💡 R/R Mínimo: o menor risco/recompensa para NÃO perder dinheiro")
        print(f"💡 R/R 1:2 = arriscar R$100 pra ganhar R$200")
        print(f"💡 Com {acuracia_geral}% + R/R 1:2, a cada 100 trades você LUCRA!")
    
    print("=" * 70)

if __name__ == "__main__":
    calcular_risk_reward()