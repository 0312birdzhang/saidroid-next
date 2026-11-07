A=/tmp/art-build/art-standalone/art/runtime
echo "=== 所有 .compare( 调用 ==="
grep -rn "\.compare(" $A --include=*.cc --include=*.h | head -20
echo
echo "=== 含 size() - 的 compare/substr ==="
grep -rn "compare(.*size() *-\|substr(size() *-" $A --include=*.cc | head -10
