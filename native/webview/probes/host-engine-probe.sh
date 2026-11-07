#!/bin/sh
# Read-only probe: what browser engine does the Sailfish host (device) expose?
# Runs inside the "MeeGo Build" VM and reaches the phone over SSH.
# Writes a report to stdout. No device modification.
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@192.168.2.15"

run() {
    echo "===== $1"
    $SSH "$2" 2>&1
    echo "===== exit=$?"
}

run uname "$SSH uname -a"

run os-release 'cat /etc/os-release'
run sailfish-release 'cat /etc/sailfish-release 2>/dev/null || true'

echo "===== rpm-engines"
$SSH 'rpm -qa | grep -i -E "webengine|qt5-qtwebengine|qtwebkit|chromium|gecko" | sort' 2>&1
echo "===== exit=$?"

echo "===== qt5-lib64"
$SSH 'ls -la /usr/lib64/qt5/ 2>&1 | head -60'

echo "===== libQt5WebEngine"
$SSH 'ls -la /usr/lib64/libQt5WebEngine* 2>&1'

echo "===== libQt5WebKit"
$SSH 'ls -la /usr/lib64/libQt5WebKit* /usr/lib64/libQt5WebKitWidgets* 2>&1'

echo "===== qt5-imports/plugins"
$SSH 'ls -la /usr/lib64/qt5/plugins/ 2>&1 | head -40'
$SSH 'ls -la /usr/lib64/qt5/qml/ 2>&1 | head -40'

echo "===== webengine-process-binary"
$SSH 'ls -la /usr/lib64/qt5/libexec/ 2>&1 | head -20'

echo "===== packaged-files-webengine"
$SSH 'rpm -ql qt5-qtwebengine 2>&1 | head -40'

echo "===== qtversion"
$SSH 'qmake-qt5 -v 2>&1 || qmake -v 2>&1 || true'
$SSH 'pkg-config --modversion Qt5Core Qt5WebEngineWidgets Qt5WebKitWidgets 2>&1 || true'

echo "===== running-browser-apps"
$SSH 'ps aux 2>/dev/null | grep -i -E "webengine|sailfish-browser|embedlite|qmlscene" | grep -v grep | head -20'

echo "===== droid-hybris-qtwebengine"
$SSH 'rpm -qa | grep -i -E "droid|hybris" | head -30'

echo "===== surface/graphics"
$SSH 'ls /usr/lib64/libQt5Gui.so* /usr/lib64/libQt5Quick.so* 2>&1'

echo "===== mesa/dri"
$SSH 'rpm -qa | grep -i -E "mesa|libgl" | sort | head -30'

echo "===== EGL/GBM/dma-buf device nodes"
$SSH 'ls -la /dev/dri/ 2>&1; ls -la /dev/dma_heap 2>&1; ls -la /dev/udmabuf 2>&1'

echo "===== wayland-socket"
$SSH 'ls -la /run/user/*/wayland-* 2>&1; echo WAYLAND_DISPLAY=$WAYLAND_DISPLAY'

echo "===== cpu/mem"
$SSH 'nproc; free -m 2>/dev/null | head -3'

echo "===== current-release"
$SSH 'ls -la /home/art/releases/ 2>&1 | tail -10; readlink -f /home/art/api29-root 2>&1'

echo "DONE"
