import subprocess,os
body=r'''
from pathlib import Path
import os
hits=[]
for process in Path('/proc').iterdir():
    if not process.name.isdigit():continue
    try:
        command=(process/'cmdline').read_bytes()
        executable=os.readlink(process/'exe')
        bad=(executable=='/home/art/bin/dalvikvm'
             or(executable.startswith('/home/art/apps/')and executable.endswith('/dalvikvm'))
             or b'api29-root/lib/runtime.jar' in command
             or b'api29-root/libexec/saildroid-open' in command
             or command.startswith((b'org.saildroid.manager\0',b'saildroid-supervisor:')))
        if bad:hits.append((process.name,executable,command[:120]))
    except (OSError,PermissionError):pass
print('HITS',hits)
'''
r=subprocess.run(['sshpass','-e','ssh','-o','StrictHostKeyChecking=no','root@bonito','python3','-'],input=body.encode(),capture_output=True,env=dict(os.environ,SSHPASS=os.environ['SSHPASS']),timeout=30)
print(r.stdout.decode());print('ERR',r.stderr.decode()[-300:])
