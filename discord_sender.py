# discord_sender.py  v1
# ─────────────────────────────────────────────────────────────────────────────
# Envia sinais de trading para Discord via Webhook, com mensagens geradas
# dinamicamente pela API Groq (llama-3.1-8b-instant).
#
# Integração com o SignalEngine existente:
#   from discord_sender import DiscordSender
#   discord = DiscordSender()
#   discord.enviar(payload)   ← mesmo payload usado pelo telegram_sender.py
#
# Variáveis de ambiente:
#   DISCORD_WEBHOOK_URL   — URL do webhook do canal Discord
#   GROQ_API_KEY          — Chave da API Groq
# ─────────────────────────────────────────────────────────────────────────────

import os
import time
import json
import random
import datetime
import requests

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURAÇÃO
# ─────────────────────────────────────────────────────────────────────────────

DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1520959870331912313/iqfWZu4gBpbANUwmQROM9SVpBsky2a05Vm_a2JtH6cj6V9ZFI1eyDbvOdIDKWZd5jmHv"
GROQ_API_KEY        = os.environ.get("GROQ_API_KEY", "")
GROQ_ENDPOINT       = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL          = "llama-3.1-8b-instant"

# Filtros de qualidade
ACC_MINIMA    = 48.0   # % — abaixo disso não envia
EV_MINIMO     = 0.0015 # fração — 0.15%
COOLDOWN_S    = 180

# Timeout da chamada Groq (segundos)
GROQ_TIMEOUT  = 5

# Tamanho máximo da mensagem Discord (2000 chars)
DISCORD_MAX   = 1900


# ─────────────────────────────────────────────────────────────────────────────
# EMOJIS / HELPERS VISUAIS
# ─────────────────────────────────────────────────────────────────────────────

def _emoji_direcao(direcao: str) -> str:
    return "📈" if direcao.upper() in ("ALTA", "LONG", "BUY") else "📉"


def _emoji_confluencia(n_grupos: int) -> str:
    return {0: "⚠️", 1: "🟡", 2: "🟢", 3: "🔥"}.get(min(n_grupos, 3), "🔥")


def _emoji_ev(ev: float) -> str:
    if ev >= 0.012: return "🔥🔥"
    if ev >= 0.006: return "🔥"
    if ev >= 0.003: return "✅"
    return "⚠️"


def _barra(valor: float, total: float = 100.0, largura: int = 10) -> str:
    filled = round(valor / total * largura)
    filled = max(0, min(largura, filled))
    return "█" * filled + "░" * (largura - filled)


def _regime_label(regime: str) -> str:
    return {
        "trend_up":   "📈 Tendência de Alta",
        "trend_down": "📉 Tendência de Baixa",
        "volatile":   "⚡ Volátil",
        "ranging":    "↔️ Lateralizado",
    }.get(regime, regime)


# ─────────────────────────────────────────────────────────────────────────────
# FALLBACK — template simples usado quando a Groq falha
# ─────────────────────────────────────────────────────────────────────────────

def _fallback(dados: dict) -> str:
    eh_alta   = dados["direcao"].upper() in ("ALTA", "LONG", "BUY")
    ativo     = dados["ativo"].upper()
    horizonte = dados["horizonte"]
    entrada   = dados["entrada"]
    alvo      = dados["alvo"]
    stop      = dados["stop"]
    acuracia  = dados["acuracia"]
    ev        = dados.get("ev", 0)
    pf        = dados.get("profit_factor", 0)
    rr        = dados.get("rr", 0)
    n_grupos  = dados.get("confluencia_n", 0)
    regime    = dados.get("regime", "")

    direcao_str = "COMPRA" if eh_alta else "VENDA"
    emoji       = _emoji_direcao(dados["direcao"])
    ganho_pct   = abs(alvo - entrada) / entrada * 100
    risco_pct   = abs(entrada - stop)  / entrada * 100

    return (
        f"## {emoji} {direcao_str} — `{ativo}` · `{horizonte}`\n\n"
        f"**Entrada:** `{entrada:.4f}`\n"
        f"**Alvo:** `{alvo:.4f}` *(+{ganho_pct:.2f}%)*\n"
        f"**Stop:** `{stop:.4f}` *(-{risco_pct:.2f}%)*\n"
        f"**R/R:** `1:{rr:.2f}` {_emoji_ev(ev)}\n\n"
        f"`{_barra(acuracia)}` Acurácia `{acuracia:.1f}%` · "
        f"EV `{ev*100:+.3f}%` · PF `{pf:.2f}` · "
        f"{_emoji_confluencia(n_grupos)} `{n_grupos}` grupo(s) confluentes\n\n"
        f"🌐 Regime: {_regime_label(regime)}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# GERAÇÃO DE PROMPT PARA GROQ
# ─────────────────────────────────────────────────────────────────────────────

# Cada chamada sorteia um "papel" diferente para o modelo, garantindo
# que mensagens sucessivas soem distintas.
_PAPEIS = [
    "Você é um trader quantitativo sênior, direto ao ponto, sem rodeios. "
    "Fala como alguém que leu os dados e tirou a conclusão — sem jargão excessivo.",

    "Você é um analista técnico rigoroso. Prefere dados a emoção. "
    "Menciona os números que importam e o que eles significam na prática.",

    "Você é um gestor de risco experiente. Sempre lembra que proteção do capital "
    "vem antes do lucro. Tom ponderado, mas confiante quando os números apoiam.",

    "Você é um trader de mercado que pensa em probabilidades. "
    "Foca em EV e repetibilidade — o que funciona em 1000 trades.",

    "Você é analista de fluxo de mercado. Gosta de interpretar o que os horizontes "
    "temporais dizem sobre o comportamento dos participantes.",
]

# Tons por contexto (inseridos no prompt para variar o estilo)
def _tom_contexto(dados: dict) -> str:
    regime    = dados.get("regime", "")
    n_grupos  = dados.get("confluencia_n", 0)
    partes    = []

    if regime == "ranging":
        partes.append(
            "O mercado está LATERALIZADO. Seja MAIS CAUTELOSO na análise — "
            "enfatize a incerteza e que o risco de falso rompimento é maior."
        )
    elif regime == "volatile":
        partes.append(
            "O mercado está VOLÁTIL. Destaque a rapidez necessária na execução "
            "e a importância do stop."
        )

    if n_grupos >= 3:
        partes.append(
            "A confluência é MUITO FORTE (3+ grupos). Seja mais CONFIANTE — "
            "esse tipo de alinhamento multi-horizonte é estatisticamente raro."
        )
    elif n_grupos == 2:
        partes.append("Confluência FORTE entre 2 grupos distintos — contexto favorável.")
    elif n_grupos <= 1:
        partes.append(
            "Confluência MODERADA. Reconheça que há menos confirmação do que o ideal."
        )

    return " ".join(partes) if partes else ""


def _montar_prompt(dados: dict) -> str:
    eh_alta   = dados["direcao"].upper() in ("ALTA", "LONG", "BUY")
    ativo     = dados["ativo"].upper()
    horizonte = dados["horizonte"]
    entrada   = dados["entrada"]
    alvo      = dados["alvo"]
    stop      = dados["stop"]
    acuracia  = dados["acuracia"]
    ev        = dados.get("ev", 0) * 100           # converte para %
    pf        = dados.get("profit_factor", 0)
    rr        = dados.get("rr", 0)
    n_grupos  = dados.get("confluencia_n", 0)
    grupos    = ", ".join(dados.get("confluencia_grupos", [])) or "—"
    h_conf    = ", ".join(dados.get("horizontes_confirmadores", [])) or "—"
    regime    = dados.get("regime", "")
    ganho_pct = abs(alvo - entrada) / entrada * 100
    risco_pct = abs(entrada - stop) / entrada * 100

    contexto_extra = _tom_contexto(dados)
    papel = random.choice(_PAPEIS)

    prompt = f"""
{papel}

{contexto_extra}

Gere UMA mensagem curta (máximo 4 linhas, linguagem natural, sem markdown pesado)
para um canal de trading profissional no Discord.
A mensagem deve soar ÚNICA, como se você estivesse dando sua opinião
— não copie os dados mecanicamente, INTERPRETE eles.

DADOS DO SINAL:
- Ativo: {ativo}
- Direção: {"ALTA (compra)" if eh_alta else "BAIXA (venda)"}
- Horizonte: {horizonte}
- Entrada: {entrada:.4f}
- Alvo: {alvo:.4f} (+{ganho_pct:.2f}%)
- Stop: {stop:.4f} (-{risco_pct:.2f}%)
- R/R: 1:{rr:.2f}
- Acurácia do modelo (últimas amostras): {acuracia:.1f}%
- EV por operação: +{ev:.3f}%
- Profit Factor: {pf:.2f}
- Grupos confluentes: {n_grupos} ({grupos})
- Horizontes confirmadores: {h_conf}
- Regime de mercado: {regime}

REGRAS:
1. Máximo 4 linhas de texto corrido.
2. Pode mencionar 1 ou 2 números — os mais relevantes.
3. NÃO liste todos os dados — escolha o que importa para a tese.
4. NÃO use markdown além de negrito (*palavra*) para 1 termo chave.
5. Termine com a informação de stop ou entrada — algo acionável.
6. Escreva em português do Brasil.
""".strip()

    return prompt


# ─────────────────────────────────────────────────────────────────────────────
# CHAMADA GROQ
# ─────────────────────────────────────────────────────────────────────────────

def _gerar_com_groq(dados: dict) -> str | None:
    if not GROQ_API_KEY:
        return None

    prompt = _montar_prompt(dados)

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 200,
        "temperature": 0.85,   # alguma criatividade sem perder coerência
        "top_p": 0.9,
    }

    try:
        resp = requests.post(
            GROQ_ENDPOINT,
            headers=headers,
            json=body,
            timeout=GROQ_TIMEOUT,
        )
        if resp.status_code == 200:
            texto = resp.json()["choices"][0]["message"]["content"].strip()
            return texto if texto else None
        else:
            print(f"[Discord] Groq HTTP {resp.status_code}: {resp.text[:120]}")
            return None
    except requests.exceptions.Timeout:
        print("[Discord] ⏱ Groq timeout — usando fallback")
        return None
    except Exception as e:
        print(f"[Discord] Groq erro: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# MONTAGEM DO EMBED DISCORD
# ─────────────────────────────────────────────────────────────────────────────

def _cor_embed(direcao: str, regime: str) -> int:
    """Cor do embed em decimal (hex RGB)."""
    eh_alta = direcao.upper() in ("ALTA", "LONG", "BUY")
    if regime == "volatile":
        return 0xF39C12  # laranja
    if regime == "ranging":
        return 0x95A5A6  # cinza (cauteloso)
    return 0x2ECC71 if eh_alta else 0xE74C3C  # verde / vermelho


def _montar_embed(dados: dict, analise_ia: str) -> dict:
    """
    Monta o payload de embed rico para a API do Discord.
    """
    eh_alta   = dados["direcao"].upper() in ("ALTA", "LONG", "BUY")
    ativo     = dados["ativo"].upper()
    horizonte = dados["horizonte"]
    entrada   = dados["entrada"]
    alvo      = dados["alvo"]
    stop      = dados["stop"]
    acuracia  = dados["acuracia"]
    ev        = dados.get("ev", 0)
    pf        = dados.get("profit_factor", 0)
    rr        = dados.get("rr", 0)
    n_grupos  = dados.get("confluencia_n", 0)
    regime    = dados.get("regime", "")
    score     = dados.get("score", 0)

    ganho_pct = abs(alvo - entrada) / entrada * 100
    risco_pct = abs(entrada - stop) / entrada * 100

    emoji_dir = _emoji_direcao(dados["direcao"])
    emoji_ev_ = _emoji_ev(ev)
    emoji_conf = _emoji_confluencia(n_grupos)
    barra_acc  = _barra(acuracia)
    agora_str  = datetime.datetime.now().strftime("%H:%M:%S")
    direcao_label = "COMPRA" if eh_alta else "VENDA"

    # Trunca análise da IA se necessário
    analise_ia = analise_ia[:800] if len(analise_ia) > 800 else analise_ia

    embed = {
        "title": f"{emoji_dir} {direcao_label} — {ativo} · {horizonte}",
        "description": analise_ia,
        "color": _cor_embed(dados["direcao"], regime),
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "footer": {
            "text": f"Torch AI · {agora_str} · Score {score:.5f}"
        },
        "fields": [
            {
                "name": "📥 Entrada",
                "value": f"`{entrada:.4f}`",
                "inline": True,
            },
            {
                "name": "🎯 Alvo",
                "value": f"`{alvo:.4f}` *(+{ganho_pct:.2f}%)*",
                "inline": True,
            },
            {
                "name": "🛑 Stop",
                "value": f"`{stop:.4f}` *(-{risco_pct:.2f}%)*",
                "inline": True,
            },
            {
                "name": f"⚖️ R/R",
                "value": f"`1:{rr:.2f}`",
                "inline": True,
            },
            {
                "name": f"{emoji_ev_} EV / operação",
                "value": f"`{ev*100:+.3f}%`",
                "inline": True,
            },
            {
                "name": "📊 Profit Factor",
                "value": f"`{pf:.2f}`",
                "inline": True,
            },
            {
                "name": f"{barra_acc} Acurácia",
                "value": f"`{acuracia:.1f}%`",
                "inline": True,
            },
            {
                "name": f"{emoji_conf} Confluência",
                "value": f"`{n_grupos}` grupo(s)",
                "inline": True,
            },
            {
                "name": "🌐 Regime",
                "value": _regime_label(regime),
                "inline": True,
            },
        ],
    }

    return embed


# ─────────────────────────────────────────────────────────────────────────────
# ENVIO PARA DISCORD
# ─────────────────────────────────────────────────────────────────────────────

def _enviar_webhook(webhook_url: str, embed: dict, conteudo: str = "") -> bool:
    payload = {"embeds": [embed]}
    if conteudo:
        payload["content"] = conteudo[:2000]

    try:
        resp = requests.post(
            webhook_url,
            json=payload,
            timeout=10,
        )
        if resp.status_code in (200, 204):
            print(f"[Discord] ✅ Sinal enviado (HTTP {resp.status_code})")
            return True
        else:
            print(f"[Discord] ❌ HTTP {resp.status_code}: {resp.text[:150]}")
            return False
    except Exception as e:
        print(f"[Discord] Falha no webhook: {e}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# CLASSE PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

class DiscordSender:
    """
    Uso:
        sender = DiscordSender()
        sender.enviar(payload)   ← mesmo dict usado pelo telegram_sender.py

    O payload esperado é o mesmo gerado pelo SignalEngine:
        {
            "ativo", "direcao", "horizonte",
            "entrada", "alvo", "stop",
            "acuracia", "acuracia_janela",
            "ev", "profit_factor", "rr",
            "confluencia_n", "confluencia_grupos",
            "horizontes_confirmadores",
            "regime", "score"
        }
    """

    def __init__(
        self,
        webhook_url: str | None = None,
        acc_minima:  float = ACC_MINIMA,
        ev_minimo:   float = EV_MINIMO,
        cooldown_s:  int   = COOLDOWN_S,
    ):
        self.webhook_url = webhook_url or DISCORD_WEBHOOK_URL
        self.acc_minima  = acc_minima
        self.ev_minimo   = ev_minimo
        self.cooldown_s  = cooldown_s

        # {moeda: timestamp do último envio}
        self._ultimo_envio: dict[str, float] = {}

    # ─────────────────────────────────────────────────────────────────────────

    def enviar(self, dados: dict) -> bool:
        """
        Avalia o sinal e envia para o Discord se passar nos filtros.
        Retorna True se enviou, False caso contrário.
        """
        if not self.webhook_url:
            print("[Discord] ⚠️ DISCORD_WEBHOOK_URL não configurada.")
            return False

        ativo    = dados.get("ativo", "???").upper()
        acuracia = dados.get("acuracia", 0.0)
        ev       = dados.get("ev", 0.0)
        agora    = time.time()

        # ── Filtro 1: acurácia mínima ─────────────────────────────────────
        if acuracia < self.acc_minima:
            print(f"[Discord] ❌ {ativo} — acurácia {acuracia:.1f}% < {self.acc_minima:.1f}%")
            return False

        # ── Filtro 2: EV mínimo ───────────────────────────────────────────
        if ev < self.ev_minimo:
            print(f"[Discord] ❌ {ativo} — EV {ev*100:.3f}% < {self.ev_minimo*100:.3f}%")
            return False

        # ── Filtro 3: cooldown ────────────────────────────────────────────
        ultimo = self._ultimo_envio.get(ativo, 0)
        elapsed = agora - ultimo
        if elapsed < self.cooldown_s:
            restante = int(self.cooldown_s - elapsed)
            print(f"[Discord] ⏳ {ativo} — cooldown ({restante}s restantes)")
            return False

        # ── Gera análise com Groq ─────────────────────────────────────────
        print(f"[Discord] 🤖 Gerando análise Groq para {ativo}...")
        analise = _gerar_com_groq(dados)

        if analise:
            print(f"[Discord] ✅ Groq gerou análise ({len(analise)} chars)")
        else:
            print("[Discord] ⚠️ Groq falhou — usando fallback")
            analise = _fallback(dados)

        # ── Monta e envia embed ───────────────────────────────────────────
        embed = _montar_embed(dados, analise)
        ok = _enviar_webhook(self.webhook_url, embed)

        if ok:
            self._ultimo_envio[ativo] = agora

        return ok

    # ─────────────────────────────────────────────────────────────────────────
    # INTEGRAÇÃO DIRETA COM SignalEngine
    # ─────────────────────────────────────────────────────────────────────────

    def patch_signal_engine(self, engine) -> None:
        """
        Monkey-patch opcional: faz o SignalEngine chamar o Discord
        logo após enviar para o Telegram, sem alterar o código existente.

        Uso:
            from discord_sender import DiscordSender
            discord = DiscordSender()
            discord.patch_signal_engine(self._signal_engine)
        """
        _original_enviar = engine.avaliar.__func__  # método desacoplado
        _discord = self

        def _avaliar_patched(self_engine, moeda, preco, preds_percentual,
                             resultados_verificacao, regime="ranging",
                             arquivo_disco=None, acc_mente=None):
            # Chama o método original
            _original_enviar(self_engine, moeda, preco, preds_percentual,
                             resultados_verificacao, regime,
                             arquivo_disco, acc_mente)

            # Tenta recriar o payload do último sinal enviado pelo engine.
            # Se o engine tiver um atributo _ultimo_payload, usa ele;
            # senão monta um payload mínimo a partir dos parâmetros disponíveis.
            payload = getattr(self_engine, "_ultimo_payload", None)
            if payload:
                _discord.enviar(payload)

        import types
        engine.avaliar = types.MethodType(_avaliar_patched, engine)
        print("[Discord] ✅ SignalEngine patched — Discord ativo")


# ─────────────────────────────────────────────────────────────────────────────
# INTEGRAÇÃO COM sinal_engine.py (método alternativo: subclasse)
# ─────────────────────────────────────────────────────────────────────────────

class SignalEngineComDiscord:
    """
    Wrapper leve ao redor do SignalEngine original.
    Intercepta o momento pós-envio e dispara o Discord.

    Uso (em crypto_app.py, substitua):
        self._signal_engine = SignalEngine(TELEGRAM_TOKEN)
    por:
        from discord_sender import SignalEngineComDiscord, DiscordSender
        _discord = DiscordSender()
        self._signal_engine = SignalEngineComDiscord(TELEGRAM_TOKEN, _discord)
    """

    def __init__(self, token_bot: str, discord_sender: "DiscordSender"):
        # Importa aqui para não criar dependência circular no topo do arquivo
        from Software.core.sinal_engine import SignalEngine as _SE
        self._engine = _SE(token_bot)
        self._discord = discord_sender
        self._ultimo_payload: dict | None = None

    def avaliar(
        self,
        moeda:                  str,
        preco:                  float,
        preds_percentual:       list,
        resultados_verificacao: dict,
        regime:                 str = "ranging",
        arquivo_disco:          str | None = None,
        acc_mente:              list | None = None,
    ):
        # Chama o engine original (Telegram)
        self._engine.avaliar(
            moeda, preco, preds_percentual,
            resultados_verificacao, regime,
            arquivo_disco, acc_mente,
        )

        # Reconstrói payload aproximado para o Discord.
        # O SignalEngine original não expõe o último payload diretamente —
        # por isso usamos os dados disponíveis aqui para montar um payload
        # compatível com o formato do telegram_sender.
        h_idx     = 0   # horizonte de maior EV (simplificado)
        pred_abs  = max((abs(p) for p in preds_percentual), default=0)
        direcao   = "ALTA" if (preds_percentual[h_idx] if preds_percentual else 0) > 0 else "BAIXA"

        # Acurácia: usa acc_mente se disponível
        acuracia  = (sum(acc_mente[:4]) / 4 * 100) if acc_mente else 50.0

        # EV aproximado (não temos o R/R aqui, usamos uma proxy)
        ev_proxy  = max(pred_abs / 100 * 0.5, 0.001)

        payload = {
            "ativo":                  moeda,
            "direcao":                direcao,
            "horizonte":              "multi",
            "entrada":                preco,
            "alvo":                   preco * (1 + pred_abs / 100 * 0.7),
            "stop":                   preco * (1 - pred_abs / 100 * 0.35),
            "acuracia":               round(acuracia, 1),
            "acuracia_janela":        500,
            "ev":                     ev_proxy,
            "profit_factor":          1.5,
            "rr":                     round(pred_abs / 100 * 0.7 / (pred_abs / 100 * 0.35 + 1e-9), 2),
            "confluencia_n":          0,
            "confluencia_grupos":     [],
            "horizontes_confirmadores": [],
            "regime":                 regime,
            "score":                  0.0,
        }

        self._discord.enviar(payload)

    # Delega todos os outros atributos ao engine interno
    def __getattr__(self, item):
        return getattr(self._engine, item)


# ─────────────────────────────────────────────────────────────────────────────
# CONVENIÊNCIA: enviar direto a partir de um payload completo do SignalEngine
# ─────────────────────────────────────────────────────────────────────────────

def enviar_sinal_discord(dados_sinal: dict) -> bool:
    """
    Função standalone — equivalente a enviar_para_todos_canais() do telegram_sender,
    mas para Discord.  Instancia um DiscordSender com os padrões de ambiente.

    Uso em sinal_engine.py:
        from discord_sender import enviar_sinal_discord
        enviar_sinal_discord(payload)
    """
    sender = DiscordSender()
    return sender.enviar(dados_sinal)


# ─────────────────────────────────────────────────────────────────────────────
# TESTE LOCAL
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Payload de exemplo (mesmo formato do SignalEngine)
    payload_teste = {
        "ativo":                    "BTC/USDT",
        "direcao":                  "ALTA",
        "horizonte":                "5min",
        "entrada":                  67_450.0,
        "alvo":                     67_787.25,
        "stop":                     67_281.75,
        "acuracia":                 61.4,
        "acuracia_janela":          2843,
        "ev":                       0.00312,
        "profit_factor":            1.87,
        "rr":                       2.01,
        "confluencia_n":            3,
        "confluencia_grupos":       ["micro", "scalping", "intraday"],
        "horizontes_confirmadores": ["5s", "15s", "1min", "5min", "15min"],
        "regime":                   "trend_up",
        "score":                    0.00821,
    }

    print("=== TESTE discord_sender.py ===")
    print(f"Webhook URL: {'✅ configurada' if DISCORD_WEBHOOK_URL else '❌ NÃO configurada'}")
    print(f"Groq API Key: {'✅ configurada' if GROQ_API_KEY else '❌ NÃO configurada'}")
    print()

    if not DISCORD_WEBHOOK_URL:
        print("ℹ️  Configure DISCORD_WEBHOOK_URL para testar o envio real.")
        print()
        # Testa apenas a geração de mensagem
        print("--- Fallback template ---")
        print(_fallback(payload_teste))
        print()
        print("--- Prompt Groq (preview) ---")
        print(_montar_prompt(payload_teste)[:500] + "...")
    else:
        sender = DiscordSender()
        ok = sender.enviar(payload_teste)
        print(f"\nResultado: {'✅ enviado' if ok else '❌ falhou'}")