#!/usr/bin/env python3
"""Finite local hash/invariant verification; no test, network, or device actions."""
from pathlib import Path
import hashlib,json,zipfile
p=Path(__file__).resolve().parent;repo=p.parents[4];manifest=json.loads((p/'reviewer-manifest.json').read_text());sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
for name,record in manifest['files'].items():
 f=repo/name;assert f.is_file(),name;assert f.stat().st_size==record['bytes']and sha(f)==record['sha256'],name
b=json.loads((p/'build-v5/result.json').read_text());a=json.loads((p/'actual-product-v5/result.json').read_text());im=json.loads((p/'candidate-images-v1/image-manifest.json').read_text());r=json.loads((p/'candidate-images-v1/runtime.json').read_text());pr=json.loads((p/'promotion-readiness-v1/result.json').read_text())
assert b['passed']and b['inputs_unchanged']and b['baseline_class_count']==257 and b['candidate_changed_classes']==['SdRuntime.class']and b['anonymous_class_byte_identical']
assert b['changed_jars']==['java/dex/art/framework29-classes3.jar','lib/runtime.jar']and b['canonical_old_hiddenapi_flags_unchanged']and b['framework_serialization_omissions']==94 and b['framework_serialization_omission_classes']==55
assert b['new_private_descriptors']==['LSdRuntime;->selectHeadlessChoreographer()V']
assert json.loads((p/'build-v5/baseline-all15-reproduction.json').read_text())['all15_exact_M1']
assert len(im['files'])==45 and len(im['boot_jars'])==15 and im['boot_jars']=={k:v['sha256']for k,v in b['encoded_union'].items()}
assert im['runtime_sha256']==b['encoded_runtime_sha256']and r['isolated_candidate']['runtime_sha256']==b['encoded_runtime_sha256']and r['boot_image']['manifest_sha256']==sha(p/'candidate-images-v1/image-manifest.json')
assert r['hidden_api']['manifest_sha256']==sha(p/'build-v5/candidate/encoded/manifest.json')
assert a['passed']and a['inputs_unchanged']and a['actual_candidate_images']and a['actual_target_sdks']==[29,34]and a['hidden_api_policy']=='enabled'and len(a['results'])==28
for label,v in a['results'].items():
 assert v['passed']and v['code']==0 and len(v['markers'])==1 and not v['gpu_device_open_attempts']and not v['wayland_connect_attempts'],label
 assert sha(p/'actual-product-v5'/(label+'-maps.txt'))==v['maps_sha256']and sha(p/'actual-product-v5'/(label+'-syscalls.txt'))==v['syscalls_sha256']
 for suffix in ['-syscalls.txt']:
  for line in (p/'actual-product-v5'/(label+suffix)).read_text().splitlines():assert '/dev/dri'not in line and '/dev/kgsl'not in line and not('connect('in line and 'wayland'in line),label
 assert '|sdk='+label.split('-sdk')[1].split('-')[0]in v['markers'][0]
 for c in a['commands']:
  if label not in ' '.join(c):continue
  if 'HeadlessProductEntry'in c:assert '--unshare-net'in c and '-Xhidden-api-policy:enabled'in c
for sdk in [29,34]:
 for mode in ['service','provider','service-provider']:
  v=a['results'][mode+'-sdk'+str(sdk)];assert len(v['fallback_markers'])==1 and '|callbacks=2|'in v['markers'][0]and '|release_recreate=true|'in v['markers'][0]
 assert '|fail_closed=true|'in a['results']['late-sdk'+str(sdk)]['markers'][0]
 assert '|default_vsync=true|'in a['results']['main-sdk'+str(sdk)+'-isolation']['markers'][0]
assert not pr['qualified']and not pr['actual_window_created']and not pr['actual_input_sent']and not pr['full_apk_binding']and pr['ordinary_host_returncode']==125
assert not pr['configured_binder']['exists']and not pr['kernel_or_mount_configuration_changed']and pr['no_mock_activation']
for source in ['SdRuntime.java','GuardChoreographerDispose.java']:assert sha(p/'source'/source)==sha(p/'build-v5/source-snapshot'/source)
for source in ['HeadlessProductProbe.java','HeadlessProductEntry.java']:assert sha(p/'fixtures'/source)==sha(p/'actual-product-v5/source-snapshot'/source)
print('HEADLESS_PACKET=verified|files='+str(len(manifest['files']))+'|build=v5|images=45|actual_ART_rows=28|promotion=pending|phone=false')
