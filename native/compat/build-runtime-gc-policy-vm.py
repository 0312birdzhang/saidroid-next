#!/usr/bin/env python3
"""Build one real Runtime.gc policy entry over the verified existing native host shim."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess
p=argparse.ArgumentParser(description=__doc__)
for n in ['baseline-product','baseline-openjdk','output']:p.add_argument('--'+n,type=Path,required=True)
a=p.parse_args();os.umask(0o022);repo=Path(__file__).resolve().parents[2];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();old=a.baseline_product/'libsdhost29.so';m=json.loads((a.baseline_product/'manifest.json').read_text());assert sha(old)==m['files'][old.name];assert sha(a.baseline_openjdk)=='f59985a283b244f2e0001a246b3d33933b2f817c89ee1c652331ad198228ce8a';assert not a.output.exists();a.output.mkdir(parents=True)
names='api29-host api29-fdsan api29-signal api29-diagnostics api29-regex api29-egl-host api29-thread api29-cfi api29-renderscript api29-native-loader api29-hardware-loader'.split();sources=[repo/('native/compat/'+n+'.c')for n in names]
for f in sources:assert sha(f)==m['native_sources'][str(f.relative_to(repo))]
extra=repo/'native/compat/runtime-policy/runtime-gc.c';java=Path(os.environ.get('JAVA_HOME','/tmp/jdkfull/jdk-21.0.13+9'));flags=['gcc','-shared','-fPIC','-O2','-Wall','-I'+str(java/'include'),'-I'+str(java/'include/linux')]
for label,files in [('baseline',sources),('new',[*sources,extra])]:
 with(a.output/(label+'.log')).open('x')as log:subprocess.run(flags+['-o',str(a.output/(label+'.so')),*map(str,files),'-ldl','-pthread'],check=True,stdout=log,stderr=subprocess.STDOUT)
assert sha(a.output/'baseline.so')==sha(old)
def symbols(f,defined=False):return set(' '.join(l.split()[-2:])for l in subprocess.check_output(['nm','-D',*(['--defined-only']if defined else[]),str(f)],text=True).splitlines()if len(l.split())>=2)
assert symbols(a.output/'new.so')-symbols(old)=={'T Runtime_gc'}and not symbols(old)-symbols(a.output/'new.so')
needed=lambda f:sorted(l.strip()for l in subprocess.check_output(['readelf','-d',str(f)],text=True).splitlines()if '(NEEDED)'in l)
assert needed(old)==needed(a.output/'new.so');relocs=subprocess.check_output(['readelf','-rW',str(a.baseline_openjdk)],text=True);assert any('Runtime_gc'in l and 'R_AARCH64_ABS64'in l for l in relocs.splitlines()),'Original JNI registration must use a preemptable Runtime_gc symbol'
shutil.copyfile(a.output/'new.so',a.output/'libsdhost29.so');(a.output/'libsdhost29.so').chmod(0o444)
record=dict(schema='saildroid-runtime-gc-policy-native-v1',passed=True,scope='All legacy Runtime.gc callers: actual BlockGuard thread policy then already-loaded original libopenjdk/ART GC. Exceptions propagate before collector. No Java/native registration change, no phone/fullCTS acceptance.',builder_sha256=sha(Path(__file__)),source_sha256=sha(extra),baseline_library_sha256=sha(old),library_sha256=sha(a.output/'libsdhost29.so'),baseline_rebuild_byte_identical=True,baseline_openjdk_sha256=sha(a.baseline_openjdk),baseline_openjdk_registration_preemptable=True,all_previous_dynamic_symbols_preserved=True,added_exports=['Runtime_gc'],needed_identical=True,sources={str(f.relative_to(repo)):sha(f)for f in sources},dynamic=subprocess.check_output(['readelf','-d',str(a.output/'libsdhost29.so')],text=True))
(a.output/'manifest.json').write_text(json.dumps(record,indent=2)+'\n');print('RUNTIME_GC_POLICY_NATIVE=built|baseline_byte_identical=true|added_export=Runtime_gc|phone_changed=false')
