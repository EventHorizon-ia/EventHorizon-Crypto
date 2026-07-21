# Software/core/mind_pytorch.py
#
# MUDANÇAS v3 (vs v2_bugfix):
# ─────────────────────────────────────────────────────────────────────────────
# 1. DelayedRewardBuffer  — a rede só recebe a recompensa de um horizonte
#    quando o tempo real passa (ex: recompensa de 5 min chega 5 min depois).
#    Isso elimina o problema de treinar com dados do passado como se fossem
#    dados do futuro.
#
# 2. aprender_horizonte(i, recompensa)  — treina só a cabeça relevante com
#    a recompensa real do horizonte i.  Gradiente focado, sem ruído cruzado.
#
# 3. Remoção do warmup manual dentro do aprender()  — o scheduler já cuida
#    disso corretamente com LinearLR + CosineAnnealingLR encadeados.
#
# 4. n_acertos / n_erros agora são atualizados APENAS pelo buffer real,
#    nunca pela comparação instantânea pred vs recompensa estimada.
#
# 5. snapshot() expandido para incluir métricas por tipo de horizonte.
# ─────────────────────────────────────────────────────────────────────────────

import torch
import torch.nn as nn
import torch.nn.functional as F
import os
import math
from collections import deque

# 10 HORIZONTES - do micro-scalping ao swing trade
HORIZONTES = [
    5,      # 5 segundos  (micro-scalping)
    15,     # 15 segundos
    30,     # 30 segundos
    60,     # 1 minuto
    300,    # 5 minutos   (scalping)
    900,    # 15 minutos  (intraday)
    1800,   # 30 minutos
    3600,   # 1 hora      (swing curto)
    18000,  # 5 horas     (swing médio)
    86400,  # 1 dia       (position trade)
]
N_HORIZONTES = len(HORIZONTES)


# =============================================================================
# DELAYED REWARD BUFFER
# =============================================================================

class DelayedRewardBuffer:
    """
    Armazena snapshots (timestamp, pred_i, preco) e, quando o horizonte i
    transcorreu, calcula o retorno REAL e devolve para treinamento.

    Uso:
        buf = DelayedRewardBuffer(HORIZONTES, timeframe_s=5)
        buf.registrar(time.time(), preds_lista, preco_atual)
        recompensas = buf.coletar_maduras(time.time(), preco_atual)
        # recompensas: list[(i, recompensa_float)] prontas para aprender
    """

    def __init__(self, horizontes: list[int], timeframe_s: int = 5):
        self.horizontes = horizontes
        self.timeframe_s = timeframe_s
        # Cada entrada: {'ts': float, 'preds': list[float], 'preco': float, 'verificado': set}
        self._buffer: deque = deque(maxlen=10_000)

    def registrar(self, ts: float, preds: list[float], preco: float):
        self._buffer.append({
            'ts': ts,
            'preds': list(preds),
            'preco': preco,
            'verificado': set(),
        })

    def coletar_maduras(self, ts_agora: float, preco_agora: float) -> list[tuple[int, float]]:
        """
        Percorre o buffer e retorna pares (horizonte_idx, recompensa) para
        cada entrada cujo tempo de espera já transcorreu.

        A recompensa é o retorno percentual normalizado por horizonte.
        """
        resultados: list[tuple[int, float]] = []
        tolerancia = max(self.timeframe_s * 3, 15)  # tolerância razoável

        for entrada in self._buffer:
            elapsed = ts_agora - entrada['ts']
            for i, h in enumerate(self.horizontes):
                if i in entrada['verificado']:
                    continue
                if elapsed >= h - tolerancia:
                    # Procura o preço mais próximo do momento alvo no buffer
                    ts_alvo = entrada['ts'] + h
                    preco_alvo = self._buscar_preco_proximo(ts_alvo, ts_agora, preco_agora)
                    if preco_alvo is None:
                        continue

                    retorno_pct = (preco_alvo - entrada['preco']) / (entrada['preco'] + 1e-9) * 100

                    # Normalização por horizonte: horizontes mais longos têm
                    # movimentos maiores — normalizamos para mesma escala
                    if h <= 60:
                        clamp = 3.0
                    elif h <= 3600:
                        clamp = 2.0
                    else:
                        clamp = 1.0

                    recompensa = max(-clamp, min(clamp, retorno_pct)) / clamp

                    resultados.append((i, recompensa))
                    entrada['verificado'].add(i)

        # Limpa entradas totalmente verificadas ou muito antigas (> 2 dias)
        limite_idade = 86400 * 2
        self._buffer = deque(
            (e for e in self._buffer
             if len(e['verificado']) < N_HORIZONTES and (ts_agora - e['ts']) < limite_idade),
            maxlen=10_000
        )
        return resultados

    def _buscar_preco_proximo(self, ts_alvo: float, ts_agora: float,
                               preco_agora: float) -> float | None:
        """
        Procura no buffer o preço mais próximo do timestamp alvo.
        Se o alvo ainda não chegou, retorna None.
        Se o alvo passou, usa o preço mais próximo disponível.
        """
        if ts_alvo > ts_agora + 5:
            return None  # Horizonte ainda não chegou

        melhor = None
        melhor_dist = float('inf')
        for entrada in self._buffer:
            dist = abs(entrada['ts'] - ts_alvo)
            if dist < melhor_dist:
                melhor_dist = dist
                melhor = entrada['preco']

        # Tolerância: aceita até 10% do horizonte de distância
        return melhor if melhor_dist < max(30, ts_agora - ts_alvo + 60) else preco_agora


# =============================================================================
# BLOCOS DA REDE
# =============================================================================

class AtencaoMultiCabeca(nn.Module):
    def __init__(self, dim, num_cabecas=4):
        super().__init__()
        self.num_cabecas = num_cabecas
        self.dim_cabeca = dim // num_cabecas
        self.scale = self.dim_cabeca ** -0.5

        self.q_proj = nn.Linear(dim, dim)
        self.k_proj = nn.Linear(dim, dim)
        self.v_proj = nn.Linear(dim, dim)
        self.out_proj = nn.Linear(dim, dim)
        self.dropout = nn.Dropout(0.1)

    def forward(self, x):
        batch, seq, dim = x.shape
        Q = self.q_proj(x).view(batch, seq, self.num_cabecas, self.dim_cabeca).transpose(1, 2)
        K = self.k_proj(x).view(batch, seq, self.num_cabecas, self.dim_cabeca).transpose(1, 2)
        V = self.v_proj(x).view(batch, seq, self.num_cabecas, self.dim_cabeca).transpose(1, 2)

        atencao = (Q @ K.transpose(-2, -1)) * self.scale
        atencao = F.softmax(atencao, dim=-1)
        atencao = self.dropout(atencao)

        saida = (atencao @ V).transpose(1, 2).contiguous().view(batch, seq, dim)
        return self.out_proj(saida)


class BlocoTransformer(nn.Module):
    def __init__(self, dim, num_cabecas=4, dropout=0.1):
        super().__init__()
        self.atencao = AtencaoMultiCabeca(dim, num_cabecas)
        self.norm1 = nn.LayerNorm(dim)
        self.norm2 = nn.LayerNorm(dim)

        self.ffn = nn.Sequential(
            nn.Linear(dim, dim * 4),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(dim * 4, dim),
            nn.Dropout(dropout)
        )

    def forward(self, x):
        x = x + self.atencao(self.norm1(x))
        x = x + self.ffn(self.norm2(x))
        return x


# =============================================================================
# MENTE TORCH
# =============================================================================

class MenteTorch(nn.Module):

    def __init__(self, id_agente: int, n_entradas: int = 14):
        super().__init__()
        self.id_agente = id_agente
        self.n_entradas = n_entradas

        # ── Embedding inicial ──────────────────────────────────────────────
        self.embedding = nn.Sequential(
            nn.Linear(n_entradas, 128),
            nn.LayerNorm(128),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(128, 256),
            nn.LayerNorm(256),
            nn.GELU(),
        )

        # ── Transformer (curto prazo) ─────────────────────────────────────
        self.transformer = nn.ModuleList([
            BlocoTransformer(256, num_cabecas=8, dropout=0.1)
            for _ in range(6)
        ])

        # ── LSTM (longo prazo, bidirecional) ─────────────────────────────
        self.lstm = nn.LSTM(
            input_size=256,
            hidden_size=128,
            num_layers=2,
            batch_first=True,
            dropout=0.2,
            bidirectional=True
        )
        self.lstm_hidden = None
        self.memoria_longa = deque(maxlen=200)

        # Projeção do LSTM (256 porque bidirecional: 128*2)
        self.proj_lstm = nn.Linear(256, 256)

        # ── Cross-attention ───────────────────────────────────────────────
        self.cross_attention = nn.MultiheadAttention(
            embed_dim=256,
            num_heads=4,
            dropout=0.1,
            batch_first=True
        )

        self.residual_1 = nn.Linear(256, 256)
        self.residual_2 = nn.Linear(256, 128)

        # ── Cabeças por horizonte ─────────────────────────────────────────
        self.cabecas = nn.ModuleList()
        for _ in range(4):                  # micro  (5s–60s)
            self.cabecas.append(self._criar_cabeca('micro'))
        for _ in range(3):                  # intraday (5m–30m)
            self.cabecas.append(self._criar_cabeca('intraday'))
        for _ in range(2):                  # swing  (1h–5h)
            self.cabecas.append(self._criar_cabeca('swing'))
        self.cabecas.append(self._criar_cabeca('position'))  # 1d

        # ── Cabeças auxiliares ────────────────────────────────────────────
        self.cabeca_tendencia = nn.Sequential(
            nn.Linear(256 + N_HORIZONTES, 128),
            nn.LayerNorm(128),
            nn.GELU(),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            nn.GELU(),
            nn.Linear(64, 3),
            nn.Softmax(dim=1)
        )
        self.cabeca_confianca = nn.Sequential(
            nn.Linear(256, 64),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )
        self.cabeca_volatilidade = nn.Sequential(
            nn.Linear(256, 64),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Softplus()
        )
        self.cabeca_regime = nn.Sequential(
            nn.Linear(256, 32),
            nn.ReLU(),
            nn.Linear(32, 4),
            nn.Softmax(dim=1)
        )

        # ── Embeddings de horizonte (aprendíveis) ─────────────────────────
        self.horizon_embeddings = nn.ParameterList([
            nn.Parameter(torch.randn(1, 32) * 0.02)
            for _ in range(N_HORIZONTES)
        ])
        self.proj_embed = nn.Linear(256 + 32, 256)

        # ── Otimizador com scheduler encadeado ───────────────────────────
        # LinearLR faz warmup nos primeiros 200 steps;
        # depois CosineAnnealingLR decai suavemente.
        self.otimizador = torch.optim.AdamW(
            self.parameters(),
            lr=1e-3,
            betas=(0.9, 0.999),
            weight_decay=0.01,
            amsgrad=True
        )
        self._scheduler_warmup = torch.optim.lr_scheduler.LinearLR(
            self.otimizador,
            start_factor=0.1,
            end_factor=1.0,
            total_iters=200
        )
        self._scheduler_cosine = torch.optim.lr_scheduler.CosineAnnealingLR(
            self.otimizador,
            T_max=2000,
            eta_min=5e-5
        )
        self._scheduler = torch.optim.lr_scheduler.SequentialLR(
            self.otimizador,
            schedulers=[self._scheduler_warmup, self._scheduler_cosine],
            milestones=[200]
        )

        # ── Métricas ──────────────────────────────────────────────────────
        # n_acertos[i] / n_erros[i] SÓ são atualizados pelo delayed buffer
        self.n_acertos = [0] * N_HORIZONTES
        self.n_erros   = [0] * N_HORIZONTES
        self.geracao   = 0

        self.memoria_erros     = deque(maxlen=50)
        self.memoria_loss      = deque(maxlen=100)
        self.memoria_gradientes = deque(maxlen=20)

        # ── Estado interno ────────────────────────────────────────────────
        self.ultima_entrada     = None
        self.ultimo_estado_oculto = None
        self.estado_interno     = torch.zeros(1, 256)
        self._ultimos_x_cabecas = None

    # ─────────────────────────────────────────────────────────────────────────
    # PROPRIEDADES
    # ─────────────────────────────────────────────────────────────────────────

    @property
    def accuracy_por_horizonte(self) -> list[float]:
        result = []
        for a, e in zip(self.n_acertos, self.n_erros):
            total = a + e
            result.append(round(a / total, 3) if total > 0 else 0.5)
        return result

    @property
    def accuracy(self) -> float:
        accs = self.accuracy_por_horizonte
        return sum(accs) / len(accs) if accs else 0.5

    @property
    def confidence(self) -> float:
        if not self.memoria_erros:
            return 0.7
        erro_medio = sum(self.memoria_erros) / len(self.memoria_erros)
        return max(0.3, min(0.95, 1 - erro_medio * 2))

    @property
    def learning_stability(self) -> str:
        if not self.memoria_gradientes:
            return "desconhecida"
        grad_medio = sum(self.memoria_gradientes) / len(self.memoria_gradientes)
        if grad_medio < 0.1:
            return "estável"
        elif grad_medio < 0.3:
            return "moderada"
        else:
            return "instável"

    @property
    def loss_medio(self) -> float:
        if not self.memoria_loss:
            return 0.5
        return sum(self.memoria_loss) / len(self.memoria_loss)

    # ─────────────────────────────────────────────────────────────────────────
    # SNAPSHOT
    # ─────────────────────────────────────────────────────────────────────────

    def snapshot(self) -> dict:
        accs = self.accuracy_por_horizonte
        return {
            "geracao":              self.geracao,
            "accuracy_por_horizonte": accs,
            "accuracy_micro":       round(sum(accs[:4]) / 4, 4) if len(accs) >= 4 else 0.5,
            "accuracy_intraday":    round(sum(accs[4:7]) / 3, 4) if len(accs) >= 7 else 0.5,
            "accuracy_swing":       round(sum(accs[7:9]) / 2, 4) if len(accs) >= 9 else 0.5,
            "accuracy_position":    round(accs[9], 4) if len(accs) >= 10 else 0.5,
            "accuracy_media":       round(self.accuracy, 4),
            "loss_medio":           round(self.loss_medio, 6),
            "confidence":           round(self.confidence, 4),
            "learning_stability":   self.learning_stability,
        }

    # ─────────────────────────────────────────────────────────────────────────
    # CRIAÇÃO DE CABEÇAS
    # ─────────────────────────────────────────────────────────────────────────

    def _criar_cabeca(self, tipo: str) -> nn.Module:
        if tipo == 'micro':
            return nn.Sequential(
                nn.Linear(256, 64),
                nn.GELU(),
                nn.Dropout(0.05),
                nn.Linear(64, 16),
                nn.GELU(),
                nn.Linear(16, 1),
                nn.Tanh()
            )
        elif tipo == 'intraday':
            return nn.Sequential(
                nn.Linear(256, 128),
                nn.LayerNorm(128),
                nn.GELU(),
                nn.Dropout(0.1),
                nn.Linear(128, 64),
                nn.GELU(),
                nn.Linear(64, 16),
                nn.GELU(),
                nn.Linear(16, 1),
                nn.Tanh()
            )
        elif tipo == 'swing':
            return nn.Sequential(
                nn.Linear(256, 128),
                nn.LayerNorm(128),
                nn.GELU(),
                nn.Dropout(0.15),
                nn.Linear(128, 64),
                nn.LayerNorm(64),
                nn.GELU(),
                nn.Dropout(0.15),
                nn.Linear(64, 32),
                nn.GELU(),
                nn.Linear(32, 16),
                nn.GELU(),
                nn.Linear(16, 1),
                nn.Tanh()
            )
        else:  # position
            return nn.Sequential(
                nn.Linear(256, 128),
                nn.LayerNorm(128),
                nn.GELU(),
                nn.Dropout(0.2),
                nn.Linear(128, 64),
                nn.LayerNorm(64),
                nn.GELU(),
                nn.Dropout(0.2),
                nn.Linear(64, 32),
                nn.LayerNorm(32),
                nn.GELU(),
                nn.Dropout(0.2),
                nn.Linear(32, 16),
                nn.GELU(),
                nn.Linear(16, 1),
                nn.Tanh()
            )

    # ─────────────────────────────────────────────────────────────────────────
    # FORWARD
    # ─────────────────────────────────────────────────────────────────────────

    def forward(self, entrada: list) -> list[float]:
        if len(entrada) < self.n_entradas:
            entrada = entrada + [0.0] * (self.n_entradas - len(entrada))

        tensor = torch.tensor(entrada[:self.n_entradas], dtype=torch.float32)

        # ── Sequência curto prazo ─────────────────────────────────────────
        if self.ultimo_estado_oculto is None:
            sequencia = tensor.unsqueeze(0).unsqueeze(0)
            self.ultimo_estado_oculto = tensor.clone()
        else:
            estado_anterior = self.ultimo_estado_oculto.unsqueeze(0).unsqueeze(0)
            atual = tensor.unsqueeze(0).unsqueeze(0)
            sequencia = torch.cat([estado_anterior, atual], dim=1)
            if sequencia.shape[1] > 10:
                sequencia = sequencia[:, -10:, :]
            self.ultimo_estado_oculto = tensor.clone()

        # ── Embedding + Transformer ───────────────────────────────────────
        x_curto = self.embedding(sequencia)
        for bloco in self.transformer:
            x_curto = bloco(x_curto)
        x_curto = x_curto.mean(dim=1)  # [1, 256]

        # ── LSTM (memória longa) ──────────────────────────────────────────
        self.memoria_longa.append(x_curto.detach().squeeze(0))

        if len(self.memoria_longa) >= 10:
            estados_recentes = list(self.memoria_longa)[-200:]
            seq_longa = torch.stack(estados_recentes, dim=0).unsqueeze(0)

            if self.lstm_hidden is None:
                lstm_out, self.lstm_hidden = self.lstm(seq_longa)
            else:
                h, c = self.lstm_hidden
                lstm_out, self.lstm_hidden = self.lstm(seq_longa, (h.detach(), c.detach()))

            x_longo = self.proj_lstm(lstm_out[:, -1, :])
        else:
            x_longo = x_curto

        # ── Cross-attention ───────────────────────────────────────────────
        x_curto_3d = x_curto.unsqueeze(1)
        x_longo_3d = x_longo.unsqueeze(1)
        x_cross, _ = self.cross_attention(x_curto_3d, x_longo_3d, x_longo_3d)
        x_cross = x_cross.squeeze(1)

        # ── Combinação ────────────────────────────────────────────────────
        x_combinado = x_curto + x_longo * 0.3 + x_cross * 0.2
        x_combinado = x_combinado + self.residual_1(x_combinado) * 0.3

        self.estado_interno = 0.9 * self.estado_interno + 0.1 * x_combinado.detach()
        self.ultima_entrada = x_combinado.clone()

        # ── Cabeças por horizonte ─────────────────────────────────────────
        saidas = []
        xs_cabecas = []
        for i, cab in enumerate(self.cabecas):
            if i < 4:
                x = x_curto * 0.7 + x_cross * 0.2 + x_longo * 0.1
            elif i < 7:
                x_base = x_curto * 0.4 + x_cross * 0.3 + x_longo * 0.3
                if i == 4:
                    x = x_base + x_curto * 0.15
                elif i == 5:
                    x = x_base + x_longo * 0.15
                else:
                    x = x_base + x_longo * 0.3
            elif i < 9:
                x_base = x_longo * 0.6 + x_cross * 0.3 + x_curto * 0.1
                x = x_base + (x_curto if i == 7 else x_longo) * 0.1
            else:
                x = x_longo * 0.8 + x_cross * 0.2

            emb = self.horizon_embeddings[i] * 3.0
            x = self.proj_embed(torch.cat([x, emb], dim=1))
            x = x + self.residual_1(x) * 0.3

            xs_cabecas.append(x.detach())
            saidas.append(float(cab(x).item()))

        self._ultimos_x_cabecas = xs_cabecas
        return saidas

    # ─────────────────────────────────────────────────────────────────────────
    # APRENDER (batch completo — todos os 10 horizontes de uma vez)
    # ─────────────────────────────────────────────────────────────────────────

    def aprender(self, recompensas: list[float]):
        """
        Treina todas as cabeças de uma vez com recompensas reais.
        Só deve ser chamado pelo crypto.py APÓS o delayed buffer confirmar
        os retornos reais.  Para treinamento parcial (horizonte único),
        use aprender_horizonte().
        """
        if self.ultima_entrada is None or self._ultimos_x_cabecas is None:
            return

        if isinstance(recompensas, (int, float)):
            recompensas = [float(recompensas)] * N_HORIZONTES
        elif isinstance(recompensas, torch.Tensor):
            recompensas = recompensas.detach().flatten().tolist()
        elif not isinstance(recompensas, list):
            return

        if len(recompensas) != N_HORIZONTES:
            return

        if any(math.isnan(r) or math.isinf(r) for r in recompensas):
            return

        self._passo_gradiente(recompensas, list(range(N_HORIZONTES)))

    # ─────────────────────────────────────────────────────────────────────────
    # APRENDER HORIZONTE (treinamento parcial — só a cabeça i)
    # ─────────────────────────────────────────────────────────────────────────

    def aprender_horizonte(self, i: int, recompensa: float):
        """
        Recebe a recompensa REAL de um único horizonte (quando o tempo passou)
        e treina apenas a cabeça correspondente.

        Atualiza n_acertos / n_erros com o dado real.
        """
        if self.ultima_entrada is None or self._ultimos_x_cabecas is None:
            return
        if math.isnan(recompensa) or math.isinf(recompensa):
            return
        if not (0 <= i < N_HORIZONTES):
            return

        self._passo_gradiente([recompensa], [i])

        # Atualiza métricas com sinal real
        x_i = self._ultimos_x_cabecas[i]
        with torch.no_grad():
            pred = float(self.cabecas[i](x_i).item())
        if (pred > 0) == (recompensa > 0):
            self.n_acertos[i] += 1
        else:
            self.n_erros[i] += 1

    # ─────────────────────────────────────────────────────────────────────────
    # PASSO DE GRADIENTE INTERNO
    # ─────────────────────────────────────────────────────────────────────────

    def _passo_gradiente(self, recompensas: list[float], indices: list[int]):
        """
        Executa um passo de otimização nas cabeças indicadas por `indices`.
        `recompensas` deve ter o mesmo comprimento que `indices`.
        """
        self.otimizador.zero_grad()

        x = self.ultima_entrada
        preds_lista = [self.cabecas[i](self._ultimos_x_cabecas[i]) for i in indices]
        preds = torch.cat(preds_lista, dim=1)                        # [1, n]
        alvo  = torch.tensor([recompensas], dtype=torch.float32)     # [1, n]

        if preds.shape != alvo.shape:
            return

        loss_huber = F.smooth_l1_loss(preds, alvo)
        loss_mse   = F.mse_loss(preds, alvo)
        loss_mae   = F.l1_loss(preds, alvo)

        erro_abs = torch.abs(preds - alvo).mean()
        confianca = self.cabeca_confianca(x)
        target_conf = torch.sigmoid(1 - erro_abs).view_as(confianca)
        loss_conf = F.binary_cross_entropy(confianca, target_conf)

        # Consistência temporal só faz sentido com múltiplas cabeças em sequência
        if len(indices) > 1 and all(indices[j] + 1 == indices[j + 1] for j in range(len(indices) - 1)):
            loss_consist = torch.mean((preds[:, 1:] - preds[:, :-1]) ** 2)
        else:
            loss_consist = torch.tensor(0.0)

        loss_vol = self.cabeca_volatilidade(x).mean()

        # Regularização L2 só nas cabeças envolvidas
        loss_reg = sum(
            torch.sum(p ** 2)
            for i in indices[-3:]
            for p in self.cabecas[i].parameters()
        ) * 1e-5

        loss = (loss_huber  * 0.45 +
                loss_mse    * 0.15 +
                loss_mae    * 0.10 +
                loss_conf   * 0.10 +
                loss_consist * 0.10 +
                loss_vol    * 0.05 +
                loss_reg    * 0.05)

        loss.backward()

           # ✅ Verifica e corrige gradientes NaN
        for param in self.parameters():
            if param.grad is not None:
                param.grad = torch.nan_to_num(param.grad, nan=0.0, posinf=1.0, neginf=-1.0)

        grad_norm = torch.nn.utils.clip_grad_norm_(self.parameters(), max_norm=0.3)

        if math.isnan(grad_norm.item()):
            print("[PyTorch] ⚠️ Gradiente NaN detectado! Pulando passo.")
            self.otimizador.zero_grad()
            return


        self.memoria_gradientes.append(grad_norm.item())

        self.otimizador.step()
        self._scheduler.step()

        self.memoria_loss.append(loss.item())
        self.memoria_erros.append(erro_abs.item())
        self.geracao += 1

    # ─────────────────────────────────────────────────────────────────────────
    # PERSISTÊNCIA
    # ─────────────────────────────────────────────────────────────────────────

    def salvar_com_nome(self, caminho_completo: str):
        os.makedirs(os.path.dirname(caminho_completo), exist_ok=True)
        torch.save({
            'model_state_dict':     self.state_dict(),
            'optimizer_state_dict': self.otimizador.state_dict(),
            'scheduler_state_dict': self._scheduler.state_dict(),
            'n_acertos':            self.n_acertos,
            'n_erros':              self.n_erros,
            'geracao':              self.geracao,
            'historico_loss':       list(self.memoria_loss),
            'memoria_erros':        list(self.memoria_erros),
            'estado_interno':       self.estado_interno,
            'versao':               'v3_delayed_reward'
        }, caminho_completo)

    def carregar(self, caminho: str = "data/mentes_pytorch") -> bool:
        arquivo = f"{caminho}/mente_{self.id_agente}.pt"
        if os.path.exists(arquivo):
            try:
                ck = torch.load(arquivo, map_location='cpu')
                self.load_state_dict(ck['model_state_dict'], strict=False)
                self.otimizador.load_state_dict(ck['optimizer_state_dict'])
                try:
                    self.scheduler.load_state_dict(ck['scheduler_state_dict'])
                except Exception:
                    pass
                self.n_acertos    = ck.get('n_acertos',    [0] * N_HORIZONTES)
                self.n_erros      = ck.get('n_erros',      [0] * N_HORIZONTES)
                self.geracao      = ck.get('geracao',      0)
                self.memoria_loss = deque(ck.get('historico_loss', []), maxlen=100)
                self.memoria_erros = deque(ck.get('memoria_erros', []), maxlen=50)
                if 'estado_interno' in ck:
                    self.estado_interno = ck['estado_interno']
                print(f"[PyTorch] Mente {self.id_agente} carregada (estabilidade: {self.learning_stability})")
                return True
            except Exception as e:
                print(f"[PyTorch] Erro ao carregar mente {self.id_agente}: {e}")
        return False

    def para_dict(self) -> dict:
        return {
            "id_agente":            self.id_agente,
            "n_acertos":            self.n_acertos,
            "n_erros":              self.n_erros,
            "geracao":              self.geracao,
            "accuracy_por_horizonte": self.accuracy_por_horizonte,
            "confidence":           self.confidence,
            "learning_stability":   self.learning_stability,
            "tipo":                 "pytorch_v3_delayed_reward"
        }