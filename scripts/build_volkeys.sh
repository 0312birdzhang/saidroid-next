set -eu
V=/tmp/vk; rm -rf $V; mkdir -p $V; cd $V
gcc -O2 -o $V/inject_volkeys /media/psf/Home/WorkSpace/saidroid-next/native/viewer/tools/inject_volkeys.c 2>&1 | head -10
ls -l $V/inject_volkeys
