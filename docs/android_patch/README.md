Android patch for PermissionBridge and Activity changes

Purpose
- Provide small Java/Kotlin helpers to forward permission results from the Android Activity to the Python runtime via `PermissionBridge`.

Files included
- `PermissionBridge.java` - static holder for last grantResults (placed into app Java package).
- `Activity_onRequestPermissionsResult.java` - snippet to paste into your Activity (Java).
- `Activity_onRequestPermissionsResult.kt` - Kotlin equivalent snippet.

Where to place files
- For a Briefcase-generated Android app, put `PermissionBridge.java` in:
  `<briefcase-project>/app/src/main/java/org/example/alarma/PermissionBridge.java`
- Edit your Activity (likely under the same package) and add the `onRequestPermissionsResult` snippet.

AndroidManifest
- Ensure `AndroidManifest.xml` includes these uses-permission entries:

```xml
<uses-permission android:name="android.permission.READ_CALENDAR" />
<uses-permission android:name="android.permission.WRITE_CALENDAR" />
```

How it works
- When the Activity receives the runtime permission result, it stores `grantResults` in `PermissionBridge`.
- Python code (via PyJNIus) can poll `PermissionBridge.getLastGrantResults()`; `Controlador/calendar_adapters/android_adapter.py` already does this.

Rebuild & test
1. Add files to the Android project.
2. Rebuild with Briefcase: `briefcase build android` then `briefcase run android`.
3. On device, when app requests calendar permissions, grant them and the bridge will expose results to Python.

Notes & alternatives
- This is a low-effort bridge. For production, prefer a direct callback mechanism from Java to Python, or use an event bus integrated with the Python runtime.
- If you want, puedo generar un parche git/diff listo para aplicar a un proyecto Briefcase si me proporcionas la estructura del proyecto Android.
