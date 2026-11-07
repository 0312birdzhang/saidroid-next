#!/bin/bash
# Run while holding the device lock. Private test tool, no launcher installation.
set -euo pipefail
repo=$(cd "$(dirname "$0")/../.." && pwd)
mkdir -p "$repo/build/hwui"
gcc -std=c11 -O2 -Wall -Wextra -Werror "$repo/native/hwui/tests/wayland-health.c" -o "$repo/build/hwui/sd-wayland-health" $(pkg-config --cflags --libs wayland-client)
sshpass -e ssh -o ConnectTimeout=8 root@bonito mkdir -p /home/art/test/hwui-tools
sshpass -e scp -O -q -o ConnectTimeout=8 "$repo/build/hwui/sd-wayland-health" root@bonito:/home/art/test/hwui-tools/sd-wayland-health
sshpass -e ssh -o ConnectTimeout=8 root@bonito chmod 755 /home/art/test/hwui-tools/sd-wayland-health
