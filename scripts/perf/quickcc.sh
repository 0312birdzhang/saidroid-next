set -e
cd /media/psf/Home/WorkSpace/saidroid-next
D=/var/tmp/saidroid-next-perf-quickcc
rm -rf $D && mkdir -p $D
xml=/usr/share/wayland-protocols/stable/xdg-shell/xdg-shell.xml
wayland-scanner client-header $xml $D/xdg-shell-client-protocol.h
wayland-scanner private-code $xml $D/xdg-shell-protocol.c
wayland-scanner client-header native/window/surface-extension.xml $D/surface-extension-client-protocol.h
wayland-scanner private-code native/window/surface-extension.xml $D/surface-extension-protocol.c
JAVAHOME=${JAVA_HOME:-/tmp/jdkfull/jdk-21.0.13+9}
gcc -shared -fPIC -O2 -Wall -o $D/libsdwindow.so native/window/sdwindow.c native/window/sdcontrol.c native/window/sdactivate.c $D/xdg-shell-protocol.c $D/surface-extension-protocol.c -I$D -I$JAVAHOME/include -I$JAVAHOME/include/linux $(pkg-config --cflags --libs wayland-client) -pthread
echo QUICKCC_OK
