#!/usr/bin/env python3
"""Retest modules affected by implemented fixes; retain every previous attempt."""
from pathlib import Path
import argparse,json,subprocess,time
p=argparse.ArgumentParser();p.add_argument('evidence',type=Path);p.add_argument('--release',required=True);p.add_argument('--expected-boot',required=True);p.add_argument('--modules',nargs='+',required=True);a=p.parse_args();repo=Path(__file__).resolve().parents[2];stamp=time.strftime('%Y%m%dT%H%M%SZ',time.gmtime())
# No user app or test process is signalled by this local evidence operation.
# Each subsequent VM transaction acquires and enforces the normal device lock.
for name in a.modules:
 folder=a.evidence/'modules'/name
 if folder.exists():
  value=json.loads((folder/'attempt.json').read_text())
  if value['status']=='RUNNING':raise RuntimeError('Refuse to replace a running module '+name)
  archive=a.evidence/'history'/name/stamp;archive.parent.mkdir(parents=True,exist_ok=True);folder.rename(archive)
command=['python3',str(repo/'scripts/cts/run-modules.py'),str(a.evidence),'--release',a.release,'--max-seconds','240','--cross-package','--expected-boot',a.expected_boot,'--modules',*a.modules]
result=subprocess.run(command);raise SystemExit(result.returncode)
