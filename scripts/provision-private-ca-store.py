#!/usr/bin/env python3
"""Snapshot the existing Sailfish public CA roots into the private ART CA path."""
import subprocess

ssh = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=5', 'root@bonito']
body = r'''
from pathlib import Path
import hashlib,json,os,re,ssl
boot=Path('/proc/sys/kernel/random/boot_id')
expected='5db879ed-48ea-4bf0-b5c1-64e271c11045'
assert boot.read_text().strip()==expected
assert 'ID=sailfishos' in Path('/etc/sailfish-release').read_text()
source=Path('/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem')
data=source.read_bytes();digest=hashlib.sha256(data).hexdigest()
assert digest=='00411c197b16f659945fba3c2f970a26030f56eef5d445c913cb59a089c813b9'
certificates=re.findall(br'-----BEGIN CERTIFICATE-----\s+.*?-----END CERTIFICATE-----',data,re.S)
assert len(certificates)==146
root=Path('/home/art');target=root/'etc/security/cacerts'
for parent in [root,root/'test',root/'etc',root/'etc/security',target]:
 assert not parent.is_symlink()
assert not target.exists(),'Preserve an existing private CA store'
stage=root/'test/codex-private-ca-store-20261025-r1'
stage.mkdir(mode=0o700)
candidate=stage/'cacerts';candidate.mkdir(mode=0o755)
records={}
for pem in certificates:
 der=ssl.PEM_cert_to_DER_cert(pem.decode('ascii'))
 name=hashlib.sha256(der).hexdigest()+'.pem'
 if name in records:continue
 raw=pem+b'\n'
 with (candidate/name).open('xb') as f:f.write(raw)
 (candidate/name).chmod(0o644)
 records[name]=hashlib.sha256(raw).hexdigest()
target.parent.mkdir(parents=True,exist_ok=True)
os.rename(candidate,target)
manifest=dict(result='private_ca_store=ready',source=str(source),source_sha256=digest,
 target=str(target),certificates=len(records),files=records,boot=expected)
(stage/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
assert source.read_bytes()==data and boot.read_text().strip()==expected
print(json.dumps({key:value for key,value in manifest.items() if key!='files'}))
'''
subprocess.run(ssh + ['python3 -'], input=body.encode(), check=True, timeout=20)
