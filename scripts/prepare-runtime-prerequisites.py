#!/usr/bin/env python3
"""Build omitted Android graphics APIs and extract the matching timezone data."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import zipfile

root = Path(__file__).resolve().parents[1]
output = Path(sys.argv[1])
if not str(output).startswith('/var/tmp/saidroid-next-'):
    raise SystemExit('Use a new isolated VM output directory')
output.mkdir(mode=0o700)
source = root / 'third_party/android-23-arm64/android-all-6.0.1_r3-robolectric-r1.jar'
image = Path('/tmp/and23/arm64-v8a/system.img')
prefixes = ('javax/microedition/khronos/', 'com/google/android/')
with zipfile.ZipFile(source) as original, zipfile.ZipFile(output / 'graphics-classes.jar', 'w') as target:
    entries = sorted(n for n in original.namelist()
                     if n.endswith('.class') and n.startswith(prefixes))
    if not entries or 'javax/microedition/khronos/egl/EGL10.class' not in entries:
        raise SystemExit('Required Android EGL interfaces absent from source framework')
    for name in entries:
        target.writestr(name, original.read(name))
java_home = Path('/tmp/jdkfull/jdk-21.0.13+9')
dx = Path('/tmp/art-build/art-standalone/out/host/linux-x86/bin/dx')
env = dict(os.environ, JAVA_HOME=str(java_home), PATH=str(java_home / 'bin') + ':' + os.environ['PATH'])
subprocess.run([str(dx), '--dex', '--output=' + str(output / 'framework-compat-hostdex.jar'),
                str(output / 'graphics-classes.jar')], env=env, check=True)
subprocess.run(['debugfs', '-R', 'dump /usr/share/zoneinfo/tzdata ' + str(output / 'tzdata'),
                str(image)], check=True, capture_output=True)
raw = (output / 'tzdata').read_bytes()
if len(raw) < 24 or raw[:6] != b'tzdata' or raw[11] != 0:
    raise SystemExit('Extracted timezone data header is invalid')
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
manifest = dict(schema='saidroid-runtime-prerequisites-v2',
                source_framework=str(source), source_framework_sha256=sha(source),
                source_image=str(image), source_image_sha256=sha(image),
                framework_classes=entries, timezone_version=raw[6:11].decode('ascii'),
                files={name: dict(sha256=sha(output / name), bytes=(output / name).stat().st_size)
                       for name in ('framework-compat-hostdex.jar', 'tzdata')})
(output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps(dict(manifest=str(output / 'manifest.json'), classes=len(entries),
                     timezone_version=manifest['timezone_version'], files=manifest['files']), indent=2))
