import requests, config

def get_pl_candles(symbol):
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "apikey": config.ALPHA_API_KEY
    }

    r = requests.get(url)
    if r.status_code != 200:
        return None

    data = r.json()
    return data if "Time Series" in str(data) else None
