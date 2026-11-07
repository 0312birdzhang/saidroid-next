# Android camera capability boundary

The current Android component has no camera capture backend, and its existing
PackageManager advertises no camera features. android.hardware.Camera's native
enumeration was nevertheless unregistered; a QQ background capability query
recorded an UnsatisfiedLinkError after entering the conversation.

This module registers the legacy Camera enumeration against the component's
empty exposed-camera inventory. It reports zero exposed **Android** cameras,
not a physical-phone camera count. Camera info and explicit camera open fail
with a descriptive RuntimeException. No host camera is queried, opened or
reconfigured. A partially constructed Java Camera has no native context to
release; a nonzero unexpected context is rejected.

The JNI registration is invoked from the existing component bootstrap, as
recorded by the r303 source snapshot under
build/evidence/qq-camera-capability303-20261103-v1/source/bootstrap-host.c.
The byte-identical r300/r302 graphics library is reproduced before adding
this module. The host graphics/allocator implementations are unchanged.

Ordinary signed SDK29/34 fixtures query 33 times from a HandlerThread, check
five absent camera features, reject invalid info/open requests, and verify
Camera.open() returns null when the enumeration is empty. The fixture has no
camera permission and must never access the host cameras. The r302 negative
control reproduces the missing enumeration JNI.

This is capability reporting only. Android photo/video capture remains
unsupported until a real host camera backend is implemented.
