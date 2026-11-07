#!/bin/bash
# Second phase: the first tap landed at y=1985, i.e. below the login button
# (measured bbox from the screenshot: blue button y=1836..1965, centre 791,1900).
# This repoints api29-root at the already-deployed diag release and taps the centre.
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
H=root@192.168.2.15
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 $H"
REPO=/media/psf/Home/WorkSpace/saidroid-next
RUN=${1:-whiteboard2}
REL=/home/art/releases/api29-whiteboard1
EVID=$REPO/build/codex-api29/webview-$RUN
mkdir -p "$EVID"; cd "$REPO" || exit 1
scripts/devlock.sh status | grep -q "sd-webview" || { echo LOCK_NOT_MINE; exit 2; }
BASE=$($SSH 'readlink -f /home/art/api29-root'); echo "BASE_BEFORE=$BASE"
trap '$SSH "python3 -c \"import os,pathlib;link=pathlib.Path(\\\"/home/art/api29-root\\\");tmp=pathlib.Path(\\\"/home/art/.api29-root-webview\\\");tmp.unlink(missing_ok=True);tmp.symlink_to(\\\"'"$BASE"'\\\");os.replace(tmp,link);print(\\\"ROOT_NOW=\\\"+os.readlink(link))\" "' EXIT
scripts/lead_close_all.sh 2>&1 | tail -2
$SSH "python3 -c \"import os,pathlib;link=pathlib.Path('/home/art/api29-root');tmp=pathlib.Path('/home/art/.api29-root-webview');tmp.unlink(missing_ok=True);tmp.symlink_to('$REL');os.replace(tmp,link);print('ROOT_NOW='+os.readlink(link))\""
scripts/sd.sh launch --wait 60 --env SAILDROID_DIAG_INPUT=1 --env SAILDROID_ANDROID_LOG_STDERR=1 2>&1 | tail -2
scripts/sd.sh wait --wait 60 --marker SDWINDOW_SESSION=drawn 2>&1 | tail -1
sleep 3
scripts/sd.sh shot "$RUN-login" 2>&1 | tail -1
echo "=== tap login centre 791,1900 ==="
scripts/sd.sh input tap 791 1900 60 2>&1 | tail -1
sleep 3
scripts/sd.sh shot "$RUN-after" 2>&1 | tail -1
sleep 5
scripts/sd.sh shot "$RUN-late" 2>&1 | tail -1
scripts/sd.sh log -n 6000 > "$EVID/app.log" 2>&1
echo "LOG_LINES=$(wc -l < "$EVID/app.log")"
for pat in 'SDWEBVIEW=diag|' 'SDWEBVIEW=draw|' 'SDWEBVIEW=set_frame|' 'SDWEBVIEW=attached' 'SDWEBVIEW=predispatch' 'SDWEBVIEW=window_visibility' 'unsupported|' 'SDRUNTIME=failed' 'MarginLayoutParams.leftMargin' 'transaction_scheduled|class=com.tencent.mobileqq.webview'; do
  echo "COUNT[$pat]=$(grep -ac "$pat" "$EVID/app.log")"
done
grep -a 'SDACTIVITY=transaction_scheduled' "$EVID/app.log" | tr -d '\000' | tail -3
grep -a 'SDINPUT=finished' "$EVID/app.log" | tr -d '\000' | tail -3
echo "--- diag ---"; grep -a 'SDWEBVIEW=diag|' "$EVID/app.log" | tr -d '\000' | head -60
echo "--- draw/frame/state ---"; grep -a -E 'SDWEBVIEW=(draw|set_frame|attached|placeholder|state|callback|load_)' "$EVID/app.log" | tr -d '\000' | head -30
scripts/sd.sh close 2>&1 | tail -1
echo "DONE run=$RUN"
