from pathlib import Path
import hashlib,json
p=Path(__file__).resolve().parent;repo=p.parents[4];sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest();read=lambda q:json.loads(q.read_text());base=p.parent/'uimode-product-candidates-v1/u1a-build-v1';root=p.parent/'distribution-v14/assembly/root';build=p/'build-v2';candidate=build/'candidate';images=p/'candidate-images-v1';checked=0
b=read(build/'result.json');assert b['passed']and b['baseline_reproduced_exact']and b['full_class_count']==257
for v in ['baseline','candidate']:
 r=read(build/v/'result.json');assert r['passed']
 actual={str(q.relative_to(build/(v+'-classes'))):sha(q)for q in (build/(v+'-classes')).rglob('*.class')};assert actual==r['classfiles'];checked+=len(actual)
 assert sha(build/v/'encoded/lib/runtime.jar')==r['encoded_runtime_sha256'];checked+=1
 assert sha(build/v/'runtime.jar')==r['raw_runtime_sha256'];checked+=1
before=read(base/'result.json')['classfiles'];after=read(candidate/'result.json')['classfiles'];assert [k for k in before if before[k]!=after[k]]==['SdAudio.class'];assert before.keys()==after.keys();assert before['SdAudio$1.class']==after['SdAudio$1.class'];assert sha(build/'baseline/encoded/lib/runtime.jar')==sha(root/'lib/runtime.jar')=='eb7e30783cad033a67d0efe202dbd94b41f7fea0c09ec13251d4acf4bf762495'
flags=lambda q:dict(line.split(',',1)for line in q.read_text().splitlines());old,new=flags(base/'encoded/effective-api-flags.csv'),flags(candidate/'encoded/effective-api-flags.csv');assert all(new[k]==v for k,v in old.items());assert sorted(set(new)-set(old))==['LSdAudio;->APPLIED_ANDROID_MODE:I']
im=read(images/'image-manifest.json');assert read(images/'result.json')['passed']and len(im['files'])==45;assert {q.name:dict(sha256=sha(q),bytes=q.stat().st_size)for q in (images/'arm64').iterdir()if q.is_file()}==im['files'];checked+=45
for name,digest in im['boot_jars'].items():assert sha(candidate/'encoded'/name if name=='lib/runtime.jar'else root/name)==digest;checked+=1
assert im['runtime_sha256']==sha(candidate/'encoded/lib/runtime.jar');rt=read(images/'runtime.json');assert rt['boot_image']['manifest_sha256']==sha(images/'image-manifest.json');assert rt['hidden_api']['manifest_sha256']==sha(candidate/'encoded/manifest.json');assert rt['isolated_candidate']['runtime_sha256']==im['runtime_sha256'];assert rt['isolated_candidate']['image_manifest_sha256']==sha(images/'image-manifest.json');assert rt['isolated_candidate']['hidden_api_manifest_sha256']==sha(candidate/'encoded/manifest.json')
r=read(p/'product-fixture-v1/result.json');assert r['passed']and r['accepted_runtime_unchanged']and len(r['results'])==4
for variant in r['results']:
 row=r['results'][variant];assert row['passed']and row['code']==0;log=(p/'product-fixture-v1'/(variant+'.log')).read_text(errors='replace');assert log.count('AUDIO_MODE_PRODUCT=passed')==1;assert log.count('AUDIO_MODE_NATIVE=rejected|mode=')==10;assert log.count('SDAUDIO=mode|source=android-applied-mode|mode=0|supported_transitions=none|host_call_mode=unintegrated')==(0 if variant=='baseline'else 78)
assert read(p/'bytecode-audit-v3/result.json')['passed'];manifest=p/'reviewer-manifest.json'
if manifest.exists():
 m=read(manifest)
 for name,row in m['files'].items():q=p/name;assert q.stat().st_size==row['bytes']and sha(q)==row['sha256'],name;checked+=1
 actual={str(q.relative_to(p))for q in p.rglob('*')if q.is_file()and q.name not in ['reviewer-manifest.json','verification-host.json','verification-vm.json']};assert actual==set(m['files'])
 for name,row in m['external_inputs'].items():q=repo/name;assert q.stat().st_size==row['bytes']and sha(q)==row['sha256'],name;checked+=1
print(json.dumps(dict(passed=True,checked=checked,full_class_count=257,only_changed_class='SdAudio.class',images=45,baseline_checks=85,candidate_checks_per_process=124,candidate_ART_process_invocations=3,phone_accessed=False,app_caches_built=False,full_app_startup_tested=False,candidate_encoded_runtime_sha256=sha(candidate/'encoded/lib/runtime.jar'),image_manifest_sha256=sha(images/'image-manifest.json'),hidden_api_manifest_sha256=sha(candidate/'encoded/manifest.json')),indent=2))
