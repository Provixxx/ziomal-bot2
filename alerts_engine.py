import datetime
import config
from webhook_alerts import send_alert

# ======================================
# COOLDOWN (CZASOWY, NIE KIERUNKOWY)
# ======================================
_last_alert_time = {}


def cooldown_ok(symbol, minutes=30):
    now = datetime.datetime.utcnow()
    last = _last_alert_time.get(symbol)

    if not last:
        return True

    return (now - last).total_seconds() >= minutes * 60


# ======================================
# ALERT HANDLER
# ======================================
def handle_gold_signal(symbol, signal_code, price):
    """
    signal_code:
        1  -> LONG
        -1 -> SHORT
        0  -> brak sygnału
    """
    if signal_code == 0:
        return

    if not cooldown_ok(symbol):
        return

    side = "LONG" if signal_code == 1 else "SHORT"

    send_alert(
        webhook=config.DISCORD_WEBHOOK,
        title=f"🟡 GOLD SIGNAL ({side})",
        data={
            "symbol": symbol,
            "side": side,
            "price": round(price, 2),
            "source": "GoldAnalyzer V2"
        }
    )

    _last_alert_time[symbol] = datetime.datetime.utcnow()
