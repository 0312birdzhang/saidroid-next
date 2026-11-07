from pathlib import Path
import os,json,hashlib,subprocess
os.umask(0o022)
repo=Path('/media/psf/Home/WorkSpace/saidroid-next');b=repo/'build/evidence/qq-audio-properties293-20261102-v1';out=Path('/var/tmp/saidroid-audio-properties293-native-v2');out.mkdir();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();old=json.loads((repo/'build/evidence/qq-manifest-receivers292-20261102-v1/native-build.json').read_text());commands=[]
cmd=list(old['commands'][-1]);audio=next(Path(v)for v in cmd if v.endswith('/host-audio.cpp'));assert sha(audio)==sha(repo/'native/host/host-audio.cpp')
def run(label,path):
 command=list(cmd);command[command.index('-o')+1]=str(out/(label+'.so'));command[command.index(str(audio))]=str(path);commands.append(command)
 with(b/(label+'.log')).open('ab',buffering=0)as stream:subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT,check=True,timeout=180)
 return out/(label+'.so')
baseline=run('baseline',audio);assert sha(baseline)==old['binary_sha256']['libsdhostapi.so']
candidate=run('candidate',b/'source/native/host/host-audio.cpp')
def symbols(p):return sorted(' '.join(l.split()[3:])for l in subprocess.check_output(['readelf','--dyn-syms','--wide',str(p)],text=True).splitlines()if len(l.split())>=8 and l.split()[0].rstrip(':').isdigit())
assert symbols(candidate)==symbols(baseline)
r=dict(passed=True,builder_sha256=sha(Path(__file__)),baseline_binary_sha256=sha(baseline),binary_sha256=sha(candidate),candidate=str(candidate),baseline_reproduced_byte_identical=True,dynamic_symbols_unchanged=True,commands=commands)
(out/'manifest.json').write_text(json.dumps(r,indent=2)+'\n');(b/'native-build.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2),flush=True)
