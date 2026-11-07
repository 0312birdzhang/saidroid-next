from pathlib import Path
import json,hashlib,copy,shutil,stat,os,tarfile
repo=Path('/media/psf/Home/WorkSpace/saidroid-next');b=repo/'build/evidence/qq-signal-stack291-20261102-v1';priorb=repo/'build/evidence/qq-bootstrap290-20261102-v1';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
proof=json.loads((priorb/'package.json').read_text());assert proof['passed'];prior=Path(proof['bundle']);assert sha(prior/'native-overlay.tar.gz')==proof['tarball_sha256'];before=json.loads((prior/'overlay.json').read_text());assert before['schema']=='saildroid-native-overlay-v3'
build=json.loads((b/'art-build.json').read_text());test=json.loads((b/'ownership-contract-v5.json').read_text());assert build['passed']and build['baseline_reproduced_byte_identical']and build['dynamic_abi_unchanged']and build['vm_original_sources_objects_restored']and test['passed'];art=Path('/var/tmp/saidroid-art291-host-signal-stack-ownership-v1/libart.so');assert sha(art)==build['binary_sha256']
workspace=Path('/var/tmp/saidroid-native-stack-ownership291-v1');workspace.mkdir();payload=workspace/'payload';shutil.copytree(Path(proof['native_payload']),payload,copy_function=os.link);after=copy.deepcopy(before);updated=[]
def install(f,n,mode=0o644):
 target=payload/n;target.parent.mkdir(parents=True,exist_ok=True)
 if target.exists()or target.is_symlink():target.unlink()
 shutil.copyfile(f,target);target.chmod(mode);v=dict(sha256=sha(target),size=target.stat().st_size,mode=mode);after['changes'][n]=after['install_manifest']['files'][n]=v;updated.append(n)
assert before['install_manifest']['files']['lib/libart.so']['sha256']==build['baseline_binary_sha256']
install(art,'lib/libart.so')
for f,n in [(repo/'native/compat/art-host-signal-stack-ownership/thread_linux.cc','thread_linux.cc'),(repo/'native/compat/art-host-signal-stack-ownership/ownership.patch','ownership.patch'),(repo/'native/compat/art-host-signal-stack-ownership/sources.json','sources.json'),(b/'art-build.json','build.json'),(b/'build-art-vm.py','builder.py'),(b/'ownership-contract-v5.json','contract.json'),(repo/'scripts/api29/tests/signal-stack-ownership/unmap-observer.c','unmap-observer.c'),(repo/'scripts/api29/tests/signal-stack-ownership/ownership.c','ownership.c'),(repo/'scripts/api29/tests/signal-stack-ownership/ArtSignalStackOwnership.java','ArtSignalStackOwnership.java'),(b/'run-ownership-v5-vm.py','test-builder.py'),(Path(__file__),'packager.py')]:install(f,'share/build/art-host-signal-stack-ownership/'+n)
runtime=json.loads((payload/'runtime.json').read_text());runtime['art_host_signal_stack_ownership']=dict(schema='saidroid-art-host-stack-ownership-v1',binary_sha256=build['binary_sha256'],build_manifest_sha256=sha(b/'art-build.json'),source_manifest_sha256=build['source_meta_sha256'],contract_sha256=sha(b/'ownership-contract-v5.json'),dynamic_abi_unchanged=True)
tmp=workspace/'runtime.json';tmp.write_text(json.dumps(runtime,indent=2)+'\n');install(tmp,'runtime.json')
manifest=after['install_manifest'];manifest['bytes']=sum(v['size']for v in manifest['files'].values());after['art_host_signal_stack_ownership_overlay']=dict(schema='saidroid-art-host-stack-ownership-overlay-v1',baseline_tarball_sha256=proof['tarball_sha256'],build_manifest_sha256=sha(b/'art-build.json'),updated_files=updated,all_other_native_core_framework_boot_files_unchanged=True)
assert set(before['install_manifest']['files'])<=set(manifest['files'])and manifest['symlinks']==before['install_manifest']['symlinks']
for n,v in before['install_manifest']['files'].items():
 if n not in updated:assert manifest['files'][n]==v
for n,v in after['changes'].items():assert sha(payload/n)==v['sha256']and stat.S_IMODE((payload/n).stat().st_mode)==v['mode']
for key in ['predecessor','predecessor_manifest_sha256','product_manifest','remove_files','ca_alias_cleanup','release_file_cleanup']:assert before[key]==after[key]
bundle=b/'bundle';bundle.mkdir();(bundle/'overlay.json').write_text(json.dumps(after,indent=2)+'\n')
with tarfile.open(bundle/'native-overlay.tar.gz.pending','w:gz',dereference=True)as t:t.add(payload,arcname='payload');t.add(bundle/'overlay.json',arcname='overlay.json')
with tarfile.open(bundle/'native-overlay.tar.gz.pending','r:gz')as t:assert all(v.isfile()or v.isdir()for v in t.getmembers())and sum(v.isfile()for v in t.getmembers())==len(after['changes'])+1
(bundle/'native-overlay.tar.gz.pending').replace(bundle/'native-overlay.tar.gz')
r=dict(passed=True,bundle=str(bundle),native_payload=str(payload),tarball_sha256=sha(bundle/'native-overlay.tar.gz'),overlay_sha256=sha(bundle/'overlay.json'),files=len(manifest['files']),symlinks=len(manifest['symlinks']),updated_files=updated,other_native_core_framework_boot_unchanged=True,contract_sha256=sha(b/'ownership-contract-v5.json'))
(b/'package.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2),flush=True)
