from datetime import datetime, timezone, date

from app.modules.tenant.business_days import add_business_days


def test_add_business_days_skips_weekends():
    start = datetime(2026, 1, 2, 10, 0, tzinfo=timezone.utc)  # Friday
    result = add_business_days(
        start=start,
        days=1,
        weekend_days=[5, 6],
        holidays=[],
        saturday_is_business_day=False,
        cutoff_hour=17,
    )
    # Next business day should be Monday (Jan 5, 2026)
    assert result.date() == date(2026, 1, 5)


def test_add_business_days_respects_holiday():
    start = datetime(2026, 1, 5, 10, 0, tzinfo=timezone.utc)  # Monday
    holiday = date(2026, 1, 6)
    result = add_business_days(
        start=start,
        days=1,
        weekend_days=[5, 6],
        holidays=[holiday],
        saturday_is_business_day=False,
        cutoff_hour=17,
    )
    # Skip holiday, so next business day is Jan 7, 2026
    assert result.date() == date(2026, 1, 7)


def test_cutoff_hour_rolls_forward():
    start = datetime(2026, 1, 5, 18, 0, tzinfo=timezone.utc)  # After cutoff
    result = add_business_days(
        start=start,
        days=1,
        weekend_days=[5, 6],
        holidays=[],
        saturday_is_business_day=False,
        cutoff_hour=17,
    )
    # After cutoff, start is treated as next day (Jan 6), so +1 business day = Jan 7
    assert result.date() == date(2026, 1, 7)
