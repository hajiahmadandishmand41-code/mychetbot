package com.mychatbot.bridge

import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context
import androidx.core.app.NotificationCompat

object Notifier {
    private const val CHANNEL_ID = "mychatbot"

    fun ensureChannel(context: Context) {
        val mgr = context.getSystemService(NotificationManager::class.java)
        mgr.createNotificationChannel(
            NotificationChannel(CHANNEL_ID, "MyChatBot", NotificationManager.IMPORTANCE_DEFAULT)
        )
    }

    fun notify(context: Context, id: Int, title: String, body: String) {
        val n = NotificationCompat.Builder(context, CHANNEL_ID)
            .setContentTitle(title)
            .setContentText(body)
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .build()
        NotificationManager::class.java
        context.getSystemService(NotificationManager::class.java).notify(id, n)
    }
}
