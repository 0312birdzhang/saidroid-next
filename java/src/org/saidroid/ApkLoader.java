package org.saidroid;

import java.io.*;
import java.util.*;
import java.util.jar.*;
import java.util.zip.*;

/**
 * APK 加载器：从 .apk 直接到可启动状态。
 *
 * 流程：
 *   1. 读 AndroidManifest.xml（AXML）→ package + launcher activity
 *   2. 提取所有 classes*.dex
 *   3. 用 DexConverter 转成 JVM 字节码
 *   4. 组装 classpath（转换产物 + framework）
 */
public class ApkLoader {

    public static class ApkInfo {
        public String path;
        public String packageName;
        public String launcherActivity;
        public String versionName;
        public int versionCode;
        public List<String> dexFiles = new ArrayList<>();
        public List<String> nativeLibs = new ArrayList<>();
        public File outputJar;
        public String toString() {
            return "APK[" + packageName + "] launcher=" + launcherActivity
                 + " dex=" + dexFiles.size() + " so=" + nativeLibs.size();
        }
    }

    /** 解析 APK 元信息 */
    public static ApkInfo inspect(File apk) throws IOException {
        ApkInfo info = new ApkInfo();
        info.path = apk.getAbsolutePath();

        try (ZipFile zf = new ZipFile(apk)) {
            // 1. Manifest
            ZipEntry me = zf.getEntry("AndroidManifest.xml");
            if (me == null) throw new IOException("no AndroidManifest.xml");
            byte[] mbytes = readAll(zf.getInputStream(me));
            AxmlReader.Result mr = new AxmlReader(mbytes).parse();
            info.packageName = mr.packageName;
            info.launcherActivity = mr.launcherActivity;
            info.versionName = mr.versionName;
            info.versionCode = mr.versionCode;

            // 2. dex 文件
            Enumeration<? extends ZipEntry> en = zf.entries();
            while (en.hasMoreElements()) {
                ZipEntry e = en.nextElement();
                String n = e.getName();
                if (n.startsWith("classes") && n.endsWith(".dex")) info.dexFiles.add(n);
                else if (n.startsWith("lib/arm64-v8a/") && n.endsWith(".so")) info.nativeLibs.add(n);
            }
            Collections.sort(info.dexFiles);
        }
        return info;
    }

    /** 转换 APK 的所有 dex 到 jar */
    public static File convertDex(File apk, File outJar, File workDir) throws Exception {
        ApkInfo info = inspect(apk);
        System.out.println("ApkLoader=inspect|" + info);

        workDir.mkdirs();
        Map<String, byte[]> allClasses = new LinkedHashMap<>();

        try (ZipFile zf = new ZipFile(apk)) {
            for (String dexName : info.dexFiles) {
                ZipEntry de = zf.getEntry(dexName);
                if (de == null) continue;
                byte[] dexBytes = readAll(zf.getInputStream(de));
                System.out.println("ApkLoader=dex|" + dexName + "|" + dexBytes.length + " bytes");

                long t0 = System.currentTimeMillis();
                Map<String, byte[]> classes =
                    com.macapk.dex.DexConverter.convert(dexBytes);
                long t1 = System.currentTimeMillis();
                System.out.println("ApkLoader=converted|" + classes.size()
                    + " classes|" + (t1 - t0) + "ms");
                allClasses.putAll(classes);
            }
        }

        // 写 jar
        try (JarOutputStream jos = new JarOutputStream(new FileOutputStream(outJar))) {
            for (Map.Entry<String, byte[]> e : allClasses.entrySet()) {
                String name = e.getKey().replace('.', '/') + ".class";
                jos.putNextEntry(new JarEntry(name));
                jos.write(e.getValue());
                jos.closeEntry();
            }
        }
        System.out.println("ApkLoader=jar|" + outJar.getAbsolutePath()
            + "|" + allClasses.size() + " classes|" + outJar.length() + " bytes");
        return outJar;
    }

    /** 提取 native 库到目录 */
    public static int extractNativeLibs(File apk, File libDir) throws IOException {
        libDir.mkdirs();
        int n = 0;
        try (ZipFile zf = new ZipFile(apk)) {
            Enumeration<? extends ZipEntry> en = zf.entries();
            while (en.hasMoreElements()) {
                ZipEntry e = en.nextElement();
                String name = e.getName();
                if (!name.startsWith("lib/arm64-v8a/") || !name.endsWith(".so")) continue;
                File out = new File(libDir, new File(name).getName());
                try (InputStream is = zf.getInputStream(e);
                     FileOutputStream fos = new FileOutputStream(out)) {
                    copy(is, fos);
                }
                n++;
            }
        }
        System.out.println("ApkLoader=native_libs|" + n + " extracted to " + libDir);
        return n;
    }

    private static byte[] readAll(InputStream is) throws IOException {
        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        copy(is, bos);
        return bos.toByteArray();
    }

    private static void copy(InputStream is, OutputStream os) throws IOException {
        byte[] buf = new byte[65536];
        int n;
        while ((n = is.read(buf)) > 0) os.write(buf, 0, n);
    }

    /** 命令行入口 */
    public static void main(String[] args) throws Exception {
        if (args.length < 1) {
            System.err.println("usage: ApkLoader <app.apk> [out.jar] [libdir]");
            System.exit(2);
        }
        File apk = new File(args[0]);
        if (!apk.exists()) { System.err.println("not found: " + apk); System.exit(2); }

        ApkInfo info = inspect(apk);
        System.out.println("APK=info|" + info);
        System.out.println("APK=package|" + info.packageName);
        System.out.println("APK=launcher|" + info.launcherActivity);
        System.out.println("APK=version|" + info.versionName + "(" + info.versionCode + ")");

        if (args.length >= 2) {
            File outJar = new File(args[1]);
            convertDex(apk, outJar, new File(outJar.getParentFile(), "work"));
        }
        if (args.length >= 3) {
            extractNativeLibs(apk, new File(args[2]));
        }
        System.out.println("APK=OK");
    }
}
