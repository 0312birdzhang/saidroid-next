A=/tmp/art-build/art-standalone
echo "=== 谁打印 known location ==="
grep -rn "is in boot class path but is not in a known location" $A/art/runtime/ | head -3
echo "=== 该文件里 compare/substr 用法 ==="
f=$(grep -rl "is in boot class path but is not in a known location" $A/art/runtime/ | head -1)
echo "file=$f"
grep -n "compare\|substr\|\.size() -\|size()-" "$f" | head -20
