The private `getprop` command reads the component's existing native property
backend through its real exported API. The executable derives its own component
root, verifies immutable root-owned file paths and selects that component's
build.prop. It supports one key, one key with a fallback, or sorted enumeration.
Unsupported type options and writes fail explicitly.

The backend binary is an exact copy of the app's existing Bionic translation
library; its defaults and limitations are preserved. No property values or test
names are handled specially. This does not implement a shared mutable Android
property service or assert that the host has become a secure Android user build.
The CLI and Java property reads are checked together in a real internal APK.

`build-private-getprop-vm.py` compiles the command and copies a SHA-pinned backend
without rebuilding it. It records source references separately from binary build
provenance, verifies the native ABI, and carries the existing linker notices.
`package-property-overlay.py` composes this into a new isolated artifact while
preserving every existing native, Java, boot-image and manager byte.

The component metadata declares its first implemented platform API (29), not the
phone vendor's shipping Android version. Its fingerprint derives from the same
existing brand/product/device/version/build/signing fields. Development signing
tags remain unchanged; Android partition properties are not invented.

The exact 1331-file r194-v2 artifact has been reconstructed and exercised with
the unchanged original OS APK and its declared AndroidJUnitRunner in the VM.
Both Build classes complete with seven passes and two retained failures: the
production signing-key check and actual Android partition inventory. This is a
nine-method diagnostic, not full OS/CTS or secure-build acceptance. The initial
archive's new 0700 directories were caught by the complete-artifact test and are
not admitted. New archive directories are now explicitly 0755 and verified in
the tarball as well as the reconstructed filesystem. No r194 phone staging has
occurred.
