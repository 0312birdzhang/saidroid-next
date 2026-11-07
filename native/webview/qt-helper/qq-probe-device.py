import subprocess,sys,os,time,json,signal
from pathlib import Path
label=sys.argv[1];pkg='com.tencent.mobileqq';tool='/home/art/bin/sdtool.py'
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
lip=subprocess.check_output(['pidof','lipstick']).decode().strip()
subprocess.run(['mcetool','--blank-screen'],check=True)
watch=subprocess.Popen(['/bin/sh','-c','sleep 90; mcetool --blank-screen'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
try:
    subprocess.run(['python3',tool,'--package',pkg,'launch','--env','SAILDROID_DIAG_INPUT=1','--env','SAILDROID_WEBVIEW_DIAGNOSTICS=1','--wait','20'],check=True,timeout=25)
    record=json.loads(Path('/run/user/100000/saildroid/'+pkg+'.json').read_text())
    deadline=time.monotonic()+45
    while time.monotonic()<deadline:
        text=Path(record['log']).read_text(errors='replace')
        if 'SDRUNTIME=activity_queued' in text or 'SDRUNTIME=failed' in text:break
        time.sleep(.25)
    if 'SDRUNTIME=activity_queued' not in text:
        import pwd
        u=pwd.getpwnam('defaultuser');env=dict(os.environ,HOME=u.pw_dir,XDG_RUNTIME_DIR='/run/user/100000',DBUS_SESSION_BUS_ADDRESS='unix:path=/run/user/100000/dbus/user_bus_socket')
        subprocess.run(['/home/art/bin/saildroid-open','--package',pkg,'--dump-threads'],env=env,user=u.pw_uid,group=u.pw_gid,extra_groups=os.getgrouplist(u.pw_name,u.pw_gid),timeout=8)
        time.sleep(1)
        raise AssertionError('QQ initialization stalled before activity launch')
    subprocess.run(['mcetool','--unblank-screen','--set-tklock-mode=unlocked'],check=True)
    time.sleep(2)
    # Historical path: QQ login -> Help -> QQ Safety Center. No credentials,
    # account changes, or login submission are performed by this probe.
    steps='tap 791 1900 60\nsleep 1300\ntap 1005 152 60\nsleep 1300\ntap 400 1803 60\n'
    subprocess.run(['/home/art/bin/sdinput','serve'],input=steps,text=True,check=True,timeout=15)
    record=json.loads(Path('/run/user/100000/saildroid/'+pkg+'.json').read_text())
    deadline=time.monotonic()+22
    while time.monotonic()<deadline:
        text=Path(record['log']).read_text(errors='replace')
        if '"event":"load","status":2' in text or 'SDRUNTIME=failed' in text or 'SDWEBVIEW=engine_failed' in text:break
        time.sleep(.25)
    time.sleep(3)
    subprocess.run(['python3',tool,'--package',pkg,'shot',label+'-h5'],check=True,timeout=12)
    text=Path(record['log']).read_text(errors='replace')
    Path('/home/art/test/'+label+'-app.log').write_bytes(Path(record['log']).read_bytes())
    print('QQ_WEBVIEW|browser_activity='+str('QQBrowserActivity' in text)+'|frames='+str(text.count('SDWEBVIEW=frame|'))+'|runtime_failed='+str('SDRUNTIME=failed' in text),flush=True)
    assert 'QQBrowserActivity' in text,'QQ H5 precondition not reached'
    assert 'SDWEBVIEW=draw|renderer=qt-wpe' in text,'webview pixels not drawn'
    assert '"event":"load","status":2' in text,'real page did not finish loading'
    assert 'SDRUNTIME=failed' not in text
    assert lip==subprocess.check_output(['pidof','lipstick']).decode().strip()
    assert boot==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    print('QQ_WEBVIEW_ENGINE=ready|mode=load-finished-pixel-verdict-pending|lipstick='+lip,flush=True)
finally:
    r=Path('/run/user/100000/saildroid/'+pkg+'.json')
    if r.exists():
        record=json.loads(r.read_text());Path('/home/art/test/'+label+'-app.log').write_bytes(Path(record['log']).read_bytes())
    subprocess.run(['python3',tool,'--package',pkg,'close'],timeout=20)
    subprocess.run(['mcetool','--blank-screen'],check=True)
    try:os.killpg(watch.pid,signal.SIGTERM)
    except ProcessLookupError:pass
