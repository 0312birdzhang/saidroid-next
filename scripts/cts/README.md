# Official API29 compatibility attempts

`run-modules.py` runs a reproducible, bounded first pass across the 377 official
Android 10_r16 ARM configuration files. It is not an Android CTS certificate.

- Java tests bind the APK's real declared Instrumentation through ActivityThread,
  including distinct test and target APK Contexts when supported by the candidate.
  The original runner emits status bundles and a final callback. APKs/DEX and
  assertions are unmodified.
- Packages are temporarily installed under `/home/art/apps` using exact SHA-256
  input records, with no desktop entries. This does **not** provide Android-grade
  per-package UID isolation. Android dangerous/signature permissions are not
  invented or automatically granted.
- Standard device preparers (Android shell, permission controller, reboot,
  policy changes, etc.) are preserved as requirements. Implemented preparation
  includes exact APK inputs, device-targeted DynamicConfigPusher data, and the
  declared signature-test input files. Successful individual tests do not prove
  all module preparers or full CTS acceptance.
- Original GTest ELF binaries are run as the ordinary phone user where the
  existing system Android linker can load them. Their environment is recorded:
  this is **not** the SailDroid in-process glibc bridge. A loader failure,
  unsupported runtime, required reboot, or deadline is retained explicitly.
- Tradefed host/JVMTI/graphics configurations require a matching Android/ADB
  target. The official Tradefed configuration factory has validated all 377
  configurations, and the official console's target allocation fails without
  such a target. Configuration loading is not a module test pass.

The runtime and this batch execute the ARM64/full-APK mode only. The ARMv7,
instant-app, and other generated official configuration parameter variants are
not silently counted as executed. Each of the 377 source configurations is a
dispatch entry, not the total of all ABI/mode combinations or Android APIs.

Every phone mutation holds the project device lock. Runs keep OLED off, have an
independent blank watchdog, and verify boot/compositor identity, current daily
release, cleanup, and actual brightness before allowing serial continuation.
A cleanup or identity failure stops the batch. Never reuse a result from a prior
boot, candidate, APK hash, or run label.
Instrumentation transactions also require a real, surface-free Wayland sync
before installing test inputs and after cleanup. An unchanged compositor PID
does not establish that its event loop is responsive. A failed sync preserves
the raw test outcomes, marks the transaction unsafe, and stops the dispatcher;
it does not turn those outcomes into accepted compatibility evidence.

`--max-seconds` bounds each instrumentation runner, excluding input download and
staging. A configuration can declare multiple runners. The initial diagnostic pass supplied
AndroidJUnitRunner with `timeout_msec=15000` (15 seconds per test).
These deadlines can truncate a module; they must be reported and followed by a
longer run when its prerequisites are implemented. They are not default CTS
certification timing or a claim that every test was executed.
New runs honor the original runner's declared `test-timeout` (or the verified
10_r16 Tradefed default of 300,000 ms) when providing `timeout_msec`.
The earlier 15-second diagnostic limit could interrupt a long native call and
surface as a listener/cleanup failure after its individual PASS event. Such
attempts remain in history. Overall runner deadlines still bound every attempt.
Runner final summaries are audited independently of individual status events;
`FAILURES!!!`, reported failures/errors, or an aborted callback prevent success.

`--module-timeouts` accepts a recorded per-configuration JSON map. Second-round
PDF/OS/Text/View/Widget bounds are longer than the first pass; comparison reports
keep added/missing terminal events separate from changes to matched tests.

For device-targeted dynamic configuration, `PrepareDynamicConfig.java` uses the
original Tradefed DynamicConfigPusher URL and DynamicConfigHandler merge code.
The HTTP result, retrieved flag, source and prepared hashes are recorded. The
runtime's instrumentation-only provider serves whitelisted, hash-verified files
read-only from the private test data directory. Unavailable remote configuration
is recorded explicitly. This provider is not exposed to normal application runs.

FilePusher supports declared files only beneath
`/data/local/tmp/signature-test/`. The transaction refuses existing destinations
or untrusted parents, installs exact hashed bytes read-only, and removes only
those files and directories it created after tests exit. Other Android preparers,
including package signature inventory generation, remain unimplemented.

`attempt.json` records module disposition; `instrumentation-events.jsonl` and
`instrumentation-result.json` preserve the runner's evidence. `report-suite.py`
aggregates dispatch counts separately from single-test events.
`NO_TESTS` status means no individual test event was emitted and must not be
counted as an executed/passed module. A normal runner finish alone is insufficient.
The optional
`diagnostic-junit.xml` is labelled diagnostic and is not `test_result.xml` from
CTS/Tradefed. `reconcile-results.py` only rebuilds aggregates from retained raw
evidence and preserves the original aggregate file for audit.

Official inputs come from Google's published API29 archives via HTTP ranges.
`official_archive.py` verifies ZIP sizes and CRC, records SHA-256, and bounds
individual input sizes. The large full CTS ZIP is never retained. Canonical
inputs are kept only when useful for reproduction; duplicated phone/test input
copies are removed after verified cleanup.

`compare-rounds.py` pairs terminal events by unchanged configuration/APK identity,
runner index/type/package, test class/name and occurrence. It reports matched
fixes/regressions, still passing/failing, newly executed and missing outcomes
separately. Its counts are not an Android API compatibility percentage.
