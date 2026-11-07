#!/usr/bin/env python3
"""Bounded device execution of selected unmodified official utility classes.
Runs as the ordinary user, OLED off, private harness only; no daily-root change.
"""
from pathlib import Path
import subprocess,os,json,hashlib,sys
REPO=Path('/media/psf/Home/WorkSpace/saidroid-next');EV=REPO/'build/evidence/cts-api29-20261030';os.environ['SSHPASS']=os.environ['SSHPASS']
SSH=['sshpass','-e','ssh','-o','ConnectTimeout=6','root@bonito'];SCP=['sshpass','-e','scp','-O'];lock=REPO/'scripts/devlock.sh'
label=sys.argv[1];assert label.replace('-','').isalnum()
subprocess.run(['bash',str(lock),'acquire','0','official-cts-diagnostic'],check=True,timeout=15)
try:
 subprocess.run(['python3',str(REPO/'scripts/perf/close-owned-vm.py')],check=True,timeout=50)
 subprocess.run(['python3',str(REPO/'scripts/cts/install-harness-vm.py'),'cts4'],check=True,timeout=45)
 apk=EV/'cts/CtsUtilTestCases.apk';sha=hashlib.sha256(apk.read_bytes()).hexdigest()
 subprocess.run(SSH+['mkdir','-p','/home/art/test/'+label],check=True,timeout=10)
 subprocess.run(SCP+[str(apk),'root@bonito:/home/art/test/'+label+'/official.apk'],check=True,timeout=20)
 body='LABEL='+repr(label)+'\nSHA='+repr(sha)+'\n'+(REPO/'scripts/cts/run-util-phone.py').read_text()
 r=subprocess.run(SSH+['python3','-'],input=body.encode(),timeout=160)
 subprocess.run(SCP+['-r','root@bonito:/home/art/test/'+label,str(EV)],check=True,timeout=20)
 r.check_returncode()
finally:
 subprocess.run(['python3',str(REPO/'scripts/perf/close-owned-vm.py')],timeout=50)
 subprocess.run(SSH+['mcetool','--set-never-blank=disabled','--blank-screen'],timeout=6)
 subprocess.run(['bash',str(lock),'release','official-cts-diagnostic'],check=True,timeout=15)
