#!/bin/bash
set -u
echo "=== robolectric jar ==="
ls -l /tmp/*/android-all-10-robolectric-5803371.jar /var/tmp/*/android-all-10-robolectric-5803371.jar /home/art/test/*/*.jar 2>/dev/null | head -5
find /tmp /var/tmp /home/art/test -maxdepth 3 -name "android-all-10-robolectric*" 2>/dev/null | head -5
echo "=== r8 ==="
find /tmp /var/tmp -maxdepth 3 -name "r8-*.jar" 2>/dev/null | head -3
echo "=== framework29 jars ==="
find /tmp /var/tmp /home/art/test -maxdepth 3 -name "framework29-*" 2>/dev/null | head -8
echo "=== native/system staging ==="
ls -d /tmp/ap29-* /var/tmp/ap29-* /home/art/test/ap29-* 2>/dev/null | head -10
