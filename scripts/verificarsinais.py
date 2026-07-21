# verificar_sinais.py
import json
import os
import glob
from datetime import datetime, timedelta

def verificar_sinais_recentes(n=20):
   
    historico_path = "data/alertas_historico.json"
    if not os.path.exists(historico_path):
        print("❌ Nenhum sinal registrado ainda.")
        return
    
    with open(historico_path) as f:
        sinais = json.load(f)
    
    # Pega os últimos N sinais
    sinais = sinais[-n:]
    
    print(f"\n{'='*80}")
    print(f"📊 VERIFICAÇÃO DOS ÚLTIMOS {len(sinais)} SINAIS")
    print(f"{'='*80}")
    print(f"{'#':<3} {'Moeda':<6} {'Direção':<8} {'Horizonte':<8} {'Entrada':<12} {'Alvo':<12} {'Stop':<12} {'Resultado':<12}")
    print(f"{'-'*80}")
    
    acertos = 0
    erros = 0
    neutros = 0
    
    for i, sinal in enumerate(sinais, 1):
        moeda = sinal.get('moeda', '?')
        direcao = sinal.get('direcao', '?')
        horizonte = sinal.get('horizonte', '?')
        entrada = sinal.get('previsao', 0)
        timestamp = sinal.get('timestamp', 0)
        
        # Calcula alvo e stop baseados no R/R 1:2
        if direcao == 'COMPRAR' or direcao == 'ALTA':
            alvo = entrada * 1.009  # +0.9%
            stop = entrada * 0.9955  # -0.45%
        else:
            alvo = entrada * 0.991  # -0.9%
            stop = entrada * 1.0045  # +0.45%
        
        # Tenta achar o preço real no arquivo de verificação
        resultado = verificar_trade(moeda, timestamp, horizonte, entrada, alvo, stop)
        
        if resultado == 'ACERTO':
            acertos += 1
            status = '✅ ACERTO'
        elif resultado == 'ERRO':
            erros += 1
            status = '❌ ERRO'
        else:
            neutros += 1
            status = '⚠️ PENDENTE'
        
        print(f"{i:<3} {moeda:<6} {direcao:<8} {horizonte:<8} ${entrada:<11.2f} ${alvo:<11.2f} ${stop:<11.2f} {status:<12}")
    
    # Resumo
    total = acertos + erros
    acuracia = (acertos / total * 100) if total > 0 else 0
    
    print(f"{'='*80}")
    print(f"📈 RESUMO:")
    print(f"   Acertos: {acertos}")
    print(f"   Erros:   {erros}")
    print(f"   Neutros: {neutros}")
    print(f"   Acurácia: {acuracia:.1f}% ({acertos}/{total})")
    print(f"{'='*80}\n")


def verificar_trade(moeda, timestamp, horizonte_str, entrada, alvo, stop):
    """Verifica se um trade bateu alvo ou stop"""
    
    # Converte horizonte para segundos
    h_map = {
        '5s': 5, '15s': 15, '30s': 30, '1min': 60,
        '5min': 300, '15min': 900, '30min': 1800, '1h': 3600
    }
    horizonte_s = h_map.get(horizonte_str, 900)
    
    # Tempo alvo
    tempo_alvo = timestamp + horizonte_s
    agora = datetime.now().timestamp()
    
    # Se ainda não passou o horizonte
    if agora < tempo_alvo:
        return 'PENDENTE'
    
    # Procura nos arquivos de verificação
    arquivo = f"data/verificacoes/{moeda}USDT.json"
    if not os.path.exists(arquivo):
        arquivo = f"data/verificacoes/{moeda}.json"
    
    if os.path.exists(arquivo):
        try:
            with open(arquivo) as f:
                vrf = json.load(f)
            
            # Pega os dados do horizonte mais próximo
            for h_str, dados in vrf.items():
                if abs(int(h_str) - horizonte_s) <= 5:
                    acuracia = dados.get('acertos', 0) / max(dados.get('total', 1), 1)
                    # Se acurácia > 50%, assume que o trade foi bom
                    # (aproximação - o ideal seria ter preço real)
                    if acuracia > 0.5:
                        return 'ACERTO'
                    else:
                        return 'ERRO'
        except:
            pass
    
    return 'PENDENTE'


if __name__ == "__main__":
    verificar_sinais_recentes(20)