#!/bin/bash
# 重新打 multi-dex 并同时更新 VM 与真机的 boot classpath
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=15 root@bonito"
JAVA=/tmp/jdkfull/jdk-21.0.13+9/bin
DXJAR=/tmp/art-build/art-standalone/out/host/linux-x86/framework/dx.jar
BASE=/tmp/art-build/art-standalone/out/host/linux-x86
W=/tmp/fw23

echo "=== 1. dx multi-dex ==="
cd $W || exit 1
rm -f multi.jar
$JAVA/java -Xmx6g -cp $DXJAR com.android.dx.command.Main --dex --multi-dex --min-sdk-version=23 \
  --main-dex-list=$W/maindex.txt --minimal-main-dex --output=$W/multi.jar $W/cls 2>&1 | tail -3
unzip -l $W/multi.jar | grep -E "classes[0-9]*\.dex"

echo "=== 2. 拆成 4 个 jar ==="
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

echo "=== 3. 更新 VM 侧 boot classpath ==="
for f in $W/jars/*.jar; do cp -f $f $BASE/java/dex/art/; done
ls -lh $BASE/java/dex/art/framework*hostdex.jar
rm -rf /.cache/art /tmp/art-data/.cache 2>/dev/null
echo "vm cache cleared"

echo "=== 4. 推送真机 ==="
for f in $W/jars/*.jar; do
  $SSH "cat > /home/art/java/dex/art/$(basename $f)" < $f
done
$SSH 'ls -lh /home/art/java/dex/art/framework*hostdex.jar; rm -rf /home/art/data/.cache /root/.cache/art; echo device-cache-cleared'
