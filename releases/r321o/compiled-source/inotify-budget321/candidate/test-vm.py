from pathlib import Path
import subprocess,json,hashlib,os,shutil,time
p=Path(__file__).parent;meta=json.loads((p/'build.json').read_text());assert meta['passed'];sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
for name,key in [('candidate.so','candidate_sha256'),('fixture.so','fixture_sha256'),('cancel-fixture','cancel_sha256')]:assert sha(p/name)==meta[key]
out=p/'tests';out.mkdir();results=[]
for label,cmd in [('policy',['runuser','-u','nobody','--','python3',str(p/'source/fixture.py'),str(p/'fixture.so')]),('cancellation',['runuser','-u','nobody','--',str(p/'cancel-fixture'),str(p/'fixture.so')])]:
 tick=time.monotonic();q=subprocess.run(cmd,text=True,capture_output=True,timeout=90);(out/(label+'.stdout')).write_text(q.stdout);(out/(label+'.stderr')).write_text(q.stderr)
 row={'case':label,'returncode':q.returncode,'seconds':time.monotonic()-tick,'command':cmd,'passed':q.returncode==0};results.append(row)
 if q.returncode:print(q.stdout+q.stderr);raise SystemExit(q.returncode)
 if label=='policy':assert json.loads(q.stdout)['passed']
 else:assert 'CANCELLATION_GUARD=passed' in q.stdout
# The combined production-form candidate (no fixture configuration) must
# preserve the own-mem event sequence and actual open/close positive controls.
mem_fixture=p.parent/'signal-causality-v1/proc-mem-events.py';shutil.copyfile(mem_fixture,out/'proc-mem-events.py')
runtime=Path('/var/tmp/saidroid-no-opath-production-runtime');assert not runtime.exists();runtime.mkdir(mode=0o700);os.chown(runtime,65534,65534)
try:
 for label,args in [('libc',[]),('baseline',[str(p/'baseline.so')]),('candidate',[str(p/'candidate.so')])]:
  cmd=['bwrap','--ro-bind','/','/','--tmpfs','/run/user','--dir','/run/user/65534','--bind',str(runtime),'/run/user/65534','--unshare-pid','--proc','/proc','--','runuser','-u','nobody','--','python3',str(out/'proc-mem-events.py')]+args
  q=subprocess.run(cmd,text=True,capture_output=True,timeout=15);(out/('mem-'+label+'.stdout')).write_text(q.stdout);(out/('mem-'+label+'.stderr')).write_text(q.stderr);q.check_returncode();value=json.loads(q.stdout);assert value['passed'];assert value['immediate']['events']==[]
  results.append({'case':'production-own-mem-'+label,'passed':True,'command':cmd,'result':value})
finally:shutil.rmtree(runtime)
result={'passed':True,'candidate_sha256':meta['candidate_sha256'],'phone_accessed':False,'accepted_runtime_changed':False,'cases':results};(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':True,'candidate_sha256':meta['candidate_sha256'],'cases':[{'case':x['case'],'passed':x['passed']}for x in results]}),flush=True)
