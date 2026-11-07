#!/usr/bin/env python3
"""Reproduce an accepted host, then change only its linker RUNPATH for packaging."""
from pathlib import Path
import argparse,hashlib,json,subprocess,shutil
p=argparse.ArgumentParser();p.add_argument('--reference',type=Path,required=True);p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
assert not a.output.exists();a.output.mkdir(parents=True)
reference=json.loads(a.reference.read_text());assert reference['passed'];sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
expected=reference['sha256'];assert sha(a.root/'libexec/saildroid-host')==expected
cmd=list(reference['commands'][-1]);sources={v:sha(v)for v in cmd if v.endswith(('.cpp','.c'))and Path(v).is_file()}
assert '-Wl,-rpath,/home/art/lib'in cmd
first=list(cmd);first[first.index('-o')+1]=str(a.output/'baseline-host')
with(a.output/'baseline-build.log').open('wb')as log:subprocess.run(first,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=240)
assert sha(a.output/'baseline-host')==expected,'Accepted source no longer reproduces baseline host'
second=list(cmd);second[second.index('-o')+1]=str(a.output/'origin-host');second[second.index('-Wl,-rpath,/home/art/lib')]='-Wl,-rpath,$ORIGIN/../lib'
with(a.output/'origin-build.log').open('wb')as log:subprocess.run(second,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=240)
assert all(sha(k)==v for k,v in sources.items())
dynamic=subprocess.check_output(['readelf','-dW',str(a.output/'origin-host')],text=True)
assert '[$ORIGIN/../lib]'in dynamic and '/home/art/lib'not in dynamic
shutil.copyfile(a.output/'origin-host',a.root/'libexec/saildroid-host');(a.root/'libexec/saildroid-host').chmod(0o755)
record=dict(passed=True,baseline_byte_identical=True,baseline_sha256=expected,
            relocated_sha256=sha(a.output/'origin-host'),source_hashes=sources,
            commands=[first,second],only_semantic_build_change='RUNPATH=/home/art/lib -> $ORIGIN/../lib',
            root=str(a.root),target_tested=False)
(a.output/'result.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({k:v for k,v in record.items()if k not in ['commands','source_hashes']},indent=2))
