#!/usr/bin/env python3
"""Build the API28 ordinary-user Java CLI and its private bootstrap class."""
import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
for name in ('framework', 'r8', 'runtime-classes', 'output'):
    parser.add_argument('--'+name, type=Path, required=True)
parser.add_argument('--cxx', default='g++')
parser.add_argument('--classpath-separator', default=os.pathsep)
arguments = parser.parse_args()
repo = Path(__file__).resolve().parents[2]
source = repo/'native/commands/java-cli-headless'
output = arguments.output
assert not output.exists()
output.mkdir(parents=True)
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
assert sha(arguments.framework) == 'cf4aed5e458deb48ddc0ca92fc25156e6f478d9d5c1d948cdd1817a67ee11b32'
assert sha(arguments.r8) == '59753e70a74f918389cc87f1b7d66b5c0862932559167425708ded159e3de439'
classes = output/'classes'
classes.mkdir()
commands = [
    [arguments.cxx, '-std=c++17', '-O2', '-Wall', '-Wextra', '-Werror',
     '-o', str(output/'dalvikvm'), str(source/'dalvikvm.cpp')],
    ['javac', '--release', '8', '-nowarn', '-encoding', 'UTF-8', '-cp',
     str(arguments.framework)+arguments.classpath_separator+str(arguments.runtime_classes),
     '-d', str(classes), str(source/'SdJavaCommand.java')],
    ['java', '-cp', str(arguments.r8), 'com.android.tools.r8.D8', '--release',
     '--min-api', '28', '--lib', str(arguments.framework), '--output',
     str(output/'bootstrap-raw.jar'), str(classes/'SdJavaCommand.class')],
]
with (output/'build.log').open('x') as log:
    for command in commands:
        subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
elf = subprocess.check_output(['readelf', '-h', str(output/'dalvikvm')], text=True)
assert 'AArch64' in elf and 'ELF64' in elf
spec = importlib.util.spec_from_file_location('platform_encoder', Path(__file__).with_name('encode-platform-dex.py'))
encoder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(encoder)
flags = encoder.encode_jar(output/'bootstrap-raw.jar', [], output/'java-cli-bootstrap.jar')
assert flags['preserved'] == 0 and flags['private'] == flags['members']
record = {'schema': 'saildroid-api28-java-cli-v1', 'api': 28, 'commands': commands,
          'source_sha256': sha(source/'dalvikvm.cpp'),
          'bootstrap_source_sha256': sha(source/'SdJavaCommand.java'),
          'binary_sha256': sha(output/'dalvikvm'),
          'bootstrap_jar_sha256': sha(output/'java-cli-bootstrap.jar'), 'flags': flags}
(output/'manifest.json').write_text(json.dumps(record, indent=2)+'\n')
(output/'dalvikvm').chmod(0o755)
print('API28_JAVA_CLI_BUILT', record['bootstrap_jar_sha256'])
