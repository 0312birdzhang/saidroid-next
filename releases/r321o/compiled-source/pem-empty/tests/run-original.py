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

os.umask(0o022)

repo = Path('/media/psf/Home/WorkSpace/saidroid-next')
base = repo / 'build/evidence/cts-frame-repair-20261031'
clone = Path('/var/tmp/saidroid-unprivileged182-runtime-20261031')
work = Path('/var/tmp/saidroid-original-pem-empty266-selected-v1')
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
classes = work / 'classes'
classes.mkdir()
source = base / 'Hamcrest235OriginalJUnitEventRunnerV2.java'
subprocess.run([str(java / 'javac'), '--release', '8', '-nowarn', '-cp', str(framework),
                '-d', str(classes), str(source)], check=True)
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
(base / 'original-pem-empty266-selected-v1-preflight.json').write_text(probe.stdout)
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
extended=Path('/var/tmp/saidroid-pem-empty266-encoded-v1');newencoded=extended/'encoded';newboot=extended/'boot'
newimages_after=json.loads((newboot/'manifest.json').read_text());assert len(newimages_after)==27
assert all(hashlib.sha256((newencoded/n).read_bytes()).hexdigest()==v['sha256']for n,v in json.loads((newencoded/'manifest.json').read_text())['files'].items())
assert all(hashlib.sha256((newboot/n).read_bytes()).hexdigest()==v for n,v in newimages_after.items())
new_required=[str(f)for parent in [newencoded,newboot]for f in parent.rglob('*')if f.is_file()]
check=subprocess.run([sys.executable,'-c','import os,json,sys;p=json.loads(sys.argv[1]);bad=[f for f in p if not os.access(f,os.R_OK)];print(json.dumps(dict(uid=os.getuid(),unreadable=bad)));sys.exit(bool(bad))',json.dumps(new_required)],preexec_fn=nobody,cwd=data,text=True,capture_output=True,timeout=20)
assert check.returncode==0,check.stdout+check.stderr
(base/('original-pem-empty266-selected-v1-after-readability.json')).write_text(check.stdout)

for label in ['before263','after266']:
 for selection in ['com.android.org.conscrypt.java.security.cert.CertificateFactoryTest', 'libcore.java.security.cert.X509CRLTest', 'tests.security.cert.CertificateFactory2Test', 'tests.security.cert.X509CRLTest', 'tests.targets.security.cert.CertificateFactoryTestX509']:
    native_jni=component/'lib'
    actualhost=component/'lib/libsdhost29.so'
    run_env=dict(env,LD_PRELOAD=env['LD_PRELOAD'].replace(str(private_product/'libsdhost29.so'),str(actualhost)))
    run_env.update(ANDROID_ROOT=str(component),ANDROID_RUNTIME_ROOT=str(component/'apex/com.android.runtime.debug'),ANDROID_TZDATA_ROOT=str(component/'apex/com.android.tzdata'),ICU_DATA=str(component/'usr/icu'))
    boot_root=component/'system/framework';actual_runtime=component/'lib/runtime.jar'
    active_boot_jars=runtime['boot_jars'];active_images=newimages if label=='before263'else newimages_after
    if label=='after266':boot_root=newboot
    paths=[(component if label=='before263'else newencoded)/n for n in active_boot_jars]+[work/'runner.jar',actual_runtime]
    run_locations=['/home/art/api29-root/'+n for n in active_boot_jars]+[str(work/'runner.jar'),str(actual_runtime)]
    actualart=component/'lib/libart.so'
    companion=component/'lib/libsdmath-precision.so'
    run_env['LD_PRELOAD']=str(companion)+':'+run_env['LD_PRELOAD']
    cmd = [str(policy), str(clone / 'bin/dalvikvm'), '-XXlib:' + str(actualart),
           '-Xnoimage-dex2oat', '-Ximage:' + str(boot_root/'boot.art'),
           '-Xbootclasspath:' + ':'.join(map(str, paths)), '-Xbootclasspath-locations:' + ':'.join(run_locations),
           '-Djava.library.path='+str(native_jni)+':'+str(component/'lib')+':/var/tmp/saidroid-actual-phone-openjdk-20261031:' + str(native / 'apex/com.android.conscrypt/lib64') + ':' + str(native / 'lib64') + ':' + str(clone / 'crypto') + ':' + prefix + ':' + str(clone / 'homeart'),
           '-Dsaidroid.test.character.helper=/var/tmp/saidroid-character-native-20261031-r189-v2/libsdcharacter-icu63.so',
           '-Dsaidroid.test.fdlibm.helper=/var/tmp/saidroid-fdlibm-native-20261031-r188-v4/libsdstrictmath-fdlibm.so',
           '-Dsaidroid.test.apk.native='+str(apk_native),'-Dsaidroid.test.hamcrest.owner=apk',
           '-Dsaidroid.bridge.library=' + str(component / 'lib/libsdbridge.so'),
           '-Dsaidroid.native.runtime=' + str(native / 'lib64'), '-Dsaidroid.native.root=' + str(native),
           '-Dsaidroid.test.host='+str(actualhost),'-Dsaidroid.test.javacore='+str(native_jni/'libjavacore.so'),'-Dsaidroid.test.art='+str(actualart),'-Dsaidroid.test.boot-images='+';'.join(str(boot_root/n)for n in active_images if n.endswith('.art')),'-Xhidden-api-policy:disabled', '-cp', str(work / 'empty.jar'),
           'Hamcrest235OriginalJUnitEventRunnerV2', str(apk), selection, str(sdk), str(listener), str(data / 'dexcache'),str(runner_apk)]
    started = time.monotonic()
    p = subprocess.run(cmd, env=run_env, preexec_fn=nobody, cwd=data, capture_output=True, text=True, timeout=1800)
    (work / (label+'-'+selection + '.stdout')).write_text(p.stdout)
    (work / (label+'-'+selection + '.stderr')).write_text(p.stderr)
    outcome = re.search(r'ORIGINAL_CORE_EVENT_VM\|tests=(\d+)\|failures=(\d+)\|assumptions=(\d+)\|ignored=(\d+)\|passed=(\d+)\|targetSdk=(\d+)', p.stdout)
    if not outcome:
        expected_abort=label=='before195'and'Test#testSocketpairNullFileDescriptor'in selection and 'JNI DETECTED ERROR IN APPLICATION: obj == null'in p.stderr and p.returncode!=0
        if not expected_abort:
            print(p.stdout[-1000:]+p.stderr[-5000:],flush=True)
            raise RuntimeError('Unexpected original native test/bootstrap termination')
        row=dict(runtime=label,selection=selection,expected_baseline_jni_abort=True,exit=p.returncode,passed=False,stdout_sha256=hashlib.sha256(p.stdout.encode()).hexdigest(),stderr_sha256=hashlib.sha256(p.stderr.encode()).hexdigest())
        results.append(row);print(json.dumps(row),flush=True);continue
    assert 'FINAL_NATIVE_COMPONENT_MAP=verified' in p.stdout
    assert 'OJ195_BOOT_IMAGES=verified|count=9'in p.stdout
    assert 'HAMCREST235_CLASS_OWNER=apk|actual_apk_loader=true|actual_everyItem=true'in p.stdout
    assert 'SDTLS=platform_jsse|provider=HarmonyJSSE|backend=matching-api29|legacy_providers=retained'in p.stderr
    assert 'PLATFORM_CORE_BOOTSTRAP|registered=104|uid=65534' in p.stdout
    assert 'APP_FILESYSTEM_POLICY=installed|uid=65534|backend=kernel-seccomp' in p.stderr
    assert 'SDBRIDGE registered=104 missing=0' in p.stderr and int(outcome[6]) == sdk
    events=[line.split('|',2)[1:]for line in p.stdout.splitlines()if line.startswith('OJ195_EVENT|')]
    row = dict(runtime=label,selection=selection,events=events, uid=65534, tests=int(outcome[1]), failures=int(outcome[2]),
               assumptions=int(outcome[3]), ignored=int(outcome[4]), real_passed=int(outcome[5]),
               exit=p.returncode, seconds=time.monotonic() - started,
               passed=p.returncode == 0 and int(outcome[1]) > 0 and int(outcome[2]) == 0,
               stdout_sha256=hashlib.sha256(p.stdout.encode()).hexdigest(),
               stderr_sha256=hashlib.sha256(p.stderr.encode()).hexdigest())
    results.append(row)
    print(json.dumps({k:v for k,v in row.items()if k!='events'}), flush=True)
    record=dict(scope='Fivewhole originalCertificateFactory/CRL classes paired263vs266 onlyzero-payloadPEM/noobject compatibility. Currentstrictnonemptyfooter/ASN1/Base64rejection retained. OriginalAPKJUnit/JNI104/SDK29UID65534matching9images; cores263/runtime260/nativeARTunchanged; noAPK/assertion/filter/heap/budget/clockchanges. NotfullAJUR/module/phoneacceptance',status='RUNNING',apk_sha256=inventory['apk_sha256'],runner_source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),actual_art_baseline_sha256=hashlib.sha256((component/'lib/libart.so').read_bytes()).hexdigest(),actual_art_candidate_sha256=hashlib.sha256(Path('/var/tmp/saidroid-art240-host-math-precision-v1/libart.so').read_bytes()).hexdigest(),actual_companion_sha256=hashlib.sha256(companion.read_bytes()).hexdigest(),actual_new_bouncycastle_sha256=hashlib.sha256((newencoded/'java/dex/art/bouncycastle-hostdex.jar').read_bytes()).hexdigest(),actual_old_bouncycastle_sha256=hashlib.sha256((component/'java/dex/art/bouncycastle-hostdex.jar').read_bytes()).hexdigest(),actual_new_core_libart_sha256=hashlib.sha256((newencoded/'java/dex/art/core-libart.jar').read_bytes()).hexdigest(),actual_new_core_oj_sha256=hashlib.sha256((newencoded/'java/dex/art/core-oj.jar').read_bytes()).hexdigest(),actual_new_encoded_manifest_sha256=hashlib.sha256((newencoded/'manifest.json').read_bytes()).hexdigest(),actual_new_boot_manifest_sha256=hashlib.sha256((newboot/'manifest.json').read_bytes()).hexdigest(),actual_core_oj_sha256=hashlib.sha256((component/'java/dex/art/core-oj.jar').read_bytes()).hexdigest(),actual_core_libart_sha256=hashlib.sha256((component/'java/dex/art/core-libart.jar').read_bytes()).hexdigest(),actual_runtime_sha256=hashlib.sha256((component/'lib/runtime.jar').read_bytes()).hexdigest(),actual_boot_manifest_sha256=hashlib.sha256((component/'share/build/boot-image-manifest.json').read_bytes()).hexdigest(),actual_javacore_sha256=hashlib.sha256((component/'lib/libjavacore.so').read_bytes()).hexdigest(),actual_native_host_sha256=hashlib.sha256(actualhost.read_bytes()).hexdigest(),actual_bridge_sha256=hashlib.sha256((component/'lib/libsdbridge.so').read_bytes()).hexdigest(),results=results)
    (base/'original-pem-empty266-selected-v1-progress.json').write_text(json.dumps(record,indent=2)+'\n')
record['status']='COMPLETE'
(base/'original-pem-empty266-selected-v1.json').write_text(json.dumps(record,indent=2)+'\n')
