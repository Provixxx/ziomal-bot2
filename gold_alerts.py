# gold_alerts.py
import time
import config
from webhook_alerts import send_trade_alert
from candle_patterns import detect_candle_pattern
from atr import calculate_atr

# ======================================================
# KONFIG GOLD (PRO)
# ======================================================
RSI_OVERSOLD = 35
RSI_OVERBOUGHT = 65

MIN_ATR_PCT = 0.0025      # 0.25% ceny (filtr konsolidacji)
GOLD_COOLDOWN = 1800      # 30 minut

_last_gold_alert_ts = 0

def ema_trend_filter(price, ema50, ema200, side):
    if not ema50 or not ema200:
        return False

    if side == "LONG":
        return price > ema50 > ema200

    if side == "SHORT":
        return price < ema50 < ema200

    return False

# ======================================================
# GOLD ALERT LOGIC (RSI + PATTERN + ATR)
# ======================================================
async def check_gold_alert(opens, highs, lows, closes, rsi):
    global _last_gold_alert_ts

    now = time.time()
    diff = now - _last_gold_alert_ts
    print(f"⏱ GOLD cooldown diff: {diff:.0f}s")

    if diff < GOLD_COOLDOWN:
        print("⛔ GOLD cooldown aktywny")
        return

    price = closes[-1]
    atr = calculate_atr(highs, lows, closes)

    if not atr:
        print("⛔ GOLD ATR brak")
        return

    # --- filtr zmienności ---
    if atr < price * MIN_ATR_PCT:
        print("⛔ GOLD konsolidacja (ATR za małe)")
        return

    pattern = detect_candle_pattern(opens, highs, lows, closes)
    if not pattern:
        print("⛔ GOLD brak patternu")
        return

    # ==================================================
    # 🟢 LONG
    # ==================================================
    if rsi <= RSI_OVERSOLD and pattern in ["Hammer", "Bullish Engulfing"]:
        side = "LONG"
        sl = round(price - atr * 1.2, 2)
        tp = round(price + atr * 2.4, 2)

    # ==================================================
    # 🔴 SHORT
    # ==================================================
    elif rsi >= RSI_OVERBOUGHT and pattern in ["Shooting Star", "Bearish Engulfing"]:
        side = "SHORT"
        sl = round(price + atr * 1.2, 2)
        tp = round(price - atr * 2.4, 2)

    else:
        print("⛔ GOLD brak konfluencji")
        return

    # ==================================================
    # ALERT
    # ==================================================
    send_trade_alert(
        webhook_url=config.ALERT_WEBHOOK_URL,
        instrument="XAUUSD",
        side=side,
        entry=price,
        tp=tp,
        sl=sl,
        daily_change=0.0,
        rsi=rsi,
        pattern=pattern
    )

    _last_gold_alert_ts = now
    print("✅ GOLD ALERT SENT")
