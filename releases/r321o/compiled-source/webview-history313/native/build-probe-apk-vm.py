#!/usr/bin/env python3
"""Build the WebView regression APK (ordinary signed Android package).

Run inside the MeeGo Build VM:

    python3 scripts/perf/build-probe-apk-vm.py <tag>

Uses the same JDK / r8 / aapt / signing key as the existing product and probe
builds, all of which already live under /var/tmp in the VM.
"""
from pathlib import Path
import hashlib, os, subprocess, sys, zipfile

REPO = Path('/media/psf/Home/WorkSpace/saidroid-next')
INPUTS = REPO / 'build/codex-api29/inputs'
FRAMEWORK_JAR = INPUTS / 'android-all-10-robolectric-5803371.jar'
R8 = INPUTS / 'r8-8.3.37.jar'
JAVA = Path(os.environ.get('JAVA_HOME', '/tmp/jdkfull/jdk-21.0.13+9')) / 'bin'
AAPT_TOOL = Path('/var/tmp/saidroid-next-aapt-tools-20261025-r1/root')
SIGNING = Path('/var/tmp/saidroid-next-private-signing-20261025')
FRAMEWORK_APK = Path('/home/art/api29-root/system/framework/framework-res.apk')
PACKAGE = 'org.example.saildroid.webviewprobe'
ACTIVITY = 'WebViewProbeActivity'


def main():
    if len(sys.argv) not in (2,3):
        raise SystemExit('usage: build-probe-apk-vm.py <tag>')
    tag = sys.argv[1]
    activity=sys.argv[2] if len(sys.argv)==3 else ACTIVITY
    assert activity in ['WebViewProbeActivity','VerificationProbeActivity','ImeProbeActivity']
    out = Path('/var/tmp/saidroid-next-api29-webviewprobe-' + tag)
    assert str(out).startswith('/var/tmp/saidroid-next-'), 'keep outputs under /var/tmp'
    out.mkdir(parents=True, exist_ok=False)
    classes = out / 'classes'
    classes.mkdir()
    source = REPO / 'native/webview/qt-helper' / (activity + '.java')
    subprocess.run([str(JAVA / 'javac'), '--release', '8', '-nowarn', '-cp', str(FRAMEWORK_JAR),
                    '-d', str(classes), str(source)], check=True)
    subprocess.run([str(JAVA / 'java'), '-cp', str(R8), 'com.android.tools.r8.D8', '--release',
                    '--min-api', '29', '--lib', str(FRAMEWORK_JAR),
                    '--output', str(out / 'dex.jar'),
                    *[str(f) for f in sorted(classes.rglob('*.class'))]], check=True)
    manifest = (
        '<manifest xmlns:android="http://schemas.android.com/apk/res/android" '
        'package="' + PACKAGE + '" android:versionCode="1" android:versionName="1">'
        '<uses-permission android:name="android.permission.INTERNET"/><uses-sdk android:minSdkVersion="29" android:targetSdkVersion="29"/>'
        '<application android:label="SailDroid WebView probe" '
        'android:theme="@android:style/Theme.Material.Light.NoActionBar" '
        'android:hardwareAccelerated="true">'
        '<activity android:name="' + PACKAGE + '.' + activity + '" android:exported="true" '
        'android:configChanges="orientation|screenSize|keyboardHidden">'
        '<intent-filter><action android:name="android.intent.action.MAIN"/>'
        '<category android:name="android.intent.category.LAUNCHER"/></intent-filter>'
        '</activity></application></manifest>')
    (out / 'AndroidManifest.xml').write_text(manifest)
    env = dict(os.environ, LD_LIBRARY_PATH=str(AAPT_TOOL / 'usr/lib/aarch64-linux-gnu/android'))
    apk = out / 'webview.apk'
    subprocess.run([str(AAPT_TOOL / 'usr/bin/aapt'), 'package', '-f',
                    '-M', str(out / 'AndroidManifest.xml'), '-I', str(FRAMEWORK_APK),
                    '-F', str(apk)], env=env, check=True)
    with zipfile.ZipFile(apk, 'a', zipfile.ZIP_DEFLATED) as target, \
            zipfile.ZipFile(out / 'dex.jar') as dex:
        target.writestr('classes.dex', dex.read('classes.dex'))
    env = dict(os.environ, SAILDROID_BUILD_KEY_PASSWORD=(SIGNING / 'password').read_text().strip())
    subprocess.run([str(JAVA / 'jarsigner'), '-keystore', str(SIGNING / 'manager.jks'),
                    '-storepass:env', 'SAILDROID_BUILD_KEY_PASSWORD',
                    '-keypass:env', 'SAILDROID_BUILD_KEY_PASSWORD',
                    '-sigalg', 'SHA256withRSA', '-digestalg', 'SHA-256',
                    str(apk), 'saildroid'], env=env, check=True, capture_output=True)
    print('WEBVIEW_PROBE_APK=' + str(apk))
    print('SHA256=' + hashlib.sha256(apk.read_bytes()).hexdigest())


if __name__ == '__main__':
    main()
