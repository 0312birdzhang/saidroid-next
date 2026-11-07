#!/usr/bin/env python3
"""Build genuine splice JNI and native constants over the exact Linux/ICU base.

Two existing translation units only. Native registration intentionally gains one
method and dynamic imports gain the real glibc splice. Never edits shared ART.
"""
from pathlib import Path
import argparse, hashlib, json, os, shutil, subprocess

p=argparse.ArgumentParser(description=__doc__)
for n in ['art-source','baseline','original-build','output']:
    p.add_argument('--'+n,type=Path,required=True)
a=p.parse_args();os.umask(0o022);repo=Path(__file__).resolve().parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
baseline=json.loads((a.baseline/'manifest.json').read_text())
assert baseline['schema']=='saildroid-linux-io-native-compat-v1' and baseline['passed']
assert sha(a.baseline/'libjavacore.so')==baseline['library_sha256']
assert not a.output.exists();a.output.mkdir(parents=True)
def inventory(folder):
    return {str(f.relative_to(folder)):sha(f)for f in folder.rglob('*')if f.is_file()}
old_objects=inventory(a.baseline/'objects')
shared_roots=[a.art_source/'out/host/linux-x86/lib64',a.art_source/'out/host/linux-x86/obj/SHARED_LIBRARIES/libjavacore_intermediates']
shared={str(f.relative_to(a.art_source)):sha(f)for d in shared_roots for f in d.rglob('*')if f.is_file()}
objects=a.output/'objects';shutil.copytree(a.baseline/'objects',objects)
original=json.loads((a.original_build/'compile-commands.json').read_text())
commands=[];metadata={};shared_sources={}
for filename,patchname in [('libcore_io_Linux.cpp','libcore-linux-io-splice-api29-v2.patch'),('android_system_OsConstants.cpp','libcore-io-constants-api29-v1.patch')]:
    name='libcore/luni/src/main/native/'+filename
    patch=repo/'native/compat/patches'/patchname
    meta=json.loads(patch.with_suffix('.source.json').read_text())
    source=a.art_source/name
    assert sha(source)==meta['baseline_sha256']==sha(repo/meta['baseline_source'])
    assert sha(patch)==meta['patch_sha256'] and sha(repo/meta['reference'])==meta['reference_sha256']
    assert sha(repo/meta['baseline_prior_patch'])==meta['baseline_prior_patch_sha256']
    shared_sources[name]=sha(source)
    work=a.output/filename;draft=work/name;draft.parent.mkdir(parents=True)
    shutil.copyfile(source,draft)
    subprocess.run(['patch','-p1','--fuzz=0','-i',str(patch)],cwd=work,check=True)
    assert sha(draft)==meta['patched_sha256']
    matches=[c for c in original['compile']if c[-1]==name];assert len(matches)==1
    command=matches[0].copy();command[-1]=str(draft)
    command[1:1]=['-I'+str(source.parent)]
    command=[str(objects)+v[len(str(a.original_build/'objects')):]if v.startswith(str(a.original_build/'objects')+'/')else v for v in command]
    commands.append(command);metadata[name]=dict(meta,patch_source_manifest_sha256=sha(patch.with_suffix('.source.json')))
link=[str(objects)+v[len(str(a.baseline/'objects')):]if v.startswith(str(a.baseline/'objects')+'/')else v for v in baseline['commands']['link']]
link[link.index('-o')+1]=str(a.output/'libjavacore.so')
try:
    with(a.output/'build.log').open('x')as log:
        for command in commands:
            subprocess.run(command,cwd=a.art_source,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
        subprocess.run(link,cwd=a.art_source,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
finally:
    assert all(sha(a.art_source/n)==v for n,v in shared_sources.items())
    assert inventory(a.baseline/'objects')==old_objects
    assert shared=={str(f.relative_to(a.art_source)):sha(f)for d in shared_roots for f in d.rglob('*')if f.is_file()}
def symbols(f,defined=False):
    return {v[-1]:v[-2]for line in subprocess.check_output(['nm','-D',*(['--defined-only']if defined else[]),str(f)],text=True).splitlines()if len(v:=line.split())>=2}
old=symbols(a.baseline/'libjavacore.so');new=symbols(a.output/'libjavacore.so')
assert symbols(a.baseline/'libjavacore.so',True)==symbols(a.output/'libjavacore.so',True),'Existing exports changed'
assert all(new.get(n)==v for n,v in old.items()),'Existing import/export changed'
added={n:v for n,v in new.items()if n not in old}
assert len(added)==1 and next(iter(added)).split('@',1)[0]=='splice' and set(added.values())=={'U'},added
changed=[n for n,h in inventory(objects).items()if old_objects.get(n)!=h]
assert len([n for n in changed if n.endswith('.o')])==2
assert all(any(x in n for x in ['libcore_io_Linux','android_system_OsConstants'])for n in changed)
dynamic=subprocess.check_output(['readelf','-d',str(a.output/'libjavacore.so')],text=True)
assert 'libicuuc.so.63'in dynamic and 'libicui18n.so.63'in dynamic and '.so.74'not in dynamic
record=dict(schema='saildroid-os-extended-io-native-v1',scope='Original Android10 real splice JNI and Int64Ref field binding plus4 real kernel constants. Existing7 Linux behavior ports/socket constants/ICU63 retained. Exactly2 objects rebuilt; intentional JNI method extension and genuine splice import, no old declarations/symbols removed. No phone/core/ART changes.',passed=True,
    builder_sha256=sha(Path(__file__)),patches=metadata,baseline_manifest_sha256=sha(a.baseline/'manifest.json'),
    baseline_library_sha256=sha(a.baseline/'libjavacore.so'),library_sha256=sha(a.output/'libjavacore.so'),
    all_previous_dynamic_symbols_preserved=True,added_dynamic_symbols=added,
    added_native_registration='libcore/io/Linux.splice(Ljava/io/FileDescriptor;Landroid/system/Int64Ref;Ljava/io/FileDescriptor;Landroid/system/Int64Ref;JI)J',
    changed_object_files=changed,shared_tree_unchanged=True,commands=dict(compile=commands,link=link),dynamic=dynamic)
(a.output/'manifest.json').write_text(json.dumps(record,indent=2)+'\n')
print('OS_EXTENDED_IO_NATIVE=built|objects=2|new_jni=splice|added_import=splice|previous_symbols=retained|phone_changed=false')
