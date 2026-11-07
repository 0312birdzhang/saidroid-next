#!/usr/bin/env python3
"""Build only the private native host timezone environment over its byte-identical baseline."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,shutil
p=argparse.ArgumentParser(description=__doc__)
for n in ['baseline-product','output']:p.add_argument('--'+n,type=Path,required=True)
a=p.parse_args();os.umask(0o022);repo=Path(__file__).resolve().parents[2];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();base=json.loads((a.baseline_product/'manifest.json').read_text());old=a.baseline_product/'saildroid-host';assert sha(old)==base['files']['saildroid-host']
names=['native/host/saildroid-app.cpp','native/host/host-entry.cpp','native/host/host-manager.cpp','native/host/host-common.hpp','native/host/instrumentation-policy.hpp','native/host/app-filesystem-policy.hpp','native/host/third_party/json.hpp','native/host/build-host-vm.sh'];assert all(sha(repo/n)==base['native_sources'][n]for n in names)
snapshot=a.baseline_product.parent/'source';assert all(sha(snapshot/n)==base['native_sources'][n]for n in names)
source=repo/'native/compat/timezone-layout';meta=json.loads((source/'sources.json').read_text());assert sha(source/'host-entry.cpp')==meta['sha256']and sha(repo/meta['baseline_source'])==meta['baseline_sha256'];assert not a.output.exists();a.output.mkdir(parents=True)
includes=['-I'+str(repo/'third_party/art-standalone/libnativehelper/include/nativehelper'),'-I'+str(repo/'third_party/art-standalone/libnativehelper/include')];gio=subprocess.check_output(['pkg-config','--cflags','--libs','gio-2.0'],text=True).split();commands={}
for label,entry in [('baseline',snapshot/'native/host/host-entry.cpp'),('new',source/'host-entry.cpp')]:
 cmd=['g++','-std=c++17','-O2','-Wall','-Wextra','-rdynamic','-o',str(a.output/(label+'-host')),str(snapshot/'native/host/saildroid-app.cpp'),str(entry),str(snapshot/'native/host/host-manager.cpp'),*includes,'-I'+str(snapshot/'native/host'),*gio,'-L/home/art/lib','-Wl,-rpath,/home/art/lib','-lnativehelper','-ldl','-pthread'];commands[label]=cmd
 with(a.output/(label+'.log')).open('x')as log:subprocess.run(cmd,check=True,stdout=log,stderr=subprocess.STDOUT,timeout=180)
assert sha(a.output/'baseline-host')==sha(old),'Baseline native host rebuild differs'
symbols=lambda f:set(' '.join(l.split()[-2:])for l in subprocess.check_output(['nm','-D',str(f)],text=True).splitlines()if len(l.split())>=2)
assert symbols(old)==symbols(a.output/'new-host')
needed=lambda f:sorted(l.strip()for l in subprocess.check_output(['readelf','-d',str(f)],text=True).splitlines()if'(NEEDED)'in l);assert needed(old)==needed(a.output/'new-host');shutil.copyfile(a.output/'new-host',a.output/'saildroid-host');(a.output/'saildroid-host').chmod(0o555)
record=dict(schema='saildroid-timezone-env-native-v1',passed=True,scope=meta['scope'],builder_sha256=sha(Path(__file__)),source_meta_sha256=sha(source/'sources.json'),source_sha256=sha(source/'host-entry.cpp'),baseline_library_sha256=sha(old),library_sha256=sha(a.output/'saildroid-host'),baseline_rebuild_byte_identical=True,all_dynamic_symbols_identical=True,needed_identical=True,sources={n:sha(repo/n)for n in names},baseline_snapshot=str(snapshot),commands=commands);(a.output/'manifest.json').write_text(json.dumps(record,indent=2)+'\n');print('TIMEZONE_ENV_NATIVE=built|baseline_byte_identical=true|existing_ABI_identical=true|all_ART_roles=true|phone_changed=false')
