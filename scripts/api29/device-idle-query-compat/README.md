# Runtime power exemption queries

The standalone runtime has no provisioned per-package Android power exemption
configuration. It now registers `deviceidle` and answers
`isPowerSaveWhitelistApp` / `isPowerSaveWhitelistExceptIdleApp` against that
empty exemption inventory. It does not mark arbitrary applications exempt,
change Sailfish MCE policy, claim an Android Doze implementation, or accept
whitelist mutation calls. Other controller operations remain explicitly
unsupported. Host power-save state remains the separate `SdPower` backend.

This makes the public `PowerManager.isIgnoringBatteryOptimizations()` query
available without a null Binder failure. It means “no runtime exemption
configured”; it does not claim that Android Doze scheduling is active.

[API29 controller contract](https://raw.githubusercontent.com/aosp-mirror/platform_frameworks_base/android-10.0.0_r47/core/java/android/os/IDeviceIdleController.aidl).
