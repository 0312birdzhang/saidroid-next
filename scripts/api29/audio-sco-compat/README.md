# Read-only Bluetooth SCO query candidate

This opt-in r294 variant implements `IAudioService.isBluetoothScoOn()` for the
current default PulseAudio output. It reads `device.api`, `bluetooth.protocol`
and `api.bluez5.profile`; explicit HSP/HFP/SCO profiles on a BlueZ output are
treated as SCO. It does not change routes, connect a headset, transmit audio or
claim full Android audio policy support. A missing default output is an error.

The signed SDK 29/34 fixtures call the public `AudioManager.isBluetoothScoOn()`
33 times from a real HandlerThread. Both passed on the test phone, with false
matching the independent `pactl` default `droid-hal` output. The old r293 fixture
reproduced the unsupported-method exception. Bluetooth-connected hardware has
not been exercised.

Existing Java classfiles and native API bytes reproduced exactly before the
change. Existing exports remain unchanged; the native library adds the real
PulseAudio `pa_proplist_gets@PULSE_0` import. Existing hidden-API flags remain,
and new implementation methods are private. Core/framework/ART/boot bytes stay
unchanged. `snapshot.json` retains exact source/patch/fixture hashes and pinned
VM recipe snapshots; use a fresh run directory for future builds.

**r294 is not promoted.** A real touch into an existing QQ conversation exercised
the new SCO query successfully, then the conversation's dynamic avatar crashed
on missing `SurfaceTexture.nativeInit`, Bugly record 51. The main process exited
115.8 seconds after launch. This candidate fixes the isolated query but does
not pass conversation stability. Existing r293 remains the daily version.

Evidence is under `build/evidence/qq-audio-sco294-20261102-v1` and
`build/evidence/qq-r294-conversation-20261102-v1`. The user's original r293
conversation failure is preserved under
`build/evidence/qq-r293-conversation-crash-20261102-v1`.
