from pathlib import Path
import os,copy,json,hashlib,shutil,tarfile,stat
os.umask(0o022)
b=Path(__file__).parent;r=b.parents[2];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();prior=json.loads((r/'build/evidence/qq-pending-intent301-20261102-v1/package.json').read_text());native=json.loads((b/'native-build.json').read_text());assert prior['passed']and native['passed']and json.loads((b/'vm-fixture-results.json').read_text())[1]['passed']
old=Path(prior['bundle']);assert sha(old/'native-overlay.tar.gz')==prior['tarball_sha256'];before=json.loads((old/'overlay.json').read_text());after=copy.deepcopy(before);workspace=Path('/var/tmp/saidroid-native-strerror302-v1');workspace.mkdir();payload=workspace/'payload';shutil.copytree(Path(prior['native_payload']),payload,copy_function=os.link);updated=[]
def install(f,n):
 p=payload/n;p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():p.unlink()
 shutil.copyfile(f,p);p.chmod(0o644);v=dict(sha256=sha(p),size=p.stat().st_size,mode=0o644);after['changes'][n]=after['install_manifest']['files'][n]=v;updated.append(n)
p=Path(native['output'])/'libsdhost29.so';assert sha(p)==native['candidate_sha256'];install(p,'lib/libsdhost29.so')
for p in (r/'native/compat/strerror-api29').glob('*'):
 if p.is_file():install(p,'share/build/strerror-api29/'+p.name)
for n in ['native-build.json','vm-fixture-results.json','build-vm.py','package-vm.py','test-vm.py']:install(b/n,'share/build/strerror-api29/'+n)
manifest=after['install_manifest'];manifest['bytes']=sum(v['size']for v in manifest['files'].values());after['strerror_api29_overlay']=dict(baseline_sha256=prior['tarball_sha256'],updated_files=updated,scope='API29 strerror_r integer return / errno / caller buffer contract; Android 10 English error table.')
for n,v in before['install_manifest']['files'].items():
 if n not in updated:assert manifest['files'][n]==v
for n,v in after['changes'].items():assert sha(payload/n)==v['sha256']
bundle=b/'bundle';bundle.mkdir();(bundle/'overlay.json').write_text(json.dumps(after,indent=2)+'\n')
with tarfile.open(bundle/'native-overlay.tar.gz.pending','w:gz',dereference=True)as t:t.add(payload,arcname='payload');t.add(bundle/'overlay.json',arcname='overlay.json')
(bundle/'native-overlay.tar.gz.pending').replace(bundle/'native-overlay.tar.gz');v=dict(passed=True,bundle=str(bundle),native_payload=str(payload),tarball_sha256=sha(bundle/'native-overlay.tar.gz'),files=len(manifest['files']),symlinks=len(manifest['symlinks']),updated_files=updated,scope='Packaging only; no QQ acceptance yet.');(b/'package.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v,indent=2),flush=True)
