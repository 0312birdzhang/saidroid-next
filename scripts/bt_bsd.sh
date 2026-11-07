F=/tmp/art-build/bionic_translation/builddir/libc_bio.so.0
B=/usr/lib/aarch64-linux-gnu/libbsd.so.0
echo "=== libc_bio 未定义符号 ==="
nm -D --undefined-only $F | awk '{print $2}' | sort -u > /tmp/undef.txt
wc -l /tmp/undef.txt
echo "=== 其中 libbsd 提供的 ==="
nm -D --defined-only $B 2>/dev/null | awk '{print $3}' | sort -u > /tmp/bsdsyms.txt
comm -12 /tmp/undef.txt /tmp/bsdsyms.txt
