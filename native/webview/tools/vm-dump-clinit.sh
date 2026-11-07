#!/bin/sh
# Dump the <clinit> (static initializer) of the compiled provider so we can prove
# it does not touch graphics natives. This exists because of a real outage:
# `new Paint()` in a static field made the binder broker die with
#   java.lang.UnsatisfiedLinkError: android.graphics.Paint.nInit
#   at SdWebViewProvider.<clinit> ... System.exit(12)
# The broker has no graphics natives, so anything native in <clinit> kills it.
set -eu
JAVA_HOME=/tmp/jdkfull/jdk-21.0.13+9
CLS=/var/tmp/sd-webview-javac
JAR=/media/psf/Home/WorkSpace/saidroid-next/build/codex-api29/inputs/android-all-10-robolectric-5803371.jar
"$JAVA_HOME/bin/javap" -p -c -classpath "$CLS:$JAR" SdWebViewProvider > /var/tmp/sd-webview-javac/clinit.txt 2>&1
echo "== clinit body =="
awk '/static \{\}/{f=1} f{print} f&&/^$/{exit}' /var/tmp/sd-webview-javac/clinit.txt | sed -n '1,80p'
echo "== native-capable calls inside clinit =="
awk '/static \{\}/{f=1} f{print} f&&/^$/{exit}' /var/tmp/sd-webview-javac/clinit.txt \
    | grep -nE 'invoke(static|virtual|special|interface)' || echo "(none)"
