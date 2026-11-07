import subprocess,os
E=dict(os.environ,SSHPASS=os.environ['SSHPASS'])
SSH=['sshpass','-e','ssh','-o','StrictHostKeyChecking=no','root@bonito']
c=r'''ls -t /home/defaultuser/.cache/lipstick/*.log 2>/dev/null | head -3; echo ---; grep -iE "close|kill|p1d47ed0aadf712ce2c80|no_response|not responding" $(ls -t /home/defaultuser/.cache/lipstick/*.log 2>/dev/null | head -1) | tail -25'''
r=subprocess.run(SSH+[c],capture_output=True,text=True,env=E,timeout=40)
print(r.stdout[-3000:]);print(r.stderr[-300:])
c2=r'''grep -n "close_requested" /media/psf/Home/WorkSpace/saidroid-next/native/window/sdwindow.c | head'''
r2=subprocess.run(SSH+[c2],capture_output=True,text=True,env=E,timeout=20);print(r2.stdout)
