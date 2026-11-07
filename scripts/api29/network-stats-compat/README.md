# Read-only host interface statistics

Registers the API29 `netstats` service used by public `TrafficStats` calls.
Interface byte/packet counters come from `/proc/net/dev` as 64-bit values;
loopback is excluded from total counts. Unknown interfaces and unsupported
counter types return `TrafficStats.UNSUPPORTED` (-1). Per-Android-application
UID accounting is unavailable because applications share the host user's UID;
these queries return -1 rather than claiming another application's traffic.

The mobile backend recognizes existing logical RMNET/WWAN data interfaces
with kernel RAWIP type 519 or Qualcomm's older type 530. It includes down links
so their counters since boot are retained. It excludes aggregate `rmnet_ipa`
and reverse offload links to avoid double counting. This is the current
Qualcomm/Linux backend boundary, not universal modem discovery. Removed kernel
interfaces and historical network-usage sessions are not reconstructed.
Unsupported usage sessions, callbacks, and mutation operations fail explicitly.

Sources:
- [API29 network statistics contract](https://raw.githubusercontent.com/aosp-mirror/platform_frameworks_base/android-10.0.0_r47/core/java/android/net/INetworkStatsService.aidl)
- [Public TrafficStats aggregation](https://raw.githubusercontent.com/aosp-mirror/platform_frameworks_base/android-10.0.0_r47/core/java/android/net/TrafficStats.java)
- [AOSP RAWIP kernel compatibility test](https://android.googlesource.com/platform/system/netd/+/003524e75b847376b361f310443405bdb6d37c6d/server/OffloadUtilsTest.cpp)

SDK29 and SDK34 signed ordinary-app fixtures call public mobile/total byte and
packet APIs. The device harness independently reads kernel counters before and
after, requires every result to fall within those bounds, and checks that UID
statistics are explicitly unsupported. No launcher entry is installed.
