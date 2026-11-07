# Live media refresh and keyboard dismissal

The runtime MediaStore provider reconciles the existing read-only media roots on
query. It inserts new files, refreshes metadata when size or modification time
changes, and removes missing files in one SQLite transaction. Unchanged files
reuse their decoded dimensions. Existing path IDs stay stable; hash collisions
allocate the next unused ID. Roots that do not yet exist are retained so a later
Pictures/DCIM directory can appear without restarting the Android process.
Canonical path checks, read permission enforcement and read-only item handles
continue to apply. The existing scan depth and file-count limits remain.

`SdInputMethods` presents a non-focusable “收起 ⌄” button inside the currently
focused editor's Android decor while the Sailfish keyboard is visible. Tapping
it clears the show request and asks the real Maliit peer to hide. Its area
callback restores app geometry and removes the button. Native keyboard-initiated
hide also clears the show request; temporary host focus loss preserves it.
The button is removed on editor finish and host focus loss.

`baseline/` reproduces the accepted r313y MediaStore and input-method classfiles
with the repository's Java 8 build settings. The baseline InputMethods excludes
the source-only `requestShow()` helper, which was absent from that runtime.
`probe/MainActivity.java` tests permission denial, a root/file created after
provider initialization, image modification with a stable ID, removal and
rejection of provider write handles on both target SDKs 29 and 34.
