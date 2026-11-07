# Resident-library queries

`RTLD_NOLOAD` must only return an already resident library. In particular, an
existing ELF file is not permission to map it or run its constructors during a
query. A successful query acquires a reference, which `dlclose` releases.

The patch preserves the Android-linker resident-object lookup and its reference
counting, then handles this flag before the file-loading branch. Host libraries
already loaded by glibc remain queryable through glibc's own `RTLD_NOLOAD` path.
It does not add a package-specific library rule or invoke JNI initialization.

Sources:

- [Android 10 dlfcn flags](https://android.googlesource.com/platform/bionic/+/android-10.0.0_r47/libc/include/dlfcn.h)
- [Android 10 linker load refusal for RTLD_NOLOAD](https://android.googlesource.com/platform/bionic/+/android-10.0.0_r47/linker/linker.cpp)

`test-vm.py` contrasts the old and patched loaders with a real ELF constructor
and destructor, repeated full-path and SONAME queries, final unload, host-library
queries, and one-shot error retrieval. `phone-fixture-vm.py` builds the same
fixture in the configured VM and runs it on the phone as `defaultuser`, with
the OLED off and under the device lock. Its evidence paths intentionally belong
to the r320 development run; they are not a general release installer.

The fixture proves linker semantics. The r320g WeChat replay still reaches its
original null-object JNI failure; this patch alone is not a WeChat startup fix.
