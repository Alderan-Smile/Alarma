import sys
from pathlib import Path

if sys.platform.startswith('linux') or sys.platform.startswith('win') or sys.platform.startswith('darwin'):
    from .desktop_adapter import create_event
else:
    # On Android/other platforms, try to import platform adapter (may raise)
    try:
        from .android_adapter import create_event
    except Exception:
        def create_event(dt, title, description):
            raise NotImplementedError('Calendar adapter for this platform is not implemented')
