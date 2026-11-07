from pathlib import Path
import json,copy,hashlib,shutil
r=Path('/media/psf/Home/WorkSpace/saidroid-next');b=Path(__file__).parent;prior=r/'build/evidence/qq-picker-camera-settings313-20261103-v1/v26';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();meta=copy.deepcopy(json.loads((prior/'overlay.json').read_text()));after=meta['install_manifest'];payload=b/'payload';payload.mkdir(exist_ok=True);updated=[];build=json.loads((b/'encoded-build-v1.json').read_text());assert build['passed']
def install(p,n,mode=0o644):
 q=payload/n;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q);q.chmod(mode);v=dict(sha256=sha(q),size=q.stat().st_size,mode=mode)
 if after['files'].get(n)==v:return
 after['files'][n]=meta['changes'][n]=v;updated.append(n)
install(Path(build['encoded_root'])/'lib/runtime.jar','lib/runtime.jar')
install(r/'scripts/api29/runtime-permission-compat/source/SdMediaProvider.java','share/build/runtime-permission313/source/SdMediaProvider.java')
install(r/'scripts/api29/runtime-permission-compat/source/SdActivityHost.java','share/build/runtime-permission313/source/SdActivityHost.java')
install(r/'scripts/device/SdInputMethods.java','share/build/media-ime314/source/SdInputMethods.java')
for p in (r/'scripts/api29/media-refresh-ime-dismiss-compat').rglob('*'):
 if p.is_file():install(p,'share/build/media-ime314/'+str(p.relative_to(r/'scripts/api29/media-refresh-ime-dismiss-compat')))
for n in ['build-runtime-vm.py','runtime-build-v1.json','encode-runtime-vm.py','encoded-build-v1.json','package-vm.py']:install(b/n,'share/build/media-ime314/'+n)
after['bytes']=sum(v['size']for v in after['files'].values());(b/'overlay.json').write_text(json.dumps(meta,indent=2)+'\n');(b/'package.json').write_text(json.dumps(dict(passed=True,payload=str(payload),updated_files=updated,files=len(after['files']),symlinks=len(after['symlinks']),manifest_sha256=hashlib.sha256((json.dumps(after,indent=2)+'\n').encode()).hexdigest()),indent=2)+'\n');print('MEDIA_IME314_PACKAGE=passed|files='+str(len(after['files'])))
