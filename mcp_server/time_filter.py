from datetime import datetime, timedelta, timezone
from typing import Tuple

def get_time_range(period: str) -> Tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)
    today = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)

    if not period:
        period = "last 30 days"

    p = period.lower().strip()

    if "last" in p and "day" in p:
        try:
            num_days = int(p.split("last")[1].split("day")[0].strip())
        except Exception:
            num_days = 30
        start = now - timedelta(days=num_days)
        return start, now

    if "this week" in p:
        start = today - timedelta(days=today.weekday())
        return start, now

    if "last week" in p:
        start = today - timedelta(days=today.weekday() + 7)
        end = start + timedelta(days=7)
        return start, end

    if "this month" in p:
        start = today.replace(day=1)
        return start, now

    if "last month" in p:
        first_of_this_month = today.replace(day=1)
        last_month_end = first_of_this_month - timedelta(days=1)
        start = last_month_end.replace(day=1)
        end = last_month_end.replace(hour=23, minute=59, second=59)
        return start, end

    if p == "today":
        return today, now

    if p == "yesterday":
        start = today - timedelta(days=1)
        return start, today

    start = now - timedelta(days=30)
    return start, now
