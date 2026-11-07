"""Rebuild a frozen libsdhost29 command, verify its baseline, then add the bridge."""
from pathlib import Path
import argparse,hashlib,json,subprocess
p=argparse.ArgumentParser()
p.add_argument('--baseline-build-json',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args();source=Path(__file__).with_name('strerror-api29.c');proof=json.loads(a.baseline_build_json.read_text());assert proof['passed'];out=a.output;out.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
commands=[c for c in proof['commands']if '-o'in c and Path(c[c.index('-o')+1]).name=='libsdhost29.so'];assert len(commands)==1
baseline=list(commands[0]);baseline[baseline.index('-o')+1]=str(out/'baseline.so');subprocess.run(baseline,check=True)
assert sha(out/'baseline.so')==proof['files']['libsdhost29.so'],'Baseline source closure changed'
cmd=list(baseline);cmd[cmd.index('-o')+1]=str(out/'libsdhost29.so');cmd.insert(cmd.index('-ldl'),str(source));subprocess.run(cmd,check=True)
inputs=[Path(v)for v in cmd if v.endswith(('.c','.cpp'))]
v=dict(passed=True,baseline_build_json_sha256=sha(a.baseline_build_json),baseline_byte_identical=True,baseline_sha256=sha(out/'baseline.so'),candidate_sha256=sha(out/'libsdhost29.so'),command=cmd,sources={str(f):sha(f)for f in inputs},scope='Native build only; ABI and application acceptance require separate probes.');(out/'manifest.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v,indent=2))
