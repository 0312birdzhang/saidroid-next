# Window session haptic feedback

API29 `IWindowSession.performHapticFeedback(int effectId, boolean always)` has
no window parameter. Looking up `args[0]` as `IWindow` crashes the main thread
when `TextView.performLongClick()` requests haptic feedback. The source overlay
reads the real argument types and returns false because the host currently has
no vibrator backend. It preserves the absence of vibration support and lets
normal long-click handling continue.

The baseline is the accepted window/IME source, including IME resize and gesture
exclusion support. Compile it against the current classfiles first and require
byte-for-byte equality, then replace only the changed class and encode canonical
hidden-API flags. Keep the unrelated GPU/display recovery separate from this
reproducible Java exception.
