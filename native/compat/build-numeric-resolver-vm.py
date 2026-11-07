#!/usr/bin/env python3
"""Build the actual glibc libcore numeric-host adapter in one private JNI object.

The existing Bionic host shim is a different ABI path. This builder patches only
an offside copy of Portability.h and recompiles the real Linux JNI object. No
shared sources, original APKs, Java classes, ART or running components change.
"""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess
p=argparse.ArgumentParser(description=__doc__)
for n in ['art-source','baseline','output']:p.add_argument('--'+n,type=Path,required=True)
a=p.parse_args();os.umask(0o022);repo=Path(__file__).resolve().parents[2];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((a.baseline/'manifest.json').read_text());assert m['schema']=='saildroid-os-extended-io-native-v1'and m['passed']and sha(a.baseline/'libjavacore.so')==m['library_sha256']
assert not a.output.exists();a.output.mkdir(parents=True)
def inventory(p):return {str(f.relative_to(p)):sha(f)for f in p.rglob('*')if f.is_file()}
oldobjects=inventory(a.baseline/'objects');objects=a.output/'objects';shutil.copytree(a.baseline/'objects',objects)
name='libcore/luni/src/main/native/libcore_io_Linux.cpp';source=a.baseline/'libcore_io_Linux.cpp'/name
assert sha(source)==m['patches'][name]['patched_sha256']
shared_roots=[a.art_source/'out/host/linux-x86/lib64',a.art_source/'out/host/linux-x86/obj/SHARED_LIBRARIES/libjavacore_intermediates']
shared={str(f.relative_to(a.art_source)):sha(f)for d in shared_roots for f in d.rglob('*')if f.is_file()}
portability=a.art_source/'libcore/luni/src/main/native/Portability.h';oldport=portability.read_text()
assert oldport==(repo/'third_party/art-standalone/libcore/luni/src/main/native/Portability.h').read_text()
old='''static inline int android_getaddrinfofornet(const char* hostname, const char* servname,
    const struct addrinfo* hints, unsigned /*netid*/, unsigned /*mark*/, struct addrinfo** res) {
  return getaddrinfo(hostname, servname, hints, res);
}'''
assert oldport.count(old)==1
header=repo/'native/compat/resolver/libcore-numeric-host.h'
replacement='''#include "'''+str(header)+'''"
static inline int android_getaddrinfofornet(const char* hostname, const char* servname,
    const struct addrinfo* hints, unsigned netid, unsigned mark, struct addrinfo** res) {
  return sd_libcore_getaddrinfofornet(hostname, servname, hints, netid, mark, res);
}'''
private=a.output/'source';private.mkdir();shutil.copyfile(source,private/source.name);(private/'Portability.h').write_text(oldport.replace(old,replacement))
compile=m['commands']['compile'][0].copy();assert 'libcore_io_Linux.cpp'in compile[-1];compile[-1]=str(private/source.name)
compile=[str(objects)+v[len(str(a.baseline/'objects')):]if v.startswith(str(a.baseline/'objects')+'/')else v for v in compile]
link=[str(objects)+v[len(str(a.baseline/'objects')):]if v.startswith(str(a.baseline/'objects')+'/')else v for v in m['commands']['link']];link[link.index('-o')+1]=str(a.output/'libjavacore.so')
try:
 with(a.output/'build.log').open('x')as log:
  subprocess.run(compile,cwd=a.art_source,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
  subprocess.run(link,cwd=a.art_source,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
finally:
 assert inventory(a.baseline/'objects')==oldobjects
 assert sha(source)==m['patches'][name]['patched_sha256']and portability.read_text()==oldport
 assert shared=={str(f.relative_to(a.art_source)):sha(f)for d in shared_roots for f in d.rglob('*')if f.is_file()}
def symbols(p):return sorted(' '.join(l.split()[-2:])for l in subprocess.check_output(['nm','-D',str(p)],text=True).splitlines()if len(l.split())>=2)
old_symbols=set(symbols(a.baseline/'libjavacore.so'));new_symbols=set(symbols(a.output/'libjavacore.so'))
assert not old_symbols-new_symbols and new_symbols-old_symbols=={'U snprintf@GLIBC_2.17'}
assert {n for n in old_symbols if not n.startswith('U ')}=={n for n in new_symbols if not n.startswith('U ')}
changed=[n for n,h in inventory(objects).items()if oldobjects.get(n)!=h];assert len([n for n in changed if n.endswith('.o')])==1 and all('libcore_io_Linux'in n for n in changed),changed
dynamic=subprocess.check_output(['readelf','-d',str(a.output/'libjavacore.so')],text=True);assert 'libicuuc.so.63'in dynamic and 'libicui18n.so.63'in dynamic and '.so.74'not in dynamic
record=dict(schema='saildroid-libcore-numeric-resolver-v1',scope='Private glibc Linux JNI Portability numeric-host IPv4 decimal adapter and nondefault-network rejection, one real JNI object only; unchanged Java/ART/APK/system',passed=True,builder_sha256=sha(Path(__file__)),header_sha256=sha(header),baseline_manifest_sha256=sha(a.baseline/'manifest.json'),baseline_library_sha256=sha(a.baseline/'libjavacore.so'),library_sha256=sha(a.output/'libjavacore.so'),baseline_portability_sha256=sha(portability),patched_portability_sha256=sha(private/'Portability.h'),linux_source_sha256=sha(source),all_previous_dynamic_symbols_preserved=True,all_defined_exports_identical=True,added_imports=sorted(new_symbols-old_symbols),changed_object_files=changed,shared_tree_unchanged=True,commands=dict(compile=compile,link=link),dynamic=dynamic)
(a.output/'manifest.json').write_text(json.dumps(record,indent=2)+'\n');print('LIBCORE_NUMERIC_RESOLVER=built|objects=1|all_old_symbols=preserved|new_import=snprintf|shared_tree=unchanged|phone_changed=false')
