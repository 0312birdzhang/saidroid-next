#!/usr/bin/env python3
"""Verify and retire old test candidates; preserve daily/rollback/final roots.

Requires the compact build snapshots produced for this investigation. Defaults
to a read-only plan. Run only after the dispatcher and retries have stopped.
"""
from pathlib import Path
import argparse,hashlib,json,os,subprocess
p=argparse.ArgumentParser();p.add_argument('evidence',type=Path);p.add_argument('--apply',action='store_true');a=p.parse_args()
repo=Path('/media/psf/Home/WorkSpace/saidroid-next');os.environ['SSHPASS']=os.environ['SSHPASS'];lock=repo/'scripts/devlock.sh'
expected={};stages={}
for version in range(114,123):
 path=a.evidence/'runtime-history'/('r'+str(version))/'bundle/overlay.json'
 if path.exists():expected['api29-r'+str(version)+'-native-candidate']=json.loads(path.read_text())['install_manifest']
assert expected
for version in range(114,124):
 bundle=Path('/var/tmp')/('saidroid-native-transition-20261030-r'+str(version))/'bundle'
 if(bundle/'overlay.json').exists():stages['r'+str(version)+'-native-candidate']=dict(sha256=hashlib.sha256((bundle/'native-overlay.tar.gz').read_bytes()).hexdigest(),manifest=json.loads((bundle/'overlay.json').read_text())['install_manifest'])
config=dict(apply=a.apply,expected=expected,stages=stages,boot='0d92d007-eb74-48c0-b801-9c96dbc42708',lipstick='9587')
body='CONFIG='+repr(config)+'\n'+r'''
from pathlib import Path
import hashlib,json,os,shutil,stat,subprocess
assert Path('/home/art/test/.device-lock/owner').read_text().startswith('cts-prune-candidates|')
assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==CONFIG['boot']
assert subprocess.check_output(['pidof','lipstick'],text=True).strip()==CONFIG['lipstick']
assert Path('/home/art/api29-root').resolve()==Path('/home/art/releases/api29-r112-native-candidate')
assert Path('/home/art/releases/api29-r98-native-gate').is_dir()
assert Path('/home/art/releases/api29-r86-compat').is_dir()
assert Path('/home/art/releases/api29-r123-native-candidate').is_dir()
desktop=[p.read_text()for p in Path('/home/defaultuser/.local/share/applications').glob('*.desktop')]
rows=[];stage_rows=[]
for name,manifest in CONFIG['expected'].items():
 root=Path('/home/art/releases')/name
 if not root.exists():continue
 assert root.is_dir()and not root.is_symlink()and root.stat().st_uid==0
 assert json.loads((root/'install-manifest.json').read_text())==manifest,name
 assert not any(str(root)in text for text in desktop),name
 for proc in Path('/proc').iterdir():
  if not proc.name.isdigit():continue
  try:exe=os.readlink(proc/'exe');cmd=(proc/'cmdline').read_bytes()
  except OSError:continue
  assert not exe.startswith(str(root)+'/')and str(root).encode()not in cmd,'Candidate still referenced '+proc.name
 for relative,entry in manifest['files'].items():
  path=root/relative
  assert path.is_file()and not path.is_symlink(),relative
  assert hashlib.sha256(path.read_bytes()).hexdigest()==entry['sha256'],relative
  assert stat.S_IMODE(path.stat().st_mode)==entry['mode'],relative
 for relative,target in manifest['symlinks'].items():assert(root/relative).is_symlink()and os.readlink(root/relative)==target
 size=int(subprocess.check_output(['du','-sk',str(root)],text=True).split()[0])
 rows.append(dict(root=str(root),kib=size,files=len(manifest['files']),removed=CONFIG['apply']))
 # Every candidate is independently verified before removing that exact root.
 if CONFIG['apply']:shutil.rmtree(root)
for name,info in CONFIG['stages'].items():
 stage=Path('/home/art/test')/('native-overlay-'+name)
 if not stage.exists():continue
 assert stage.is_dir()and not stage.is_symlink()and stage.stat().st_uid==0
 assert hashlib.sha256((stage/'native-overlay.tar.gz').read_bytes()).hexdigest()==info['sha256']
 assert json.loads((stage/'unpacked/overlay.json').read_text())['install_manifest']==info['manifest']
 size=int(subprocess.check_output(['du','-sk',str(stage)],text=True).split()[0])
 stage_rows.append(dict(stage=str(stage),kib=size,removed=CONFIG['apply']))
 if CONFIG['apply']:shutil.rmtree(stage)
subprocess.run(['mcetool','--set-never-blank=disabled','--blank-screen'],check=True,timeout=5)
assert Path('/sys/class/backlight/panel0-backlight/actual_brightness').read_text().strip()=='0'
assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==CONFIG['boot']
assert subprocess.check_output(['pidof','lipstick'],text=True).strip()==CONFIG['lipstick']
print(json.dumps(dict(applied=CONFIG['apply'],candidates=rows,stages=stage_rows,preserved=['r112','r98','r86','r123'])))
'''
subprocess.run(['bash',str(lock),'acquire','0','cts-prune-candidates'],check=True,timeout=15)
try:
 run=subprocess.run(['sshpass','-e','ssh','-o','ConnectTimeout=6','root@bonito','python3','-'],input=body.encode(),capture_output=True,check=True,timeout=110)
 value=json.loads(run.stdout);(a.evidence/('phone-candidate-prune.json'if a.apply else'phone-candidate-prune-plan.json')).write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value,indent=2))
finally:subprocess.run(['bash',str(lock),'release','cts-prune-candidates'],check=True,timeout=15)
