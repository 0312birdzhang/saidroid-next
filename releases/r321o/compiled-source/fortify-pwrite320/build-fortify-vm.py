from pathlib import Path
import json,hashlib,subprocess,shutil
r=Path('/media/psf/Home/WorkSpace/saidroid-next');b=Path(__file__).parent;prior=r/'build/evidence/qq-picker-camera-settings313-20261103-v1/v24/frame-native';meta=json.loads((prior/'manifest.json').read_text());out=b/'fortify-native-v1';out.mkdir();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();cmd=meta['command'];commands=[]
for label in ['baseline','candidate']:
 args=list(cmd);args[args.index('-o')+1]=str(out/(label+'.so'))
 for i,v in enumerate(args):
  if v.endswith('.c'):
   p=Path(v);n=p.relative_to(r);source=prior/'source'/n;assert sha(source)==meta['sources'][str(n)]
   if label=='candidate'and n==Path('native/compat/api29-host.c'):source=r/n
   args[i]=str(source)
 commands.append(args)
 with(out/(label+'.log')).open('wb')as f:subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=80)
assert sha(out/'baseline.so')==meta['candidate_sha256']=='9547f55595b22b72e309cb57187bb293d38ec8851a4c2dad5088485aa22718a7'
def defined(p):return {tuple(l.split()[1:])for l in subprocess.check_output(['nm','-D','--defined-only',str(p)],text=True).splitlines()}
a=defined(out/'baseline.so');z=defined(out/'candidate.so');assert a<=z and z-a=={('T','bionic___pwrite_chk')},z-a
shutil.copyfile(out/'candidate.so',out/'libsdhost29.so');record=dict(passed=True,baseline_byte_identical=True,baseline_sha256=sha(out/'baseline.so'),candidate_sha256=sha(out/'candidate.so'),source_sha256=sha(r/'native/compat/api29-host.c'),path=str(out/'libsdhost29.so'),commands=commands);(b/'fortify-build-v1.json').write_text(json.dumps(record,indent=2)+'\n');print('FORTIFY320_BUILD=passed')
