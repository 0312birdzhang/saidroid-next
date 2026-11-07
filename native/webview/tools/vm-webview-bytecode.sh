#!/bin/sh
# Dump android.webkit.WebView bytecode in the VM and report, per public method,
# whether the body touches the provider/native plumbing (mProvider, mNativeWebView)
# -- those are the calls that can break when a foreign provider is installed.
set -eu
JDK=/tmp/jdkfull/jdk-21.0.13+9/bin
JAR=/var/tmp/sd-webview-javac/../android-all-10-robolectric-5803371.jar
JAR=$(ls /media/psf/Home/WorkSpace/saidroid-next/build/codex-api29/inputs/android-all-10-robolectric-5803371.jar)
OUT=/var/tmp/webview-bc.txt
"$JDK/javap" -p -c -classpath "$JAR" android.webkit.WebView > "$OUT" 2>&1
echo "JAVAP_LINES=$(wc -l < "$OUT")"
python3 - "$OUT" <<'PY'
import re, sys
txt = open(sys.argv[1]).read().split('\n')
cur, hits, out = None, [], []
for line in txt:
    m = re.match(r'^  .*?([A-Za-z_$][\w$]*)\((.*)\)(?: throws .*)?;$', line)
    if m:
        if cur and hits:
            out.append((cur, sorted(set(hits))))
        cur, hits = m.group(1), []
        continue
    if cur is None:
        continue
    for tag, needle in (('mProvider','mProvider'), ('mNativeWebView','mNativeWebView'),
                        ('WebViewProvider','android/webkit/WebViewProvider')):
        if needle in line and tag not in hits:
            hits.append(tag)
if cur and hits:
    out.append((cur, sorted(set(hits))))
print("PROVIDER_DEPENDENT_METHODS=%d" % len(out))
for name, tags in out:
    print("PD %-42s %s" % (name, ",".join(tags)))
PY
