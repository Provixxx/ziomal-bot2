# heartbeat.py
import datetime

_last_ping = {
    "london": None,
    "ny": None
}

def should_ping(session: str, hour_utc: int, minute_from=0, minute_to=59):
    today = datetime.date.today()
    now = datetime.datetime.now(datetime.UTC)

    if _last_ping[session] == today:
        return False

    if now.hour == hour_utc and minute_from <= now.minute <= minute_to:
        _last_ping[session] = today
        return True

    return False
