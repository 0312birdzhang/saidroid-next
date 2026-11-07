from pathlib import Path
import subprocess,json,os,hashlib,base64,ast,sys
r=Path('/media/psf/Home/WorkSpace/saidroid-next');b=Path(__file__).parent;env=dict(os.environ,SSHPASS=os.environ['SSHPASS']);held=False;sdk=int(sys.argv[1]);revision=sys.argv[2]if len(sys.argv)>2 else'r307';fixtures=json.loads((b/'fixtures.json').read_text());f=next(x for x in fixtures['apks']if x['target_sdk']==sdk);p=Path(f['path']);assert hashlib.sha256(p.read_bytes()).hexdigest()==f['sha256'];label='cover307-'+revision+'-sdk'+str(sdk)+'-v3';cfg=dict(root='/home/art/releases/api29-'+revision+'-native-candidate',target_sdk=sdk,expected='pass'if revision=='r307'else'negative-control',label=label,sha256=f['sha256'],apk=base64.b64encode(p.read_bytes()).decode());body='PNG_HELPER='+repr((r/'scripts/api29/tests/sd_covers.py').read_text())+'\nCFG='+repr(cfg)+'\n'+(r/'scripts/cts/display_cleanup.py').read_text()+'\n'+(b/'probe-fixture-v3-phone.py').read_text();ast.parse(body)
try:
 q=subprocess.run(['bash',str(r/'scripts/devlock.sh'),'acquire','0','cover307-fixture'],env=env,text=True,capture_output=True,timeout=20);print(q.stdout,q.stderr,flush=True);assert q.returncode==0;held=True
 with(b/(label+'-quiesce.log')).open('ab',buffering=0)as stream:q=subprocess.run(['python3',str(r/'scripts/perf/close-owned-vm.py')],env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=180);assert q.returncode==0
 q=subprocess.run(['sshpass','-e','ssh','-o','ConnectTimeout=6','root@bonito','python3','-'],input=body,env=env,capture_output=True,text=True,timeout=140);(b/(label+'.stdout')).write_text(q.stdout);(b/(label+'.stderr')).write_text(q.stderr);print(q.stdout,q.stderr,flush=True)
 c=subprocess.run(['sshpass','-e','scp','-O','-r','root@bonito:/home/art/test/'+label,str(b/label)],env=env,text=True,capture_output=True,timeout=30);assert c.returncode==0,c.stderr;assert q.returncode==0,q.stderr
finally:
 if held:
  with(b/(label+'-quiesce-after.log')).open('ab',buffering=0)as stream:q=subprocess.run(['python3',str(r/'scripts/perf/close-owned-vm.py')],env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=180);assert q.returncode==0
  q=subprocess.run(['bash',str(r/'scripts/devlock.sh'),'release','cover307-fixture'],env=env,text=True,capture_output=True,timeout=20);print(q.stdout,q.stderr,flush=True);assert q.returncode==0
