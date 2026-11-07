# Native Android HWUI / Sailfish Wayland boundary

The application uses Android 10's real `HardwareRenderer`, Skia GLES backend,
RenderNode display lists, RenderThread and `android::Surface` from the installed
API29 component. It does not replace HWUI with a raster image viewer.

`sd-hwui-native.cpp` is a small Android-ABI library compiled against the AOSP
`android-10.0.0_r47` native headers and libc++ commit
`d356ee1683aa5681564c81ad69fe19bc6abd5da5`. Stable HIDL declarations are fetched
from VNDK snapshot `5f9884aa352825291757dfd6694b874ad8c1805e`. No HIDL service or
SurfaceFlinger is installed. The matching Android libraries provide all C++
objects; opaque pointers and C function tables cross into the glibc host.

The Surface producer supplies geometry and an opaque local window ID. Actual
GPU buffers, gralloc handles, fences, buffer release and Wayland commits belong
to the existing Sailfish libhybris Wayland EGL platform. EGL resolves the ID
from AOSP's ReliableSurface and creates its window using the associated
`wl_egl_window`. A second Activity/dialog uses a Wayland subsurface. The host
shell has a GPU-drawn background, so its lifetime spans Activity transitions.
No `Bitmap.copyPixelsToBuffer`, `glReadPixels`, wl_shm pool, or CPU image pipe
participates in this HWUI frame path.

libhybris wraps `eglSwapBuffersWithDamageEXT` with its Wayland
prepareSwap/finishSwap callbacks. Its raw KHR lookup does not perform those
callbacks. The compatibility layer implements the KHR contract through the
platform-aware EXT entry point, retaining buffer fences and damage hints.

AOSP's isolated renderer option supplies its native 16 ms RenderThread vsync
source and sRGB display defaults without contacting SurfaceFlinger. Java's
Choreographer continues using the process-owned Wayland display callbacks.
This is hardware rendering; a dedicated native compositor-vsync adapter is a
separate timing improvement.

The public Java EGL14 window-surface API remains explicitly unavailable. Its
isolated direct-window diagnostic rendered through Adreno but exposed a
Sailfish compositor failure at teardown; it is not an accepted product path.
HWUI's RenderThread uses its own C++ EGL path and verified Activity teardown.

This boundary covers ordinary hardware-accelerated Android Views and local
window presentation. It does not provide Vulkan, Android SPHAL driver
namespaces, protected buffers, SurfaceTexture video producers or cross-process
Surface parcels. The explicit `SAILDROID_HWUI=0` diagnostic mode retains the
previous software path. APKs that explicitly disable application hardware
acceleration also select that compatibility path; they are not reported as
hardware-accelerated Views. The Qt/WPE WebView engine still exports its page image
to Android separately; its page export is not made zero-copy by HWUI.

Upstream references (Apache 2.0):

- https://android.googlesource.com/platform/frameworks/native/+/android-10.0.0_r47/libs/gui/
- https://android.googlesource.com/platform/frameworks/base/+/android-10.0.0_r47/libs/hwui/
- https://android.googlesource.com/platform/system/libhidl/+/android-10.0.0_r47/

The existing device libhybris is used dynamically and is not repackaged here.
