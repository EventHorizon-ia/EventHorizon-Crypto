import json
from datetime import datetime
import math
import os
import torch
import requests
import random
import urllib.parse 
import time
import threading
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from Software.core.universe_instance import lock_universo
from Software.core.mind_pytorch import MenteTorch, HORIZONTES, N_HORIZONTES
from Software.core.mind_pytorch import DelayedRewardBuffer
from websocket import WebSocketApp

def pegar_todos_precos(tentativas=2):
    """Busca preços via REST API da Binance (mais confiável no HF)"""
    url = "https://api.binance.com/api/v3/ticker/price"
    for _ in range(tentativas):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            return {item["symbol"]: float(item["price"]) for item in data}
        except Exception as e:
            print(f"[CryptoApp] Tentativa falhou: {e}")
            time.sleep(2)
    return {}

# =============================================================================
#  INDICADORES TÉCNICOS
# =============================================================================

def calcular_ema(precos, periodo):
    if len(precos) < periodo:
        return precos[-1] if precos else 0
    k = 2 / (periodo + 1)
    ema = precos[0]
    for p in precos:
        ema = p * k + ema * (1 - k)
    return ema


def calcular_rsi(precos, periodo=14):
    if len(precos) < periodo + 1:
        return 50.0
    gains, losses = [], []
    for i in range(1, len(precos)):
        diff = precos[i] - precos[i - 1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    avg_gain = sum(gains[-periodo:]) / periodo
    avg_loss = sum(losses[-periodo:]) / periodo
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def calcular_bollinger(precos, periodo=20, mult=2.0):
    if len(precos) < periodo:
        return precos[-1], precos[-1], precos[-1]
    janela = precos[-periodo:]
    media = sum(janela) / periodo
    variancia = sum((p - media) ** 2 for p in janela) / periodo
    desvio = math.sqrt(variancia)
    return media + mult * desvio, media, media - mult * desvio


def calcular_atr(candles, periodo=14):
    if len(candles) < 2:
        return 0
    trs = []
    for i in range(1, len(candles)):
        h = candles[i]["high"]
        l = candles[i]["low"]
        pc = candles[i - 1]["close"]
        tr = max(h - l, abs(h - pc), abs(l - pc))
        trs.append(tr)
    janela = trs[-periodo:]
    return sum(janela) / len(janela)


def calcular_macd(precos):
    if len(precos) < 26:
        return 0, 0, 0
    ema12 = calcular_ema(precos, 12)
    ema26 = calcular_ema(precos, 26)
    macd = ema12 - ema26
    return macd, 0, macd


def detectar_regime(precos, candles):
    if len(precos) < 20:
        return "ranging"
    ema9  = calcular_ema(precos, 9)
    ema21 = calcular_ema(precos, 21)
    atr   = calcular_atr(candles) if len(candles) >= 2 else 0
    bb_upper, bb_mid, bb_lower = calcular_bollinger(precos)
    bb_width = (bb_upper - bb_lower) / (bb_mid + 1e-9)
    preco_atual = precos[-1]
    retorno_20 = (preco_atual - precos[-20]) / precos[-20]
    if bb_width > 0.02:
        return "volatile"
    elif ema9 > ema21 and retorno_20 > 0.001:
        return "trend_up"
    elif ema9 < ema21 and retorno_20 < -0.001:
        return "trend_down"
    else:
        return "ranging"


def detectar_padroes_candle(candles):
    if len(candles) < 3:
        return 0
    score = 0
    c0 = candles[-1]
    c1 = candles[-2]
    c2 = candles[-3]
    corpo0 = abs(c0["close"] - c0["open"])
    amplitude0 = c0["high"] - c0["low"] + 1e-9
    sombra_baixa = c0["open"] - c0["low"] if c0["close"] >= c0["open"] else c0["close"] - c0["low"]
    sombra_alta  = c0["high"] - c0["close"] if c0["close"] >= c0["open"] else c0["high"] - c0["open"]
    if sombra_baixa > corpo0 * 2 and sombra_alta < corpo0 * 0.5:
        score += 1.5
    if sombra_alta > corpo0 * 2 and sombra_baixa < corpo0 * 0.5:
        score -= 1.5
    if (c1["close"] < c1["open"] and c0["close"] > c0["open"] and
            c0["open"] < c1["close"] and c0["close"] > c1["open"]):
        score += 2.0
    if (c1["close"] > c1["open"] and c0["close"] < c0["open"] and
            c0["open"] > c1["close"] and c0["close"] < c1["open"]):
        score -= 2.0
    if (c2["close"] > c2["open"] and c1["close"] > c1["open"] and
            c0["close"] > c0["open"] and c1["close"] > c2["close"] and
            c0["close"] > c1["close"]):
        score += 1.5
    if (c2["close"] < c2["open"] and c1["close"] < c1["open"] and
            c0["close"] < c0["open"] and c1["close"] < c2["close"] and
            c0["close"] < c1["close"]):
        score -= 1.5
    return score


# =============================================================================
#  PESOS ADAPTATIVOS
# =============================================================================

class PesosAdaptativos:

    def __init__(self, n_features=12):
        self.n_features = n_features
        self.pesos  = [random.uniform(-0.1, 0.1) for _ in range(n_features)]
        self.bias   = 0.0
        self.lr     = 0.01
        self.decay  = 0.98
        self.bias_decay = 0.995
        self.n_acertos = 0
        self.n_erros   = 0
        self.historico_loss = deque(maxlen=50)
        self.media_retorno  = 0.0
        self.alpha_media    = 0.3
        self.historico_sinais = deque(maxlen=10)

    def debias_target(self, target: float) -> float:
        self.media_retorno = (
            self.alpha_media * target +
            (1 - self.alpha_media) * self.media_retorno
        )
        return target - self.media_retorno

    @property
    def vies_direcional(self) -> float:
        if not self.historico_sinais:
            return 0.5
        return sum(1 for s in self.historico_sinais if s > 0) / len(self.historico_sinais)

    def forward(self, features: list) -> float:
        raw = sum(p * f for p, f in zip(self.pesos, features)) + self.bias
        vies = self.vies_direcional
        if vies > 0.6:
            correcao = -(vies - 0.5) * abs(raw) * 0.6
            raw += correcao
        elif vies < 0.4:
            correcao = (0.5 - vies) * abs(raw) * 0.6
            raw += correcao
        return raw

    def update(self, features: list, target: float) -> float:
        pred = self.forward(features)
        self.historico_sinais.append(pred)
        target_db = self.debias_target(target)
        erro = target_db - pred
        self.historico_loss.append(abs(erro))
        for i in range(min(self.n_features, len(features))):
            self.pesos[i] = self.pesos[i] * self.decay + self.lr * erro * features[i]
        self.bias = self.bias * self.bias_decay + self.lr * erro * 0.05
        return pred

    @property
    def accuracy(self) -> float:
        total = self.n_acertos + self.n_erros
        return self.n_acertos / total if total > 0 else 0.5

    @property
    def loss_medio(self) -> float:
        return sum(self.historico_loss) / len(self.historico_loss) if self.historico_loss else 1.0


# =============================================================================
#  CRYPTO APP
# =============================================================================

class CryptoApp:

    nome = "crypto_app"

    def __init__(self, universo):
        self.universo      = universo
        self.ultimo_update = 0
        self.delay         = 2.0
        self.ativo         = False
        self.ids_cripto    = {}
        self.precos        = {}
        self.rodando_api   = False
        self.timeframe     = 5
        self.loop_thread   = None
        self.buffers: dict[str, DelayedRewardBuffer] = {}
        self._sem_init_mente = threading.Semaphore(1)
        
        self.verificacoes: dict[str, deque] = {}
        self.resultados_verificacao: dict[str, dict] = {}

        self.pesos: dict[str, PesosAdaptativos] = {}
        self.features_anteriores: dict[str, list] = {}
        self.preco_anterior: dict[str, float] = {}

        # ✅ FIX 3: Lock separado para mentes_pytorch (não bloqueia o universo)
        self.mentes_pytorch: dict[str, MenteTorch] = {}
        self._lock_mentes = threading.Lock()

        # ✅ FIX 4: Fila de inicialização assíncrona de mentes
        self._fila_init_mentes: deque = deque()
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="mente_init")

        self.lista_moedas = [
            "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT",
            "SOLUSDT", "DOGEUSDT", "DOTUSDT", "MATICUSDT", "LTCUSDT"
        ]

       # self.carregar_ultimas_moedas()

    # ─────────────────────────────────────────────────────────────────────────
    # INICIALIZAÇÃO ASSÍNCRONA DE MENTES
    # ─────────────────────────────────────────────────────────────────────────

    def _init_mente_async(self, moeda: str, id_agente: int):
        with self._sem_init_mente:
            try:
                mente = MenteTorch(id_agente=id_agente)
                
                # ✅ Tenta carregar do arquivo com nome da MOEDA
                arquivo_moeda = f"data/mentes_pytorch/mente_{moeda}.pt"
                if os.path.exists(arquivo_moeda):
                    try:
                        ck = torch.load(arquivo_moeda, map_location='cpu')
                        mente.load_state_dict(ck['model_state_dict'], strict=False)
                        mente.n_acertos = ck.get('n_acertos', [0]*10)
                        mente.n_erros = ck.get('n_erros', [0]*10)
                        mente.geracao = ck.get('geracao', 0)
                        print(f"[CRYPTO] ♻️ Mente {moeda} RECARREGADA do disco ({mente.geracao} gerações)")
                    except Exception as e:
                        print(f"[CRYPTO] ⚠️ Erro ao carregar {moeda}: {e}")
                
                with self._lock_mentes:
                    self.mentes_pytorch[moeda] = mente
                
                print(f"[CRYPTO] ✅ Mente {moeda} (ID {id_agente}) pronta")
            except Exception as e:
                print(f"[CRYPTO] ❌ Erro: {e}")

    def _garantir_mente(self, moeda: str) -> MenteTorch | None:
        """
        Retorna a mente se já estiver pronta; caso contrário None.
        Não bloqueia — a inicialização acontece em background.
        """
        with self._lock_mentes:
            return self.mentes_pytorch.get(moeda)

    # ─────────────────────────────────────────────────────────────────────────
    # HANDLE
    # ─────────────────────────────────────────────────────────────────────────

    def handle(self, comando):

        if comando == "crypto start":
            self.ativo = True
            self.rodando_api = True
            
            # ⭐ SEMPRE cria uma thread nova (a antiga já morreu ou vai morrer)
            self.loop_thread = threading.Thread(target=self.loop_api, daemon=True)
            self.loop_thread.start()
            
            return ["Crypto app started"]

        if comando == "crypto spawn all":
            return self.spawn_moedas(self.lista_moedas)

        if comando.startswith("crypto spawn"):
            partes = comando.split()
            moedas = [m.upper() for m in partes[2:]]
            self.salvar_ultimas_moedas()  # ✅ FORÇA SALVAR
            return self.spawn_moedas(moedas)

        if comando == "crypto signal":
            return self._gerar_sinais()

        if comando == "crypto stop":
            self.ativo = False
            self.rodando_api = False
            self.universo.mentes.salvar(salvar_modelos=True)
            return ["Crypto app stopped and cleaned"]

        if comando == "crypto clear":
            self.remover_moedas()
            self.universo.mentes.salvar(salvar_modelos=True)
            return ["All coins removed"]

        if comando.startswith("crypto timeframe"):
            try:
                tf = int(comando.split()[2])
                self.timeframe = tf
                return [f"Timeframe set to {tf}s"]
            except:
                return ["Invalid timeframe"]

        if comando == "crypto stats":
            return self._gerar_stats()

        if comando == "refresh":
            return ["refreshed"]

        if comando == "crypto report":
            relatorio = self.gerar_relatorio_desempenho()
            return [json.dumps(relatorio)]

        if comando.startswith("crypto remove"):
            partes = comando.split()
            moedas = [m.upper() for m in partes[2:]]
            removidas = self.remover_moedas_selecionadas(moedas)
            self.salvar_ultimas_moedas()  # ✅ ATUALIZA APÓS REMOVER
            return [f"Removidas: {', '.join(removidas)}" if removidas else "Nenhuma moeda removida"]

        if comando.startswith("crypto "):
            return ["Unknown crypto command"]

        return None
    
    def iniciar_restauracao_async(self):
        """Chame APÓS o loop_api já estar rodando"""
        threading.Thread(target=self._restaurar_moedas_background, daemon=True).start()

    def _restaurar_moedas_background(self):
        time.sleep(3)
        moedas = self._ler_ultimas_moedas_do_disco()
        if moedas:
            print(f"[CRYPTO] 🔄 Restaurando moedas: {moedas}")
            self.spawn_moedas(moedas)

    def _ler_ultimas_moedas_do_disco(self):
        try:
            with open("data/ultimas_moedas.json", "r") as f:
                return json.load(f)
        except:
            return []

    # ─────────────────────────────────────────────────────────────────────────
    # UPDATE PRINCIPAL
    # ─────────────────────────────────────────────────────────────────────────

    def update(self):
        if not self.ativo:
            return

        agora = time.time()
        if agora - self.ultimo_update < self.delay:
            return
        self.ultimo_update = agora

        dados_ativos = {}
        for moeda, id_dado in self.ids_cripto.items():
            dado = next((d for d in self.universo.dados if d["id"] == id_dado), None)
            if dado is not None:
                dados_ativos[moeda] = dado

        clusters_universo = self.universo.detectar_clusters()
        cluster_por_id = {}
        for cluster in clusters_universo:
            for d in cluster:
                cluster_por_id[d["id"]] = cluster

        # ✅ FIX 6: Coleta tudo que precisar do PyTorch FORA do lock_universo.
        # O update() é chamado de dentro do lock — então separamos as etapas:
        # (a) calcula indicadores e monta features (dentro do lock, sem PyTorch)
        # (b) roda forward/aprender de cada mente (fora do lock)
        # Como update() já é chamado com o lock ativo em loop_api,
        # garantimos que o PyTorch nunca segure o lock_universo.
        dados_para_pytorch = []

        for moeda, dado in dados_ativos.items():
            preco = self.precos.get(moeda)
            if preco is None:
                continue

            dado["history"].append({"time": int(time.time()), "price": preco})
            if len(dado["history"]) > 200:
                dado["history"].pop(0)

            precos = [p["price"] for p in dado["history"]]

            if not isinstance(precos, list):
                precos = []

            if len(precos) < 26:
                dado["price"] = preco
                continue

            # ── Candles ───────────────────────────────────────────────────────
            if "candles" not in dado:
                dado["candles"] = []

            atual_time = int(time.time())
            candle_time = atual_time - (atual_time % self.timeframe)

            if len(dado["candles"]) == 0 or dado["candles"][-1]["time"] != candle_time:
                # ⭐ NOVA VELA: começa com valores normais, SEM SPREAD ARTIFICIAL
                dado["candles"].append({
                    "time":  candle_time,
                    "open":  preco,
                    "high":  preco,
                    "low":   preco,
                    "close": preco
                })
            else:
                c = dado["candles"][-1]
                # ⭐ ATUALIZA com valores reais de tick
                c["high"] = max(c["high"], preco)
                c["low"]  = min(c["low"],  preco)
                c["close"] = preco
                
                # ⭐ CORREÇÃO: NÃO FORÇAR SPREAD ARTIFICIAL!
                
            
                # ✅ Substitua por: apenas garantir que close esteja sempre entre high/low
                c = dado["candles"][-1]
                c["high"] = max(c["high"], preco, c["open"], c["close"])
                c["low"] = min(c["low"], preco, c["open"], c["close"])
                c["close"] = preco

            if len(dado["candles"]) > 200:  # ⭐ Reduzido de 300 para 200
                dado["candles"].pop(0)

            candles = dado["candles"]

            ema9        = calcular_ema(precos, 9)
            ema21       = calcular_ema(precos, 21)
            ema50       = calcular_ema(precos, 50) if len(precos) >= 50 else ema21
            rsi         = calcular_rsi(precos)
            macd, _, _  = calcular_macd(precos)
            atr         = calcular_atr(candles)
            bb_upper, bb_mid, bb_lower = calcular_bollinger(precos)

            retorno    = (preco - precos[-2]) / precos[-2]
            retorno_5  = (preco - precos[-5]) / precos[-5]
            retorno_10 = (preco - precos[-10]) / precos[-10] if len(precos) >= 10 else 0

            regime       = detectar_regime(precos, candles)
            padrao_score = detectar_padroes_candle(candles)

            bb_pos      = (preco - bb_mid) / (bb_upper - bb_lower + 1e-9)
            vol_recente = atr / (preco + 1e-9)

            memoria_score = self.universo.score_memoria(dado)

            sync_score    = 0.0
            minha_cluster = cluster_por_id.get(dado["id"], [])
            for outro_dado in minha_cluster:
                if outro_dado["id"] == dado["id"]:
                    continue
                sync        = self.universo.sincronizacao(dado, outro_dado)
                sinal_outro = outro_dado.get("previsao", 0)
                sync_score += sync * sinal_outro * 0.3

            agora_dt = datetime.now()
            hora = agora_dt.hour
            minuto = agora_dt.minute
            segundo = agora_dt.second
            tempo_segundos = (hora * 3600 + minuto * 60 + segundo)
            ciclo_dia = (tempo_segundos / 86400) * 2 * math.pi
            hora_seno = math.sin(ciclo_dia)
            hora_cosseno = math.cos(ciclo_dia)
            dia_semana = agora_dt.weekday()
            dia_seno = math.sin((dia_semana / 7) * 2 * math.pi)
            dia_cosseno = math.cos((dia_semana / 7) * 2 * math.pi)

            features = [
                retorno * 100,
                retorno_5 * 100,
                retorno_10 * 100,
                (ema9 - ema21) / (preco + 1e-9) * 100,
                (rsi - 50) / 50,
                macd / (preco + 1e-9) * 1000,
                bb_pos,
                vol_recente * 100,
                padrao_score / 2,
                memoria_score,
                sync_score,
                self.universo.memoria_global["delta_energia"] * 0.01,
                hora_seno,
                dia_seno,
            ]

            if moeda not in self.pesos:
                self.pesos[moeda] = PesosAdaptativos(n_features=12)

            pesos = self.pesos[moeda]

            if moeda in self.features_anteriores and moeda in self.preco_anterior:
                target = (preco - self.preco_anterior[moeda]) / self.preco_anterior[moeda] * 100
                pred_anterior = pesos.update(self.features_anteriores[moeda], target)
                if (pred_anterior > 0) == (target > 0):
                    pesos.n_acertos += 1
                else:
                    pesos.n_erros += 1

            self.features_anteriores[moeda] = features
            self.preco_anterior[moeda]       = preco

            energia_cluster = sum(d["energia"] for d in minha_cluster if d["id"] != dado["id"])
            score_universo  = self.universo.forward(
                dado,
                energia_outro=energia_cluster if energia_cluster > 0 else features[0],
                distancia=features[3] * 100
            )

            confianca_regime = {
                "trend_up":   0.9,
                "trend_down": 0.9,
                "ranging":    0.5,
                "volatile":   0.3,
            }.get(regime, 0.7)

            score_pesos = pesos.forward(features)

            # ✅ FIX 7: Pega mente sem bloquear (retorna None se ainda carregando)
            mente = self._garantir_mente(moeda)

            # No update(), substitua esta parte:

            if mente is not None:
                preds_raw = mente.forward(features)
                preds_percentual = [p * 5.0 for p in preds_raw]
                preds_para_verificar = preds_percentual.copy()  # VALORES PUROS DA REDE

                # ✅ Proteção contra NaN
    
                tem_nan = False
                for i, val in enumerate(preds_percentual):
                    if math.isnan(val) or math.isinf(val):
                        preds_percentual[i] = 0.0  # Substitui NaN por 0
                        tem_nan = True

                if tem_nan:
                    print(f"[{moeda}] ⚠️ NaN detectado nas previsões! Substituído por 0.")
                    # Opcional: recarrega o modelo do disco para recuperar
                    if moeda in self.mentes_pytorch and self.mentes_pytorch[moeda] is not None:
                        arquivo = f"data/mentes_pytorch/mente_{moeda}.pt"
                        if os.path.exists(arquivo):
                            try:
                                self.mentes_pytorch[moeda].carregar()
                                print(f"[{moeda}] 🔄 Modelo recarregado do disco (recuperação de NaN)")
                            except:
                                pass
                # ✅ DELAYED REWARD BUFFER: aprendizado GENUÍNO com recompensa REAL
                if moeda not in self.buffers:
                    self.buffers[moeda] = DelayedRewardBuffer(HORIZONTES, self.timeframe)

                # ✅ Registra SEMPRE (toda iteração)
                self.buffers[moeda].registrar(time.time(), preds_percentual.copy(), preco)

                # ✅ Coleta SEMPRE
                # ✅ Coleta recompensas maduras
                recompensas_maduras = self.buffers[moeda].coletar_maduras(time.time(), preco)

                if recompensas_maduras:
                    # Junta todas as recompensas maduras
                    recompensas_array = [0.0] * N_HORIZONTES
                    for i, rec in recompensas_maduras:
                        recompensas_array[i] = rec
                    
                    # Treina UMA VEZ com todas as recompensas
                    try:
                        mente.aprender(recompensas_array)
                    except Exception as e:
                        print(f"[PyTorch] Erro no aprendizado: {e}")
                # ✅ VERIFICAÇÃO REAL POR HORIZONTE
                if not hasattr(self, 'verificacoes'):
                    self.verificacoes = {}
                    self.resultados_verificacao = {}

                if moeda not in self.verificacoes:
                    self.verificacoes[moeda] = deque(maxlen=5000)
                    self.resultados_verificacao[moeda] = {
                        h: {"acertos": 0, "erros": 0, "total": 0} 
                        for h in HORIZONTES
                    }

                # Salva snapshot atual para verificar depois
                self.verificacoes[moeda].append({
                    "time": int(time.time()),
                    "price": preco,
                    "preds": preds_para_verificar,  # Usa os valores FINAIS (após jitter + EMA)
                })

                # Verifica previsões passadas
                agora_ts = int(time.time())
                resultados = self.resultados_verificacao[moeda]
                para_remover = []

                for v in self.verificacoes[moeda]:
                    tempo_passado = agora_ts - v["time"]
                    
                    for i, horizonte in enumerate(HORIZONTES):
                        chave = f"_vrf_{i}"
                        if tempo_passado >= horizonte and not v.get(chave):
                            # Preço alvo: busca o preço real no momento do horizonte
                            preco_alvo = None
                            for v2 in self.verificacoes[moeda]:
                                if abs(v2["time"] - (v["time"] + horizonte)) <= self.timeframe * 2:
                                    preco_alvo = v2["price"]
                                    break
                            
                            if preco_alvo is None:
                                preco_alvo = preco  # Fallback
                            
                            direcao_prevista = 1 if v["preds"][i] > 0 else -1
                            direcao_real = 1 if preco_alvo > v["price"] else -1
                            
                            if direcao_prevista == direcao_real:
                                resultados[horizonte]["acertos"] += 1
                            else:
                                resultados[horizonte]["erros"] += 1
                            resultados[horizonte]["total"] += 1
                            
                            v[chave] = True
                    
                    # Remove se todos horizontes verificados ou > 2 dias
                    todos_vrf = all(v.get(f"_vrf_{i}") for i in range(len(HORIZONTES)))
                    if todos_vrf or tempo_passado > 172800:
                        para_remover.append(v)

                for v in para_remover:
                    try:
                        self.verificacoes[moeda].remove(v)
                    except ValueError:
                        pass

                # Log a cada 30 atualizações
                if not hasattr(self, '_log_vrf_counter'):
                    self._log_vrf_counter = 0
                self._log_vrf_counter += 1

                if self._log_vrf_counter % 30 == 0:
                    print(f"\n📊 [ACURÁCIA REAL {moeda}]")
                    print(f"   {'Horizonte':<8} {'Acurácia':<10} {'Acertos':<8} {'Total'}")
                    print(f"   {'-'*40}")
                    for h in HORIZONTES:
                        r = resultados[h]
                        if r["total"] > 0:
                            acc = r["acertos"] / r["total"] * 100
                            bar = "█" * int(acc / 10) + "░" * (10 - int(acc / 10))
                            print(f"   {f'{h}s':<8} {bar} {acc:5.1f}%  ({r['acertos']}/{r['total']})")
                        else:
                            print(f"   {f'{h}s':<8} {'⌛ aguardando...'}")

                # 🔍 LOG 1: Valores brutos da rede neural
                print(f"\n{'='*60}")
                print(f"🔍 [DEBUG {moeda}] Valores BRUTOS da rede (após ×5.0):")
                for i, h in enumerate(HORIZONTES):
                    print(f"   {h}s: {preds_percentual[i]:.6f}")

            

                # 🔍 LOG 3: Após EMA
                if not hasattr(self, '_historico_predicoes'):
                    self._historico_predicoes: dict[str, dict] = {}

                if moeda not in self._historico_predicoes:
                    self._historico_predicoes[moeda] = {
                        'swing_ema': [0.0, 0.0],
                        'position_ema': 0.0,
                    }

                alpha_swing = 0.1
                for j in range(2):
                    old_val = self._historico_predicoes[moeda]['swing_ema'][j]
                    self._historico_predicoes[moeda]['swing_ema'][j] = (
                        alpha_swing * preds_percentual[7 + j] + 
                        (1 - alpha_swing) * self._historico_predicoes[moeda]['swing_ema'][j]
                    )
                    new_val = self._historico_predicoes[moeda]['swing_ema'][j]
                    preds_percentual[7 + j] = new_val
                    print(f"🔍 [DEBUG {moeda}] EMA swing[{j}]: {old_val:.6f} → {new_val:.6f} (raw: {preds_percentual[7+j]:.6f})")

                alpha_position = 0.05
                old_pos = self._historico_predicoes[moeda]['position_ema']
                self._historico_predicoes[moeda]['position_ema'] = (
                    alpha_position * preds_percentual[9] + 
                    (1 - alpha_position) * self._historico_predicoes[moeda]['position_ema']
                )
                preds_percentual[9] = self._historico_predicoes[moeda]['position_ema']
                print(f"🔍 [DEBUG {moeda}] EMA position: {old_pos:.6f} → {self._historico_predicoes[moeda]['position_ema']:.6f}")

                print(f"\n🔍 [DEBUG {moeda}] Valores FINAIS enviados ao frontend:")
                for i, h in enumerate(HORIZONTES):
                    print(f"   {h}s: {preds_percentual[i]:.6f}")
                print(f"{'='*60}\n")

                # ✅ O resto continua igual daqui pra baixo
                previsao = preds_percentual[0]

                # ✅ NOVO: Salva TODOS os horizontes dinamicamente
                # Mapeia HORIZONTES para nomes de campo
                for i, horizonte in enumerate(HORIZONTES):
                    nome_campo = f"previsao_{horizonte}s"
                    if i < len(preds_percentual):
                        dado[nome_campo] = preds_percentual[i]
                
                # ✅ NOVO: Salva array completo de predições
                dado["predicoes_array"] = preds_percentual
                
                # ✅ NOVO: Calcula sinal consolidado
                curto = preds_percentual[:4] if len(preds_percentual) >= 4 else preds_percentual
                medio = preds_percentual[4:7] if len(preds_percentual) >= 7 else []
                longo = preds_percentual[7:] if len(preds_percentual) >= 8 else []
                
                media_curto = sum(curto) / len(curto) if curto else 0
                media_medio = sum(medio) / len(medio) if medio else media_curto
                media_longo = sum(longo) / len(longo) if longo else media_curto
                
                # Só gera sinal forte se todos os prazos concordam
                if (media_curto > 0.1 and media_medio > 0.05 and media_longo > 0) or \
                (media_curto < -0.1 and media_medio < -0.05 and media_longo < 0):
                    previsao = media_curto * 1.5  # Sinal amplificado quando há consenso
                else:
                    previsao = media_curto * 0.5  # Sinal reduzido quando há divergência
                
                dado["consenso_curto"] = round(media_curto, 4)
                dado["consenso_medio"] = round(media_medio, 4)
                dado["consenso_longo"] = round(media_longo, 4)
                
                acc_por_horizonte = mente.accuracy_por_horizonte
                # Média ponderada: horizontes mais longos têm menos peso na confiança inicial
                confianca_pytorch = (
                    sum(acc_por_horizonte[:4]) / 4 * 0.6 +  # Curto prazo: 60% do peso
                    sum(acc_por_horizonte[4:7]) / 3 * 0.3 +  # Médio prazo: 30%
                    sum(acc_por_horizonte[7:]) / 3 * 0.1      # Longo prazo: 10%
                ) * 100 if len(acc_por_horizonte) >= 10 else acc_por_horizonte[0] * 100

            if abs(previsao) > 2.0 and len(minha_cluster) > 1:
                for outro_dado in minha_cluster:
                    if outro_dado["id"] == dado["id"]:
                        continue
                    sync = self.universo.sincronizacao(dado, outro_dado)
                    if sync > 0.4:
                        energia_pulso = min(dado["energia"] * 0.05, 0.3)
                        self.universo.enviar_pulso(dado["id"], outro_dado["id"], energia=energia_pulso)

            media_atual    = (preco + precos[-2]) / 2
            media_anterior = (precos[-2] + precos[-3]) / 2
            direcao_real   = 1 if media_atual > media_anterior else -1
            acertou   = (previsao > 0) == (direcao_real > 0)
            confianca = min(abs(previsao), 1.0)
            recompensa = (confianca if acertou else -confianca) * 2.0


            # SQL
            try:
                from Software.core.mind_sql import get_banco_sql
                banco_sql = get_banco_sql()
                banco_sql.registrar_performance(
                    mente_id=dado["id"],
                    symbol=moeda,
                    previsao=previsao,
                    preco_atual=preco,
                    direcao=1 if previsao > 0 else -1,
                    acertou=acertou,
                    reward=recompensa,
                    loss=abs(previsao - (1 if acertou else -1)) * 0.1,
                    regime=regime
                )
            except Exception as e:
                print(f"[SQL] Erro ao salvar performance: {e}")

            taxa = 0.15 if acertou else 0.25
            dado["energia"] += recompensa * taxa
            dado["energia"]  = max(0.5, min(10.0, dado["energia"]))
            if dado.get("tipo") == "crypto":
                dado["energia"] = max(5.0, min(10.0, dado["energia"]))

            print(f"[{moeda}]: acertou={acertou}, energia={dado['energia']:.2f}")

            dado["previsao"] = previsao
            dado["regime"]   = regime
            dado["rsi"]      = round(rsi, 2)
            dado["atr"]      = round(atr, 4)
            dado["bb_pos"]   = round(bb_pos, 3)
            dado["accuracy"] = round(pesos.accuracy, 3)
            dado["ema9"]     = ema9
            dado["ema21"]    = ema21
            dado["sync"]     = round(sync_score, 3)
            dado["price"]    = preco
            dado["delta"]    = preco - precos[-2]

        

    # ─────────────────────────────────────────────────────────────────────────
    # SINAIS
    # ─────────────────────────────────────────────────────────────────────────

    def _gerar_sinais(self):
        sinais = []
        for moeda, id_dado in self.ids_cripto.items():
            dado = next((d for d in self.universo.dados if d["id"] == id_dado), None)
            if dado is None:
                continue
            energia  = dado.get("energia", 0)
            previsao = dado.get("previsao", 0)
            regime   = dado.get("regime", "?")
            accuracy = dado.get("accuracy", 0)
            rsi      = dado.get("rsi", 50)
            if previsao > 30:
                direcao = "STRONG BUY 🚀"
            elif previsao > 10:
                direcao = "BUY 📈"
            elif previsao < -30:
                direcao = "STRONG SELL 💥"
            elif previsao < -10:
                direcao = "SELL 📉"
            else:
                direcao = "HOLD ⏸"
            sinais.append((moeda, energia, previsao, direcao, regime, accuracy, rsi))
        sinais.sort(key=lambda x: abs(x[2]), reverse=True)
        resposta = ["📊 CRYPTO SIGNAL", ""]
        for moeda, energia, previsao, direcao, regime, accuracy, rsi in sinais:
            resposta.append(
                f"{moeda:10} | {direcao:18} | "
                f"score: {previsao:+.2f} | "
                f"acc: {accuracy:.0%} | "
                f"RSI: {rsi:.0f} | "
                f"regime: {regime}"
            )
        return resposta

    def _gerar_stats(self):
        linhas = ["📈 CRYPTO STATS", ""]
        for moeda, pesos in self.pesos.items():
            linhas.append(
                f"{moeda:10} | acc: {pesos.accuracy:.1%} | "
                f"loss: {pesos.loss_medio:.4f} | "
                f"ticks: {pesos.n_acertos + pesos.n_erros}"
            )
        return linhas if len(linhas) > 2 else ["Sem dados ainda"]

    # ─────────────────────────────────────────────────────────────────────────
    # SPAWN
    # ─────────────────────────────────────────────────────────────────────────

    def spawn_moedas(self, moedas):
        """
        🧠 SISTEMA DE MOEDAS PERSISTENTES
        - Se a moeda já existe no universo → reutiliza
        - Se existe arquivo .pt salvo → recarrega com aprendizado anterior
        - Se não existe nada → cria do zero
        - Remove só some do frontend, aprendizado fica salvo no disco
        """
        inicio = time.time()
        
        # Limpa IDs órfãos (dados que não existem mais no universo)
        self.ids_cripto = {
            m: id_d
            for m, id_d in self.ids_cripto.items()
            if any(d["id"] == id_d for d in self.universo.dados)
        }

        print(f"[CRYPTO] 🔄 Buscando preços de todas as moedas...")
        todos_precos = pegar_todos_precos()

        if not todos_precos:
            return ["Erro ao buscar preços da Binance"]

        criados = []       # Moedas totalmente novas
        reutilizados = []  # Já estão no universo
        recarregados = []  # Já tinham arquivo .pt salvo

        for moeda in moedas:
            # ═══════════════════════════════════════════
            # PASSO 1: Já existe no universo?
            # ═══════════════════════════════════════════
            agente_existente = None
            for dado in self.universo.dados:
                if dado.get("symbol") == moeda and dado.get("tipo") == "crypto":
                    agente_existente = dado
                    break

            if agente_existente:
                id_agente = agente_existente["id"]
                self.ids_cripto[moeda] = id_agente

                # Garante que a mente está carregada
                with self._lock_mentes:
                    ja_tem = moeda in self.mentes_pytorch and self.mentes_pytorch[moeda] is not None

                if not ja_tem:
                    with self._lock_mentes:
                        self.mentes_pytorch[moeda] = None
                    self._executor.submit(self._init_mente_async, moeda, id_agente)

                reutilizados.append(f"{moeda} → ID {id_agente} (já ativa)")
                print(f"[CRYPTO] ✅ {moeda} já está ativa no universo")
                continue

            # ═══════════════════════════════════════════
            # PASSO 2: Existe arquivo .pt salvo no disco?
            # ═══════════════════════════════════════════
            arquivo_pt = f"data/mentes_pytorch/mente_{moeda}.pt"
            tem_backup = os.path.exists(arquivo_pt)
            
            preco = todos_precos.get(moeda)
            if preco is None:
                print(f"[CRYPTO] ❌ {moeda} - preço não encontrado na Binance")
                continue

            # Cria o agente no universo (comum aos passos 2 e 3)
            dado = self.universo.criar_dado(
                tipo="energetico",
                pos=[preco / 1000, 300 + random.uniform(-50, 50)]
            )
            dado["history"]  = [{"time": int(time.time()), "price": preco}]
            dado["symbol"]   = moeda
            dado["price"]    = preco
            dado["delta"]    = 0.0
            dado["tipo"]     = "crypto"
            dado["energia"]  = min(10, max(3, math.log(preco + 1)))
            dado["previsao"] = 0.0
            dado["regime"]   = "ranging"
            dado["accuracy"] = 0.5
            dado["rsi"]      = 50.0
            dado["estado"]   = [
                random.uniform(0, 2 * math.pi),
                random.uniform(0.05, 0.3),
                random.uniform(0.6, 0.95)
            ]
            dado["memoria"]  = [{"tipo": "spawn_crypto", "preco_inicial": preco}]

            id_agente = dado["id"]
            self.ids_cripto[moeda] = id_agente
            self.pesos[moeda] = PesosAdaptativos()

            # Inicia carregamento da mente em background
            with self._lock_mentes:
                self.mentes_pytorch[moeda] = None
            self._executor.submit(self._init_mente_async, moeda, id_agente)

            if tem_backup:
                recarregados.append(f"{moeda} → ID {id_agente} @ ${preco:,.2f} (🧠 aprendizado restaurado)")
                print(f"[CRYPTO] ♻️ {moeda} recarregada do disco com aprendizado anterior")
            else:
                criados.append(f"{moeda} → ID {id_agente} @ ${preco:,.2f} (🆕 nova)")
                print(f"[CRYPTO] 🆕 {moeda} criada do zero (primeira vez)")

        # ═══════════════════════════════════════════
        # Monta resposta bonita
        # ═══════════════════════════════════════════
        resposta = []
        
        if recarregados:
            resposta.append("♻️ MOEDAS RECARREGADAS (aprendizado mantido do disco):")
            resposta.extend(recarregados)
        
        if reutilizados:
            resposta.append("✅ MOEDAS JÁ ATIVAS (nada foi alterado):")
            resposta.extend(reutilizados)
        
        if criados:
            resposta.append("🆕 MOEDAS NOVAS (primeira vez treinando):")
            resposta.extend(criados)

        tempo_total = time.time() - inicio
        print(f"[CRYPTO] ✅ spawn concluído em {tempo_total:.1f}s")
        print(f"[CRYPTO]    ♻️ {len(recarregados)} recarregadas | ✅ {len(reutilizados)} ativas | 🆕 {len(criados)} novas")

        return resposta if resposta else ["Nenhuma moeda carregada"]

    # ─────────────────────────────────────────────────────────────────────────
    # REMOÇÃO
    # ─────────────────────────────────────────────────────────────────────────

    def remover_moedas(self):
        print(f"[CRYPTO] ids_cripto ANTES: {list(self.ids_cripto.keys())}")

        if not self.ids_cripto:
            for dado in self.universo.dados:
                if dado.get("tipo") == "crypto":
                    self.ids_cripto[dado.get("symbol", "unknown")] = dado["id"]

        ids_para_remover = set(self.ids_cripto.values())
        novos_dados = [d for d in self.universo.dados if d["id"] not in ids_para_remover]
        self.universo.dados = novos_dados

        self.ids_cripto.clear()
        self.pesos.clear()
        self.features_anteriores.clear()
        self.preco_anterior.clear()
        self.precos.clear()
        with self._lock_mentes:
            self.mentes_pytorch.clear()

        print(f"[CRYPTO] Removidas {len(ids_para_remover)} moedas. Restam {len(self.universo.dados)} dados.")

    def remover_moedas_selecionadas(self, moedas_para_remover):
        removidas = []
        ids_para_remover = set()

        for moeda in moedas_para_remover:
            if moeda in self.ids_cripto:
                ids_para_remover.add(self.ids_cripto[moeda])
                removidas.append(moeda)
            else:
                for dado in self.universo.dados:
                    if dado.get("symbol") == moeda and dado.get("tipo") == "crypto":
                        ids_para_remover.add(dado["id"])
                        removidas.append(moeda)
                        self.ids_cripto[moeda] = dado["id"]
                        break

        if ids_para_remover:
            self.universo.dados = [d for d in self.universo.dados if d["id"] not in ids_para_remover]
            for moeda in removidas:
                self.ids_cripto.pop(moeda, None)
                self.pesos.pop(moeda, None)
                self.features_anteriores.pop(moeda, None)
                self.preco_anterior.pop(moeda, None)
                self.precos.pop(moeda, None)
                with self._lock_mentes:
                    self.mentes_pytorch.pop(moeda, None)

        return removidas

    # ─────────────────────────────────────────────────────────────────────────
    # RELATÓRIOS / STATS
    # ─────────────────────────────────────────────────────────────────────────

    def gerar_relatorio_desempenho(self):
        relatorio = []
        for moeda, id_dado in self.ids_cripto.items():
            mente_pt = self._garantir_mente(moeda)
            if mente_pt is not None:
                acertos = mente_pt.n_acertos[0] if mente_pt.n_acertos else 0
                erros   = mente_pt.n_erros[0]   if mente_pt.n_erros   else 0
                total   = acertos + erros
                acuracia = (acertos / total * 100) if total > 0 else 0
                confianca = min(100, acuracia)
                categoria = "recommended" if acuracia >= 55 else ("bad" if acuracia < 45 else "learning")
                relatorio.append({
                    "symbol": moeda, "acertos": acertos, "erros": erros,
                    "total": total, "acuracia": round(acuracia, 1),
                    "confianca": round(confianca, 1), "categoria": categoria,
                    "id": id_dado, "tipo": "pytorch_multi"
                })
            else:
                mente = self.universo.mentes.obter(id_dado)
                if mente is None:
                    continue
                total    = mente.n_acertos + mente.n_erros
                acuracia = (mente.n_acertos / total * 100) if total > 0 else 0
                confianca = min(100, acuracia)
                categoria = "recommended" if acuracia >= 55 else ("bad" if acuracia < 45 else "learning")
                relatorio.append({
                    "symbol": moeda, "acertos": mente.n_acertos, "erros": mente.n_erros,
                    "total": total, "acuracia": round(acuracia, 1),
                    "confianca": round(confianca, 1), "categoria": categoria,
                    "id": id_dado, "tipo": "classic"
                })
        relatorio.sort(key=lambda x: x["acuracia"], reverse=True)
        return relatorio

    def fetchAllAccuracies(self):
        cache = {}
        for moeda, id_dado in self.ids_cripto.items():
            mente = self._garantir_mente(moeda)
            if mente is not None:
                acertos = mente.n_acertos[0] if mente.n_acertos else 0
                erros   = mente.n_erros[0]   if mente.n_erros   else 0
                total   = acertos + erros
                acuracia = (acertos / total * 100) if total > 0 else 0
                cache[moeda] = {"acuracia": round(acuracia, 1), "acertos": acertos, "total": total}
            else:
                mente_cls = self.universo.mentes.obter(id_dado)
                if mente_cls:
                    total    = mente_cls.n_acertos + mente_cls.n_erros
                    acuracia = (mente_cls.n_acertos / total * 100) if total > 0 else 0
                    cache[moeda] = {"acuracia": round(acuracia, 1),
                                    "acertos": mente_cls.n_acertos, "total": total}
                else:
                    cache[moeda] = {"acuracia": 0, "acertos": 0, "total": 0}
        return cache

    def carregar_ultimas_moedas(self):
        try:
            import os
            arquivo = "data/ultimas_moedas.json"
            if os.path.exists(arquivo):
                with open(arquivo, "r") as f:
                    moedas = json.load(f)
                if moedas:
                    print(f"[CRYPTO] Carregando últimas moedas: {moedas}")
                    self.spawn_moedas(moedas)
                return moedas
        except Exception as e:
            print(f"[CRYPTO] Erro ao carregar últimas moedas: {e}")
        return []

    def salvar_ultimas_moedas(self):
        try:
            import os
            os.makedirs("data", exist_ok=True)
            with open("data/ultimas_moedas.json", "w") as f:
                json.dump(list(self.ids_cripto.keys()), f)
        except Exception as e:
            print(f"[CRYPTO] Erro ao salvar últimas moedas: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # LOOP API
    # ─────────────────────────────────────────────────────────────────────────

    def loop_api(self):
        print("[CRYPTO] 🔥 loop_api INICIADO")
        ultimo_salvar = time.time()

        while self.rodando_api:
            try:
                # ✅ FIX 11: Busca preços FORA do lock_universo
                todos_precos = pegar_todos_precos()
                if todos_precos:
                    for moeda in list(self.ids_cripto.keys()):
                        preco = todos_precos.get(moeda)
                        if preco:
                            self.precos[moeda] = preco
                    print(f"[CRYPTO] ✅ Preços atualizados")
                else:
                    print("[CRYPTO] ❌ Erro ao buscar preços")

                # ✅ FIX 12: Lock cobrindo apenas a seção de leitura/escrita de dados.
                # O aprendizado PyTorch (dados_para_pytorch) ocorre em update()
                # depois que o loop de dados termina — mas ainda dentro do lock.
                # Para remover totalmente o PyTorch do lock, mova o aprendizado
                # para cá fora, separando forward() (ainda precisa do dado) de
                # aprender() (não precisa do dado). Já fizemos isso no update().
                with lock_universo:
                    self.update()

                agora = time.time()
                if agora - ultimo_salvar > 60:
                    print("[CRYPTO] 💾 Salvando modelos .pt...")
                    # ✅ Salva mentes em background para não bloquear o loop
                    self._executor.submit(self._salvar_mentes_background)
                    ultimo_salvar = agora

            except Exception as e:
                print(f"[CryptoApp] loop_api erro: {e}")

            time.sleep(self.delay)

    # Encontre a moeda pelo ID e salve com o nome dela
    def _salvar_mentes_background(self):
        try:
            with self._lock_mentes:
                mentes_snapshot = dict(self.mentes_pytorch)
            
            # Mapa reverso: id → symbol
            id_para_simbolo = {v: k for k, v in self.ids_cripto.items()}

            self.salvar_ultimas_moedas()
            self.salvar_resultados_verificacao()
            
            for moeda, mente in mentes_snapshot.items():
                if mente is not None:
                    try:
                        # Salva com o nome da MOEDA, não do ID
                        mente.salvar_com_nome(f"data/mentes_pytorch/mente_{moeda}.pt")
                    except Exception as e:
                        print(f"[CRYPTO] Erro ao salvar {moeda}: {e}")
            
            self.salvar_resultados_verificacao()
            print("[CRYPTO] 💾 Mentes salvas")
        except Exception as e:
            print(f"[CRYPTO] Erro: {e}")

    def salvar_resultados_verificacao(self):
        """Salva os resultados de verificação em JSON"""
        if not hasattr(self, 'resultados_verificacao'):
            return
    
        os.makedirs("data/verificacoes", exist_ok=True)
        
        for moeda, resultados in self.resultados_verificacao.items():
            arquivo = f"data/verificacoes/{moeda}.json"
            with open(arquivo, "w") as f:
                # Converte as chaves para string (JSON não aceita int como chave)
                resultados_str = {str(k): v for k, v in resultados.items()}
                json.dump(resultados_str, f, indent=2)