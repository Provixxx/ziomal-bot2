# candle_patterns.py

def detect_candle_pattern(opens, highs, lows, closes):
    """
    Zwraca nazwę patternu albo None
    """
    if len(closes) < 2:
        return None

    o = opens[-1]
    h = highs[-1]
    l = lows[-1]
    c = closes[-1]

    body = abs(c - o)
    upper = h - max(o, c)
    lower = min(o, c) - l

    # HAMMER
    if lower > body * 2 and upper < body:
        return "Hammer"

    # SHOOTING STAR
    if upper > body * 2 and lower < body:
        return "Shooting Star"

    return None
