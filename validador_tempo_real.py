#!/usr/bin/env python3
"""
validador_em_tempo_real.py
===========================
Carrega um checkpoint .pt do Event Horizon e valida previsões
em tempo real contra a API pública da Binance.

Uso:
    python validador_em_tempo_real.py --symbol BTCUSDT --checkpoint mente_BTCUSDT_365d_v2.pt

Não depende do crypto.py nem do Universo.
"""

import argparse
import json
import math
import os
import sys
import time
from collections import deque
from datetime import datetime, timezone

import numpy as np
import requests
import torch

# ---------------------------------------------------------------------------
# Constantes idênticas ao mind_pytorch.py de produção
# ---------------------------------------------------------------------------
HORIZONTES = [5, 15, 30, 60, 300, 900, 1800, 3600, 18000, 86400]
N_HORIZONTES = len(HORIZONTES)
NOMES_H = {
    5: "5s", 15: "15s", 30: "30s", 60: "1min",
    300: "5min", 900: "15min", 1800: "30min", 3600: "1h",
    18000: "5h", 86400: "1d",
}
DELAY = 5.0               # segundos entre iterações (igual ao crypto_app.delay)
FATOR_INDICADORES = 5     # mesmo FATOR usado no Colab
JANELA_PRECOS = 200        # máximo de velas de 5s mantidas em memória
JANELA_SYNC = 300          # ticks para correlação (não usada sozinha, mas mantida)

# ---------------------------------------------------------------------------
# Importação da arquitetura
# ---------------------------------------------------------------------------
# O script espera que o arquivo mind_pytorch.py esteja no mesmo diretório
# ou no Python path. Ajuste o caminho se necessário.
try:
    from Software.core.mind_pytorch import MenteTorch
except ImportError:
    # fallback: supõe que o arquivo foi copiado para o diretório local
    from Software.core.mind_pytorch import MenteTorch


def buscar_preco_atual(symbol: str) -> float | None:
    """Retorna o preço atual do par na Binance ou None em caso de erro."""
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        return float(data["price"])
    except Exception as e:
        print(f"[ERRO] Binance: {e}")
        return None


class VerificadorTempoReal:
    """
    Mantém um buffer de previsões timestamped e, quando o horizonte
    transcorre, compara com o preço real para contabilizar acerto/erro.
    """

    def __init__(self, horizontes: list[int]):
        self.horizontes = horizontes
        self.buffer: list[dict] = []          # snapshots pendentes
        self.acertos = [0] * len(horizontes)
        self.erros   = [0] * len(horizontes)

    def registrar(self, ts: float, preds: list[float], preco: float):
        self.buffer.append({
            "ts": ts,
            "preds": list(preds),
            "preco": preco,
            "verificados": [False] * len(self.horizontes),
        })

    def verificar(self, ts_atual: float, precos_historicos: list[float]):
        """Varre o buffer e devolve lista de (índice_horizonte, acertou)."""
        resultados = []
        for entrada in self.buffer:
            for i, h in enumerate(self.horizontes):
                if entrada["verificados"][i]:
                    continue
                if ts_atual - entrada["ts"] < h:
                    continue
                # procura o preço mais próximo do momento alvo no histórico recente
                ts_alvo = entrada["ts"] + h
                preco_alvo = self._buscar_preco_proximo(ts_alvo, ts_atual, precos_historicos)
                if preco_alvo is None:
                    continue

                direcao_prevista = 1 if entrada["preds"][i] > 0 else -1
                direcao_real = 1 if preco_alvo > entrada["preco"] else -1
                acertou = direcao_prevista == direcao_real

                if acertou:
                    self.acertos[i] += 1
                else:
                    self.erros[i] += 1

                entrada["verificados"][i] = True
                resultados.append((i, acertou))
        # remove entradas totalmente verificadas
        self.buffer = [e for e in self.buffer if not all(e["verificados"])]
        return resultados

    def _buscar_preco_proximo(self, ts_alvo: float, ts_agora: float,
                               precos: list[float]) -> float | None:
        """Retorna o preço mais próximo do ts_alvo no histórico em memória."""
        if not precos:
            return None
        # usa o último preço se o alvo já passou
        return precos[-1]

    def acuracia_por_horizonte(self) -> list[tuple[str, float, int, int]]:
        """Retorna lista de (nome, acc, acertos, erros)."""
        resultado = []
        for i, h in enumerate(self.horizontes):
            total = self.acertos[i] + self.erros[i]
            acc = (self.acertos[i] / total * 100) if total > 0 else 0.0
            resultado.append((NOMES_H[h], acc, self.acertos[i], self.erros[i]))
        return resultado


def extrair_features(precos: list[float]) -> list[float]:
    """
    Calcula as mesmas 14 features usadas no treino do Colab,
    usando FATOR_INDICADORES para equivalência com a produção.
    """
    n = len(precos)
    if n < 26:
        return [0.0] * 14

    close = np.array(precos, dtype=np.float64)
    # EMA
    ema9 = _ema(close, 9 * FATOR_INDICADORES)
    ema21 = _ema(close, 21 * FATOR_INDICADORES)
    # RSI
    rsi = _rsi(close, 14 * FATOR_INDICADORES)
    # MACD
    ema12 = _ema(close, 12 * FATOR_INDICADORES)
    ema26 = _ema(close, 26 * FATOR_INDICADORES)
    macd_line = ema12 - ema26
    # Bollinger
    bb_mid = np.mean(close[-20 * FATOR_INDICADORES:])
    bb_std = np.std(close[-20 * FATOR_INDICADORES:])
    bb_upper = bb_mid + 2.0 * bb_std
    bb_lower = bb_mid - 2.0 * bb_std
    bb_pos = (close[-1] - bb_mid) / (bb_upper - bb_lower + 1e-9)
    # ATR (simplificado: usa apenas a série de fechamento)
    atr = _atr_simples(close, 14 * FATOR_INDICADORES)
    # retornos
    ret1 = (close[-1] - close[-2]) / (close[-2] + 1e-9) * 100
    ret5 = (close[-1] - close[-6]) / (close[-6] + 1e-9) * 100 if n >= 6 else 0.0
    ret10 = (close[-1] - close[-11]) / (close[-11] + 1e-9) * 100 if n >= 11 else 0.0
    # clamps
    ema_spread = np.clip((ema9 - ema21) / (close[-1] + 1e-9) * 100, -5, 5)
    macd_norm = np.clip(macd_line / (atr + 1e-9), -5, 5)
    bb_pos_clamped = np.clip(bb_pos, -3, 3)
    vol_pct = min((atr / (close[-1] + 1e-9) * 100), 5.0)

    # features 9,10,11 zeradas (memoria_score, sync_score, delta_energia)
    agora = datetime.now(timezone.utc)
    hora_seno = math.sin((agora.hour * 3600 + agora.minute * 60 + agora.second) / 86400 * 2 * math.pi)
    dia_seno = math.sin(agora.weekday() / 7 * 2 * math.pi)

    return [
        np.clip(ret1, -5, 5), np.clip(ret5, -10, 10), np.clip(ret10, -15, 15),
        ema_spread, (rsi - 50) / 50, macd_norm, bb_pos_clamped, vol_pct,
        0.0, 0.0, 0.0, 0.0, hora_seno, dia_seno,
    ]


def _ema(serie: np.ndarray, periodo: int) -> float:
    if len(serie) < periodo:
        return serie[-1]
    k = 2 / (periodo + 1)
    ema = serie[0]
    for val in serie[1:]:
        ema = val * k + ema * (1 - k)
    return ema


def _rsi(serie: np.ndarray, periodo: int) -> float:
    if len(serie) < periodo + 1:
        return 50.0
    deltas = np.diff(serie)
    ganhos = np.maximum(deltas, 0)
    perdas = np.maximum(-deltas, 0)
    avg_gain = np.mean(ganhos[-periodo:])
    avg_loss = np.mean(perdas[-periodo:])
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def _atr_simples(serie: np.ndarray, periodo: int) -> float:
    if len(serie) < 2:
        return 0.0
    trs = np.abs(np.diff(serie))
    if len(trs) < periodo:
        return np.mean(trs)
    return np.mean(trs[-periodo:])


def carregar_modelo(caminho: str) -> MenteTorch:
    """Instancia a MenteTorch e carrega os pesos do checkpoint."""
    modelo = MenteTorch(id_agente=0)
    ck = torch.load(caminho, map_location="cpu")
    modelo.load_state_dict(ck["model_state_dict"], strict=False)
    modelo.eval()
    print(f"Modelo carregado: {caminho} (geração {ck.get('geracao', '?')})")
    return modelo


def main():
    parser = argparse.ArgumentParser(description="Validador em tempo real")
    parser.add_argument("--symbol", default="BTCUSDT", help="Par da Binance")
    parser.add_argument("--checkpoint", default="data/mentes_pytorch/mente_h0_v2_h0_20260717_161041.pt",
                        help="Caminho do checkpoint .pt")
    args = parser.parse_args()

    modelo = carregar_modelo(args.checkpoint)
    verificador = VerificadorTempoReal(HORIZONTES)
    precos_historicos: deque[float] = deque(maxlen=JANELA_PRECOS)

    print(f"Monitorando {args.symbol} a cada {DELAY}s\n")

    try:
        while True:
            preco = buscar_preco_atual(args.symbol)
            if preco is None:
                time.sleep(DELAY)
                continue

            ts = time.time()
            precos_historicos.append(preco)

            # Features e predição
            features = extrair_features(list(precos_historicos))
            with torch.no_grad():
                preds_raw = modelo.forward(features)
                preds_pct = [p * 5.0 for p in preds_raw]

            verificador.registrar(ts, preds_pct, preco)

            # Verifica horizontes que já fecharam
            resultados = verificador.verificar(ts, list(precos_historicos))

            # Exibe status
            now_str = datetime.now().strftime("%H:%M:%S")
            print(f"\n{'='*60}")
            print(f"[{now_str}] {args.symbol} ${preco:.2f}")
            print(f"{'Horizonte':<10} {'Acurácia':<10} {'Acertos':<8} {'Erros':<8} {'Total':<8}")
            print("-" * 60)
            for nome, acc, a, e in verificador.acuracia_por_horizonte():
                total = a + e
                barra = "█" * int(acc / 10) + "░" * (10 - int(acc / 10))
                print(f"{nome:<10} {barra} {acc:5.1f}%   {a:<8} {e:<8} {total:<8}")
            print(f"{'='*60}")

            time.sleep(DELAY)

    except KeyboardInterrupt:
        print("\nInterrompido pelo usuário.")


if __name__ == "__main__":
    main()