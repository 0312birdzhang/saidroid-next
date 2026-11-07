#!/bin/bash
# VM 侧：编译并运行 TLS 网络探针（决定 -329 的真正原因）。
# 在 Parallels VM 里按路径执行：
#   /bin/bash /media/psf/Home/WorkSpace/saidroid-next/scripts/tls/run-tls-probe.sh
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
H=root@bonito
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 $H"
SCP="sshpass -e scp -o StrictHostKeyChecking=no -o ConnectTimeout=8"
REPO=/media/psf/Home/WorkSpace/saidroid-next
JDK=/tmp/jdkfull/jdk-21.0.13+9
export JAVA_HOME=$JDK
export PATH=$JDK/bin:$PATH
OUT=/home/art/test

ech() { echo "=== $* ==="; }

ech "1. 定位 d8 / android.jar"
INPUTS=$REPO/build/codex-api29/inputs
D8=$INPUTS/r8-8.3.37.jar
if [ ! -f "$D8" ]; then echo "FAIL=no_r8_jar|$D8"; exit 1; fi
echo "D8=$D8"
ANDROIDJAR=$INPUTS/android-all-10-robolectric-5803371.jar
if [ ! -f "$ANDROIDJAR" ]; then echo "FAIL=no_android_jar|$ANDROIDJAR"; exit 1; fi
echo "ANDROIDJAR=$ANDROIDJAR"

ech "2. javac"
W=/tmp/tlsprobe
rm -rf $W && mkdir -p $W/cls
cp "$REPO/scripts/device/TlsNetProbe.java" $W/
javac --release 8 -nowarn -d $W/cls $W/TlsNetProbe.java 2>&1 | head -20
if [ ! -f $W/cls/TlsNetProbe.class ]; then echo "FAIL=javac"; exit 1; fi
echo "JAVAC_OK"

ech "3. d8 -> classes.dex"
mkdir -p $W/dex
java -Xmx2g -cp "$D8" com.android.tools.r8.D8 --release --min-api 29 --lib "$ANDROIDJAR" --output $W/dex $W/cls/TlsNetProbe.class 2>&1 | head -10
if [ ! -f $W/dex/classes.dex ]; then echo "FAIL=d8"; exit 1; fi
ls -l $W/dex/classes.dex
(cd $W/dex && zip -q $W/probe.jar classes.dex)
ls -l $W/probe.jar

if [ "${COMPILE_ONLY:-0}" = "1" ]; then echo "COMPILE_ONLY_OK"; exit 0; fi

ech "4. 推设备"
$SSH "mkdir -p $OUT"
$SCP -q $W/probe.jar "$H:$OUT/tlsprobe.jar"
$SCP -q "$REPO/scripts/tls/tls-probe-run.py" "$H:$OUT/tls-probe-run.py"
$SSH "chmod 644 $OUT/tlsprobe.jar; chmod 755 $OUT/tls-probe-run.py"

ech "5. 跑探针（wolfjsse.debug 打开）"
$SSH "python3 $OUT/tls-probe-run.py TlsNetProbe $OUT/tlsprobe.jar -Dwolfjsse.debug=true" 2>&1 | tee /tmp/tls-probe.out
echo "=== 结果摘要 ==="
grep -E "TLSPROBE=(env|path|android_ca_store|private_store|tmf|tm_roots|tm\||handshake)" /tmp/tls-probe.out | head -60
