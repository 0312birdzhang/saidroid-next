#!/bin/bash
set -u
JAVA=/tmp/jdkfull/jdk-21.0.13+9/bin
W=/tmp/ap
for spec in "android.os.storage.IMountService:SdMountService" "android.os.IServiceManager:SdServiceManagerStub"; do
  iface=${spec%%:*}; cls=${spec##*:}
  python3 /media/psf/Home/WorkSpace/saidroid-next/scripts/debug/genstub.py \
    --javap $JAVA/javap --cp /tmp/fw23/cls --iface $iface --class $cls \
    --out $W/$cls.java 2>&1 | tail -1
done
echo "=== IServiceManager 方法 ==="
$JAVA/javap -p -classpath /tmp/fw23/cls android.os.IServiceManager 2>/dev/null | grep abstract | sed 's/ throws android.os.RemoteException//'
echo "=== IMountService 里和卷/存储状态相关的 ==="
grep -n "getVolumeList\|getVolumeState\|isExternalStorageEmulated\|getEncrypt" $W/SdMountService.java | head -6
