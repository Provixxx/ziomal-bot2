import pandas as pd
import numpy as np


class GoldAnalyzer:
    def __init__(self, data: pd.DataFrame):
        """
        Analyzer GOLD (XAUUSD)
        Dane wejściowe: DataFrame z kolumnami
        ['date', 'open', 'high', 'low', 'close', 'vol']
        """
        self.df = data.copy()
        self.df.columns = [c.lower() for c in self.df.columns]

    # =========================
    # INDICATORS
    # =========================
    def add_indicators(self):
        # Trend – EMA (dynamiczne, nie beton jak SMA200)
        self.df['ema_fast'] = self.df['close'].ewm(span=8, adjust=False).mean()
        self.df['ema_slow'] = self.df['close'].ewm(span=21, adjust=False).mean()

        # RSI – momentum (kontynuacja trendu)
        delta = self.df['close'].diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = -delta.clip(upper=0).rolling(14).mean()
        rs = gain / loss
        self.df['rsi'] = 100 - (100 / (1 + rs))

        # ATR – zmienność (opcjonalnie na przyszłość)
        high_low = self.df['high'] - self.df['low']
        high_close = (self.df['high'] - self.df['close'].shift()).abs()
        low_close = (self.df['low'] - self.df['close'].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        self.df['atr'] = tr.rolling(14).mean()

        return self.df

    # =========================
    # PRICE ACTION (SMC-lite)
    # =========================
    def add_price_action(self):
        # Impuls strukturalny – realny, częsty
        self.df['bullish_impulse'] = self.df['close'] > self.df['high'].shift(1)
        self.df['bearish_impulse'] = self.df['close'] < self.df['low'].shift(1)
        return self.df

    # =========================
    # MAIN ANALYSIS
    # =========================
    def analyze(self):
        self.add_indicators()
        self.add_price_action()

        # Czyścimy NaNy
        df = self.df.dropna().copy()

        # Domyślnie brak sygnału
        df['signal_code'] = 0   # 1 = BUY, -1 = SELL

        # =========================
        # SIGNAL LOGIC – GOLD
        # =========================

        buy_condition = (
            (df['ema_fast'] > df['ema_slow']) &          # trend up
            (df['bullish_impulse']) &                    # impuls ceny
            (df['rsi'] < 45)                              # momentum pullback
        )

        sell_condition = (
            (df['ema_fast'] < df['ema_slow']) &          # trend down
            (df['bearish_impulse']) &                    # impuls ceny
            (df['rsi'] > 55)                              # momentum pullback
        )

        df.loc[buy_condition, 'signal_code'] = 1
        df.loc[sell_condition, 'signal_code'] = -1

        return df


# =========================
# LOCAL TEST (opcjonalny)
# =========================
if __name__ == "__main__":
    data = {
        'date': pd.date_range(start='2024-01-01', periods=300, freq='H'),
        'open': np.random.uniform(2000, 2050, 300),
        'high': np.random.uniform(2050, 2060, 300),
        'low': np.random.uniform(1990, 2000, 300),
        'close': np.random.uniform(2000, 2050, 300),
        'vol': np.random.randint(100, 1000, 300)
    }

    df_mock = pd.DataFrame(data)
    analyzer = GoldAnalyzer(df_mock)
    result = analyzer.analyze()

    print(result[['date', 'close', 'rsi', 'signal_code']].tail())
