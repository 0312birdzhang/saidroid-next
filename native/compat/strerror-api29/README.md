# Android 10 strerror_r bridge

QQ's unmodified libqqxfoundation_shared.so calls the Android integer-returning
strerror_r from std::error_code::message after a missing CDN metadata file.
Without bionic_strerror_r, the translation linker falls back to the GNU host
symbol. The host returns a string pointer; Android libc++ interprets its low
bits as an error number and calls abort. This affects ordinary native error
handling, independently of rendering.

strerror-api29.c exports bionic_strerror_r, the name the existing linker checks
before the host symbol. It uses the Android 10 error strings and contract:
return 0 with caller-owned NUL-terminated text and preserved errno; truncate
with -1 and errno=ERANGE. No process abort handler or application library is
modified. The host GNU symbol is unchanged. The upstream file/hash and retained
license are recorded in upstream.json and the C source.

The accepted component recipe adds this C source to libsdhost29.so, rebuilding
the exact previous command first and requiring its byte-identical output.
The recorded r302 recipe and all input hashes are under
build/evidence/qq-strerror302-20261103-v1. Its baseline is the r300 graphics
libsdhost29.so (also used unchanged by r301); Java, ART and framework bytes
remain inherited from r301.

relocation-fixture.c and probe.py exercise real unversioned strerror_r ELF
relocations through the component's Bionic linker. The test uses a host errno
accessor only to inspect that thread's errno. It checks known and unknown
errors, exact and truncated buffers, zero length, errno preservation, boundary
canaries and 8 concurrent workers. Run baseline and candidate in separate
processes to prevent global symbol contamination. The phone driver must use
the normal host library search path (component/lib:/home/art/lib).

The VM and phone tests each have an r301 negative control and 30 boundary
checks plus 1600 concurrent calls. They prove the native ABI; the separate
bounded QQ conversation run determines application acceptance.

A reusable build driver is provided (VM paths):

    python3 native/compat/strerror-api29/build-vm.py \
      --baseline-build-json build/evidence/qq-surface-texture300-20261102-v1/native-build.json \
      --output /var/tmp/saidroid-strerror-next

The output directory must be new. The driver verifies the baseline binary hash
before compiling the new bridge and records the full source/command closure.
Do not replace a deployed library in place; package an isolated component.
