from pathlib import Path
import os,json,hashlib,subprocess
os.umask(0o022)
repo=Path('/media/psf/Home/WorkSpace/saidroid-next');b=repo/'build/evidence/qq-audio-sco294-20261102-v1';out=Path('/var/tmp/saidroid-audio-sco294-native-v2');out.mkdir();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();old=json.loads((repo/'build/evidence/qq-audio-properties293-20261102-v1/native-build.json').read_text());commands=[]
cmd=list(old['commands'][-1]);audio=next(Path(v)for v in cmd if v.endswith('/host-audio.cpp'));assert sha(audio)==sha(repo/'build/evidence/qq-audio-properties293-20261102-v1/source/native/host/host-audio.cpp')
def run(label,path):
 command=list(cmd);command[command.index('-o')+1]=str(out/(label+'.so'));command[command.index(str(audio))]=str(path);commands.append(command)
 with(b/(label+'.log')).open('ab',buffering=0)as stream:subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT,check=True,timeout=180)
 return out/(label+'.so')
baseline=run('baseline',audio);assert sha(baseline)==old['binary_sha256']
candidate=run('candidate',b/'source/native/host/host-audio.cpp')
def symbols(p):
 d={}
 for line in subprocess.check_output(['readelf','--dyn-syms','--wide',str(p)],text=True).splitlines():
  v=line.split()
  if len(v)>=8 and v[0].rstrip(':').isdigit():d[v[7]]=(v[3],v[4],v[5],v[6]=='UND')
 return d
a=symbols(baseline);z=symbols(candidate);assert all(z.get(n)==v for n,v in a.items());assert set(z)-set(a)=={'pa_proplist_gets@PULSE_0'}and z['pa_proplist_gets@PULSE_0'][3]
r=dict(passed=True,builder_sha256=sha(Path(__file__)),baseline_binary_sha256=sha(baseline),binary_sha256=sha(candidate),candidate=str(candidate),baseline_reproduced_byte_identical=True,existing_dynamic_symbols_unchanged=True,exported_dynamic_symbols_unchanged=True,added_imports=["pa_proplist_gets@PULSE_0"],commands=commands)
(out/'manifest.json').write_text(json.dumps(r,indent=2)+'\n');(b/'native-build.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2),flush=True)
