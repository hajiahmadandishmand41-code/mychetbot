package com.mychatbot.bridge

import android.content.Context
import android.net.ConnectivityManager
import android.net.Network
import android.net.NetworkCapabilities
import android.net.NetworkRequest
import android.net.wifi.WifiNetworkSpecifier
import android.os.Build

/**
 * Device-local Wi-Fi connector. Android owns the actual credential prompt and
 * network permission flow; credentials are never persisted by this class.
 */
class WifiConnector(private val context: Context) {
    data class Request(
        val ssid: String,
        val passphrase: String,
    )

    fun connect(request: Request): Result<String> {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.Q) {
            return Result.failure(
                UnsupportedOperationException("Wi-Fi connection helper requires Android 10+")
            )
        }
        if (request.ssid.isBlank()) {
            return Result.failure(IllegalArgumentException("SSID must not be blank"))
        }
        if (request.passphrase.isBlank()) {
            return Result.failure(IllegalArgumentException("Wi-Fi passphrase must not be blank"))
        }

        val specifier = WifiNetworkSpecifier.Builder()
            .setSsid(request.ssid)
            .setWpa2Passphrase(request.passphrase)
            .build()

        val networkRequest = NetworkRequest.Builder()
            .addTransportType(NetworkCapabilities.TRANSPORT_WIFI)
            .setNetworkSpecifier(specifier)
            .build()

        val connectivity = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        return try {
            connectivity.requestNetwork(
                networkRequest,
                object : ConnectivityManager.NetworkCallback() {
                    override fun onAvailable(network: Network) {
                        connectivity.bindProcessToNetwork(network)
                    }

                    override fun onUnavailable() {
                        connectivity.bindProcessToNetwork(null)
                    }
                },
            )
            Result.success("request_submitted")
        } catch (security: SecurityException) {
            Result.failure(IllegalStateException("Android Wi-Fi permission is not available", security))
        }
    }
}
