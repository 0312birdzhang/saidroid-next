from pathlib import Path
import subprocess,json,os,hashlib
b=Path(__file__).parent;out=b/'error-fixture';subprocess.run(['gcc','-O2','-Wall','-Wextra','-Werror','-pthread','-o',str(out),str(b/'error-fixture.c'),'-ldl'],check=True)
meta=json.loads((b/'native-build-v3.json').read_text());env=dict(os.environ,LD_LIBRARY_PATH='/var/tmp/saidroid-native-service-lifecycle305-v1/payload/lib:/home/art/lib');results=[]
for name,path,code in [('baseline',Path('/var/tmp/saidroid-linker-cfi-owner-20261031/libdl_bio.so.0'),1),('fixed',Path(meta['path']),0)]:
 p=subprocess.run([str(out),str(path)],capture_output=True,text=True,timeout=30,env=env);(b/(name+'-fixture.stdout')).write_text(p.stdout);(b/(name+'-fixture.stderr')).write_text(p.stderr);print(name,p.stdout,p.stderr,flush=True);assert p.returncode==code,p.stderr;results.append(dict(name=name,returncode=p.returncode,output=p.stdout,library_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
(b/'error-fixture-results.json').write_text(json.dumps(dict(passed=True,results=results),indent=2)+'\n')
