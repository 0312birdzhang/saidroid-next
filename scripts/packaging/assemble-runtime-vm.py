#!/usr/bin/env python3
"""Materialize a full versioned runtime from an exact source index, without activation."""
from pathlib import Path,PurePosixPath
import argparse,hashlib,json,os,re,shutil,stat

def digest(path):
 h=hashlib.sha256()
 with Path(path).open('rb')as f:
  for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
 return h.hexdigest()

p=argparse.ArgumentParser();p.add_argument('--audit',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--release-id',required=True);p.add_argument('--compiler',type=Path);a=p.parse_args()
assert re.fullmatch(r'[a-z0-9][a-z0-9.-]+',a.release_id)
assert not a.output.exists();audit=json.loads(a.audit.read_text());assert audit['passed']and not audit['missing']
manifest_path=a.audit.parent/'accepted-install-manifest.json';manifest=json.loads(manifest_path.read_text());assert digest(manifest_path)==audit['manifest_sha256']
root=a.output/'root';root.mkdir(parents=True)
for name,entry in manifest['files'].items():
 relative=PurePosixPath(name);assert not relative.is_absolute()and '..'not in relative.parts
 source=Path(audit['sources'][name]['path']);assert source.is_file()and source.stat().st_size==entry['size']and digest(source)==entry['sha256'],name
 target=root/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target);target.chmod(entry['mode'])
 assert digest(target)==entry['sha256']and stat.S_IMODE(target.stat().st_mode)==entry['mode'],name
for name,value in manifest['symlinks'].items():
 relative=PurePosixPath(name);assert not relative.is_absolute()and '..'not in relative.parts
 target=root/name;target.parent.mkdir(parents=True,exist_ok=True);target.symlink_to(value)
 assert str(target.resolve()).startswith(str(root.resolve())+'/'),name
for directory in ['empty-libs','apex/com.android.tzdata/etc/tz']:(root/directory).mkdir(parents=True,exist_ok=True)
compiler_info=None
if a.compiler:
 c=json.loads((a.compiler/'manifest.json').read_text())
 assert c['accepted_art_sha256']==manifest['files']['lib/libart.so']['sha256']
 for name,value in c['files'].items():assert digest(a.compiler/name)==value['sha256'],name
 shutil.copytree(a.compiler,root/'compiler')
 compiler_info=dict(manifest_sha256=digest(a.compiler/'manifest.json'),files=len(c['files']),source=str(a.compiler))
result=dict(passed=True,release_id=a.release_id,installed_root='/opt/saildroid/releases/'+a.release_id,
            root=str(root),baseline_manifest_sha256=audit['manifest_sha256'],
            baseline_files=len(manifest['files']),baseline_links=len(manifest['symlinks']),
            baseline_bytes=sum(v['size']for v in manifest['files'].values()),baseline_unchanged=True,
            compiler=compiler_info,activation_performed=False,service_changes=False,target_tested=False)
(a.output/'assembly.json').write_text(json.dumps(result,indent=2)+'\n');shutil.copyfile(manifest_path,a.output/'baseline-install-manifest.json')
print(json.dumps(result,indent=2))
