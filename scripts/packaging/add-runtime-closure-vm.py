#!/usr/bin/env python3
"""Add reviewed non-OS runtime providers without replacing baseline files."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,re
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--audit',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
assert not a.output.exists();audit=json.loads(a.audit.read_text());assert Path(audit['root'])==a.root
sources={}
for name,value in audit['external_non_os'].items():
 assert len(value['paths'])==1,(name,value)
 sources[name]=dict(path=value['paths'][0],reason='DT_NEEDED closure',required_by=value['required_by'])
for name,reason in [('libopenjdk.so','ART native bootstrap dlopen'),('libart-compiler.so','ART JIT compiler dlopen')]:
 source=Path('/home/art/lib')/name;assert source.is_file()
 sources[name]=dict(path=str(source.resolve()),reason=reason,required_by=['lib/libart.so'])
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
added={}
for name,source in sources.items():
 assert '/'not in name
 target=a.root/'lib'/name
 assert not target.exists()and not target.is_symlink(),str(target)
 original=Path(source['path']);shutil.copyfile(original,target);target.chmod(0o644)
 assert sha(target)==sha(original)
 dynamic=subprocess.check_output(['readelf','-dW',str(target)],text=True)
 symbols=subprocess.check_output(['readelf','--dyn-syms','--wide',str(target)],text=True)
 undefined=[l.strip()for l in symbols.splitlines()if re.search(r'\bUND\b',l)]
 added['lib/'+name]=dict(source=source['path'],sha256=sha(target),size=target.stat().st_size,mode=0o644,
                        reason=source['reason'],required_by=source['required_by'],
                        search_paths=re.findall(r'\((RPATH|RUNPATH)\).*\[([^]]*)\]',dynamic),
                        required_versions=sorted(set(re.findall(r'@((?:GLIBC|GLIBCXX|CXXABI)_[0-9.]+)','\n'.join(undefined)))))
record=dict(passed=True,root=str(a.root),added=added,baseline_overwrites=0,
            source_boundary='VM accepted runtime/compiler support libraries; new private dependency bytes require target replay',
            nativehelper_vm_sha256=added['lib/libnativehelper.so']['sha256'],
            historical_phone_nativehelper_sha256='b950106fdbba3e60a13bfdbeb64c8bcce50afcc9400dfbe447d80629997828a3')
record['nativehelper_byte_matches_historical_phone']=record['nativehelper_vm_sha256']==record['historical_phone_nativehelper_sha256']
a.output.write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({k:v for k,v in record.items()if k!='added'},indent=2));print('Added',len(added),'private dependencies')
