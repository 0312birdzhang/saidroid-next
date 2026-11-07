#!/bin/sh
# Inspect the API29 contract for the API23 onReceivedError overload: is
# WebResourceError an interface or an abstract class, and what must we implement?
set -u
JAR=/media/psf/Home/WorkSpace/saidroid-next/build/codex-api29/inputs/android-all-10-robolectric-5803371.jar
JP=/tmp/jdkfull/jdk-21.0.13+9/bin/javap
echo "== WebResourceError"
$JP -classpath "$JAR" android.webkit.WebResourceError 2>&1 | head -20
echo "== WebResourceRequest"
$JP -classpath "$JAR" android.webkit.WebResourceRequest 2>&1 | head -20
echo "== WebViewClient.onReceivedError (both overloads)"
$JP -classpath "$JAR" android.webkit.WebViewClient 2>&1 | grep -E "onReceivedError|onReceivedHttpError" | head -5
