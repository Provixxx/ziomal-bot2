import csv
import os
from datetime import datetime

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "signals_gold.csv")

os.makedirs(LOG_DIR, exist_ok=True)


def log_signal(signal, price):
    file_exists = os.path.isfile(LOG_FILE)

    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "signal", "price"])

        writer.writerow([
            datetime.utcnow().isoformat(),
            signal,
            round(price, 2)
        ])
