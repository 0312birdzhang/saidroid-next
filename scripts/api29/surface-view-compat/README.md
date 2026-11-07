# Owned SurfaceView / HWUI window compatibility

The existing API29 SurfaceTexture backend remains unchanged. The source EGL
and Wayland files extend the process-owned HWUI queues for SurfaceView frame
barriers and headless-to-Activity display reuse. Baseline files preserve the
accepted input used by the exact compiler comparison.

`source/SdSurfaceStore.java` fixes window removal with retained SurfaceControl
references. A removed layer is hidden immediately; its native Surface remains
owned until outstanding references are released. Previously hardware visibility
was updated only during final collection, allowing removed windows to remain
mapped while those references survived. The matching baseline was compiled and
its class files compared byte-for-byte with the accepted r312i build before
applying this change. This fixes a visibility bug; it does not by itself prove
the cause or resolution of the observed compositor GPU faults.

Current working evidence is under
`build/evidence/qq-picker-camera-settings313-20261103-v1/`. Runtime candidates
remain isolated; the daily r312i release and its AOT cache are unchanged.


Removal also retires the owned Wayland subsurface role on its event thread.
This unmaps the removed control immediately while preserving the wl_surface,
EGL window, and producer references. Retired entries are excluded from role
restacking and cannot be revived by late geometry or producer updates. The
strict combined fixture includes real blank/wake transitions, and rejects new
kernel GPU errors even when its Java checks pass.
