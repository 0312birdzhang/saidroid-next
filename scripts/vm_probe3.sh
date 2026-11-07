echo "=== shimtest ==="
ls /tmp/shimtest | head -5; ls /tmp/shimtest | wc -l
echo "=== nohwui ==="
ls /tmp/nohwui | wc -l
echo "=== build dirs of bionic_translation ==="
find /tmp -maxdepth 4 -name "build.ninja" -path "*bionic*" 2>/dev/null | head
find /tmp -maxdepth 3 -name "build.ninja" 2>/dev/null | head -20
echo "=== shim presence ==="
for d in /tmp/shimtest /tmp/nohwui /tmp/and23/bio2 /tmp/and23/biolibs; do
  printf "%s: " "$d"; ls "$d"/libhwui* 2>/dev/null | tr '\n' ' '; echo
done
echo "=== libandroid_runtime real ==="
ls -lh /tmp/and23/libs/libandroid_runtime.so 2>/dev/null
find /tmp/and23 -name libandroid_runtime.so | head
