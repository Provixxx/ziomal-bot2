_run_count = 0

from logger import logger
from data import get_gold_candles
from analyzer import GoldAnalyzer
from webhook_alerts import send_alert
from signals_log import log_signal
import time
logger.info("GOLD BOT MVP START")
_last_signal = None

def run_once():
    global _run_count
    _run_count += 1
    logger.info(f"RUN #{_run_count}")
    df = get_gold_candles()
    if df is None or df.empty:
        logger.warning("No data fetched – skipping cycle")
        return

    analyzed = GoldAnalyzer(df).analyze()
    last = analyzed.iloc[-1]

    logger.info(
        f"STATE | close={last['close']:.2f} "
        f"ema_fast={last['ema_fast']:.2f} "
        f"ema_slow={last['ema_slow']:.2f} "
        f"rsi={last['rsi']:.1f} "
        f"signal={last['signal']}"
    )

    global _last_signal

    if last["signal"] in ("LONG", "SHORT") and last["signal"] != _last_signal:
        send_alert(
            signal=last["signal"],
            price=last["close"],
            sl=last["sl"],
            tp=last["tp"]
        )

        log_signal(last["signal"], last["close"])
        _last_signal = last["signal"]

    if last["signal"] == "NONE":
        _last_signal = None


if __name__ == "__main__":
    while True:
        run_once()
        logger.info("sleep 5 minutes")
        time.sleep(300)

