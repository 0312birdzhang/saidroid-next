#!/bin/sh
# Compile scripts/device/SdWebViewProvider.java against the real API29 framework jar.
set -eu
REPO=/media/psf/Home/WorkSpace/saidroid-next
JDK=/tmp/jdkfull/jdk-21.0.13+9
FW=$(find /tmp /var/tmp "$REPO" -maxdepth 4 -name 'android-all-10-robolectric-*.jar' 2>/dev/null | head -1)
[ -n "$FW" ] || { echo NO_FRAMEWORK_JAR; exit 2; }
echo "FW=$FW"

# Gate: the provider class is also loaded in the binder broker (no graphics
# natives). A static field that constructs a graphics object killed that process
# with UnsatisfiedLinkError: android.graphics.Paint.nInit and broke every launch.
if ! python3 "$REPO/native/webview/tools/check-clinit-safety.py" \
        "$REPO/scripts/device/SdWebViewProvider.java"; then
    echo "JAVAC_RC=refused_clinit_unsafe"
    exit 4
fi
OUT=/var/tmp/sd-webview-javac
rm -rf "$OUT"; mkdir -p "$OUT"
set +e
"$JDK/bin/javac" --release 8 -nowarn -cp "$FW" -d "$OUT" $REPO/scripts/device/SdWebViewProvider.java -sourcepath "$REPO/scripts/device" > "$OUT/javac.log" 2>&1
RC=$?
set -e
echo "JAVAC_RC=$RC"
head -40 "$OUT/javac.log"
[ "$RC" = 0 ] && ls "$OUT"/*.class
