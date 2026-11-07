from pathlib import Path
import subprocess,json,hashlib,shutil
r=Path('/media/psf/Home/WorkSpace/saidroid-next');b=Path(__file__).parent;out=b/'hostapi-native-v2';out.mkdir();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();meta=json.loads((r/'build/evidence/qq-camera-capability304-20261103-v1/native-build.json').read_text());commands=[];original=list(meta['commands'][-1]);oldapi=next(n for n in original if n.endswith('/host-api.cpp'));module=r/'scripts/api29/thermal-service-compat'
assert sha(Path(oldapi))==sha(module/'baseline/host-api.cpp')
for label in ['baseline','candidate']:
 cmd=list(original);cmd[cmd.index('-o')+1]=str(out/(label+'.so'));cmd[cmd.index(oldapi)]=str(module/('baseline'if label=='baseline'else'source')/'host-api.cpp');commands.append(cmd)
 with(out/(label+'.log')).open('wb')as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=90)
assert sha(out/'baseline.so')==meta['candidate_sha256']=='d1ccb55159bcdaeb04d8028a4a351b13beb4a37a0fa5c3d10ed48d3fa7e4584b','Host API baseline differs'
def symbols(p):return {tuple(l.split()[1:])for l in subprocess.check_output(['nm','-D','--defined-only',str(p)],text=True).splitlines()}
a=symbols(out/'baseline.so');z=symbols(out/'candidate.so');assert a<=z and z-a=={('T','Java_org_saildroid_host_HostApi_thermalState')},z-a
shutil.copyfile(out/'candidate.so',out/'libsdhostapi.so');record=dict(passed=True,baseline_byte_identical=True,path=str(out/'libsdhostapi.so'),sha256=sha(out/'libsdhostapi.so'),commands=commands,sources={n:sha(Path(n))for n in commands[-1]if n.endswith(('.cpp','.o'))});(b/'hostapi-build-v1.json').write_text(json.dumps(record,indent=2)+'\n');print('THERMAL_HOST_BUILD=passed')
