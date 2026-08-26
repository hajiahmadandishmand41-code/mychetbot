package com.mychatbot.bridge

import android.accessibilityservice.AccessibilityService
import android.view.accessibility.AccessibilityEvent

/**
 * User-enabled accessibility capability hook.
 *
 * The service intentionally performs no automated UI actions by itself;
 * supported actions must be explicitly initiated by the user through the app.
 */
class MyChatBotAccessibilityService : AccessibilityService() {
    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        // Capability detection only; no implicit UI automation is performed.
    }

    override fun onInterrupt() = Unit
}
