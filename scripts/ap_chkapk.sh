A=/tmp/art-build/art-standalone/out/host/linux-x86/framework/framework-res.apk
echo "=== apk 基本信息 ==="
ls -l $A
unzip -l $A 2>/dev/null | head -8
echo "=== resources.arsc 是否在 ==="
unzip -l $A 2>/dev/null | grep -c "resources.arsc"
echo "=== 有没有 ALOG 之类的输出（run.log 里非 AP/SDBRIDGE 行）==="
grep -av "AP\[\|SDBRIDGE\|^ *x[0-9]\|^OS:\|^Cmdline\|^Thread\|^Registers\|^ *sp:\|^ pstate\|^\*\*\*\|^Fatal\|^Backtrace" /tmp/ap/run.log | head -20
