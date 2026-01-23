import requests
from config import DISCORD_WEBHOOK


def send_alert(signal, price, sl=None, tp=None):
    """
    Prosty, czytelny alert GOLD
    """
    lines = [
        f"🟡 GOLD ALERT | {signal}",
        f"ENTRY: {round(price, 2)}"
    ]

    if sl is not None:
        lines.append(f"SL: {sl}")
    if tp is not None:
        lines.append(f"TP: {tp}")

    payload = {
        "content": "\n".join(lines)
    }

    requests.post(DISCORD_WEBHOOK, json=payload, timeout=10)
