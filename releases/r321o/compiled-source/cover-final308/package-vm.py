from pathlib import Path
import json,hashlib,copy,os,shutil
r=Path('/media/psf/Home/WorkSpace/saidroid-next');b=Path(__file__).parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();prior=r/'build/evidence/qq-cover-snapshot307-20261103-v1';old=json.loads((prior/'overlay.json').read_text());meta=copy.deepcopy(old);before=old['install_manifest'];after=meta['install_manifest'];payload=b/'payload';payload.mkdir();updated=[]
nb=json.loads((b/'native-build.json').read_text());host=json.loads((b/'host-build.json').read_text());assert nb['passed']and host['passed']
def install(p,n,mode=0o644):
 q=payload/n;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q);q.chmod(mode);v=dict(sha256=sha(q),size=q.stat().st_size,mode=mode);after['files'][n]=meta['changes'][n]=v;updated.append(n)
assert sha(Path(nb['path']))==nb['sha256'];assert sha(Path(host['path']))==host['sha256'];install(Path(nb['path']),'lib/libsdwindow.so');install(Path(host['path']),'libexec/saildroid-host',0o755)
for n in ['native-build.json','build-native-vm.py','host-build.json','build-host-vm.py','package-vm.py']:install(b/n,'share/build/cover-final308/'+n)
for p in (b/'source').rglob('*'):
 if p.is_file():install(p,'share/build/cover-final308/'+str(p.relative_to(b)))
runtime=json.loads((prior/'payload/runtime.json').read_text());runtime['gpu_presentation']=dict(schema='saidroid-gpu-subsurface-v1',primary='android-subsurfaces',cover='one-shot-hwui-snapshot-to-parent',steady_state_readback=False);runtime['native_startup']=dict(schema='saidroid-native-startup-overlap-v1',fifo_heavy_admission=True,app_vm_overlaps_broker=True,java_waits_for_broker=True);tmp=b/'runtime.json';tmp.write_text(json.dumps(runtime,indent=2)+'\n');install(tmp,'runtime.json');after['bytes']=sum(v['size']for v in after['files'].values());meta['cover_final308']=dict(updated_files=updated,scope='Keep original app subsurfaces; background-only HWUI snapshot; overlap admitted VM and broker startup without invoking Java early.')
assert before['symlinks']==after['symlinks'];assert all(after['files'][n]==v for n,v in before['files'].items()if n not in updated)
(b/'overlay.json').write_text(json.dumps(meta,indent=2)+'\n');record=dict(passed=True,candidate='r308',payload=str(payload),updated_files=updated,files=len(after['files']),symlinks=len(after['symlinks']),copied_bytes=sum((payload/n).stat().st_size for n in updated),install_manifest_sha256=hashlib.sha256((json.dumps(after,indent=2)+'\n').encode()).hexdigest(),overlay_sha256=sha(b/'overlay.json'),scope='Candidate only; not accepted.')
(b/'package.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2),flush=True)
