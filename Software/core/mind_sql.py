# mind_sql.py - Banco de dados neural para PyTorch

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, Optional, List, Any
from collections import deque

class BancoMentesSQL:
    """
    Banco de dados SQLite para armazenar:
    - Modelos PyTorch (pesos serializados)
    - Estatísticas de performance
    - Histórico de acertos/erros
    - Métricas temporais
    """
    
    def __init__(self, db_path: str = "data/mentes.db"):
        self.db_path = db_path
        self.cache_mentes: Dict[int, Any] = {}  # Cache em memória
        self._init_tables()
    
    def _init_tables(self):
        """Cria todas as tabelas necessárias"""
        os.makedirs("data", exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            # 1. Tabela principal de mentes
            conn.execute("""
                CREATE TABLE IF NOT EXISTS mentes (
                    id INTEGER PRIMARY KEY,
                    tipo TEXT DEFAULT 'pytorch',
                    n_acertos INTEGER DEFAULT 0,
                    n_erros INTEGER DEFAULT 0,
                    geracao INTEGER DEFAULT 0,
                    accuracy REAL DEFAULT 0.5,
                    pesos BLOB,
                    optimizer_state BLOB,
                    historico_loss TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 2. Tabela de performance (cada previsão)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mente_id INTEGER,
                    symbol TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    previsao REAL,
                    preco_atual REAL,
                    direcao INTEGER,
                    acertou INTEGER,
                    reward REAL,
                    loss REAL,
                    regime TEXT,
                    FOREIGN KEY (mente_id) REFERENCES mentes(id)
                )
            """)
            
            # 3. Tabela de métricas diárias
            conn.execute("""
                CREATE TABLE IF NOT EXISTS metrics_daily (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE UNIQUE,
                    total_mentes INTEGER,
                    total_previsoes INTEGER,
                    total_acertos INTEGER,
                    avg_accuracy REAL,
                    avg_loss REAL,
                    best_accuracy REAL,
                    worst_accuracy REAL
                )
            """)
            
            # 4. Tabela de ranking por hora
            conn.execute("""
                CREATE TABLE IF NOT EXISTS hourly_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE,
                    hora INTEGER,
                    total_previsoes INTEGER,
                    acertos INTEGER,
                    accuracy REAL,
                    UNIQUE(date, hora)
                )
            """)
            
            # 5. Tabela de configuração
            conn.execute("""
                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Criar índices para performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_performance_mente ON performance(mente_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_performance_time ON performance(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_performance_symbol ON performance(symbol)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_performance_date ON performance(date(timestamp))")
            
            # Inserir configuração inicial se não existir
            conn.execute("""
                INSERT OR IGNORE INTO config (key, value)
                VALUES ('db_version', '1.0')
            """)
            
            print(f"[SQL] Banco de dados inicializado: {self.db_path}")
    
    def salvar_mente(self, id_agente: int, stats: Dict, pesos_bytes: bytes = None, optimizer_bytes: bytes = None):
        """Salva ou atualiza uma mente no banco"""
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO mentes 
                (id, tipo, n_acertos, n_erros, geracao, accuracy, 
                 pesos, optimizer_state, historico_loss, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                id_agente,
                stats.get('tipo', 'pytorch'),
                stats.get('n_acertos', 0),
                stats.get('n_erros', 0),
                stats.get('geracao', 0),
                stats.get('accuracy', 0.5),
                pesos_bytes,
                optimizer_bytes,
                json.dumps(stats.get('historico_loss', []))
            ))
        
        print(f"[SQL] Mente {id_agente} salva (acertos: {stats.get('n_acertos', 0)})")
    
    def carregar_mente(self, id_agente: int) -> Optional[Dict]:
        """Carrega os dados de uma mente do banco"""
        
        # Verifica cache
        if id_agente in self.cache_mentes:
            return self.cache_mentes[id_agente]
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM mentes WHERE id = ?
            """, (id_agente,))
            row = cursor.fetchone()
        
        if not row:
            return None
        
        dados = {
            'id': row['id'],
            'tipo': row['tipo'],
            'n_acertos': row['n_acertos'],
            'n_erros': row['n_erros'],
            'geracao': row['geracao'],
            'accuracy': row['accuracy'],
            'pesos': row['pesos'],
            'optimizer_state': row['optimizer_state'],
            'historico_loss': json.loads(row['historico_loss']) if row['historico_loss'] else []
        }
        
        # Cache
        self.cache_mentes[id_agente] = dados
        
        return dados
    
    def registrar_performance(self, mente_id: int, symbol: str, previsao: float,
                              preco_atual: float, direcao: int, acertou: bool,
                              reward: float, loss: float, regime: str = "ranging"):
        """Registra cada previsão para análise"""
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO performance 
                (mente_id, symbol, previsao, preco_atual, direcao, acertou, reward, loss, regime)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                mente_id, symbol, previsao, preco_atual, direcao,
                1 if acertou else 0, reward, loss, regime
            ))
    
    def registrar_metricas_diarias(self):
        """Calcula e registra métricas do dia"""
        
        with sqlite3.connect(self.db_path) as conn:
            # Métricas do dia
            cursor = conn.execute("""
                SELECT 
                    COUNT(DISTINCT mente_id) as total_mentes,
                    COUNT(*) as total_previsoes,
                    SUM(acertou) as total_acertos,
                    AVG(CASE WHEN loss IS NOT NULL THEN loss ELSE 0 END) as avg_loss
                FROM performance
                WHERE date(timestamp) = date('now')
            """)
            row = cursor.fetchone()
            
            # Acurácia por mente
            cursor = conn.execute("""
                SELECT 
                    mente_id,
                    CAST(SUM(acertou) AS FLOAT) / COUNT(*) as accuracy
                FROM performance
                WHERE date(timestamp) = date('now')
                GROUP BY mente_id
            """)
            accuracies = [row2[1] for row2 in cursor.fetchall()]
            
            conn.execute("""
                INSERT OR REPLACE INTO metrics_daily 
                (date, total_mentes, total_previsoes, total_acertos, avg_accuracy, avg_loss,
                 best_accuracy, worst_accuracy)
                VALUES (date('now'), ?, ?, ?, ?, ?, ?, ?)
            """, (
                row[0] or 0,
                row[1] or 0,
                row[2] or 0,
                sum(accuracies) / len(accuracies) if accuracies else 0,
                row[3] or 0,
                max(accuracies) if accuracies else 0,
                min(accuracies) if accuracies else 0
            ))
    
    def get_ranking(self, limit: int = 10, min_trades: int = 10) -> List[Dict]:
        """Retorna ranking das melhores IAs"""
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT 
                    m.id,
                    m.n_acertos,
                    m.n_erros,
                    CAST(m.n_acertos AS FLOAT) / (m.n_acertos + m.n_erros) as acuracia,
                    m.geracao,
                    datetime(m.updated_at) as ultimo_treinamento,
                    (SELECT symbol FROM performance WHERE mente_id = m.id ORDER BY timestamp DESC LIMIT 1) as ultima_moeda
                FROM mentes m
                WHERE m.n_acertos + m.n_erros > ?
                ORDER BY acuracia DESC
                LIMIT ?
            """, (min_trades, limit))
            
            return [dict(row) for row in cursor]
    
    def get_performance_por_hora(self, symbol: str = None) -> List[Dict]:
        """Retorna performance agregada por hora do dia"""
        
        where_symbol = "AND symbol = ?" if symbol else ""
        params = (symbol,) if symbol else ()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(f"""
                SELECT 
                    strftime('%H', timestamp) as hora,
                    COUNT(*) as total,
                    SUM(acertou) as acertos,
                    CAST(SUM(acertou) AS FLOAT) / COUNT(*) as accuracy
                FROM performance
                {where_symbol}
                GROUP BY hora
                ORDER BY hora
            """, params)
            
            return [dict(row) for row in cursor]
        
    
        # ========================================================================
    # MÉTODOS PARA O DASHBOARD DO TRADER
    # ========================================================================
    
    def get_performance_por_moeda(self, limit: int = 10) -> List[Dict]:
        """Retorna performance agregada por moeda para o dashboard"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT 
                    symbol,
                    COUNT(*) as total,
                    SUM(acertou) as acertos,
                    ROUND(SUM(acertou) * 100.0 / COUNT(*), 1) as acuracia
                FROM performance
                WHERE symbol IS NOT NULL
                GROUP BY symbol
                ORDER BY acuracia DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor]
    
    def get_melhores_horarios(self, limit: int = 5) -> List[Dict]:
        """Retorna os melhores horários para trade (últimos 7 dias)"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT 
                    strftime('%H:00', timestamp) as hora,
                    COUNT(*) as total,
                    ROUND(SUM(acertou) * 100.0 / COUNT(*), 1) as acuracia
                FROM performance
                WHERE timestamp > datetime('now', '-7 days')
                GROUP BY strftime('%H', timestamp)
                ORDER BY acuracia DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor]
    
    def get_piores_horarios(self, limit: int = 3) -> List[Dict]:
        """Retorna os piores horários para trade (evitar)"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT 
                    strftime('%H:00', timestamp) as hora,
                    COUNT(*) as total,
                    ROUND(SUM(acertou) * 100.0 / COUNT(*), 1) as acuracia
                FROM performance
                WHERE timestamp > datetime('now', '-7 days')
                GROUP BY strftime('%H', timestamp)
                ORDER BY acuracia ASC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor]
    
    def get_evolucao_acuracia(self, dias: int = 7) -> List[Dict]:
        """Retorna evolução da acurácia nos últimos X dias"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT 
                    DATE(timestamp) as data,
                    COUNT(*) as total,
                    ROUND(SUM(acertou) * 100.0 / COUNT(*), 1) as acuracia
                FROM performance
                WHERE timestamp > datetime('now', ?)
                GROUP BY DATE(timestamp)
                ORDER BY data ASC
            """, (f'-{dias} days',))
            return [dict(row) for row in cursor]
    
    def get_sinais_por_moeda(self) -> List[Dict]:
        """Retorna o último sinal de cada moeda (para o dashboard)"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT 
                    symbol,
                    previsao,
                    direcao,
                    acertou,
                    timestamp,
                    regime
                FROM performance p1
                WHERE timestamp = (
                    SELECT MAX(timestamp) 
                    FROM performance p2 
                    WHERE p2.symbol = p1.symbol
                )
                ORDER BY timestamp DESC
            """)
            return [dict(row) for row in cursor]
    
    def get_estatisticas_gerais(self) -> Dict:
        """Retorna estatísticas gerais do sistema"""
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Total de mentes
            cursor = conn.execute("SELECT COUNT(*) as total FROM mentes")
            total_mentes = cursor.fetchone()['total']
            
            # Performance geral
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_previsoes,
                    SUM(acertou) as total_acertos,
                    AVG(reward) as avg_reward,
                    AVG(loss) as avg_loss,
                    AVG(previsao) as avg_previsao
                FROM performance
            """)
            perf = cursor.fetchone()
            
            # Melhor mente
            cursor = conn.execute("""
                SELECT 
                    m.id,
                    CAST(m.n_acertos AS FLOAT) / (m.n_acertos + m.n_erros) as acuracia
                FROM mentes m
                WHERE m.n_acertos + m.n_erros > 10
                ORDER BY acuracia DESC
                LIMIT 1
            """)
            melhor = cursor.fetchone()
            
            return {
                'total_mentes': total_mentes,
                'total_previsoes': perf['total_previsoes'] or 0,
                'total_acertos': perf['total_acertos'] or 0,
                'acurácia_global': (perf['total_acertos'] or 0) / (perf['total_previsoes'] or 1),
                'reward_medio': perf['avg_reward'] or 0,
                'loss_medio': perf['avg_loss'] or 0,
                'previsao_media': perf['avg_previsao'] or 0,
                'melhor_ia': melhor['id'] if melhor else None,
                'melhor_acuracia': melhor['acuracia'] if melhor else 0
            }
    
    def limpar_cache(self):
        """Limpa cache em memória"""
        self.cache_mentes.clear()
    
    def backup(self, backup_path: str = None):
        """Faz backup do banco de dados"""
        if not backup_path:
            backup_path = f"data/backup_mentes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        
        import shutil
        shutil.copy2(self.db_path, backup_path)
        print(f"[SQL] Backup salvo em {backup_path}")
        return backup_path
    
   # No final do arquivo mind_sql.py, adicione:

    # ⭐ Instância global para uso em outros módulos
_banco_sql_instance = None

def get_banco_sql():
    global _banco_sql_instance
    if _banco_sql_instance is None:
        _banco_sql_instance = BancoMentesSQL()
    return _banco_sql_instance

# Para compatibilidade com o código existente
banco_sql = get_banco_sql()
   