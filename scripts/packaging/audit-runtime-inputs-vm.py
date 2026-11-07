#!/usr/bin/env python3
"""Find exact immutable component inputs and audit packaging tools; VM only."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,time

p=argparse.ArgumentParser();p.add_argument('--overlay',type=Path,required=True);p.add_argument('--expected-manifest',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
started=time.monotonic();a.output.mkdir(parents=True,exist_ok=False)
raw=a.overlay.read_bytes();overlay=json.loads(raw);manifest=overlay['install_manifest']
manifest_bytes=(json.dumps(manifest,indent=2)+'\n').encode()
assert hashlib.sha256(manifest_bytes).hexdigest()==a.expected_manifest
(a.output/'accepted-overlay.json').write_bytes(raw);(a.output/'accepted-install-manifest.json').write_bytes(manifest_bytes)
repo=Path('/media/psf/Home/WorkSpace/saidroid-next')
roots=[a.overlay.parent/'domain-payload',a.overlay.parent/'segment-payload',
       Path('/var/tmp/saidroid-icmp-cleanup286-v1-formal-vm-component/root'),
       Path('/var/tmp/saidroid-next-api29-component-r86-web/root')]
for parent,maxdepth in [(repo/'build/evidence',5),(Path('/var/tmp'),4)]:
 for directory,children,files in os.walk(parent):
  current=Path(directory);depth=len(current.relative_to(parent).parts)
  if current.name in ('root','payload') or current.name.endswith('-payload') or current.name.startswith('payload-') or '-payload-' in current.name:
   roots.append(current);children[:]=[];continue
  if depth>=maxdepth:children[:]=[]
  else:children[:]=[n for n in children if not n.startswith(('aot-build','runtime-build','classes','original-native','node_modules','.git','performance','distribution'))]
roots=list(dict.fromkeys(root for root in roots if root.is_dir()))
cache={}
def digest(path):
 stat=path.stat();key=(str(path.resolve()),stat.st_size,stat.st_mtime_ns)
 if key not in cache:
  h=hashlib.sha256()
  with path.open('rb')as f:
   for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
  cache[key]=h.hexdigest()
 return cache[key]
sources={};missing=[]
for index,(name,expected)in enumerate(manifest['files'].items()):
 found=None
 for root in roots:
  candidate=root/name
  if candidate.is_file()and candidate.stat().st_size==expected['size']and digest(candidate)==expected['sha256']:
   found=candidate;break
 if found:sources[name]=dict(path=str(found),sha256=expected['sha256'],size=expected['size'],mode=expected['mode'])
 else:missing.append(name)
 if index%250==0:print('RUNTIME_SOURCE_AUDIT|checked='+str(index)+'|found='+str(len(sources))+'|missing='+str(len(missing)),flush=True)
tools={n:shutil.which(n)for n in ['rpmbuild','rpm','readelf','ldd','setcap','runuser','unshare','bwrap','strace','gcc','python3']}
info=dict(passed=not missing,manifest_sha256=a.expected_manifest,overlay_sha256=hashlib.sha256(raw).hexdigest(),
          source_roots=[str(x)for x in roots],sources=sources,missing=missing,tools=tools,
          uid=os.getuid(),vm_os=Path('/etc/os-release').read_text(),seconds=time.monotonic()-started)
(a.output/'input-audit.json').write_text(json.dumps(info,indent=2)+'\n')
print(json.dumps({k:info[k]for k in ['passed','manifest_sha256','missing','tools','uid','seconds']},indent=2))
