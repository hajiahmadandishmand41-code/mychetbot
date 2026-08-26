package com.mychatbot.bridge

import android.Manifest
import android.os.Build
import android.os.Bundle
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {
    private lateinit var termux: TermuxBridge
    private lateinit var wifi: WifiScanner

    private val permissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { /* Permission state is checked again by WifiScanner when used. */ }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        termux = TermuxBridge(this)
        wifi = WifiScanner(this)
        Notifier.ensureChannel(this)

        val permissions = buildList {
            add(Manifest.permission.ACCESS_FINE_LOCATION)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                add(Manifest.permission.NEARBY_WIFI_DEVICES)
            }
        }
        permissionLauncher.launch(permissions.toTypedArray())

        val result = termux.startBackend()
        result.onFailure { error ->
            Toast.makeText(this, error.message ?: "خطا در اتصال به Termux", Toast.LENGTH_LONG).show()
        }
    }
}
