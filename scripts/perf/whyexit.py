import subprocess,os
E=dict(os.environ,SSHPASS=os.environ['SSHPASS'])
SSH=['sshpass','-e','ssh','-o','StrictHostKeyChecking=no','root@bonito']
cmds=['ls -la /home/art/data/logs/com.tencent.mobileqq/ | tail -5',
      'ls -la /home/art/data/logs/com.tencent.mobileqq/perf-*.bin 2>/dev/null | tail -3',
      'tail -25 /home/art/test/sdtool-com.tencent.mobileqq-1793048079.log',
      'log=$(ls -t /home/art/data/logs/com.tencent.mobileqq/*.log | head -1); wc -l $log; tail -40 $log']
for c in cmds:
    r=subprocess.run(SSH+[c],capture_output=True,text=True,env=E,timeout=40)
    print('$',c);print(r.stdout[-2500:]);print(r.stderr[-300:])
