# EventHorizon Crypto

**BTC/USDT 5-second directional prediction research.**  
Honest validation, documented limitations and an economic-viability case study.

---

## Status

🔎 **Research case study — economically unviable.**

EventHorizon Crypto explores short-horizon BTC/USDT directional prediction.
The project includes model research, temporal validation, uncertainty
estimation and a simulated maker-execution study.

Under the evaluated execution assumptions, the strategy was economically
unviable. This negative result is published as part of the project’s
commitment to honest research.

---

## What Was Evaluated

The economic case study used the checkpoint:

```text
mente_h0_v2_h0_20260717_161041.pt
```

This model was evaluated on H0 — directional prediction over the next five
seconds — using a temporal validation period.

The evaluation included:

- Simulated maker limit orders
- A one-tick distance from the current price
- A five-second order-waiting window
- Trade closure five seconds after the signal
- Maker-fee sensitivity analysis

Under the evaluated assumptions, the strategy was economically unviable.

---

## Research Models

| Model | Scope | Validation result | Status |
|---|---|---:|---|
| **Multi-horizon model** | H0–H9 | 51.2% mean honest-validation accuracy; H0 59.9% | Research |
| **H0-focused model** | H0 only | 60.7% H0 validation accuracy | Research |

These results come from validation sets used for checkpoint selection and
early stopping. They should not be interpreted as final out-of-sample
performance.

---

## System Overview

| Component | Description |
|---|---|
| **Model** | Custom Transformer, BiLSTM and cross-attention architecture |
| **Horizons** | 10 simultaneous horizons, from 5 seconds to 1 day |
| **Features** | 14 engineered features, including returns, technical indicators, volume and order-flow proxies |
| **Training** | AdamW, balanced loss across horizons |
| **Validation** | Temporal validation, block bootstrap and permutation testing |
| **Deployment research** | Simulated maker execution, PnL and fee sensitivity |

---

## Validation Pipeline

The research pipeline includes:

- Temporal validation with embargo between training and evaluation
- Walk-forward analysis
- Block bootstrap for uncertainty estimation
- Paired gap bootstrap comparing model and baseline
- Permutation testing with shuffled targets and aligned masks

The validation methodology is available through the standalone library:

**[honest-validation-toolkit](https://github.com/EventHorizon-ia/honest-validation-toolkit)**

---

## Economic-Viability Study

The economic study simulated maker limit orders rather than assuming
immediate execution at the current price.

For a buy signal, the simulation placed a limit order one tick below the
current price. For a sell signal, it placed a limit order one tick above.
An order was considered filled if the relevant high or low touched the limit
price within five seconds.

The trade was then closed at the price five seconds after the signal.

### Honest limitations

- The evaluation period was also used for checkpoint selection.
- The simulation assumes that a limit order fills when price touches its
  level; it does not model queue position, partial fills or adverse selection.
- Signals may overlap; the simulation does not model position limits, order
  cancellation or risk management.
- The displayed execution test used a zero maker fee; fee sensitivity was
  evaluated separately.
- Results are specific to BTC/USDT data and the evaluated period.

**Conclusion:** the strategy was economically unviable under the tested
execution assumptions.


---

## Links

- [EventHorizon-AI Hub](https://github.com/EventHorizon-ia/EventHorizon)
- [Crypto Research](https://github.com/EventHorizon-ia/crypto-h0-edge)
- [Public Audit Dashboard](https://eventhorizon-ia.github.io/trader-ai/dashboard-en.html)

---

*EventHorizon Crypto — honest research, documented limitations and negative
results.*