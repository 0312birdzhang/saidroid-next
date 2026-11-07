#!/bin/bash
# Focused Android API29 regression, never an official CTS certification claim.
set -euo pipefail
repo=$(cd "$(dirname "$0")/../.." && pwd)
label=${1:?unique-run-label}
release=${2:?staged-component-release}
tag=${3:?built-compat-apk-tag}
[[ $label =~ ^[a-z0-9-]+$ && $release =~ ^api29-[a-z0-9-]+$ && $tag =~ ^[a-z0-9-]+$ ]] || exit 2
out="$repo/build/compat/$label"
mkdir "$out"
bash "$repo/scripts/compat/run-vm.sh" "$label-api" "$release" "$tag" > "$out/api.log" 2>&1
bash "$repo/native/webview/qt-helper/run-verification-vm.sh" "$release" "$label-webview" > "$out/webview.log" 2>&1
python3 "$repo/scripts/compat/check-web-frame.py" "$repo/build/qq-startup-webview/$label-webview-after.png" > "$out/webview-pixels.json"
bash "$repo/native/webview/qt-helper/run-boundary-probe-vm.sh" "$label-native-webview" "$release" > "$out/native-boundary.log" 2>&1
bash "$repo/native/hwui/run-app-vm.sh" "$label-lifecycle" "$release" > "$out/lifecycle.log" 2>&1
python3 "$repo/native/hwui/check-app-frames.py" "$repo/build/hwui/$label-lifecycle" > "$out/static-frames.json"
bash "$repo/native/hwui/run-performance-vm.sh" "$label-perf" "$release" > "$out/performance.log" 2>&1
printf 'ANDROID_API29_REGRESSION=ready|run=%s|official_cts=false\n' "$label"
