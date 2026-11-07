#!/bin/sh
JAVA=/tmp/jdkfull/jdk-21.0.13+9/bin
J=/media/psf/Home/WorkSpace/saidroid-next/build/codex-api29/inputs/android-all-10-robolectric-5803371.jar
echo "== ScrollDelegate"
$JAVA/javap -p -classpath "$J" 'android.webkit.WebViewProvider$ScrollDelegate' 2>&1
echo "== WebSettings abstract count"
$JAVA/javap -p -classpath "$J" android.webkit.WebSettings 2>&1 | grep -c "abstract"
echo "== WebSettings sample"
$JAVA/javap -p -classpath "$J" android.webkit.WebSettings 2>&1 | head -20
echo "== WebViewClient surface"
$JAVA/javap -p -classpath "$J" android.webkit.WebViewClient 2>&1 | head -30
