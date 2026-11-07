#!/bin/bash
set -u
JAVA=/tmp/jdkfull/jdk-21.0.13+9/bin
W=/tmp/ap
python3 /media/psf/Home/WorkSpace/saidroid-next/scripts/debug/genstub.py \
  --javap $JAVA/javap --cp /tmp/fw23/cls \
  --iface android.content.pm.IPackageManager --class SdPackageManagerService \
  --out $W/SdPackageManagerService.java \
  --comment "单包世界：只有 com.tencent.mobileqq 这一个包，其余按默认值返回" 2>&1 | tail -2
wc -l $W/SdPackageManagerService.java
echo "=== QQ 早期会用到的几个方法签名 ==="
grep -n "public android.content.pm.PackageInfo getPackageInfo\|public android.content.pm.ApplicationInfo getApplicationInfo\|public int getPackageUid\|public int checkPermission\|public java.util.List<android.content.pm.ResolveInfo> queryIntentActivities\|public java.util.List<android.content.pm.ApplicationInfo> getInstalledApplications\|public android.content.pm.ActivityInfo getActivityInfo" $W/SdPackageManagerService.java | head -10
