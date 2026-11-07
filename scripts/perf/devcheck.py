import subprocess
body=r'''
import subprocess,os,json
def sh(c):
    try:return subprocess.run(c,shell=True,capture_output=True,text=True,timeout=15).stdout.strip()
    except Exception as e:return 'ERR '+str(e)
print('uname',sh('uname -a'))
print('boot_id',sh('cat /proc/sys/kernel/random/boot_id'))
print('lipstick',sh("ps -o pid,lstart,cmd -p $(pidof lipstick) 2>/dev/null"))
print('api29-root',sh('readlink -f /home/art/api29-root'))
print('releases',sh('ls -1 /home/art/releases'))
print('lockdir',sh('ls -ld /home/art/test/.device-lock 2>&1'))
print('art_procs',sh("ps -eo pid,user,cmd | grep -c '[S]dRuntime'"))
print('cpu',sh('nproc; cat /proc/cpuinfo | grep -m1 "model name"'))
print('gpu',sh('cat /sys/class/kgsl/kgsl-3d0/gpuclk 2>/dev/null; cat /sys/class/kgsl/kgsl-3d0/devfreq/cur_freq 2>/dev/null'))
print('governor',sh('cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null'))
print('mem',sh('free -m'))
print('df',sh('df -h /home/art | tail -1'))
'''
r=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=6','root@bonito','python3 -'],input=body.encode(),capture_output=True,timeout=40)
print(r.stdout.decode());print('STDERR',r.stderr.decode());print('RC',r.returncode)
