package com.mychatbot.bridge

import android.content.Context
import android.net.wifi.ScanResult
import android.net.wifi.WifiManager

data class WifiNetwork(val ssid: String, val bssid: String, val rssi: Int, val frequency: Int)

class WifiScanner(context: Context) {
    private val wifiManager =
        context.applicationContext.getSystemService(Context.WIFI_SERVICE) as WifiManager

    fun isEnabled(): Boolean = wifiManager.isWifiEnabled

    @Suppress("DEPRECATION")
    fun scan(): List<WifiNetwork> {
        wifiManager.startScan()
        return wifiManager.scanResults.map { r: ScanResult ->
            WifiNetwork(r.SSID ?: "", r.BSSID ?: "", r.level, r.frequency)
        }.sortedByDescending { it.rssi }
    }

    @Suppress("DEPRECATION")
    fun currentSsid(): String = wifiManager.connectionInfo.ssid ?: "unknown"
}
