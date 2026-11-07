# Native StrictMath on the ARM64 host

The older standalone Android host makefile recognizes `arm` and `x86` for
fdlibm's `__LITTLE_ENDIAN` setting, omitting `arm64`. Its double-word macros then
read the wrong halves on this little-endian host. The observed failures include
ordinary exp/log/sqrt/hypot operations, not just rounding differences.

Build the actual existing fdlibm algorithms with the correct compiler byte
order and their IEEE/aliasing settings:

```sh
python3 native/compat/build-fdlibm-helper-vm.py /var/tmp/saildroid-fdlibm-build
```

The builder verifies all 80 sources and headers against this repository's
nested source snapshot, compiles outside that snapshot, disables floating-point
contraction, and records the compiler, commands and source/payload hashes.
It creates `libsdstrictmath-fdlibm.so` with only the 50 private `ieee_*` entry
points exported. It does not export host libc's `sin`, `exp`, `pow` or other
standard names, replace JNI registrations, or alter `/home/art/lib/libopenjdk.so`.

The captured phone libopenjdk calls these private functions through its existing
ELF symbol relocations. The trusted native host preloads the component's helper
before ART starts, and checks the actual owner of `ieee_exp` before accepting
that backend. The package option `--strictmath-runtime` validates the ELF,
source hashes, dependencies and exact export set, then records it in runtime
metadata. All ART roles use the same real algorithm backend.

The original 104 StrictMath tests were run on the unchanged captured phone
libopenjdk under an ordinary VM UID. They changed from 36 failures to zero with
the correctly built companion; the diagnostic also requires both actual DSO
mappings. That is component evidence. Phone execution and complete module
results are recorded separately in the CTS continuation report.
