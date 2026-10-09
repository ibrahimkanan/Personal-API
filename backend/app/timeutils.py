import os
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv()

# "Today" must follow YOUR local day, not the database's (UTC on Neon).
# Otherwise something logged at 1am Amman time lands on "yesterday".
APP_TZ_NAME = os.getenv("APP_TIMEZONE", "Asia/Amman")
APP_TZ = ZoneInfo(APP_TZ_NAME)


def utcnow() -> datetime:
    """Timezone-aware 'now'. Always use this instead of datetime.utcnow(),
    because timestamptz columns come back timezone-aware and mixing aware
    with naive datetimes raises TypeError."""
    return datetime.now(timezone.utc)


def local_today() -> date:
    return datetime.now(APP_TZ).date()


def day_bounds(d: date):
    """[start, end) of local day d, as aware datetimes."""
    start = datetime.combine(d, time.min, tzinfo=APP_TZ)
    return start, start + timedelta(days=1)