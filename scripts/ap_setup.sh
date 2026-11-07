#!/bin/bash
# VM 侧：把 AssetProbe 编译成 dex，并构出 libsdbridge.so
set -u
BASE=/tmp/art-build/art-standalone/out/host/linux-x86
export JAVA_HOME=/tmp/jdkfull/jdk-21.0.13+9
export PATH=$JAVA_HOME/bin:$PATH
W=/tmp/ap
rm -rf $W; mkdir -p $W/cls

echo "=== 1. framework 宿主 dex 放进 boot classpath 目录 ==="
mkdir -p $BASE/framework
for j in framework-hostdex.jar framework2-hostdex.jar framework3-hostdex.jar framework4-hostdex.jar; do
  cp -f /tmp/fw23/jars/$j $BASE/framework/ 2>/dev/null && echo "  $j ok"
done

echo "=== 2. javac ==="
cp /media/psf/Home/WorkSpace/saidroid-next/scripts/device/SdBridge.java $W/
cp /media/psf/Home/WorkSpace/saidroid-next/scripts/device/AssetProbe.java $W/
cp /media/psf/Home/WorkSpace/saidroid-next/scripts/device/ContextProbe.java $W/
cp /media/psf/Home/WorkSpace/saidroid-next/scripts/device/DumpMembers.java $W/
cp /media/psf/Home/WorkSpace/saidroid-next/scripts/device/ViewProbe.java $W/
cp /media/psf/Home/WorkSpace/saidroid-next/scripts/device/SdDisplayShim.java $W/
cp /media/psf/Home/WorkSpace/saidroid-next/scripts/device/SdServices.java $W/
cp /media/psf/Home/WorkSpace/saidroid-next/scripts/device/SdActivityManagerService.java $W/
cp /media/psf/Home/WorkSpace/saidroid-next/scripts/device/ActivityManagerProbe.java $W/
cp /media/psf/Home/WorkSpace/saidroid-next/scripts/device/RuntimePrerequisitesProbe.java $W/
cp /media/psf/Home/WorkSpace/saidroid-next/scripts/device/PackageManagerProbe.java $W/
cp /media/psf/Home/WorkSpace/saidroid-next/scripts/device/SchedulingProbe.java $W/
cp /media/psf/Home/WorkSpace/saidroid-next/scripts/device/SdAppPermissions.java $W/
cp /media/psf/Home/WorkSpace/saidroid-next/scripts/device/SdActivityHost.java $W/
cp /media/psf/Home/WorkSpace/saidroid-next/scripts/device/BroadcastProbe.java $W/
cp /media/psf/Home/WorkSpace/saidroid-next/scripts/device/SQLiteProbe.java $W/
cp /media/psf/Home/WorkSpace/saidroid-next/scripts/device/ApkManifestProbe.java $W/
cp /media/psf/Home/WorkSpace/saidroid-next/scripts/device/TlsTrustProbe.java $W/
cp /media/psf/Home/WorkSpace/saidroid-next/scripts/device/FrameworkResourcesProbe.java $W/
cp /media/psf/Home/WorkSpace/saidroid-next/scripts/device/FontRuntimeProbe.java $W/
cp /media/psf/Home/WorkSpace/saidroid-next/scripts/device/TouchProbe.java $W/
cp /media/psf/Home/WorkSpace/saidroid-next/scripts/device/LiveProbe.java $W/
cp /media/psf/Home/WorkSpace/saidroid-next/scripts/device/QQProbe.java $W/
python3 /media/psf/Home/WorkSpace/saidroid-next/scripts/debug/genstub.py \
  --javap $JAVA_HOME/bin/javap --cp /tmp/fw23/cls \
  --iface android.view.IWindowManager --class SdWindowManagerService \
  --out $W/SdWindowManagerService.java 2>&1 | tail -2
bash /media/psf/Home/WorkSpace/saidroid-next/scripts/fix_wms.sh
python3 /media/psf/Home/WorkSpace/saidroid-next/scripts/debug/genstub.py \
  --javap $JAVA_HOME/bin/javap --cp /tmp/fw23/cls \
  --iface android.content.pm.IPackageManager --class SdPackageManagerService \
  --out $W/SdPackageManagerService.java 2>&1 | tail -2
bash /media/psf/Home/WorkSpace/saidroid-next/scripts/fix_pms.sh
for spec in "android.os.storage.IMountService:SdMountService" "android.os.IServiceManager:SdServiceManagerStub"; do
  iface=${spec%%:*}; cls=${spec##*:}
  python3 /media/psf/Home/WorkSpace/saidroid-next/scripts/debug/genstub.py \
    --javap $JAVA_HOME/bin/javap --cp /tmp/fw23/cls --iface $iface --class $cls \
    --out $W/$cls.java 2>&1 | tail -1
done
bash /media/psf/Home/WorkSpace/saidroid-next/scripts/fix_services.sh
javac --release 8 -nowarn -d $W/cls $W/SdBridge.java $W/AssetProbe.java $W/ContextProbe.java $W/DumpMembers.java 2>&1 | grep -v "obsolete" | head -8
echo "  (ViewProbe 需要框架 jar 做 classpath)"
javac --release 8 -nowarn -cp $W/cls:/tmp/fw23/cls:/tmp/art-build/art-standalone/out/host/common/obj/JAVA_LIBRARIES/core-libart-hostdex_intermediates/classes -d $W/cls $W/SdDisplayShim.java $W/SdWindowManagerService.java $W/SdPackageManagerService.java $W/SdServices.java $W/SdActivityManagerService.java $W/SdAppPermissions.java $W/SdActivityHost.java $W/ActivityManagerProbe.java $W/RuntimePrerequisitesProbe.java $W/PackageManagerProbe.java $W/SchedulingProbe.java $W/BroadcastProbe.java $W/SQLiteProbe.java $W/ApkManifestProbe.java $W/TlsTrustProbe.java $W/FrameworkResourcesProbe.java $W/FontRuntimeProbe.java $W/SdMountService.java $W/SdServiceManagerStub.java $W/ViewProbe.java $W/TouchProbe.java $W/LiveProbe.java $W/QQProbe.java 2>&1 | grep -v "obsolete\|unchecked\|Recompile" | head -12
ls $W/cls

echo "=== 3. dx ==="
$BASE/bin/dx --dex --output=$W/ap.dex $W/cls 2>&1 | tail -5
ls -l $W/ap.dex

echo "=== 4. libsdbridge.so ==="
gcc -shared -fPIC -O2 -o $W/libsdbridge.so \
  /media/psf/Home/WorkSpace/saidroid-next/scripts/device/sdbridge.c \
  -I$JAVA_HOME/include -I$JAVA_HOME/include/linux -ldl 2>&1 | head -10
ls -l $W/libsdbridge.so
