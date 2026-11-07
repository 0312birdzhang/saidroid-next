import subprocess,os
body=r'''
import subprocess
r=subprocess.run(['ps','-eo','pid,user,etimes,args'],capture_output=True,text=True)
for line in r.stdout.splitlines():
    if any(k in line for k in ('dalvikvm','saildroid','runtime.jar','com.tencent')):
        print(line[:220])
'''
r=subprocess.run(['sshpass','-e','ssh','-o','StrictHostKeyChecking=no','root@bonito','python3','-'],input=body.encode(),capture_output=True,env=dict(os.environ,SSHPASS=os.environ['SSHPASS']),timeout=30)
print(r.stdout.decode());print('ERR',r.stderr.decode()[-200:])
