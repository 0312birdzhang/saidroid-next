echo "=== which java is ResProbe2 ==="
grep -ln "class ResProbe2" /tmp/*.java /tmp/*/*.java 2>/dev/null
echo "=== content ==="
f=$(grep -ln "class ResProbe2" /tmp/*.java /tmp/*/*.java 2>/dev/null | head -1)
echo "file=$f"
[ -n "$f" ] && cat "$f"
echo "=== run scripts mentioning ResProbe2 ==="
grep -ln "ResProbe2" /tmp/*.sh 2>/dev/null | head
