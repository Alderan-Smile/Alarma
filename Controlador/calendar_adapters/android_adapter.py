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
    Context = autoclass('android.content.Context')
    ContentValues = autoclass('android.content.ContentValues')
    Uri = autoclass('android.net.Uri')

    resolver = activity.getContentResolver()
    values = ContentValues()
    values.put('title', title)
    values.put('description', description)
    # times in milliseconds
    startMillis = int(dt.timestamp() * 1000)
    values.put('dtstart', startMillis)
    values.put('dtend', startMillis + 60 * 60 * 1000)  # 1 hour
    values.put('eventTimezone', 'UTC')
    # The calendar_id selection requires querying available calendars; using 1 as common default may fail.
    values.put('calendar_id', 1)

    Events = autoclass('android.provider.CalendarContract$Events')
    uri = resolver.insert(Events.CONTENT_URI, values)
    return uri
  except Exception as e:
    raise NotImplementedError(f'Error al insertar evento en Android: {e}')
