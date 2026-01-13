import pandas as pd

def rsi(closes, period=14):
    if len(closes) < period + 1:
        return None
    delta = pd.Series(closes).diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    if loss.iloc[-1] == 0:
        return 100
    rs = gain.iloc[-1] / loss.iloc[-1]
    return round(100 - (100 / (1 + rs)), 1)


def ema(closes, period=50):
    if len(closes) < period:
        return None
    return round(pd.Series(closes).ewm(span=period).mean().iloc[-1], 2)


def atr(highs, lows, closes, period=14):
    if len(closes) < period + 1:
        return None
    tr = pd.concat([
        pd.Series(highs) - pd.Series(lows),
        abs(pd.Series(highs) - pd.Series(closes).shift()),
        abs(pd.Series(lows) - pd.Series(closes).shift())
    ], axis=1).max(axis=1)
    return round(tr.rolling(period).mean().iloc[-1], 2)
