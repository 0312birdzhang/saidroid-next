#!/usr/bin/env python3
"""Build the Android ELF helper using matching API29 headers and libc++.

The Linux compiler emits an AArch64 ELF with no host runtime linked in. All
Android C++ classes and allocations are provided by the selected API29 release.
"""
from pathlib import Path
import argparse,subprocess,json,hashlib,os
p=argparse.ArgumentParser();p.add_argument('headers',type=Path);p.add_argument('libcxx',type=Path);p.add_argument('android_libs',type=Path);p.add_argument('output',type=Path);p.add_argument('--compiler',default='clang++');a=p.parse_args()
a.output.mkdir(parents=True,exist_ok=True);repo=Path(__file__).resolve().parents[2]
resource=subprocess.check_output([a.compiler,'-print-resource-dir'],text=True).strip()+'/include'
cmd=[a.compiler,'-target','aarch64-linux-android29','-c','-O2','-fPIC','-std=c++17','-fno-exceptions','-fno-rtti','-nostdinc','-nostdinc++','-isystem',str(a.libcxx/'include'),'-isystem',resource]
for name in ['generated','hybrid','hidlbase','hidltransport','opengl','bionic','kernelandroid','kernelarm64','kernel','gui','ui','nativewindow','nativebase','binder','math','arect','libutils','liblog','libcutils','libsystem','libbacktrace','libbase','libhardware','sync']:
 directory=a.headers/name;assert directory.is_dir(),directory;cmd+=['-isystem',str(directory)]
source=repo/'native/hwui/sd-hwui-native.cpp';obj=a.output/'sd-hwui-native.o';target=a.output/'libsdhwui-native.so'
subprocess.run(cmd+['-o',str(obj),str(source)],check=True)
subprocess.run(['ld','-shared','-soname',target.name,'--allow-shlib-undefined','-o',str(target),str(obj),'-L'+str(a.android_libs),'-lgui','-lui','-lbinder','-lutils','-lc++'],check=True)
record=dict(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),elf_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),headers={str(f.relative_to(a.headers)):hashlib.sha256(f.read_bytes()).hexdigest()for f in sorted(a.headers.rglob('*.h'))},compiler=subprocess.check_output([a.compiler,'--version'],text=True).splitlines()[0])
(a.output/'native-manifest.json').write_text(json.dumps(record,indent=2)+'\n');print('HWUI_NATIVE_HELPER=compiled|sha256='+record['elf_sha256'])
