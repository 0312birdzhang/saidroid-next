from pathlib import Path
import subprocess,json,hashlib,zipfile
r=Path('/media/psf/Home/WorkSpace/saidroid-next');b=Path(__file__).parent;out=b/'manager-build-v1';recipe=['python3',str(r/'scripts/api29/build-manager.py'),str(r/'build/codex-api29/inputs'),str(b/'runtime-build-v1'),'/var/tmp/saidroid-icmp-cleanup286-v1-formal-vm-component/root/system/framework/framework-res.apk',str(out)]
with(b/'manager-build.log').open('ab',buffering=0)as f:subprocess.run(recipe,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=90)
print('MANAGER_BUILD=passed|sha256='+hashlib.sha256((out/'manager.apk').read_bytes()).hexdigest())
