from pathlib import Path
import os,json,hashlib,subprocess,shlex
os.umask(0o022)
repo=Path('/media/psf/Home/WorkSpace/saidroid-next');b=repo/'build/evidence/qq-manifest-receivers292-20261102-v1';out=Path('/var/tmp/saidroid-manifest-receivers292-native-v3');out.mkdir();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();prior=json.loads((repo/'build/evidence/qq-signal-stack291-20261102-v1/bundle/overlay.json').read_text());old=json.loads((b/'baseline-host-manifest.json').read_text());commands=[]
def run(cmd,name):
 commands.append(cmd)
 with(b/(name+'.log')).open('ab',buffering=0)as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=180)
host=list(old['commands'][-1]);entry=next(Path(v)for v in host if v.endswith('/host-entry.cpp'));manager=next(Path(v)for v in host if v.endswith('/host-manager.cpp'));assert sha(entry)==old['sources_after']['host-entry.cpp']==sha(b/'baseline-host-entry.cpp');assert sha(manager)==prior['product_manifest']['native_sources']['native/host/host-manager.cpp']
baseline=out/'baseline';baseline.mkdir();host[host.index('-o')+1]=str(baseline/'saildroid-host');run(host,'native-v3-baseline-host');expected=prior['install_manifest']['files']['libexec/saildroid-host']['sha256'];assert sha(baseline/'saildroid-host')==old['binary_sha256']==expected
apiroot=Path('/var/tmp/saidroid-native-transition-20261031-r172/source/native/host');includes=['-I'+str(repo/'third_party/art-standalone/libnativehelper/include/nativehelper'),'-I'+str(repo/'third_party/art-standalone/libnativehelper/include'),'-I'+str(apiroot)];flags=shlex.split(subprocess.check_output(['pkg-config','--cflags','--libs','gio-2.0','libpulse'],text=True));api=['g++','-std=c++17','-O2','-Wall','-Wextra','-fPIC','-shared','-o',str(baseline/'libsdhostapi.so'),str(apiroot/'host-api.cpp'),str(apiroot/'host-audio.cpp'),str(apiroot/'host-network.cpp'),*includes,*flags,'-pthread']
for n in ['host-api.cpp','host-audio.cpp','host-network.cpp','host-common.hpp']:assert sha(apiroot/n)==prior['product_manifest']['native_sources']['native/host/'+n]
run(api,'native-v3-baseline-api');assert sha(baseline/'libsdhostapi.so')==prior['install_manifest']['files']['lib/libsdhostapi.so']['sha256']
candidate=out/'candidate';candidate.mkdir();cmd=list(host);cmd[cmd.index('-o')+1]=str(candidate/'saildroid-host');cmd[cmd.index(str(entry))]=str(b/'source/native/host/host-entry.cpp');cmd[cmd.index(str(manager))]=str(b/'source/native/host/host-manager.cpp');run(cmd,'native-v3-candidate-host')
cmd=list(api);cmd[cmd.index('-o')+1]=str(candidate/'libsdhostapi.so');cmd[cmd.index(str(apiroot/'host-api.cpp'))]=str(b/'source/native/host/host-api.cpp');run(cmd,'native-v3-candidate-api')
def symbols(p):
 values={}
 for line in subprocess.check_output(['readelf','--dyn-syms','--wide',str(p)],text=True).splitlines():
  v=line.split()
  if len(v)>=8 and v[0].rstrip(':').isdigit():values[v[7]]=(v[3],v[4],v[5],v[6]=='UND')
 return values
before=symbols(baseline/'libsdhostapi.so');after=symbols(candidate/'libsdhostapi.so');assert all(after.get(n)==v for n,v in before.items());added=sorted(set(after)-set(before));assert added==['Java_org_saildroid_host_HostApi_startReceiverProcess'],added
record=dict(passed=True,builder_sha256=sha(Path(__file__)),baseline_host_manifest_sha256=sha(b/'baseline-host-manifest.json'),baseline_native_binary_hashes={n:sha(baseline/n)for n in ['saildroid-host','libsdhostapi.so']},baseline_reproduced_byte_identical=True,binary_sha256={n:sha(candidate/n)for n in ['saildroid-host','libsdhostapi.so']},candidate=str(candidate),native_hostapi_added_symbols=added,existing_hostapi_dynamic_symbols_unchanged=True,bootstrap_unchanged=True,commands=commands)
(out/'manifest.json').write_text(json.dumps(record,indent=2)+'\n');(b/'native-build.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2),flush=True)
