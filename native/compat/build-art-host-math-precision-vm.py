#!/usr/bin/env python3
"""Build isolated native Math.sin/cos/tan/cbrt/pow intrinsic routing over byte-identical current ART.

Preserve all existing agent/resource/interface/signal-stack changes. Restore
every touched VM source, object and library even on failure. No phone staging,
managed heap, JIT policy, original test, timeout or clock changes.
"""
from pathlib import Path
import argparse, fcntl, hashlib, json, os, shutil, subprocess, time
p = argparse.ArgumentParser(description=__doc__)
for n in ['art-source', 'baseline-art', 'output']: p.add_argument('--' + n, type=Path, required=True)
a = p.parse_args(); os.umask(0o022)
r = Path(__file__).resolve().parents[2]; art = a.art_source; out = a.output
sha = lambda f: hashlib.sha256(f.read_bytes()).hexdigest()
assert not out.exists(); out.mkdir(parents=True)
lock = open('/var/lock/saidroid-art-host-math-build.lock', 'a')
fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
os.environ['JAVA_HOME'] = '/tmp/jdkfull/jdk-21.0.13+9'
os.environ['PATH'] = os.environ['JAVA_HOME'] + '/bin:' + os.environ['PATH']
old = json.loads((a.baseline_art / 'manifest.json').read_text())
assert old['passed'] and sha(a.baseline_art / 'libart.so') == old['binary_sha256']
assert old['binary_sha256'] == '764c106948fa4f3121bcd2f30bde8aeb382a951f387b50ae580511e509228460'
meta = json.loads((r / 'native/compat/math-precision/sources.json').read_text())
assert sha(r / meta['patch']) == meta['patch_sha256']
names = list(old['sources']) + list(meta['sources']); assert len(names) == len(set(names)) == 6
for n, v in old['sources'].items(): assert sha(art / n) == v['base_sha256']
for n, v in meta['sources'].items(): assert sha(art / n) == v['baseline_sha256'] == sha(r / 'third_party/art-standalone' / n)
sources = {n: ((art / n).read_bytes(), (art / n).stat()) for n in names}
inter = art / 'out/host/linux-x86/obj/SHARED_LIBRARIES/libart_intermediates'
files = [f for f in inter.rglob('*') if f.is_file()] + [art / 'out/host/linux-x86/lib64/libart.so', art / 'out/host/linux-x86/obj/lib/libart.so']
backups = {}; start = time.monotonic()
for f in files:
    n = str(f.relative_to(art)); dst = out / 'original' / n; dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(f, dst); backups[n] = sha(f)
record = dict(scope=__doc__, passed=False)
def build(label):
    with (out / (label + '.log')).open('x') as log:
        subprocess.run(['make', 'out/host/linux-x86/lib64/libart.so', '-j3'], cwd=art,
                       stdout=log, stderr=subprocess.STDOUT, check=True, timeout=1200)
    dst = out / (label + '-libart.so'); shutil.copy2(art / 'out/host/linux-x86/lib64/libart.so', dst)
    subprocess.run(['objcopy', '--strip-debug', str(dst)], check=True); return dst
def abi(f):
    result = {}
    for line in subprocess.check_output(['readelf', '--dyn-syms', '--wide', str(f)], text=True).splitlines():
        v = line.split()
        if len(v) >= 8 and v[0].rstrip(':').isdigit() and v[7]: result[v[7]] = (v[3], v[4], v[5], v[6] == 'UND')
    return result
try:
    for name, digest in old['patches'].items():
        patch = r / 'native/compat/patches' / name; assert sha(patch) == digest
        subprocess.run(['patch', '--batch', '--forward', '--no-backup-if-mismatch', '--fuzz=0', '-p1', '-i', str(patch)],
                       cwd=art, check=True, capture_output=True)
    assert all(sha(art / n) == v['patched_sha256'] for n, v in old['sources'].items())
    baseline = build('baseline'); assert sha(baseline) == old['binary_sha256'], 'Unmodified current ART must reproduce exact bytes first'
    subprocess.run(['patch', '--batch', '--forward', '--no-backup-if-mismatch', '--fuzz=0', '-p1', '-i', str(r / meta['patch'])],
                   cwd=art, check=True, capture_output=True)
    assert all(sha(art / n) == v['patched_sha256'] for n, v in meta['sources'].items())
    for n in names:
        dst = out / 'patched' / n; dst.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(art / n, dst)
    binary = build('candidate'); before, after = abi(baseline), abi(binary)
    assert all(after.get(n) == v for n, v in before.items())
    assert {n: v for n, v in after.items() if n not in before} == {n: ('NOTYPE', 'WEAK', 'DEFAULT', True) for n in ['ieee_sin','ieee_cos','ieee_tan','ieee_cbrt','ieee_pow']}
    shutil.copyfile(binary, out / 'libart.so'); (out / 'libart.so').chmod(0o644)
    record.update(passed=True, builder_sha256=sha(Path(__file__)), source_meta_sha256=sha(r / 'native/compat/math-precision/sources.json'),
                  baseline_manifest_sha256=sha(a.baseline_art / 'manifest.json'), baseline_binary_sha256=sha(baseline),
                  unmodified_art_reproduced_byte_identical=True, binary_sha256=sha(out / 'libart.so'),
                  old_dynamic_symbols_unchanged=True, only_new_weak_imports=['ieee_sin','ieee_cos','ieee_tan','ieee_cbrt','ieee_pow'], sources=meta['sources'],
                  patches={**old['patches'], Path(meta['patch']).name: meta['patch_sha256']}, seconds=time.monotonic()-start)
except BaseException as e: record.update(error=repr(e), traceback=__import__('traceback').format_exc())
finally:
    for n, (content, stamp) in sources.items():
        (art / n).write_bytes(content); os.utime(art / n, ns=(stamp.st_atime_ns, stamp.st_mtime_ns)); assert (art / n).read_bytes() == content
    for n, digest in backups.items(): shutil.copy2(out / 'original' / n, art / n); assert sha(art / n) == digest
    for file in inter.rglob('*'):
        if file.is_file() and str(file.relative_to(art)) not in backups: file.unlink()
    record['vm_baseline_sources_and_objects_restored'] = True
    (out / 'manifest.json').write_text(json.dumps(record, indent=2) + '\n')
    proof = r / 'build/evidence/cts-frame-repair-20261031' / (out.name.removeprefix('saidroid-') + '-build.json')
    assert not proof.exists(); proof.write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record, indent=2), flush=True)
assert record['passed']
