from pathlib import Path
import subprocess,os,json,base64,hashlib,time
r=Path('/media/psf/Home/WorkSpace/saidroid-next');b=Path(__file__).parent;env=dict(os.environ,SSHPASS=os.environ['SSHPASS']);exe=b/'error-fixture';data=exe.read_bytes();meta=json.loads((b/'native-build-v3.json').read_text());stage=b/'stage.json';deadline=time.monotonic()+60
while not stage.exists()and time.monotonic()<deadline:time.sleep(.5)
assert stage.exists()and json.loads(stage.read_text())['passed'];held=False
body=r'''from pathlib import Path
import os,subprocess,json,base64,hashlib,pwd
assert 'ID=sailfishos'in Path('/etc/sailfish-release').read_text();assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()=='4fab5d11-f3fd-4a5f-8724-f20785e27485';assert Path('/sys/class/backlight/panel0-backlight/actual_brightness').read_text().strip()=='0';assert Path('/home/art/test/.device-lock/owner').read_text().startswith('linker310-fixture|')
b=Path('/home/art/test/linker310-errors-fixture-v1');b.mkdir(mode=0o755);p=b/'fixture';p.write_bytes(base64.b64decode(EXE));assert hashlib.sha256(p.read_bytes()).hexdigest()==SHA;p.chmod(0o755);u=pwd.getpwnam('defaultuser');results=[]
for revision,code in [('r309',1),('r310',0)]:
 root=Path('/home/art/releases/api29-'+revision+'-native-candidate');env=dict(os.environ,LD_LIBRARY_PATH=str(root/'lib')+':/home/art/lib');q=subprocess.run([str(p),str(root/'lib/libdl_bio.so.0')],env=env,user=u.pw_uid,group=u.pw_gid,extra_groups=os.getgrouplist(u.pw_name,u.pw_gid),capture_output=True,text=True,timeout=30);(b/(revision+'.stdout')).write_text(q.stdout);(b/(revision+'.stderr')).write_text(q.stderr);assert q.returncode==code,q.stderr[-1500:];results.append(dict(revision=revision,expected_code=code,code=q.returncode,output=q.stdout.strip(),library_sha256=hashlib.sha256((root/'lib/libdl_bio.so.0').read_bytes()).hexdigest()))
print(json.dumps(dict(passed=True,results=results,brightness=Path('/sys/class/backlight/panel0-backlight/actual_brightness').read_text().strip(),daily=str(Path('/home/art/api29-root').resolve()))))
'''
try:
 p=subprocess.run(['bash',str(r/'scripts/devlock.sh'),'acquire','0','linker310-fixture'],env=env,text=True,capture_output=True,timeout=20);print(p.stdout,p.stderr,flush=True);assert p.returncode==0;held=True
 p=subprocess.run(['sshpass','-e','ssh','-o','ConnectTimeout=6','root@bonito','python3','-'],input='EXE='+repr(base64.b64encode(data).decode())+'\nSHA='+repr(hashlib.sha256(data).hexdigest())+'\n'+body,env=env,capture_output=True,text=True,timeout=90);print(p.stdout,p.stderr,flush=True);assert p.returncode==0,p.stderr;(b/'phone-fixture-results.json').write_text(json.dumps(json.loads(p.stdout),indent=2)+'\n')
finally:
 if held:
  p=subprocess.run(['bash',str(r/'scripts/devlock.sh'),'release','linker310-fixture'],env=env,text=True,capture_output=True,timeout=20);print(p.stdout,p.stderr,flush=True);assert p.returncode==0
