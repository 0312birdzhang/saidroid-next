#!/usr/bin/env python3
"""Preserve frozen source recipes before retiring superseded round-two builds.

This CPU-only operation does not access the phone. Default is a read-only plan
apart from writing compact audit snapshots into the evidence directory.
"""
from pathlib import Path
import argparse, hashlib, json, shutil, subprocess

p = argparse.ArgumentParser()
p.add_argument('evidence', type=Path)
p.add_argument('--apply', action='store_true')
a = p.parse_args()
history = a.evidence / 'runtime-history'
history.mkdir(exist_ok=True)
rows = []
for version in range(124, 130):
    source = Path('/var/tmp') / ('saidroid-native-transition-20261030-r' + str(version))
    if not source.exists():
        continue
    assert source.is_dir() and not source.is_symlink()
    out = history / ('r' + str(version))
    out.mkdir(exist_ok=True)
    recipe_path = source / 'transition-recipe.json'
    recipe = json.loads(recipe_path.read_text()) if recipe_path.is_file() else None
    fallback = history / 'r124/transition-recipe.json'
    names = recipe['overlays'] if recipe else json.loads(fallback.read_text())['overlays']
    actual_source_hashes = {}
    for name, expected in names.items():
        file = source / 'source' / name
        actual = hashlib.sha256(file.read_bytes()).hexdigest()
        if recipe:
            assert actual == expected, name
        actual_source_hashes[name] = actual
        target = out / 'source' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(file, target)
    (out / 'source-snapshot.json').write_text(json.dumps(dict(recipe_present=bool(recipe),
        note='Actual frozen source hashes; missing recipe means a failed build, not a deployable release',
        files=actual_source_hashes), indent=2) + '\n')
    for name in ['native/host', 'third_party/art-standalone/libnativehelper/include']:
        shutil.copytree(source / 'source' / name, out / 'source' / name, dirs_exist_ok=True)
    preserved = []
    for name in ['transition-recipe.json', 'bundle/overlay.json', 'product/manifest.json',
                 'product/native-build.log', 'product/javac.log', 'product/d8.log']:
        file = source / name
        if file.is_file():
            target = out / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(file, target)
            preserved.append(dict(path=name, sha256=hashlib.sha256(file.read_bytes()).hexdigest()))
    tarball = source / 'bundle/native-overlay.tar.gz'
    row = dict(runtime='r' + str(version), vm_path=str(source),
               vm_kib=int(subprocess.check_output(['du', '-sk', str(source)], text=True).split()[0]),
               preserved=preserved, bundle_complete=tarball.is_file(), removed=False)
    if tarball.is_file():
        row['tarball_sha256'] = hashlib.sha256(tarball.read_bytes()).hexdigest()
    else:
        row['note'] = 'Build failed before a deployable bundle; source and build diagnostics retained'
    if a.apply:
        for proc in Path('/proc').iterdir():
            if not proc.name.isdigit():
                continue
            try:
                command = (proc / 'cmdline').read_bytes()
            except OSError:
                continue
            assert str(source).encode() not in command, 'Build still referenced by process ' + proc.name
        shutil.rmtree(source)
        row['removed'] = True
    rows.append(row)
(history / ('vm-prune.json' if a.apply else 'vm-prune-plan.json')).write_text(json.dumps(rows, indent=2) + '\n')
print(json.dumps(rows, indent=2))
