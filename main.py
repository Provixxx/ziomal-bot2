print("🔥 MAIN.PY V2 STARTED 🔥")

import time
import datetime
import threading
import config

from heartbeat import should_ping
from webhook_alerts import send_alert
from alerts_engine import handle_gold_signal

from analyzer_gold import GoldAnalyzer
from analyzer_crypto import CryptoAnalyzer  # analogiczny V2

from api_us import get_us_candles
from analyzer_stocks import analyze_stock

import web_server


# ======================
# WEB SERVER (HEALTHCHECK)
# ======================
threading.Thread(
    target=web_server.start_web,
    daemon=True
).start()


# ======================
# HEARTBEAT
# ======================
def heartbeat():
    if should_ping("london", 7, 0, 15):
        send_alert(
            config.ALERT_WEBHOOK_URL,
            "SYSTEM",
            {"status": "🟢 BOT LIVE – London session open"}
        )

    if should_ping("ny", 14, 30, 45):
        send_alert(
            config.ALERT_WEBHOOK_URL,
            "SYSTEM",
            {"status": "🟢 BOT LIVE – NY session open"}
        )


# ======================
# GOLD PIPELINE (V2)
# ======================
def run_gold():
    from api_pl import get_gold_candles  # ważne: lokalny import

    df = get_gold_candles()
    if df is None or len(df) < 30:
        return

    analyzed = GoldAnalyzer(df).analyze()
    last = analyzed.iloc[-1]

    handle_gold_signal(
        symbol="XAUUSD",
        signal_code=last["signal_code"],
        price=last["close"]
    )


# ======================
# BTC PIPELINE (V2)
# ======================
def run_btc():
    from analyzer_crypto import get_btc_candles

    df = get_btc_candles()
    if df is None or len(df) < 30:
        return

    analyzed = CryptoAnalyzer(df).analyze()
    last = analyzed.iloc[-1]

    # analogiczny handler BTC
    # handle_crypto_signal(...)


# ======================
# STOCKS (LEGACY – zostawiamy)
# ======================
def run_stocks():
    END = int(time.time())
    START = END - 60 * 60 * 24 * 5

    for symbol in config.STOCKS_US:
        h1 = get_us_candles(symbol, "60", START, END)
        m5 = get_us_candles(symbol, "5", START, END)

        if h1 and m5:
            analyze_stock(symbol, m5, h1)

        time.sleep(1.2)


# ======================
# MAIN LOOP (5 MIN)
# ======================
if __name__ == "__main__":
    while True:
        now = datetime.datetime.now(datetime.UTC)
        print(f"[LOOP] {now}")

        heartbeat()
        run_gold()
        run_btc()
        run_stocks()

        print("⏳ sleep 5 min")
        time.sleep(300)
