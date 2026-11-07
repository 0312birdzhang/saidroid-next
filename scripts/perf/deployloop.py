import subprocess
R='/media/psf/Home/WorkSpace/saidroid-next'
for attempt in range(3):
    print('=== attempt',attempt,flush=True)
    subprocess.run(['/usr/bin/python3',R+'/scripts/perf/close-owned-vm.py'],check=True)
    r=subprocess.run(['/usr/bin/python3',R+'/scripts/perf/deploy-perf-release-vm.py','perf1'],capture_output=True,text=True)
    print(r.stdout[-2000:]);print(r.stderr[-1500:])
    if r.returncode==0:
        print('DEPLOY_OK');break
    try:
        print(open('/var/tmp/saidroid-next-api29-component-perf-perf1/deploy-20261026-perf1.stderr').read()[-500:])
    except Exception as e: print(e)
