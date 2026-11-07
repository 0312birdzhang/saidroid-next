# Native startup, app heap and background Cover snapshots

This directory records the selected source overlay for the QQ performance and
Cover work. It leaves the frozen CTS inputs and the established shared source
variants intact. Candidate packaging selects these exact snapshots and verifies
the installed file hashes; arbitrary current working-tree files are not inputs.

The native host admits one heavy application initialization through the existing
FIFO, starts that application's VM while the independent private Binder broker
initializes, and waits for the verified broker before invoking Java. Monotonic
native phase markers make the overlap observable. The manifest supplies a
bounded application heap policy: 16 MiB initial size, 4 MiB minimum free slack,
16 MiB maximum free slack, 0.75 target utilization; the existing maximum heap
and application/debug/hidden-API policies stay unchanged.

The app continues to render through its original HWUI/GLES Wayland subsurfaces.
On a real foreground-to-background transition, the UI thread records visible
application RenderNodes, including dialog ordering, insets and dimming, into a
540-pixel-wide composition. HardwareRenderer renders that composition once;
the result is committed to the parent as a static Cover after stop settles.
Secure windows suppress the snapshot. No compositor or display screenshot is
read and ordinary foreground frames do not perform CPU readback. Two bounded
SHM buffers track real Wayland releases and wake a pending Cover update when
one becomes available. Snapshots are process-private memory and are not saved
to user storage by the implementation.

A stale QQ AOT cache compiled against r86 is invalid with the current boot
classpath and runtime.jar. Rebuild from the unchanged APK with the exact full
extended boot classpath, logical locations, and `PCL[]` application context.
The recipe verifies every runtime input hash. The selected cache works with
all later candidate releases whose Java boot inputs are identical. Cache
replacement checks the old bytes against verified VM backups, stages and
hashes new files, then renames the directory. The original APK, certificates
and application data are retained.

`tests/` contains an ordinary signed-app source for RGB/BGR Cover generations
and a real dialog. Device probes use physical edge swipes and locate the card
from its measured colors before tapping it. Both semantic lifecycle markers
and screenshot pixels must agree. `recipes/` preserves the exact versioned
build/probe recipes and their predecessor requirements; they replay the
corresponding isolated evidence workspaces, rather than a standalone SDK setup.

The integration also includes `native/compat/linker-thread-errors/`, because
faster native initialization exposed the old process-global `dlerror()` race.
Functional acceptance, measured timings and deployment status are recorded in
`docs/QQ-PERFORMANCE-COVER-2026-11-03.md`.
