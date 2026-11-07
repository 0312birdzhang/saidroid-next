echo "=== whoami/kernel ==="
id; uname -m; uptime | tr -s ' '
echo "=== art build ==="
ls -d /tmp/art-build/art-standalone 2>/dev/null
ls /tmp/art-build/art-standalone/out/host/linux-x86/bin 2>/dev/null | head
echo "=== bionic out ==="
find /tmp -maxdepth 3 -name "libc_bio.so*" 2>/dev/null | head
find /tmp -maxdepth 3 -name "libdl_bio.so*" 2>/dev/null | head
echo "=== gdb ==="
which gdb; gdb --version 2>/dev/null | head -1
echo "=== ninja/meson ==="
which meson ninja cc gcc
