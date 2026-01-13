from alerts_engine import send_stock_alert
import datetime
import config

def analyze_stock(symbol, data_m5, data_h1):
    closes_h1 = data_h1["c"]
    closes_m5 = data_m5["c"]

    # DEBUG – heartbeat analyzera
    print(f"[STOCKS] analyzing {symbol}")

    # --- FILTR TRENDU (H1) ---
    if len(closes_h1) < 10:
        print(f"[{symbol}] H1 too short")
        return

    if closes_h1[-1] <= closes_h1[-5]:
        print(f"[{symbol}] H1 trend NO")
        return

    # --- WEJŚCIE (M5) ---
    if closes_m5[-1] <= closes_m5[-2]:
        print(f"[{symbol}] M5 no trigger")
        return

    entry = round(closes_m5[-1], 2)

    send_stock_alert(symbol, {
        "side": "LONG",
        "entry": entry,
        "sl": round(entry * 0.97, 2),
        "tp": round(entry * 1.05, 2),
        "rsi": "n/a",
        "ema": "n/a",
        "atr": "n/a"
    })

    print(f"[ALERT] {symbol} sent at {datetime.datetime.now()}")
