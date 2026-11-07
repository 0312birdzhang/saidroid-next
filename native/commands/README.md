# Private Android application commands

`build-toybox-vm.py` verifies the recorded Android 10 r16 source archive and
builds its unchanged `touch` implementation with the Linux build VM's glibc.
The resulting component contains `bin/touch`, an upstream license, and exact
build provenance. It does not install a command into the Sailfish system.

The native application host starts ordinary app/declared-process roles at `/`
and prepends the component's `bin` directory to their inherited PATH when a
validated command runtime is packaged. Manager, broker, and session roles keep
their existing launch environment. No test name or instrumentation option
selects these behaviors.

This fixes the actual phone's BusyBox rejection of the ISO-Z date accepted by
Android's command and the inheritance of an unsearchable root SSH working
directory. Java filesystem calls and errors continue to come from the kernel.
Only `touch` is currently provided; other inherited commands still resolve to
the host environment. The unchanged upstream implementation rejects colon
numeric timezone offsets such as `+01:00`; support for that format is not
claimed. UTC `Z`, nanoseconds, reference timestamps, access/modification-only
updates, symlink timestamps and invalid-input behavior are exercised by the
ordinary-UID contract in `tests/command-contract-vm.py`.
