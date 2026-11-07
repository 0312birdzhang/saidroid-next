from pathlib import Path
import subprocess,json,hashlib
r=Path('/media/psf/Home/WorkSpace/saidroid-next');b=Path(__file__).parent;out=b/'audio-connection-native-v3';out.mkdir();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();meta=json.loads((r/'build/evidence/wechat-startup320-20261104/hostapi-build-v1.json').read_text());original=list(meta['commands'][-1]);old=next(n for n in original if n.endswith('/host-audio.cpp'));m=r/'scripts/api29/audio-connection-compat';commands=[]
assert sha(Path(old))==sha(m/'baseline/host-audio.cpp')
for label in ['baseline','candidate']:
 cmd=list(original);cmd[cmd.index('-o')+1]=str(out/(label+'.so'));cmd[cmd.index(old)]=str(m/('baseline'if label=='baseline'else'source')/'host-audio.cpp');commands.append(cmd)
 with(out/(label+'.log')).open('wb')as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=90)
assert sha(out/'baseline.so')==meta['sha256'],'Audio baseline differs'
record=dict(passed=True,baseline_byte_identical=True,path=str(out/'candidate.so'),sha256=sha(out/'candidate.so'),commands=commands,sources={n:sha(Path(n))for n in commands[-1]if n.endswith(('.cpp','.o'))});(b/'audio-connection-build-v3.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
