from pathlib import Path
import json,subprocess,hashlib
r=Path('/media/psf/Home/WorkSpace/saidroid-next');b=Path(__file__).parent;old=json.loads((r/'build/evidence/qq-picker-camera-settings313-20261103-v1/v26/window-native/manifest.json').read_text());cmd=list(old['command']);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();o=b/'window-native';o.mkdir();cmd[cmd.index('-o')+1]=str(o/'baseline.so')
with(o/'baseline.log').open('ab',buffering=0)as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=90)
assert sha(o/'baseline.so')==old['candidate_sha256']
cmd[cmd.index(str(r/'scripts/api29/surface-view-compat/source/sdwindow.c'))]=str(r/'scripts/api29/window-retirement-compat/source/sdwindow.c');cmd[cmd.index('-o')+1]=str(o/'libsdwindow.so')
with(o/'build.log').open('ab',buffering=0)as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=90)
d=dict(passed=True,baseline_byte_identical=True,baseline_sha256=old['candidate_sha256'],candidate_sha256=sha(o/'libsdwindow.so'),command=cmd);(o/'manifest.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d))
