from pathlib import Path
import subprocess,json,hashlib,os
r=Path('/media/psf/Home/WorkSpace/saidroid-next');b=Path(__file__).parent;out=b/'native-build-v1';out.mkdir();prior=r/'build/evidence/qq-cover-perf306-20261103-v1';meta=json.loads((prior/'native-build-v2.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();cmd=next(c for c in meta['commands']if any(v.endswith('/native-build-v2/libsdwindow.so')for v in c));oldsource=prior/'source/native/window/sdwindow.c';assert sha(oldsource)==meta['sources']['native/window/sdwindow.c'];cmd=cmd[:];cmd[cmd.index('-o')+1]=str(out/'baseline.so')
with(b/'native-baseline.log').open('ab',buffering=0)as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=180)
assert sha(out/'baseline.so')==meta['files']['libsdwindow.so']['sha256'];cmd[cmd.index('-o')+1]=str(out/'libsdwindow.so');cmd[cmd.index(str(oldsource))]=str(b/'source/native/window/sdwindow.c')
with(b/'native-candidate.log').open('ab',buffering=0)as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=180)
record=dict(passed=True,baseline_byte_identical=True,source_sha256=sha(b/'source/native/window/sdwindow.c'),sha256=sha(out/'libsdwindow.so'),path=str(out/'libsdwindow.so'),command=cmd);(b/'native-build.json').write_text(json.dumps(record,indent=2)+'\n');print('NATIVE307_BUILD=passed',flush=True)
