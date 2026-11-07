#!/bin/bash
# 用 Android 5.1.1 的框架类重建 boot classpath（与真机 native 库的 ABI 对齐）
set -u
JAVA=/tmp/jdkfull/jdk-21.0.13+9/bin
DXJAR=/tmp/art-build/art-standalone/out/host/linux-x86/framework/dx.jar
BASE=/tmp/art-build/art-standalone/out/host/linux-x86
W=/tmp/fw51
VER=5.1.1_r9-robolectric-r2
J=$W/android-all-$VER.jar
mkdir -p $W
if [ ! -f "$J" ] || [ $(stat -c%s "$J") -lt 10000000 ]; then
  echo "=== 下载 $VER ==="
  curl -sSL -o "$J" "https://repo1.maven.org/maven2/org/robolectric/android-all/$VER/android-all-$VER.jar"
  ls -lh "$J"
fi
n=$(unzip -l "$J" 2>/dev/null | grep -c "\.class")
echo "jar 内 class 数 = $n"
[ "$n" -lt 1000 ] && { echo "下载不完整，退出"; exit 1; }

echo "=== 抽取 android/** 与 com/android/** ==="
rm -rf $W/cls && mkdir -p $W/cls/raw
unzip -q -o "$J" 'android/*' 'com/android/*' -d $W/cls/raw 2>/dev/null
find $W/cls/raw -name "*.class" > $W/list.txt
cnt=$(wc -l < $W/list.txt)
echo "class 文件数 = $cnt"
# 只保留 .class，其余资源不要
mkdir -p $W/cls/all
while read -r f; do
  rel=${f#$W/cls/raw/}
  mkdir -p "$W/cls/all/$(dirname "$rel")"
  cp "$f" "$W/cls/all/$rel"
done < $W/list.txt
echo "整理后: $(find $W/cls/all -name '*.class' | wc -l) 个"

echo "=== dx multi-dex ==="
cp -f /tmp/fw23/maindex.txt $W/maindex.txt 2>/dev/null
rm -f $W/multi.jar
$JAVA/java -Xmx6g -cp $DXJAR com.android.dx.command.Main --dex --multi-dex --min-sdk-version=22 \
  --main-dex-list=$W/maindex.txt --minimal-main-dex --output=$W/multi.jar $W/cls/all 2>&1 | tail -3
unzip -l $W/multi.jar | grep -E "classes[0-9]*\.dex"

echo "=== 拆 jar ==="
rm -rf $W/jars && mkdir -p $W/jars
unzip -o -q $W/multi.jar "classes*.dex" -d $W/jars
cd $W/jars
i=1
for f in $(ls classes*.dex | sort -V); do
  if [ "$i" = "1" ]; then name=framework-hostdex.jar; else name=framework$i-hostdex.jar; fi
  rm -rf tmp && mkdir tmp && cp $f tmp/classes.dex
  (cd tmp && zip -q -r ../$name classes.dex)
  i=$((i+1))
done
ls -lh $W/jars/*.jar

echo "=== 备份旧 jar 并安装 5.1.1 ==="
mkdir -p /tmp/fw-backup-m
for f in $BASE/java/dex/art/framework*-hostdex.jar; do cp -f "$f" /tmp/fw-backup-m/ 2>/dev/null; done
for f in $W/jars/*.jar; do cp -f "$f" $BASE/java/dex/art/; done
rm -rf /.cache/art /tmp/art-data/.cache 2>/dev/null
ls -lh $BASE/java/dex/art/framework*hostdex.jar
echo "done"
