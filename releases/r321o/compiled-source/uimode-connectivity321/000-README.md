# Isolated UI-mode product candidates U1 / U1A — VM reviewer packet

U1 is the preferred isolated causal candidate for a later Zhihu check. U1A is a separate composite containing the already phone-public-PASS connectivity change. Neither is installed, promoted, packaged as RPM or tested on the phone. Canonical sources and original V5 five-app failure remain unchanged. The new fixed-NO policy is owned Android resource behavior, not a claim about Sailfish dark theme.

## Exact predecessor and source attribution

Baseline-v1 verified the exact accepted ime-async-runtime-v1 class tree against its accepted full class map. Recompiling the accepted device-idle320 SdServices and activity-caller321 SdActivityHost snapshots reproduced all12 emitted classfiles byte-for-byte. Re-D8/hiddenapi encoding of the complete accepted class tree reproduced raw06119dd0…8137 and encoded `ec5048600e09cbb8cb8bc96831d6a84291fb8f7872dbdad36302f32f87d047cd` exactly. The stale canonical source copies were not used to replace either class.

U1 overlays only the two accepted integration classes plus new SdUiMode/SdUiModePolicy. Runtime hash `0760e377695b7415285374abdf310decd8e748c31087fa61b6c19d3d6606086e`. Ten classfile hashes change and two are added; none removed. Eight changed ActivityHost inner classes have byte-identical javap code; differences are line metadata from the added factory statement. Only main SdActivityHost and SdServices have intended code changes (owned policy application and normal uimode registration). Bytecode audit and exact source diffs preserve accepted lifecycle/clear-top/caller/device_identifiers behavior. Existing hidden API flags remain unchanged; new descriptors belong only to UI-mode classes.

U1A runtime `eb7e30783cad033a67d0efe202dbd94b41f7fea0c09ec13251d4acf4bf762495` overlays the identical UI-mode classfiles onto the exact connectivity candidate class tree. Its class map is verified as the exact union of U1 and the accepted→connectivity delta, including the old removed connectivity class. No connectivity class is rebuilt or edited. Dependency runtime `7a87f2dc2ac06f41bb5783e7d509a2ca291a21371c0d3812e402ce9b640f0461` and read-only helper `d882d45b7b8ed423b2c7522f52a3cff12137161878a9e76352bde394757b9151` match the prior public-phone PASS and remain separate attributed inputs. The helper itself was not rebuilt. U1 contains no connectivity change/helper requirement.

## Fresh images and final metadata

Each candidate has a fresh real dex2oat speed boot build (15 ordered boot jars,45 ART/OAT/VDEX files). Build logs, recipes, jar hashes, actual file hashes and bounded VM resource observations are retained. U1 took20.1s; U1A13.9s. Thirty-one image files differ from accepted and fourteen VDEX files are identical, but all45 belong to each freshly built set. Root/native/framework jars remain accepted except the candidate runtime.

Use the final `u1-metadata-v2` / `u1a-metadata-v2` files with their respective `*-images-v1/arm64` and `*-build-v1/encoded/lib/runtime.jar`. Metadata-v2 preserves first metadata evidence and corrects the inherited hidden_api manifest pointer to the actual candidate encoder manifest. This is provenance metadata only: runtime/image bytes are unchanged. It retains the original hiddenapi manifest hash explicitly as baseline provenance. Final image and hiddenapi manifests must be bound/staged at `share/build/boot-image-manifest.json` and `share/build/hiddenapi-manifest.json`, plus runtime.json at the root, when materializing an isolated candidate. Never bind only the new runtime against old images or old hiddenapi/image metadata.

`independent-verification.json` verifies both actual class maps, exact composite union, helper bytes, all45 images against actual files and their candidate jar identity, and image/runtime metadata consistency. `verify-candidates.py` ran successfully on host and VM. Metadata-v2 proof separately checks final metadata pointer hashes. None of this is a phone runtime mapping claim.

## Real framework configuration gate

Product-fixture-v4 uses the actual U1/U1A runtime jars and matching image directories under a read-only VM namespace. The boot-appended platform fixture contains only test setup/consumer classes; it does not override SdServices, SdActivityHost, SdUiMode, UiModeManager, ContextImpl or SystemServiceRegistry. The candidate's ordinary SdServices.installAll registers uimode before Context lookup. Candidate SdActivityHost.displayConfiguration returns0x11; its actual applyDisplayConfiguration invokes ActivityThread.handleConfigurationChanged. The test performs no manual Resources.updateConfiguration or manual binder injection.

Baseline reports the original undefined configuration and null service (3checks). U1/U1A each pass63checks:

- real ContextImpl public manager name/type caching, owned policy NO, current type NORMAL, matching actual Resources;
- actual ActivityThread.handleConfigurationChanged delivery to Activity and Application, with a non-night font-scale change preserved and callback/resource state matching;
- actual ActivityThread.handleCreateService→Service.onCreate reads initialized manager/resources using a genuine SdServiceHost-owned service token;
- actual ContentProvider.attachInfo→onCreate and normal ActivityThread-delivered provider/service configuration callbacks;
- setter UnsupportedOperationException with no configuration mutation;
- actual boot-runtime.art and boot-runtime.oat mappings present, alongside the precisely selected candidate45-file view.

Activity records/initial Application are fixture-created platform setup. Provider attachment is direct framework attachInfo, not a real APK authority-resolution launch. No window, full Activity resume, real Zhihu APK or normal desktop family was exercised. These tests prove the narrowed real framework boundaries, not phone startup success. Hidden API policy remains enabled; setup uses platform fixture reflection, which grants no hidden API access to apps.

Earlier product fixture-v1/v2 failures are preserved with exact source snapshots: harness lacked Instrumentation, then used an unknown synthetic service token. V3 corrected only fixture setup and passed62checks. V4 added actual image mapping assurance and passed63. Product candidate bytes did not change between those fixture attempts. The earlier source-design packet's manual callback tests are distinct and must not be relabelled as this normal ActivityThread delivery.

## Cache invalidation and storage

No app cache has been built at the product freeze. Changing runtime.jar and boot-image identities invalidates existing accepted app AOT dependency metadata. Old accepted app ODEX/VDEX must not be relabelled or used as matching candidate caches; ART checksum/context gates stay enabled. A later explicitly authorized cache build needs the complete original69-input closure, including all45 active images and six accepted inactive compatibility image files, original APK/dex identities, exact shared-library context and compiler dependencies. New cache and private namespace identities must be separate from accepted cache paths and verified before use.

Minimum uncompressed overlay bytes (runtime+45images+final metadata; U1A also helper) are approximately264.4MB U1 /264.6MB U1A. Active images alone are264171528 /264256560bytes. These are floors, not deployment budgets: archives, extraction coexistence, six compatibility files, cache artifacts, data/work/evidence and reserve are additional. The external `post-five-v5-health-v1/health.json` snapshot reports1380327424 free bytes, boot3fec/Lip9403; it is neither current allocation nor permission to reclaim anything. Prefer staging U1 only for the narrow causal target; no two-variant app caches or all-five rebuilds are implied.

## Review and next boundary

`reviewer-manifest.json` freezes sources, scripts, baseline proof, candidate class/output hashes,45images each, final metadata, fixture records and exact dependencies. No automatic phone runner is included. Root alone decides and reviews any later phone namespace/routing/cache/cleanup transaction; no global root installation, canonical adoption or RPM is authorized here. A later U1-only Zhihu quicken cache, if explicitly authorized, lives in a new evidence directory outside this frozen product closure and must use original installed APK/context bytes. Keep any failed or inconclusive target result, and retain full normal fresh-manager/broker/worker inheritance checks before phone acceptance.
