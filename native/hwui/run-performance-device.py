"""One bounded, same-APK frame-throughput sample for software or HWUI."""
from pathlib import Path
import os,sys,json,subprocess,time,signal,pwd,re
label,release=sys.argv[1:3];assert label.replace('-','').isalnum()
pkg='org.example.saildroid.perfscroll';tool='/home/art/bin/sdtool.py';account=pwd.getpwnam('defaultuser')
root=Path('/home/art/api29-root');old=root.resolve();candidate=Path('/home/art/releases')/release;assert candidate.is_dir()
hardware=json.loads((candidate/'runtime.json').read_text())['renderer']=='hwui-gles-wayland'
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();lip=subprocess.check_output(['pidof','lipstick'],text=True).strip()
watch=subprocess.Popen(['/bin/sh','-c','sleep 35; mcetool --blank-screen'],start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
record=None
def replace_root(target):
 link=Path('/home/art/.hwui-perf-root');assert not link.exists();link.symlink_to(target);os.replace(link,root)
def stat(pid):
 raw=Path('/proc/'+str(pid)+'/stat').read_text();v=raw[raw.rfind(') ')+2:].split();return int(v[11])+int(v[12])
def compositor_health():
 env=dict(os.environ,XDG_RUNTIME_DIR='/run/user/100000',WAYLAND_DISPLAY='../../display/wayland-0')
 subprocess.run(['/home/art/test/hwui-tools/sd-wayland-health'],env=env,user=account.pw_uid,group=account.pw_gid,extra_groups=os.getgrouplist(account.pw_name,account.pw_gid),check=True,timeout=5)
try:
 compositor_health()
 replace_root(candidate)
 subprocess.run(['mcetool','--unblank-screen','--set-tklock-mode=unlocked'],check=True,timeout=4)
 command=['python3',tool,'--package',pkg,'launch','--env','SAILDROID_HWUI='+('1' if hardware else '0'),
  '--env','EGL_PLATFORM=wayland','--env','HYBRIS_EGLPLATFORM=wayland',
  '--env','PERFSCROLL_MODE=heavy','--env','PERFSCROLL_DRIVER=choreographer',
  '--env','SAILDROID_PERF=1','--env','WAYLAND_DEBUG=1','--wait','15']
 subprocess.run(command,check=True,timeout=22)
 record=json.loads(Path('/run/user/100000/saildroid/'+pkg+'.json').read_text());log=Path(record['log'])
 deadline=time.monotonic()+10
 while time.monotonic()<deadline:
  text=log.read_text(errors='replace')
  if 'PERFSCROLL=renderer|' in text:break
  if 'SDRUNTIME=failed' in text:raise AssertionError(text[-2000:])
  time.sleep(.1)
 assert 'PERFSCROLL=renderer|view_hardware='+str(hardware).lower() in text
 time.sleep(2)
 offset=log.stat().st_size;cpu0=stat(record['pid']);t0=time.monotonic()
 time.sleep(7)
 cpu1=stat(record['pid']);elapsed=time.monotonic()-t0;end=log.stat().st_size
 text=log.read_bytes()[offset:end].decode(errors='replace')
 # The actual queue commits, never invalidate()/driver tick counts.
 pattern=r'\[\s*([\d.]+)\].*-> wl_surface[#@](\d+)\.attach\(wl_buffer[#@]'
 commits=[float(m.group(1)) for m in re.finditer(pattern,text)]
 gaps=[b-a for a,b in zip(commits,commits[1:]) if b>=a]
 frames=[dict(re.findall(r'(\w+)=([^|\n]+)',line)) for line in text.splitlines() if line.startswith('PERFHWUI=frame|')]
 def percentile(v,p):
  v=sorted(v);return v[min(len(v)-1,int((len(v)-1)*p))] if v else None
 summary=dict(label=label,release=release,hardware=hardware,window_seconds=elapsed,queue_commits=len(commits),commits_per_second=len(commits)/elapsed,
  frame_gap_p50_ms=percentile(gaps,.5),frame_gap_p95_ms=percentile(gaps,.95),cpu_percent=(cpu1-cpu0)/os.sysconf('SC_CLK_TCK')/elapsed*100,
  hwui_frame_metrics=len(frames),hwui_total_p50_ms=percentile([int(x['total_ns'])/1e6 for x in frames],.5),hwui_total_p95_ms=percentile([int(x['total_ns'])/1e6 for x in frames],.95),
  app_progress=[line for line in text.splitlines() if 'PERFSCROLL=progress|' in line])
 assert len(commits)>20,summary
 assert 'SDRUNTIME=failed' not in text
 Path('/home/art/test/'+label+'.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))
finally:
 subprocess.run(['python3',tool,'--package',pkg,'close'],timeout=15)
 if record:
  final_log=Path(record['log']).read_bytes();Path('/home/art/test/'+label+'.log').write_bytes(final_log)
  cleanup_crash=b'Fatal signal' in final_log or b'SDRUNTIME=failed' in final_log
 if record:
  exit_deadline=time.monotonic()+6
  while time.monotonic()<exit_deadline:
   final=json.loads(Path('/run/user/100000/saildroid/'+pkg+'.json').read_text())
   if final.get('state')=='exited':break
   time.sleep(.1)
  Path('/home/art/test/'+label+'.log').write_bytes(Path(record['log']).read_bytes())
 subprocess.run(['mcetool','--blank-screen'],check=True,timeout=4)
 env=dict(os.environ,HOME=account.pw_dir,XDG_RUNTIME_DIR='/run/user/100000',DBUS_SESSION_BUS_ADDRESS='unix:path=/run/user/100000/dbus/user_bus_socket')
 subprocess.run(['/home/art/bin/saildroid-open','--broker','--close'],env=env,user=account.pw_uid,group=account.pw_gid,extra_groups=os.getgrouplist(account.pw_name,account.pw_gid),timeout=8)
 replace_root(old)
 deadline=time.monotonic()+4
 while time.monotonic()<deadline and Path('/sys/class/backlight/panel0-backlight/actual_brightness').read_text().strip()!='0':time.sleep(.1)
 try:os.killpg(watch.pid,signal.SIGTERM)
 except ProcessLookupError:pass
 brightness=Path('/sys/class/backlight/panel0-backlight/actual_brightness').read_text().strip();print('FINAL_BRIGHTNESS='+brightness);assert brightness=='0'
 assert boot==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 assert lip==subprocess.check_output(['pidof','lipstick'],text=True).strip()
 compositor_health()

 if record:assert not cleanup_crash, 'Crash during lifecycle cleanup'
