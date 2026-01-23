import requests
import pandas as pd
from logger import logger

BINANCE_URL = "https://api.binance.com/api/v3/klines"


def get_gold_candles():
    """
    GOLD proxy via PAXGUSDT (Binance)
    TF: 15m
    """
    symbol = "PAXGUSDT"
    interval = "15m"
    limit = 500

    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }

    r = requests.get(BINANCE_URL, params=params, timeout=10)
    data = r.json()

    if not isinstance(data, list):
        logger.error(f"Binance error: {data}")
        return None

    rows = []
    for k in data:
        rows.append({
            "date": pd.to_datetime(k[0], unit="ms"),
            "open": float(k[1]),
            "high": float(k[2]),
            "low": float(k[3]),
            "close": float(k[4]),
        })

    df = pd.DataFrame(rows)
    logger.info(f"Fetched {len(df)} PAXGUSDT candles from Binance")
    return df
