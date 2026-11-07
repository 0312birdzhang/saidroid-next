"""Actualcrypto provider alias contract: sameeffectiveinventory/order/allmixedcaseDESede/ARC4/RC4operations; duplicateproperty only removed. VM only, originaltests untouched."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys

if '--inside' not in sys.argv:
    run = subprocess.run(['unshare', '--mount', '--', sys.executable,
                          str(Path(__file__).resolve()), '--inside'],
                         capture_output=True, text=True, timeout=240)
    print(run.stdout)
    print(run.stderr, file=sys.stderr)
    sys.exit(run.returncode)

subprocess.run(['mount', '--make-rprivate', '/'], check=True)
subprocess.run(['mount', '-t', 'tmpfs', '-o', 'mode=0755,size=4m,nr_inodes=128', 'tmpfs', '/home'], check=True)
Path('/home/art').mkdir(mode=0o755)
Path('/home/art').chmod(0o755)
lib = Path('/home/art/lib')
lib.mkdir(mode=0o755)
lib.chmod(0o755)
clone = Path('/var/tmp/saidroid-unprivileged182-runtime-20261031')
for directory in ['homeart', 'crypto', 'icu', 'artlib']:
    for file in (clone / directory).iterdir():
        if file.is_file() and not (lib / file.name).exists():
            (lib / file.name).symlink_to(file)
(lib / 'libopenjdk.so').unlink()
(lib / 'libopenjdk.so').symlink_to('/var/tmp/saidroid-actual-phone-openjdk-20261031/libopenjdk.so')
os.umask(0o022)
repo = Path('/media/psf/Home/WorkSpace/saidroid-next')
base = repo / 'build/evidence/cts-frame-repair-20261031'
source = repo / 'scripts/api29/tests/crypto-provider-alias'
work = Path('/var/tmp/saidroid-crypto-provider-alias277-own-v1')
assert not work.exists()
work.mkdir()
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
frozen=json.loads((base/'crypto-provider-alias277-own-frozen-inputs-v1.json').read_text());assert all(sha(repo/n)==h for n,h in frozen['sources'].items())and all(sha(base/n)==h for n,h in frozen['proofs'].items())
before = Path('/var/tmp/saidroid-pbe-api29274-v2-formal-vm-component/root')
after = Path('/var/tmp/saidroid-crypto-provider-alias277-prototype-v1/root')
for root in [before, after]:
    manifest = json.loads((root / 'install-manifest.json').read_text())
    for name, item in manifest['files'].items():
        assert sha(root / name) == item['sha256']
        assert stat.S_IMODE((root / name).stat().st_mode) == item['mode']
    assert {str(p.relative_to(root)): os.readlink(p) for p in root.rglob('*') if p.is_symlink()} == manifest['symlinks']
Path('/home/art/api29-root').symlink_to(before)
classes = work / 'classes'
classes.mkdir()
java = Path('/tmp/jdkfull/jdk-21.0.13+9/bin')
inputs = repo / 'build/codex-api29/inputs'
framework = inputs / 'android-all-10-robolectric-5803371.jar'
subprocess.run([str(java / 'javac'), '-source', '8', '-target', '8', '-nowarn',
                '-bootclasspath', '/var/tmp/saidroid-classpath-cache-lifecycle263-module-v3/core-oj-classes.jar:'
                '/var/tmp/saidroid-classpath-cache-lifecycle263-module-v3/core-libart-classes.jar:' + str(framework),
                '-d', str(classes), str(source / 'CryptoProviderAlias277Contract.java'),
                str(source / 'CryptoProviderAlias277Runner.java')], check=True)
jar = work / 'contract.jar'
subprocess.run([str(java / 'java'), '-cp', str(inputs / 'r8-8.3.37.jar'),
                'com.android.tools.r8.D8', '--release', '--min-api', '29', '--lib', str(framework),
                '--output', str(jar), *map(str, sorted(classes.rglob('*.class')))], check=True)
jar.chmod(0o444)
policy = work / 'app-policy-exec'
subprocess.run(['g++', '-std=c++17', '-O2', '-Wall', '-Wextra', '-Werror',
                str(repo / 'native/host/tests/app-filesystem-policy-exec.cpp'), '-o', str(policy)], check=True)
policy.chmod(0o555)


def ordinary():
    import resource
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    os.setgroups([])
    os.setgid(65534)
    os.setuid(65534)
    os.umask(0o077)


results = []
for label, root, sdk in [('before-29', before, 29), ('after-29', after, 29)]:
    data = work / label
    data.mkdir(mode=0o700)
    os.chown(data, 65534, 65534)
    cache = data / 'dalvik-cache'
    cache.mkdir(mode=0o700)
    os.chown(cache, 65534, 65534)
    Path('/home/art/api29-root').unlink()
    Path('/home/art/api29-root').symlink_to(root)
    runtime = json.loads((root / 'runtime.json').read_text())
    jars = [root / n for n in runtime['boot_jars']] + [root / 'lib/runtime.jar', jar]
    locations = ['/home/art/api29-root/' + n for n in runtime['boot_jars']] + ['/home/art/api29-root/lib/runtime.jar', str(jar)]
    environment = dict(PATH='/usr/bin:/bin', HOME=str(data), TMPDIR=str(data), LANG='C.UTF-8',
                       ANDROID_ROOT=str(root), ANDROID_RUNTIME_ROOT=str(root / 'apex/com.android.runtime.debug'),
                       ANDROID_TZDATA_ROOT=str(root / 'apex/com.android.tzdata'), ICU_DATA=str(root / 'usr/icu'),
                       ANDROID_DATA=str(data), SAILDROID_DATA_DIR=str(data), SD_BUILD_PROP=str(root / 'build.prop'),
                       BIONIC_TRANSLATION_CONFIG_DIR=str(root / 'linker-config'),
                       LD_LIBRARY_PATH=str(root / 'lib') + ':/home/art/lib',
                       LD_PRELOAD=':'.join(str(root / 'lib' / n) for n in [
                           'libsdmath-precision.so', 'libsdstrictmath-fdlibm.so', 'libsdcharacter-icu63.so',
                           'libsdhost29.so', 'libdl_bio.so.0']) + ':libresolv.so.2')
    command = [str(policy), str(root / 'libexec/dalvikvm-real'), '-XXlib:' + str(root / 'lib/libart.so'),
               '-Xnoimage-dex2oat', '-Ximage:' + str(root / 'system/framework/boot.art'),
               '-Xbootclasspath:' + ':'.join(map(str, jars)),
               '-Xbootclasspath-locations:' + ':'.join(locations),
               '-Xtarget-sdk-version:' + str(sdk), '-Xhidden-api-policy:enabled',
               '-Djava.library.path=' + str(root / 'lib') + ':' + str(root / 'android-libs') + ':/home/art/lib',
               'CryptoProviderAlias277Runner', str(sdk), str(label.startswith('before')).lower()]
    run = subprocess.run(command, env=environment, cwd=data, preexec_fn=ordinary,
                         capture_output=True, text=True, timeout=25)
    (work / (label + '.stdout')).write_text(run.stdout)
    (work / (label + '.stderr')).write_text(run.stderr)
    marker = next((line for line in run.stdout.splitlines() if line.startswith('ALIAS277_CONTRACT=PASS|')), None)
    record = dict(label=label, sdk=sdk, returncode=run.returncode, marker=marker,
                  command=command, stdout_sha256=hashlib.sha256(run.stdout.encode()).hexdigest(),
                  stderr_sha256=hashlib.sha256(run.stderr.encode()).hexdigest(),
                  component_manifest_sha256=sha(root / 'install-manifest.json'))
    results.append(record)
    print(json.dumps(record), flush=True)
    assert run.returncode == 0 and marker, run.stdout[-3000:] + run.stderr[-5000:]
    assert 'ALIAS277_BOOTSTRAP=ready|jni=104|ui=false' in run.stdout
before_stdout=(work/'before-29.stdout').read_text();after_stdout=(work/'after-29.stdout').read_text()
for prefix in ['ALIAS277_PROVIDER_ORDER=', 'ALIAS277_EFFECTIVE_SERVICE=']:
    assert [s for s in before_stdout.splitlines()if s.startswith(prefix)]==[s for s in after_stdout.splitlines()if s.startswith(prefix)]

record = dict(passed=True, scope=__doc__ + ' Before274 duplicated caseproperty, after277 unique; identical effectiveproviderorder/services andoperations, includingJKS preserved. Trusted VM-only runner sets each separate target SDK; no original test SDK changed.',
              results=results, source_sha256=sha(source / 'CryptoProviderAlias277Contract.java'),
              runner_source_sha256=sha(source / 'CryptoProviderAlias277Runner.java'),
              jar_sha256=sha(jar), product_source_meta_sha256=sha(repo / 'scripts/api29/crypto-provider-alias-compat/sources.json'),
              actual_nonroot=True, phone_executed=False, formal_module_acceptance=False)
out = base / 'crypto-provider-alias277-own-v1.json'
assert not out.exists()
out.write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record, indent=2))
