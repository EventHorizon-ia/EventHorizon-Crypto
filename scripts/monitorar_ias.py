# validar_previsoes.py



import json
import os
import time
from datetime import datetime, timedelta
from collections import defaultdict

HORIZONTES = [5, 15, 30, 60, 300, 900, 1800, 3600, 18000, 86400]

_NOMES_H = {
    5: "5s", 15: "15s", 30: "30s", 60: "1min",
    300: "5min", 900: "15min", 1800: "30min", 3600: "1h",
    18000: "5h", 86400: "1d",
}

# =============================================================================
# ANÁLISE POR ARQUIVO JSON
# =============================================================================

def analisar_json_verificacao():
    """Analisa os arquivos JSON de verificação (dados REAIS)"""
    
    print("\n" + "=" * 70)
    print("📊 VALIDAÇÃO DE PREVISÕES - DADOS REAIS DE VERIFICAÇÃO")
    print("=" * 70)
    
    pasta = "data/verificacoes"
    if not os.path.exists(pasta):
        print("❌ Pasta data/verificacoes não encontrada!")
        return
    
    arquivos = sorted([f for f in os.listdir(pasta) if f.endswith('.json')])
    
    if not arquivos:
        print("❌ Nenhum arquivo de verificação encontrado!")
        return
    
    for arquivo in arquivos:
        moeda = arquivo.replace('.json', '')
        caminho = os.path.join(pasta, arquivo)
        
        try:
            with open(caminho, 'r') as f:
                dados = json.load(f)
        except:
            continue
        
        print(f"\n{'─' * 70}")
        print(f"💰 {moeda}")
        print(f"{'─' * 70}")
        print(f"{'Horizonte':<10} {'Trades':<10} {'Acertos':<10} {'Erros':<10} {'Acurácia':<12} {'Status'}")
        print(f"{'─' * 70}")
        
        for h in sorted(dados.keys(), key=int):
            d = dados[h]
            total = d.get('total', 0)
            acertos = d.get('acertos', 0)
            erros = d.get('erros', 0)
            
            if total == 0:
                continue
            
            acc = (acertos / total) * 100
            nome = _NOMES_H.get(int(h), f"{h}s")
            
            # Status
            if acc >= 60:
                status = "🟢 EXCELENTE"
            elif acc >= 55:
                status = "🟡 BOM"
            elif acc >= 50:
                status = "🟠 REGULAR"
            elif acc >= 45:
                status = "🔴 RUIM"
            else:
                status = "💀 PÉSSIMO"
            
            # Barra visual
            barra = "█" * int(acc / 10) + "░" * (10 - int(acc / 10))
            
            print(f"{nome:<10} {total:<10} {acertos:<10} {erros:<10} {barra} {acc:5.1f}%  {status}")
        
        # Análise recente (últimos 100 trades de cada horizonte)
        print(f"\n   📈 PERFORMANCE RECENTE (últimos 100 trades):")
        for h in sorted(dados.keys(), key=int):
            d = dados[h]
            historico = d.get('historico', [])
            
            if len(historico) >= 50:
                recente = historico[-100:]
                acc_recente = (sum(recente) / len(recente)) * 100
                total_acc = (d['acertos'] / d['total'] * 100) if d['total'] > 0 else 0
                tendencia = acc_recente - total_acc
                
                nome = _NOMES_H.get(int(h), f"{h}s")
                seta = "📈" if tendencia > 2 else ("📉" if tendencia < -2 else "➡️")
                
                print(f"   {nome:<8}: {acc_recente:5.1f}% {seta} ({tendencia:+.1f}% vs total)")

# =============================================================================
# ANÁLISE POR MOEDA (visão geral)
# =============================================================================

def resumo_geral():
    """Resumo geral de todas as moedas"""
    
    print("\n" + "=" * 70)
    print("🎯 RESUMO GERAL - MELHORES HORIZONTES POR MOEDA")
    print("=" * 70)
    
    pasta = "data/verificacoes"
    if not os.path.exists(pasta):
        return
    
    arquivos = sorted([f for f in os.listdir(pasta) if f.endswith('.json')])
    ranking = []
    
    for arquivo in arquivos:
        moeda = arquivo.replace('.json', '')
        caminho = os.path.join(pasta, arquivo)
        
        try:
            with open(caminho, 'r') as f:
                dados = json.load(f)
        except:
            continue
        
        # Encontra o melhor horizonte para cada moeda
        melhor_h = None
        melhor_acc = 0
        melhor_total = 0
        
        for h in dados:
            d = dados[h]
            total = d.get('total', 0)
            if total >= 500:  # mínimo 500 trades
                acc = (d.get('acertos', 0) / total) * 100
                if acc > melhor_acc:
                    melhor_acc = acc
                    melhor_h = h
                    melhor_total = total
        
        if melhor_h:
            nome_h = _NOMES_H.get(int(melhor_h), f"{melhor_h}s")
            ranking.append((moeda, nome_h, melhor_acc, melhor_total))
    
    ranking.sort(key=lambda x: x[2], reverse=True)
    
    print(f"\n{'Moeda':<12} {'Melhor H':<10} {'Acurácia':<12} {'Trades':<10}")
    print(f"{'─' * 50}")
    
    for moeda, h, acc, total in ranking:
        barra = "█" * int(acc / 10) + "░" * (10 - int(acc / 10))
        print(f"{moeda:<12} {h:<10} {barra} {acc:5.1f}%  {total}")

# =============================================================================
# SIMULAÇÃO DE TRADES RECENTES
# =============================================================================

def simular_trades_recentes():
    """Simula o resultado dos últimos 50 sinais de cada moeda"""
    
    print("\n" + "=" * 70)
    print("🧪 SIMULAÇÃO - ÚLTIMOS 50 TRADES")
    print("=" * 70)
    
    pasta = "data/verificacoes"
    if not os.path.exists(pasta):
        return
    
    arquivos = sorted([f for f in os.listdir(pasta) if f.endswith('.json')])
    
    for arquivo in arquivos:
        moeda = arquivo.replace('.json', '')
        caminho = os.path.join(pasta, arquivo)
        
        try:
            with open(caminho, 'r') as f:
                dados = json.load(f)
        except:
            continue
        
        print(f"\n💰 {moeda}:")
        
        for h in sorted(dados.keys(), key=int):
            d = dados[h]
            historico = d.get('historico', [])
            
            if len(historico) < 5000:
                continue
            
            # Últimos 50 trades
            ultimos = historico[-5000:]
            acertos = sum(ultimos)
            erros = len(ultimos) - acertos
            acc = (acertos / len(ultimos)) * 100
            
            nome = _NOMES_H.get(int(h), f"{h}s")
            
            # Simula lucro com R/R 1:2
            lucro_1_2 = acertos * 2 - erros * 1
            
            # Simula lucro com R/R 1:3
            lucro_1_3 = acertos * 3 - erros * 1
            
            print(f"  {nome:<8}: {acertos}✅ {erros}❌ | {acc:5.1f}% | "
                  f"Lucro 1:2 = {lucro_1_2:+d}R | Lucro 1:3 = {lucro_1_3:+d}R")

# =============================================================================
# TENDÊNCIAS (melhorando ou piorando?)
# =============================================================================

def analisar_tendencias():
    """Analisa se o modelo está melhorando ou piorando"""
    
    print("\n" + "=" * 70)
    print("📈 ANÁLISE DE TENDÊNCIAS (melhorando ou piorando?)")
    print("=" * 70)
    
    pasta = "data/verificacoes"
    if not os.path.exists(pasta):
        return
    
    arquivos = sorted([f for f in os.listdir(pasta) if f.endswith('.json')])
    
    print(f"\n{'Moeda':<12} {'Horizonte':<10} {'Total':<10} {'Recente':<10} {'Tendência'}")
    print(f"{'─' * 65}")
    
    for arquivo in arquivos:
        moeda = arquivo.replace('.json', '')
        caminho = os.path.join(pasta, arquivo)
        
        try:
            with open(caminho, 'r') as f:
                dados = json.load(f)
        except:
            continue
        
        for h in sorted(dados.keys(), key=int):
            d = dados[h]
            historico = d.get('historico', [])
            total = d.get('total', 0)
            
            if total < 100 or len(historico) < 100:
                continue
            
            # Divide em 3 partes: antigo, médio, recente
            tercos = len(historico) // 3
            if tercos < 30:
                continue
            
            antigo = historico[:tercos]
            medio = historico[tercos:2*tercos]
            recente = historico[2*tercos:]
            
            acc_antigo = (sum(antigo) / len(antigo)) * 100
            acc_medio = (sum(medio) / len(medio)) * 100
            acc_recente = (sum(recente) / len(recente)) * 100
            
            # Tendência
            if acc_recente > acc_medio > acc_antigo:
                tendencia = "📈 MELHORANDO"
            elif acc_recente < acc_medio < acc_antigo:
                tendencia = "📉 PIORANDO"
            elif acc_recente > acc_antigo:
                tendencia = "↗️ RECUPERANDO"
            elif acc_recente < acc_antigo:
                tendencia = "↘️ CAINDO"
            else:
                tendencia = "➡️ ESTÁVEL"
            
            nome = _NOMES_H.get(int(h), f"{h}s")
            
            if abs(acc_recente - acc_antigo) > 3:  # só mostra mudanças significativas
                print(f"{moeda:<12} {nome:<10} {acc_antigo:5.1f}%     {acc_recente:5.1f}%     {tendencia}")

# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("\n" + "💀" * 35)
    print("🔮 SISTEMA DE VALIDAÇÃO DE PREVISÕES")
    print("💀" * 35)
    print(f"⏰ Executado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Análise detalhada por moeda
    analisar_json_verificacao()
    
    # 2. Resumo geral
    resumo_geral()
    
    # 3. Simulação de trades recentes
    simular_trades_recentes()
    
    # 4. Tendências
    analisar_tendencias()
    
    print("\n" + "=" * 70)
    print("💡 INTERPRETAÇÃO:")
    print("   📈 MELHORANDO = O aprendizado está funcionando")
    print("   📉 PIORANDO = Overfitting ou regime change")
    print("   ➡️ ESTÁVEL = Modelo convergiu (bom ou ruim?)")
    print("   🟢 >60% = Lucrativo com R/R adequado")
    print("   💀 <45% = Melhor jogar moeda pro ar")
    print("=" * 70)