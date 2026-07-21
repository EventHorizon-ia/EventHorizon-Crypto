# telegram_sender.py  v3
# ─────────────────────────────────────────────────────────────────────────────
# PT e EN têm estrutura IDÊNTICA — apenas os textos fixos mudam.
# Todos os campos do payload são usados nos dois idiomas.
# ─────────────────────────────────────────────────────────────────────────────

import datetime
import requests

CANAL_VIP_PT = "-1004322239279"
CANAL_VIP_EN = "-5434201315"


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS VISUAIS
# ─────────────────────────────────────────────────────────────────────────────

def _barra_acuracia(acuracia: float, largura: int = 10) -> str:
    filled = round(acuracia / 100 * largura)
    filled = max(0, min(largura, filled))
    return "█" * filled + "░" * (largura - filled)


def _emoji_ev(ev: float) -> str:
    """EV já recebido em fração (0.003 = 0.3%)."""
    if ev >= 0.012:
        return "🔥🔥"
    if ev >= 0.006:
        return "🔥"
    if ev >= 0.003:
        return "✅"
    return "⚠️"


def _emoji_rr(rr: float) -> str:
    if rr >= 3.0:
        return "💎"
    if rr >= 2.0:
        return "✅"
    if rr >= 1.5:
        return "🟡"
    return "⚠️"


def _label_confluencia_pt(n_grupos: int) -> str:
    if n_grupos >= 3:
        return "MUITO FORTE ████"
    if n_grupos == 2:
        return "FORTE ███░"
    if n_grupos == 1:
        return "MODERADA ██░░"
    return "FRACA █░░░"


def _label_confluencia_en(n_grupos: int) -> str:
    if n_grupos >= 3:
        return "VERY STRONG ████"
    if n_grupos == 2:
        return "STRONG ███░"
    if n_grupos == 1:
        return "MODERATE ██░░"
    return "WEAK █░░░"


def _regime_pt(regime: str) -> str:
    return {
        "trend_up":   "📈 Tendência de Alta",
        "trend_down": "📉 Tendência de Baixa",
        "volatile":   "⚡ Volátil",
        "ranging":    "↔️  Lateralizado",
    }.get(regime, "—")


def _regime_en(regime: str) -> str:
    return {
        "trend_up":   "📈 Uptrend",
        "trend_down": "📉 Downtrend",
        "volatile":   "⚡ Volatile",
        "ranging":    "↔️  Ranging",
    }.get(regime, "—")


def _grupos_conf_pt(grupos: list[str]) -> str:
    mapa = {
        "micro":    "Micro (≤1min)",
        "scalping": "Scalping (5–15min)",
        "intraday": "Intraday (30min–1h)",
        "swing":    "Swing (5h–1d)",
    }
    return "  ".join(f"`{mapa.get(g, g)}`" for g in grupos) if grupos else "—"


def _grupos_conf_en(grupos: list[str]) -> str:
    mapa = {
        "micro":    "Micro (≤1min)",
        "scalping": "Scalping (5–15min)",
        "intraday": "Intraday (30min–1h)",
        "swing":    "Swing (5h–1d)",
    }
    return "  ".join(f"`{mapa.get(g, g)}`" for g in grupos) if grupos else "—"


# ─────────────────────────────────────────────────────────────────────────────
# CORE DO FORMATADOR  (lógica compartilhada PT/EN)
# ─────────────────────────────────────────────────────────────────────────────

def _calcular_campos(dados: dict) -> dict:
    """Pré-calcula todos os campos derivados usados por ambos os formatadores."""
    entrada = dados["entrada"]
    alvo    = dados["alvo"]
    stop    = dados["stop"]
    risco   = abs(entrada - stop)
    ganho   = abs(alvo    - entrada)
    rr      = dados.get("rr", round(ganho / risco, 2) if risco > 0 else 0)

    acuracia       = dados["acuracia"]           # %
    acuracia_janela = dados.get("acuracia_janela", "?")
    ev             = dados.get("ev", 0)           # fração
    pf             = dados.get("profit_factor", 0)
    n_grupos       = dados.get("confluencia_n", 0)
    grupos_conf    = dados.get("confluencia_grupos", [])
    h_conf         = dados.get("horizontes_confirmadores", [])
    regime         = dados.get("regime", "")
    score          = dados.get("score", 0)

    h_str = "  ".join(f"`{h}`" for h in h_conf) if h_conf else "—"

    barra = _barra_acuracia(acuracia)

    return {
        "entrada":        entrada,
        "alvo":           alvo,
        "stop":           stop,
        "risco":          risco,
        "ganho":          ganho,
        "rr":             rr,
        "acuracia":       acuracia,
        "acuracia_janela": acuracia_janela,
        "ev":             ev,
        "pf":             pf,
        "n_grupos":       n_grupos,
        "grupos_conf":    grupos_conf,
        "h_conf":         h_conf,
        "h_str":          h_str,
        "regime":         regime,
        "score":          score,
        "barra":          barra,
        "emoji_ev":       _emoji_ev(ev),
        "emoji_rr":       _emoji_rr(rr),
    }


# ─────────────────────────────────────────────────────────────────────────────
# FORMATADORES
# ─────────────────────────────────────────────────────────────────────────────

def formatar_sinal_pt(dados_sinal: dict) -> str:
    agora   = datetime.datetime.now().strftime("%H:%M:%S")
    direcao = dados_sinal["direcao"].upper()
    eh_alta = direcao in ("ALTA", "LONG", "BUY")
    c       = _calcular_campos(dados_sinal)

    cabecalho    = "🚨 SINAL DE ALTA 📈" if eh_alta else "🚨 SINAL DE BAIXA 📉"
    conf_label   = _label_confluencia_pt(c["n_grupos"])
    regime_str   = _regime_pt(c["regime"])
    grupos_str   = _grupos_conf_pt(c["grupos_conf"])

    ganho_pct = c["ganho"] / c["entrada"] * 100
    risco_pct = c["risco"] / c["entrada"] * 100

    linhas = [
        f"{cabecalho}",
        f"",
        f"*Par:* `{dados_sinal['ativo'].upper()}` — *{dados_sinal['horizonte']}*",
        f"*Horário:* {agora}",
        f"",
        f"*Entrada:*  `{c['entrada']:.4f}`",
        f"*Alvo:*     `{c['alvo']:.4f}`  _(+{ganho_pct:.2f}%)_",
        f"*Stop:*     `{c['stop']:.4f}`  _(-{risco_pct:.2f}%)_",
        f"{c['emoji_rr']} *R/R:* `1:{c['rr']:.2f}`",
        f"",
        f"━━━━━━━━━━━━━━━━━━━━━━",
        f"📊 *Métricas Quantitativas*",
        f"",
        f"`{c['barra']}` *Acurácia:* {c['acuracia']:.1f}% _(últimos {c['acuracia_janela']} trades)_",
        f"{c['emoji_ev']} *EV por operação:* `{c['ev']*100:+.3f}%`",
        f"📈 *Profit Factor:* `{c['pf']:.2f}`",
        f"",
        f"━━━━━━━━━━━━━━━━━━━━━━",
        f"🎯 *Confluência:* {conf_label}",
        f"📐 *Grupos confirmadores:* {grupos_str}",
        f"🕐 *Horizontes:* {c['h_str']}",
        f"🌐 *Regime:* {regime_str}",
        f"",
        f"━━━━━━━━━━━━━━━━━━━━━━",
        f"🔗 [Auditoria Pública](https://torch-ai-official.github.io/trader-ai/dashboard.html)",
    ]
    return "\n".join(linhas)


def formatar_sinal_en(dados_sinal: dict) -> str:
    agora   = datetime.datetime.now().strftime("%H:%M:%S")
    direcao = dados_sinal["direcao"].upper()
    eh_alta = direcao in ("ALTA", "LONG", "BUY")
    c       = _calcular_campos(dados_sinal)

    cabecalho  = "🚨 BUY SIGNAL 📈" if eh_alta else "🚨 SELL SIGNAL 📉"
    conf_label = _label_confluencia_en(c["n_grupos"])
    regime_str = _regime_en(c["regime"])
    grupos_str = _grupos_conf_en(c["grupos_conf"])

    ganho_pct = c["ganho"] / c["entrada"] * 100
    risco_pct = c["risco"] / c["entrada"] * 100

    linhas = [
        f"{cabecalho}",
        f"",
        f"*Pair:* `{dados_sinal['ativo'].upper()}` — *{dados_sinal['horizonte']}*",
        f"*Time:* {agora} (UTC-3)",
        f"",
        f"*Entry:*   `{c['entrada']:.4f}`",
        f"*Target:*  `{c['alvo']:.4f}`  _(+{ganho_pct:.2f}%)_",
        f"*Stop:*    `{c['stop']:.4f}`  _(-{risco_pct:.2f}%)_",
        f"{c['emoji_rr']} *R/R:* `1:{c['rr']:.2f}`",
        f"",
        f"━━━━━━━━━━━━━━━━━━━━━━",
        f"📊 *Quantitative Metrics*",
        f"",
        f"`{c['barra']}` *Accuracy:* {c['acuracia']:.1f}% _(last {c['acuracia_janela']} trades)_",
        f"{c['emoji_ev']} *EV per trade:* `{c['ev']*100:+.3f}%`",
        f"📈 *Profit Factor:* `{c['pf']:.2f}`",
        f"",
        f"━━━━━━━━━━━━━━━━━━━━━━",
        f"🎯 *Confluence:* {conf_label}",
        f"📐 *Confirming groups:* {grupos_str}",
        f"🕐 *Timeframes:* {c['h_str']}",
        f"🌐 *Regime:* {regime_str}",
        f"",
        f"━━━━━━━━━━━━━━━━━━━━━━",
        f"🔗 [Public Audit](https://torch-ai-official.github.io/trader-ai/dashboard-en.html)",
    ]
    return "\n".join(linhas)


# ─────────────────────────────────────────────────────────────────────────────
# ENVIO
# ─────────────────────────────────────────────────────────────────────────────

def enviar_sinal_telegram(token_bot: str, chat_id: str, texto: str) -> bool:
    url = f"https://api.telegram.org/bot{token_bot}/sendMessage"
    payload = {
        "chat_id":    chat_id,
        "text":       texto,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            print(f"[Telegram] ✅ Enviado para {chat_id}")
            return True
        print(f"[Telegram] ❌ {r.status_code} — {r.text[:120]}")
        return False
    except Exception as e:
        print(f"[Telegram] Falha: {e}")
        return False


def enviar_para_todos_canais(token_bot: str, dados_sinal: dict):
    """Envia o mesmo payload para PT e EN — apenas a formatação muda."""
    enviar_sinal_telegram(token_bot, CANAL_VIP_PT, formatar_sinal_pt(dados_sinal))
    enviar_sinal_telegram(token_bot, CANAL_VIP_EN, formatar_sinal_en(dados_sinal))