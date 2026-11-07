# Frame-path performance work (sd-runtime)

Everything in this directory exists to answer one question with numbers: **where does
one frame of a SailDroid (standalone ART / API 29) application go?** Nothing here counts
"the process is alive" or "the screenshot worked" as a performance result.

## The pipeline being measured

```
App thread:  ViewRootImpl.drawSoftware -> Surface.lockCanvas (JNI: SdSurfaceStore.lock)
             Canvas ops -> Bitmap
             Surface.unlockCanvasAndPost  (JNI: SdSurfaceStore.unlock)
               -> compose(): erase scene, blit every layer, scene.getPixels(int[1080*2160])
               -> SdWindowHost.present(int[])            (JNI: nativePresent, GetIntArrayRegion)
Wayland thread: publish(): memcpy int[] -> wl_shm buffer, attach+damage, wl_surface_commit
Compositor:  wl_surface_frame callback -> SdDisplayFrames.onFrame -> Choreographer vsync
```

The compositor callback is **not** a 60 Hz clock. On this device it is "I composited a
frame of this surface", measured at mean 401 ms / p50 161 ms / max 1289 ms during QQ's
burst. Treating it as a clock is a mistake we already made once.

## Instruments

Native sampling (`native/window/sdwindow.c`), on only when `SAILDROID_PERF` is set:

| field | meaning |
| --- | --- |
| `vsync` | last compositor frame callback before this frame |
| `lock` / `lr` | `Surface.lockCanvas` entered / returned (pure `View.draw` starts at `lr`) |
| `unlock` | `unlockCanvasAndPost` entered (draw finished) |
| `present` / `pdone` | `SdWindowHost.present` entered / int[] copied into native memory |
| `mw` | UI-thread time waiting for the native frame mutex |
| `memcpy` | int[] -> wl_shm copy inside `publish()` |
| `commit` / `release` | `wl_surface_commit` returned / `wl_buffer.release` |
| `ui` | whole synchronous compose+present cycle on the UI thread |
| `cinv` | ordinal of this commit inside the current vsync interval |
| `gap` | time since the previous compositor callback |
| `drop` | frames dropped because both SHM buffers were busy |

Sampling is **streamed**: one line per commit, `fflush`ed immediately, so a process that
dies (QQ calls `System.exit(0)`) still leaves the frames it managed to produce. The meta
line (`SDPERF=meta|api=5|...`) is written when the window thread exits.

Meta counters that answer "did the app even ask?":

| field | meaning |
| --- | --- |
| `locks` / `unlocks` | Java `SdSurfaceStore.lock()` / `unlock()` entries (did a view really draw) |
| `jdraws` | `transactionComplete()` calls |
| `composes` | `compose()` runs |
| `creq` / `cfall` | coalesced compose requests / fallback (100 ms) fires |
| `fast` / `layers` / `layer_full` / `layer_identity` | single-full-screen-layer fast path hits and the last scene shape |
| `dinit` / `dsched` | `DisplayEventReceiver.nativeInit` / `nativeScheduleVsync` calls from the app |
| `rf` | `SdWindowHost.requestFrame` calls reaching the window thread |
| `fcb` | compositor frame callbacks received |
| `fcommit` / `ecommit` | commits that carried a new buffer / commits issued only to get a callback |
| `force` | `SAILDROID_FORCE_FRAME_COMMIT` mode in effect |

## Judgement rules (do not skip these)

* `steps ≈ 1000` (driver ticks) with `locks <= 2` -> the scene never redrew; the frame
  pump is innocent, fix the scene.
* `locks ≈ steps` but `composes <= 2` -> frames were produced and not composited;
  `dsched` / `rf` / `fcb` then say whether the request or the answer is missing.
* Fewer than 100 frames -> report "insufficient sample", never a p95 or an fps.

## Environment switches (all default off, so an unset run is the old code path)

| variable | effect |
| --- | --- |
| `SAILDROID_PERF=1`, `SAILDROID_PERF_FILE=...` | enable streaming sampling |
| `SAILDROID_NO_FASTPATH=1` | disable the single-layer fast path (A/B baseline) |
| `SAILDROID_COMPOSE_ON_VSYNC=1` | coalesce composes to the compositor callback (+100 ms fallback) |
| `SAILDROID_FORCE_FRAME_COMMIT=attach\|empty` | diagnostic: when the app asks for a vsync without a new frame, re-attach the on-screen buffer and damage 1x1 (attach) or issue the bare commit (empty) |
| `SAILDROID_DIRECT_SHM=1` | UI thread copies the Java pixel array straight into the spare `wl_shm` buffer (no staging array, one full-screen copy less); default off, A/B-able |
| `PERFSCROLL_MODE=heavy\|light\|blank\|touch\|pulse` | test scene; `pulse` is the pure frame-pump probe (no scrolling) |
| `PERFSCROLL_DRIVER=choreographer\|handler\|both` | drive from the Choreographer or from a 16 ms `Handler` |

## Reproducing one window

```bash
scripts/devlock.sh acquire 900 sd-runtime
bash scripts/perf/session-vm.sh perf7 --only scroll-pulse-handler --only scroll-handler
scripts/devlock.sh release sd-runtime
```

`session-vm.sh` refuses to run unless the lock owner is `sd-runtime`, closes leftover
owned processes, deploys the release, installs the probe APK and runs
`run-matrix-vm.py`. Each run leaves `build/perf/<tag>/{perf.bin,meta.json,stats.json,
report.md,app.log,shot.png}`.

## Build-time JNI contract gate (mandatory before any native build)

`scripts/perf/check-jni-contract.py` compares every JNI lookup in `native/window/*.c`
with the Java side **by exact JVM descriptor** (it parses the compiled `.class` files,
so it sees `J` vs `I`, not just the field name):

* `GetStaticFieldID(e, <class>, "<name>", "<sig>")`
* `GetStaticMethodID(e, <class>, "<name>", "<sig>")`
* classes named in `FindClass` (own sources, or the framework jar for `android/*`)
* every `JNINativeMethod` table entry: the Java method must exist with that signature
  and the C function it registers must be defined in `native/window`

Exit code 3 and `BUILD_RC=refused_field_mismatch` mean *do not build*.
`build-perf-release-vm.py` runs it before compiling and again with `--so` afterwards.

```bash
scripts/perf/gate-jni.sh                          # VM-side wrapper
scripts/perf/selftest-jni-gate.sh                 # proves the gate has teeth
```

The self-test mutates `lastLayerCount` to `int` (the r64 crash) and points a
`RegisterNatives` entry at a non-existent function; both must be refused.

## Facts learned the hard way

* The application classloader **cannot see classes from our `runtime.jar`**
  (`ClassNotFoundException: SdDisplayFrames`). Diagnostics must use the app's own
  counters or runtime-side logs; do not reflect into our classes from an Activity.
* A commit that changes nothing may give the compositor no reason to composite, and the
  frame callback only arrives when it does. Hence the `SAILDROID_FORCE_FRAME_COMMIT`
  diagnostic variants instead of changing `publish()` behaviour by default.
* QQ exits by itself (`System.exit(0)`) seconds after its login page appears, right after
  `com.tencent.turingfd.sdk.xq` reports `SSLHandshakeException ... (error code: -329)`.
  The measurement window is therefore reported as the measured lifetime, never as a
  requested observation time.
* **A timer field's Java type is part of the ABI.** `GetStaticFieldID(..., "lastLayerCount",
  "J")` against `private static int lastLayerCount;` returns NULL, leaves a pending
  `NoSuchFieldError`, and ART aborts the whole app at the next JNI call -- the stack
  looks like an internal GC crash. All perf counters are `long` on the Java side, and
  native must not trust a `jfieldID` (see `sd_perf_fields_guard`).
* **A long in a colour expression is a packed ColorLong.** `paint.setColor(0xff000000 | (x * 2654435761L))`
  made the framework parse it as a ColorLong and `ColorSpace.get()` threw
  `IllegalArgumentException: Invalid ID, must be in the range [0..16)` inside `onDraw`; the app
  died with `System.exit code=10`. Keep colour arithmetic in `int`.
* **ScrollView measures its child with an UNSPECIFIED height.** A custom `View` that does not
  implement `onMeasure` reports 0, `scrollTo()` clamps to 0, and the "scrolling" scene never
  scrolls (`scrollY=0` in all 1087 steps, first measured on `scroll-handler-r78`). The probe now
  overrides `onMeasure` and also counts app-side `draws` (OnDrawListener) and `appvsync`
  (its own `Choreographer`), so "did it redraw" never depends on runtime counters.
* **`sdinput` takes five separate numbers**, not `x1,y1` pairs: `sdinput swipe X1 Y1 X2 Y2 [dur]
  [steps]`. Passing `540,1700` makes `atoi()` read `x1=540 y1=540` and the gesture silently lands
  elsewhere (measured on device: `SDINPUT=swipe|x1=540|y1=540|x2=1500|y2=60|dur=400|steps=24`
  for a request of `540,1700 -> 540,700`). `run-perf-vm.py` now splits the pairs.
* **Compositor callbacks arriving is not the same as the app drawing.** `scroll-swipe-r78`:
  `dsched=191 rf=192 fcb=192` but `locks=1 fcommit=1` — 192 frame callbacks, one committed
  frame. A single probe scene cannot distinguish "frame pump deadlock" from "scene never
  invalidated", which is why the app-side counters exist.
* Existence of a symbol/string on both sides proves nothing: `grep lastLayerCount`
  finds it in `jdeps`-clean code and in code that crashes. The check must be
  "the lookup resolves with this descriptor", which is what the gate does.

## Direct pixel copy (SAILDROID_DIRECT_COPY, r79)

Measured on r78 (`PERFSCROLL=micro`, 1080x2160 ARGB_8888, median of 3):

| copy | ms |
|---|---|
| `Bitmap.getPixels` into `int[2332800]` | 48.60 |
| `System.arraycopy` 9 MB (self copy) | 0.00 -- JIT removed it, unusable as a baseline |
| `Bitmap.copyPixelsToBuffer(ByteBuffer)` | 3.13 |

`getPixels` was also the largest single stage of a steady-state frame: 28.10 ms of a
33.42 ms UI-thread frame in `scroll-pulse-handler-r78` (368 composes, 176 dropped).

The path: the window's two `wl_shm` buffers are `WL_SHM_FORMAT_ABGR8888` when the
compositor advertises that format (`wl_shm_listener` collects the format list at bind
time) and `SAILDROID_DIRECT_COPY` is set. `SdWindowHost.directAcquire()` returns a
direct `ByteBuffer` over the spare buffer, `Bitmap.copyPixelsToBuffer` fills it, and
`directCommit()` marks it ready; `publish()` attaches ready buffers before the staging
path. Because ARGB_8888 memory is RGBA byte order, ABGR8888 is the matching shm format --
if the compositor does not advertise it, `directAcquire()` returns null and the old
`getPixels` + `JNI GetIntArrayRegion` path runs unchanged (`dcopy=0`, `dmiss>0` in meta).

Proof counters in `SDPERF=meta`: `dcopy` (frames actually sent through the ByteBuffer),
`dmiss` (acquires that found both buffers busy). A run that reports `dcopy=0` did not
optimise anything.

Reproduce (VM, one lock window):

    scripts/devlock.sh acquire 600 sd-runtime      # only after the Lead says GO
    scripts/perf/install-scroll-vm.py r79-probe4
    python3 scripts/perf/run-matrix-vm.py r79 --only scroll-color-legacy \
        --only scroll-color-copy --only scroll-pulse --only scroll-pulse-copy \
        --only scroll-copy --only qq-copy
    scripts/devlock.sh release sd-runtime

`scroll-color-*` is the byte-order oracle: five pure R/G/B/W/K bands, screenshot
compared between the staging and the direct path. A swapped R/B is a pixel diff, not an
argument about memory layout.

### Three buffers are part of the optimisation (r79, measured)

Same binary, same probe scene (scroll, handler driven, 12.5 s window), only the env
changes; the two-buffer staging run is the r78 baseline:

| configuration | UI-thread ms/vsync mean / p95 | `getPixels` | commit rate | frames lost |
|---|---|---|---|---|
| staging, 2 buffers (r78) | 37.76 / 55.40 | 31.95 | 21.1 /s | 176 publish drops |
| staging, 3 buffers | 41.76 / 57.83 | 34.57 | 20.8 /s | 0 |
| direct copy, 2 buffers | 46.53 / 56.08 | 3.70 | 20.1 /s | 339 direct misses |
| direct copy, 3 buffers | **10.05 / 15.42** | **3.56** | **32.2 /s** | 0 |

Reading: one more buffer on its own buys nothing (20.8 vs 21.1 commits/s), because the
UI thread is the bottleneck. Removing the 28 ms `getPixels` only pays off when a spare
buffer is available: with two buffers the UI thread waits for the compositor
(`java_lock` 0.10 ms -> 36.06 ms) and the direct path *loses* frames. With three buffers
the UI thread drops to ~10 ms and the run becomes compositor-bound (`frame_interval`
31 ms). `SAILDROID_TRIPLE_BUFFER=1` selects three; both switches are opt-in because the
default path must stay byte-for-byte the shipped one.

Frame-loss counters are separate on purpose: `drop` is the staging path dropping because
both buffers were busy, `dmiss` is a direct-path acquire that found no spare buffer and
`ddrop` is the commit dropped as a result. A run can report zero `drop` and still be
losing frames on the direct path.

Functional parity (`scripts/perf/functional-probe.sh`, VM, Pillow): QQ login page and the
colour oracle are pixel-identical between the staging and the direct path at tolerance
8/255 (`build/evidence/r79/functional.json`), so the format choice does not swap R and B.
