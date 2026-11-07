#!/bin/bash
cd /tmp/art-build/bionic_translation/builddir
echo "=== dynamic symbols (malloc family) ==="
nm -D --defined-only libc_bio.so.0 | grep -E "malloc|free|realloc|memalign|valloc" | head -20
echo "=== is malloc defined at all? ==="
nm -D libc_bio.so.0 | grep -w malloc | head
echo "=== readelf dynsym count ==="
readelf -sW libc_bio.so.0 2>/dev/null | grep -c FUNC
echo "=== grep SD_GUARD strings present? ==="
strings libc_bio.so.0 | grep -c "SD_GUARD"
