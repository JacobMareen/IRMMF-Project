from __future__ import annotations

from datetime import datetime, timedelta, date
from typing import Iterable


def add_business_days(
    start: datetime,
    days: int,
    weekend_days: Iterable[int],
    holidays: Iterable[date],
    saturday_is_business_day: bool,
    cutoff_hour: int,
) -> datetime:
    if days <= 0:
        return start

    holiday_set = {h for h in holidays}
    weekend_set = set(weekend_days)
    if saturday_is_business_day and 5 in weekend_set:
        weekend_set.remove(5)

    current = start
    if cutoff_hour is not None and current.hour >= cutoff_hour:
        current = current + timedelta(days=1)

    added = 0
    while added < days:
        current = current + timedelta(days=1)
        if _is_business_day(current.date(), weekend_set, holiday_set):
            added += 1

    return current


def _is_business_day(target: date, weekend_days: set[int], holidays: set[date]) -> bool:
    if target in holidays:
        return False
    if target.weekday() in weekend_days:
        return False
    return True
