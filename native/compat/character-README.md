# Android 10 Character native data

The captured phone `libopenjdk.so` links its original 23 Character entry points
to ICU 74. Android 10's matching Java and native ICU runtime uses ICU 63.2 and
Unicode 11. This changes public character classification: for example, U+30000
is unassigned in Unicode 11 and assigned in later Unicode versions.

`build-character-helper-vm.py` compiles the unchanged original `Character.cpp`
against the verified ICU63 headers and library. Its anonymous export map exposes
only the 23 existing Character ABI symbols from the actual captured phone
library. Function/data sections remove the unused registration function. The
helper has no dependency on `libnativehelper`, ART or ICU74.

The component's optional `--character-runtime` package input includes this
library, its source/header/compiler provenance and its original license notice.
It requires the matching packaged ICU63 library hash. The host preloads the
trusted private helper, checks its actual `getTypeImpl` symbol owner, and checks
the actual private ICU owner and native ICU/Unicode versions before entering ART.
Libopenjdk retains JNI registration, its other native implementations and its
existing dependencies. This does not claim removal of its ICU74 dependency.

The paired original-APK VM diagnostic preserves the actual captured phone
libopenjdk, SDK29, product JNI/Crypto/TLS bootstrap and ordinary UID65534. The
original four failing Character tests pass with ICU63; actual ELF binding traces
show all 23 registered entry points resolving to the helper. The helper does not
inspect test names, change Java results, or re-register JNI methods. Phone and
complete-module acceptance remain separate gates.
