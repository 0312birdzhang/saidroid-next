#!/usr/bin/env python3
"""Add hash-verified captured target dependencies without replacing component files."""
from pathlib import Path
import argparse, hashlib, json, shutil
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--capture',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
assert not a.output.exists()
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
manifest=a.capture/'manifest.json';data=json.loads(manifest.read_text());assert data['passed']and not data['missing']
assert 'ID=sailfishos' in data['os']
records={};skipped={}
for entry in data['items']:
 name=entry['name'];assert Path(name).name==name
 source=a.capture/'files'/name
 assert source.is_file()and sha(source)==entry['sha256']and source.stat().st_size==entry['bytes'],name
 target=a.root/'lib'/name
 if target.exists()or target.is_symlink():
  skipped[name]=dict(reason='preserve accepted component bytes',component_sha256=sha(target),phone_sha256=entry['sha256']);continue
 # Materialize resolved bytes under the advertised basename. Target symlink
 # provenance remains recorded; no link can escape into /home/art.
 shutil.copyfile(source,target);target.chmod(0o644)
 records[name]=dict(source=str(source),sha256=sha(target),mode=0o644,original=entry)
result=dict(passed=True,capture_manifest_sha256=sha(manifest),phone_boot=data['boot'],phone_os=data['os'],
            added=records,baseline_preserved=skipped,root=str(a.root),phone_contacted=False,
            note='Resolved target bytes; library permissions normalized to root-owned 0644 for ordinary callers')
a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,added=len(records),preserved=len(skipped))))
