#!/bin/bash
set -euo pipefail
repo=/media/psf/Home/WorkSpace/saidroid-next
label=${1:-qt-offscreen-$(date -u +%Y%m%dT%H%M%SZ)}
[[ $label =~ ^[a-zA-Z0-9_-]+$ ]] || exit 2
out=$repo/build/evidence/$label
remote=/home/defaultuser/.local/share/saidroid-webview-probes/$label
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
ssh=(sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@bonito)
scp=(sshpass -e scp -q -o StrictHostKeyChecking=no -o ConnectTimeout=8)
mkdir -p "$out"
cd "$repo"
bash scripts/devlock.sh acquire 0 codex-webview
trap 'bash scripts/devlock.sh release codex-webview' EXIT
"${ssh[@]}" "test ! -e '$remote' && mkdir -p '$remote/out'"
"${scp[@]}" "$repo/build/qt-webview-probe/offscreen-probe" "$repo/native/webview/qt-helper/probe.qml" "root@bonito:$remote/"
"${ssh[@]}" "cat > '$remote/run.sh'" <<'PHONE'
#!/bin/sh
set -eu
cd "$(dirname "$0")"
export HOME="$PWD/home" XDG_DATA_HOME="$PWD/home/data" XDG_CACHE_HOME="$PWD/home/cache" XDG_CONFIG_HOME="$PWD/home/config"
mkdir -p "$XDG_DATA_HOME" "$XDG_CACHE_HOME" "$XDG_CONFIG_HOME"
. /opt/wpe-sfos/libexec/atlantic/runtime-common.sh
atlantic_export_browser_env
export ATLANTIC_DIRECT_COMPOSITE=0 QSG_RENDER_LOOP=basic
exec ./offscreen-probe "$PWD/probe.qml" "$PWD/out"
PHONE
"${ssh[@]}" "chmod 755 '$remote/offscreen-probe' '$remote/run.sh'; chown -R defaultuser:defaultuser '$remote'; python3 - '$remote'" <<'PY'
import subprocess,sys,os,signal
root=sys.argv[1]
before=open('/proc/sys/kernel/random/boot_id').read().strip()
lip_before=subprocess.check_output(['pidof','lipstick']).decode().strip()
with open(root+'/run.log','wb') as log:
    p=subprocess.Popen(['su','defaultuser','-s','/bin/sh','-c',root+'/run.sh'],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    try: code=p.wait(timeout=25)
    except subprocess.TimeoutExpired: code=124
    finally:
        try: os.killpg(p.pid,signal.SIGTERM)
        except ProcessLookupError: pass
        try: p.wait(timeout=3)
        except subprocess.TimeoutExpired: os.killpg(p.pid,signal.SIGKILL);p.wait()
print('SDWEBHOST_RUN=finished|exit=%s|boot=%s|lipstick_before=%s|lipstick_after=%s'%(code,before,lip_before,subprocess.check_output(['pidof','lipstick']).decode().strip()))
subprocess.run(['mcetool','--blank-screen'],check=True)
PY
"${scp[@]}" "root@bonito:$remote/run.log" "$out/run.log"
"${scp[@]}" -r "root@bonito:$remote/out" "$out/frames"
cat "$out/run.log"
echo "EVIDENCE=$out"
