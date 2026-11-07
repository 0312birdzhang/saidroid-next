cd /tmp/shimtest
echo "=== 统计 TLS 重定位类型（按库）==="
for f in libandroid_runtime.so libhwui.so libc++.so libgui.so libutils.so libbinder.so libandroidfw.so libskia.so libcutils.so libnativehelper.so; do
  [ -f "$f" ] || continue
  printf "%-24s " "$f"
  readelf -rW "$f" 2>/dev/null | awk '/TLS/ {print $3}' | sort | uniq -c | tr '\n' ' '
  echo
done
echo "=== 全部库中含 TLS_TPREL 的 ==="
for f in *.so; do
  n=$(readelf -rW "$f" 2>/dev/null | grep -c TPOFF\|TPREL)
  [ "$n" -gt 0 ] 2>/dev/null && echo "$f: $n"
done 2>/dev/null | head -20
