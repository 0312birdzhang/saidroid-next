"""Separate original file-class diagnostic with real product JNI and Crypto/TLS initialization, UID65534.

This is an environment correction to the bare-core probe, not a CTS runner or
an APK/test replacement. Native registration uses the unchanged product179.
"""
from pathlib import Path
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import zipfile

if '--inside' not in sys.argv:
    p=subprocess.run(['unshare','--mount','--',sys.executable,str(Path(__file__).resolve()),'--inside'],capture_output=True,text=True,timeout=1800)
    print(p.stdout); print(p.stderr,file=sys.stderr);sys.exit(p.returncode)
subprocess.run(['mount','--make-rprivate','/'],check=True)
subprocess.run(['mount','-t','tmpfs','-o','mode=0755,size=4m,nr_inodes=64','tmpfs','/home'],check=True)
Path('/home/art').mkdir(mode=0o755)
Path('/home/art').chmod(0o755)
Path('/home/art/api29-root').symlink_to('/var/tmp/saidroid-classpath-cache-lifecycle263-v2-formal-vm-component/root')

os.umask(0o022)

repo = Path('/media/psf/Home/WorkSpace/saidroid-next')
base = repo / 'build/evidence/cts-frame-repair-20261031'
clone = Path('/var/tmp/saidroid-unprivileged182-runtime-20261031')
work = Path('/var/tmp/saidroid-pem-empty266-own-contract-v4')
work.mkdir(mode=0o755)
inventory=json.loads((base/'lang187-class-inventory.json').read_text())
apk=clone/'CtsLibcoreTestCases.apk';runner_apk=apk
assert hashlib.sha256(apk.read_bytes()).hexdigest()==inventory['apk_sha256']
selections=['libcore.android.system.OsTest#'+n for n in ['testSocketpairNullFileDescriptor1','testSocketpairNullFileDescriptor2','testSocketpairNullFileDescriptorBoth','testInetPtonIpv6','testCrossFamilyBindConnectSendto','test_sendtoSocketAddress_af_inet','test_sendtoSocketAddress_af_inet6']]
product = Path('/var/tmp/saidroid-native-transition-20261031-r191/product')
manifest = json.loads((product / 'manifest.json').read_text())
private_product = work / 'product'
private_product.mkdir()
copied = {}
for name in ['runtime.jar', 'libsdhost29.so', 'libsdbridge.so']:
    source = product / name
    assert hashlib.sha256(source.read_bytes()).hexdigest() == manifest['files'][name]
    shutil.copyfile(source, private_product / name)
    (private_product / name).chmod(0o444)
    copied[name] = manifest['files'][name]
old_bundle = Path('/var/tmp/saidroid-native-transition-20261031-r184/bundle')
overlay = json.loads((old_bundle / 'overlay.json').read_text())
buildprop = old_bundle / 'payload/build.prop'
assert hashlib.sha256(buildprop.read_bytes()).hexdigest() == overlay['install_manifest']['files']['build.prop']['sha256']
shutil.copyfile(buildprop, private_product / 'build.prop')
(private_product / 'build.prop').chmod(0o444)
apk_native=work/'apk-native';apk_native.mkdir(mode=0o755);native_files={}
with zipfile.ZipFile(apk)as archive:
 for n in archive.namelist():
  if n.startswith('lib/arm64-v8a/')and n.endswith('.so'):
   target=apk_native/Path(n).name;assert n=='lib/arm64-v8a/'+target.name;target.write_bytes(archive.read(n));target.chmod(0o444);native_files[n]=hashlib.sha256(target.read_bytes()).hexdigest();assert 'AArch64'in subprocess.check_output(['readelf','-h',str(target)],text=True)
assert native_files
java = Path('/tmp/jdkfull/jdk-21.0.13+9/bin')
inputs = repo / 'build/codex-api29/inputs'
framework = inputs / 'android-all-10-robolectric-5803371.jar'
fixture=work/'pem-fixture';fixture.mkdir(mode=0o700);key=fixture/'ca.key';(fixture/'index.txt').write_text('');(fixture/'serial.txt').write_text('1000\n');(fixture/'crlnumber.txt').write_text('1000\n');conf=fixture/'openssl.cnf'
conf.write_text('[ca]\ndefault_ca=local\n[local]\ndatabase='+str(fixture/'index.txt')+'\nserial='+str(fixture/'serial.txt')+'\ncrlnumber='+str(fixture/'crlnumber.txt')+'\nprivate_key='+str(key)+'\ncertificate='+str(fixture/'ca.pem')+'\ndefault_md=sha256\ndefault_crl_days=2\npolicy=policy\n[policy]\ncommonName=supplied\n[req]\nprompt=no\ndistinguished_name=dn\nx509_extensions=v3_ca\n[dn]\nCN=SailDroid ephemeral parser fixture\n[v3_ca]\nbasicConstraints=critical,CA:true\nkeyUsage=critical,keyCertSign,cRLSign\nsubjectKeyIdentifier=hash\nauthorityKeyIdentifier=keyid:always\n')
try:
 with(work/'fixture-build.log').open('x')as log:
  for cmd in [['openssl','req','-new','-x509','-newkey','rsa:2048','-nodes','-keyout',str(key),'-out',str(fixture/'ca.pem'),'-days','2','-config',str(conf)],['openssl','x509','-in',str(fixture/'ca.pem'),'-outform','DER','-out',str(fixture/'ca.der')],['openssl','ca','-gencrl','-config',str(conf),'-out',str(fixture/'valid.crl.pem'),'-batch'],['openssl','crl','-in',str(fixture/'valid.crl.pem'),'-outform','DER','-out',str(fixture/'valid.crl.der')]]:subprocess.run(cmd,stdout=log,stderr=log,check=True,timeout=30)
finally:
 if key.exists():key.unlink()
assert not key.exists();fixture.chmod(0o755)
for n in ['ca.pem','ca.der','valid.crl.pem','valid.crl.der']:(fixture/n).chmod(0o444)
classes = work / 'classes'
classes.mkdir()
source = base / 'PemEmpty266ContractRunner.java'
subprocess.run([str(java / 'javac'), '-source','8','-target','8','-nowarn','-bootclasspath','/var/tmp/saidroid-classpath-cache-lifecycle263-module-v3/core-oj-classes.jar:/var/tmp/saidroid-classpath-cache-lifecycle263-module-v3/core-libart-classes.jar:'+str(framework),
                '-d', str(classes), str(source),str(repo/'scripts/api29/tests/pem-empty/PemEmpty266Contract.java')], check=True)
subprocess.run([str(java / 'java'), '-cp', str(inputs / 'r8-8.3.37.jar'),
                'com.android.tools.r8.D8', '--release', '--min-api', '29', '--lib', str(framework),
                '--output', str(work / 'runner.jar'), *map(str, classes.rglob('*.class'))], check=True)
compile_junit=repo/'third_party/art-standalone/libcore/support/src/test/java/tests/resources/junit4-4.3.1.jar'
assert hashlib.sha256(compile_junit.read_bytes()).hexdigest()=='c9e01c6b466b9d86e44a4e2096c8bbbf5818d31573c12c0862aea7b0b9daf0b6'
listener_classes=work/'listener-classes';listener_classes.mkdir()
subprocess.run([str(java/'javac'),'--release','8','-cp',str(compile_junit),'-d',str(listener_classes),str(base/'OriginalOj195EventListenerV2.java')],check=True)
listener=work/'listener.jar'
subprocess.run([str(java/'java'),'-cp',str(inputs/'r8-8.3.37.jar'),'com.android.tools.r8.D8','--release','--min-api','29','--lib',str(framework),'--classpath',str(compile_junit),'--output',str(listener),str(listener_classes/'OriginalOj195EventListenerV2.class')],check=True)
androidroot = work / 'androidroot'
tz = androidroot / 'usr/share/zoneinfo'
tz.mkdir(parents=True)
with zipfile.ZipFile(framework) as z:
    for name in ['tzdata', 'tzlookup.xml']:
        (tz / name).write_bytes(z.read('usr/share/zoneinfo/' + name))
data = work / 'private'
data.mkdir(mode=0o700)
os.chown(data, 65534, 65534)
for name in ['home', 'tmp', 'config', 'dexcache', 'code_cache']:
    path = data / name
    path.mkdir(mode=0o700)
    os.chown(path, 65534, 65534)
config = data / 'config/runtime.cfg'
config.write_text('libc.so libc_bio.so.0\nlibstdc++.so libstdc++_bio.so.0\nlibm.so libm.so.6\nlibdl.so libdl.so.2\n')
os.chown(config, 65534, 65534)
config.chmod(0o600)
native = Path('/var/tmp/saidroid-readable-android-product-runtime-20261031')
native_copy=json.loads((native/'source-manifest.json').read_text())
assert all(hashlib.sha256((native/n).read_bytes()).hexdigest()==v['sha256']for n,v in native_copy['files'].items())
component = Path('/var/tmp/saidroid-classpath-cache-lifecycle263-v2-formal-vm-component/root')
runtime = json.loads((component/'runtime.json').read_text())
base_paths = [component / name for name in runtime['boot_jars']]
paths=base_paths + [work / 'runner.jar', component / 'lib/runtime.jar']
locations = ['/home/art/api29-root/' + name for name in runtime['boot_jars']] + list(map(str, paths[-2:]))
linker_source=Path('/var/tmp/saidroid-linker-cfi-owner-20261031/libdl_bio.so.0');linker_manifest=json.loads((linker_source.parent/'manifest.json').read_text());assert hashlib.sha256(linker_source.read_bytes()).hexdigest()==linker_manifest['sha256']
private_linker=work/'linker';private_linker.mkdir(mode=0o755);shutil.copyfile(linker_source,private_linker/linker_source.name);(private_linker/linker_source.name).chmod(0o444)
prefix = str(component/'lib')+':'+str(clone / 'icu') + ':' + str(clone / 'artlib')
env = dict(PATH='/usr/bin:/bin', HOME=str(data / 'home'), TMPDIR=str(data / 'tmp'), LANG='C.UTF-8',
           LD_LIBRARY_PATH='/var/tmp/saidroid-actual-phone-openjdk-20261031:'+str(clone / 'crypto') + ':' + prefix + ':' + str(clone / 'patched') + ':' +
           str(private_linker) + ':' + str(clone / 'homeart') + ':/usr/local/lib',
           LD_PRELOAD='/var/tmp/saidroid-fdlibm-native-20261031-r188-v4/libsdstrictmath-fdlibm.so:/var/tmp/saidroid-character-native-20261031-r189-v2/libsdcharacter-icu63.so:'+str(private_product / 'libsdhost29.so')+':'+str(private_linker/'libdl_bio.so.0'),
           BIONIC_TRANSLATION_CONFIG_DIR=str(data / 'config'), ANDROID_ROOT=str(androidroot),
           ANDROID_DATA=str(data), SAILDROID_DATA_DIR=str(data),
           SD_BUILD_PROP=str(private_product / 'build.prop'), ICU_DATA=str(clone / 'bionic-icu'))


def nobody():
    import resource
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    os.setgroups([])
    os.setgid(65534)
    os.setuid(65534)
    os.umask(0o077)


install_manifest=json.loads((component/'install-manifest.json').read_text())
assert all(hashlib.sha256((component/n).read_bytes()).hexdigest()==v['sha256']for n,v in install_manifest['files'].items())
newimages=json.loads((component/'share/build/boot-image-manifest.json').read_text())
required = [component/n for n in install_manifest['files']]+[clone/'bin/dalvikvm',listener,private_product/'libsdbridge.so',native/'lib64/libandroid_runtime.so']
required_list=work/'required-files.json';required_list.write_text(json.dumps(list(map(str,required))));required_list.chmod(0o444)
probe = subprocess.run([sys.executable, '-c',
                        'import os,json,sys; p=json.load(open(sys.argv[1])); bad=[v for v in p if not os.access(v,os.R_OK)]; print(json.dumps(dict(uid=os.getuid(),unreadable=bad))); sys.exit(bool(bad))',
                        str(required_list)], preexec_fn=nobody,
                       env=dict(PATH='/usr/bin:/bin', HOME=str(data / 'home')),
                       cwd=data, capture_output=True, text=True, timeout=20)
(base / 'pem-empty266-own-contract-v4-preflight.json').write_text(probe.stdout)
assert probe.returncode == 0, probe.stdout + probe.stderr
sys.path.insert(0, str(repo / 'scripts/cts'))
from apk_manifest import parse
sdk = next(n['attributes']['targetSdkVersion'] for n in parse(apk)['manifest']['children'] if n['tag'] == 'uses-sdk')
assert type(sdk) is int and sdk == 29
policy_source=repo/'native/host/tests/app-filesystem-policy-exec.cpp'
policy=work/'app-policy-exec'
subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',str(policy_source),'-o',str(policy)],check=True)
policy.chmod(0o555)
art_build=json.loads((base/'art240-host-math-precision-v1-build.json').read_text());assert art_build['passed']and art_build['unmodified_art_reproduced_byte_identical']and art_build['vm_baseline_sources_and_objects_restored'];assert hashlib.sha256(Path('/var/tmp/saidroid-art240-host-math-precision-v1/libart.so').read_bytes()).hexdigest()==art_build['binary_sha256']
results = []
for label in ['before263', 'after266']:
 for selection in [label]:
    native_jni=component/'lib'
    actualhost=component/'lib/libsdhost29.so'
    run_env=dict(env,LD_PRELOAD=env['LD_PRELOAD'].replace(str(private_product/'libsdhost29.so'),str(actualhost)))
    run_env.update(ANDROID_ROOT=str(component),ANDROID_RUNTIME_ROOT=str(component/'apex/com.android.runtime.debug'),ANDROID_TZDATA_ROOT=str(component/'apex/com.android.tzdata'),ICU_DATA=str(component/'usr/icu'))
    boot_root=component/'system/framework';actual_runtime=component/'lib/runtime.jar'
    active_boot_jars=runtime['boot_jars'];variant=Path('/var/tmp/saidroid-pem-empty266-encoded-v1' if label=='after266' else '/var/tmp/saidroid-classpath-cache-lifecycle263-encoded-v1');encoded=variant/'encoded';boot_root=variant/'boot';actual_runtime=encoded/'lib/runtime.jar';active_images=json.loads((boot_root/'manifest.json').read_text())
    encoded_meta=json.loads((encoded/'manifest.json').read_text());assert all(hashlib.sha256((encoded/n).read_bytes()).hexdigest()==v['sha256']for n,v in encoded_meta['files'].items())
    assert all(hashlib.sha256((boot_root/n).read_bytes()).hexdigest()==v for n,v in active_images.items())
    paths=[encoded/n for n in active_boot_jars]+[work/'runner.jar',actual_runtime]
    assert all(f.is_file()and os.access(f,os.R_OK)for f in paths)
    run_locations=['/home/art/api29-root/'+n for n in active_boot_jars]+[str(work/'runner.jar'),str(actual_runtime)]
    actualart=component/'lib/libart.so'
    companion=Path('/var/tmp/saidroid-math-precision240-companion-v1/libsdmath-precision.so')
    if label!='before237':run_env['LD_PRELOAD']=str(companion)+':'+run_env['LD_PRELOAD']
    cmd = [str(policy), str(clone / 'bin/dalvikvm'), '-XXlib:' + str(actualart),
           '-Xnoimage-dex2oat', '-Ximage:' + str(boot_root/'boot.art'),
           '-Xbootclasspath:' + ':'.join(map(str, paths)), '-Xbootclasspath-locations:' + ':'.join(run_locations),
           '-Djava.library.path='+str(native_jni)+':'+str(component/'lib')+':/var/tmp/saidroid-actual-phone-openjdk-20261031:' + str(native / 'apex/com.android.conscrypt/lib64') + ':' + str(native / 'lib64') + ':' + str(clone / 'crypto') + ':' + prefix + ':' + str(clone / 'homeart'),
           '-Dsaidroid.test.character.helper=/var/tmp/saidroid-character-native-20261031-r189-v2/libsdcharacter-icu63.so',
           '-Dsaidroid.test.fdlibm.helper=/var/tmp/saidroid-fdlibm-native-20261031-r188-v4/libsdstrictmath-fdlibm.so',
           '-Dsaidroid.test.apk.native='+str(apk_native),'-Dsaidroid.test.hamcrest.owner=apk','-Dsaidroid.test.pem.fixture='+str(fixture),
           '-Dsaidroid.bridge.library=' + str(component / 'lib/libsdbridge.so'),
           '-Dsaidroid.native.runtime=' + str(native / 'lib64'), '-Dsaidroid.native.root=' + str(native),
           '-Dsaidroid.test.host='+str(actualhost),'-Dsaidroid.test.javacore='+str(native_jni/'libjavacore.so'),'-Dsaidroid.test.art='+str(actualart),'-Dsaidroid.test.boot-images='+';'.join(str(boot_root/n)for n in active_images if n.endswith('.art')),'-Xhidden-api-policy:disabled', '-cp', str(work / 'empty.jar'),
           'PemEmpty266ContractRunner', str(apk), selection, str(sdk), str(listener), str(data / 'dexcache'),str(runner_apk)]
    started = time.monotonic()
    p = subprocess.run(cmd, env=run_env, preexec_fn=nobody, cwd=data, capture_output=True, text=True, timeout=1800)
    (work / (label+'-'+selection + '.stdout')).write_text(p.stdout)
    (work / (label+'-'+selection + '.stderr')).write_text(p.stderr)
    marker=next((s for s in p.stdout.splitlines()if s.startswith('PEM_EMPTY266_CONTRACT=PASS|')),None)
    if label=='before263':
     assert p.returncode!=0 and not marker and 'AssertionError: empty PEM record rejected instead of no certificate' in p.stderr,p.stdout[-2500:]+p.stderr[-4000:]
    else:assert p.returncode==0 and marker,p.stdout[-2500:]+p.stderr[-4000:]
    assert 'FINAL_NATIVE_COMPONENT_MAP=verified'in p.stdout and'OJ195_BOOT_IMAGES=verified|count=9'in p.stdout and'PLATFORM_CORE_BOOTSTRAP|registered=104|uid=65534'in p.stdout
    jit=[l for l in p.stderr.splitlines()if 'MathPrecision240Contract' in l and ('compiled' in l.lower() or 'compiling'in l.lower())]
    row=dict(boundary=label,returncode=p.returncode,actual_runtime_sha256=hashlib.sha256(actual_runtime.read_bytes()).hexdigest(),actual_encoded_manifest_sha256=hashlib.sha256((encoded/'manifest.json').read_bytes()).hexdigest(),marker=marker,jit_evidence=jit,stdout_sha256=hashlib.sha256(p.stdout.encode()).hexdigest(),stderr_sha256=hashlib.sha256(p.stderr.encode()).hexdigest(),command=cmd)
    results.append(row);print(json.dumps(row),flush=True)
record=dict(valid_certificate_pem_sha256=hashlib.sha256((fixture/'ca.pem').read_bytes()).hexdigest(),valid_crl_pem_sha256=hashlib.sha256((fixture/'valid.crl.pem').read_bytes()).hexdigest(),fixture_private_key_removed=not key.exists(),source_meta_sha256=hashlib.sha256((repo/'scripts/api29/core/pem-empty-compat/sources.json').read_bytes()).hexdigest(),scope='Independent zero-payload PEM/noobject semantics plusfresh real certificate/CRL PEM/DER/CRLF/signatureverification/datechecks and malformednonempty/footer/Base64/DER/badsignature rejection. Before263 vs266 BC only, runtime260/cores263/nativeARTunchanged. SDK29UID65534actualJNI1049images. TemporaryCA keyremoved. Notphone/fullmoduleacceptance',passed=True,results=results,source_sha256=hashlib.sha256((repo/'scripts/api29/tests/pem-empty/PemEmpty266Contract.java').read_bytes()).hexdigest(),runner_source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),art_candidate_sha256=hashlib.sha256(actualart.read_bytes()).hexdigest(),companion_sha256=hashlib.sha256(companion.read_bytes()).hexdigest())
(base/'pem-empty266-own-contract-v4.json').write_text(json.dumps(record,indent=2)+'\n')
