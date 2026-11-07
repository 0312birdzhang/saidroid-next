import subprocess,os
R='/media/psf/Home/WorkSpace/saidroid-next'
subprocess.run(['/usr/bin/python3',R+'/scripts/perf/close-owned-vm.py'],check=True)
body=r'''
from pathlib import Path
import os,time
def scan():
    hits=[]
    for p in Path('/proc').iterdir():
        if not p.name.isdigit():continue
        try:
            cmd=(p/'cmdline').read_bytes();exe=os.readlink(p/'exe')
            if exe=='/home/art/bin/dalvikvm' or b'api29-root/lib/runtime.jar' in cmd or b'api29-root/libexec/saildroid-open' in cmd or cmd.startswith((b'org.saildroid.manager\0',b'saildroid-supervisor:')) or (exe.startswith('/home/art/apps/') and exe.endswith('/dalvikvm')):
                hits.append((p.name,exe,cmd[:80]))
        except (OSError,PermissionError):pass
    return hits
for i in range(30):
    h=scan()
    if h:print('T',i,h)
    time.sleep(1)
print('WATCH_DONE')
'''
r=subprocess.run(['sshpass','-e','ssh','-o','StrictHostKeyChecking=no','root@bonito','python3','-'],input=body.encode(),capture_output=True,env=dict(os.environ,SSHPASS=os.environ['SSHPASS']),timeout=60)
print(r.stdout.decode());print(r.stderr.decode()[-300:])
