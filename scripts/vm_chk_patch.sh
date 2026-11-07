BASE=/tmp/art-build/art-standalone/out/host/linux-x86
ls -l $BASE/lib64/libart.so $BASE/bin/dalvikvm $BASE/bin/dex2oat
echo "=== 补丁是否在 so 里（找新加的告警串）==="
strings $BASE/lib64/libart.so | grep -c "Short dex location"
echo "=== 谁定义 _ULaarch64_set_iterate_phdr_function ==="
grep -rn "set_iterate_phdr_function" /tmp/art-build/bionic_translation/ 2>/dev/null | head -5
