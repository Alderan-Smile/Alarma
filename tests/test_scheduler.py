import sys
from datetime import date, datetime
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from Controlador import scheduler, dbcon


def test_schedule_recurring_workday_alarms_mon_fri(tmp_path, monkeypatch):
    # use in-memory DB
    conn = dbcon.get_db_connection(':memory:')
    dbcon.create_tables(conn)

    events = []

    def fake_create_event(dt, title, description):
        events.append(dt)

    # monkeypatch adapter
    import Controlador.calendar_adapters.adapter as adapter
    adapter.create_event = fake_create_event

    start = date(2026, 1, 5)  # Monday
    scheduled = scheduler.schedule_recurring_workday_alarms(conn, 'AD', start_date=start, hour=9, minute=0, occurrences=3, weekdays=set(range(0,5)))
    assert scheduled == 3
    assert len(events) == 3
    assert events[0].date() == start


def test_schedule_with_rrule(monkeypatch):
    # Skip if dateutil not available
    try:
        from dateutil.rrule import rrulestr
    except Exception:
        return

    events = []

    def fake_create_event(dt, title, description):
        events.append(dt)

    import Controlador.calendar_adapters.adapter as adapter
    adapter.create_event = fake_create_event

    # simple weekly RRULE: every Monday for 3 occurrences, starting 2026-01-05
    start = date(2026, 1, 5)
    rrule_str = 'RRULE:FREQ=WEEKLY;BYDAY=MO;COUNT=3'
    scheduled = scheduler.schedule_with_rule(None, 'AD', start_date=start, hour=8, minute=30, occurrences=3, rule={'type':'rrule','rrule': rrule_str})
    assert scheduled == 3
    assert len(events) == 3
    assert all(isinstance(d, datetime) for d in events)
