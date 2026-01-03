package org.example.alarma;

/**
 * Simple static bridge to expose the last onRequestPermissionsResult grantResults
 * to Python via pyjnius. Place this file in your Android app Java package
 * (e.g. app/src/main/java/org/example/alarma/PermissionBridge.java).
 */
public class PermissionBridge {
    private static int[] lastGrantResults = null;

    public static void setLastGrantResults(int[] results) {
        lastGrantResults = results;
    }

    public static int[] getLastGrantResults() {
        return lastGrantResults;
    }
}
