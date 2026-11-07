#!/usr/bin/env python3
"""Extract the real ICU55 data used by the existing Android native libraries."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

output = Path(sys.argv[1])
if not str(output).startswith('/var/tmp/saidroid-next-'):
    raise SystemExit('Use a fresh isolated VM asset directory')
output.mkdir(mode=0o700)
image = Path('/tmp/and23/arm64-v8a/system.img')
target = output / 'icudt55l.dat'
subprocess.run(['debugfs', '-R', 'dump /usr/icu/icudt55l.dat ' + str(target), str(image)],
               check=True, capture_output=True)
data = target.read_bytes()
if len(data) < 1000000 or data[2:4] != b'\xda\x27' or data[12:16] != b'CmnD':
    raise SystemExit('Invalid ICU common data package')
manifest = dict(schema='saidroid-runtime-prerequisites-v3', source_image=str(image),
                source_image_sha256=hashlib.sha256(image.read_bytes()).hexdigest(),
                source_image_path='/usr/icu/icudt55l.dat',
                files={'icudt55l.dat': dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())})
(output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps(manifest, indent=2))
