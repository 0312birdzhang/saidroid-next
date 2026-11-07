# Read-only Android audio connection queries

Registers API29 `AudioSystem.getDeviceConnectionState(int,String)` through the
existing audio JNI installation. It queries current PulseAudio card and
sink/source ports, excludes monitor/null/parking endpoints, and never selects a
route or changes volume. This removes an unresolved native method reached by
ordinary `AudioManager.isWiredHeadsetOn()` callers.

Standard PulseAudio ports use availability; an unknown port needs an actually
selected route. Sailfish's droid HAL advertises a catalogue of external routes
as available even without attached accessories, so its external ports require
selection by an actual sink/source. Built-in speaker/earpiece/microphone ports
can be present without being selected. This backend cannot report an external
droid accessory that is connected but absent from all selected host routes.
Bluetooth/USB endpoints use published device/profile properties. Nonempty
addresses must match host addresses; unrecognized/unavailable devices return
the Android disconnected state. Server failures are logged as unavailable.

The port fixture covers wired/SCO/A2DP classification, unknown/disconnected
availability, and address matching. The private SDK29/34 activity fixture is
for the independently observed speaker/no-wired-accessory phone state; it
requires a connected speaker plus absent wired, foreign-address and invalid
devices through the real registered JNI method. Neither fixture is a phone
launcher entry.

`baseline/host-audio.cpp` reproduces the accepted r320 host audio binary input.
The rebuild keeps thermal, camera, and network objects unchanged and verifies
the complete baseline library byte for byte before building the candidate.
