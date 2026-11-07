#!/usr/bin/env python3
"""Build a read-only component property CLI over a pinned existing native backend.
The backend is copied unchanged, not rebuilt or relabeled as Android's shared
property service. Its historical provenance and limitations remain explicit.
"""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess
p=argparse.ArgumentParser();p.add_argument('backend',type=Path);p.add_argument('output',type=Path);p.add_argument('--expected-backend-sha256',required=True);a=p.parse_args()
repo=Path(__file__).resolve().parents[2];sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();source=Path(__file__).with_name('private-getprop.cpp')
assert a.backend.is_file()and sha(a.backend)==a.expected_backend_sha256
assert not a.output.exists();a.output.mkdir(parents=True)
command=['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror','-o',str(a.output/'getprop'),str(source),'-ldl']
with(a.output/'build.log').open('w')as log:subprocess.run(command,check=True,stdout=log,stderr=subprocess.STDOUT)
shutil.copyfile(a.backend,a.output/'libc_bio.so.0');(a.output/'getprop').chmod(0o755);(a.output/'libc_bio.so.0').chmod(0o444)
headers={}
for name in ['getprop','libc_bio.so.0']:
 text=subprocess.check_output(['readelf','-h',str(a.output/name)],text=True);assert 'ELF64'in text and 'AArch64'in text;headers[name]=text
symbols=subprocess.check_output(['nm','-D','--defined-only',str(a.output/'libc_bio.so.0')],text=True)
for name in ['get','read','foreach']:assert ' bionic___system_property_'+name+'\n'in symbols
references={}
for relative in ['third_party/bionic_translation/README.md','third_party/bionic_translation/linker/NOTICE','third_party/bionic_translation/libc/props.c']:
 src=repo/relative;references[relative]=sha(src);dst=a.output/'reference'/Path(relative).name;dst.parent.mkdir(exist_ok=True);shutil.copyfile(src,dst);dst.chmod(0o444)
notice='''SailDroid private property command\n\nThe getprop command is repository-owned code. Its native property backend is\nan unchanged copy of the existing Bionic translation binary, identified by\nSHA-256 in manifest.json. The backend is not rebuilt by this tool. The supplied\nreference files describe the existing source tree and its linker notices; they\nare reference material, not a claim that this binary was rebuilt from this\ncheckout. The source tree's existing uncommitted state is preserved.\n\nThis implements component property reads and enumeration, not a shared mutable\nAndroid property service, setprop, or certification of a secure Android build.\n\nExisting linker notices follow:\n\n'''+(repo/'third_party/bionic_translation/linker/NOTICE').read_text()
(a.output/'NOTICE').write_text(notice)
m=dict(schema='saildroid-private-getprop-v2',source_sha256=sha(source),binary_sha256=sha(a.output/'getprop'),property_backend_sha256=sha(a.output/'libc_bio.so.0'),backend_copied_unchanged=True,backend_original_path=str(a.backend),reference_source_hashes=references,backend_build_from_reference_sources_claimed=False,notice_sha256=sha(a.output/'NOTICE'),architecture='AArch64',command=command,interface=['getprop','getprop NAME','getprop NAME DEFAULT'],unsupported=['property type options','property writes','shared Android property service lifecycle'],scope='All application processes; read-only component build.prop through the same existing native property implementation, no test-specific keys or host command wrapper')
(a.output/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');assert sha(a.backend)==a.expected_backend_sha256
print('PRIVATE_GETPROP=compiled|architecture=AArch64|native_backend_unchanged=true')
