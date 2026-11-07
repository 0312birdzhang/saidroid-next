# Startup proxy permission correction (r321o)

Android ActivityThread queries process proxy configuration while binding every application.
This query is allowed without ACCESS_NETWORK_STATE in Android 10.
SdConnectivity now handles getGlobalProxy/getProxyForNetwork before the passive
network observation permission gate. The runtime currently configures no proxy.
Real network observations and subscriptions keep their existing permission checks.

These sources replace the compiled r321n connectivity family. The older
scripts/device/SdConnectivity.java belongs to the base development source, not
the final assembled release. ProxyPermissionProbe is a platform-only ART fixture,
never an installed phone application. It reproduces the old startup denial and
requires all eight denied network operations to remain denied after the fix.

The build reproduces the predecessor runtime byte for byte before changing only
SdConnectivity.class. Hidden API flags and all fourteen framework boot jars stay
identical. All 45 matching boot image/OAT/VDEX files are regenerated.

Reference: https://android.googlesource.com/platform/frameworks/base/+/refs/heads/android10-release/services/core/java/com/android/server/ConnectivityService.java
