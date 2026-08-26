package com.mychatbot.bridge

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {
    private lateinit var termux: TermuxBridge
    private lateinit var wifi: WifiScanner

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        termux = TermuxBridge(this)
        wifi = WifiScanner(this)
        Notifier.ensureChannel(this)
        termux.startBackend()
    }
}
