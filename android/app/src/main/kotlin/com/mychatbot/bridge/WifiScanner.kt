package com.mychatbot.bridge

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.net.wifi.ScanResult
import android.net.wifi.WifiManager
import androidx.core.content.ContextCompat

data class WifiNetwork(val ssid: String, val bssid: String, val rssi: Int, val frequency: Int)

class WifiScanner(context: Context) {
    private val appContext = context.applicationContext
    private val wifiManager = appContext.getSystemService(Context.WIFI_SERVICE) as WifiManager

    fun isEnabled(): Boolean = wifiManager.isWifiEnabled

    fun hasLocationPermission(): Boolean =
        ContextCompat.checkSelfPermission(appContext, Manifest.permission.ACCESS_FINE_LOCATION) ==
            PackageManager.PERMISSION_GRANTED

    @Suppress("DEPRECATION")
    fun scan(): Result<List<WifiNetwork>> {
        if (!isEnabled()) return Result.failure(IllegalStateException("Wi-Fi خاموش است"))
        if (!hasLocationPermission()) {
            return Result.failure(IllegalStateException("مجوز موقعیت مکانی برای اسکن Wi-Fi لازم است"))
        }
        return try {
            wifiManager.startScan()
            val results = wifiManager.scanResults.map { r: ScanResult ->
                WifiNetwork(r.SSID ?: "", maskBssid(r.BSSID ?: ""), r.level, r.frequency)
            }.sortedByDescending { it.rssi }
            Result.success(results)
        } catch (security: SecurityException) {
            Result.failure(IllegalStateException("دسترسی اسکن Wi-Fi موجود نیست", security))
        }
    }

    @Suppress("DEPRECATION")
    fun currentSsid(): String = wifiManager.connectionInfo.ssid ?: "unknown"

    private fun maskBssid(bssid: String): String {
        val parts = bssid.split(":")
        return if (parts.size == 6) parts.take(3).joinToString(":") + ":xx:xx:xx" else bssid
    }
}
