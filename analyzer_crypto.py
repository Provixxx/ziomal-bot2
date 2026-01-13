import requests
import config
from indicators import ema

def get_btc_candles():
    url = f"{config.BINANCE_BASE_URL}/api/v3/klines"
    params = {
        "symbol": "BTCUSDT",
        "interval": "15m",
        "limit": config.CANDLE_LIMIT
    }

    r = requests.get(url, params=params, timeout=10).json()
    if not isinstance(r, list):
        return None

    o, h, l, c = [], [], [], []
    for k in r:
        o.append(float(k[1]))
        h.append(float(k[2]))
        l.append(float(k[3]))
        c.append(float(k[4]))

    ema200 = ema(c, 200)

    return o, h, l, c, ema200


def analyze_btc(data):
    print("[BTC] analyzed")
