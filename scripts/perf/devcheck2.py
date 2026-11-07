import subprocess
body=r'''
import subprocess
def sh(c):
    try:return subprocess.run(c,shell=True,capture_output=True,text=True,timeout=15).stdout.strip()
    except Exception as e:return 'ERR '+str(e)
for k,c in [('boot','cat /proc/sys/kernel/random/boot_id'),('lip','ps -o pid,lstart,comm -p $(pidof lipstick)'),('root','readlink -f /home/art/api29-root'),('ver','cat /home/art/api29-root/version 2>/dev/null; cat /home/art/api29-root/build.prop 2>/dev/null | head -3'),('nproc','getconf _NPROCESSORS_ONLN'),('python','python3 -V'),('weston','which weston; which gdbus; which perf; which strace; which sshpass')]:
    print(k,'=',sh(c))
'''
r=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=6','root@bonito','python3 -'],input=body.encode(),capture_output=True,timeout=40)
print(r.stdout.decode());print('ERR',r.stderr.decode()[-500:])
