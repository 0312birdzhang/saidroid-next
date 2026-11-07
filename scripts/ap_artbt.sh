L=/tmp/ap/run.log
echo "=== ART 自己打的 Backtrace 段 ==="
awk '/^Backtrace:/{p=1} p' $L | head -30
echo "=== 或 A/ 行 ==="
grep -a "^A/\|^  #" $L | tail -30
