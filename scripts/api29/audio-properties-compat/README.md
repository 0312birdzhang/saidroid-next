# Read-only primary audio output properties

This is the opt-in r293 source variant over the tested r292 startup overlay in
`scripts/api29/app-startup-compat`. It retains `SdAudio.java`, `host-audio.cpp`,
their patches and signed-app fixture sources without editing the frozen shared
baseline.

`AudioSystem.getPrimaryOutputSamplingRate()` delegates to the existing cached
PulseAudio snapshot and returns the real default sink rate. The native query
rejects a missing or nonpositive rate. `getPrimaryOutputFrameCount()` returns 0,
which Android's public `AudioManager.getProperty` converts to `null`: the backend
does not have an Android primary HAL frame count. This does not provide audio
playback, negotiate a stream buffer or change the host volume.

The target SDK 29/34 fixtures use only public Android audio queries. Both read
48000 Hz on the test phone, agree with the host audio device ports and an
independent ordinary-user `pactl` query, and receive `null` for frames per buffer.
The r292 negative control reproduces the original missing JNI method. Tests
create no launcher entry and run with the OLED off.

`snapshot.json` hashes the retained source inputs and links the package boundary
and phone fixture proofs. Builder snapshots retain the pinned VM evidence paths
for reproduction in a fresh run directory, not for overwriting completed runs.
The required gates reproduce accepted raw class/native bytes before applying the
variant, retain existing hidden-API flags, mark new implementation members
private, and verify all core/framework/ART/boot bytes unchanged. Stage a new
isolated release and run its contracts before changing the daily entry.

A successful property fixture is not a QQ stability, audio playback or full CTS
claim. The separate unchanged-APK QQ observation has its own result and cleanup
evidence.
