from pathlib import Path
import os,subprocess,hashlib,json,shutil,zipfile,importlib.util
repo=Path('/media/psf/Home/WorkSpace/saidroid-next');b=repo/'build/evidence/qq-bootstrap290-20261102-v1';base=Path('/var/tmp/saidroid-crypto-provider-alias277-runtime-v1');component=Path('/var/tmp/saidroid-icmp-cleanup286-v1-formal-vm-component/root');out=Path('/var/tmp/saidroid-app-native-bootstrap290-v2');out.mkdir();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();meta=json.loads((base/'manifest.json').read_text());assert meta['passed']and sha(base/'runtime.jar')==meta['runtime_sha256']=='31c90a3f6a8b3cd975661740a03ec2b468e173e63eb18719d30a90d96cf57dac'
source=json.loads((b/'source/sources.json').read_text());assert sha(repo/source['baseline_source'])==source['baseline_sha256']and sha(b/'source/SdRuntime.java')==source['variant_sha256']
java=Path('/tmp/jdkfull/jdk-21.0.13+9/bin');inputs=repo/'build/codex-api29/inputs';fw=inputs/'android-all-10-robolectric-5803371.jar';r8=inputs/'r8-8.3.37.jar';commands=[]
def run(c,n):
 commands.append(c)
 with(out/n).open('ab',buffering=0)as f:subprocess.run(c,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=90)
def entries(p):
 with zipfile.ZipFile(p)as z:return {n:z.read(n)for n in z.namelist()}
before={str(p.relative_to(base/'classes')):sha(p)for p in(base/'classes').rglob('*.class')};assert before==meta['classfiles_after']
old=out/'unmodified-classes';old.mkdir();run([str(java/'javac'),'--release','8','-nowarn','-cp',str(fw)+':'+str(base/'classes'),'-d',str(old),str(repo/source['baseline_source'])],'baseline-javac.log');assert {str(p.relative_to(old)):sha(p)for p in old.rglob('*.class')}=={n:h for n,h in before.items()if n=='SdRuntime.class'or n.startswith('SdRuntime$')},'Baseline source must reproduce existing class bytes'
new=out/'overlay-classes';new.mkdir();run([str(java/'javac'),'--release','8','-nowarn','-cp',str(fw)+':'+str(base/'classes'),'-d',str(new),str(b/'source/SdRuntime.java')],'javac.log')
classes=out/'classes';shutil.copytree(base/'classes',classes)
for p in new.rglob('*.class'):shutil.copyfile(p,classes/p.relative_to(new))
after={str(p.relative_to(classes)):sha(p)for p in classes.rglob('*.class')};assert after.keys()==before.keys();changed=[n for n in before if before[n]!=after[n]];assert set(changed)<={'SdRuntime.class','SdRuntime$1.class'}and 'SdRuntime.class'in changed,changed
run([str(java/'java'),'-Xmx2g','-cp',str(r8),'com.android.tools.r8.D8','--release','--min-api','29','--lib',str(fw),'--output',str(out/'runtime.jar'),*map(str,sorted(classes.rglob('*.class')))],'d8.log')
spec=importlib.util.spec_from_file_location('enc',repo/'scripts/api29/encode-hiddenapi-vm.py');enc=importlib.util.module_from_spec(spec);spec.loader.exec_module(enc);oldmembers,_=enc.dex_members(entries(base/'runtime.jar')['classes.dex']);newmembers,_=enc.dex_members(entries(out/'runtime.jar')['classes.dex']);assert oldmembers.keys()==newmembers.keys()and all(oldmembers[n][0]==newmembers[n][0]for n in oldmembers)
encoded=out/'encoded';run(['python3',str(repo/'scripts/api29/encode-hiddenapi-vm.py'),str(component),str(out/'runtime.jar'),str(repo/'build/evidence/cts-frame-repair-20261031/aosp-extra/android10-hiddenapi-flags.csv.gz'),'/var/tmp/saidroid-hiddenapi-tool-20261031/hiddenapi',str(encoded)],'encode.log')
oldenc=json.loads((component/'share/build/hiddenapi-manifest.json').read_text());newenc=json.loads((encoded/'manifest.json').read_text());assert oldenc['files'].keys()==newenc['files'].keys()
for key in ['schema','canonical_flags_sha256','effective_flags_sha256','tool_sha256','unknown_policy','public_library_apis']:assert oldenc[key]==newenc[key],key
changes=[n for n,v in newenc['files'].items()if v['sha256']!=oldenc['files'][n]['sha256']];assert changes==['lib/runtime.jar'],changes
for n,v in newenc['files'].items():
 assert sha(encoded/n)==v['sha256']and v['executable_code_unchanged']
 if n!='lib/runtime.jar':assert sha(component/n)==v['sha256']
r=dict(passed=True,schema='saidroid-app-native-bootstrap-v1',scope=source['scope'],source=source,builder_sha256=sha(Path(__file__)),baseline_manifest_sha256=sha(base/'manifest.json'),component_manifest_sha256=sha(component/'install-manifest.json'),classfiles_before=before,classfiles_after=after,changed_classfiles=changed,new_members=[],existing_members_flags_native_preserved=True,runtime_sha256=sha(out/'runtime.jar'),encoded_runtime_sha256=sha(encoded/'lib/runtime.jar'),encoded_manifest_sha256=sha(encoded/'manifest.json'),changed_encoded_jars=changes,core_framework_boot_inputs_unchanged=True,boot_images_reused=True,shared_frozen_source_unchanged=True,commands=commands)
(out/'manifest.json').write_text(json.dumps(r,indent=2)+'\n');(b/'runtime-build.json').write_text(json.dumps(r,indent=2)+'\n');print('BOOTSTRAP290_BUILD=ready|changed_classfiles='+','.join(changed)+'|changed_encoded_jars=runtime.jar|core_boot_native_unchanged=true',flush=True)
