from pathlib import Path
import os,subprocess
REPO=Path('/media/psf/Home/WorkSpace/saidroid-next');EV=REPO/'build/evidence/cts-api29-20261030';os.environ['SSHPASS']=os.environ['SSHPASS'];SSH=['sshpass','-e','ssh','-o','ConnectTimeout=6','root@bonito'];lock=REPO/'scripts/devlock.sh'
subprocess.run(['bash',str(lock),'acquire','0','official-verifier-startup'],check=True,timeout=15)
try:
 subprocess.run(['python3',str(REPO/'scripts/perf/close-owned-vm.py')],check=True,timeout=50)
 subprocess.run(['python3',str(REPO/'scripts/cts/install-verifier-vm.py'),'official10r16'],check=True,timeout=60)
 body=r'''
from pathlib import Path
import subprocess,os,pwd,time,json
assert Path('/home/art/test/.device-lock/owner').read_text().startswith('official-verifier-startup|')
assert 'ID=sailfishos'in Path('/etc/sailfish-release').read_text()
pkg='com.android.cts.verifier';base=Path('/home/art/test/cts-verifier-r114-1');base.mkdir(exist_ok=False);u=pwd.getpwnam('defaultuser');boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();lip=subprocess.check_output(['pidof','lipstick'],text=True).strip()
env=dict(os.environ,HOME=u.pw_dir,USER=u.pw_name,LOGNAME=u.pw_name,XDG_RUNTIME_DIR='/run/user/100000',WAYLAND_DISPLAY='../../display/wayland-0',DBUS_SESSION_BUS_ADDRESS='unix:path=/run/user/100000/dbus/user_bus_socket');kw=dict(env=env,user=u.pw_uid,group=u.pw_gid,extra_groups=os.getgrouplist(u.pw_name,u.pw_gid));host='/home/art/releases/api29-r114-native-candidate/libexec/saildroid-app';record=None
watch=subprocess.Popen(['python3','-c',"import time,subprocess;time.sleep(38);subprocess.run(['mcetool','--set-never-blank=disabled','--blank-screen'])"],start_new_session=True)
try:
 subprocess.run(['mcetool','--set-never-blank=disabled','--blank-screen'],check=True,timeout=5)
 with(base/'entry.log').open('w')as out:p=subprocess.Popen([host,'--package',pkg,'--debug-log'],stdout=out,stderr=subprocess.STDOUT,**kw)
 end=time.monotonic()+23
 while time.monotonic()<end:
  state=Path('/run/user/100000/saildroid')/(pkg+'.json')
  if state.exists():record=json.loads(state.read_text())
  if p.poll()is not None:break
  time.sleep(.2)
 text=Path(record['log']).read_text(errors='replace').replace(chr(0),'')if record else''
 result=dict(apk='official-10_r16',pid=record.get('pid')if record else None,exit=p.poll(),drawn='SDWINDOW_SESSION=drawn|'in text,activity_launched='SDACTIVITY=launched|'in text,exceptions=[line[:450]for line in text.splitlines()if line.startswith(('SDRUNTIME=failed','SDRUNTIME=uncaught','SDUNSUPPORTED'))])
 (base/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('CTS_VERIFIER_STARTUP='+json.dumps(result))
finally:
 if record and Path(record['log']).exists():(base/'runtime.log').write_bytes(Path(record['log']).read_bytes())
 subprocess.run([host,'--package',pkg,'--close'],capture_output=True,timeout=18,**kw);subprocess.run([host,'--broker','--close'],capture_output=True,timeout=18,**kw)
 subprocess.run(['mcetool','--set-never-blank=disabled','--blank-screen'],timeout=5);watch.terminate();watch.wait(timeout=3)
 assert Path('/sys/class/backlight/panel0-backlight/actual_brightness').read_text().strip()=='0'
 assert boot==Path('/proc/sys/kernel/random/boot_id').read_text().strip()and lip==subprocess.check_output(['pidof','lipstick'],text=True).strip()
 print('DEVICE_FINAL=OLED-off|boot-and-lipstick-unchanged')
'''
 subprocess.run(SSH+['python3','-'],input=body.encode(),check=True,timeout=100)
 subprocess.run(['sshpass','-e','scp','-O','-r','root@bonito:/home/art/test/cts-verifier-r114-1',str(EV)],check=True,timeout=20)
finally:
 subprocess.run(['python3',str(REPO/'scripts/perf/close-owned-vm.py')],timeout=50)
 subprocess.run(SSH+['mcetool','--set-never-blank=disabled','--blank-screen'],timeout=6)
 subprocess.run(['bash',str(lock),'release','official-verifier-startup'],check=True,timeout=15)
