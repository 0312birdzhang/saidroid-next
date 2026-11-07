from pathlib import Path
import os,copy,json,hashlib,shutil,tarfile,stat
os.umask(0o022)
b=Path(__file__).parent;r=b.parents[2];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();prior=json.loads((r/'build/evidence/qq-strerror302-20261103-v1/package.json').read_text());native=json.loads((b/'native-build.json').read_text());assert prior['passed']and native['passed']
old=Path(prior['bundle']);assert sha(old/'native-overlay.tar.gz')==prior['tarball_sha256'];before=json.loads((old/'overlay.json').read_text());after=copy.deepcopy(before);workspace=Path('/var/tmp/saidroid-native-camera304-v1');workspace.mkdir();payload=workspace/'payload';shutil.copytree(Path(prior['native_payload']),payload,copy_function=os.link);updated=[]
def install(f,n):
 p=payload/n;p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():p.unlink()
 shutil.copyfile(f,p);p.chmod(0o644);v=dict(sha256=sha(p),size=p.stat().st_size,mode=0o644);after['changes'][n]=after['install_manifest']['files'][n]=v;updated.append(n)
p=Path(native['output'])/'libsdhostapi.so';assert sha(p)==native['candidate_sha256'];install(p,'lib/libsdhostapi.so')
for p in (r/'native/compat/camera-capability').glob('*'):
 if p.is_file():install(p,'share/build/camera-capability/'+p.name)
for n in ['native-build.json','build-vm.py','package-vm.py']:install(b/n,'share/build/camera-capability/'+n)
install(b/'source/host-audio.cpp','share/build/camera-capability/host-audio.cpp');manifest=after['install_manifest'];manifest['bytes']=sum(v['size']for v in manifest['files'].values());after['camera_capability_overlay']=dict(baseline_sha256=prior['tarball_sha256'],updated_files=updated,scope='Empty exposed Android camera inventory consistent with absent PackageManager camera features; explicit unsupported capture.')
for n,v in before['install_manifest']['files'].items():
 if n not in updated:assert manifest['files'][n]==v
for n,v in after['changes'].items():assert sha(payload/n)==v['sha256']
bundle=b/'bundle';bundle.mkdir();(bundle/'overlay.json').write_text(json.dumps(after,indent=2)+'\n')
with tarfile.open(bundle/'native-overlay.tar.gz.pending','w:gz',dereference=True)as t:t.add(payload,arcname='payload');t.add(bundle/'overlay.json',arcname='overlay.json')
(bundle/'native-overlay.tar.gz.pending').replace(bundle/'native-overlay.tar.gz');v=dict(passed=True,bundle=str(bundle),native_payload=str(payload),tarball_sha256=sha(bundle/'native-overlay.tar.gz'),files=len(manifest['files']),symlinks=len(manifest['symlinks']),updated_files=updated,scope='Packaging only; no QQ acceptance yet.');(b/'package.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v,indent=2),flush=True)
