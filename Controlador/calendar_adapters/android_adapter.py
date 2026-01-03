def create_event(dt, title, description):
  """Attempt to create an event on Android using pyjnius and CalendarContract.

  This implementation tries to use `pyjnius`. When running on Android (via Briefcase),
  `pyjnius` should be available and the app should request `WRITE_CALENDAR` permission
  at runtime before calling this.

  If `pyjnius` is not available or an error occurs, this will raise NotImplementedError
  with guidance for how to implement it when packaging to Android.
  """
  try:
    from jnius import autoclass, cast
  except Exception as e:
    raise NotImplementedError('pyjnius no disponible. Implementar Android CalendarContract usando pyjnius cuando empaquetes con Briefcase.')

  try:
    # Minimal example: insert an event via ContentResolver
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    activity = PythonActivity.mActivity
    ContentValues = autoclass('android.content.ContentValues')

    resolver = activity.getContentResolver()
    values = ContentValues()
    values.put('title', title)
    values.put('description', description)
    # times in milliseconds
    startMillis = int(dt.timestamp() * 1000)
    values.put('dtstart', startMillis)
    values.put('dtend', startMillis + 60 * 60 * 1000)  # 1 hour
    values.put('eventTimezone', 'UTC')

    # Try to find a usable calendar_id
    cal_id = find_calendar_id(activity)
    if cal_id is None:
      raise NotImplementedError('No se pudo encontrar calendar_id. Asegúrate de dar permisos y tener al menos un calendario.')
    values.put('calendar_id', cal_id)

    Events = autoclass('android.provider.CalendarContract$Events')
    uri = resolver.insert(Events.CONTENT_URI, values)
    return uri
  except Exception as e:
    raise NotImplementedError(f'Error al insertar evento en Android: {e}')


def ensure_calendar_permissions():
  """Check and request calendar permissions on Android. Returns True if already granted, False if requested now.

  Note: requestPermissions is asynchronous; the app should handle the callback. This helper requests permissions
  and returns False to indicate permissions were requested.
  """
  try:
    from jnius import autoclass
  except Exception:
    raise NotImplementedError('pyjnius no disponible. No se pueden gestionar permisos en este entorno.')

  ActivityCompat = autoclass('androidx.core.app.ActivityCompat')
  Manifest = autoclass('android.Manifest')
  PackageManager = autoclass('android.content.pm.PackageManager')
  PythonActivity = autoclass('org.kivy.android.PythonActivity')
  activity = PythonActivity.mActivity

  perms = [Manifest.permission.WRITE_CALENDAR, Manifest.permission.READ_CALENDAR]
  missing = []
  for p in perms:
    if ActivityCompat.checkSelfPermission(activity, p) != PackageManager.PERMISSION_GRANTED:
      missing.append(p)
  if missing:
    # Try event-based callback approach: register a waiter and request permissions.
    try:
      from threading import Event
    except Exception:
      Event = None

    # If Java Activity is instrumented to call `permission_callback(requestCode, permissions, grantResults)`
    # then `PermissionAwaiter` below will be notified and we can wait on an Event.
    from .android_adapter import PermissionAwaiter
    awaiter = PermissionAwaiter.get_instance()
    awaiter.clear()
    ActivityCompat.requestPermissions(activity, missing, 1)
    # First try to observe a Java-side PermissionBridge if the Android project added it.
    try:
      # Try to find PermissionBridge class in the app package (works with Briefcase/BeeWare)
      pkg = activity.getPackageName()
      bridge_cls = f"{pkg}.PermissionBridge"
      PermissionBridge = None
      try:
        PermissionBridge = autoclass(bridge_cls)
      except Exception:
        try:
          # fallback to the example package used by the repo
          PermissionBridge = autoclass('org.example.alarma.PermissionBridge')
        except Exception:
          PermissionBridge = None

      # If we have a bridge, poll it briefly for results
      if PermissionBridge is not None:
        import time as _time
        timeout = 15
        elapsed = 0
        interval = 0.5
        granted = None
        while elapsed < timeout:
          try:
            res = PermissionBridge.getLastGrantResults()
          except Exception:
            res = None
          if res is not None and len(res) > 0:
            # interpret results
            ok = True
            for i in range(len(res)):
              if res[i] != 0:
                ok = False
                break
            granted = ok
            break
          _time.sleep(interval)
          elapsed += interval
      else:
        granted = None
    except Exception:
      granted = None

    # If PermissionBridge didn't provide results, check for Python callback awaiter (set by permission_callback)
    if granted is None:
      granted = awaiter.wait(timeout=15)
    if granted is None:
      # fallback: poll for permission status
      import time as _time
      timeout = 15
      elapsed = 0
      interval = 0.5
      while elapsed < timeout:
        all_granted = True
        for p in perms:
          if ActivityCompat.checkSelfPermission(activity, p) != PackageManager.PERMISSION_GRANTED:
            all_granted = False
            break
        if all_granted:
          return True
        _time.sleep(interval)
        elapsed += interval
      return False
    return granted
  return True


def find_calendar_id(activity):
  """Attempt to find an appropriate calendar_id on the device; returns int or None.

  This function queries CalendarContract.Calendars and returns the first calendar _id.
  """
  try:
    from jnius import autoclass
  except Exception:
    return None

  try:
    resolver = activity.getContentResolver()
    Calendars = autoclass('android.provider.CalendarContract$Calendars')
    uri = Calendars.CONTENT_URI
    # Prefer visible and syncable calendars; prefer those with account_name (primary)
    projection = ['_id', 'calendar_displayName', 'visible', 'sync_events', 'account_name', 'ownerAccount']
    Cursor = resolver.query(uri, projection, None, None, None)
    if Cursor is None:
      return None
    best_id = None
    best_score = -1
    if Cursor.moveToFirst():
      while True:
        try:
          _id = Cursor.getLong(Cursor.getColumnIndex('_id'))
        except Exception:
          _id = Cursor.getLong(0)
        def col_int(name, default=0):
          try:
            idx = Cursor.getColumnIndex(name)
            return Cursor.getInt(idx)
          except Exception:
            return default
        def col_str(name, default=None):
          try:
            idx = Cursor.getColumnIndex(name)
            return Cursor.getString(idx)
          except Exception:
            return default

        visible = col_int('visible', 0)
        sync = col_int('sync_events', 0)
        account = col_str('account_name') or col_str('ownerAccount')
        score = (2 if account else 0) + (1 if visible else 0) + (1 if sync else 0)
        # bonus if account looks like an email (likely primary Google account)
        if account and '@' in account:
          score += 2
        # bonus if ownerAccount equals account
        owner = col_str('ownerAccount')
        if owner and account and owner == account:
          score += 1
        # deprioritize local/phone-only calendars (account may be like 'Local' or None)
        if account and account.lower() in ('local', 'phone', 'null'):
          score -= 1
        if score > best_score:
          best_score = score
          best_id = _id
        if not Cursor.moveToNext():
          break
    Cursor.close()
    if best_id is None:
      return None
    return int(best_id)
  except Exception:
    return None


class PermissionAwaiter:
  """Helper to wait for permission callback from Java Activity.

  Usage: Java-side Activity's onRequestPermissionsResult should call into Python:
    org.example.alarma.Controlador.calendar_adapters.android_adapter.permission_callback(requestCode, permissions, grantResults)

  The awaiter stores the last result and unblocks waiting code.
  """
  _instance = None

  def __init__(self):
    import threading
    self._event = threading.Event()
    self._granted = None

  @classmethod
  def get_instance(cls):
    if cls._instance is None:
      cls._instance = PermissionAwaiter()
    return cls._instance

  def clear(self):
    self._granted = None
    self._event.clear()

  def set_result(self, granted: bool):
    self._granted = granted
    self._event.set()

  def wait(self, timeout: int = 15):
    waited = self._event.wait(timeout)
    if not waited:
      return None
    return self._granted


def permission_callback(requestCode, permissions, grantResults):
  """This function should be called from the Android Activity's
  `onRequestPermissionsResult` to notify Python about the user's choice.

  Parameters mirror Android's signature.
  """
  try:
    # grantResults is an int[]; consider granted if all entries == 0 (PackageManager.PERMISSION_GRANTED)
    from jnius import autoclass
    PackageManager = autoclass('android.content.pm.PackageManager')
  except Exception:
    PackageManager = None

  granted = True
  try:
    # iterate grantResults
    for i in range(len(grantResults)):
      if grantResults[i] != 0:
        granted = False
        break
  except Exception:
    granted = False

  awaiter = PermissionAwaiter.get_instance()
  awaiter.set_result(granted)
