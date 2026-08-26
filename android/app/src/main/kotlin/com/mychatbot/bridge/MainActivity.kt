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
    private lateinit var capabilities: CapabilityDetector

    private val permissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { /* CapabilityDetector re-checks the effective state. */
        reportCapabilities()
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        termux = TermuxBridge(this)
        wifi = WifiScanner(this)
        capabilities = CapabilityDetector(this)
        Notifier.ensureChannel(this)

        requestRuntimeCapabilities()
        reportCapabilities()

        val status = capabilities.detect()
        if (status.termuxInstalled && status.termuxRunCommandPermission) {
            val result = termux.startBackend()
            result.onFailure { error ->
                Toast.makeText(
                    this,
                    error.message ?: "خطا در اتصال به Termux",
                    Toast.LENGTH_LONG
                ).show()
            }
        }
    }

    override fun onResume() {
        super.onResume()
        if (::capabilities.isInitialized) reportCapabilities()
    }

    private fun requestRuntimeCapabilities() {
        val permissions = buildList {
            add(Manifest.permission.ACCESS_FINE_LOCATION)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                add(Manifest.permission.NEARBY_WIFI_DEVICES)
                add(Manifest.permission.POST_NOTIFICATIONS)
            }
        }
        permissionLauncher.launch(permissions.toTypedArray())
    }

    private fun reportCapabilities() {
        val status = capabilities.detect()
        val missing = buildList {
            if (!status.wifiEnabled) add("Wi-Fi روشن نیست")
            if (!status.wifiScanPermission) add("مجوزهای اسکن Wi-Fi کامل نیست")
            if (!status.locationServicesEnabled) add("Location خاموش است")
            if (!status.termuxInstalled) add("Termux نصب نیست")
            else if (!status.termuxRunCommandPermission) add("اجازه RUN_COMMAND برای Termux موجود نیست")
            if (!status.accessibilityEnabled) add("Accessibility توسط کاربر فعال نشده است")
        }

        if (missing.isNotEmpty()) {
            Toast.makeText(
                this,
                "قابلیت‌های محدودشده: ${missing.joinToString("، ")}",
                Toast.LENGTH_LONG
            ).show()
        }
    }
}
