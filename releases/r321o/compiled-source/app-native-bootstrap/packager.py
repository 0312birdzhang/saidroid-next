from pathlib import Path
import json,hashlib,copy,shutil,stat,os,tarfile
repo=Path('/media/psf/Home/WorkSpace/saidroid-next');b=repo/'build/evidence/qq-bootstrap290-20261102-v1';prior=Path('/var/tmp/saidroid-native-icmp-cleanup-20261101-r286-v1/bundle');module=Path('/var/tmp/saidroid-app-native-bootstrap290-v2');root=Path('/var/tmp/saidroid-icmp-cleanup286-v1-formal-vm-component/root');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();proof=json.loads((repo/'build/evidence/cts-frame-repair-20261031/r286-icmp-cleanup-v1-package-boundary.json').read_text());assert sha(prior/'native-overlay.tar.gz')==proof['tarball_sha256'];before=json.loads((prior/'overlay.json').read_text());assert before['schema']=='saildroid-native-overlay-v3';assert json.loads((root/'install-manifest.json').read_text())==before['install_manifest'];assert sha(root/'install-manifest.json')=='9aa6f703fdcc97cca848357aacc6727b85d5d55ae48084c778a007c4937dd505'
build=json.loads((b/'runtime-build.json').read_text());assert build['passed']and build['core_framework_boot_inputs_unchanged']and build['new_members']==[];encoded=Path(build['encoded_root']);assert sha(encoded/'lib/runtime.jar')==build['encoded_runtime_sha256'];assert sha(encoded/'manifest.json')==build['encoded_manifest_sha256']
workspace=Path('/var/tmp/saidroid-native-bootstrap290-v1');workspace.mkdir();payload=workspace/'payload';shutil.copytree(prior/'payload',payload,copy_function=os.link);after=copy.deepcopy(before);updated=[]
def install(f,n,mode=0o644):
 target=payload/n;target.parent.mkdir(parents=True,exist_ok=True)
 if target.exists()or target.is_symlink():target.unlink()
 shutil.copyfile(f,target);target.chmod(mode);v=dict(sha256=sha(target),size=target.stat().st_size,mode=mode);after['changes'][n]=after['install_manifest']['files'][n]=v;updated.append(n)
install(encoded/'lib/runtime.jar','lib/runtime.jar');install(encoded/'manifest.json','share/build/hiddenapi-manifest.json')
for f,n in [(b/'source/SdRuntime.java','SdRuntime.java'),(b/'source/SdRuntime.java.before','SdRuntime.java.before'),(b/'source/SdRuntime.patch','SdRuntime.patch'),(b/'source/sources.json','sources.json'),(b/'runtime-build.json','build.json'),(b/'build-runtime-v2-vm.py','builder.py'),(b/'encode-runtime-v3-vm.py','encoder.py'),(Path(__file__),'packager.py')]:install(f,'share/build/app-native-bootstrap/'+n)
runtime=json.loads((prior/'payload/runtime.json').read_text());runtime['hidden_api']['manifest_sha256']=build['encoded_manifest_sha256'];runtime['app_native_bootstrap']=dict(schema='saidroid-app-native-bootstrap-v1',runtime_source_sha256=build['source']['variant_sha256'],build_manifest_sha256=sha(b/'runtime-build.json'),app_specific_preload=False,public_app_native_loading=True,core_sdk_guard_unchanged=True)
tmp=workspace/'runtime.json';tmp.write_text(json.dumps(runtime,indent=2)+'\n');install(tmp,'runtime.json')
manifest=after['install_manifest'];manifest['bytes']=sum(v['size']for v in manifest['files'].values());after['app_native_bootstrap_overlay']=dict(schema='saidroid-app-native-bootstrap-overlay-v1',baseline_tarball_sha256=proof['tarball_sha256'],baseline_component_manifest_sha256=sha(root/'install-manifest.json'),build_manifest_sha256=sha(b/'runtime-build.json'),updated_files=updated,all_native_core_framework_boot_cli_manager_files_unchanged=True,phone_staged=False)
assert set(before['install_manifest']['files'])<=set(manifest['files']);assert manifest['symlinks']==before['install_manifest']['symlinks']
for n,v in before['install_manifest']['files'].items():
 if n not in updated:assert manifest['files'][n]==v
for n,v in after['changes'].items():assert sha(payload/n)==v['sha256']and stat.S_IMODE((payload/n).stat().st_mode)==v['mode']
for key in ['predecessor','predecessor_manifest_sha256','product_manifest','remove_files','ca_alias_cleanup','release_file_cleanup']:assert before[key]==after[key]
bundle=b/'bundle';bundle.mkdir();(bundle/'overlay.json').write_text(json.dumps(after,indent=2)+'\n')
with tarfile.open(bundle/'native-overlay.tar.gz.pending','w:gz',dereference=True)as t:t.add(payload,arcname='payload');t.add(bundle/'overlay.json',arcname='overlay.json')
with tarfile.open(bundle/'native-overlay.tar.gz.pending','r:gz')as t:
 members=t.getmembers();assert all(v.isfile()or v.isdir()for v in members);assert sum(v.isfile()for v in members)==len(after['changes'])+1
(bundle/'native-overlay.tar.gz.pending').replace(bundle/'native-overlay.tar.gz')
r=dict(passed=True,bundle=str(bundle),native_payload=str(payload),tarball_sha256=sha(bundle/'native-overlay.tar.gz'),overlay_sha256=sha(bundle/'overlay.json'),files=len(manifest['files']),symlinks=len(manifest['symlinks']),updated_files=updated,core_boot_native_unchanged=True,old_frozen_source_unchanged=sha(repo/build['source']['baseline_source'])==build['source']['baseline_sha256'],disk_free=shutil.disk_usage('/var/tmp').free)
(b/'package.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2),flush=True)
