#!/bin/bash
set -euo pipefail
repo=$(cd "$(dirname "$0")/../../.." && pwd)
sysroot=${SAILDROID_QT_SYSROOT:-/srv/mer/targets/SailfishOS-5.1.0.11-aarch64}
out=${1:-$repo/build/qt-webview-host}
mkdir -p "$out"
includes=()
for module in QtCore QtGui QtQml QtQuick QtNetwork; do includes+=("-I$sysroot/usr/include/qt5/$module"); done
moc=$sysroot/usr/lib64/qt5/bin/moc
[ -x "$moc" ] || moc=$sysroot/usr/bin/moc
"$moc" "$repo/native/webview/qt-helper/sdwebviewd.cpp" -o "$out/sdwebviewd.moc"
g++ --sysroot="$sysroot" -std=c++11 -O2 -fPIC -Wall -Wextra -Wno-deprecated-copy \
  -I"$sysroot/usr/include/glib-2.0" -I"$sysroot/usr/lib64/glib-2.0/include" \
  -I"$sysroot/usr/include/qt5" "${includes[@]}" -I"$out" \
  "$repo/native/webview/qt-helper/sdwebviewd.cpp" \
  -L"$sysroot/usr/lib64" -Wl,--allow-shlib-undefined \
  -lQt5Quick -lQt5Qml -lQt5Gui -lQt5Core -lGLESv2 -lgobject-2.0 -lglib-2.0 -o "$out/sdwebviewd"
cp "$repo/native/webview/qt-helper/engine.qml" "$out/webview-engine.qml"
g++ -std=c++17 -O2 -Wall -Wextra "$repo/native/webview/qt-helper/native-host.cpp" -o "$out/sdwebview-host"
cp "$repo/native/webview/qt-helper/runtime-env.sailfish52.json" "$out/webview-host-env.json"
chmod 755 "$out/sdwebview-host"
sha256sum "$out/sdwebviewd"
