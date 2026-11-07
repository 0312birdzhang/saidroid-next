#!/usr/bin/env python3
"""Remove exited CTS-only leftovers and verify the unchanged daily environment.

Run in MeeGo Build after the serial dispatcher and retries have stopped.
No application without a CTS ownership record is removed.
"""
from pathlib import Path
import argparse, json, os, subprocess

p = argparse.ArgumentParser()
p.add_argument('evidence', type=Path)
p.add_argument('--expected-boot', required=True)
p.add_argument('--expected-lipstick', required=True)
p.add_argument('--candidate', default='r123-native-candidate')
a = p.parse_args()
repo = Path('/media/psf/Home/WorkSpace/saidroid-next')
os.environ['SSHPASS'] = os.environ['SSHPASS']
ssh = ['sshpass', '-e', 'ssh', '-o', 'ConnectTimeout=6', 'root@bonito']
lock = repo / 'scripts/devlock.sh'
import re
assert re.fullmatch(r'r[0-9]+-native-candidate',a.candidate)
config = dict(boot=a.expected_boot, lipstick=a.expected_lipstick,candidate=a.candidate,max_cts_version=int(a.candidate.split('-')[0][1:]))
body = 'CONFIG=' + repr(config) + '\n' + r'''
from pathlib import Path
import hashlib,json,os,pwd,re,shutil,stat,subprocess
assert Path('/home/art/test/.device-lock/owner').read_text().startswith('cts-finalize|')
assert 'ID=sailfishos' in Path('/etc/sailfish-release').read_text()
assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==CONFIG['boot']
assert subprocess.check_output(['pidof','lipstick'],text=True).strip()==CONFIG['lipstick']
daily=Path('/home/art/releases/api29-r112-native-candidate')
assert Path('/home/art/api29-root').resolve()==daily
assert Path('/home/art/bin/saildroid-open').resolve()==daily/'libexec/saildroid-app'
assert Path('/home/art/releases/api29-r98-native-gate').is_dir()
candidate=Path('/home/art/releases')/('api29-'+CONFIG['candidate'])
manifest=json.loads((candidate/'install-manifest.json').read_text())
for name,entry in manifest['files'].items():
 path=candidate/name
 assert path.is_file()and not path.is_symlink()
 assert hashlib.sha256(path.read_bytes()).hexdigest()==entry['sha256'],name
 assert stat.S_IMODE(path.stat().st_mode)==entry['mode'],name
for name,target in manifest['symlinks'].items():assert(candidate/name).is_symlink()and os.readlink(candidate/name)==target
for proc in Path('/proc').iterdir():
 if not proc.name.isdigit():continue
 try:exe=os.readlink(proc/'exe')
 except OSError:continue
 assert not(exe.startswith('/home/art/releases/')and exe.endswith('/libexec/saildroid-host')),'Owned host remains '+proc.name
 assert not(exe.startswith('/home/art/releases/')and '/rs/bin/'in exe),'Compiler tool process remains '+proc.name
 assert not exe.startswith('/home/art/test/cts'),'Native CTS process remains '+proc.name
desktop=Path('/home/defaultuser/.local/share/applications')
desktops=list(desktop.glob('*.desktop'))
removed=[]
def owned_cts_name(name):
 match=re.fullmatch(r'cts([0-9]+)-[A-Za-z0-9-]+',name)
 return match is not None and 116<=int(match.group(1))<=CONFIG['max_cts_version']
for app in Path('/home/art/apps').iterdir():
 record=app/'record.json'
 if app.is_symlink()or not record.is_file():continue
 value=json.loads(record.read_text());run=value.get('cts_run','')
 if not owned_cts_name(run):continue
 assert value['package']==app.name and value['data']==str(app/'data')
 assert value['apk']==str(app/'app.apk')
 assert hashlib.sha256((app/'app.apk').read_bytes()).hexdigest()==value['apkSha256']
 assert not any(app.name in d.read_text()or str(app)in d.read_text()for d in desktops)
 for state in Path('/run/user/100000/saildroid').glob(app.name+'*.json'):
  identity=json.loads(state.read_text())
  if identity.get('boot')!=CONFIG['boot']:continue
  proc=Path('/proc')/str(identity.get('pid',0))
  if proc.exists():
   fields=(proc/'stat').read_text().rsplit(') ',1)[1].split()
   assert fields[0]in['Z','X']or int(fields[19])!=identity.get('start_ticks'),'CTS process remains'
 shutil.rmtree(app);removed.append(dict(package=app.name,run=run,sha256=value['apkSha256']))
removed_runs=[]
for folder in Path('/home/art/test').iterdir():
 if not owned_cts_name(folder.name):continue
 assert folder.is_dir()and not folder.is_symlink()
 shutil.rmtree(folder);removed_runs.append(folder.name)
count=0
for file in desktop.glob('org.saildroid.app.p*.desktop'):
 lines=[x for x in file.read_text().splitlines()if x.startswith('Exec=')]
 assert len(lines)==1 and lines[0].startswith('Exec='+str(daily/'libexec/saildroid-app')+' ')
 count+=1
assert count==5,count
for fixture in ['org.example.saildroid.remoteactivity','org.example.saildroid.instrumenttarget','org.example.saildroid.instrumentrunner','org.example.saildroid.ctsharness','com.android.cts.verifier']:
 assert not(Path('/home/art/apps')/fixture).exists(),fixture
for app in Path('/home/art/apps').iterdir():
 record=app/'record.json'
 if record.is_file():assert not json.loads(record.read_text()).get('cts_run'),app.name
services={}
for name in ['sshd.socket','connman.service']:
 state=subprocess.check_output(['systemctl','is-active',name],text=True,timeout=5).strip()
 assert state=='active';services[name]=state
subprocess.run(['mcetool','--set-never-blank=disabled','--blank-screen'],check=True,timeout=5)
assert Path('/sys/class/backlight/panel0-backlight/actual_brightness').read_text().strip()=='0'
display=subprocess.check_output(['gdbus','call','--system','--dest','com.nokia.mce','--object-path','/com/nokia/mce/request','--method','com.nokia.mce.request.get_display_status'],text=True,timeout=5)
assert "'off'"in display
u=pwd.getpwnam('defaultuser')
env=dict(os.environ,HOME=u.pw_dir,XDG_RUNTIME_DIR='/run/user/100000',WAYLAND_DISPLAY='../../display/wayland-0',DBUS_SESSION_BUS_ADDRESS='unix:path=/run/user/100000/dbus/user_bus_socket')
health=subprocess.run(['/home/art/test/hwui-tools/sd-wayland-health'],env=env,user=u.pw_uid,group=u.pw_gid,extra_groups=os.getgrouplist(u.pw_name,u.pw_gid),capture_output=True,text=True,timeout=5)
assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==CONFIG['boot']
assert subprocess.check_output(['pidof','lipstick'],text=True).strip()==CONFIG['lipstick']
assert not Path('/data/local/tmp/signature-test').exists(),'Signature preparation leftovers remain'
print(json.dumps(dict(status='PASS'if health.returncode==0 else'DEGRADED',boot=CONFIG['boot'],lipstick=CONFIG['lipstick'],daily='r112',previous='r98',candidate=CONFIG['candidate'],candidate_files_verified=len(manifest['files']),desktop_entries=count,removed_apps=removed,removed_run_directories=removed_runs,services=services,owned_hosts=0,cts_apps_remaining=0,signature_preparation_remaining=0,brightness=0,display='off',wayland_sync=health.stdout.strip(),wayland_exit=health.returncode,wayland_stderr=health.stderr)))
'''
subprocess.run(['bash', str(lock), 'acquire', '0', 'cts-finalize'], check=True, timeout=15)
try:
    # Identity validation precedes any process closure or removal.
    preflight = 'from pathlib import Path;import subprocess;assert Path("/proc/sys/kernel/random/boot_id").read_text().strip()==' + repr(a.expected_boot) + ';assert subprocess.check_output(["pidof","lipstick"],text=True).strip()==' + repr(a.expected_lipstick)
    subprocess.run(ssh + ['python3', '-'], input=preflight.encode(), check=True, timeout=12)
    subprocess.run(['python3', str(repo/'scripts/perf/close-owned-vm.py')], check=True, timeout=80)
    run = subprocess.run(ssh + ['python3', '-'], input=body.encode(), capture_output=True, timeout=60)
    if run.returncode:
        (a.evidence/'final-health-error.log').write_bytes(run.stderr)
        raise RuntimeError('Final health transaction failed: '+run.stderr.decode(errors='replace'))
    result = json.loads(run.stdout)
    a.evidence.mkdir(parents=True, exist_ok=True)
    (a.evidence/'final-health.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
    if result['status']!='PASS':raise RuntimeError('Device cleanup complete but compositor sync failed; final-health.json records DEGRADED')
finally:
    subprocess.run(ssh + ['mcetool', '--set-never-blank=disabled', '--blank-screen'], timeout=6)
    subprocess.run(['bash', str(lock), 'release', 'cts-finalize'], check=True, timeout=15)
