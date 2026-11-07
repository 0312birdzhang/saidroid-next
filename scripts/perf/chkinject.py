import subprocess,os
body=r'''
from pathlib import Path
import os,glob
for p in ['/home/art/test/delivery-touch-tool-r3/inject-touch','/home/art/test/delivery-touch-tool-r2/inject-touch','/home/art/bin/sdtool.py']:
    q=Path(p);print(('OK  ' if q.exists() else 'MISS'),p, oct(q.stat().st_mode) if q.exists() else '')
print('apps', sorted(x.name for x in Path('/home/art/apps').iterdir()))
print('logs', sorted(x.name for x in Path('/home/art/data/logs').iterdir()) if Path('/home/art/data/logs').exists() else 'none')
'''
r=subprocess.run(['sshpass','-e','ssh','-o','StrictHostKeyChecking=no','-o','ConnectTimeout=8','root@bonito','python3','-'],input=body.encode(),capture_output=True,env=dict(os.environ,SSHPASS=os.environ['SSHPASS']),timeout=30)
print(r.stdout.decode());print(r.stderr.decode()[-300:])
