#!/bin/bash
# One device-lock window for the frame-path measurement (VM side).
#
#   scripts/perf/session-vm.sh perf5                 # deploy + the full matrix
#   scripts/perf/session-vm.sh perf5 --only scroll-handler
#
# Requires scripts/devlock.sh acquired by sd-runtime (it refuses otherwise) and
# releases nothing on its own: the caller owns the lock lifetime, so a failed run
# still leaves the device inspectable.
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
REPO=/media/psf/Home/WorkSpace/saidroid-next
cd "$REPO" || exit 1
release=${1:-perf5}
shift || true

# Measure what is already installed (the r78 baseline is deployed by the Lead):
# --no-deploy skips the component install, --no-apk skips the probe APK install.
deploy=1
apk=1
matrix_args=()
for argument in "$@"; do
  case "$argument" in
    --no-deploy) deploy=0 ;;
    --no-apk) apk=0 ;;
    *) matrix_args+=("$argument") ;;
  esac
done

start=$(date +%s)
echo "SESSION_START=$(date -Is) release=$release"

holder=$(sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 \
         root@bonito "cat /home/art/test/.device-lock/owner 2>/dev/null" 2>/dev/null)
case "$holder" in
  sd-runtime*) echo "LOCK_OK owner=$holder" ;;
  *) echo "LOCK_REFUSED owner=${holder:-none} (acquire with: scripts/devlock.sh acquire 900 sd-runtime)"; exit 2 ;;
esac

echo "=== device display state (screen on? screensaver? our window visible?)"
bash scripts/perf/display-state.sh || true

echo "=== close stale owned processes"
python3 scripts/perf/close-owned-vm.py || exit 3

if [ "$deploy" -eq 1 ]; then
echo "=== deploy $release"
# A failed earlier deploy can leave its staging directory behind, and the
# deployer refuses to start while it exists. It only ever holds our own
# half-installed tree under /home/art/test.
stage=/home/art/test/api29-deploy-20261026-$release
sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@bonito \
  "if [ -e '$stage' ]; then rm -rf '$stage' && echo stage_removed=$stage; fi" 2>&1 | tail -1
python3 scripts/perf/deploy-perf-release-vm.py "$release" || exit 4
echo "=== deploy done at $(date -Is) ($(( $(date +%s) - start ))s)"
else
echo "=== deploy skipped (--no-deploy), measuring the installed release: $(sshpass -e ssh -o StrictHostKeyChecking=no root@bonito 'readlink /home/art/api29-root' 2>/dev/null)"
fi

if [ "$apk" -eq 1 ]; then
echo "=== install scroll APK"
python3 scripts/perf/install-scroll-vm.py ${release}-scroll || exit 5
echo "=== APK installed at $(date -Is) ($(( $(date +%s) - start ))s)"
else
echo "=== APK install skipped (--no-apk)"
fi

echo "=== matrix"
python3 scripts/perf/run-matrix-vm.py "$release" "${matrix_args[@]}"
status=$?

echo "SESSION_END=$(date -Is) elapsed=$(( $(date +%s) - start ))s status=$status"
exit $status
