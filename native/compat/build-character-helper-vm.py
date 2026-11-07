#!/usr/bin/env python3
"""Build the original Character native implementation against Android 10 ICU.

Keep libopenjdk's JNI registration and its other native implementations. Export
only its 23 existing Character entry points; the component loader can resolve
those entries to this library before loading the legacy libopenjdk.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import shlex
import subprocess


PHONE_OPENJDK_SHA256 = 'f59985a283b244f2e0001a246b3d33933b2f817c89ee1c652331ad198228ce8a'
SOURCE = 'libcore/ojluni/src/main/native/Character.cpp'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def symbols(path):
    return sorted(line.split()[-1] for line in subprocess.check_output(
        ['nm', '-D', '--defined-only', str(path)], text=True).splitlines() if line.split())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path)
    parser.add_argument('--source', type=Path, default=Path('/tmp/art-build/art-standalone'))
    parser.add_argument('--icu-prefix', type=Path, required=True)
    parser.add_argument('--icu-config-headers', type=Path, required=True)
    parser.add_argument('--baseline-openjdk', type=Path, required=True)
    args = parser.parse_args()
    os.umask(0o022)
    repo = Path(__file__).resolve().parents[2]
    art = args.source.resolve(strict=True)
    icu = args.icu_prefix.resolve(strict=True)
    icu_config = args.icu_config_headers.resolve(strict=True)
    baseline = args.baseline_openjdk.resolve(strict=True)
    output = args.output.absolute()
    assert not output.exists(), 'Use a new immutable output directory'
    assert digest(baseline) == PHONE_OPENJDK_SHA256, 'Unverified native baseline'
    assert (art / SOURCE).read_bytes() == (repo / 'third_party/art-standalone' / SOURCE).read_bytes()
    assert re.search(r'^#define U_ICU_VERSION "63\.2"$',
                     (icu / 'include/unicode/uvernum.h').read_text(), re.MULTILINE)
    assert (icu_config / 'uconfig_local.h').is_file()
    expected = [name for name in symbols(baseline)
                if re.fullmatch(r'_Z\d+Character_.*', name)]
    assert len(expected) == 23
    shared = art / 'out/host/linux-x86/lib64'
    before = {str(p): digest(p) for p in shared.glob('*.so*') if p.is_file()}
    env = dict(os.environ)
    env.setdefault('JAVA_HOME', '/tmp/jdkfull/jdk-21.0.13+9')
    env['PATH'] = env['JAVA_HOME'] + '/bin:' + env['PATH']
    dry = subprocess.run(['make', '-n', '-W', SOURCE,
                          'out/host/linux-x86/lib64/libopenjdk.so', '-j2'],
                         cwd=art, env=env, capture_output=True, text=True, timeout=60)
    assert dry.returncode == 0, dry.stdout + dry.stderr
    commands = [shlex.split(line) for line in dry.stdout.splitlines()
                if ' -c ' in line and line.endswith(SOURCE)]
    assert len(commands) == 1 and commands[0][0] == 'g++'
    output.mkdir(parents=True)
    (output / 'original-dry-run.log').write_text(dry.stdout + dry.stderr)
    command = commands[0]
    command[command.index('-o') + 1] = str(output / 'Character.o')
    command[command.index('-MF') + 1] = str(output / 'Character.d')
    command[1:1] = ['-I' + str(icu / 'include'), '-I' + str(icu_config),
                    '-ffunction-sections', '-fdata-sections']
    exports = output / 'exports.map'
    exports.write_text('{ global: _Z*Character_*; local: *; };\n')
    library = output / 'libsdcharacter-icu63.so'
    link = ['g++', '-shared', '-Wl,-soname,' + library.name, '-Wl,-z,defs',
            '-Wl,--gc-sections', '-Wl,--version-script=' + str(exports),
            '-o', str(library), str(output / 'Character.o'),
            '-L' + str(icu / 'lib'), '-Wl,-rpath-link=' + str(icu / 'lib'), '-licuuc', '-lm']
    with (output / 'build.log').open('x') as log:
        subprocess.run(command, cwd=art, stdout=log, stderr=subprocess.STDOUT,
                       check=True, timeout=120)
        subprocess.run(link, cwd=art, stdout=log, stderr=subprocess.STDOUT,
                       check=True, timeout=120)
    assert symbols(library) == expected
    dynamic = subprocess.check_output(['readelf', '-d', str(library)], text=True)
    needed = set(re.findall(r'\(NEEDED\).*\[([^]]+)\]', dynamic))
    assert 'libicuuc.so.63' in needed
    assert needed <= {'libicuuc.so.63', 'libc.so.6', 'libm.so.6', 'ld-linux-aarch64.so.1'}
    dependency_text = (output / 'Character.d').read_text().replace('\\\n', ' ')
    dependencies = {}
    for name in shlex.split(dependency_text.split(':', 1)[1]):
        path = Path(name)
        path = path if path.is_absolute() else art / path
        dependencies[str(path)] = digest(path)
    assert str(art / SOURCE) in dependencies
    assert before == {str(p): digest(p) for p in shared.glob('*.so*') if p.is_file()}
    assert (art / SOURCE).read_bytes() == (repo / 'third_party/art-standalone' / SOURCE).read_bytes()
    (output / 'compile-commands.json').write_text(json.dumps(
        dict(compile=command, link=link), indent=2) + '\n')
    (output / 'NOTICE').write_text((art / SOURCE).read_text().split('#include', 1)[0])
    record = dict(schema='saildroid-character-native-v1', api=29,
                  scope='Unchanged Character.cpp, Android10 ICU63, existing 23 native ABI entries; '
                        'original JNI registration and all other libopenjdk implementations retained',
                  file=library.name, sha256=digest(library), bytes=library.stat().st_size,
                  source=SOURCE, source_sha256=digest(art / SOURCE),
                  source_unmodified=True, baseline_openjdk_sha256=digest(baseline),
                  exported_symbols=expected, dynamic=dynamic, dependencies=dependencies,
                  icu_library_sha256=digest(icu / 'lib/libicuuc.so.63'),
                  builder_sha256=digest(Path(__file__)),
                  compile_commands_sha256=digest(output / 'compile-commands.json'),
                  notice_sha256=digest(output / 'NOTICE'),
                  original_jni_registration_unchanged=True, shared_runtime_unchanged=True)
    (output / 'manifest.json').write_text(json.dumps(record, indent=2) + '\n')
    print('CHARACTER_NATIVE=compiled|original_source=true|icu=63|existing_native_ABI=23'
          '|original_jni_registration=unchanged|shared_runtime=unchanged')


if __name__ == '__main__':
    main()
