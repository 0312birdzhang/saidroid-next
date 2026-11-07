#!/usr/bin/env python3
"""Package original HIDL JNI registrations over an exact V3 private component."""
from pathlib import Path
import argparse,copy,hashlib,json,os,shutil,stat,subprocess,tarfile
p=argparse.ArgumentParser(description=__doc__)
for n in ['baseline','native','output']:p.add_argument('--'+n,type=Path,required=True)
p.add_argument('--expected-baseline-sha256',required=True);a=p.parse_args();os.umask(0o022);repo=Path(__file__).resolve().parents[2];b=repo/'build/evidence/cts-frame-repair-20261031';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(a.baseline/'native-overlay.tar.gz')==a.expected_baseline_sha256
before=json.loads((a.baseline/'overlay.json').read_text());assert before['schema']=='saildroid-native-overlay-v3'and before['api']==29;oldroot=a.baseline/'payload';full=before['install_manifest']
for n,v in before['changes'].items():
 f=oldroot/n;assert not Path(n).is_absolute()and'..'not in Path(n).parts
 assert f.is_file()and not f.is_symlink()and sha(f)==v['sha256']and f.stat().st_size==v['size']and stat.S_IMODE(f.stat().st_mode)==v['mode']and full['files'][n]==v
build=json.loads((a.native/'manifest.json').read_text());builder=repo/'native/compat/build-hwbinder-jni-vm.py';owned=repo/'native/compat/hwbinder-jni';meta=json.loads((owned/'sources.json').read_text())
assert build['schema']=='saildroid-hwbinder-jni-v1'and build['passed']and all(build[k]for k in ['existing_dynamic_symbols_identical','needed_identical','original_inputs_unchanged'])
assert sha(builder)==build['builder_sha256']and sha(owned/'sources.json')==build['source_meta_sha256']and sha(owned/'api29-jni-entries.inc')==build['prepared_entries_sha256']
assert sha(a.native/'libsdbridge.so')==build['library_sha256']and build['baseline_library_sha256']==full['files']['lib/libsdbridge.so']['sha256']
assert all(sha(Path(n))==h for n,h in build['original_inputs'].items())
assert all(sha(repo/n)==v['sha256']for n,v in meta['canonical_references'].items())
proofnames=['original-hwbinder228-selected-v2-audit.json','original-hwbinder228-selected-v2.json','hwbinder228-own-contract-v2.json','hwbinder228-pid-native-policy-v1.json'];proofs=[b/n for n in proofnames];paired,raw,own,pid=[json.loads(p.read_text())for p in proofs]
assert paired['passed']and paired['selected_original_methods']==6 and paired['before_failed']==paired['after_passed']==6 and paired['before_passed']==paired['after_failed']==0 and not paired['full_class_or_module_passed']and not paired['phone_executed']and paired['hardware_service_manager_test_unrun']
assert paired['source_record_sha256']==sha(proofs[1])and paired['exact_new_bridge_sha256']==build['library_sha256']and raw['native_manifest_sha256']==sha(a.native/'manifest.json')
assert own['passed']and own['native_manifest_sha256']==sha(a.native/'manifest.json')and own['contract_source_sha256']==sha(repo/'scripts/api29/tests/hwbinder/HwBinderJniContract.java')
row=next(r for r in own['results']if r['runtime']=='hwbinder228');assert row['passed']and row['checks']==964 and row['uid']==65534 and row['actual_bridge_sha256']==build['library_sha256']
for proof in [raw,row]:
 assert proof['actual_art_sha256']==full['files']['lib/libart.so']['sha256']and proof['actual_javacore_sha256']==full['files']['lib/libjavacore.so']['sha256']and proof['actual_native_host_sha256']==full['files']['lib/libsdhost29.so']['sha256']
assert len(pid)==1 and sha(Path(pid[0]['path']))==pid[0]['sha256']and '<getpid@plt>'in pid[0]['disassembly']
assert raw['component_manifest_sha256']==sha(Path('/var/tmp/saidroid-deployment225-v1-formal-vm-component/root/install-manifest.json'))
assert not a.output.exists();a.output.mkdir(parents=True);root=a.output/'payload';shutil.copytree(oldroot,root);root.chmod(0o755)
for d in root.rglob('*'):
 if d.is_dir()and not d.is_symlink():d.chmod(0o755)
after=copy.deepcopy(before);manifest,changes,updated=after['install_manifest'],after['changes'],[]
def install(f,n,mode=0o644):
 t=root/n;t.parent.mkdir(parents=True,exist_ok=True);assert not t.is_symlink();shutil.copyfile(f,t);t.chmod(mode);v=dict(sha256=sha(t),size=t.stat().st_size,mode=mode);manifest['files'][n]=changes[n]=v;updated.append(n)
def generated(value,n):
 t=a.output/'metadata.pending.json';t.write_text(json.dumps(value,indent=2)+'\n');install(t,n);t.unlink()
install(a.native/'libsdbridge.so','lib/libsdbridge.so',full['files']['lib/libsdbridge.so']['mode'])
for f,n in [(a.native/'manifest.json','native-manifest.json'),(builder,'builder.py'),(Path(__file__),'packager.py'),(owned/'sources.json','sources.json'),(owned/'api29-jni-entries.inc','api29-jni-entries.inc'),(a.native/'source/scripts/device/sdbridge.c','prepared-sdbridge.c'),(repo/'scripts/api29/tests/hwbinder/HwBinderJniContract.java','tests/HwBinderJniContract.java')]:install(f,'share/build/hwbinder-jni/'+n)
for f in proofs:install(f,'share/build/hwbinder-jni/evidence/'+f.name)
for n in meta['canonical_references']:install(repo/n,'share/build/hwbinder-jni/references/'+Path(n).name)
runtime=json.loads((oldroot/'runtime.json').read_text());runtime['hidl_jni']=dict(schema=build['schema'],scope=build['scope'],native_manifest_sha256=sha(a.native/'manifest.json'),libsdbridge_sha256=build['library_sha256'],previous_registration_count=100,registration_count=104,added_original_registrations=meta['added_symbols'],selected_original_vm_methods=6,selected_original_vm_passed=6,own_vm_checks=964,hardware_service_manager_unrun=True,full_class_or_module_passed=False,phone_staged=False)
generated(runtime,'runtime.json');manifest['bytes']=sum(v['size']for v in manifest['files'].values());assert manifest['symlinks']==full['symlinks']and set(full['files'])<=set(manifest['files'])and all(manifest['files'][n]==v for n,v in full['files'].items()if n not in updated)
assert all(after[k]==v for k,v in before.items()if k not in ['install_manifest','changes'])
assert all(sha(root/n)==v['sha256']and stat.S_IMODE((root/n).stat().st_mode)==v['mode']for n,v in changes.items())
after['hidl_jni_overlay']=dict(schema='saildroid-hidl-jni-overlay-v1',baseline_archive_sha256=a.expected_baseline_sha256,updated_files=sorted(updated),all_other_core_images_ART_hostshim_JNI_framework_media_manager_trust_bytes_unchanged=True,existing_dynamic_symbols_identical=True,phone_staged=False)
(a.output/'overlay.json').write_text(json.dumps(after,indent=2)+'\n')
with tarfile.open(a.output/'native-overlay.tar.gz.pending','w:gz')as archive:archive.add(root,arcname='payload');archive.add(a.output/'overlay.json',arcname='overlay.json')
assert sha(a.baseline/'native-overlay.tar.gz')==a.expected_baseline_sha256 and sha(a.native/'libsdbridge.so')==build['library_sha256']and sha(builder)==build['builder_sha256']and sha(owned/'sources.json')==build['source_meta_sha256']
(a.output/'native-overlay.tar.gz.pending').replace(a.output/'native-overlay.tar.gz');print('HIDL_JNI_OVERLAY=packaged|sha256='+sha(a.output/'native-overlay.tar.gz')+'|phone_staged=false')
