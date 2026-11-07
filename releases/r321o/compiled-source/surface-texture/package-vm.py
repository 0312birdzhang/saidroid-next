from pathlib import Path
import json,hashlib,copy,shutil,stat,os,tarfile
os.umask(0o022)
r=Path('/media/psf/Home/WorkSpace/saidroid-next');b=r/'build/evidence/qq-surface-texture300-20261102-v1';priorb=r/'build/evidence/qq-audio-sco294-20261102-v1';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();proof=json.loads((priorb/'package.json').read_text());assert proof['passed'];prior=Path(proof['bundle']);assert sha(prior/'native-overlay.tar.gz')==proof['tarball_sha256'];before=json.loads((prior/'overlay.json').read_text());java=json.loads((b/'runtime-build.json').read_text());native=json.loads((b/'native-build.json').read_text());enc=json.loads((b/'encoded-build.json').read_text());source=json.loads((b/'sources.json').read_text());assert all(x['passed']for x in [java,native,enc]);assert native['output']=='/var/tmp/saidroid-surface-texture300-native-v4';assert native['baseline_host29_byte_identical']and native['baseline_host_byte_identical']and enc['all_existing_hidden_api_flags_unchanged']and enc['core_framework_boot_jars_byte_unchanged']
for n,v in source['sources'].items():assert sha(b/'source'/n)==v['source_sha256']and sha(r/v['baseline_source'])==v['baseline_sha256']
for n,h in native['sources'].items():assert sha(r/n)==h
workspace=Path('/var/tmp/saidroid-native-surface-texture300-v1');workspace.mkdir();payload=workspace/'payload';shutil.copytree(Path(proof['native_payload']),payload,copy_function=os.link);after=copy.deepcopy(before);updated=[]
def install(f,n,mode=0o644):
 target=payload/n;target.parent.mkdir(parents=True,exist_ok=True)
 if target.exists()or target.is_symlink():target.unlink()
 shutil.copyfile(f,target);target.chmod(mode);v=dict(sha256=sha(target),size=target.stat().st_size,mode=mode);after['changes'][n]=after['install_manifest']['files'][n]=v;updated.append(n)
encoded=Path(enc['encoded_root']);assert sha(encoded/'lib/runtime.jar')==enc['encoded_runtime_sha256'];install(encoded/'lib/runtime.jar','lib/runtime.jar');install(encoded/'manifest.json','share/build/hiddenapi-manifest.json')
for name,path,mode in [('libsdtexture-host.so','lib/libsdtexture-host.so',0o644),('libsdtexture-android.so','android-libs/libsdtexture-android.so',0o644),('libsdhost29.so','lib/libsdhost29.so',0o644),('saildroid-host','libexec/saildroid-host',0o755)]:
 p=Path(native['output'])/name;assert sha(p)==native['files'][name];install(p,path,mode)
for n in ['runtime-build.json','native-build.json','encoded-build.json','sources.json','build-runtime-vm.py','build-native-v4-vm.py','encode-runtime-vm.py','package-vm.py']:install(b/n,'share/build/surface-texture/'+n)
for parent in ['source','test-source']:
 for f in sorted((b/parent).rglob('*')):
  if f.is_file():install(f,'share/build/surface-texture/'+str(f.relative_to(b)))
for f in sorted((r/'native/graphics/surface-texture-owned-release').glob('*')):
 if f.is_file():install(f,'share/build/surface-texture/native/'+f.name)
runtime=json.loads((payload/'runtime.json').read_text());runtime['hidden_api']['manifest_sha256']=enc['encoded_manifest_sha256'];runtime['surface_texture']=dict(schema='saidroid-surface-texture-v1',scope=source['scope'],runtime_build_sha256=sha(b/'runtime-build.json'),native_build_sha256=sha(b/'native-build.json'),source_sha256=sha(b/'sources.json'),validation='candidate-not-yet-accepted')
tmp=workspace/'runtime.json';tmp.write_text(json.dumps(runtime,indent=2)+'\n');install(tmp,'runtime.json');manifest=after['install_manifest'];manifest['bytes']=sum(v['size']for v in manifest['files'].values());after['surface_texture_overlay']=dict(schema='saidroid-surface-texture-overlay-v1',baseline_sha256=proof['tarball_sha256'],updated_files=updated,core_framework_boot_art_unchanged=True)
assert manifest['symlinks']==before['install_manifest']['symlinks']and set(before['install_manifest']['files'])<=set(manifest['files'])
for n,v in before['install_manifest']['files'].items():
 if n not in updated:assert manifest['files'][n]==v
for n,v in after['changes'].items():assert sha(payload/n)==v['sha256']and stat.S_IMODE((payload/n).stat().st_mode)==v['mode']
bundle=b/'bundle';bundle.mkdir();(bundle/'overlay.json').write_text(json.dumps(after,indent=2)+'\n')
with tarfile.open(bundle/'native-overlay.tar.gz.pending','w:gz',dereference=True)as t:t.add(payload,arcname='payload');t.add(bundle/'overlay.json',arcname='overlay.json')
with tarfile.open(bundle/'native-overlay.tar.gz.pending','r:gz')as t:assert all(v.isfile()or v.isdir()for v in t.getmembers())and sum(v.isfile()for v in t.getmembers())==len(after['changes'])+1
(bundle/'native-overlay.tar.gz.pending').replace(bundle/'native-overlay.tar.gz');record=dict(passed=True,scope='Candidate packaging only; no functional acceptance.',bundle=str(bundle),native_payload=str(payload),tarball_sha256=sha(bundle/'native-overlay.tar.gz'),overlay_sha256=sha(bundle/'overlay.json'),files=len(manifest['files']),symlinks=len(manifest['symlinks']),updated_files=updated,core_framework_boot_art_unchanged=True);(b/'package.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2),flush=True)
