echo "=== parsed_options patch ==="
grep -n "framework-hostdex\|hostdex" /tmp/art-build/art-standalone/art/runtime/parsed_options.cc | head -20
echo "=== context around ==="
grep -n -B4 -A12 "framework-hostdex" /tmp/art-build/art-standalone/art/runtime/parsed_options.cc | head -40
echo "=== fw23 jars linked into base framework? ==="
ls -l /tmp/art-build/art-standalone/out/host/linux-x86/framework/*hostdex* 2>/dev/null | head
