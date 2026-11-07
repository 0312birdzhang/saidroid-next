#!/usr/bin/env python3
"""Apply the public snapshot's pinned local changes to clean submodules."""
from pathlib import Path
import hashlib
import json
import subprocess

root = Path(__file__).resolve().parents[1]
dependencies = json.loads((root / 'third-party-sources.json').read_text())['dependencies']
plans = []
for row in dependencies:
    repo = root / row['path']
    if not (repo / '.git').exists():
        raise SystemExit('Run git submodule update --init --recursive first: ' + row['path'])
    revision = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
    if revision != row['revision']:
        raise SystemExit('Unexpected dependency revision: ' + row['path'])
    if subprocess.check_output(['git', '-C', str(repo), 'status', '--porcelain']):
        raise SystemExit('Dependency must be clean before patching: ' + row['path'])
    if 'patch' in row:
        patch = root / row['patch']
        if hashlib.sha256(patch.read_bytes()).hexdigest() != row['patch_sha256']:
            raise SystemExit('Patch checksum mismatch: ' + row['patch'])
        subprocess.run(['git', '-C', str(repo), 'apply', '--check', str(patch)], check=True)
        plans.append((repo, patch))
for repo, patch in plans:
    subprocess.run(['git', '-C', str(repo), 'apply', str(patch)], check=True)
print('SAILDROID_SOURCE=ready|dependencies=4|patches=' + str(len(plans)))
