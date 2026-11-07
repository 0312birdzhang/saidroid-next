from pathlib import Path
import subprocess,json,hashlib
r=Path('/media/psf/Home/WorkSpace/saidroid-next');b=Path(__file__).parent;out=b/'host-build-v1';out.mkdir();prior=r/'build/evidence/qq-cover-perf306-20261103-v1';meta=json.loads((prior/'native-build-v2.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();cmd=meta['commands'][-1][:];cmd[cmd.index('-o')+1]=str(out/'baseline-host')
with(b/'host-baseline.log').open('ab',buffering=0)as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=180)
assert sha(out/'baseline-host')==meta['files']['saildroid-host']['sha256'];commands=[cmd[:]]
cmd[cmd.index('-o')+1]=str(out/'saildroid-host')
for n in ['host-entry.cpp','saildroid-app.cpp']:
 old=next(v for v in cmd if v.endswith('/'+n));cmd[cmd.index(old)]=str(b/'source/native/host'/n)
with(b/'host-candidate.log').open('ab',buffering=0)as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=180)
commands.append(cmd);result=dict(passed=True,baseline_byte_identical=True,path=str(out/'saildroid-host'),sha256=sha(out/'saildroid-host'),sources={str(p.relative_to(b/'source')):sha(p)for p in (b/'source/native/host').glob('*.cpp')},commands=commands,scope='Keep FIFO heavy admission; overlap at most one app VM initialization with broker initialization; wait for verified broker before invoking Java.');(b/'host-build.json').write_text(json.dumps(result,indent=2)+'\n');print('HOST308_BUILD=passed',flush=True)
