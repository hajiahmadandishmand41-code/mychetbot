package com.mychatbot.bridge

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.location.LocationManager
import android.net.wifi.ScanResult
import android.net.wifi.WifiManager
import android.os.Build
import androidx.core.content.ContextCompat

data class WifiNetwork(
    val ssid: String,
    val bssid: String,
    val rssi: Int,
    val frequency: Int,
    val channel: Int,
    val capabilities: String,
    val security: String,
    val wpsStatus: String,
    val wifiStandard: String,
)

data class WifiCapabilities(
    val wifiEnabled: Boolean,
    val locationPermission: Boolean,
    val nearbyWifiPermission: Boolean,
    val locationServicesEnabled: Boolean,
    val scanAvailable: Boolean,
    val rootRequired: Boolean = false,
    val unsupportedOperations: List<String> = listOf(
        "password guessing/cracking",
        "handshake/PMKID capture",
        "WPS PIN attacks",
        "deauthentication",
        "packet injection",
        "permission/root bypass",
        "authentication/CAPTCHA bypass",
    ),
)

class WifiScanner(context: Context) {
    private val appContext = context.applicationContext
    private val wifiManager = appContext.getSystemService(Context.WIFI_SERVICE) as WifiManager
    private val locationManager = appContext.getSystemService(Context.LOCATION_SERVICE) as LocationManager

    fun isEnabled(): Boolean = wifiManager.isWifiEnabled

    fun hasLocationPermission(): Boolean =
        ContextCompat.checkSelfPermission(appContext, Manifest.permission.ACCESS_FINE_LOCATION) ==
            PackageManager.PERMISSION_GRANTED

    fun hasNearbyWifiPermission(): Boolean =
        Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU ||
            ContextCompat.checkSelfPermission(appContext, Manifest.permission.NEARBY_WIFI_DEVICES) ==
            PackageManager.PERMISSION_GRANTED

    fun isLocationServicesEnabled(): Boolean =
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
            locationManager.isLocationEnabled
        } else {
            @Suppress("DEPRECATION")
            locationManager.isProviderEnabled(LocationManager.GPS_PROVIDER) ||
                locationManager.isProviderEnabled(LocationManager.NETWORK_PROVIDER)
        }

    fun capabilities(): WifiCapabilities = WifiCapabilities(
        wifiEnabled = isEnabled(),
        locationPermission = hasLocationPermission(),
        nearbyWifiPermission = hasNearbyWifiPermission(),
        locationServicesEnabled = isLocationServicesEnabled(),
        scanAvailable = isEnabled() && hasLocationPermission() && hasNearbyWifiPermission(),
    )

    @Suppress("DEPRECATION")
    fun scan(): Result<List<WifiNetwork>> {
        if (!isEnabled()) return Result.failure(IllegalStateException("Wi-Fi خاموش است"))
        if (!hasLocationPermission()) {
            return Result.failure(IllegalStateException("مجوز ACCESS_FINE_LOCATION برای اسکن Wi-Fi لازم است"))
        }
        if (!hasNearbyWifiPermission()) {
            return Result.failure(IllegalStateException("در Android 13+ مجوز NEARBY_WIFI_DEVICES لازم است"))
        }

        return try {
            // startScan() is deprecated on modern Android and can be throttled.
            // We still use the official API when available, then safely fall back
            // to getScanResults() (which may contain cached results).
            wifiManager.startScan()
            val results = wifiManager.scanResults
                .map { it.toWifiNetwork() }
                .sortedByDescending { it.rssi }
            Result.success(results)
        } catch (security: SecurityException) {
            Result.failure(IllegalStateException("دسترسی اسکن Wi-Fi موجود نیست", security))
        }
    }

    @Suppress("DEPRECATION")
    fun currentSsid(): String = wifiManager.connectionInfo.ssid ?: WifiManager.UNKNOWN_SSID

    @Suppress("DEPRECATION")
    fun currentDiagnostics(): Map<String, Any?> {
        val info = wifiManager.connectionInfo
        return mapOf(
            "ssid" to (info.ssid ?: WifiManager.UNKNOWN_SSID),
            "bssid" to maskBssid(info.bssid ?: ""),
            "rssi_dbm" to info.rssi,
            "frequency_mhz" to info.frequency,
            "link_speed_mbps" to info.linkSpeed,
            "network_id" to info.networkId,
            "supplicant_state" to info.supplicantState?.toString(),
            "wifi_standard" to if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) standardName(info.wifiStandard) else "unknown",
        )
    }

    @Suppress("DEPRECATION")
    private fun ScanResult.toWifiNetwork(): WifiNetwork = WifiNetwork(
        ssid = SSID ?: "",
        bssid = maskBssid(BSSID ?: ""),
        rssi = level,
        frequency = frequency,
        channel = frequencyToChannel(frequency),
        capabilities = capabilities ?: "",
        security = securityFromCapabilities(capabilities ?: ""),
        wpsStatus = wpsFromCapabilities(capabilities ?: ""),
        wifiStandard = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) standardName(wifiStandard) else "unknown",
    )

    private fun securityFromCapabilities(raw: String): String {
        val caps = raw.uppercase()
        return when {
            "OWE" in caps -> "OWE"
            "SAE" in caps || "WPA3" in caps -> "WPA3-Personal"
            "EAP" in caps -> "WPA/WPA2-Enterprise"
            "WEP" in caps -> "WEP"
            "WPA2" in caps -> "WPA2"
            "WPA" in caps -> "WPA"
            "[ESS" in caps -> "Open-or-Unknown"
            else -> "Unknown"
        }
    }

    private fun wpsFromCapabilities(raw: String): String =
        when {
            raw.uppercase().contains("WPS") -> "advertised"
            raw.isBlank() -> "unknown"
            else -> "not-advertised"
        }

    private fun standardName(standard: Int): String = when (standard) {
        ScanResult.WIFI_STANDARD_LEGACY -> "802.11a/b/g"
        ScanResult.WIFI_STANDARD_11N -> "802.11n"
        ScanResult.WIFI_STANDARD_11AC -> "802.11ac"
        ScanResult.WIFI_STANDARD_11AX -> "802.11ax"
        ScanResult.WIFI_STANDARD_11AD -> "802.11ad"
        ScanResult.WIFI_STANDARD_11BE -> "802.11be"
        else -> "unknown"
    }

    private fun frequencyToChannel(mhz: Int): Int = when {
        mhz in 2412..2484 -> if (mhz == 2484) 14 else (mhz - 2407) / 5
        mhz in 5000..5895 -> (mhz - 5000) / 5
        mhz in 5955..7115 -> (mhz - 5950) / 5
        else -> -1
    }

    private fun maskBssid(bssid: String): String {
        val parts = bssid.split(":")
        return if (parts.size == 6) parts.take(3).joinToString(":") + ":xx:xx:xx" else bssid
    }
}
