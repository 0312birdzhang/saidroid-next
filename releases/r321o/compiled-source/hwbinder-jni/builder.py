#!/usr/bin/env python3
"""Reproduce the pinned JNI bridge, then register original Android HIDL JNI."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess
p=argparse.ArgumentParser(description=__doc__)
for n in ['product','source','component','output']:p.add_argument('--'+n,type=Path,required=True)
a=p.parse_args();os.umask(0o022);repo=Path(__file__).resolve().parents[2];owned=repo/'native/compat/hwbinder-jni';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();meta=json.loads((owned/'sources.json').read_text());product=json.loads((a.product/'manifest.json').read_text());assert not a.output.exists();a.output.mkdir(parents=True)
assert sha(a.product/'libsdbridge.so')==product['files']['libsdbridge.so']==sha(a.component/'lib/libsdbridge.so')
assert sha(repo/meta['baseline_entries'])==meta['baseline_entries_sha256']and sha(owned/'api29-jni-entries.inc')==meta['entries_sha256']
for n,v in meta['canonical_references'].items():assert sha(repo/n)==v['sha256']
sources=['scripts/device/sdbridge.c','native/compat/api29-memory.c','native/compat/api29-eventlog.c','native/compat/api29-hardware-properties.c','native/launcher/sdruntime-control.c','native/saidroid-system-paths.h','native/api29-jni-entries.inc']
frozen=json.loads((repo/'build/evidence/cts-frame-repair-20261031/continuation225-frozen-inputs.json').read_text())
for n in sources:
 expected=product['native_sources'].get(n,meta['existing_unrecorded_source_pins'].get(n));assert expected is not None and sha(a.source/n)==expected,n
assert sha(a.source/'native/api29-jni-entries.inc')==meta['baseline_entries_sha256']
original_inputs={str(a.source/n):sha(a.source/n)for n in sources};original_inputs.update({str(a.product/n):sha(a.product/n)for n in ['binder.o','runtime-control.o','libsdbridge.so','manifest.json']})
java=Path(os.environ.get('JAVA_HOME','/tmp/jdkfull/jdk-21.0.13+9'));commands=[]
def build(target,bridge):
 cmd=['gcc','-shared','-fPIC','-O2','-Wall','-o',str(target),str(bridge),*[str(a.source/n)for n in ['native/compat/api29-memory.c','native/compat/api29-eventlog.c','native/compat/api29-hardware-properties.c']],str(a.product/'binder.o'),str(a.product/'runtime-control.o'),str(a.source/'native/launcher/sdruntime-control.c'),'-I'+str(java/'include'),'-I'+str(java/'include/linux'),'-ldl','-pthread'];commands.append(cmd)
 with(target.with_suffix('.build.log')).open('x')as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
baseline=a.output/'baseline-libsdbridge.so';build(baseline,a.source/'scripts/device/sdbridge.c');assert sha(baseline)==product['files']['libsdbridge.so'],'Unmodified exact JNI bridge must reproduce byte-for-byte'
prepared=a.output/'source';(prepared/'scripts/device').mkdir(parents=True);(prepared/'native').mkdir();shutil.copyfile(a.source/'scripts/device/sdbridge.c',prepared/'scripts/device/sdbridge.c');shutil.copyfile(a.source/'native/saidroid-system-paths.h',prepared/'native/saidroid-system-paths.h');shutil.copyfile(owned/'api29-jni-entries.inc',prepared/'native/api29-jni-entries.inc')
new=a.output/'libsdbridge.so';build(new,prepared/'scripts/device/sdbridge.c')
def symbols(f):return sorted(l.split()[-2:]for l in subprocess.check_output(['nm','-D',str(f)],text=True).splitlines()if len(l.split())>=2)
needed=lambda f:sorted(l.strip()for l in subprocess.check_output(['readelf','-d',str(f)],text=True).splitlines()if'(NEEDED)'in l)
assert symbols(new)==symbols(baseline)and needed(new)==needed(baseline)
assert all(sha(Path(n))==h for n,h in original_inputs.items()),'Pinned original source/objects changed'
exports=subprocess.check_output(['nm','-D',str(a.component/'android-libs/libandroid_runtime.so')],text=True)
assert all(any(line.split()[-1]==name for line in exports.splitlines())for name in meta['added_symbols'])
record=dict(schema='saildroid-hwbinder-jni-v1',scope=meta['scope'],passed=True,builder_sha256=sha(Path(__file__)),source_meta_sha256=sha(owned/'sources.json'),baseline_product_manifest_sha256=sha(a.product/'manifest.json'),baseline_library_sha256=sha(baseline),library_sha256=sha(new),prepared_bridge_sha256=sha(prepared/'scripts/device/sdbridge.c'),prepared_entries_sha256=sha(prepared/'native/api29-jni-entries.inc'),existing_dynamic_symbols_identical=True,needed_identical=True,original_inputs_unchanged=True,original_inputs=original_inputs,commands=commands,phone_staged=False)
(a.output/'manifest.json').write_text(json.dumps(record,indent=2)+'\n');print('HWBINDER_JNI=built|baseline_byte_identical=true|original_tables_only=true|dynamic_symbols_identical=true|phone_staged=false')
