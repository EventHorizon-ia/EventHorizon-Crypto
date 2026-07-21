# calcular_metricas.py
import json
import os
import glob

def calcular_metricas():
    """Calcula métricas profissionais de todas as moedas"""
    
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO DE PERFORMANCE — TRADER AI")
    print("=" * 60)
    
    arquivos = glob.glob("data/verificacoes/*.json")
    
    if not arquivos:
        print("❌ Nenhum arquivo de verificação encontrado.")
        return
    
    total_global_acertos = 0
    total_global_erros = 0
    
    for arquivo in arquivos:
        moeda = os.path.basename(arquivo).replace(".json", "")
        
        with open(arquivo) as f:
            dados = json.load(f)
        
        print(f"\n{'─' * 60}")
        print(f"💰 {moeda.replace('USDT', '')}")
        print(f"{'─' * 60}")
        
        for h in ['5', '15', '30', '60', '300', '900', '1800', '3600']:
            if h in dados and dados[h]['total'] > 10:
                d = dados[h]
                acertos = d['acertos']
                erros = d['erros']
                total = d['total']
                acuracia = round(acertos / total * 100, 1)
                
                # Profit Factor (supondo ganho = perda = 1 unidade)
                pf = round(acertos / erros, 2) if erros > 0 else float('inf')
                
                # Nome do horizonte
                h_int = int(h)
                if h_int < 60:
                    nome_h = f"{h_int}s"
                elif h_int < 3600:
                    nome_h = f"{h_int//60}min"
                else:
                    nome_h = f"{h_int//3600}h"
                
                print(f"\n⏱️ {nome_h}:")
                print(f"   Trades: {total}")
                print(f"   Acertos: {acertos} | Erros: {erros}")
                print(f"   Acurácia: {acuracia}%")
                print(f"   Profit Factor: {pf}")
                
                total_global_acertos += acertos
                total_global_erros += erros
    
    # Global
    if total_global_acertos + total_global_erros > 0:
        total_global = total_global_acertos + total_global_erros
        acuracia_global = round(total_global_acertos / total_global * 100, 1)
        pf_global = round(total_global_acertos / total_global_erros, 2) if total_global_erros > 0 else float('inf')
        
        print(f"\n{'=' * 60}")
        print(f"🌍 GLOBAL (todos horizontes, todas moedas):")
        print(f"{'=' * 60}")
        print(f"   Trades Totais: {total_global}")
        print(f"   Acertos: {total_global_acertos} | Erros: {total_global_erros}")
        print(f"   Acurácia Média: {acuracia_global}%")
        print(f"   Profit Factor: {pf_global}")
        
        # Interpretação
        print(f"\n📈 INTERPRETAÇÃO:")
        if pf_global > 1.5:
            print(f"   ✅ EXCELENTE — Estratégia altamente lucrativa")
        elif pf_global > 1.2:
            print(f"   👍 BOM — Estratégia lucrativa")
        elif pf_global > 1.0:
            print(f"   ⚠️ OK — Estratégia marginalmente lucrativa")
        else:
            print(f"   ❌ RUIM — Estratégia não lucrativa")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    calcular_metricas()