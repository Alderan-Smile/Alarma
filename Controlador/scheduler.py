from datetime import date, datetime, timedelta, time as dtime
from typing import Optional
from pathlib import Path

from . import dbcon
from .calendar_adapters import adapter as calendar_adapter
try:
    from dateutil.rrule import rrulestr
    from dateutil.rrule import rrule
    from dateutil.parser import parse as dateutil_parse
    _HAS_DATEUTIL = True
except Exception:
    _HAS_DATEUTIL = False


def _is_workday(d: date, holidays_set: set, weekdays: set):
    if d.weekday() not in weekdays:
        return False
    if d.isoformat() in holidays_set:
        return False
    return True


def schedule_recurring_workday_alarms(conn, country_code: str, start_date: Optional[date] = None, hour: int = 9, minute: int = 0, occurrences: int = 10, weekdays: Optional[set] = None):
    """Schedule `occurrences` next workday alarms for `country_code`, skipping weekends and holidays.

    This function reads holidays from the DB via `dbcon.fetch_holidays_by_country` and
    creates individual events via the calendar adapter. It returns the number of events created.
    """
    if start_date is None:
        start_date = date.today()

    if weekdays is None:
        weekdays = set(range(0, 5))  # default Mon-Fri

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
        if _is_workday(d, holidays_set, weekdays):
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


def schedule_with_rule(conn, country_code: str, start_date: Optional[date] = None, hour: int = 9, minute: int = 0,
                       occurrences: int = 10, rule: dict = None):
    """Schedule events according to a recurrence rule dict.

    Supported rule formats:
    - {'type': 'weekly', 'interval': 1, 'weekdays': {0,1,2}}  # 0=Mon..6=Sun
    - {'type': 'monthly', 'bymonthday': 15}  # day of month
    - {'type': 'rrule', 'rrule': 'RRULE:FREQ=WEEKLY;COUNT=10;BYDAY=MO,TU'}  # dateutil rrule string

    Returns number of scheduled events.
    """
    if rule is None:
        return schedule_recurring_workday_alarms(conn, country_code, start_date, hour, minute, occurrences)

    if start_date is None:
        start_date = date.today()

    scheduled = 0
    if rule.get('type') == 'weekly':
        interval = int(rule.get('interval', 1))
        weekdays = rule.get('weekdays', set(range(0, 5)))
        # simple generator: walk days forward and pick matching weekdays with interval
        d = start_date
        step = 0
        while scheduled < occurrences:
            if d.weekday() in weekdays:
                if step % interval == 0:
                    dt = datetime.combine(d, dtime(hour, minute))
                    calendar_adapter.create_event(dt, 'Alarma laboral', 'Alarma recurrente')
                    scheduled += 1
            d = d + timedelta(days=1)
            step += 1
        return scheduled

    if rule.get('type') == 'monthly':
        bymonthday = int(rule.get('bymonthday', start_date.day))
        d = start_date
        while scheduled < occurrences:
            if d.day == bymonthday:
                dt = datetime.combine(d, dtime(hour, minute))
                calendar_adapter.create_event(dt, 'Alarma laboral', 'Alarma mensual')
                scheduled += 1
                # move to next month
                d = (d.replace(day=1) + timedelta(days=32)).replace(day=bymonthday)
            else:
                d = d + timedelta(days=1)
        return scheduled

    if rule.get('type') == 'rrule':
        if not _HAS_DATEUTIL:
            raise NotImplementedError('python-dateutil no está instalado; RRULE no disponible')
        rrule_str = rule.get('rrule')
        if not rrule_str:
            raise ValueError('No se proporcionó rrule')
        # rrulestr returns an rrule/rruleset that yields datetimes
        rs = rrulestr(rrule_str, dtstart=datetime.combine(start_date, dtime(hour, minute)))
        for dt in rs:
            calendar_adapter.create_event(dt, 'Alarma laboral', 'Alarma RRULE')
            scheduled += 1
            if scheduled >= occurrences:
                break
        return scheduled

    # fallback: no rule recognized
    return 0
