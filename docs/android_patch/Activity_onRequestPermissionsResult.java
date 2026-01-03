// Add this snippet inside your Activity class (Java)
@Override
public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
    super.onRequestPermissionsResult(requestCode, permissions, grantResults);
    // notify bridge for Python side
    org.example.alarma.PermissionBridge.setLastGrantResults(grantResults);
}
