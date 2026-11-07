from pathlib import Path
import json,copy,hashlib,shutil
r=Path('/media/psf/Home/WorkSpace/saidroid-next');b=Path(__file__).parent;prior=b.parent/'fix-v1';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();meta=copy.deepcopy(json.loads((prior/'overlay.json').read_text()));after=meta['install_manifest'];payload=b/'payload';payload.mkdir(exist_ok=True);updated=[];build=json.loads((b/'window-native/manifest.json').read_text());assert build['passed']
def install(p,n,mode=0o644):
 q=payload/n;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q);q.chmod(mode);v=dict(sha256=sha(q),size=q.stat().st_size,mode=mode)
 if after['files'].get(n)==v:return
 after['files'][n]=meta['changes'][n]=v;updated.append(n)
install(b/'window-native/libsdwindow.so','lib/libsdwindow.so')
for p in (r/'scripts/api29/window-retirement-compat').rglob('*'):
 if p.is_file():install(p,'share/build/window-retirement317/'+str(p.relative_to(r/'scripts/api29/window-retirement-compat')))
for name in ['build-window-vm.py','window-native/manifest.json','package-vm.py']:install(b/name,'share/build/window-retirement317/'+name)
after['bytes']=sum(v['size']for v in after['files'].values());(b/'overlay.json').write_text(json.dumps(meta,indent=2)+'\n');(b/'package.json').write_text(json.dumps(dict(passed=True,payload=str(payload),updated_files=updated,files=len(after['files']),symlinks=len(after['symlinks']),manifest_sha256=hashlib.sha256((json.dumps(after,indent=2)+'\n').encode()).hexdigest()),indent=2)+'\n');print('RETIREMENT317_PACKAGE=passed|files='+str(len(after['files'])))
