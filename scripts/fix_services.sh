#!/bin/bash
set -u
python3 - <<'PY'
import re

# ---- 1) SdMountService: 给出一块可用的外部存储 ----
p = '/tmp/ap/SdMountService.java'
src = open(p).read()

STORE = '/home/art/storage/sdcard0'

helpers = '''
    /* 单用户、单卷世界：给 QQ 一块可写的外部存储 */
    public static final String EXTERNAL_PATH = "%s";

    private static android.os.storage.StorageVolume volume() {
        java.io.File f = new java.io.File(EXTERNAL_PATH);
        return new android.os.storage.StorageVolume(
                EXTERNAL_PATH, 0, f, "SaiDroid storage",
                true,    /* primary */
                false,   /* removable */
                true,    /* emulated */
                0,       /* mtpReserveSize */
                false,   /* allowMassStorage */
                0,       /* maxFileSize */
                android.os.Process.myUserHandle(),
                null,    /* fsUuid */
                "mounted");
    }
''' % STORE

idx = src.index('{', src.index('public class SdMountService')) + 1
src = src[:idx] + helpers + src[idx:]

def repl(src, ret, name, params, body):
    head = '    @Override\n    public %s %s(%s) {\n' % (ret, name, params)
    assert head in src, '没找到: %s %s(%s)' % (ret, name, params)
    i = src.index(head)
    j = src.index('\n    }\n', i)
    return src[:i] + head + body + '\n    }\n' + src[j + len('\n    }\n'):]

src = repl(src, 'android.os.storage.StorageVolume[]', 'getVolumeList',
           'int arg0, java.lang.String arg1, int arg2',
           '        return new android.os.storage.StorageVolume[]{ volume() };')
src = repl(src, 'java.lang.String', 'getVolumeState', 'java.lang.String arg0',
           '        return "mounted";')
src = repl(src, 'boolean', 'isExternalStorageEmulated', '', '        return true;')
src = repl(src, 'int', 'getEncryptionState', '', '        return 1; /* ENCRYPTION_STATE_NONE */')
open(p, 'w').write(src)
print('SdMountService: 卷/状态已实现')

# ---- 2) SdServiceManagerStub: 名字到本地 binder 的映射 ----
p2 = '/tmp/ap/SdServiceManagerStub.java'
s2 = open(p2).read()

# IServiceManager 的 AIDL 生成类（Stub/Proxy）不在这套框架 jar 里，只有接口本体，
# 所以直接继承 Binder 实现接口即可。
s2 = s2.replace('public class SdServiceManagerStub extends android.os.IServiceManager.Stub {',
                'public class SdServiceManagerStub extends android.os.Binder\n'
                '        implements android.os.IServiceManager {', 1)

h2 = '''
    /* 进程内的服务表：名字 -> 本地 binder。没有的返回 null，
     * 这样框架不会去碰 /dev/binder（没有 servicemanager 时会直接 abort）。 */
    private static final java.util.HashMap<String, android.os.IBinder> MAP =
            new java.util.HashMap<String, android.os.IBinder>();

    public static void put(String name, android.os.IBinder b) {
        MAP.put(name, b);
    }
'''
idx2 = s2.index('{', s2.index('public class SdServiceManagerStub')) + 1
s2 = s2[:idx2] + h2 + s2[idx2:]

def repl2(src, ret, name, params, body):
    head = '    @Override\n    public %s %s(%s) {\n' % (ret, name, params)
    assert head in src, '没找到: %s %s(%s)' % (ret, name, params)
    i = src.index(head)
    j = src.index('\n    }\n', i)
    return src[:i] + head + body + '\n    }\n' + src[j + len('\n    }\n'):]

s2 = repl2(s2, 'android.os.IBinder', 'getService', 'java.lang.String arg0',
           '        return MAP.get(arg0);')
s2 = repl2(s2, 'android.os.IBinder', 'checkService', 'java.lang.String arg0',
           '        return MAP.get(arg0);')
s2 = repl2(s2, 'void', 'addService',
           'java.lang.String arg0, android.os.IBinder arg1, boolean arg2',
           '        MAP.put(arg0, arg1);')
s2 = repl2(s2, 'java.lang.String[]', 'listServices', '',
           '        return MAP.keySet().toArray(new String[0]);')
open(p2, 'w').write(s2)
print('SdServiceManagerStub: 服务表已实现')
PY
