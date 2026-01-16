print("🔥 MAIN.PY STARTED 🔥")

import time
import datetime
import threading
import config

from api_us import get_us_candles
from analyzer_stocks import analyze_stock

from analyzer_crypto import get_btc_candles, analyze_btc
from analyzer_gold import get_gold_candles, analyze_gold

from heartbeat import should_ping
from webhook_alerts import send_alert

import web_server

# ======================
# WEB SERVER (KOYEB HEALTHCHECK)
# ======================
threading.Thread(
    target=web_server.start_web,
    daemon=True
).start()

# ======================
# TIME RANGE (STOCKS)
# ======================
END = int(time.time())
START = END - 60 * 60 * 24 * 5  # 5 dni historii


def run():
    now = datetime.datetime.now(datetime.UTC)

    # ======================
    # HEARTBEAT (SESSION OPEN)
    # ======================

    # London session: 07:00–07:15 UTC
    if should_ping("london", 7, 0, 15):
        send_alert(
            config.ALERT_WEBHOOK_URL,
            "SYSTEM",
            {"status": "🟢 GOLD BOT LIVE – London session open"}
        )

    # NY session: 14:30–14:45 UTC
    if should_ping("ny", 14, 30, 45):
        send_alert(
            config.ALERT_WEBHOOK_URL,
            "SYSTEM",
            {"status": "🟢 GOLD BOT LIVE – NY session open"}
        )

    print(f"[HEARTBEAT] scan ok {now}")

    # ======================
    # STOCKS (MTF)
    # ======================
    print("=== STOCKS MTF ===")
    for symbol in config.STOCKS_US:
        h1 = get_us_candles(symbol, "60", START, END)
        m5 = get_us_candles(symbol, "5", START, END)

        if h1 and m5:
            analyze_stock(symbol, m5, h1)

        time.sleep(1.2)  # rate limit

    # ======================
    # BTC
    # ======================
    print("=== BTC ===")
    btc = get_btc_candles()
    if btc:
        analyze_btc(btc)

    # ======================
    # GOLD
    # ======================
    print("=== GOLD ===")
    gold = get_gold_candles()
    if gold:
        analyze_gold(gold)


# ======================
# MAIN LOOP (5 MIN)
# ======================
if __name__ == "__main__":
    while True:
        run()
        print("⏳ sleep 5 min")
        time.sleep(300)
