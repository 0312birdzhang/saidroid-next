#!/bin/bash
set -u
J=/tmp/fw51/android-all-5.1.1_r1-robolectric-r1.jar
mkdir -p /tmp/fw51
if [ -f "$J" ] && [ $(stat -c%s "$J") -gt 10000000 ]; then
  echo "已存在: $(ls -lh $J | awk '{print $5}')"
else
  echo "=== 下载 android-all 5.1.1_r1 (Maven Central) ==="
  curl -sSL -o "$J" https://repo1.maven.org/maven2/org/robolectric/android-all/5.1.1_r1-robolectric-r1/android-all-5.1.1_r1-robolectric-r1.jar
  ls -lh "$J"
fi
echo "=== jar 里 class 数 ==="
unzip -l "$J" 2>/dev/null | grep -c "\.class"
echo "=== 抽查关键类是否在 ==="
unzip -l "$J" 2>/dev/null | grep -E "android/os/Parcel.class|android/os/Binder.class|android/app/ActivityThread.class|android/graphics/Canvas.class" | head -5
