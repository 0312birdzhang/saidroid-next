# Versioned app cache compiler

`compile-app-aot-vm.py` compiles unchanged, previously verified single-base APKs
inside the aarch64 Linux build VM. It does not access the phone, install a cache,
change an APK, or suppress ART verification. A successful build is not a target
startup or performance pass.

The required inputs are a successful accepted compiler result, its complete
component manifest, matching runtime.json, a verified installer app record,
the original APK, an explicitly confirmed `PCL[]` loader context, and a new
output directory. The record can be supplied directly or as the `app` field in
an inspection JSON. Split/shared-library/custom-loader compilation is outside
this wrapper's current scope; do not invent `PCL[]` for such workloads.

The wrapper verifies all referenced input bytes against both the accepted
recipe and component manifest, including the encoded platform runtime,
ordered extended boot classpath, logical boot locations, full core image
closure, ART library and properties. It verifies the compiler and records its
resolved ELF dependency hashes. The original APK and inputs are rechecked after
compilation. Failed builds retain logs but produce no installable cache manifest.

Example R320j recipe is retained in
`build/evidence/apps-performance321-20261104/performance/build-wechat-aot-vm.sh`.
Run it with the repository's `scripts/vmrun.sh` wrapper and `quicken` or `speed`.
The generic Python script has no package-name exceptions. Subsequent apps use
their own verified records and APK locations. Subsequent runtimes need an
accepted reference with the new exact encoded Java inputs.

Outputs include `recipe.json`, compiler log, bounded run resource/timing
measurements in `result.json`, `base.odex`, `base.vdex`, and on success a
`saidroid-cache-manifest.json` with a content key and installation preconditions.
The key includes APK identity/location, ordered boot inputs, compiler/dependency
hashes, compiler filter, ISA, class-loader context and debugging policy.

Before a separate authorized device transaction installs a candidate:

1. Acquire the project device lock, discover the live OS/boot/release identity,
   quiesce only SailDroid-owned runtimes and verify OLED-off state.
2. Verify the actual installed record, signer identities, unchanged APK bytes,
   full required runtime/image hashes and the actual class-loader context.
3. Check free space for the candidate plus a preserved previous cache. Transfer
   both files into a new sibling directory; verify byte sizes/hashes and set
   the package user's ownership and ordinary read permissions.
4. Write the complete manifest, preserve the old `oat/arm64` directory and
   rename the complete candidate into place while no runtime is using it.
   Roll back the directory if activation fails. Never overwrite a live file.
5. Launch normally; verify ART accepts the new cache and the correct ODEX/VDEX
   files are mapped, then require actual application content and physical input
   correctness. Measure baseline/candidate under the same documented workload.
   Clean up the owned app and verify display protection.

AOT artifacts are tied to their runtime. Runtime, launcher and cache rollback
must stay consistent. Do not transplant the R320j cache into a later runtime
without validating every recorded dependency.

The accepted R320j reference resolves sources through historical VM symlinks and
uses `/home/art/bin/dex2oat` plus VM libraries. These paths are verified but this
is not yet a standalone compiler distribution. The recorded `ldd` closure does
not guarantee coverage of dynamically opened plugins. A distributable optimizer
needs a separately versioned compiler/runtime dependency closure and a clean
environment replay before it can claim self-contained reproducibility.

## Shared library contexts

`PCL[]` is valid only after checking the installed app's actual parent classpath.
Optional `uses-library` entries can resolve to packaged platform JARs even when
the APK is a single base file. A cache can initially be opened by ART and then
rejected for a context mismatch; `GetBestOatFile(... executable=1)` alone is not
acceptance evidence. Scan the subsequent class-loader validation diagnostics.

For a non-empty single `PathClassLoader` context, pass
`--shared-library-context CONTEXT.json` and the exact target
`--class-loader-context 'PCL[/actual/release/system/framework/library.jar:...]'`.
The context manifest schema is `saildroid-shared-library-context-v1` and records
`package`, `apk_sha256`, `component_manifest_sha256`, `target_root`,
`stored_context`, and the ordered `libraries`. Each library contains a component
`relative` path, its build-host `source`, `sha256`, and `bytes`.

The builder checks every library against the pinned component, uses source paths
for `--class-loader-context`, and uses actual target paths for
`--stored-class-loader-context`. It verifies the emitted OAT classpath and
single-DEX JAR CRCs, then rehashes the inputs. It never disables ART's validation.
The current explicit grammar supports one PCL containing ordered component
framework JARs; arbitrary loader graphs and split APKs remain unsupported.

The target release path is part of cache identity. Moving an identical JAR from
`/home/art/releases/...` to `/opt/saildroid/releases/...` can invalidate an app
cache because the real runtime resolver uses `ANDROID_ROOT`. Rebuild against the
final installed root, or leave the cache inactive. Do not rewrite the recorded
classpath without recompiling.

Task 321 context audit found HTTP legacy for Douyin/XHS/QQ, HTTP legacy then
Android test base for WeChat, and Android test base/mock/runner then HTTP legacy
for Zhihu. These are actual APK declarations and the accepted resolver's order,
not package-name branches in the generic compiler. The previous PCL[] candidates
are retained as failed-context evidence and are not accepted target caches.

## Stored boot DEX experiment

`repack-dex-jars-vm.py` produces new JARs with stored, four-byte-aligned DEX ZIP
entries. It verifies every uncompressed entry and original encoded DEX byte for
byte. It does not activate a component or rewrite AOT manifests. A bounded real
ART CLI experiment converted five compressed framework DEX files into file-backed
mappings and reduced anonymous memory by 38,096 KiB. This is sharing eligibility
on the VM, not a measured phone speedup or a multi-process PSS result. Any adoption
requires a new component manifest, exact-input cache rebuilds, and target tests.

`--input-root` can select the final RPM-extracted payload for compilation. Every
boot JAR/image and runtime input is still checked against both the successful
reference's recorded hash and the new component manifest. Boot ordering and
logical `/home/art/api29-root` locations retain the reviewed native-host recipe.
The accepted compiler executable and its reviewed dependency environment remain
independently pinned; this option does not reinterpret an unexecuted recipe as a
successful reference. Final cache records carry the final component-manifest
hash and the real `/opt` shared-library context.
