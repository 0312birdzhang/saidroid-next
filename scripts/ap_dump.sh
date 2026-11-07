#!/bin/bash
set -u
BASE=/tmp/art-build/art-standalone/out/host/linux-x86
export LD_LIBRARY_PATH=$BASE/lib64:/usr/local/lib
export ANDROID_ROOT=$BASE
export ANDROID_DATA=/tmp/art-data
mkdir -p $ANDROID_DATA
cd /tmp/ap || exit 1
echo "=== android.os.Binder 里和 onBinder 相关的成员 ==="
timeout 120 $BASE/bin/dalvikvm -cp /tmp/ap/ap.dex DumpMembers android.os.Binder onBinder 2>&1 | grep -a "^M \|^CLASS" | head -10
echo "=== Binder 的关键成员（execTransact / mObject）==="
timeout 120 $BASE/bin/dalvikvm -cp /tmp/ap/ap.dex DumpMembers android.os.Binder 2>&1 | grep -a "execTransact\|mObject\|^CLASS" | head -8
