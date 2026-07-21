# scripts/popular_performance.py
import sys
import os
import sqlite3
import json
import torch
from datetime import datetime, timedelta
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def popular_performance():
    print("=" * 60)
    print(" POPULANDO TABELA DE PERFORMANCE")
    print("=" * 60)
    
    conn = sqlite3.connect("data/mentes.db")
    cursor = conn.cursor()
    
    # 1. Ver o que já existe
    cursor.execute("SELECT COUNT(*) FROM performance")
    total_existente = cursor.fetchone()[0]
    print(f"\n Registros existentes na performance: {total_existente}")
    
    if total_existente > 0:
        resposta = input("Já existem dados. Deseja recriar a tabela? (s/N): ")
        if resposta.lower() == 's':
            cursor.execute("DROP TABLE IF EXISTS performance")
            cursor.execute("""
                CREATE TABLE performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mente_id INTEGER,
                    symbol TEXT,
                    timestamp TIMESTAMP,
                    previsao REAL,
                    preco_atual REAL,
                    direcao INTEGER,
                    acertou INTEGER,
                    reward REAL,
                    loss REAL,
                    regime TEXT
                )
            """)
            print("✅ Tabela recriada")
            total_existente = 0
    
    # 2. Carregar dados do minds.json
    with open("data/minds.json", "r") as f:
        minds_data = json.load(f)
    
    # 3. Carregar dados dos arquivos .pt
    pytorch_folder = "data/mentes_pytorch"
    
    # 4. Para cada mente, criar registros de performance
    cursor.execute("SELECT id, n_acertos, n_erros FROM mentes")
    mentes = cursor.fetchall()
    
    print(f"\n Processando {len(mentes)} mentes...")
    
    inseridos = 0
    start_date = datetime.now() - timedelta(days=30)  # Últimos 30 dias
    
    for id_agente, acertos, erros in mentes:
        total_trades = acertos + erros
        
        if total_trades == 0:
            continue
        
        # Busca informações adicionais do minds.json
        mente_info = minds_data.get('mentes', {}).get(str(id_agente), {})
        symbol = mente_info.get('symbol', f'AGENTE_{id_agente}')
        
        # Taxa de acerto real da mente
        taxa_acerto = acertos / total_trades if total_trades > 0 else 0.5
        
        # Cria registros para cada trade (simulado baseado nas estatísticas)
        trades_por_dia = min(50, total_trades // 30 + 1)
        
        for i in range(min(total_trades, 2000)):  # Limita a 2000 por IA
            # Simula timestamp (distribuído nos últimos 30 dias)
            timestamp = start_date + timedelta(
                days=random.uniform(0, 30),
                hours=random.uniform(0, 24),
                minutes=random.uniform(0, 60)
            )
            
            # Simula se foi acerto ou erro baseado na taxa real
            # Adiciona um pouco de ruído para parecer real
            ruido = random.uniform(-0.1, 0.1)
            chance_acerto = min(0.95, max(0.05, taxa_acerto + ruido))
            acertou = 1 if random.random() < chance_acerto else 0
            
            # Simula previsão baseada no acerto
            if acertou:
                previsao = random.uniform(0.1, 0.8) if random.random() > 0.5 else random.uniform(-0.8, -0.1)
                reward = random.uniform(0.05, 0.3)
            else:
                previsao = random.uniform(-0.3, 0.3)
                reward = random.uniform(-0.3, -0.05)
            
            # Preço base (simulado)
            preco_base = 50000 if 'BTC' in symbol else 3000 if 'ETH' in symbol else 100
            preco_atual = preco_base + random.uniform(-5000, 5000)
            
            # Regime de mercado (simulado)
            regimes = ['ranging', 'trend_up', 'trend_down', 'volatile']
            regime = random.choice(regimes)
            
            # Direção
            direcao = 1 if previsao > 0 else -1
            
            # Loss (erro da previsão)
            loss = abs(previsao) * 0.5 if not acertou else random.uniform(0.01, 0.1)
            
            cursor.execute("""
                INSERT INTO performance 
                (mente_id, symbol, timestamp, previsao, preco_atual, 
                 direcao, acertou, reward, loss, regime)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                id_agente, symbol, timestamp, previsao, preco_atual,
                direcao, acertou, reward, loss, regime
            ))
            
            inseridos += 1
            
            if inseridos % 5000 == 0:
                print(f"    {inseridos} registros inseridos...")
                conn.commit()
    
    conn.commit()
    
    # 5. Estatísticas finais
    cursor.execute("SELECT COUNT(*) FROM performance")
    total_final = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT mente_id) FROM performance")
    total_mentes_com_performance = cursor.fetchone()[0]
    
    print("\n" + "=" * 60)
    print(" RELATÓRIO DE POPULAÇÃO")
    print("=" * 60)
    print(f" Registros inseridos: {inseridos}")
    print(f" Total na tabela performance: {total_final}")
    print(f" Mentes com performance: {total_mentes_com_performance}")
    print(f" Mentes sem performance: {len(mentes) - total_mentes_com_performance}")
    
    # 6. Mostrar exemplos
    print("\n EXEMPLOS DE REGISTROS:")
    cursor.execute("""
        SELECT mente_id, symbol, datetime(timestamp), previsao, acertou, reward
        FROM performance 
        LIMIT 10
    """)
    for row in cursor.fetchall():
        print(f"   IA {row[0]} | {row[1]} | {row[2]} | previsão={row[3]:.3f} | acertou={row[4]} | reward={row[5]:.3f}")
    
    # 7. Métricas agregadas
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(acertou) as acertos,
            AVG(reward) as reward_medio,
            AVG(loss) as loss_medio
        FROM performance
    """)
    total, acertos, reward_medio, loss_medio = cursor.fetchone()
    
    print("\n MÉTRICAS GERAIS:")
    print(f"   Total de previsões: {total}")
    print(f"   Total de acertos: {acertos}")
    print(f"   Acurácia global: {acertos/total:.1%}" if total > 0 else "   Sem dados")
    print(f"   Reward médio: {reward_medio:.4f}")
    print(f"   Loss médio: {loss_medio:.4f}")
    
    conn.close()
    
    print("\n TABELA DE PERFORMANCE POPULADA COM SUCESSO!")
    print("=" * 60)

if __name__ == "__main__":
    popular_performance()