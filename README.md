# EventHorizon Crypto

**BTC/USDT 5‑second directional prediction system.**
Rigorously validated, honestly documented.

---

## Status

✅ **Edge validated** — +8 pp over baseline (60 % vs 52 %), confirmed with
walk‑forward, block bootstrap, and permutation testing on 1.5 M samples.
❌ **Economically unviable** under standard exchange fees — published as a
complete case study, including the initial false positives that were caught
by the validation pipeline.

---

## System Overview

| Component | Description |
|-----------|-------------|
| **Model** | Custom Transformer (6 blocks, 8 heads) + BiLSTM + Cross‑Attention |
| **Horizons** | 10 simultaneous horizons (5 s to 1 day) |
| **Features** | 14 engineered features (returns, RSI, MACD, Bollinger, volume, order flow) |
| **Training** | AdamW, 15 epochs, balanced loss across horizons |
| **Validation** | Walk‑forward, block bootstrap, permutation test, gap bootstrap |

---

## Validation Pipeline

Every result is audited with the same pipeline:

- Walk‑forward analysis with temporal embargo
- Block bootstrap (multiple block sizes)
- Permutation testing (shuffled targets, aligned mask)
- Gap bootstrap (real vs. permuted)

This pipeline is shared across all EventHorizon products and available as a
standalone library: **[honest‑validation‑toolkit](https://github.com/EventHorizon-ia/honest-validation-toolkit)**.

---

## Repository Structure

eventhorizon-crypto/
├── bot/ # Trading bot and execution engine
├── dashboard/ # Public audit dashboard (Next.js)
├── models/ # Model checkpoints and inference code
├── validation/ # Walk‑forward, bootstrap, permutation scripts
└── README.md

---

## Links

- [Main Hub](https://github.com/EventHorizon-ia/eventhorizon-ai)
- [Research Notebook](https://github.com/EventHorizon-ia/crypto-h0-edge)
- [Public Audit Dashboard](https://eventhorizon-ia.github.io/trader-ai/dashboard-en.html)

---

*EventHorizon Crypto — Proof, not promises.*
