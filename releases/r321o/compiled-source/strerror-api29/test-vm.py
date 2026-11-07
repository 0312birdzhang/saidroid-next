from pathlib import Path
import os,subprocess,json
b=Path(__file__).parent;r=b.parents[2];source=r/'native/compat/strerror-api29';out=Path('/var/tmp/saidroid-strerror302-native-v1')
subprocess.run(['gcc','-shared','-fPIC','-nostdlib','-fno-stack-protector','-Wl,--hash-style=both','-o',str(out/'fixture.so'),str(source/'relocation-fixture.c')],check=True)
linker='/var/tmp/saidroid-icmp-cleanup286-v1-formal-vm-component/root/lib/libdl_bio.so.0'
results=[]
for name,mode in [('baseline.so','negative'),('libsdhost29.so','positive')]:
 p=subprocess.run(['python3',str(source/'probe.py'),str(out/name),linker,str(out/'fixture.so'),mode],capture_output=True,text=True,timeout=20);print(p.stdout,p.stderr);assert p.returncode==0;results.append(json.loads(p.stdout))
(b/'vm-fixture-results.json').write_text(json.dumps(results,indent=2)+'\n')
