#!/bin/sh
# Prove the provider class has no <clinit> at all after the Paint incident.
set -eu
REPO=/media/psf/Home/WorkSpace/saidroid-next
JDK=/tmp/jdkfull/jdk-21.0.13+9/bin
OUT=/var/tmp/sd-webview-javac
[ -f "$OUT/SdWebViewProvider.class" ] || { echo "NO_CLASS"; exit 2; }
echo "CLINIT_SECTION_COUNT=$($JDK/javap -p -c "$OUT/SdWebViewProvider.class" | grep -c 'static {}')"
$JDK/javap -p -c "$OUT/SdWebViewProvider.class" | grep -nE 'static \{\}|<clinit>' || echo "NO_CLINIT_BYTECODE"
