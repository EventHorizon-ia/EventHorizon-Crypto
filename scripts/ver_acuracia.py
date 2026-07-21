#!/usr/bin/env python3
# accuracy_report.py — Relatório de acurácia das IAs
# Rode na raiz do projeto: python accuracy_report.py

import json
import os
import glob
from datetime import datetime

HORIZONTES = [5, 15, 30, 60]
CAMINHO_JSON = "data/minds.json"
CAMINHO_PT   = "data/mentes_pytorch"
MOEDAS_PT    = "data/ultimas_moedas.json"


# ── Cores ANSI ────────────────────────────────────────────────────────────────
R  = "\033[0m"
B  = "\033[1m"
DIM= "\033[2m"
GR = "\033[32m"
YL = "\033[33m"
RD = "\033[31m"
CY = "\033[36m"
MG = "\033[35m"
WH = "\033[97m"


def cor_acuracia(acc: float) -> str:
    if acc >= 55: return GR
    if acc >= 45: return YL
    return RD


def barra(acc: float, largura: int = 20) -> str:
    preenchido = int((acc / 100) * largura)
    c = cor_acuracia(acc)
    return c + "█" * preenchido + DIM + "░" * (largura - preenchido) + R


def categoria(acc: float) -> str:
    if acc >= 55: return f"{GR}● RECOMENDADA{R}"
    if acc >= 45: return f"{YL}◐ APRENDENDO {R}"
    return f"{RD}○ RUIM       {R}"


def formatar_numero(n) -> str:
    if isinstance(n, float):
        return f"{n:,.0f}"
    return f"{n:,}"


# ── Lê minds.json ─────────────────────────────────────────────────────────────

def ler_minds_json() -> dict:
    if not os.path.exists(CAMINHO_JSON):
        return {}
    try:
        with open(CAMINHO_JSON) as f:
            dados = json.load(f)
        return dados.get("mentes", {})
    except Exception as e:
        print(f"{RD}Erro ao ler {CAMINHO_JSON}: {e}{R}")
        return {}


# ── Lê .pt com torch ──────────────────────────────────────────────────────────

def ler_pt(id_agente: int) -> dict | None:
    caminho = os.path.join(CAMINHO_PT, f"mente_{id_agente}.pt")
    if not os.path.exists(caminho):
        return None
    try:
        import torch
        ck = torch.load(caminho, map_location="cpu")
        return ck
    except Exception as e:
        print(f"{YL}  ⚠ Não foi possível ler {caminho}: {e}{R}")
        return None


# ── Descobre símbolo de cada ID ───────────────────────────────────────────────

def mapear_simbolos() -> dict[int, str]:
    """Tenta mapear id_agente → símbolo de moeda."""
    mapa = {}

    # 1. Tenta universe.json
    for caminho in ["data/universe.json", "data/universo.json"]:
        if os.path.exists(caminho):
            try:
                with open(caminho) as f:
                    uni = json.load(f)
                for dado in uni.get("dados", []):
                    if dado.get("tipo") == "crypto" and "symbol" in dado:
                        mapa[dado["id"]] = dado["symbol"]
            except Exception:
                pass
            break

    # 2. Tenta ultimas_moedas.json + minds.json (fallback por ordem)
    if not mapa and os.path.exists(MOEDAS_PT):
        try:
            with open(MOEDAS_PT) as f:
                moedas = json.load(f)
            mentes_raw = ler_minds_json()
            ids = sorted(int(k) for k in mentes_raw.keys())
            for i, id_ in enumerate(ids):
                if i < len(moedas):
                    mapa[id_] = moedas[i]
        except Exception:
            pass

    return mapa


# ── Monta tabela de resultados ────────────────────────────────────────────────

def calcular_acuracia(acertos, erros) -> float:
    if isinstance(acertos, list):
        total_a = sum(acertos)
        total_e = sum(erros) if isinstance(erros, list) else erros
    else:
        total_a = acertos
        total_e = erros
    total = total_a + total_e
    return (total_a / total * 100) if total > 0 else 0.0


def acuracia_por_horizonte(acertos, erros) -> list[float]:
    if not isinstance(acertos, list):
        return []
    result = []
    for a, e in zip(acertos, erros if isinstance(erros, list) else []):
        total = a + e
        result.append(a / total * 100 if total > 0 else 0.0)
    return result


def total_operacoes(acertos, erros) -> int:
    if isinstance(acertos, list):
        return int(sum(acertos) + (sum(erros) if isinstance(erros, list) else erros))
    return int(acertos + erros)


# ── Exibição principal ────────────────────────────────────────────────────────

def main():
    os.system("clear" if os.name == "posix" else "cls")

    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    print(f"\n{B}{WH}{'━'*64}{R}")
    print(f"{B}{WH}  🧠  RELATÓRIO DE ACURÁCIA DAS IAs   {DIM}{agora}{R}")
    print(f"{B}{WH}{'━'*64}{R}\n")

    mentes_raw = ler_minds_json()
    if not mentes_raw:
        print(f"{RD}  Nenhuma mente encontrada em {CAMINHO_JSON}{R}\n")
        return

    simbolos = mapear_simbolos()

    registros = []
    for id_str, m in mentes_raw.items():
        id_ = int(id_str)
        acertos = m.get("n_acertos", 0)
        erros   = m.get("n_erros",   0)
        geracao = m.get("geracao",   0)
        tipo    = m.get("tipo", "?")
        simbolo = simbolos.get(id_, f"ID-{id_}")

        # Tenta enriquecer com dados do .pt
        pt = ler_pt(id_)
        if pt:
            acertos = pt.get("n_acertos", acertos)
            erros   = pt.get("n_erros",   erros)
            geracao = pt.get("geracao",   geracao)
            loss_hist = pt.get("historico_loss", [])
            loss_medio = sum(loss_hist) / len(loss_hist) if loss_hist else None
            mem_erros  = pt.get("memoria_erros", [])
            erro_medio = sum(mem_erros) / len(mem_erros) if mem_erros else None
        else:
            loss_medio = None
            erro_medio = None

        acc_geral = calcular_acuracia(acertos, erros)
        acc_hz    = acuracia_por_horizonte(acertos, erros)
        total_ops = total_operacoes(acertos, erros)

        registros.append({
            "id":        id_,
            "simbolo":   simbolo,
            "acc":       acc_geral,
            "acc_hz":    acc_hz,
            "geracao":   geracao,
            "total":     total_ops,
            "loss":      loss_medio,
            "erro_med":  erro_medio,
            "tipo":      tipo,
            "tem_pt":    pt is not None,
        })

    # Ordena por acurácia decrescente
    registros.sort(key=lambda x: x["acc"], reverse=True)

    # ── Cards por moeda ───────────────────────────────────────────────────
    for r in registros:
        acc  = r["acc"]
        c    = cor_acuracia(acc)
        simb = r["simbolo"]
        tipo_label = f"{CY}PyTorch{R}" if "pytorch" in r["tipo"] else f"{MG}Linear{R}"
        pt_label   = f"{GR}[.pt ✓]{R}" if r["tem_pt"] else f"{DIM}[.pt ✗]{R}"

        print(f"  {B}{WH}{simb:<12}{R}  {tipo_label}  {pt_label}   ID: {DIM}{r['id']}{R}")
        print(f"  {barra(acc)}  {c}{B}{acc:5.1f}%{R}  {categoria(acc)}")

        # Detalhes
        print(f"  {DIM}Operações: {formatar_numero(r['total'])}   "
              f"Gerações: {formatar_numero(r['geracao'])}", end="")
        if r["loss"] is not None:
            print(f"   Loss médio: {r['loss']:.4f}", end="")
        if r["erro_med"] is not None:
            conf = max(0, min(100, (1 - r["erro_med"] * 2) * 100))
            print(f"   Confiança: {conf:.1f}%", end="")
        print(R)

        # Acurácia por horizonte
        if r["acc_hz"]:
            labels = [f"{h}s" for h in HORIZONTES[:len(r["acc_hz"])]]
            partes = []
            for lbl, a in zip(labels, r["acc_hz"]):
                c2 = cor_acuracia(a)
                partes.append(f"{DIM}{lbl}:{R} {c2}{a:.1f}%{R}")
            print(f"  Horizontes → {' │ '.join(partes)}")

        print()

    # ── Sumário global ────────────────────────────────────────────────────
    print(f"{B}{WH}{'─'*64}{R}")
    total_mentes = len(registros)
    recomendadas = sum(1 for r in registros if r["acc"] >= 55)
    aprendendo   = sum(1 for r in registros if 45 <= r["acc"] < 55)
    ruins        = sum(1 for r in registros if r["acc"] < 45)
    acc_media    = sum(r["acc"] for r in registros) / total_mentes if registros else 0
    total_ops_g  = sum(r["total"] for r in registros)

    print(f"\n  {B}Mentes:{R} {total_mentes}  │  "
          f"{GR}Recomendadas: {recomendadas}{R}  │  "
          f"{YL}Aprendendo: {aprendendo}{R}  │  "
          f"{RD}Ruins: {ruins}{R}")
    print(f"  {B}Acurácia média:{R} {cor_acuracia(acc_media)}{acc_media:.1f}%{R}  │  "
          f"{B}Total de operações:{R} {formatar_numero(total_ops_g)}")
    print(f"\n  {DIM}Fonte: {CAMINHO_JSON}  +  {CAMINHO_PT}/*.pt{R}")
    print(f"{B}{WH}{'━'*64}{R}\n")


if __name__ == "__main__":
    main()