package com.mychatbot.bridge

import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri

/** اجرای فقط launcherهای شناخته‌شده MyChatBot داخل Termux. */
class TermuxBridge(private val context: Context) {
    companion object {
        private const val TERMUX_PACKAGE = "com.termux"
        private const val ACTION_RUN = "com.termux.RUN_COMMAND"
        private const val SERVICE = "com.termux.app.RunCommandService"
        private const val HOME = "/data/data/com.termux/files/home"
        private const val BASH = "/data/data/com.termux/files/usr/bin/bash"
        private val ALLOWED = setOf("cli", "api")
    }

    fun isInstalled(): Boolean = try {
        context.packageManager.getPackageInfo(TERMUX_PACKAGE, 0)
        true
    } catch (_: PackageManager.NameNotFoundException) {
        false
    }

    fun run(mode: String): Result<Unit> {
        if (mode !in ALLOWED) return Result.failure(IllegalArgumentException("unsupported bridge mode"))
        if (!isInstalled()) return Result.failure(IllegalStateException("Termux نصب نیست"))
        return try {
            val intent = Intent(ACTION_RUN).apply {
                setClassName(TERMUX_PACKAGE, SERVICE)
                putExtra("com.termux.RUN_COMMAND_PATH", BASH)
                putExtra("com.termux.RUN_COMMAND_ARGUMENTS", arrayOf("termux/run_bridge.sh", mode))
                putExtra("com.termux.RUN_COMMAND_WORKDIR", "$HOME/mychetbot")
                putExtra("com.termux.RUN_COMMAND_BACKGROUND", true)
            }
            context.startService(intent)
            Result.success(Unit)
        } catch (security: SecurityException) {
            Result.failure(IllegalStateException("مجوز RUN_COMMAND برای Termux در دسترس نیست", security))
        } catch (error: Exception) {
            Result.failure(error)
        }
    }

    fun startBackend(): Result<Unit> = run("api")

    fun openTermux() {
        context.startActivity(
            Intent(Intent.ACTION_VIEW, Uri.parse("termux://"))
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        )
    }
}
