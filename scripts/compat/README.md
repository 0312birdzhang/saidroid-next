# Android API29 compatibility regression

This is a focused device regression for the independent ART implementation. It
is not the Android CTS/VTS runner and does not establish Android certification.

The signed temporary APK runs four **unmodified** AOSP libcore test classes with
JUnit 3: CRC32, Adler32, reflection Array, and Integer (86 tests). The vendored
files retain their Apache headers; `upstream/manifest.json` pins Android
10 r47's commit, original paths, and SHA-256 hashes. The builder verifies these
hashes before compiling. `upstream/LICENSE` contains Apache License 2.0.

Another 23 public-API contract groups exercise Parcel, Bundle, Intent, Uri,
Base64, JSON, resources/density, app identity/classloading, private files,
SharedPreferences, SQLite bind/rollback/blob/null behavior, main/worker Handlers,
monotonic time, executor error propagation, SHA-256, ZIP and CookieManager.
The tests run inside the real signed APK process, not Robolectric or host Java.
`android-all` is the compile/framework input; device execution uses independent ART.

The serial suite also checks physical input and real page pixels for the
WebView Java bridge/navigation flow, native WebKit headers/cookies/redirects/
popups/POST, HWUI click/dialog and two Cover cycles, resumed static pixels,
background CPU, and a controlled scrolling workload. Each device transaction
holds `scripts/devlock.sh`, checks Wayland responsiveness and returns the screen
to brightness 0. Pure API and native WebView tests never wake it.

Build inside `MeeGo Build` using the repository's existing toolchain and signing
key. The staged component must already contain the matching product build.

```sh
python3 scripts/compat/build-apk-vm.py unique-apk-tag
# The WebView flow uses its own signed VerificationProbeActivity APK.
python3 native/webview/qt-helper/build-probe-apk-vm.py r86-verification2 VerificationProbeActivity
# Existing HWUI/scroll probes are prerequisites (see native/hwui/README.md).
bash scripts/compat/run-suite-vm.sh unique-run api29-staged-release unique-apk-tag
```

Set `SD_WEBVIEW_APK_TAG` to a different built WebView APK tag when rerunning.
Evidence is saved beneath `build/compat/`, `build/hwui/` and
`build/qq-startup-webview/`. Temporary app records have no desktop entries. The
runners restore the previous component; selecting a new default is a separate
verified deployment transaction. The one-page result and known unsupported APIs
are recorded in `docs/ANDROID-COMPATIBILITY-2026-10-29.md`.
