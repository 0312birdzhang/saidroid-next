#!/usr/bin/env python3
"""Inventory official module requirements. Inventoried modules remain NOT_RUN."""
from pathlib import Path
import argparse,json,collections,xml.etree.ElementTree as ET
p=argparse.ArgumentParser();p.add_argument('config_dir',type=Path);p.add_argument('out',type=Path);a=p.parse_args()
inventory=json.loads((a.config_dir/'inventory.json').read_text());entries=[x for x in inventory['entries']if x['path'].endswith('.config')]
assert len({Path(x['path']).name for x in entries})==len(entries),'Basename collisions require preserving ZIP directories'
rows=[]
for entry in entries:
 path=a.config_dir/Path(entry['path']).name;root=ET.parse(path).getroot()
 rows.append(dict(module=path.stem,status='NOT_RUN',source=entry['path'],description=root.get('description'),components=[o.get('value')for o in root.findall('.//option')if o.get('key')=='component'],runners=[t.get('class')for t in root.findall('./test')],preparers=[t.get('class')for t in root.findall('./target_preparer')],apk_dependencies=sorted({o.get('value')for o in root.findall('.//option')if o.get('name')=='test-file-name'})))
counts=collections.Counter(r for row in rows for r in row['runners'])
result=dict(source=inventory['url'],module_configs=len(rows),formal_cts_runs=0,full_suite_status='BLOCKED',blockers=['No Android adbd/Tradefed device target','No Android am instrument/PackageInstaller/privileged permission preparation contract','No CTS-grade per-APK Android UID and permission isolation','Incomplete Android system service and hardware contracts'],runner_types=dict(sorted(counts.items())),modules=rows)
a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='modules'},indent=2))
