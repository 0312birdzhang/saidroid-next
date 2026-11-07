#!/bin/bash
set -euo pipefail
repo=/media/psf/Home/WorkSpace/saidroid-next
sysroot=/srv/mer/targets/SailfishOS-5.1.0.11-aarch64
out=$repo/build/qt-webview-probe
mkdir -p "$out"
includes=()
for module in QtCore QtGui QtQml QtQuick QtNetwork; do
  includes+=("-I$sysroot/usr/include/qt5/$module")
done
g++ --sysroot="$sysroot" -std=c++11 -O2 -fPIC -Wall -Wextra -Wno-deprecated-copy \
  -I"$sysroot/usr/include/qt5" "${includes[@]}" \
  "$repo/native/webview/qt-helper/offscreen-probe.cpp" \
  -L"$sysroot/usr/lib64" -Wl,--allow-shlib-undefined \
  -lQt5Quick -lQt5Qml -lQt5Gui -lQt5Core -lGLESv2 -o "$out/offscreen-probe"
sha256sum "$out/offscreen-probe"
