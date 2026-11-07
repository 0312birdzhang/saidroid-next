from pathlib import Path
import json,hashlib,copy,shutil,stat,os,tarfile
os.umask(0o022)
repo=Path('/media/psf/Home/WorkSpace/saidroid-next');b=repo/'build/evidence/qq-audio-properties293-20261102-v1';priorb=repo/'build/evidence/qq-manifest-receivers292-20261102-v1';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();proof=json.loads((priorb/'package.json').read_text());assert proof['passed'];prior=Path(proof['bundle']);assert sha(prior/'native-overlay.tar.gz')==proof['tarball_sha256'];before=json.loads((prior/'overlay.json').read_text());java=json.loads((b/'runtime-build.json').read_text());native=json.loads((b/'native-build.json').read_text());enc=json.loads((b/'encoded-build.json').read_text());source=json.loads((b/'sources.json').read_text());assert all(x['passed']for x in [java,native,enc]);assert java['baseline_classfiles_reproduced']and native['baseline_reproduced_byte_identical']and native['dynamic_symbols_unchanged']and enc['all_existing_hidden_api_flags_unchanged']and enc['all_new_members_implementation_private']
for n,v in source['sources'].items():assert sha(b/'source'/n)==v['source_sha256']and sha(repo/v['baseline_source'])==v['baseline_sha256']
workspace=Path('/var/tmp/saidroid-native-audio-properties293-v1');workspace.mkdir();payload=workspace/'payload';shutil.copytree(Path(proof['native_payload']),payload,copy_function=os.link);after=copy.deepcopy(before);updated=[]
def install(f,n,mode=0o644):
 target=payload/n;target.parent.mkdir(parents=True,exist_ok=True)
 if target.exists()or target.is_symlink():target.unlink()
 shutil.copyfile(f,target);target.chmod(mode);v=dict(sha256=sha(target),size=target.stat().st_size,mode=mode);after['changes'][n]=after['install_manifest']['files'][n]=v;updated.append(n)
encoded=Path(enc['encoded_root']);assert sha(encoded/'lib/runtime.jar')==enc['encoded_runtime_sha256'];install(encoded/'lib/runtime.jar','lib/runtime.jar');install(encoded/'manifest.json','share/build/hiddenapi-manifest.json');api=Path(native['candidate']);assert sha(api)==native['binary_sha256'];install(api,'lib/libsdhostapi.so')
for n in ['runtime-build.json','native-build.json','encoded-build.json','sources.json','build-runtime-v2-vm.py','build-native-v2-vm.py','encode-runtime-v2-vm.py','package-vm.py']:install(b/n,'share/build/audio-properties/'+n)
for parent in ['source','patches','test-source']:
 for f in sorted((b/parent).rglob('*')):
  if f.is_file():install(f,'share/build/audio-properties/'+str(f.relative_to(b)))
runtime=json.loads((payload/'runtime.json').read_text());runtime['hidden_api']['manifest_sha256']=enc['encoded_manifest_sha256'];runtime['audio_properties']=dict(schema='saidroid-host-audio-properties-v1',scope=source['scope'],runtime_build_sha256=sha(b/'runtime-build.json'),native_build_sha256=sha(b/'native-build.json'),source_sha256=sha(b/'sources.json'),sampling_rate='actual-default-pulseaudio-sink',primary_hal_frames='unavailable-null')
tmp=workspace/'runtime.json';tmp.write_text(json.dumps(runtime,indent=2)+'\n');install(tmp,'runtime.json');manifest=after['install_manifest'];manifest['bytes']=sum(v['size']for v in manifest['files'].values());after['audio_properties_overlay']=dict(schema='saidroid-host-audio-properties-overlay-v1',baseline_sha256=proof['tarball_sha256'],updated_files=updated,core_framework_boot_art_host_other_native_unchanged=True)
assert manifest['symlinks']==before['install_manifest']['symlinks']and set(before['install_manifest']['files'])<=set(manifest['files'])
for n,v in before['install_manifest']['files'].items():
 if n not in updated:assert manifest['files'][n]==v
for n,v in after['changes'].items():assert sha(payload/n)==v['sha256']and stat.S_IMODE((payload/n).stat().st_mode)==v['mode']
bundle=b/'bundle';bundle.mkdir();(bundle/'overlay.json').write_text(json.dumps(after,indent=2)+'\n')
with tarfile.open(bundle/'native-overlay.tar.gz.pending','w:gz',dereference=True)as t:t.add(payload,arcname='payload');t.add(bundle/'overlay.json',arcname='overlay.json')
with tarfile.open(bundle/'native-overlay.tar.gz.pending','r:gz')as t:assert all(v.isfile()or v.isdir()for v in t.getmembers())and sum(v.isfile()for v in t.getmembers())==len(after['changes'])+1
(bundle/'native-overlay.tar.gz.pending').replace(bundle/'native-overlay.tar.gz');r=dict(passed=True,bundle=str(bundle),native_payload=str(payload),tarball_sha256=sha(bundle/'native-overlay.tar.gz'),overlay_sha256=sha(bundle/'overlay.json'),files=len(manifest['files']),symlinks=len(manifest['symlinks']),updated_files=updated,core_framework_boot_art_host_other_native_unchanged=True);(b/'package.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2),flush=True)
