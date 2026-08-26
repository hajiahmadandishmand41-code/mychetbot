package com.mychetbot

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {
    companion object { private const val CHANNEL = "com.mychetbot/android" }

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, CHANNEL).setMethodCallHandler { call, result ->
            when (call.method) {
                "clipboardWrite" -> {
                    val text = call.argument<String>("text") ?: ""
                    val manager = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
                    manager.setPrimaryClip(ClipData.newPlainText("MyChatBot", text))
                    result.success(true)
                }
                "clipboardRead" -> {
                    val manager = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
                    result.success(manager.primaryClip?.getItemAt(0)?.coerceToText(this)?.toString() ?: "")
                }
                "runTermux" -> {
                    val commandPath = call.argument<String>("path") ?: ""
                    val args = (call.argument<List<String>>("args") ?: emptyList()).toTypedArray()
                    if (commandPath.isBlank() || commandPath.contains("..")) {
                        result.error("INVALID_COMMAND", "Invalid Termux command path", null)
                        return@setMethodCallHandler
                    }
                    val intent = Intent().apply {
                        setClassName("com.termux", "com.termux.app.RunCommandService")
                        action = "com.termux.RUN_COMMAND"
                        putExtra("com.termux.RUN_COMMAND_PATH", commandPath)
                        putExtra("com.termux.RUN_COMMAND_ARGUMENTS", args)
                        putExtra("com.termux.RUN_COMMAND_WORKDIR", call.argument<String>("workdir") ?: "/data/data/com.termux/files/home")
                        putExtra("com.termux.RUN_COMMAND_BACKGROUND", true)
                    }
                    try {
                        startService(intent)
                        result.success(true)
                    } catch (e: Exception) {
                        result.error("TERMUX_UNAVAILABLE", e.message, null)
                    }
                }
                else -> result.notImplemented()
            }
        }
    }
}
