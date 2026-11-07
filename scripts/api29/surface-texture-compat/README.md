# Android 10 SurfaceTexture / TextureView bridge

The r300 source snapshot registers the actual API29 SurfaceTexture,
TextureLayer and TextureView JNI implementations. Android BufferQueue and HWUI
consume real gralloc buffers allocated through the phone's existing libhybris
allocator. The component-private EGL shim forwards producer surfaces to the
same vendor EGL instance and imports only handles owned by this component.
The Android ABI helper converts Surface* to its ANativeWindow base before
querying its owner and releasing it. Host-window and BufferQueue surfaces keep
their original reference owners. YCbCr mapping remains explicitly unsupported.

The signed target SDK29 and SDK34 fixture apps each produced red, green and
blue GPU frames. TextureView.getBitmap() read back the exact corresponding
pixels. Each fixture released both producer and consumer, freed both buffers
with status 0 and final remaining count 0, stayed alive after release, and
left the OLED off with no test app installed. The native renderer is not
replaced with test pixels or a no-op JNI implementation.

Evidence: `build/evidence/qq-surface-texture300-20261102-v1/`.
`texture-fixture-results.json` is the independent graphics gate. Failed
r295-r299 runs remain intact. `snapshot.json` pins these native sources,
Java/EGL/launcher overlays, patches and original VM build recipe snapshots.
The recipes retain original evidence/output paths for audit. Future builds
must use a fresh run directory and fresh VM output paths, verify the pinned
baseline sources, then build-runtime, encode-runtime, build-native,
build-fixtures and package in that order. They depend on the existing API29
runtime, HWUI header tree and private compiler inputs recorded in the recipes.

r300 is not the daily release. Its QQ conversation retest passed real touch
entry and the SCO query, then exited on a new incoming-message notification
failure: unsupported IActivityManager.getIntentSender(). The run did not reach
a QQ texture producer, so the independent fixture is the graphics proof, not
that QQ observation. See `qq-r300-conversation-20261102-v1/conversation-audit.json`.
The next PendingIntent candidate layers on these exact native graphics bytes.
