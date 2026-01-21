import datetime
import config
from webhook_alerts import send_alert
import csv
import os
from datetime import datetime
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
ddef handle_gold_signal(symbol, signal_code, price):
    if signal_code == 0:
        return

    if not cooldown_ok(symbol):
        return

    side = "LONG" if signal_code == 1 else "SHORT"
    now = datetime.utcnow().isoformat()

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

    log_gold_alert(now, symbol, side, price)
    _last_alert_time[symbol] = datetime.utcnow()

LOG_FILE = "logs/alerts_gold.csv"
os.makedirs("logs", exist_ok=True)


def log_gold_alert(timestamp, symbol, side, price):
    file_exists = os.path.isfile(LOG_FILE)

    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "symbol", "side", "price"])

        writer.writerow([timestamp, symbol, side, price])
