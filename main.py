import json
import math
import os
import statistics


QUANTILE_LEVELS = (0.05, 0.25, 0.5, 0.75, 0.95)
NORMAL_QUANTILES = (-1.644854, -0.674490, 0.0, 0.674490, 1.644854)
# Per-quantile width multipliers (v10): widen the outer 5%/95% bands, narrow
# the inner 25%/75% bands. The median (z = 0) is unaffected. Measured: this
# plus a smaller sigma shrink and a longer jump window beats v9 on both
# practice and held-out, while wider/narrower alone or a horizon exponent
# trades one metric against the other.
TAIL_MULTS = (1.25, 0.75, 1.0, 0.75, 1.25)
HORIZON = 240
WINDOW = 360
JUMP_WINDOW = 120
JUMP_THRESHOLD = 0.03
JUMP_MULTIPLIER = 2.0
JUMP_CAP = 0.05
WIN_SIZE = 0.01
SHRINK = 0.6
FALLBACK_SIGMA = 0.0025
SIGMA_MIN = 0.001
SIGMA_MAX = 0.05


def normal_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def forecast_market(market):
    prices = market["prices"]
    if not prices:
        return [[0.5] * len(NORMAL_QUANTILES) for _ in range(HORIZON)]
    last_price = prices[-1]
    if len(prices) == 1:
        sigma = FALLBACK_SIGMA
    else:
        raw_diffs = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
        recent_raw = raw_diffs[-WINDOW:]
        winsorized = [max(-WIN_SIZE, min(WIN_SIZE, d)) for d in recent_raw]
        if len(winsorized) < 30:
            sigma = FALLBACK_SIGMA
        else:
            sigma = statistics.stdev(winsorized)
        sigma = max(SIGMA_MIN, min(SIGMA_MAX, sigma))
        sigma *= SHRINK
        recent_raw_120 = raw_diffs[-JUMP_WINDOW:]
        if any(abs(d) >= JUMP_THRESHOLD for d in recent_raw_120):
            sigma = min(sigma * JUMP_MULTIPLIER, JUMP_CAP)
    rows = []
    for h in range(1, HORIZON + 1):
        row = [last_price + z * sigma * math.sqrt(h) * m
               for z, m in zip(NORMAL_QUANTILES, TAIL_MULTS)]
        row = [max(0.0, min(1.0, v)) for v in row]
        row.sort()
        row = [round(v, 6) for v in row]
        rows.append(row)
    return rows


def process_case(data):
    quantiles = data["quantiles"]
    if quantiles != list(QUANTILE_LEVELS):
        raise ValueError("quantiles list does not match expected levels")
    forecasts = []
    for market in data["markets"]:
        rows = forecast_market(market)
        forecasts.append({"id": market["id"], "q": rows})
    return {"forecasts": forecasts}


def main():
    input_dir = os.environ.get("MAKEFUN_INPUT_DIR", "/input")
    output_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(output_dir, exist_ok=True)
    for filename in sorted(os.listdir(input_dir)):
        if not filename.endswith(".in"):
            continue
        input_path = os.path.join(input_dir, filename)
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        result = process_case(data)
        output_filename = filename[:-3] + ".out"
        output_path = os.path.join(output_dir, output_filename)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, sort_keys=True)


if __name__ == "__main__":
    main()
