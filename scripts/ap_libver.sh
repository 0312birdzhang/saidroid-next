echo "=== 镜像里抽出的 libandroid_runtime ==="
ls -l /tmp/and23/libs/lib64/libandroid_runtime.so /tmp/and23/bio2/libandroid_runtime.so /tmp/shimtest/libandroid_runtime.so 2>/dev/null
echo "=== md5 对比 ==="
md5sum /tmp/and23/libs/lib64/libandroid_runtime.so /tmp/and23/bio2/libandroid_runtime.so /tmp/shimtest/libandroid_runtime.so 2>/dev/null
echo "=== 是否含 AssetManager::CacheMode 构造 ==="
for f in /tmp/and23/libs/lib64/libandroid_runtime.so /tmp/shimtest/libandroid_runtime.so; do
  printf "%s : " "$f"
  nm -D --defined-only "$f" 2>/dev/null | grep -c "AssetManagerC1ENS0_9CacheModeE"
done
echo "=== libandroidfw 里的同名检查 ==="
for f in /tmp/and23/libs/lib64/libandroidfw.so /tmp/shimtest/libandroidfw.so; do
  printf "%s : " "$f"
  nm -D --defined-only "$f" 2>/dev/null | grep -c "CacheModeE"
done
