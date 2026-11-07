#!/usr/bin/env python3
"""VM-only real ICU/SQLite execution and safe rejection of the old mixed layout.

Usage: test-native-library-layout.py PHONE_LIBRARY_FIXTURE ICU_DATA BRIDGE_BUILD OUTPUT
The fixture contains lib/, original bio2/ and corrected bio-clean/ from diagnosis.
No phone connection, package install or global library replacement is performed.
"""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys

fixture, icu, build, output = map(Path, sys.argv[1:])
if not str(output).startswith('/var/tmp/saidroid-next-'):
    raise SystemExit('Use a fresh isolated VM output directory')
output.mkdir(mode=0o700)
root = Path(__file__).resolve().parents[1]
art = Path('/tmp/art-build/art-standalone/out/host/linux-x86')
java = Path('/tmp/jdkfull/jdk-21.0.13+9')
env = dict(os.environ, JAVA_HOME=str(java), PATH=str(java / 'bin') + ':' + os.environ['PATH'],
           LD_LIBRARY_PATH=str(fixture / 'lib') + ':' + str(art / 'lib64')
           + ':/tmp/art-build/local-prefix/usr/lib/aarch64-linux-gnu:/usr/local/lib',
           ICU_DATA=str(icu))

def run(name, command, expected):
    result = subprocess.run(command, env=env, capture_output=True, timeout=20)
    (output / (name + '.stdout')).write_bytes(result.stdout)
    (output / (name + '.stderr')).write_bytes(result.stderr)
    if result.returncode != 0 or expected.encode() not in result.stdout:
        raise AssertionError((name, result.returncode, result.stderr[-1500:]))
    return dict(name=name, exit=result.returncode,
                stdout_sha256=hashlib.sha256(result.stdout).hexdigest(),
                stderr_sha256=hashlib.sha256(result.stderr).hexdigest())

binary = output / 'android-icu-check'
subprocess.run(['gcc', '-O2', '-Wall', '-Wextra', '-o', str(binary),
                str(root / 'native/android-icu-check.c'), '-ldl'], check=True)
cases = [run('real-sqlite', [str(binary), str(fixture / 'bio-clean'), str(icu)],
             'SQLITE_NATIVE_CHECK=PASS')]
classes = output / 'classes'
classes.mkdir()
sources = [root / 'scripts/device' / (name + '.java')
           for name in ('SdBridge', 'NativeLibraryLayoutProbe')]
subprocess.run([str(java / 'bin/javac'), '--release', '8', '-nowarn', '-d', str(classes),
                *map(str, sources)], check=True)
dex = output / 'layout.dex'
subprocess.run([str(art / 'bin/dx'), '--dex', '--output=' + str(dex), str(classes)],
               env=env, check=True)
data = output / 'art-data'
data.mkdir()
env.update(ANDROID_ROOT=str(art), ANDROID_DATA=str(data),
           LD_PRELOAD='/var/tmp/saidroid-next-jit-policy-20261025-r1/libsaidroid-unwind-compat.so')
cases.append(run('mixed-layout-rejected', [str(art / 'bin/dalvikvm'), '-Xnoimage-dex2oat',
                 '-cp', str(dex), 'NativeLibraryLayoutProbe', str(build / 'libsdbridge.so'),
                 str(fixture / 'bio2')], 'NATIVE_LIBRARY_LAYOUT_TESTS=PASS'))
proof = dict(result='PASS', cases=cases,
             bridge_sha256=hashlib.sha256((build / 'libsdbridge.so').read_bytes()).hexdigest(),
             icu_data_sha256=hashlib.sha256((icu / 'icudt55l.dat').read_bytes()).hexdigest())
(output / 'proof.json').write_text(json.dumps(proof, indent=2) + '\n')
print(json.dumps(proof, indent=2))
