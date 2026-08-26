package com.mychatbot.bridge

import android.Manifest
import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {
    private lateinit var termux: TermuxBridge
    private lateinit var wifi: WifiScanner
    private lateinit var wifiConnector: WifiConnector
    private lateinit var capabilities: CapabilityDetector

    private val permissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) {
        reportCapabilities()
        showMissingCapabilityHelp()
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        termux = TermuxBridge(this)
        wifi = WifiScanner(this)
        wifiConnector = WifiConnector(this)
        capabilities = CapabilityDetector(this)
        Notifier.ensureChannel(this)

        requestRuntimeCapabilities()
        reportCapabilities()
        showMissingCapabilityHelp()

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
        if (::capabilities.isInitialized) {
            reportCapabilities()
            showMissingCapabilityHelp()
        }
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

    private fun showMissingCapabilityHelp() {
        val status = capabilities.detect()
        val missing = buildList {
            if (!status.wifiEnabled) add("Wi-Fi")
            if (!status.wifiScanPermission) add("مجوز اسکن Wi-Fi")
            if (!status.locationServicesEnabled) add("Location Services")
            if (!status.termuxInstalled) add("Termux")
            else if (!status.termuxRunCommandPermission) add("مجوز اجرای Termux")
            if (!status.accessibilityEnabled) add("Accessibility")
        }
        if (missing.isEmpty()) return

        val message = "برای فعال شدن قابلیت‌های دستگاه، موارد زیر نیاز به اقدام کاربر دارند:\n\n" +
            missing.joinToString("\n") { "• $it" } +
            "\n\nAndroid برای برخی مجوزهای ویژه اجازه اعطای خودکار نمی‌دهد."

        AlertDialog.Builder(this)
            .setTitle("راه‌اندازی MyChatBot")
            .setMessage(message)
            .setPositiveButton("تنظیم Accessibility") { _, _ ->
                capabilities.openAccessibilitySettings()
            }
            .setNeutralButton("تنظیمات Wi-Fi") { _, _ ->
                startActivity(Intent(Settings.ACTION_WIFI_SETTINGS))
            }
            .setNegativeButton("بعداً") { dialog, _ -> dialog.dismiss() }
            .show()
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
