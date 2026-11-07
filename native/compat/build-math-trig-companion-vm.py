#!/usr/bin/env python3
"""Build a private Math_sin/cos/tan entry over the verified unmodified fdlibm backend.

This DSO adds no ordinary libc math symbol. JNI/native registration and Java
declarations remain unchanged; actual ART intrinsic paths require the matching
isolated ART patch and separate execution checks before packaging.
"""
from pathlib import Path
import argparse, hashlib, json, os, re, shutil, subprocess
p = argparse.ArgumentParser(description=__doc__)
for n in ['component', 'output']: p.add_argument('--' + n, type=Path, required=True)
a = p.parse_args(); os.umask(0o022); r = Path(__file__).resolve().parents[2]
sha = lambda f: hashlib.sha256(f.read_bytes()).hexdigest()
assert not a.output.exists(); a.output.mkdir(parents=True)
macros = subprocess.check_output(['gcc', '-dM', '-E', '-'], input='', text=True)
assert '#define __aarch64__ 1' in macros and '#define __BYTE_ORDER__ __ORDER_LITTLE_ENDIAN__' in macros
manifest = json.loads((a.component / 'install-manifest.json').read_text())
backend = a.component / 'lib/libsdstrictmath-fdlibm.so'
assert sha(backend) == manifest['files']['lib/libsdstrictmath-fdlibm.so']['sha256']
source = r / 'native/compat/math-trig/MathTrig.c'; shutil.copyfile(source, a.output / source.name)
exports = a.output / 'exports.map'; exports.write_text('{ global: Math_sin; Math_cos; Math_tan; local: *; };\n')
library = a.output / 'libsdmath-trig.so'
command = ['gcc', '-std=gnu99', '-O2', '-fPIC', '-fno-fast-math', '-ffp-contract=off',
           '-Wall', '-Wextra', '-Werror', '-shared', '-Wl,-z,defs', '-Wl,-soname,libsdmath-trig.so',
           '-Wl,--version-script=' + str(exports), '-Wl,-rpath,$ORIGIN', '-o', str(library),
           str(a.output / source.name), '-L' + str(backend.parent), '-lsdstrictmath-fdlibm']
with (a.output / 'build.log').open('x') as log: subprocess.run(command, check=True, stdout=log, stderr=subprocess.STDOUT)
symbols = [l.split()[-1] for l in subprocess.check_output(['nm', '-D', '--defined-only', str(library)], text=True).splitlines() if l.split()]
assert sorted(symbols) == ['Math_cos','Math_sin','Math_tan']
dynamic = subprocess.check_output(['readelf', '-d', str(library)], text=True)
assert set(re.findall(r'\(NEEDED\).*\[([^]]+)\]', dynamic)) <= {'libsdstrictmath-fdlibm.so', 'libc.so.6'}
assert 'libsdstrictmath-fdlibm.so' in dynamic and '$ORIGIN' in dynamic
assert sha(source) == sha(a.output / source.name) and sha(backend) == manifest['files']['lib/libsdstrictmath-fdlibm.so']['sha256']
record = dict(schema='saildroid-math-trig-companion-v1', scope=__doc__, passed=True,
              builder_sha256=sha(Path(__file__)), source_sha256=sha(source), backend_sha256=sha(backend),
              library_sha256=sha(library), defined_symbols=symbols, dynamic=dynamic, command=command,
              host_libc_math_unchanged=True, original_phone_libopenjdk_unchanged=True, phone_staged=False)
(a.output / 'manifest.json').write_text(json.dumps(record, indent=2) + '\n')
print('MATH_TAN_COMPANION=built|only_exports=Math_sin,Math_cos,Math_tan|ordinary_libc_symbols=unchanged|phone_staged=false')
