"""Verify NOLOAD on the phone as defaultuser, with the OLED off."""
from pathlib import Path
import subprocess,os,json,base64,shutil
r=Path('/media/psf/Home/WorkSpace/saidroid-next');b=r/'build/evidence/wechat-startup320-20261104';out=b/'phone-noload-fixture';out.mkdir()
s=(r/'native/compat/linker-noload/test-vm.py').read_text()
fixture='extern void event(int);__attribute__((constructor))static void init(void){event(1);}\n__attribute__((destructor))static void fini(void){event(-1);}\nint identity(void){return 81;}\n'
(out/'fixture.c').write_text(fixture);(out/'run.c').write_text(s.split("(root/'run.c').write_text(r'''",1)[1].split("''')",1)[0])
subprocess.run(['gcc','-shared','-fPIC','-nostdlib','-Wl,--hash-style=both','-Wl,-soname,fixture.so','-o',str(out/'fixture.so'),str(out/'fixture.c')],check=True)
subprocess.run(['gcc','-O2','-Wl,--export-dynamic','-o',str(out/'run'),str(out/'run.c'),'-ldl'],check=True)
files={n:base64.b64encode((out/n).read_bytes()).decode()for n in ['run','fixture.so']}
body=r'''from pathlib import Path
import subprocess,os,pwd,json,base64,shutil
assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()=='997d54fe-04b5-4829-baa5-dd172b8de55b'
assert subprocess.check_output(['pidof','lipstick'],text=True).strip()=='9157'
assert Path('/sys/class/backlight/panel0-backlight/actual_brightness').read_text().strip()=='0'
stage=Path('/home/art/test/noload320');assert not stage.exists();stage.mkdir(mode=0o755)
try:
 for n,v in FILES.items():(stage/n).write_bytes(base64.b64decode(v));(stage/n).chmod(0o755)
 (stage/'config').mkdir();root=Path('/home/art/releases/api29-r320g-native-candidate');u=pwd.getpwnam('defaultuser')
 env=dict(os.environ,ANDROID_ROOT=str(root),SAILDROID_STRICT_LINK='1',BIONIC_TRANSLATION_CONFIG_DIR=str(stage/'config'),LD_LIBRARY_PATH=str(root/'lib')+':/home/art/lib')
 q=subprocess.run([str(stage/'run'),str(root/'lib/libdl_bio.so.0'),str(stage),str(stage/'fixture.so')],env=env,user=u.pw_uid,group=u.pw_gid,extra_groups=os.getgrouplist(u.pw_name,u.pw_gid),capture_output=True,text=True,timeout=15)
 print(json.dumps(dict(passed=q.returncode==0,exit=q.returncode,stdout=q.stdout,stderr=q.stderr[-3000:],uid=u.pw_uid)))
 assert q.returncode==0
finally:
 shutil.rmtree(stage)
 assert Path('/sys/class/backlight/panel0-backlight/actual_brightness').read_text().strip()=='0'
'''
e=dict(os.environ,SSHPASS=os.environ['SSHPASS']);tag='wechat320-noload-fixture'
subprocess.run(['bash',str(r/'scripts/devlock.sh'),'acquire','0',tag],env=e,check=True,timeout=15)
try:
 q=subprocess.run(['sshpass','-e','ssh','-o','ConnectTimeout=6','root@bonito','python3','-'],input='FILES='+repr(files)+'\n'+body,env=e,capture_output=True,text=True,timeout=25)
 (b/'phone-noload-fixture.stdout').write_text(q.stdout);(b/'phone-noload-fixture.stderr').write_text(q.stderr);print(q.stdout,q.stderr);q.check_returncode();(b/'phone-noload-fixture.json').write_text(json.dumps(json.loads(q.stdout),indent=2)+'\n')
finally:subprocess.run(['bash',str(r/'scripts/devlock.sh'),'release',tag],env=e,check=True,timeout=15)
