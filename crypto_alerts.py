from candle_patterns import detect_candle_pattern
from atr import calculate_atr
from ema import calculate_ema

def evaluate_btc_signal(opens, highs, lows, closes, rsi):
    pattern = detect_candle_pattern(opens, highs, lows, closes)
    atr = calculate_atr(highs, lows, closes)

    if not pattern or not atr:
        return None

    price = closes[-1]
    ema = calculate_ema(closes, 50)

    # 🔇 konsolidacja
    if atr < price * 0.003:
        return None

    # 🟢 LONG
    if (
        rsi <= 50
        and pattern in ("Hammer", "Bullish Engulfing")
        and price > ema
    ):
        return {
            "instrument": "BTCUSDT",
            "side": "LONG",
            "pattern": pattern,
            "entry": price,
            "sl": round(price - atr * 1.2, 2),
            "tp": round(price + atr * 2.5, 2),
            "atr": round(atr, 2),
            "ema": round(ema, 2),
            "rsi": rsi
        }

    # 🔴 SHORT
    if (
        rsi >= 60
        and pattern in ("Shooting Star", "Bearish Engulfing")
        and price < ema
    ):
        return {
            "instrument": "BTCUSDT",
            "side": "SHORT",
            "pattern": pattern,
            "entry": price,
            "sl": round(price + atr * 1.2, 2),
            "tp": round(price - atr * 2.5, 2),
            "atr": round(atr, 2),
            "ema": round(ema, 2),
            "rsi": rsi
        }

    return None
