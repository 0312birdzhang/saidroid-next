#!/bin/bash
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=15"
H=root@bonito
JAVA=/tmp/jdkfull/jdk-21.0.13+9/bin
DXJAR=/tmp/art-build/art-standalone/out/host/linux-x86/framework/dx.jar
W=/tmp/fw23
echo "=== 1. 重新 dx 打包（multi-dex）==="
cd $W
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
echo "=== 3. 推送并清 boot image 缓存 ==="
for f in $W/jars/*.jar; do
  $SSH $H "cat > /home/art/java/dex/art/$(basename $f)" < $f
done
$SSH $H 'ls -lh /home/art/java/dex/art/framework*'
$SSH $H 'rm -rf /home/art/data/.cache /root/.cache/art; echo cache-cleared'
