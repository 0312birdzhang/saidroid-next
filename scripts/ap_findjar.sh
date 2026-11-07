echo "=== VM 上找 android-all ==="
find /tmp /root /home -maxdepth 4 -name "android-all*.jar" 2>/dev/null | head -5
echo "=== multi.jar 里有 class 吗 ==="
unzip -l /tmp/fw23/multi.jar 2>/dev/null | grep -c "\.class"
unzip -l /tmp/fw23/multi.jar 2>/dev/null | grep "android/os/Build" | head -3
echo "=== 名字里带 Build 的条目 ==="
unzip -l /tmp/fw23/multi.jar 2>/dev/null | awk '{print $4}' | grep -c "^android/"
