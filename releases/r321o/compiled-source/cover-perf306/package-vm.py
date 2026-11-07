from pathlib import Path
import json,hashlib,copy,os,shutil,stat,tarfile
r=Path('/media/psf/Home/WorkSpace/saidroid-next');b=Path(__file__).parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();nb=json.loads((b/'native-build-v2.json').read_text());assert nb['passed'];prior=r/'build/evidence/qq-service-lifecycle305-20261103-v1';old=json.loads((prior/'bundle/overlay.json').read_text());before=old['install_manifest'];meta=copy.deepcopy(old);after=meta['install_manifest'];payload=b/'payload';payload.mkdir();updated=[]
def install(p,n,mode=0o644):
 q=payload/n;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q);q.chmod(mode);v=dict(sha256=sha(q),size=q.stat().st_size,mode=mode);after['files'][n]=meta['changes'][n]=v;updated.append(n)
for n,d in nb['files'].items():
 p=Path(d['path']);assert sha(p)==d['sha256'];install(p,'libexec/'+n if n=='saildroid-host'else'lib/'+n,0o755 if n=='saildroid-host'else 0o644)
for n in ['native-build-v2.json','build-native-v2-vm.py','package-vm.py']:install(b/n,'share/build/cover-perf306/'+n)
for p in (b/'source').rglob('*'):
 if p.is_file():install(p,'share/build/cover-perf306/'+str(p.relative_to(b)))
root=Path(json.loads((prior/'package.json').read_text())['native_payload']);runtime=json.loads((root/'runtime.json').read_text());runtime['art_heap_policy']=dict(schema='saidroid-art-heap-policy-v1',initial_mb=16,min_free_mb=4,max_free_mb=16,target_utilization=0.75);runtime['gpu_presentation']=dict(schema='saidroid-gpu-primary-parent-v1',primary='first-fullscreen-android-root',other_windows='subsurfaces',cpu_readback=False);tmp=b/'runtime.json';tmp.write_text(json.dumps(runtime,indent=2)+'\n');install(tmp,'runtime.json')
after['bytes']=sum(v['size']for v in after['files'].values());meta['cover_perf306']=dict(scope='GPU primary top-level surface and measured ART heap policy; unchanged Java/core/framework/boot/ART.',updated_files=updated)
assert after['symlinks']==before['symlinks'];assert all(v==after['files'][n]for n,v in before['files'].items()if n not in updated)
for p in (b/'source').rglob('*'):
 if p.is_file():assert sha(p)==nb['sources'][str(p.relative_to(b/'source'))]
(b/'overlay.json').write_text(json.dumps(meta,indent=2)+'\n');record=dict(passed=True,candidate='r306',payload=str(payload),updated_files=updated,files=len(after['files']),symlinks=len(after['symlinks']),copied_bytes=sum((payload/n).stat().st_size for n in updated),install_manifest_sha256=hashlib.sha256((json.dumps(after,indent=2)+'\n').encode()).hexdigest(),overlay_sha256=sha(b/'overlay.json'),scope='Candidate staging only, no functional acceptance.')
(b/'package.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2),flush=True)
