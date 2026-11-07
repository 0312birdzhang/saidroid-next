#!/usr/bin/env python3
"""Bind the installed API28 release's standalone core JNI in its private linker."""
import argparse
import json
import re
import subprocess
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--root', type=Path, required=True)
parser.add_argument('--release-id', required=True)
arguments = parser.parse_args()
root = arguments.root.resolve()
assert not str(root).startswith(('/opt/saildroid/releases/', '/home/art/releases/'))
assert re.fullmatch('[a-z0-9][a-z0-9.-]{0,100}', arguments.release_id)
assert json.loads((root/'runtime.json').read_text())['api'] == 28
assert not (root/'share/packaging/activation-manifest.json').exists()
config = root/'linker-config/runtime.cfg'
names = ('libjavacore.so', 'libopenjdk.so', 'libopenjdkjvm.so')
sources = {source for name in names for source in (name, '/system/lib64/'+name, '/system/lib/'+name)}
lines = [line for line in config.read_text().splitlines()
         if not line.split() or line.split()[0] not in sources]
installed = '/opt/saildroid/releases/'+arguments.release_id
for name in names:
    dynamic = subprocess.check_output(['readelf', '-dW', str(root/'lib'/name)], text=True)
    assert '(NEEDED)' in dynamic and '[libc.so.6]' in dynamic, name
    for source in (name, '/system/lib64/'+name, '/system/lib/'+name):
        lines.append(source+' '+installed+'/lib/'+name)
config.write_text('\n'.join(lines)+'\n')
config.chmod(0o644)
print('API28_CORE_LINKER_BOUND', arguments.release_id)
