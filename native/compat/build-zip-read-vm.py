#!/usr/bin/env python3
"""Build canonical ZIP direct-array native read over the verified existing native host shim."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess
p=argparse.ArgumentParser(description=__doc__)
for n in ['baseline-product','baseline-openjdk','baseline-native','output']:p.add_argument('--'+n,type=Path,required=True)
a=p.parse_args();os.umask(0o022);repo=Path(__file__).resolve().parents[2];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();old=a.baseline_product/'libsdhost29.so';m=json.loads((a.baseline_product/'manifest.json').read_text());assert sha(old)==m['files'][old.name];assert sha(a.baseline_openjdk)=='f59985a283b244f2e0001a246b3d33933b2f817c89ee1c652331ad198228ce8a';assert not a.output.exists();a.output.mkdir(parents=True)
names='api29-host api29-fdsan api29-signal api29-diagnostics api29-regex api29-egl-host api29-thread api29-cfi api29-renderscript api29-native-loader api29-hardware-loader'.split();sources=[repo/('native/compat/'+n+'.c')for n in names]
for f in sources:assert sha(f)==m['native_sources'][str(f.relative_to(repo))]
oldmeta=json.loads((a.baseline_native/'manifest.json').read_text());assert oldmeta['passed']and sha(a.baseline_native/'libsdhost29.so')==oldmeta['library_sha256'];sources.append(repo/'native/compat/runtime-policy/runtime-gc.c');assert sha(sources[-1])==oldmeta['source_sha256'];old=a.baseline_native/'libsdhost29.so';extra=repo/'native/compat/zip/zip-read.c';java=Path(os.environ.get('JAVA_HOME','/tmp/jdkfull/jdk-21.0.13+9'));flags=['gcc','-shared','-fPIC','-O2','-Wall','-I'+str(java/'include'),'-I'+str(java/'include/linux')]
for label,files in [('baseline',sources),('new',[*sources,extra])]:
 with(a.output/(label+'.log')).open('x')as log:subprocess.run(flags+['-o',str(a.output/(label+'.so')),*map(str,files),'-ldl','-pthread'],check=True,stdout=log,stderr=subprocess.STDOUT)
assert sha(a.output/'baseline.so')==sha(old)
def symbols(f,defined=False):return set(' '.join(l.split()[-2:])for l in subprocess.check_output(['nm','-D',*(['--defined-only']if defined else[]),str(f)],text=True).splitlines()if len(l.split())>=2)
assert symbols(a.output/'new.so')-symbols(old)=={'T ZipFile_read'}and not symbols(old)-symbols(a.output/'new.so')
needed=lambda f:sorted(l.strip()for l in subprocess.check_output(['readelf','-d',str(f)],text=True).splitlines()if '(NEEDED)'in l)
assert needed(old)==needed(a.output/'new.so');relocs=subprocess.check_output(['readelf','-rW',str(a.baseline_openjdk)],text=True);assert any('ZipFile_read'in l and 'R_AARCH64_ABS64'in l for l in relocs.splitlines()),'Original JNI registration must use a preemptable ZipFile_read symbol'
shutil.copyfile(a.output/'new.so',a.output/'libsdhost29.so');(a.output/'libsdhost29.so').chmod(0o444)
record=dict(schema='saildroid-zip-read-native-v1',passed=True,scope='All ZIP callers: canonical direct array native read with actual original ZIP_Read/lock/error backend. Preserves JNI ABI, checks ranges with overflow-safe arithmetic. Existing GC policy retained. No fake data/test/phone/fullCTS acceptance.',builder_sha256=sha(Path(__file__)),source_sha256=sha(extra),baseline_library_sha256=sha(old),library_sha256=sha(a.output/'libsdhost29.so'),baseline_rebuild_byte_identical=True,baseline_openjdk_sha256=sha(a.baseline_openjdk),baseline_openjdk_registration_preemptable=True,all_previous_dynamic_symbols_preserved=True,added_exports=['ZipFile_read'],needed_identical=True,sources={str(f.relative_to(repo)):sha(f)for f in sources},dynamic=subprocess.check_output(['readelf','-d',str(a.output/'libsdhost29.so')],text=True))
(a.output/'manifest.json').write_text(json.dumps(record,indent=2)+'\n');print('ZIP_READ_NATIVE=built|baseline_byte_identical=true|added_export=ZipFile_read|phone_changed=false')
