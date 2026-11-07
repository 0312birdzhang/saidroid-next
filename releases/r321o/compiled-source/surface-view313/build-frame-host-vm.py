from pathlib import Path
import subprocess,json,hashlib,shutil
r=Path('/media/psf/Home/WorkSpace/saidroid-next');b=Path(__file__).parent;o=b/'frame-native';o.mkdir();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();meta=json.loads((r/'build/evidence/qq-strerror302-20261103-v1/native-build.json').read_text());cmd=list(meta['command']);sources=[Path(n)for n in cmd if n.endswith('.c')];before={str(p.relative_to(r)):sha(p)for p in sources};cmd[cmd.index('-o')+1]=str(o/'baseline-libsdhost29.so')
with(o/'baseline.log').open('ab',buffering=0)as f:subprocess.run(cmd,check=True,stdout=f,stderr=subprocess.STDOUT,timeout=90)
assert sha(o/'baseline-libsdhost29.so')==meta['candidate_sha256']=='2448e27b5b9ad811f803d1d816fe97df4cfdb67f20b4116e186c3238b2615dea'
original=next(p for p in sources if p.name=='api29-egl-host.c');assert sha(original)==sha(r/'scripts/api29/surface-view-compat/baseline/api29-egl-host.c');new=r/'scripts/api29/surface-view-compat/source/api29-egl-host.c';cmd[cmd.index(str(original))]=str(new);cmd[cmd.index('-o')+1]=str(o/'libsdhost29.so')
with(o/'build.log').open('ab',buffering=0)as f:subprocess.run(cmd,check=True,stdout=f,stderr=subprocess.STDOUT,timeout=90)
for p in sources:
 if p==original:p=new
 target=o/'source'/p.relative_to(r);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
d=dict(passed=True,baseline_byte_identical=True,baseline_sha256=meta['candidate_sha256'],candidate_sha256=sha(o/'libsdhost29.so'),baseline_sources=before,sources={str(p.relative_to(o/'source')):sha(p)for p in(o/'source').rglob('*')if p.is_file()},command=cmd);(o/'manifest.json').write_text(json.dumps(d,indent=2)+'\n');print('FRAME_HOST_BUILD=passed',flush=True)
