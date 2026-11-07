from pathlib import Path
import subprocess,json,os,ast
repo=Path('/media/psf/Home/WorkSpace/saidroid-next');b=repo/'build/evidence/qq-cover-perf306-20261103-v1';env=dict(os.environ,SSHPASS=os.environ['SSHPASS']);tag='qq-cover-perf306-baseline';held=False
body='CFG='+repr(json.loads((b/'inventory.json').read_text()))+'\n'+(repo/'scripts/cts/display_cleanup.py').read_text()+'\n'+(b/'baseline-phone.py').read_text();ast.parse(body)
try:
 p=subprocess.run(['bash',str(repo/'scripts/devlock.sh'),'acquire','0',tag],env=env,text=True,capture_output=True,timeout=20);print(p.stdout,p.stderr,flush=True);assert p.returncode==0;held=True
 with(b/'quiesce-before.log').open('ab',buffering=0)as stream:q=subprocess.run(['python3',str(repo/'scripts/perf/close-owned-vm.py')],env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=180)
 assert q.returncode==0,'Pre-launch owned cleanup failed'
 p=subprocess.run(['sshpass','-e','ssh','-o','ConnectTimeout=6','root@bonito','python3','-'],input=body,env=env,text=True,capture_output=True,timeout=220);(b/'remote-stdout-private.log').write_text(p.stdout);(b/'remote-stderr.log').write_text(p.stderr);print(p.stdout,p.stderr,flush=True)
 q=subprocess.run(['sshpass','-e','scp','-O','-r','root@bonito:/home/art/test/qq-cover-perf306-baseline-v1',str(b/'baseline-phone')],env=env,capture_output=True,text=True,timeout=45);assert q.returncode==0,q.stderr
 (b/'execution.json').write_text(json.dumps(dict(remote_code=p.returncode,copy_code=q.returncode),indent=2)+'\n');assert p.returncode==0,p.stderr
finally:
 if held:
  with (b/'quiesce-after.log').open('ab',buffering=0)as stream:q=subprocess.run(['python3',str(repo/'scripts/perf/close-owned-vm.py')],env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=180)
  assert q.returncode==0,'Owned cleanup failed'
  p=subprocess.run(['bash',str(repo/'scripts/devlock.sh'),'release',tag],env=env,text=True,capture_output=True,timeout=20);(b/'release.json').write_text(json.dumps(dict(code=p.returncode,stdout=p.stdout,stderr=p.stderr),indent=2)+'\n');print(p.stdout,p.stderr,flush=True)
