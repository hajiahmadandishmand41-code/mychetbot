package com.mychatbot.bridge

import android.content.Context
import android.content.Intent
import android.net.Uri

/** اجرای اسکریپت‌های MyChatBot داخل Termux از طریق RUN_COMMAND. */
class TermuxBridge(private val context: Context) {

    companion object {
        const val TERMUX_SERVICE = "com.termux/com.termux.app.RunCommandService"
        const val ACTION_RUN = "com.termux.RUN_COMMAND"
        const val HOME = "/data/data/com.termux/files/home"
    }

    fun run(path: String, args: Array<String> = arrayOf(), background: Boolean = true) {
        val intent = Intent(ACTION_RUN).apply {
            setClassName("com.termux", "com.termux.app.RunCommandService")
            putExtra("com.termux.RUN_COMMAND_PATH", path)
            putExtra("com.termux.RUN_COMMAND_ARGUMENTS", args)
            putExtra("com.termux.RUN_COMMAND_WORKDIR", "$HOME/mychetbot")
            putExtra("com.termux.RUN_COMMAND_BACKGROUND", background)
        }
        context.startService(intent)
    }

    fun startBackend() = run(
        "/data/data/com.termux/files/usr/bin/bash",
        arrayOf("termux/start_api.sh")
    )

    fun openTermux() {
        context.startActivity(
            Intent(Intent.ACTION_VIEW, Uri.parse("termux://"))
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        )
    }
}
