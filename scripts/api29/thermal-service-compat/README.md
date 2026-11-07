# API29 host thermal status compatibility

This overlay registers the real `thermalservice` name and preserves the accepted
identifier service registration and receiver launch JNI method. Compile only the
explicit overlay classes over an exact, hash-verified predecessor class tree.
The canonical working tree is not a substitute for the accepted source snapshot.

`HostApi.thermalState()` queries the fixed, read-only Sailfish DSME system D-Bus
endpoint with a one-second call timeout. Native errors and unknown states fail
explicitly; they are never converted to a fabricated normal status. The backend
does not change thermal policy, cooling, frequency, sensors, or host services.

DSME severity is coarser than Android's severity: `normal` and
`low-temp-warning` map to no heat throttling, `warning` to moderate, `alert` to
severe, and `fatal` to shutdown severity. This is an adapter policy, not an
inference of device temperatures or exact Android throttling thresholds. Status
listeners receive an initial query and changes from two-second polling while
listeners exist. Removing the last listener stops that process's daemon thread.
Sensor/cooling inventory methods remain explicitly unsupported.

Sources:
- [DSME state names](https://github.com/sailfishos/libdsme/blob/master/modules/thermalmanager_dbus_if.c)
- [DSME state manager](https://github.com/sailfishos/dsme/blob/master/modules/thermalmanager.c)
- [Android 10 IThermalService](https://android.googlesource.com/platform/frameworks/base/+/android-10.0.0_r47/core/java/android/os/IThermalService.aidl)

The private, signed test APK uses the unmodified public PowerManager API from
ordinary SDK29 and SDK34 application domains, with hidden API enforcement on.
It checks the actual host state independently, initial callback, duplicate
registration rejection, unregister, and subsequent query. It creates no desktop
entry and is removed after the bounded test. Its pass does not establish support
for sensor inventory, host state changes, all Android thermal APIs, or any app's
complete startup.
