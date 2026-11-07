"""Run same-SONAME groups and core-ELF bridge aliases on the actual phone."""
from pathlib import Path
import subprocess,os,json,tarfile,io,base64
r=Path('/media/psf/Home/WorkSpace/saidroid-next');b=r/'build/evidence/wechat-startup320-20261104';out=b/'phone-linker-fixture';out.mkdir(exist_ok=True);e=dict(os.environ,SSHPASS=os.environ['SSHPASS'])
for label,value in [('platform',17),('application',93)]:
 d=out/label;d.mkdir(exist_ok=True)
 for name,body,flags in [('same',f'static int value={value};int next(void){{return value++;}}',['-Wl,-soname,libsame.so']),('entry','extern int next(void);int entry(void){return next();}',['-L'+str(d),'-Wl,--no-as-needed','-lsame'])]:
  source=d/(name+'.c');source.write_text(body);target=d/('libsame.so'if name=='same'else'entry.so');subprocess.run(['gcc','-shared','-fPIC','-nostdlib','-Wl,--hash-style=both','-o',str(target),str(source),*flags],check=True)
files={str(p.relative_to(out)):base64.b64encode(p.read_bytes()).decode()for p in out.rglob('*.so')}
body=r'''from pathlib import Path
import subprocess,json,os,pwd,base64,shutil
assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()=='997d54fe-04b5-4829-baa5-dd172b8de55b'
assert subprocess.check_output(['pidof','lipstick'],text=True).strip()=='9157'
assert Path('/sys/class/backlight/panel0-backlight/actual_brightness').read_text().strip()=='0'
root=Path('/home/art/releases/api29-r320b-native-candidate');stage=Path('/home/art/test/linker-origin320');assert not stage.exists();stage.mkdir(mode=0o755)
try:
 for n,v in FILES.items():
  p=stage/n;p.parent.mkdir(exist_ok=True);p.write_bytes(base64.b64decode(v));p.chmod(0o644)
 code=r"""import ctypes,os,json,math
from pathlib import Path
r=Path('/home/art/releases/api29-r320b-native-candidate');s=Path('/home/art/test/linker-origin320');l=ctypes.CDLL(str(r/'lib/libdl_bio.so.0'),mode=ctypes.RTLD_GLOBAL)
l.bionic_dlopen.argtypes=[ctypes.c_char_p,ctypes.c_int];l.bionic_dlopen.restype=ctypes.c_void_p;l.bionic_dlsym.argtypes=[ctypes.c_void_p,ctypes.c_char_p];l.bionic_dlsym.restype=ctypes.c_void_p;l.bionic_dlclose.argtypes=[ctypes.c_void_p];l.bionic_dlerror.restype=ctypes.c_char_p;l.bionic_add_library_path.argtypes=[ctypes.c_char_p];assert not l.bionic_add_library_path((str(s/'platform')+':'+str(s/'application')+':'+str(r/'android-libs')).encode())
a=l.bionic_dlopen(str(s/'platform/entry.so').encode(),2);assert a,l.bionic_dlerror();pv=ctypes.CFUNCTYPE(ctypes.c_int)(l.bionic_dlsym(a,b'entry'));assert pv()==17
z=l.bionic_dlopen(str(s/'application/entry.so').encode(),2);assert z and z!=a,l.bionic_dlerror();av=ctypes.CFUNCTYPE(ctypes.c_int)(l.bionic_dlsym(z,b'entry'));assert av()==93 and pv()==18 and av()==94
z2=l.bionic_dlopen(str(s/'application/entry.so').encode(),2);assert z2==z;assert not l.bionic_dlclose(z2);assert not l.bionic_dlclose(z);assert pv()==19;assert not l.bionic_dlclose(a)
h=l.bionic_dlopen(str(r/'android-libs/libm.so').encode(),2);assert h,l.bionic_dlerror();cos=ctypes.CFUNCTYPE(ctypes.c_double,ctypes.c_double)(l.bionic_dlsym(h,b'cos'));assert abs(cos(.75)-math.cos(.75))<1e-15
maps=Path('/proc/self/maps').read_text();assert str(r/'android-libs/libm.so')not in maps;assert '/lib64/libm.so.6'in maps
print(json.dumps(dict(passed=True,independent_groups=[17,18,19,93,94],explicit_core_elf='host-libm.so.6',android_libm_executed=False,uid=os.getuid())))
"""
 u=pwd.getpwnam('defaultuser');env=dict(os.environ,LD_LIBRARY_PATH=str(root/'lib')+':/home/art/lib',ANDROID_ROOT=str(root),BIONIC_TRANSLATION_CONFIG_DIR=str(root/'linker-config'),SAILDROID_STRICT_LINK='1');q=subprocess.run(['python3','-c',code],env=env,user=u.pw_uid,group=u.pw_gid,extra_groups=os.getgrouplist(u.pw_name,u.pw_gid),capture_output=True,text=True,timeout=12);print(q.stdout);assert q.returncode==0,q.stderr[-3500:]
finally:shutil.rmtree(stage)
'''
subprocess.run(['bash',str(r/'scripts/devlock.sh'),'acquire','0','wechat320-linker-fixture'],env=e,check=True,timeout=15)
try:
 q=subprocess.run(['sshpass','-e','ssh','-o','ConnectTimeout=6','root@bonito','python3','-'],input='FILES='+repr(files)+'\n'+body,env=e,capture_output=True,text=True,timeout=25);(b/'phone-linker-fixture.stdout').write_text(q.stdout);(b/'phone-linker-fixture.stderr').write_text(q.stderr);print(q.stdout,q.stderr);q.check_returncode();(b/'phone-linker-fixture.json').write_text(json.dumps(json.loads(q.stdout),indent=2)+'\n')
finally:subprocess.run(['bash',str(r/'scripts/devlock.sh'),'release','wechat320-linker-fixture'],env=e,check=True,timeout=15)
