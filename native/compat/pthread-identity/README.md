# Android thread handles on a glibc host

Android libraries may pass `pthread_t` to public pthread APIs and may inspect
Bionic's ARM64 thread-list prefix for native diagnostics. A glibc thread object
has a different private layout. Returning a host `pthread_t` across that boundary
can turn a legitimate list traversal into a read of address 1.

`thread-identity.c` allocates independent opaque Android handles, records actual
kernel TIDs and pthread attributes, and translates handle-bearing APIs back to
the real host thread. Native glibc calls retain their ABI. The descriptor prefix
follows the Android 10 ARM64 layout; it contains real thread metadata rather than
an alias of glibc private memory. Already-created host threads are registered on
their first Android `pthread_self` call. The implementation does not attach or
detach JNI environments, suppress SDK errors, change thread entrypoints, or
identify particular applications.

A registry reference protects each in-progress operation. Canceled joins release
the reference through a POSIX cleanup handler. Creation disables cancellation
while waiting for the child registration handshake. Thread-key cleanup keeps the
handle valid through all POSIX destructor passes. Detached/imported descriptors
are reclaimed only after the kernel reports that the thread is gone. A forked
child resets the registry to its single surviving thread.

`build-vm.py OUTPUT` first reconstructs the exact accepted pthread helper before
adding the compatibility object. `test-vm.py OUTPUT` checks rejection of the old
ABI and exercises real TIDs, handle equality, names, linked-list consistency,
250 joined threads, 250 detached threads, destructor calls, imported host
threads, a timed join, cancellation of a blocked joiner, and fork identity.
Run these through MeeGo Build. The library is a candidate until phone rendering,
threading and official runtime tests accept the exact packaged bytes.
