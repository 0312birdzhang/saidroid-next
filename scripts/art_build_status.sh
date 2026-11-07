L=/tmp/art-rebuild.log
echo "=== 错误数: $(grep -ac 'error:' $L 2>/dev/null || echo 0) ==="
echo "=== 运行中? ==="
pgrep -f "make -j4" >/dev/null && echo RUNNING || echo DONE
echo "=== 尾部 ==="
tail -6 $L 2>/dev/null
