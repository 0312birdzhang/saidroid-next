#!/usr/bin/env python3
"""Build an isolated host with app-private DexMaker VM startup configuration.

The unchanged runtime helper still validates actual UID, canonical directory,
ownership and modes before any APK class loader. No APK/test/heap/timeout or
System implementation changes. This builder never stages a phone component.
"""
from pathlib import Path
import argparse, hashlib, json, os, shutil, subprocess

p = argparse.ArgumentParser(description=__doc__)
for n in ['baseline-host', 'component', 'output']:
    p.add_argument('--' + n, type=Path, required=True)
a = p.parse_args()
os.umask(0o022)
repo = Path(__file__).resolve().parents[2]
sha = lambda f: hashlib.sha256(f.read_bytes()).hexdigest()
assert not a.output.exists()
a.output.mkdir(parents=True)
manifest = json.loads((a.baseline_host / 'manifest.json').read_text())
installed = json.loads((a.component / 'install-manifest.json').read_text())
assert manifest['passed'] and manifest['schema'] == 'saildroid-timezone-env-native-v1'
host_hash = manifest['library_sha256']
assert host_hash == sha(a.baseline_host / 'saildroid-host')
assert host_hash == installed['files']['libexec/saildroid-host']['sha256']
assert host_hash == sha(a.component / 'libexec/saildroid-host')
source = a.output / 'source'
source.mkdir()
entry = repo / 'native/compat/timezone-layout/host-entry.cpp'
assert sha(entry) == manifest['source_sha256']
shutil.copyfile(entry, source / 'host-entry.cpp')
source_hashes = {str(f.relative_to(source)): sha(f) for f in source.rglob('*') if f.is_file()}
assert all(sha(repo / n) == h for n, h in manifest['sources'].items())
snapshot = Path(manifest['baseline_snapshot'])
assert all(sha(snapshot / n) == h for n, h in manifest['sources'].items())
commands = []
def compile_host(output, label, candidate=False):
    command = list(manifest['commands']['new'])
    assert command.count(str(entry)) == 1
    command[command.index('-o') + 1] = str(output)
    if candidate:
        command[command.index(str(entry))] = str(source / 'host-entry.cpp')
    commands.append(command)
    with (a.output / (label + '.log')).open('x') as log:
        subprocess.run(command, check=True, stdout=log, stderr=subprocess.STDOUT)
    output.chmod(0o755)
compile_host(a.output / 'baseline-saildroid-host', 'baseline-build')
assert sha(a.output / 'baseline-saildroid-host') == host_hash, 'Unmodified host must reproduce production bytes first'
patch = repo / 'native/compat/application-cache-startup/host-entry.patch'
with (a.output / 'patch.log').open('x') as log:
    subprocess.run(['patch', '--no-backup-if-mismatch', '--fuzz=0', '-p1', '-i', str(patch)], cwd=source, check=True, stdout=log, stderr=subprocess.STDOUT)
after = {str(f.relative_to(source)): sha(f) for f in source.rglob('*') if f.is_file()}
assert set(after) == set(source_hashes)
assert [n for n in after if after[n] != source_hashes[n]] == ['host-entry.cpp']
compile_host(a.output / 'saildroid-host', 'candidate-build', candidate=True)
assert sha(a.output / 'saildroid-host') != host_hash
assert sha(entry) == source_hashes['host-entry.cpp']
assert all(sha(repo / n) == h for n, h in manifest['sources'].items())
symbols = lambda f: set(' '.join(l.split()[-2:]) for l in subprocess.check_output(['nm', '-D', str(f)], text=True).splitlines() if len(l.split()) >= 2)
needed = lambda f: sorted(l.strip() for l in subprocess.check_output(['readelf', '-d', str(f)], text=True).splitlines() if '(NEEDED)' in l)
assert symbols(a.baseline_host / 'saildroid-host') == symbols(a.output / 'saildroid-host')
assert needed(a.baseline_host / 'saildroid-host') == needed(a.output / 'saildroid-host')
record = dict(schema='saildroid-application-cache-startup-v1', scope=__doc__, passed=True,
              builder_sha256=sha(Path(__file__)), patch_sha256=sha(patch),
              baseline_manifest_sha256=sha(a.baseline_host / 'manifest.json'),
              baseline_binary_sha256=host_hash, unmodified_host_reproduced_byte_identical=True,
              binary_sha256=sha(a.output / 'saildroid-host'), sources_before=source_hashes,
              sources_after=after, changed_sources=['host-entry.cpp'], commands=commands,
              all_dynamic_symbols_identical=True, needed_identical=True,
              phone_staged=False)
(a.output / 'manifest.json').write_text(json.dumps(record, indent=2) + '\n')
print('APPLICATION_CACHE_STARTUP=built|baseline_byte_identical=true|changed_host_sources=1|phone_staged=false')
