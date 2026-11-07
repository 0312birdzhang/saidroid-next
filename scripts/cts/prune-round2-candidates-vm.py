#!/usr/bin/env python3
"""Verify exact superseded candidate roots, then optionally retire them.

Run only after the serial suite has ended. r128 was a failed staging attempt:
its original manifest contains duplicate framework aliases. Its actual files
are verified against the canonicalized expected paths before any removal.
"""
from pathlib import Path
import argparse, hashlib, json, os, subprocess

p = argparse.ArgumentParser()
p.add_argument('evidence', type=Path)
p.add_argument('--apply', action='store_true')
p.add_argument('--expected-boot', required=True)
p.add_argument('--expected-lipstick', required=True)
a = p.parse_args()
repo = Path('/media/psf/Home/WorkSpace/saidroid-next')
os.environ['SSHPASS'] = os.environ['SSHPASS']
expected, stages = {}, {}
snapshots = {r['runtime']: r for r in json.loads((a.evidence / 'runtime-history/vm-prune-plan.json').read_text())}
for version in [124, 126, 127, 128, 129]:
    label = 'r' + str(version)
    meta = json.loads((a.evidence / 'runtime-history' / label / 'bundle/overlay.json').read_text())
    expected['api29-' + label + '-native-candidate'] = meta['install_manifest']
    stages[label + '-native-candidate'] = dict(sha256=snapshots[label]['tarball_sha256'], manifest=meta['install_manifest'])
current = Path('/var/tmp/saidroid-native-transition-20261030-r130/bundle')
stages['r130-native-candidate'] = dict(sha256=hashlib.sha256((current / 'native-overlay.tar.gz').read_bytes()).hexdigest(),
    manifest=json.loads((current / 'overlay.json').read_text())['install_manifest'])
config = dict(apply=a.apply, expected=expected, stages=stages,
    boot=a.expected_boot, lipstick=a.expected_lipstick)
body = 'CONFIG=' + repr(config) + '\n' + r'''
from pathlib import Path
import hashlib,json,os,shutil,stat,subprocess
assert Path('/home/art/test/.device-lock/owner').read_text().startswith('cts-prune-round2|')
assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==CONFIG['boot']
assert subprocess.check_output(['pidof','lipstick'],text=True).strip()==CONFIG['lipstick']
preserved=['api29-r112-native-candidate','api29-r98-native-gate','api29-r86-compat','api29-r123-native-candidate','api29-r130-native-candidate']
assert Path('/home/art/api29-root').resolve()==Path('/home/art/releases/api29-r112-native-candidate')
for name in preserved:assert(Path('/home/art/releases')/name).is_dir()
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
  assert not exe.startswith(str(root)+'/')and str(root).encode()not in cmd,'Referenced candidate '+proc.name
 files=dict(manifest['files']);normalized=[]
 if name=='api29-r128-native-candidate':
  aliases={k:v for k,v in files.items()if k.startswith('framework/')}
  assert len(aliases)==30
  assert all(k.startswith('framework/arm64/boot')and Path(k).suffix in['.art','.oat','.vdex']for k in aliases)
  for relative,entry in aliases.items():
   canonical='system/'+relative
   assert canonical in files
   files[canonical]=entry;del files[relative]
   normalized.append(dict(original=relative,canonical=canonical,sha256=entry['sha256']))
 for relative,entry in files.items():
  part=Path(relative);assert not part.is_absolute()and '..'not in part.parts
  assert not any((root/parent).is_symlink()for parent in part.parents if str(parent)!='.')
  path=root/relative
  assert path.is_file()and not path.is_symlink(),relative
  assert hashlib.sha256(path.read_bytes()).hexdigest()==entry['sha256'],relative
  assert stat.S_IMODE(path.stat().st_mode)==entry['mode'],relative
 for relative,target in manifest['symlinks'].items():assert(root/relative).is_symlink()and os.readlink(root/relative)==target
 size=int(subprocess.check_output(['du','-sk',str(root)],text=True).split()[0])
 rows.append(dict(root=str(root),logical_kib=size,files_verified=len(files),failed_stage_alias_normalization=normalized,removed=CONFIG['apply']))
 if CONFIG['apply']:shutil.rmtree(root)
for name,info in CONFIG['stages'].items():
 stage=Path('/home/art/test')/('native-overlay-'+name)
 if not stage.exists():continue
 assert stage.is_dir()and not stage.is_symlink()and stage.stat().st_uid==0
 assert hashlib.sha256((stage/'native-overlay.tar.gz').read_bytes()).hexdigest()==info['sha256']
 assert json.loads((stage/'unpacked/overlay.json').read_text())['install_manifest']==info['manifest']
 stage_rows.append(dict(stage=str(stage),removed=CONFIG['apply']))
 if CONFIG['apply']:shutil.rmtree(stage)
subprocess.run(['mcetool','--set-never-blank=disabled','--blank-screen'],check=True,timeout=5)
assert Path('/sys/class/backlight/panel0-backlight/actual_brightness').read_text().strip()=='0'
assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==CONFIG['boot']
assert subprocess.check_output(['pidof','lipstick'],text=True).strip()==CONFIG['lipstick']
print(json.dumps(dict(applied=CONFIG['apply'],candidates=rows,stages=stage_rows,preserved=preserved,
 note='Logical candidate sizes include shared hardlinks; not a measure of freed physical storage')))
'''
subprocess.run(['bash', str(repo / 'scripts/devlock.sh'), 'acquire', '0', 'cts-prune-round2'], check=True, timeout=15)
try:
    run = subprocess.run(['sshpass','-e','ssh','-o','ConnectTimeout=6','root@bonito','python3','-'],
        input=body.encode(), capture_output=True, check=True, timeout=120)
    result = json.loads(run.stdout)
    (a.evidence / ('phone-candidate-prune.json' if a.apply else 'phone-candidate-prune-plan.json')).write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
finally:
    subprocess.run(['bash', str(repo / 'scripts/devlock.sh'), 'release', 'cts-prune-round2'], check=True, timeout=15)
