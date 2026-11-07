#!/usr/bin/env python3
"""Build real fdlibm for ARM64 without changing the phone's libopenjdk.

The older Android host makefile selects __LITTLE_ENDIAN only for arm/x86,
omitting arm64. Keep its algorithms, IEEE mode and aliasing/precision flags;
select the actual compiler byte order and prohibit floating-point contraction.
Only ieee_* symbols are visible, so ordinary host libc math is unaffected.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path)
    parser.add_argument('--source', type=Path,
                        default=Path('/tmp/art-build/art-standalone/external/fdlibm'))
    args = parser.parse_args()
    # The VM build account may use umask 077. This new artifact must be
    # traversable/readable by the unprivileged runtime that will load it.
    os.umask(0o022)
    repo = Path(__file__).resolve().parents[2]
    baseline = repo / 'third_party/art-standalone/external/fdlibm'
    source = args.source.resolve(strict=True)
    assert not args.output.exists(), 'Use a new immutable output directory'
    macros = subprocess.check_output(['gcc', '-dM', '-E', '-'], input='', text=True)
    assert '#define __aarch64__ 1' in macros
    assert '#define __BYTE_ORDER__ __ORDER_LITTLE_ENDIAN__' in macros
    assert '#define __SIZEOF_DOUBLE__ 8' in macros and '#define __SIZEOF_INT__ 4' in macros
    makefile = (source / 'Android.mk').read_text()
    match = re.search(r'^src_files\s*:=\s*(.*?)(?:\n\s*\n)', makefile,
                      flags=re.MULTILINE | re.DOTALL)
    assert match is not None
    names = match[1].replace('\\\n', ' ').split()
    assert len(names) == len(set(names)) == 80
    assert all(re.fullmatch(r'[a-z0-9_]+\.c', name) for name in names)
    inputs = names + sorted(p.name for p in source.glob('*.h')) + ['Android.mk']
    hashes = {}
    for name in inputs:
        path = source / name
        assert path.is_file() and not path.is_symlink()
        assert digest(path) == digest(baseline / name), 'Unrecorded fdlibm source difference: ' + name
        hashes[name] = digest(path)
    args.output.mkdir(parents=True)
    snapshot = args.output / 'source'
    snapshot.mkdir()
    for name in inputs:
        shutil.copyfile(source / name, snapshot / name)
    objects = args.output / 'objects'
    objects.mkdir()
    flags = ['-std=gnu99', '-O2', '-fPIC', '-fno-strict-aliasing', '-ffloat-store',
             '-fno-fast-math', '-ffp-contract=off', '-D_IEEE_LIBM', '-D__LITTLE_ENDIAN',
             '-I' + str(snapshot)]
    commands = [['gcc', *flags, '-c', str(snapshot / name), '-o',
                 str(objects / (Path(name).stem + '.o'))] for name in names]
    exports = args.output / 'exports.map'
    exports.write_text('{ global: ieee_*; local: *; };\n')
    library = args.output / 'libsdstrictmath-fdlibm.so'
    link = ['gcc', '-shared', '-Wl,-soname,libsdstrictmath-fdlibm.so', '-Wl,-z,defs',
            '-Wl,--version-script=' + str(exports), '-o', str(library),
            *[str(objects / (Path(name).stem + '.o')) for name in sorted(names)], '-lm']
    with (args.output / 'build.log').open('x') as log:
        for command in commands:
            subprocess.run(command, check=True, stdout=log, stderr=subprocess.STDOUT, timeout=30)
        subprocess.run(link, check=True, stdout=log, stderr=subprocess.STDOUT, timeout=30)
    symbols = sorted(line.split()[-1] for line in subprocess.check_output(
        ['nm', '-D', '--defined-only', str(library)], text=True).splitlines() if line.split())
    assert len(symbols) == 50 and all(name.startswith('ieee_') for name in symbols)
    dynamic = subprocess.check_output(['readelf', '-d', str(library)], text=True)
    assert 'libsdstrictmath-fdlibm.so' in dynamic
    assert set(re.findall(r'\(NEEDED\).*\[([^]]+)\]', dynamic)) <= {
        'libm.so.6', 'libc.so.6', 'ld-linux-aarch64.so.1'}
    assert all(digest(source / name) == sha == digest(snapshot / name)
               for name, sha in hashes.items())
    (args.output / 'compile-commands.json').write_text(json.dumps(
        dict(compile=commands, link=link), indent=2) + '\n')
    (args.output / 'NOTICE').write_text((snapshot / 'fdlibm.h').read_text().split(
        '#ifdef __cplusplus', 1)[0])
    record = dict(schema='saildroid-fdlibm-native-v1', api=29,
                  scope='Actual fdlibm algorithms for StrictMath; correct ARM64 byte order, '
                        'IEEE mode, no floating-point contraction; private ieee_* symbols only',
                  file=library.name, sha256=digest(library), bytes=library.stat().st_size,
                  exported_symbols=symbols, sources=hashes, compiler_macros=macros,
                  flags=flags, compile_commands_sha256=digest(args.output / 'compile-commands.json'),
                  builder_sha256=digest(Path(__file__)),
                  export_script_sha256=digest(exports), dynamic=dynamic,
                  notice_sha256=digest(args.output / 'NOTICE'), original_sources_unchanged=True,
                  original_phone_openjdk_unchanged=True, host_libc_math_unchanged=True)
    (args.output / 'manifest.json').write_text(json.dumps(record, indent=2) + '\n')
    print('FDLIBM_NATIVE=compiled|actual_little_endian_arm64=true|private_ieee_exports=50'
          '|original_openjdk_unchanged=true|sha256=' + record['sha256'])


if __name__ == '__main__':
    main()
