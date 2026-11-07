#!/usr/bin/env python3
"""VM-only behavioral checks with real ART, fresh dex, and a compiler sentinel."""
from pathlib import Path
import hashlib
import json
import os
import subprocess

output = Path('/var/tmp/saidroid-next-jit-policy-20261025-r1/behavior-tests')
output.mkdir(mode=0o700)
art = Path('/tmp/art-build/art-standalone/out/host/linux-x86')
java = Path('/tmp/jdkfull/jdk-21.0.13+9')
runtime_root = output / 'android-root'
(runtime_root / 'bin').mkdir(parents=True)
for name in ('lib64', 'java', 'framework'):
    (runtime_root / name).symlink_to(art / name, target_is_directory=True)
sentinel = runtime_root / 'bin/dex2oat'
sentinel.write_text('#!/bin/sh\nprintf "%s\\n" "$@" >> "$JIT_POLICY_CALL_LOG"\nexit 1\n')
sentinel.chmod(0o700)
source = output / 'JitLoadCheck.java'
source.write_text('''public class JitLoadCheck {
 public static void main(String[] args) {
  long sum=0;for(int i=0;i<20000;i++)sum+=i;
  if(sum!=199990000L)throw new AssertionError("arithmetic changed");
  try{Integer.parseInt("invalid");throw new AssertionError("exception disappeared");}
  catch(NumberFormatException expected){}
  System.out.println("DEX_EXECUTION=PASS|sum="+sum);
 }
}''')
classes = output / 'classes'
classes.mkdir()
subprocess.run([str(java / 'bin/javac'), '--release', '8', '-d', str(classes), str(source)], check=True)
env = dict(os.environ, JAVA_HOME=str(java), PATH=str(java / 'bin') + ':' + os.environ['PATH'])
subprocess.run([str(art / 'bin/dx'), '--dex', '--output=' + str(output / 'original.dex'), str(classes)],
               check=True, env=env)
lib = art / 'lib64/libart.so'
before = hashlib.sha256(lib.read_bytes()).hexdigest()
results = []
for name, jit, valid in [('jit', True, True), ('aot', False, True), ('invalid-dex', True, False)]:
    dex = output / (name + '.dex')
    data = (output / 'original.dex').read_bytes()
    dex.write_bytes(data if valid else b'BAD!' + data[4:])
    calls = output / (name + '-compiler-calls.txt')
    run_env = dict(env, ANDROID_ROOT=str(runtime_root), ANDROID_DATA=str(output / ('data-' + name)),
                   JIT_POLICY_CALL_LOG=str(calls),
                   LD_PRELOAD='/var/tmp/saidroid-next-jit-policy-20261025-r1/libsaidroid-unwind-compat.so',
                   LD_LIBRARY_PATH=':'.join([str(art / 'lib64'), '/usr/local/lib',
                       '/tmp/art-build/local-prefix/usr/lib/aarch64-linux-gnu',
                       os.environ.get('LD_LIBRARY_PATH', '')]))
    Path(run_env['ANDROID_DATA']).mkdir()
    command = [str(art / 'bin/dalvikvm'), '-Xnoimage-dex2oat',
               '-Xusejit:' + ('true' if jit else 'false'), '-cp', str(dex), 'JitLoadCheck']
    result = subprocess.run(command, capture_output=True, timeout=120, env=run_env)
    (output / (name + '.stdout')).write_bytes(result.stdout)
    (output / (name + '.stderr')).write_bytes(result.stderr)
    lines = calls.read_text().splitlines() if calls.exists() else []
    app_compiles = lines.count('--dex-file=' + str(dex))
    executed = b'DEX_EXECUTION=PASS|sum=199990000' in result.stdout
    if valid:
        assert result.returncode == 0 and executed, (name, result.returncode, result.stderr[-1500:])
        assert app_compiles == (0 if jit else 1), (name, app_compiles)
    else:
        assert result.returncode != 0 and not executed, 'Malformed dex was accepted'
    results.append(dict(mode=name, exit=result.returncode, executed=executed,
                        app_compiler_invocations=app_compiles))
assert hashlib.sha256(lib.read_bytes()).hexdigest() == before
proof = dict(result='PASS', libart_sha256=before, cases=results)
(output / 'proof.json').write_text(json.dumps(proof, indent=2) + '\n')
print(json.dumps(proof, indent=2))
