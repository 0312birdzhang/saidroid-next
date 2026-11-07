#!/usr/bin/env python3
"""Freeze all official configurations and their runner/preparer contracts."""
from pathlib import Path
import argparse,json,xml.etree.ElementTree as E,hashlib
p=argparse.ArgumentParser();p.add_argument('configs',type=Path);p.add_argument('out',type=Path);a=p.parse_args();modules=[]
for path in sorted(a.configs.glob('*.config')):
 tree=E.parse(path).getroot()
 def spec(node):return dict(type=node.tag,**node.attrib,options=[dict(o.attrib)for o in node.findall('option')])
 modules.append(dict(module=path.stem,config_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),config_source='android-cts/testcases/'+path.name,preparers=[spec(n)for n in tree.findall('target_preparer')],runners=[spec(n)for n in tree.findall('test')],status='PENDING'))
assert len(modules)==377;a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(dict(api=29,cts='10_r16-arm',module_count=len(modules),modules=modules),indent=2)+'\n');print('MODULE_PLAN=377')
