# Native library filename compatibility

The baseline is the exact SdAppRegistry source whose compiled classes match the
deployed R318b runtime. The source permits `$` as one additional character in a
single arm64 library basename. Some real signed APKs, including WeChat 8.0.80,
use names such as `libapp.$cso.so`.

The change does not alter signature verification, update signer matching, ABI
selection, directory traversal checks, duplicate detection or the `_bio.so`
reserved-name guard. Filenames are passed as file paths, never shell commands.

R319 builds only SdAppRegistry.class over verified R318b classes, preserves all
other class hashes and hidden API members/flags, and rebuilds the installer APK
from the same classes. The device evidence is under
`build/evidence/wechat-install319-20261104/`.

Acceptance uses the user's actual arm64 APK through the visible installer,
then verifies all 209 extracted library hashes. A failed 32-bit-only update must
leave the installed arm64 package record unchanged. Matching QQ AOT is rebuilt
when the runtime jar changes; the previous component/cache pair is retained.
