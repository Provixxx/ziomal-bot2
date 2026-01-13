import pandas as pd

def calculate_ema(prices, period=50):
    if not prices or len(prices) < period:
        return None

    series = pd.Series(prices)
    ema = series.ewm(span=period, adjust=False).mean()
    return round(ema.iloc[-1], 2)
