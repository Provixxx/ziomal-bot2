import pandas as pd
import numpy as np

# ==================================================
# WSKAŹNIKI
# ==================================================

def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()


def rsi(series, period=14):
    delta = series.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def atr(df, period=14):
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()

    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(period).mean()


# ==================================================
# SETUP B – TELEGRAM STYLE (PULLBACK)
# ==================================================

def telegram_pullback_long(df):
    if len(df) < 30:
        return False

    last = df.iloc[-1]

    rsi_recent_max = df["rsi"].iloc[-10:].max()
    recent_low = df["low"].iloc[-5:].min()

    return (
        last["ema_fast"] > last["ema_slow"] and
        last["close"] > last["ema_fast"] and
        rsi_recent_max > 60 and
        45 <= last["rsi"] <= 52 and
        last["close"] > recent_low
    )


# ==================================================
# ANALYZER
# ==================================================

class GoldAnalyzer:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    def analyze(self) -> pd.DataFrame:
        df = self.df

        # ------------------
        # SAFETY
        # ------------------
        if len(df) < 50:
            df["signal"] = "NONE"
            df["setup"] = None
            df["sl"] = None
            df["tp"] = None
            return df

        # ------------------
        # WSKAŹNIKI
        # ------------------
        df["ema_fast"] = ema(df["close"], 50)
        df["ema_slow"] = ema(df["close"], 200)
        df["rsi"] = rsi(df["close"], 14)
        df["atr"] = atr(df)

        # ------------------
        # DOMYŚLNE WARTOŚCI
        # ------------------
        df["signal"] = "NONE"
        df["setup"] = None
        df["sl"] = None
        df["tp"] = None

        last_idx = df.index[-1]
        last = df.loc[last_idx]

        # ==================================================
        # SETUP A – TREND FOLLOW (BEZPIECZNY)
        # ==================================================
        if (
            last["ema_fast"] > last["ema_slow"] and
            last["close"] > last["ema_fast"] and
            last["rsi"] < 70
        ):
            sl = last["close"] - last["atr"] * 1.2
            tp = last["close"] + last["atr"] * 2.5

            df.at[last_idx, "signal"] = "LONG"
            df.at[last_idx, "setup"] = "A"
            df.at[last_idx, "sl"] = round(sl, 2)
            df.at[last_idx, "tp"] = round(tp, 2)
            return df  # NIE sprawdzamy setupu B

        # ==================================================
        # SETUP B – TELEGRAM PULLBACK
        # ==================================================
        if telegram_pullback_long(df):
            sl = last["close"] - last["atr"] * 1.2
            tp = last["close"] + last["atr"] * 2.5

            df.at[last_idx, "signal"] = "LONG"
            df.at[last_idx, "setup"] = "B"
            df.at[last_idx, "sl"] = round(sl, 2)
            df.at[last_idx, "tp"] = round(tp, 2)

        return df
