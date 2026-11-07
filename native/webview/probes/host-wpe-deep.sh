#!/bin/sh
# Inspect the WPE stack: /opt/wpe-sfos, headers, snapshot API, process helpers.
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@192.168.2.15"

echo "===== /opt/wpe-sfos"
$SSH 'find /opt/wpe-sfos -maxdepth 3 2>/dev/null | head -60'

echo "===== runtime-common.sh"
$SSH 'cat /opt/wpe-sfos/libexec/atlantic/runtime-common.sh 2>&1'

echo "===== wpe headers"
$SSH 'ls /usr/include/wpe-webkit-2.0/ /usr/include/wpe-webkit-2.0/wpe 2>&1; ls /usr/include/wpe-fdo-1.0/ /usr/include/wpe-fdo-1.0/wpe 2>&1'

echo "===== snapshot symbols"
$SSH 'nm -D --defined-only /usr/lib64/libWPEWebKit-2.0.so.1.11.4 2>/dev/null | grep -i -E "snapshot|run_javascript|evaluate_javascript" | head -20'

echo "===== webkit version string"
$SSH 'strings /usr/lib64/libWPEWebKit-2.0.so.1.11.4 2>/dev/null | grep -m5 -E "^([0-9]+\.[0-9]+\.[0-9]+|WebKitGTK)"'

echo "===== web process binaries"
$SSH 'ls -la /usr/libexec/wpe* /usr/libexec/webkit* /opt/wpe-sfos/libexec 2>&1 | head -40'

echo "===== wpe lib pkg"
$SSH 'rpm -qf /usr/lib64/libWPEWebKit-2.0.so.1.11.4 2>&1; rpm -qf /usr/lib64/libWPEBackend-fdo-1.0.so.1.11.0 2>&1; rpm -qi $(rpm -qf /usr/lib64/libWPEWebKit-2.0.so.1.11.4 2>/dev/null) 2>&1 | head -12'

echo "===== glibc version on device"
$SSH 'ldd --version 2>&1 | head -2; ls -la /lib64/libc.so.6'

echo "===== java/scene glue"
$SSH 'ls /usr/lib64/qt5/qml/Qt5MozillaNext153/ 2>&1; nm -D --defined-only /usr/lib64/qt5/qml/Qt5MozillaNext153/libqmlmozembedpluginqt5.so 2>/dev/null | grep -i -E "MozView|embed" | head -20'

echo "===== atlantic help"
$SSH '/usr/bin/atlantic-browser --help 2>&1 | head -40'
$SSH '/usr/bin/atlantic-browser.bin --help 2>&1 | head -40'

echo "===== gcc on device"
$SSH 'which gcc cc g++ make cmake meson ninja pkg-config python3 2>&1'
$SSH 'ls /usr/include/glib-2.0 2>&1 | head -3'

echo "===== wayland/EGL"
$SSH 'ls -la /run/display/ 2>&1; ls -la /usr/lib64/dri 2>&1 | head'

echo "DONE"
