from webhook_alerts import send_alert
import config

test_data = {
    "side": "LONG",
    "entry": 2600,
    "sl": 2550,
    "tp": 2700,
    "rsi": 58,
    "ema": "↑ trend",
    "atr": 2.5
}

send_alert(
    webhook=config.DISCORD_WEBHOOK,
    title="XAUUSD",
    data=test_data
)

print("TEST ALERT SENT")
