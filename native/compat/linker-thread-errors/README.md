# Thread-local dynamic linker errors

The translated Bionic linker previously stored the pending `dlerror()` pointer
and its text in process globals. A second native loader thread could consume
another thread's error or overwrite text returned to it. QQ exposed this as
ART assigning a null C string in `JavaVMExt::LoadNativeLibrary` after a failed
load, producing SIGSEGV in `strlen`.

The selected change makes both error storage and the pending pointer thread
local. Loading still fails, `dlerror()` still consumes the error once, and
library trust, symbol resolution, JNI ownership and failure reporting retain
their existing behavior. No ART abort or application exception is intercepted.

`error-fixture.c` coordinates two real native threads for 100 iterations. It
checks cross-thread error consumption, missing owner errors, and overwrites
of the owner's returned string. The installed predecessor reproduces all three
failures 100 times; the candidate reports zero failures both in the VM and on
the phone as its ordinary user. The complete results are recorded under
`build/evidence/qq-linker-errors310-20261103-v1/`.

The recorded VM recipe builds a private copy of the accepted linker source.
The baseline reproduces every loaded ELF section except the build ID; only
the private DWARF compilation directory differs. The patch keeps existing
exported symbol signatures and adds the host TLS resolver import. Recipes
require the recorded predecessor build environment; inspect their exact source
paths before replaying them into a fresh evidence directory.
