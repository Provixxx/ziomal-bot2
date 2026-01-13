import requests

def send_alert(webhook, title, data):
    side = data["side"]
    color = 15158332 if side == "SHORT" else 3066993
    emoji = "🔴" if side == "SHORT" else "🟢"

    payload = {
        "content": "@everyone",
        "embeds": [{
            "title": f"🚨 ALARM: {title}",
            "description": f"**KIERUNEK:** {emoji} **{side}**",
            "color": color,
            "fields": [
                {
                    "name": "💰 AKTUALNA CENA",
                    "value": f"${data['entry']}",
                    "inline": False
                },
                {
                    "name": "🛑 STOP LOSS",
                    "value": f"${data['sl']}",
                    "inline": True
                },
                {
                    "name": "🎯 TAKE PROFIT",
                    "value": f"${data['tp']}",
                    "inline": True
                },
                {
                    "name": "📊 WSKAŹNIKI",
                    "value": (
                        f"**RSI:** {data['rsi']}% *(momentum)*\n"
                        f"**EMA:** {data['ema']} *(trend)*\n"
                        f"**ATR:** {data['atr']}% *(zmienność)*"
                    ),
                    "inline": False
                }
            ],
            "footer": {
                "text": "Legenda: RSI=siła ruchu | EMA=kierunek trendu | ATR=zmienność"
            }
        }]
    }

    requests.post(webhook, json=payload, timeout=10)
