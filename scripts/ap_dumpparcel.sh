set -u
BASE=/tmp/art-build/art-standalone/out/host/linux-x86
export LD_LIBRARY_PATH=$BASE/lib64:/usr/local/lib
export ANDROID_ROOT=$BASE
export ANDROID_DATA=/tmp/art-data
cd /tmp/ap || exit 1
echo "=== Parcel 的 native 方法 ==="
timeout 120 $BASE/bin/dalvikvm -cp /tmp/ap/ap.dex DumpMembers android.os.Parcel native 2>&1 | grep -a "^M \|^CLASS\|Error\|Exception" | head -30
