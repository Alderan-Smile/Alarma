package org.example.alarma;

public class PermissionBridge {
    private static int[] lastGrantResults = null;

    public static void setLastGrantResults(int[] results) {
        lastGrantResults = results;
    }

    public static int[] getLastGrantResults() {
        return lastGrantResults;
    }
}
