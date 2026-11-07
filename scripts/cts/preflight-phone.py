"""Read-only CTS target preflight. Run over the existing verified VM SSH link."""
from pathlib import Path
import os,subprocess,shutil,json
assert 'ID=sailfishos'in Path('/etc/sailfish-release').read_text()
root=Path('/home/art/api29-root').resolve()
server=subprocess.run(['pidof','system_server'],capture_output=True,text=True,timeout=4)
commands={n:shutil.which(n)for n in ['adbd','am','pm','cmd','getprop','dumpsys']}
identity={}
for package in ['com.tencent.mobileqq','org.example.saildroid.ctsharness','com.android.cts.verifier']:
 p=Path('/home/art/apps')/package/'record.json'
 if p.is_file():identity[package]=p.stat().st_uid
value=dict(os=Path('/etc/sailfish-release').read_text(),boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),lipstick=subprocess.check_output(['pidof','lipstick'],text=True).strip(),daily_release=str(root),commands=commands,system_server_pids=server.stdout.strip().split(),app_record_owner_uids=identity,formal_cts_status='BLOCKED',formal_cts_test_count=0)
print(json.dumps(value,indent=2))
