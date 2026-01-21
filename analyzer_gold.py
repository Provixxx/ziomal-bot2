import pandas as pd
import numpy as np


class GoldAnalyzer:
    """
    GOLD Analyzer V2
    - Trend: EMA 8 / EMA 21
    - Momentum: RSI pullback
    - Price Action: impuls (close > high[-1] / < low[-1])
    - Output: signal_code (1 / 0 / -1)
    """

    def __init__(self, data: pd.DataFrame):
        self.df = data.copy()
        self.df.columns = [c.lower() for c in self.df.columns]

    def _add_indicators(self):
        # EMA trend
        self.df["ema_fast"] = self.df["close"].ewm(span=8, adjust=False).mean()
        self.df["ema_slow"] = self.df["close"].ewm(span=21, adjust=False).mean()

        # RSI
        delta = self.df["close"].diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = -delta.clip(upper=0).rolling(14).mean()
        rs = gain / loss
        self.df["rsi"] = 100 - (100 / (1 + rs))

    def _add_price_action(self):
        self.df["bullish_impulse"] = self.df["close"] > self.df["high"].shift(1)
        self.df["bearish_impulse"] = self.df["close"] < self.df["low"].shift(1)

    def analyze(self):
        self._add_indicators()
        self._add_price_action()

        df = self.df.dropna().copy()
        df["signal_code"] = 0  # 1 = LONG, -1 = SHORT

        # LONG
        long_condition = (
            (df["ema_fast"] > df["ema_slow"]) &
            (df["bullish_impulse"]) &
            (df["rsi"] < 45)
        )

        # SHORT
        short_condition = (
            (df["ema_fast"] < df["ema_slow"]) &
            (df["bearish_impulse"]) &
            (df["rsi"] > 55)
        )

        df.loc[long_condition, "signal_code"] = 1
        df.loc[short_condition, "signal_code"] = -1

        return df
