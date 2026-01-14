print("🔥 MAIN.PY STARTED 🔥")

import time
import config
import datetime
import threading

from api_us import get_us_candles
from analyzer_stocks import analyze_stock

from analyzer_crypto import get_btc_candles, analyze_btc
from analyzer_gold import get_gold_candles, analyze_gold

import web_server
threading.Thread(target=web_server.start_web, daemon=True).start()

# ======================
# TIME RANGE
# ======================
END = int(time.time())
START = END - 60 * 60 * 24 * 5

def run():
    print(f"[HEARTBEAT] scan ok {datetime.datetime.now()}")

    # ===== STOCKS (MTF) =====
    print("=== STOCKS MTF ===")
    for s in config.STOCKS_US:
        h1 = get_us_candles(s, "60", START, END)
        m5 = get_us_candles(s, "5", START, END)

        if h1 and m5:
            analyze_stock(s, m5, h1)

        time.sleep(1.2)

    # ===== BTC =====
    print("=== BTC ===")
    btc = get_btc_candles()
    if btc:
        analyze_btc(btc)

    # ===== GOLD =====
    print("=== GOLD ===")
    gold = get_gold_candles()
    if gold:
        analyze_gold(gold)

if __name__ == "__main__":
    while True:
        run()
        print("⏳ sleep 5 min")
        time.sleep(300)  # 5 minut

