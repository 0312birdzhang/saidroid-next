import subprocess,sys,os,time,json,signal
from pathlib import Path
label=sys.argv[1];pkg='org.example.saildroid.webviewprobe';tool='/home/art/bin/sdtool.py'
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
lip=subprocess.check_output(['pidof','lipstick']).decode().strip()
subprocess.run(['mcetool','--unblank-screen','--set-tklock-mode=unlocked'],check=True)
watch=subprocess.Popen(['/bin/sh','-c','sleep 45; mcetool --blank-screen'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
try:
    subprocess.run(['python3',tool,'--package',pkg,'launch','--wait','20'],check=True,timeout=25)
    subprocess.run(['python3',tool,'--package',pkg,'wait','--marker','SDWEBPROBE=js|','--wait','20'],check=True,timeout=25)
    record=json.loads(Path('/run/user/100000/saildroid/'+pkg+'.json').read_text());pid=record['pid']
    start=Path('/proc/%d/stat'%pid).read_text().split(') ',1)[1].split()[19]
    group=os.getpgid(pid);victims=[]
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit():continue
        try:
            candidate=int(proc.name);exe=os.readlink(proc/'exe')
            if exe.endswith('/WPEWebProcess') and os.getpgid(candidate)==group:victims.append(candidate)
        except OSError:pass
    assert len(victims)==1,victims
    os.kill(victims[0],signal.SIGKILL)
    print('WEBVIEW_CRASH=injected|renderer_pid='+str(victims[0]),flush=True)
    deadline=time.monotonic()+15
    while time.monotonic()<deadline:
        text=Path(record['log']).read_text(errors='replace')
        if 'SDWEBPROBE=finished|count=2' in text:break
        time.sleep(.25)
    assert 'SDWEBPROBE=finished|count=2' in text,'reload after renderer crash failed'
    assert Path('/proc/%d/stat'%pid).read_text().split(') ',1)[1].split()[19]==start
    text=Path(record['log']).read_text(errors='replace')
    assert 'SDWEBVIEW=engine_failed|' in text,text[-2500:]
    assert 'SDWEBPROBE=error|' in text
    assert lip==subprocess.check_output(['pidof','lipstick']).decode().strip()
    assert boot==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    print('WEBVIEW_CRASH=ready|art_pid='+str(pid)+'|start_ticks='+start+'|lipstick='+lip,flush=True)
finally:
    r=Path('/run/user/100000/saildroid/'+pkg+'.json')
    if r.exists():
        record=json.loads(r.read_text());Path('/home/art/test/'+label+'-app.log').write_bytes(Path(record['log']).read_bytes())
    subprocess.run(['python3',tool,'--package',pkg,'close'],timeout=20)
    subprocess.run(['mcetool','--blank-screen'],check=True)
    try:os.killpg(watch.pid,signal.SIGTERM)
    except ProcessLookupError:pass
