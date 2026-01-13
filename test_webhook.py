from webhook_alerts import send_alert

WEBHOOK = "https://discord.com/api/webhooks/1451632628842365013/FkOAiiIesLb18Ox_Fs9JaLj2Z_LZ-TLnayjS7Kkc0z1SW00s7WWlweHAATZdN2EgJ_8T"

test_data = {
    "side": "LONG",
    "entry": 100.0,
    "sl": 95.0,
    "tp": 110.0,
    "rsi": 55,
    "ema": 102,
    "atr": 2.5
}

send_alert(
    webhook=WEBHOOK,
    title="🧪 TEST WEBHOOK ALERT",
    data=test_data
)
