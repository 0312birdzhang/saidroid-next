echo "=== 镜像 build.prop 关键项 ==="
grep -E "ro.build.version.sdk|ro.product.cpu.abilist|ro.product.cpu.abi|ro.build.fingerprint|ro.product.model|ro.sf.lcd_density|ro.build.version.release|ro.build.version.codename" /tmp/and23/arm64-v8a/build.prop 2>/dev/null | head -20
echo "=== build.prop 总行数 ==="
wc -l /tmp/and23/arm64-v8a/build.prop 2>/dev/null
echo "=== libc_bio 当前导出的 property 符号 ==="
nm -D --defined-only /tmp/shimtest/libc_bio.so.0 2>/dev/null | grep -E "system_property" | head -20
echo "=== 框架 jar 是哪个 API：有没有 ResourcesImpl / LocaleList ==="
unzip -l /tmp/fw23/jars/framework2-hostdex.jar 2>/dev/null | grep -c "ResourcesImpl"
for j in /tmp/fw23/jars/framework*.jar; do printf "%s: " $(basename $j); unzip -l $j 2>/dev/null | grep -c "LocaleList.class"; done
