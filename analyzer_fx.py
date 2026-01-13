# analyzer_fx.py
import requests
import time
import pandas as pd
import config

# ======================================================
# RSI
# ======================================================
def calculate_rsi(prices, period=14):
    if not prices or len(prices) < period + 1:
        return 50.0

    series = pd.Series(prices)
    delta = series.diff()

    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()

    if loss.iloc[-1] == 0:
        return 100.0

    rs = gain.iloc[-1] / loss.iloc[-1]
    return round(100 - (100 / (1 + rs)), 1)


# ======================================================
# GOLD CANDLES – FINNHUB (D1)
# ======================================================
def get_gold_candles(days=50):
    """
    Zwraca: opens, highs, lows, closes
    """
    end = int(time.time())
    start = end - days * 24 * 60 * 60

    url = (
        "https://finnhub.io/api/v1/stock/candle"
        f"?symbol=XAUUSD"
        f"&resolution=D"
        f"&from={start}"
        f"&to={end}"
        f"&token={config.FINNHUB_KEY}"
    )

    try:
        r = requests.get(url, timeout=10).json()
    except Exception as e:
        print("⛔ GOLD REQUEST ERROR:", e)
        return [], [], [], []

    if r.get("s") != "ok":
        print("⛔ GOLD DATA EMPTY:", r)
        return [], [], [], []
    ema(closes, 200)

    return r["o"], r["h"], r["l"], r["c"]


# ======================================================
# ATR
# ======================================================
def calculate_atr(highs, lows, closes, period=14):
    if len(closes) < period + 1:
        return 0.0

    trs = []
    for i in range(1, len(closes)):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1])
        )
        trs.append(tr)

    atr = pd.Series(trs).rolling(period).mean().iloc[-1]
    return round(atr, 2)

if closes_h1[-1] <= closes_h1[-5]:
    print(f"[{symbol}] H1 trend NO")
    return

if closes_m5[-1] <= closes_m5[-2]:
    print(f"[{symbol}] M5 no trigger")
    return
