from indicators import rsi, ema, atr
from risk import calculate_sl_tp
from indicators import atr
import datetime
from webhook_alerts import send_alert
import config

def send_stock_alert(symbol, signal_data):
    send_alert(
        webhook=config.DISCORD_WEBHOOK,
        title=f"📈 {symbol} SIGNAL",
        data=signal_data
    )
# ======================================
# PAMIĘĆ OSTATNICH ALERTÓW
# ======================================
_gold_lock = {
    "side": None
}
def gold_is_locked(side):
    return _gold_lock["side"] == side

def gold_update_lock(side):
    _gold_lock["side"] = side

_last_alert = {}

def is_gold_session_open():
    now = datetime.datetime.now(datetime.UTC).hour
    return (7 <= now < 11) or (13 <= now < 17)

def _is_duplicate(symbol, side):
    last = _last_alert.get(symbol)
    if not last:
        return False
    return last == side


def _save_alert(symbol, side):
    _last_alert[symbol] = side


# ======================================
# GŁÓWNA LOGIKA SYGNAŁU
# ======================================

def evaluate_signal(symbol, opens, highs, lows, closes, ema200):
    # ================= SAFETY =================
    if len(closes) < 200:
        return None

    # ================= ZAMKNIĘTA ŚWIECA =================
    price = closes[-2]

    # ================= WSKAŹNIKI =================
    r = rsi(closes)
    e_fast = ema(closes, 50)
    a = atr(highs, lows, closes)

    if not all([r, e_fast, a, ema200]):
        return None

    # ================= TREND =================
    trend_up = price > ema200
    trend_down = price < ema200

    # ================= FILTR ZMIENNOŚCI =================
    if a < price * 0.003:
        return None

    signal = None

    # ================= LONG (TYLKO Z TRENDEM) =================
    if (
        trend_up and
        r <= 45 and
        price > e_fast
    ):
        signal = {
            "side": "LONG",
            "entry": round(price, 2),
            "sl": round(price - a * 1.2, 2),
            "tp": round(price + a * 2.5, 2),
            "trend": "UP",
            "ema200": round(ema200, 2),
            "reason": "RSI pullback in uptrend"
        }

    # ================= SHORT (TYLKO Z TRENDEM) =================
    elif (
        trend_down and
        r >= 55 and
        price < e_fast
    ):
        signal = {
            "side": "SHORT",
            "entry": round(price, 2),
            "sl": round(price + a * 1.2, 2),
            "tp": round(price - a * 2.5, 2),
            "trend": "DOWN",
            "ema200": round(ema200, 2),
            "reason": "RSI pullback in downtrend"
        }

    # ================= DEDUPLIKACJA =================
    if signal:
        if _is_duplicate(symbol, signal["side"]):
            return None

        _save_alert(symbol, signal["side"])
        return signal

    return None

def gold_m15_pullback(symbol, payload):
    print(
        f"GOLD DEBUG | price={price} ema50={round(ema50, 2)} "
        f"ema200_h1={round(htf['ema200'], 2)} rsi={round(r, 1)} "
        f"trend_up={trend_up} session={is_gold_session_open()}"
    )

    # ======================
    # SESSION FILTER
    # ======================
    if not is_gold_session_open():
        return None

    # ======================
    # DATA
    # ======================
    ltf = payload["ltf"]
    htf = payload["htf"]

    o, h, l, c = ltf["o"], ltf["h"], ltf["l"], ltf["c"]
    price = c[-2]

    ema50 = ema(c, 50)
    r = rsi(c)

    trend_up = price > htf["ema200"]
    trend_down = price < htf["ema200"]

    d1_high = htf["d1_high"]
    d1_low = htf["d1_low"]

    # ======================
    # UNLOCK JEŚLI TREND SIĘ ZMIENIŁ
    # ======================
    if trend_up and _gold_lock["side"] == "SHORT":
        gold_update_lock(None)
    elif trend_down and _gold_lock["side"] == "LONG":
        gold_update_lock(None)

    # ======================
    # ATR (RISK)
    # ======================
    a = atr(h, l, c)

    # ======================
    # LONG
    # ======================
    if trend_up and price > ema50 and 40 <= r <= 50:
        if gold_is_locked("LONG"):
            return None

        sl, tp = calculate_sl_tp(
            side="LONG",
            entry=price,
            atr=a,
            pattern="Pullback",
            market="GOLD"
        )

        tp = min(tp, d1_high)  # clamp TP do D1 high
        gold_update_lock("LONG")

        return {
            "side": "LONG",
            "entry": round(price, 2),
            "sl": sl,
            "tp": tp,
            "pattern": "Pullback",
            "reason": "GOLD M15 EMA50 pullback + RSI (HTF uptrend)"
        }

    # ======================
    # SHORT
    # ======================
    if trend_down and price < ema50 and 50 <= r <= 60:
        if gold_is_locked("SHORT"):
            return None

        sl, tp = calculate_sl_tp(
            side="SHORT",
            entry=price,
            atr=a,
            pattern="Pullback",
            market="GOLD"
        )

        tp = max(tp, d1_low)  # clamp TP do D1 low
        gold_update_lock("SHORT")

        return {
            "side": "SHORT",
            "entry": round(price, 2),
            "sl": sl,
            "tp": tp,
            "pattern": "Pullback",
            "reason": "GOLD M15 EMA50 pullback + RSI (HTF downtrend)"
        }

    return None
