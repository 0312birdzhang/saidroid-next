# Opt-in application startup overlay

This directory retains the exact Java/C++ variants, patches, and real-app test
sources used for the r292 candidate. It does not change the frozen
`scripts/device` or `native/host` baseline and is not selected automatically by
the ordinary product builder.

The source variant combines the following functional changes:

- Let the application call its own `System.loadLibrary` instead of preloading
  MMKV through the unsupported `Runtime.loadLibrary(String, ClassLoader)` API.
- Schedule explicit unordered broadcasts to enabled receivers declared in the
  same installed APK through the real `IApplicationThread.scheduleReceiver` and
  `ActivityThread` callback path. Track actual `finishReceiver` completion,
  including `goAsync()`.
- Start a receiver's declared secondary process through the existing host family
  ownership checks and private Binder endpoint. Recheck declared component,
  process, user, and existing permission policy before dispatch.

Implicit manifest receivers and ordered/sticky broadcasts are outside this
overlay. Existing dynamic broadcast delivery is unchanged. An undeclared or
disabled explicit target receives no callback, matching an absent target rather
than inventing delivery. Permission grants, SDK binding, filesystem restriction,
Binder driver and canonical hidden-API flags are unchanged; added implementation
members remain private.

The separate ART signal-stack ownership change is retained under
`native/compat/art-host-signal-stack-ownership` and must be included for the tested
r292 combination. It remembers the exact guarded mapping ART allocated instead
of deriving an address to free from an application-replaced kernel stack.

`snapshot.json` hashes the retained inputs. The builder files are the exact
VM recipe snapshots from `build/evidence/qq-manifest-receivers292-20261102-v1`;
they intentionally reference the pinned historical inputs and use new output
directories. They are not a command to overwrite existing evidence or rerun an
already completed build. For a future build, create a new run directory, adapt
only its input/output paths, and preserve these gates:

1. Reproduce the accepted raw Java classfiles and native host/API bytes before
   applying the overlay. Use the installed instrumentation metadata and mutable
   temp/math host source variants, rather than the older shared source copies.
2. Retain every existing member's access/native flags. Encode from raw boot JAR
   inputs using the canonical encoder; verify existing policy entries unchanged,
   all additions private, and core/framework/boot bytes unchanged.
3. Compare the complete package manifest against its predecessor and stage a
   new isolated release without changing the daily entry.
4. Hold the VM device lock, quiesce owned hosts and Binder, and run the signed
   target SDK 29/34 receiver fixtures with actual callback/process receipts.
   Leave the OLED off. Require clean process and temporary APK cleanup.
5. Run the unchanged application only after the focused contracts pass. Keep
   failures and distinguish a bounded launch observation from long-term
   stability, performance, or full CTS acceptance.

The fixture covers local, asynchronous, declared remote and protected receiver
callbacks, main-thread/restricted-context/application-loader identity, copied
payloads, one dynamic broadcast control and five negative cases. It creates no
launcher entry and uses no real account data.
