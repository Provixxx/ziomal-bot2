# risk.py

def calculate_sl_tp(
    side: str,
    entry: float,
    atr: float,
    pattern: str,
    market: str | None = None
):
    """
    Centralny risk engine.
    - ATR-based
    - pattern-aware
    - market-aware (GOLD vs reszta)
    """

    if atr is None or atr <= 0:
        return None, None

    # =========================
    # DEFAULT (BTC / STOCKS)
    # =========================
    sl_mult = 1.2
    rr = 2.0

    if pattern in ["Hammer", "Shooting Star"]:
        sl_mult = 1.0
        rr = 2.5
    elif pattern in ["Engulfing"]:
        sl_mult = 1.2
        rr = 2.0
    elif pattern in ["Pullback"]:
        sl_mult = 1.2
        rr = 2.2

    # =========================
    # GOLD OVERRIDE
    # =========================
    if market == "GOLD":
        if pattern == "Pullback":
            sl_mult = 1.0     # ciaśniejszy SL (GOLD szanuje poziomy)
            rr = 2.2
        else:
            sl_mult = 1.1
            rr = 2.0

    # =========================
    # CALC
    # =========================
    sl_distance = atr * sl_mult
    tp_distance = sl_distance * rr

    if side == "LONG":
        sl = entry - sl_distance
        tp = entry + tp_distance
    else:  # SHORT
        sl = entry + sl_distance
        tp = entry - tp_distance

    return round(sl, 2), round(tp, 2)
