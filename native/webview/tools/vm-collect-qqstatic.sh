#!/bin/sh
# Collect the static-analysis inputs into the shared repo (so the Mac side can join
# them): provider-dependent WebView methods, and the WebSettings/WebView javap surfaces.
set -eu
REPO=/media/psf/Home/WorkSpace/saidroid-next
OUT="$REPO/build/codex-api29/webview-qqstatic"
JDK=/tmp/jdkfull/jdk-21.0.13+9/bin
JAR="$REPO/build/codex-api29/inputs/android-all-10-robolectric-5803371.jar"
mkdir -p "$OUT"
sh "$REPO/native/webview/tools/vm-webview-bytecode.sh" > "$OUT/bytecode-provider-dependent.txt" 2>&1
"$JDK/javap" -classpath "$JAR" android.webkit.WebSettings > "$OUT/javap-websettings.txt" 2>&1
"$JDK/javap" -classpath "$JAR" android.webkit.WebViewClient > "$OUT/javap-webviewclient.txt" 2>&1
"$JDK/javap" -classpath "$JAR" android.webkit.CookieManager > "$OUT/javap-cookiemanager.txt" 2>&1
echo "LINES pd=$(wc -l < "$OUT/bytecode-provider-dependent.txt") settings=$(wc -l < "$OUT/javap-websettings.txt")"
