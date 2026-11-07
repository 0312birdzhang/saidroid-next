#!/bin/bash
set -u
F=${ART_PROBE_WORKDIR:-/tmp/ap}/SdPackageManagerService.java
python3 - "$F" <<'PY'
import sys, re

p = sys.argv[1]
src = open(p).read()

def repl(ret, name, params, body):
    """把生成器产出的空实现替换成真实现"""
    global src
    head = '    @Override\n    public %s %s(%s) {\n' % (ret, name, params)
    assert head in src, '没找到方法头: %s %s(%s)' % (ret, name, params)
    i = src.index(head)
    j = src.index('\n    }\n', i)
    src = src[:i] + head + body + '\n    }\n' + src[j + len('\n    }\n'):]

# ---- 单包世界的常量与构造 ----
helpers = '''
    /* ---- 单包世界：只承认 com.tencent.mobileqq 这一个包 ---- */
    public static final String QQ_PACKAGE = SdApkPackage.NAME;
    public static final String QQ_APK = SdApkPackage.APK;
    public static final String QQ_NATIVE = SdApkPackage.NATIVE;
    public static final String QQ_DATA = SdApkPackage.DATA;
    public static final int QQ_UID = android.os.Process.myUid();
    public static final int QQ_VERSION_CODE = 15730;
    public static final String QQ_VERSION_NAME = "9.3.50";
    public static final String QQ_APP_CLASS = "com.tencent.common.app.QFixApplicationImplProxy";

    private static boolean knownPackage(String name) {
        return QQ_PACKAGE.equals(name) || "android".equals(name);
    }

    private static SdAppPermissions qqPermissions;
    private static synchronized int permissionResult(String permission, String name) {
        if (!QQ_PACKAGE.equals(name)) return android.content.pm.PackageManager.PERMISSION_DENIED;
        if (permission == null) throw new IllegalArgumentException("Permission name is required");
        try {
            if (qqPermissions == null) qqPermissions = new SdAppPermissions(QQ_APK, QQ_PACKAGE);
            return qqPermissions.holds(permission) ? android.content.pm.PackageManager.PERMISSION_GRANTED
                    : android.content.pm.PackageManager.PERMISSION_DENIED;
        } catch (Exception failure) {
            throw new IllegalStateException("Cannot read installed permission definitions", failure);
        }
    }

    private static android.content.pm.ApplicationInfo appInfo(String name) {
        if (QQ_PACKAGE.equals(name)) return qqAppInfo();
        if (!"android".equals(name)) return null;
        android.content.pm.ApplicationInfo ai = new android.content.pm.ApplicationInfo();
        ai.packageName = "android";
        ai.processName = "system";
        ai.name = ai.className = "android.app.Application";
        ai.sourceDir = ai.publicSourceDir = "/home/art/framework/framework-res.apk";
        ai.uid = android.os.Process.SYSTEM_UID;
        ai.targetSdkVersion = android.os.Build.VERSION.SDK_INT;
        ai.flags = android.content.pm.ApplicationInfo.FLAG_SYSTEM;
        ai.enabled = true;
        return ai;
    }

    private static android.content.pm.PackageInfo packageInfo(String name, int flags) {
        if (QQ_PACKAGE.equals(name)) return qqPkgInfo(flags);
        if (!"android".equals(name)) return null;
        android.content.pm.PackageInfo pi = new android.content.pm.PackageInfo();
        pi.packageName = "android";
        pi.applicationInfo = appInfo(name);
        pi.versionCode = android.os.Build.VERSION.SDK_INT;
        pi.versionName = android.os.Build.VERSION.RELEASE;
        return pi;
    }

    private static android.content.pm.ApplicationInfo qqAppInfo() {
        return SdApkPackage.applicationInfo();
    }

    private static android.content.pm.PackageInfo qqPkgInfo(int flags) {
        return SdApkPackage.packageInfo(flags);
    }

    private static android.content.pm.ActivityInfo qqActivityInfo(android.content.ComponentName cn) {
        return SdApkPackage.activityInfo(cn, 0);
    }
'''
# 插到类体开头
idx = src.index('{', src.index('public class SdPackageManagerService')) + 1
src = src[:idx] + helpers + src[idx:]

# ---- 关键方法 ----
repl('android.content.pm.PackageInfo', 'getPackageInfo',
     'java.lang.String arg0, int arg1, int arg2',
     '        return packageInfo(arg0, arg1);')

repl('android.content.pm.ApplicationInfo', 'getApplicationInfo',
     'java.lang.String arg0, int arg1, int arg2',
     '        return appInfo(arg0);')

repl('int', 'getPackageUid', 'java.lang.String arg0, int arg1',
     '        android.content.pm.ApplicationInfo ai = appInfo(arg0);\n'
     '        return ai == null ? -1 : ai.uid;')

repl('int', 'getPackageUidEtc', 'java.lang.String arg0, int arg1, int arg2',
     '        android.content.pm.ApplicationInfo ai = appInfo(arg0);\n'
     '        return ai == null ? -1 : ai.uid;')

repl('java.lang.String[]', 'getPackagesForUid', 'int arg0',
     '        if (arg0 == QQ_UID) return new String[]{ QQ_PACKAGE };\n'
     '        if (arg0 == android.os.Process.SYSTEM_UID) return new String[]{ "android" };\n'
     '        return null;')

repl('int[]', 'getPackageGids', 'java.lang.String arg0, int arg1',
     '        return new int[0];')

repl('int[]', 'getPackageGidsEtc', 'java.lang.String arg0, int arg1, int arg2',
     '        return new int[0];')

repl('int', 'checkPermission', 'java.lang.String arg0, java.lang.String arg1, int arg2',
     '        return permissionResult(arg0, arg1);')

repl('int', 'checkUidPermission', 'java.lang.String arg0, int arg1',
     '        return arg1 == QQ_UID ? permissionResult(arg0, QQ_PACKAGE)\n'
     '                : android.content.pm.PackageManager.PERMISSION_DENIED;')

repl('boolean', 'isPackageAvailable', 'java.lang.String arg0, int arg1',
     '        return knownPackage(arg0);')

repl('boolean', 'isPackageFrozen', 'java.lang.String arg0',
     '        return false;')

repl('boolean', 'hasSystemFeature', 'java.lang.String arg0',
     '        return false;')

repl('android.content.pm.FeatureInfo[]', 'getSystemAvailableFeatures', '',
     '        return new android.content.pm.FeatureInfo[0];')

repl('android.content.pm.ActivityInfo', 'getActivityInfo',
     'android.content.ComponentName arg0, int arg1, int arg2',
     '        return qqActivityInfo(arg0);')

repl('android.content.pm.ParceledListSlice', 'getInstalledPackages', 'int arg0, int arg1',
     '        java.util.ArrayList<android.content.pm.PackageInfo> l =\n'
     '                new java.util.ArrayList<android.content.pm.PackageInfo>();\n'
     '        l.add(qqPkgInfo(arg0));\n'
     '        l.add(packageInfo("android", arg0));\n'
     '        return new android.content.pm.ParceledListSlice(l);')

repl('android.content.pm.ParceledListSlice', 'getInstalledApplications', 'int arg0, int arg1',
     '        java.util.ArrayList<android.content.pm.ApplicationInfo> l =\n'
     '                new java.util.ArrayList<android.content.pm.ApplicationInfo>();\n'
     '        l.add(qqAppInfo());\n'
     '        l.add(appInfo("android"));\n'
     '        return new android.content.pm.ParceledListSlice(l);')

repl('java.util.List<android.content.pm.ApplicationInfo>', 'getPersistentApplications', 'int arg0',
     '        return new java.util.ArrayList<android.content.pm.ApplicationInfo>();')

repl('java.util.List<android.content.pm.ResolveInfo>', 'queryIntentActivities',
     'android.content.Intent arg0, java.lang.String arg1, int arg2, int arg3',
     '        return SdApkPackage.resolveActivities(arg0, arg1, arg2);')

repl('java.util.List<android.content.pm.ResolveInfo>', 'queryIntentServices',
     'android.content.Intent arg0, java.lang.String arg1, int arg2, int arg3',
     '        return new java.util.ArrayList<android.content.pm.ResolveInfo>();')

open(p, 'w').write(src)
print('SdPackageManagerService: 关键方法已实现')
PY
