from pathlib import Path
import json,hashlib,copy,shutil,stat,os,tarfile
os.umask(0o022)
repo=Path('/media/psf/Home/WorkSpace/saidroid-next');b=repo/'build/evidence/qq-manifest-receivers292-20261102-v1';priorb=repo/'build/evidence/qq-signal-stack291-20261102-v1';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();proof=json.loads((priorb/'package.json').read_text());assert proof['passed'];prior=Path(proof['bundle']);assert sha(prior/'native-overlay.tar.gz')==proof['tarball_sha256'];before=json.loads((prior/'overlay.json').read_text())
runtimebuild=json.loads((b/'runtime-build.json').read_text());native=json.loads((b/'native-build.json').read_text());encoded=json.loads((b/'encoded-build.json').read_text());assert runtimebuild['passed']and native['passed']and encoded['passed'];assert runtimebuild['baseline_classfiles_reproduced']and native['baseline_reproduced_byte_identical']and encoded['all_existing_hidden_api_flags_unchanged']and encoded['all_new_members_implementation_private']and encoded['core_framework_boot_jars_byte_unchanged']
source=json.loads((b/'sources.json').read_text())
for n,v in source['sources'].items():assert sha(b/'source'/n)==v['source_sha256']
workspace=Path('/var/tmp/saidroid-native-manifest-receivers292-v1');workspace.mkdir();payload=workspace/'payload';shutil.copytree(Path(proof['native_payload']),payload,copy_function=os.link);after=copy.deepcopy(before);updated=[]
def install(f,n,mode=0o644):
 target=payload/n;target.parent.mkdir(parents=True,exist_ok=True)
 if target.exists()or target.is_symlink():target.unlink()
 shutil.copyfile(f,target);target.chmod(mode);v=dict(sha256=sha(target),size=target.stat().st_size,mode=mode);after['changes'][n]=after['install_manifest']['files'][n]=v;updated.append(n)
enc=Path(encoded['encoded_root']);assert sha(enc/'lib/runtime.jar')==encoded['encoded_runtime_sha256'];install(enc/'lib/runtime.jar','lib/runtime.jar');install(enc/'manifest.json','share/build/hiddenapi-manifest.json')
for name,path,mode in [('saildroid-host','libexec/saildroid-host',0o755),('libsdhostapi.so','lib/libsdhostapi.so',0o644)]:
 f=Path(native['candidate'])/name;assert sha(f)==native['binary_sha256'][name];install(f,path,mode)
for n in ['runtime-build.json','native-build.json','encoded-build.json','sources.json','build-runtime-v3-vm.py','build-native-v3-vm.py','encode-runtime-vm.py','package-vm.py','baseline-host-manifest.json','baseline-host-entry.cpp']:install(b/n,'share/build/manifest-receivers/'+n)
for parent in ['source','patches','test-source']:
 for f in sorted((b/parent).rglob('*')):
  if f.is_file():install(f,'share/build/manifest-receivers/'+str(f.relative_to(b)))
runtime=json.loads((payload/'runtime.json').read_text());runtime['hidden_api']['manifest_sha256']=encoded['encoded_manifest_sha256'];runtime['manifest_receivers']=dict(schema='saidroid-manifest-receivers-v1',scope=source['scope'],runtime_build_sha256=sha(b/'runtime-build.json'),native_build_sha256=sha(b/'native-build.json'),source_manifest_sha256=sha(b/'sources.json'),explicit_unordered_same_apk=True,implicit_manifest_ordered_sticky_unsupported=True)
tmp=workspace/'runtime.json';tmp.write_text(json.dumps(runtime,indent=2)+'\n');install(tmp,'runtime.json')
manifest=after['install_manifest'];manifest['bytes']=sum(v['size']for v in manifest['files'].values());after['manifest_receivers_overlay']=dict(schema='saidroid-manifest-receivers-overlay-v1',baseline_tarball_sha256=proof['tarball_sha256'],updated_files=updated,core_framework_boot_art_other_native_bytes_unchanged=True)
assert set(before['install_manifest']['files'])<=set(manifest['files'])and manifest['symlinks']==before['install_manifest']['symlinks']
for n,v in before['install_manifest']['files'].items():
 if n not in updated:assert manifest['files'][n]==v
for n,v in after['changes'].items():assert sha(payload/n)==v['sha256']and stat.S_IMODE((payload/n).stat().st_mode)==v['mode']
for key in ['predecessor','predecessor_manifest_sha256','product_manifest','remove_files','ca_alias_cleanup','release_file_cleanup']:assert before[key]==after[key]
bundle=b/'bundle';bundle.mkdir();(bundle/'overlay.json').write_text(json.dumps(after,indent=2)+'\n')
with tarfile.open(bundle/'native-overlay.tar.gz.pending','w:gz',dereference=True)as t:t.add(payload,arcname='payload');t.add(bundle/'overlay.json',arcname='overlay.json')
with tarfile.open(bundle/'native-overlay.tar.gz.pending','r:gz')as t:assert all(v.isfile()or v.isdir()for v in t.getmembers())and sum(v.isfile()for v in t.getmembers())==len(after['changes'])+1
(bundle/'native-overlay.tar.gz.pending').replace(bundle/'native-overlay.tar.gz')
r=dict(passed=True,bundle=str(bundle),native_payload=str(payload),tarball_sha256=sha(bundle/'native-overlay.tar.gz'),overlay_sha256=sha(bundle/'overlay.json'),files=len(manifest['files']),symlinks=len(manifest['symlinks']),updated_files=updated,core_framework_boot_art_other_native_unchanged=True)
(b/'package.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2),flush=True)
