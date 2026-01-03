// Kotlin snippet for Activity
override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<String>, grantResults: IntArray) {
    super.onRequestPermissionsResult(requestCode, permissions, grantResults)
    org.example.alarma.PermissionBridge.setLastGrantResults(grantResults)
}
