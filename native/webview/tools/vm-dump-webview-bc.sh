#!/bin/sh
# Full bytecode dump of android.webkit.WebView (+ WebViewProvider interface list),
# so the Mac side can map "WebView method the app calls" -> "provider method we must
# implement". Read-only.
set -eu
REPO=/media/psf/Home/WorkSpace/saidroid-next
OUT="$REPO/build/codex-api29/webview-qqstatic"
JDK=/tmp/jdkfull/jdk-21.0.13+9/bin
JAR="$REPO/build/codex-api29/inputs/android-all-10-robolectric-5803371.jar"
mkdir -p "$OUT"
"$JDK/javap" -p -c -classpath "$JAR" android.webkit.WebView > "$OUT/javap-webview-bytecode.txt" 2>&1
"$JDK/javap" -classpath "$JAR" 'android.webkit.WebViewProvider' > "$OUT/javap-webviewprovider.txt" 2>&1
echo "BC_LINES=$(wc -l < "$OUT/javap-webview-bytecode.txt") PROVIDER_LINES=$(wc -l < "$OUT/javap-webviewprovider.txt")"
