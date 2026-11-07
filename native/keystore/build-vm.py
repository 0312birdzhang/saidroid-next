#!/usr/bin/env python3
"""Build the private software-keystore service implementation in the Linux VM.

Produces libraries/classes only. No daemon, service account, hardware claims,
package installation, app registration or phone changes. Test fixtures are opt-in.
"""
from pathlib import Path
import argparse,hashlib,json,os,subprocess
p=argparse.ArgumentParser(description=__doc__)
for n in ['inputs','product','abi-headers','java-home','output']:p.add_argument('--'+n,type=Path,required=True)
p.add_argument('--with-test-fixtures',action='store_true');a=p.parse_args();os.umask(0o022);repo=Path(__file__).resolve().parents[2];source=Path(__file__).resolve().parent;sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();assert not a.output.exists();a.output.mkdir(parents=True)
framework=a.inputs/'android-all-10-robolectric-5803371.jar';r8=a.inputs/'r8-8.3.37.jar';assert sha(framework)=='a0ad701eedd47bdaefbac1c2cc80dd400c0adea3cccd8a3ad286f79da1ca294c'and sha(r8)=='59753e70a74f918389cc87f1b7d66b5c0862932559167425708ded159e3de439';product=json.loads((a.product/'manifest.json').read_text());assert sha(a.product/'runtime.jar')==product['files']['runtime.jar'];assert(a.product/'classes').is_dir()
production=sorted((source/'java').glob('*.java'));assert {f.name for f in production}=={'NativeSoftwareKeymaster.java','SoftwareKeystoreService.java','TrustedAttestationIdentity.java'}
fixtures=[source/'tests'/n for n in ['CombinedKeystoreServer.java','AttestationStandardContract.java','AttestationKeystoreServer.java','LockAwareKeystoreServer.java','LockStateKeystoreContract.java','OperationLifecycleContract.java','SymmetricKeystoreContract.java','StandardKeystoreContract.java','ProviderKeystoreContract.java','KeystoreInstrumentationBootstrap.java','StandaloneKeystoreServer.java']]if a.with_test_fixtures else []
sources=fixtures[:3]+production+fixtures[3:]if fixtures else production;native=source/'software-keystore-jni.cpp';owned=sources+[native,*[source/n for n in ['private-blob-store.hpp','software-key-policy.hpp','mce-lock-state.hpp']]];initial={str(f.relative_to(repo)):sha(f)for f in owned};headers={str(f.relative_to(a.abi_headers)):sha(f)for f in sorted(a.abi_headers.rglob('*'))if f.is_file()};assert headers and all(not(a.abi_headers/n).is_symlink()for n in headers);commands=[]
def run(c):
 commands.append(c)
 with(a.output/'build.log').open('a')as log:subprocess.run(c,stdout=log,stderr=subprocess.STDOUT,check=True)
run(['g++','-shared','-fPIC','-std=c++17','-O2','-Wall','-Wextra','-Werror','-o',str(a.output/'libsoftware-keystore.so'),str(native),'-I'+str(a.java_home/'include'),'-I'+str(a.java_home/'include/linux'),'-I'+str(a.abi_headers),'-ldl','-pthread',*subprocess.check_output(['pkg-config','--cflags','--libs','gio-2.0'],text=True).split()])
classes=a.output/'classes';classes.mkdir();run([str(a.java_home/'bin/javac'),'--release','8','-nowarn','-cp',str(framework)+':'+str(a.product/'classes'),'-d',str(classes),*map(str,sources)]);jar=a.output/('contract.jar'if a.with_test_fixtures else'service.jar');run([str(a.java_home/'bin/java'),'-cp',str(r8),'com.android.tools.r8.D8','--release','--min-api','29','--lib',str(framework),'--output',str(jar),*map(str,classes.rglob('*.class'))])
assert all(sha(repo/n)==h for n,h in initial.items())and all(sha(a.abi_headers/n)==h for n,h in headers.items())
record=dict(schema='saildroid-standard-keystore-vm-build-v1',scope='Source-owned software-only keystore implementation build; test fixtures opt-in. No production daemon/account/discovery/hardware/auth backend or phone acceptance.',passed=True,builder_sha256=sha(Path(__file__)),with_test_fixtures=a.with_test_fixtures,sources=initial,abi_header_files=headers,inputs={str(f):sha(f)for f in[framework,r8,a.product/'runtime.jar',a.product/'manifest.json']},commands=commands,library_sha256=sha(a.output/'libsoftware-keystore.so'),jar=str(jar),jar_sha256=sha(jar),classes={str(f.relative_to(classes)):sha(f)for f in classes.rglob('*.class')});(a.output/'manifest.json').write_text(json.dumps(record,indent=2)+'\n');print('SOFTWARE_KEYSTORE=built|with_test_fixtures='+str(a.with_test_fixtures).lower()+'|phone_touched=false')
