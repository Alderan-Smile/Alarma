README: How to apply Activity patch for PermissionBridge

1) Place PermissionBridge.java (added by this patch) under:
   app/src/main/java/org/example/alarma/PermissionBridge.java

2) Edit your Android Activity (the one Briefcase generates) and add the
   following method (Java) inside the Activity class. This method forwards
   the runtime permission results into the bridge so Python can poll them.

   Java snippet to add inside your Activity class:

   @Override
   public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
       super.onRequestPermissionsResult(requestCode, permissions, grantResults);
       // notify bridge for Python side
       org.example.alarma.PermissionBridge.setLastGrantResults(grantResults);
   }

   Kotlin snippet if your Activity is Kotlin:

   override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<String>, grantResults: IntArray) {
       super.onRequestPermissionsResult(requestCode, permissions, grantResults)
       org.example.alarma.PermissionBridge.setLastGrantResults(grantResults)
   }

3) Ensure `AndroidManifest.xml` contains calendar permissions:

   <uses-permission android:name="android.permission.READ_CALENDAR" />
   <uses-permission android:name="android.permission.WRITE_CALENDAR" />

Note for Briefcase/BeeWare users
- Briefcase generates the Android app package name automatically from your project metadata. The Python adapter now detects the app package at runtime and will look for `PermissionBridge` in that package.
- Place `PermissionBridge.java` under `app/src/main/java/<your_app_package_path>/PermissionBridge.java` (for example, if package is `com.example.myapp`, place it in `app/src/main/java/com/example/myapp/PermissionBridge.java`).
- If you prefer, you can keep the example path `org.example.alarma.PermissionBridge` but placing it in the actual app package is recommended for BeeWare projects.

4) Rebuild and run the app:

   briefcase build android
   briefcase run android

5) How Python reads results (already implemented in project):
   - `Controlador/calendar_adapters/android_adapter.py` polls
     `org.example.alarma.PermissionBridge.getLastGrantResults()` for up to 15s
     after requesting permissions. If present, the results will be used.

6) Applying this patch if you use git:
   - From the Briefcase project root (where `app/` lives):

     git add app/src/main/java/org/example/alarma/PermissionBridge.java
     git add app/src/main/java/org/example/alarma/README_APPLY_ACTIVITY_PATCH.txt
     git commit -m "Add PermissionBridge for runtime permission results bridge"

7) Notes and production considerations:
   - This bridge is a small integration suitable for demos and quick testing.
   - For production prefer a direct Java->Python callback mechanism.
   - Adjust the package path (`org.example.alarma`) to match your app package if needed.

End of README_APPLY_ACTIVITY_PATCH.txt
