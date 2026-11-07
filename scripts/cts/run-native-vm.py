"""Attempt an official 64-bit CTS ELF as the ordinary phone user."""
from pathlib import Path
import json,sys,os,subprocess
plan=Path(sys.argv[1]);config=json.loads(plan.read_text());repo=Path('/media/psf/Home/WorkSpace/saidroid-next');os.environ['SSHPASS']=os.environ['SSHPASS'];mux=['-o','ControlMaster=auto','-o','ControlPersist=45','-o','ControlPath=/var/tmp/saidroid-cts-transport-%C'];ssh=['sshpass','-e','ssh',*mux,'-o','ConnectTimeout=6','root@bonito'];lock=repo/'scripts/devlock.sh';base='/home/art/test/'+config['label']
subprocess.run(['bash',str(lock),'acquire','0','cts-native-attempt'],check=True,timeout=15)
preflight='from pathlib import Path;assert "ID=sailfishos" in Path("/etc/sailfish-release").read_text();expected='+repr(config.get('expected_boot'))+';assert not expected or Path("/proc/sys/kernel/random/boot_id").read_text().strip()==expected,"Suite boot identity changed before native preparation"'
try:
 subprocess.run(ssh+['python3','-'],input=preflight.encode(),check=True,timeout=12)
 subprocess.run(ssh+['test ! -e '+base+' && install -d -m0755 '+base],check=True,timeout=10)
 subprocess.run(['sshpass','-e','scp','-O',*mux,str(plan.parent/config['binary']),'root@bonito:'+base+'/test'],check=True,timeout=45)
 body='CONFIG='+repr(config)+'\n'+r'''
from pathlib import Path
import subprocess,os,pwd,json,hashlib,struct,signal
assert Path('/home/art/test/.device-lock/owner').read_text().startswith('cts-native-attempt|')
base=Path('/home/art/test')/CONFIG['label'];binary=base/'test';assert hashlib.sha256(binary.read_bytes()).hexdigest()==CONFIG['sha256'];u=pwd.getpwnam('defaultuser');binary.chmod(0o755);os.chown(base,u.pw_uid,u.pw_gid)
b=binary.read_bytes();assert b[:5]==b'\x7fELF\x02'and struct.unpack_from('<H',b,18)[0]==183
start=struct.unpack_from('<Q',b,32)[0];size,count=struct.unpack_from('<HH',b,54);interpreter=None
for i in range(count):
 p=start+i*size
 if struct.unpack_from('<I',b,p)[0]==3:
  offset=struct.unpack_from('<Q',b,p+8)[0];length=struct.unpack_from('<Q',b,p+32)[0];interpreter=b[offset:offset+length].rstrip(b'\0').decode()
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();lip=subprocess.check_output(['pidof','lipstick'],text=True).strip();result=dict(status='BLOCKED',interpreter=interpreter,interpreter_exists=Path(interpreter).exists()if interpreter else None,module=CONFIG['module'],actual_exec_attempt=True,native_runtime_scope='system-android-ELF-interpreter-not-SailDroid-in-process-glibc-bridge',formal_module_acceptance=False)
assert not CONFIG.get('expected_boot')or CONFIG['expected_boot']==boot
subprocess.run(['mcetool','--set-never-blank=disabled','--blank-screen'],check=True,timeout=5)
watch=subprocess.Popen(['python3','-c',"import subprocess,time;time.sleep(75);subprocess.run(['mcetool','--set-never-blank=disabled','--blank-screen'])"],start_new_session=True)
try:
 p=subprocess.Popen([str(binary),'--gtest_list_tests'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,user=u.pw_uid,group=u.pw_gid,extra_groups=os.getgrouplist(u.pw_name,u.pw_gid),start_new_session=True)
 try:
  out=p.communicate(timeout=15)[0];result.update(exit=p.returncode,output=out.decode(errors='replace')[:12000],status='DISCOVERY_FAILED'if p.returncode else'DISCOVERED_NOT_EXECUTED')
  if p.returncode==0 and CONFIG['module']!='CtsKernelConfigTestCases':
   result['execution_attempt']=True
   with(base/'test-output.log').open('wb')as log:
    run=subprocess.Popen([str(binary),'--gtest_color=no','--gtest_output=xml:'+str(base/'gtest.xml')],stdout=log,stderr=subprocess.STDOUT,user=u.pw_uid,group=u.pw_gid,extra_groups=os.getgrouplist(u.pw_name,u.pw_gid),start_new_session=True)
    try:run.wait(timeout=45);result.update(test_exit=run.returncode,status='EXECUTED'if run.returncode==0 else'TEST_FAILED')
    except subprocess.TimeoutExpired:os.killpg(run.pid,signal.SIGKILL);run.wait();result.update(status='TIMEOUT',reason='Native execution exceeded bounded 45 seconds')
   result['test_output']=(base/'test-output.log').read_text(errors='replace')[-16000:]
   report=base/'gtest.xml'
   if report.exists():result['gtest_xml']=report.read_text()
  elif p.returncode==0:result.update(status='BLOCKED',reason='Official kernel module requires a reboot and pmsg preparation; no reboot requested by this adapter')
 except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.communicate();result['reason']='Native discovery deadline exceeded'
except OSError as e:result.update(reason=str(e),errno=e.errno)
subprocess.run(['mcetool','--set-never-blank=disabled','--blank-screen'],check=True,timeout=5)
assert boot==Path('/proc/sys/kernel/random/boot_id').read_text().strip()and lip==subprocess.check_output(['pidof','lipstick'],text=True).strip();assert Path('/sys/class/backlight/panel0-backlight/actual_brightness').read_text().strip()=='0'
watch.terminate();watch.wait(timeout=3)
print(json.dumps(result))
'''
 r=subprocess.run(ssh+['python3','-'],input=body.encode(),check=True,capture_output=True,timeout=80);value=json.loads(r.stdout);(plan.parent/'native-result.json').write_text(json.dumps(value,indent=2)+'\n')
 subprocess.run(ssh+['rm','-rf',base],check=True,timeout=8);print('NATIVE_MODULE='+config['module']+'|'+value['status'])
finally:
 try:identity=subprocess.run(ssh+['python3','-'],input=preflight.encode(),capture_output=True,timeout=12).returncode==0
 except subprocess.TimeoutExpired:identity=False
 if identity:subprocess.run(ssh+['mcetool','--set-never-blank=disabled','--blank-screen'],timeout=5)
 else:print('CLEANUP_DEFERRED=device-identity-not-confirmed; serial dispatcher must stop',flush=True)
 subprocess.run(['bash',str(lock),'release','cts-native-attempt'],check=True,timeout=15)
