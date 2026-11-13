# polymarket-nvidia-ceo-forecast-01 — v10: per-market volatility quantile forecaster

Forecasts each Polymarket "Next CEO of NVIDIA?" market's Yes price for the 240 minutes after each checkpoint, as five quantiles (5%, 25%, 50%, 75%, 95%), optimized for mean pinball loss.

Method (measured, not guessed): persistence median at the last price; per-market sigma from the last 360 one-minute differences, winsorized to ±0.01, times 0.6; sigma doubled (capped at 0.05) when any raw move in the last 120 minutes reaches 0.03; quantile bands as last price plus the normal quantile times sigma times sqrt(horizon minute), with the outer 5%/95% bands widened x1.25 and the inner 25%/75% bands narrowed x0.75. No drift, no mean reversion, no cross-market normalization — all three made things worse in testing.

Changes vs v9 (practice 0.280378, held-out 2.329513): sigma shrink 0.7 → 0.6, jump window 60 → 120 minutes, per-quantile width multipliers (outer x1.25, inner x0.75). A ~55-config search found the v9 family near its Pareto frontier — no config reached the 0.26 practice target without worsening held-out (best practice 0.2719 failed held-out; logit cut held-out to 2.17 but practice to 0.305). This v10 is the best config that improves both metrics.

Scores measured locally with a scorer that reproduces the house persistence baseline exactly (0.363589 on the six practice cases):
- Practice (6 cases, 153,600 items): **0.274007** (house baseline 0.363589; beats the baseline on all six cases)
- Held-out (5 extra windows cut from earlier, jumpier history, 36,000 items): **2.329071** (house 2.345500)

Pure Python 3.13 standard library, deterministic, offline, ~0.3–0.5 s per case (limit 8 s).

Run: `MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py`
