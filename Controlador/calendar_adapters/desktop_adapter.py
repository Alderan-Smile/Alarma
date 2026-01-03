import json
from datetime import datetime
from pathlib import Path

STORE = Path(__file__).parent.parent.parent / 'Resources' / 'calendar_events.json'
STORE.parent.mkdir(parents=True, exist_ok=True)

def _load_store():
    if not STORE.exists():
        return []
    return json.loads(STORE.read_text(encoding='utf-8'))

def _save_store(data):
    STORE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')

def create_event(dt: datetime, title: str, description: str):
    """Create a simple event representation for desktop testing.

    This does NOT integrate with OS calendar. It stores events in
    `Resources/calendar_events.json` so you can inspect scheduled alarms.
    """
    data = _load_store()
    event = {
        'id': len(data) + 1,
        'datetime': dt.isoformat(),
        'title': title,
        'description': description,
    }
    data.append(event)
    _save_store(data)
    print(f"[desktop_adapter] Event created: {event}")
    return event['id']
