echo "=== /usr/local/lib 下 bio ==="
ls -l /usr/local/lib/lib*_bio.so* 2>/dev/null
echo "=== /usr/local/lib/aarch64-linux-gnu 下 bio ==="
ls -l /usr/local/lib/aarch64-linux-gnu/lib*_bio.so* 2>/dev/null
echo "=== 谁定义 _ULaarch64_set_iterate_phdr_function ==="
for d in /usr/local/lib /usr/local/lib/aarch64-linux-gnu; do
  for f in $d/lib*_bio*.so*; do
    [ -f "$f" ] || continue
    r=$(nm -D "$f" 2>/dev/null | grep "aarch64_set_iterate_phdr" | head -2)
    [ -n "$r" ] && echo "$f:" && echo "$r"
  done
done
echo "=== libdl.so 指向 ==="
ls -l /usr/local/lib/libdl.so /usr/local/lib/aarch64-linux-gnu/libdl.so 2>/dev/null
