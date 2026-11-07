#!/usr/bin/env python3
"""Build normal mutable application-temp startup over the exact current host.

Remove only the old immutable java.io.tmpdir startup option; owned core defaults use actual app data.
No ordinary libc interposition, System, APK, managedheap or test changes. The current host must reproduce byte-identically before patching.
"""
from pathlib import Path
import argparse, hashlib, json, os, shutil, subprocess
p = argparse.ArgumentParser(description=__doc__)
for name in ['baseline-host', 'component', 'output']: p.add_argument('--' + name, type=Path, required=True)
a = p.parse_args(); os.umask(0o022)
r = Path(__file__).resolve().parents[2]; sha = lambda f: hashlib.sha256(f.read_bytes()).hexdigest()
old = json.loads((a.baseline_host / 'manifest.json').read_text())
assert old['passed'] and old['schema'] == 'saildroid-math-precision-host-v1'
assert old['binary_sha256'] == sha(a.baseline_host / 'saildroid-host') == sha(a.component / 'libexec/saildroid-host')
installed = json.loads((a.component / 'install-manifest.json').read_text())
assert installed['files']['libexec/saildroid-host']['sha256'] == old['binary_sha256']
entry = a.baseline_host / 'source/host-entry.cpp'; assert sha(entry) == old['sources_after']['host-entry.cpp']
assert not a.output.exists(); a.output.mkdir(parents=True); source = a.output / 'source'; source.mkdir()
shutil.copyfile(entry, source / 'host-entry.cpp'); commands = []
def build(label, candidate):
    command = list(old['commands'][-1]); assert command.count(str(entry)) == 1
    output = a.output / (label + '-host'); command[command.index('-o') + 1] = str(output)
    if candidate: command[command.index(str(entry))] = str(source / 'host-entry.cpp')
    commands.append(command)
    with (a.output / (label + '.log')).open('x') as log:
        subprocess.run(command, check=True, stdout=log, stderr=subprocess.STDOUT, timeout=180)
    output.chmod(0o755); return output
baseline = build('baseline', False); assert sha(baseline) == old['binary_sha256']
patch = r / 'native/compat/patches/host-mutable-temp-default.patch'
with (a.output / 'patch.log').open('x') as log:
    subprocess.run(['patch', '--no-backup-if-mismatch', '--fuzz=0', '-p1', '-i', str(patch)], cwd=source,
                   check=True, stdout=log, stderr=subprocess.STDOUT)
assert {str(f.relative_to(source)) for f in source.rglob('*') if f.is_file()} == {'host-entry.cpp'}
candidate = build('candidate', True)
symbols = lambda f: set(' '.join(l.split()[-2:]) for l in subprocess.check_output(['nm', '-D', str(f)], text=True).splitlines() if len(l.split()) >= 2)
needed = lambda f: sorted(l.strip() for l in subprocess.check_output(['readelf', '-d', str(f)], text=True).splitlines() if '(NEEDED)' in l)
assert symbols(baseline) == symbols(candidate) and needed(baseline) == needed(candidate)
assert sha(entry) == old['sources_after']['host-entry.cpp'] and sha(candidate) != sha(baseline)
shutil.copyfile(candidate, a.output / 'saildroid-host'); (a.output / 'saildroid-host').chmod(0o755)
record = dict(schema='saildroid-mutable-temp-default-host-v1', scope=__doc__, passed=True,
              builder_sha256=sha(Path(__file__)), patch_sha256=sha(patch), baseline_manifest_sha256=sha(a.baseline_host / 'manifest.json'),
              baseline_binary_sha256=sha(baseline), binary_sha256=sha(candidate),
              sources_before={'host-entry.cpp': sha(entry)}, sources_after={'host-entry.cpp': sha(source / 'host-entry.cpp')},
              unmodified_host_reproduced_byte_identical=True, all_dynamic_symbols_identical=True, needed_identical=True,
              commands=commands, phone_staged=False)
(a.output / 'manifest.json').write_text(json.dumps(record, indent=2) + '\n')
print('MUTABLE_TEMP_DEFAULT_HOST=built|baseline_byte_identical=true|phone_staged=false')
