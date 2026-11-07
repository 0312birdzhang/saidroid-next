#!/bin/bash
# Prove the JNI contract gate is not decorative: mutate lastLayerCount to `int`
# (the exact bug that aborted QQ with SIGSEGV in r64) in a scratch copy and
# require the gate to refuse the build.
set -u
cd /media/psf/Home/WorkSpace/saidroid-next
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
cp -r native/window "$work/native-window"
cp -r scripts/device "$work/device"

python3 scripts/perf/check-jni-contract.py --native-dir "$work/native-window" \
        --java-dir "$work/device" >"$work/clean.log" 2>&1
clean_rc=$?

sed 's/private static long lastLayerCount;/private static int lastLayerCount;/' \
    "$work/device/SdSurfaceStore.java" >"$work/SdSurfaceStore.java" && \
    mv "$work/SdSurfaceStore.java" "$work/device/SdSurfaceStore.java"

python3 scripts/perf/check-jni-contract.py --native-dir "$work/native-window" \
        --java-dir "$work/device" >"$work/mutated.log" 2>&1
mutated_rc=$?

# Second mutation: a RegisterNatives table pointing at a function that does not exist.
cp -r native/window "$work/native-broken"
sed -i 's/"nativeGetWidth","(J)I",surface_width/"nativeGetWidth","(J)I",surface_width_typo/' \
    "$work/native-broken/sdwindow.c"
python3 scripts/perf/check-jni-contract.py --native-dir "$work/native-broken" \
        --java-dir "$work/device" >"$work/typo.log" 2>&1
typo_rc=$?

echo "SELFTEST_CLEAN_RC=$clean_rc"
echo "SELFTEST_TYPO_RC=$typo_rc"
echo "SELFTEST_MUTATED_RC=$mutated_rc"
grep -m3 'lastLayerCount' "$work/mutated.log" || true
grep -m1 'surface_width_typo' "$work/typo.log" || true
if [ "$clean_rc" -eq 0 ] && [ "$mutated_rc" -eq 3 ] && [ "$typo_rc" -eq 3 ] \
   && grep -q 'lastLayerCount wanted (J) but Java has (I)' "$work/mutated.log" \
   && grep -q 'surface_width_typo, which is not defined' "$work/typo.log"; then
  echo "SELFTEST=PASS"
else
  echo "SELFTEST=FAIL"
  tail -5 "$work/clean.log"; tail -5 "$work/mutated.log"
  exit 1
fi
