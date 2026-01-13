import requests
import config

def get_us_candles(symbol, resolution, start, end):
    url = "https://finnhub.io/api/v1/stock/candle"
    params = {
        "symbol": symbol,
        "resolution": resolution,  # "5", "15", "60"
        "from": start,
        "to": end,
        "token": config.FINNHUB_API_KEY
    }

    r = requests.get(url, params=params, timeout=5)
    if r.status_code != 200:
        return None

    data = r.json()
    return data if data.get("s") == "ok" else None
