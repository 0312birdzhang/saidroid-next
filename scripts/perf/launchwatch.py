import subprocess,os,sys
E=dict(os.environ,SSHPASS=os.environ['SSHPASS'])
SSH=['sshpass','-e','ssh','-o','StrictHostKeyChecking=no','root@bonito']
body=r'''
import json,os,pwd,subprocess,time
from pathlib import Path
PKG='com.tencent.mobileqq'
state=Path('/run/user/100000/saildroid/'+PKG+'.json')
def read():
    try:return json.loads(state.read_text())
    except Exception:return None
u=pwd.getpwnam('defaultuser')
env=dict(os.environ,HOME=u.pw_dir,USER=u.pw_name,LOGNAME=u.pw_name,XDG_RUNTIME_DIR='/run/user/100000',DBUS_SESSION_BUS_ADDRESS='unix:path=/run/user/100000/dbus/user_bus_socket')
perf='/home/art/data/logs/%s/perf-dbg.bin'%PKG
env.update(SAILDROID_PERF='1',SAILDROID_PERF_FILE=perf)
subprocess.run(['rm','-f',perf])
log='/home/art/test/perf-launch-dbg.log'
with open(log,'ab') as stream:
    subprocess.Popen(['/home/art/bin/saildroid-open','--package',PKG],stdout=stream,stderr=subprocess.STDOUT,start_new_session=True,env=env,user=u.pw_uid,group=u.pw_gid,extra_groups=os.getgrouplist(u.pw_name,u.pw_gid))
print('LAUNCHED',log)
last=None
for i in range(120):
    st=read()
    key=(st or {}).get('state'),(st or {}).get('pid'),(st or {}).get('exit_reason')
    if key!=last:print('T=%.1f'%(i*0.5),key,'launch=',(st or {}).get('launch_id'));last=key
    if st and st.get('state')=='exited':break
    time.sleep(0.5)
st=read() or {}
applog=st.get('log') or ''
print('APP_LOG',applog)
if applog and Path(applog).exists():
    lines=Path(applog).read_text(errors='replace').splitlines()
    print('LOG_LINES',len(lines))
    print('\n'.join(lines[-30:]))
print('PERF_FILE',perf,Path(perf).stat().st_size if Path(perf).exists() else 'MISSING')
if Path(perf).exists():
    txt=Path(perf).read_text(errors='replace').splitlines()
    print('PERF_LINES',len(txt));print(txt[0] if txt else '')
'''
r=subprocess.run(SSH+['python3 -'],input=body.encode(),capture_output=True,env=E,timeout=180)
print(r.stdout.decode()[-6000:]);print('ERR',r.stderr.decode()[-1500:])
