from pathlib import Path
import subprocess,json,hashlib
r=Path('/media/psf/Home/WorkSpace/saidroid-next');b=Path(__file__).parent;module=r/'native/compat/host-worker-identity';out=b/'worker-host-v1';out.mkdir();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();meta=json.loads((r/'build/evidence/wechat-startup320-20261104/library-path-build-v1.json').read_text());cmd=meta['commands'][-1][:];old=next(v for v in cmd if v.endswith('/host-entry.cpp'));assert sha(Path(old))==meta['source_after'];commands=[]
for label in ['baseline','candidate']:
 c=cmd[:];c[c.index('-o')+1]=str(out/('baseline-host'if label=='baseline'else'saildroid-host'))
 if label=='candidate':c[c.index(old)]=str(module/'host-entry.cpp')
 commands.append(c)
 with(out/(label+'.log')).open('ab',buffering=0)as f:subprocess.run(c,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=180)
 if label=='baseline':assert sha(out/'baseline-host')==meta['sha256'],'Baseline not reproduced'
result=dict(passed=True,baseline_byte_identical=True,path=str(out/'saildroid-host'),sha256=sha(out/'saildroid-host'),commands=commands,sources={str(p):sha(p)for p in module.iterdir()if p.is_file()});(b/'worker-host-build-v1.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in ['commands','sources']}))
