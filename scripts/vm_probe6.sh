BASE=/tmp/art-build/art-standalone/out/host/linux-x86
echo "=== framework jar built for ART ==="
ls -lh /tmp/fw23/*.jar /tmp/fw23/*/*.jar 2>/dev/null | head
find /tmp -maxdepth 3 -name "*hostdex*.jar" -o -maxdepth 3 -name "android-all*.jar" 2>/dev/null | head
echo "=== boot classpath dir ==="
ls -lh $BASE/framework 2>/dev/null | head -12
echo "=== apks ==="
find /tmp -maxdepth 3 -name "*.apk" 2>/dev/null | head -10
echo "=== dx ==="
ls -l $BASE/bin/dx
echo "=== art-data ==="
ls /tmp/art-data 2>/dev/null
echo "=== art env script on VM ==="
ls /tmp/*.sh | xargs grep -ln "dalvikvm" 2>/dev/null | head -8
