from pathlib import Path
import subprocess,json,hashlib
r=Path('/media/psf/Home/WorkSpace/saidroid-next');b=Path(__file__).parent;out=Path('/var/tmp/saidroid-strerror302-native-v1');out.mkdir();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=json.loads((r/'build/evidence/qq-surface-texture300-20261102-v1/native-build.json').read_text());commands=old['commands'];baseline=list(next(c for c in commands if any(str(x).endswith('/candidate-host29')for x in c)))if False else list(commands[-3])
assert any(str(v).endswith('/libsdhost29.so')for v in baseline),baseline
baseline[baseline.index('-o')+1]=str(out/'baseline.so');subprocess.run(baseline,check=True);assert sha(out/'baseline.so')==old['files']['libsdhost29.so']
cmd=list(baseline);cmd[cmd.index('-o')+1]=str(out/'libsdhost29.so');cmd.insert(-2,str(r/'native/compat/strerror-api29/strerror-api29.c'));subprocess.run(cmd,check=True)
v=dict(passed=True,output=str(out),baseline_byte_identical=True,baseline_sha256=sha(out/'baseline.so'),candidate_sha256=sha(out/'libsdhost29.so'),command=cmd,source_sha256=sha(r/'native/compat/strerror-api29/strerror-api29.c'));(b/'native-build.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v,indent=2))
