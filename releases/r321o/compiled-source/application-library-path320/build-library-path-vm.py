from pathlib import Path
import subprocess,json,hashlib
r=Path('/media/psf/Home/WorkSpace/saidroid-next');b=Path(__file__).parent;out=b/'library-path-native-v1';out.mkdir();module=r/'native/compat/application-library-path';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
meta=json.loads((r/'build/evidence/qq-cover-final308-20261103-v1/host-build.json').read_text());cmd=meta['commands'][-1][:];old=next(v for v in cmd if v.endswith('/host-entry.cpp'));assert sha(Path(old))==sha(module/'baseline-host-entry.cpp')
cmd[cmd.index('-o')+1]=str(out/'baseline-host');commands=[cmd[:]]
with(out/'build.log').open('ab',buffering=0)as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
assert sha(out/'baseline-host')==meta['sha256']=='7c2bc848043799accb33cfacacd4055787bb65647f5989bd815478a073ac297e'
cmd[cmd.index(old)]=str(module/'host-entry.cpp');cmd[cmd.index('-o')+1]=str(out/'saildroid-host');commands.append(cmd[:])
with(out/'build.log').open('ab',buffering=0)as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
proof=dict(passed=True,baseline_byte_identical=True,path=str(out/'saildroid-host'),sha256=sha(out/'saildroid-host'),source_before=sha(module/'baseline-host-entry.cpp'),source_after=sha(module/'host-entry.cpp'),commands=commands)
(b/'library-path-build-v1.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({k:v for k,v in proof.items()if k!='commands'}))
