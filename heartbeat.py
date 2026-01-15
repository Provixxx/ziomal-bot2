# heartbeat.py
import datetime

_last_ping = {
    "london": None,
    "ny": None
}

def should_ping(session: str, hour_utc: int):
    today = datetime.date.today()

    if _last_ping[session] == today:
        return False

    now_h = datetime.datetime.now(datetime.UTC).hour

    if now_h == hour_utc:
        _last_ping[session] = today
        return True

    return False
