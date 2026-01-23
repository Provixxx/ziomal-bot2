print("### USING alerts.py ###")
from webhook_alerts import send_alert as _send_webhook
from config import DISCORD_WEBHOOK
from logger import logger


def send_alert(signal, price):
    """
    Adapter zgodny 1:1 ze starym webhook_alerts.py
    """
    data = {
        "side": signal,
        "entry": round(price, 2),
        "sl": "n/a",
        "tp": "n/a",
        "rsi": "n/a",
        "ema": "n/a",
        "atr": "n/a"
    }

    try:
        _send_webhook(
            webhook=DISCORD_WEBHOOK,
            title="PAXGUSDT",
            data=data
        )
        logger.info("Discord alert sent")
    except Exception as e:
        logger.error(f"Alert error: {e}")
