import subprocess,os,time
R='/media/psf/Home/WorkSpace/saidroid-next'
E=dict(os.environ,SSHPASS=os.environ['SSHPASS'])
SSH=['sshpass','-e','ssh','-o','StrictHostKeyChecking=no','root@bonito']
subprocess.run(['/usr/bin/python3',R+'/scripts/perf/close-owned-vm.py'],check=True)
subprocess.run(SSH+['rm -rf /home/art/test/api29-deploy-20261026-perf1 /home/art/releases/api29-20261026-perf1'],env=E,timeout=20)
print(subprocess.run(SSH+['rm -f /tmp/owned-watch.log; nohup /bin/sh /home/art/test/watcher.sh >/dev/null 2>&1 & echo started'],capture_output=True,text=True,env=E,timeout=20).stdout)
r=subprocess.run(['/usr/bin/python3',R+'/scripts/perf/deploy-perf-release-vm.py','perf1'],capture_output=True,text=True)
print('DEPLOY_RC',r.returncode);print(r.stdout[-800:]);print(r.stderr[-600:])
time.sleep(2)
print(subprocess.run(SSH+['head -30 /tmp/owned-watch.log; echo ---; wc -l /tmp/owned-watch.log'],capture_output=True,text=True,env=E,timeout=20).stdout)
print(subprocess.run(SSH+['pkill -f watcher.sh'],capture_output=True,text=True,env=E,timeout=20).stdout)
