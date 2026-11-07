from pathlib import Path
import subprocess,json,hashlib,shutil
r=Path('/media/psf/Home/WorkSpace/saidroid-next');b=Path(__file__).parent;o=b/'window-native';o.mkdir(exist_ok=True);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();old=json.loads((r/'build/evidence/qq-cover-buffer309-20261103-v1/native-build.json').read_text());cmd=list(old['command']);sources=[Path(n)for n in cmd if n.endswith('.c')];original=next(p for p in sources if p.name=='sdwindow.c');assert sha(original)==old['source_sha256'];assert sha(original)==sha(r/'scripts/api29/surface-view-compat/baseline/sdwindow.c');cmd[cmd.index('-o')+1]=str(o/'baseline.so')
with(o/'baseline.log').open('ab',buffering=0)as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=90)
assert sha(o/'baseline.so')==old['sha256']=='155c7492b2624f60bbf8e87dd0359b2a0634cbaf32d669185a5ff10fb5ef4780'
source=r/'scripts/api29/surface-view-compat/source/sdwindow.c';cmd[cmd.index(str(original))]=str(source);background=next(p for p in sources if p.name=='sd-hwui-background.c');assert sha(background)==sha(r/'scripts/api29/surface-view-compat/baseline/sd-hwui-background.c');new_background=r/'scripts/api29/surface-view-compat/source/sd-hwui-background.c';cmd[cmd.index(str(background))]=str(new_background);cmd[cmd.index('-o')+1]=str(o/'libsdwindow.so')
with(o/'build.log').open('ab',buffering=0)as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=90)
for p in sources:
 if p==original:p=source
 if p==background:p=new_background
 q=o/'source'/p.relative_to(r);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
d=dict(passed=True,baseline_byte_identical=True,baseline_sha256=old['sha256'],candidate_sha256=sha(o/'libsdwindow.so'),sources={str(p.relative_to(o/'source')):sha(p)for p in(o/'source').rglob('*')if p.is_file()},command=cmd);(o/'manifest.json').write_text(json.dumps(d,indent=2)+'\n');print('HEADLESS_WINDOW_BUILD=passed',flush=True)
