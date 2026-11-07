import subprocess,os
body=r'''
import subprocess
print(subprocess.run("ps -eo pid,user,etimes,cmd | grep -E 'dalvikvm|saildroid|org.saildroid.manager|com.tencent' | grep -v grep",shell=True,capture_output=True,text=True).stdout)
print(subprocess.run("ls -la /run/user/100000/saildroid/ 2>/dev/null",shell=True,capture_output=True,text=True).stdout)
'''
r=subprocess.run(['sshpass','-e','ssh','-o','StrictHostKeyChecking=no','root@bonito','python3','-'],input=body.encode(),capture_output=True,env=dict(os.environ,SSHPASS=os.environ['SSHPASS']),timeout=30)
print(r.stdout.decode());print(r.stderr.decode()[-300:])
