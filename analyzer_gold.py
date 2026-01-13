import requests
from indicators import ema, rsi

BINANCE = "https://api.binance.com/api/v3/klines"
SYMBOL = "XAUUSDT"

def _fetch_d1_levels(days=20):
    d1 = _fetch("1d", days)
    if not d1:
        return None
    _, h, l, _ = d1
    return {
        "d1_high": max(h),
        "d1_low": min(l)
    }

def _fetch(interval, limit):
    params = {"symbol": SYMBOL, "interval": interval, "limit": limit}
    r = requests.get(BINANCE, params=params, timeout=10)
    data = r.json()
    if not isinstance(data, list):
        return None
    o,h,l,c = [],[],[],[]
    for k in data:
        o.append(float(k[1]))
        h.append(float(k[2]))
        l.append(float(k[3]))
        c.append(float(k[4]))
    return o,h,l,c

def get_gold_candles():
    # ======================
    # LTF M15
    # ======================
    m15 = _fetch("15m", 200)
    if not m15:
        return None
    o15, h15, l15, c15 = m15

    # ======================
    # HTF H1 (TREND)
    # ======================
    h1 = _fetch("1h", 300)
    if not h1:
        return None
    _, _, _, c1h = h1

    ema200_h1 = ema(c1h, 200)

    # ======================
    # D1 LEVELS (POZIOMY)
    # ======================
    d1 = _fetch("1d", 30)
    if not d1:
        return None
    _, h1d, l1d, _ = d1

    d1_high = max(h1d)
    d1_low = min(l1d)

    # ======================
    # RETURN
    # ======================
    return {
        "ltf": {
            "o": o15,
            "h": h15,
            "l": l15,
            "c": c15
        },
        "htf": {
            "ema200": ema200_h1,
            "d1_high": d1_high,
            "d1_low": d1_low
        }
    }

def analyze_gold(data):
    o, h, l, c = data

    # zabezpieczenie
    if len(c) < 10:
        return

    # --- BREAKOUT ---
    recent_high = max(c[-6:-1])  # ~25 minut
    last_close = c[-1]

    if last_close > recent_high:
        entry = round(last_close, 2)

        send_stock_alert("XAUUSD", {
            "side": "LONG",
            "entry": entry,
            "sl": round(entry * 0.99, 2),
            "tp": round(entry * 1.02, 2),
            "rsi": "momentum",
            "ema": "trend",
            "atr": "high"
        })

        print("[GOLD BREAKOUT]")


