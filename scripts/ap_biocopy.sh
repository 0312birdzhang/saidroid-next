echo "=== /tmp/shimtest 里的 bio 库 ==="
ls -l /tmp/shimtest/lib*_bio.so* 2>/dev/null | head -12
echo "=== /tmp/shimtest 里 libc.so ==="
ls -l /tmp/shimtest/libc.so 2>/dev/null
echo "=== 大小对比（/usr/local/lib vs shimtest）==="
ls -l /usr/local/lib/libc_bio.so.0 /tmp/shimtest/libc_bio.so.0 2>/dev/null
