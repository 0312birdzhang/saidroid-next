from pathlib import Path
import os,json,hashlib,subprocess
os.umask(0o022)
r=Path('/media/psf/Home/WorkSpace/saidroid-next');b=r/'build/evidence/qq-surface-texture300-20261102-v1';out=Path('/var/tmp/saidroid-surface-texture300-native-v4');out.mkdir();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();java=Path('/tmp/jdkfull/jdk-21.0.13+9');source=r/'native/graphics/surface-texture-owned-release';commands=[]
def run(cmd,name):
 commands.append(cmd)
 with(b/(name+'.log')).open('ab',buffering=0)as stream:subprocess.run(cmd,stdout=stream,stderr=subprocess.STDOUT,check=True,timeout=180)
headers=r/'build/hwui/headers';libcxx=r/'build/hwui/libcxx-source';clang=str(r/'build/evidence/qq-surface-texture295-20261102-v1/private-clang18/root/usr/lib/llvm-18/bin/clang');resource=subprocess.check_output([clang,'-print-resource-dir'],text=True).strip()+'/include'
flags=[clang,'-target','aarch64-linux-android29','-c','-O2','-fPIC','-std=c++17','-fno-exceptions','-fno-rtti','-nostdinc','-nostdinc++','-isystem',str(libcxx/'include'),'-isystem',resource]
for n in ['generated','hybrid','hidlbase','hidltransport','opengl','bionic','kernelandroid','kernelarm64','kernel','gui','ui','nativewindow','nativebase','binder','math','arect','libutils','liblog','libcutils','libsystem','libbacktrace','libbase','libhardware','sync']:flags+=['-isystem',str(headers/n)]
run(flags+['-o',str(out/'android-allocator.o'),str(source/'android-allocator.cpp')],'android-compile')
libs=Path('/var/tmp/saidroid-icmp-cleanup286-v1-formal-vm-component/root/android-libs')
run(['ld','-shared','-soname','libsdtexture-android.so','--allow-shlib-undefined','-o',str(out/'libsdtexture-android.so'),str(out/'android-allocator.o'),'-L'+str(libs),'-lc++','-lui'],'android-link')
run(['gcc','-shared','-fPIC','-O2','-Wall','-Wextra','-Werror','-Wno-unused-variable','-I'+str(java/'include'),'-I'+str(java/'include/linux'),'-o',str(out/'libsdtexture-host.so'),str(source/'gralloc-host.c'),str(source/'bootstrap-host.c'),'-ldl','-pthread'],'host-texture')
base=Path('/var/tmp/saidroid-fdsan219-registry-lock-v1');meta=json.loads((base/'manifest.json').read_text());assert sha(base/'libsdhost29.so')==meta['library_sha256']=='c747992aef8eccb3691148f44f79735961550712cba259d0d7e9dd8383d266d1'
sources=[r/n for n in meta['actual_sources']]
for p in sources:assert sha(p)==meta['actual_sources'][str(p.relative_to(r))]
flags=['gcc','-shared','-fPIC','-O2','-Wall','-I'+str(java/'include'),'-I'+str(java/'include/linux')]
run(flags+['-o',str(out/'baseline-host29.so'),*map(str,sources),'-ldl','-pthread'],'baseline-host29');assert sha(out/'baseline-host29.so')==meta['library_sha256']
changed=[b/'source/native/compat/api29-egl-host.c'if p.name=='api29-egl-host.c'else p for p in sources]
run(flags+['-o',str(out/'libsdhost29.so'),*map(str,changed),'-ldl','-pthread'],'candidate-host29')
old=json.loads((r/'build/evidence/qq-manifest-receivers292-20261102-v1/native-build.json').read_text());cmd=list(old['commands'][-2]);old_entry=next(v for v in cmd if v.endswith('/host-entry.cpp'));assert sha(Path(old_entry))==json.loads((b/'sources.json').read_text())['sources']['native/host/host-entry.cpp']['baseline_sha256'];cmd[cmd.index('-o')+1]=str(out/'baseline-host');run(cmd,'baseline-host');assert sha(out/'baseline-host')==old['binary_sha256']['saildroid-host']
cmd[cmd.index('-o')+1]=str(out/'saildroid-host');cmd[cmd.index(old_entry)]=str(b/'source/native/host/host-entry.cpp');run(cmd,'candidate-host')
result=dict(passed=True,builder_sha256=sha(Path(__file__)),baseline_host29_byte_identical=True,baseline_host_byte_identical=True,output=str(out),files={n:sha(out/n)for n in ['libsdtexture-host.so','libsdtexture-android.so','libsdhost29.so','saildroid-host']},sources={str(p.relative_to(r)):sha(p)for p in source.glob('*')if p.is_file()},commands=commands)
(out/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');(b/'native-build.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2),flush=True)
