from datetime import date, datetime, timedelta, time as dtime
from typing import Optional
from pathlib import Path

from . import dbcon
from .calendar_adapters import adapter as calendar_adapter


def _is_workday(d: date, holidays_set: set):
    if d.weekday() >= 5:
        return False
    if d.isoformat() in holidays_set:
        return False
    return True


def schedule_recurring_workday_alarms(conn, country_code: str, start_date: Optional[date] = None, hour: int = 9, minute: int = 0, occurrences: int = 10):
    """Schedule `occurrences` next workday alarms for `country_code`, skipping weekends and holidays.

    This function reads holidays from the DB via `dbcon.fetch_holidays_by_country` and
    creates individual events via the calendar adapter. It returns the number of events created.
    """
    if start_date is None:
        start_date = date.today()

    year = start_date.year
    # Load holidays for current year (if occurrences span next year, this should be extended)
    holidays = dbcon.fetch_holidays_by_country(conn, country_code, year)
    holidays_set = set(h.date for h in holidays)

    scheduled = 0
    d = start_date
    attempts = 0
    max_attempts = occurrences * 10 + 365  # safety
    while scheduled < occurrences and attempts < max_attempts:
        attempts += 1
        if _is_workday(d, holidays_set):
            dt = datetime.combine(d, dtime(hour, minute))
            title = 'Alarma laboral'
            description = 'Alarma programada para día laboral, omitiendo feriados y fines de semana.'
            calendar_adapter.create_event(dt, title, description)
            scheduled += 1
        d = d + timedelta(days=1)
        # if we pass into next year, load holidays for that year
        if d.year != year:
            year = d.year
            more = dbcon.fetch_holidays_by_country(conn, country_code, year)
            holidays_set.update(h.date for h in more)

    return scheduled
