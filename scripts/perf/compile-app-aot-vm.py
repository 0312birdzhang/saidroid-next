#!/usr/bin/env python3
"""Build an app cache from accepted component inputs; never contact a device.

The reference is a successful, reviewed dex2oat recipe/result, not an arbitrary
command to execute. Only the options assembled below are passed to dex2oat.
An app record supplies the installed logical APK location and accepted APK hash.
The cache is a candidate until ART accepts it on the target and real UI passes.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import resource
import signal
import subprocess
import time
import zipfile


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def option(command, prefix):
    values = [v[len(prefix):] for v in command if v.startswith(prefix)]
    require(len(values) == 1, 'Expected exactly one reference option ' + prefix)
    return values[0]


def input_files(reference, component, root):
    require(reference.get('passed') is True, 'Reference build was not accepted')
    source_records = reference['sources']
    require(source_records and 'lib/runtime.jar' in source_records, 'Missing extended runtime input')
    files = {}
    for relative, source in source_records.items():
        p = PurePosixPath(relative)
        require(not p.is_absolute() and '..' not in p.parts, 'Input path escapes component')
        expected = component['files'][relative]
        require(source['sha256'] == expected['sha256'], 'Reference/component mismatch: ' + relative)
        path = root / relative
        require(path.is_file(), 'Missing input: ' + str(path))
        require(digest(path) == expected['sha256'], 'Input hash mismatch: ' + relative)
        require(path.stat().st_size == expected['size'], 'Input size mismatch: ' + relative)
        files[relative] = dict(path=str(path), resolved=str(path.resolve()),
                               sha256=expected['sha256'], bytes=expected['size'])
    for relative, target in component.get('symlinks', {}).items():
        p = root / relative
        require(p.is_symlink() and os.readlink(p) == target, 'Component link mismatch: ' + relative)
    return files


def dependencies(compiler, env):
    check = subprocess.run(['ldd', str(compiler)], env=env, capture_output=True,
                           text=True, timeout=30, check=True)
    require('not found' not in check.stdout, 'Compiler dependency unresolved')
    paths = {str(compiler.resolve())}
    for line in check.stdout.splitlines():
        for token in line.split():
            if token.startswith('/') and Path(token).is_file():
                paths.add(str(Path(token).resolve()))
    return check.stdout, {p: dict(sha256=digest(p), bytes=Path(p).stat().st_size)
                          for p in sorted(paths)}


def shared_context(args, app, component):
    manifest = getattr(args, 'shared_library_context', None)
    if manifest is None:
        require(args.class_loader_context == 'PCL[]',
                'Non-empty context requires a pinned shared-library context manifest')
        return 'PCL[]', 'PCL[]', []
    context = load(manifest)
    require(context.get('schema') == 'saildroid-shared-library-context-v1', 'Invalid context schema')
    require(context.get('package') == app['package'] and context.get('apk_sha256') == app['apkSha256'],
            'Context belongs to another APK')
    require(context.get('component_manifest_sha256') == digest(args.component_manifest),
            'Context belongs to another component')
    target = context['target_root']
    require(re.fullmatch(r'/(?:home/art|opt/saildroid)/releases/[a-z0-9][a-z0-9.-]+', target),
            'Shared library target is not a versioned release')
    rows = context['libraries']
    require(isinstance(rows, list) and 0 < len(rows) <= 32, 'Invalid shared library count')
    sources, stored, identities = [], [], []
    for row in rows:
        relative = row['relative']
        require(re.fullmatch(r'system/framework/[A-Za-z0-9_.-]+\.jar', relative),
                'Shared library is outside the component framework directory')
        expected = component['files'][relative]
        source = Path(row['source']).absolute()
        require(not any(c in str(source) for c in ':;[]{}*'), 'Unsafe source context path')
        require(source.is_file() and digest(source) == expected['sha256'] == row['sha256'] and
                source.stat().st_size == expected['size'] == row['bytes'], 'Shared library bytes differ')
        with zipfile.ZipFile(source) as archive:
            require('classes.dex' in archive.namelist(), 'Shared library contains no DEX')
            dex = [dict(name=i.filename, bytes=i.file_size, crc32=i.CRC)
                   for i in archive.infolist() if i.filename.endswith('.dex')]
        sources.append(str(source)); stored.append(target + '/' + relative)
        identities.append(dict(relative=relative, stored_path=stored[-1], source=str(source),
                               sha256=expected['sha256'], bytes=expected['size'], dex=dex))
    require(len(set(stored)) == len(stored), 'Duplicate shared library context entry')
    actual = 'PCL[' + ':'.join(sources) + ']'
    intended = 'PCL[' + ':'.join(stored) + ']'
    require(args.class_loader_context == context['stored_context'] == intended,
            'Explicit context differs from pinned ordered libraries')
    return actual, intended, identities


def verify_stored_context(oat, intended, libraries):
    # ART's OAT key/value header precedes code. Check actual emitted metadata,
    # not just compiler options; no checksum-validation flags are disabled.
    with Path(oat).open('rb') as stream:
        header = stream.read(1024 * 1024)
    marker = b'\0classpath\0'
    require(header.count(marker) == 1, 'Missing or ambiguous OAT context header')
    value = header.split(marker, 1)[1].split(b'\0', 1)[0].decode('ascii')
    require(re.sub(r'\*[0-9]+', '', value) == intended, 'Emitted OAT context differs')
    for library in libraries:
        if len(library['dex']) == 1:
            require(library['stored_path'] + '*' + str(library['dex'][0]['crc32']) in value,
                    'Emitted OAT shared library checksum differs')
    return value


def compile_cache(args):
    require(platform.system() == 'Linux', 'Run in the Linux build VM')
    require(platform.machine() == 'aarch64', 'This accepted native compiler requires aarch64 VM')
    require(not args.output.exists(), 'Output already exists; use a new version directory')
    reference = load(args.reference)
    overlay = load(args.component_manifest)
    component = overlay.get('install_manifest', overlay)
    runtime = load(args.runtime_config)
    require(digest(args.runtime_config) == component['files']['runtime.json']['sha256'],
            'Runtime configuration differs from component manifest')
    record_source = load(args.app_record)
    app = record_source.get('app', record_source)
    require(re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z0-9_]+)+', app['package']),
            'Invalid package identity')
    require(re.fullmatch(r'[0-9a-f]{64}', app['apkSha256']), 'Missing accepted APK hash')
    location = PurePosixPath(app['apk'])
    require(location.is_absolute() and '..' not in location.parts and location.name == 'base.apk',
            'Installed APK location must be an absolute base.apk path')
    require(str(location).startswith('/home/art/apps/' + app['package'] + '/versions/'),
            'Installed APK is outside its versioned package directory')
    require(not app.get('splitNames') and not app.get('splitSourceDirs'),
            'Split APK compilation requires a complete multi-DEX-location implementation')
    actual_context, stored_context, shared_libraries = shared_context(args, app, component)
    require(app.get('signers'), 'Expected a verified installer record with signer identities')
    require(digest(args.apk) == app['apkSha256'], 'APK hash differs from verified installed record')
    with zipfile.ZipFile(args.apk) as archive:
        dex = [dict(name=i.filename, bytes=i.file_size, crc32=i.CRC,
                    compressed_bytes=i.compress_size) for i in archive.infolist()
               if re.fullmatch(r'classes(?:[2-9]|[1-9][0-9]+)?\.dex', i.filename)]
    require(dex, 'APK has no base DEX to compile')
    ref_env = reference['environment']
    reference_root = Path(ref_env['ANDROID_ROOT'])
    root = Path(getattr(args, 'input_root', None) or reference_root)
    files = input_files(reference, component, root)
    names = runtime['boot_jars'] + ['lib/runtime.jar']
    require(all(n in files for n in names), 'Boot input absent from accepted reference')
    command = reference['command']
    boot = ':'.join(str(root / n) for n in names)
    locations = ':'.join('/home/art/api29-root/' + n for n in names)
    reference_boot = ':'.join(str(reference_root / n) for n in names)
    require(option(command, '-Xbootclasspath:') == reference_boot, 'Reference boot order/path differs')
    require(option(command, '-Xbootclasspath-locations:') == locations, 'Logical boot locations differ')
    image = str(root / runtime['boot_image']['path'])
    require(option(command, '--boot-image=') == str(reference_root / runtime['boot_image']['path']),
            'Boot image selection differs')
    # ART accepts a logical framework/boot.art base and finds its arm64 siblings.
    # Validate all image/OAT/VDEX bytes, including the extended core-libart image.
    images = [n for n in files if n.startswith('system/framework/') and
              n.endswith(('.art', '.oat', '.vdex'))]
    require(images and all(n in files for n in component['files']
                          if n.startswith('system/framework/') and
                          n.endswith(('.art', '.oat', '.vdex'))), 'Incomplete boot image closure')
    compiler = Path(command[0])
    require(digest(compiler) == reference['compiler_sha256'], 'Compiler differs from accepted reference')
    # Strip inherited injection/profiling overrides; retain the reviewed library search path.
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(('LD_', 'SAILDROID_', 'SD_')) and
           k not in ('JAVA_TOOL_OPTIONS', '_JAVA_OPTIONS', 'CLASSPATH')}
    args.output.mkdir(parents=True)
    (args.output / 'data').mkdir()
    env.update(LD_LIBRARY_PATH=ref_env['LD_LIBRARY_PATH'], ANDROID_ROOT=str(root),
               ANDROID_DATA=str(args.output / 'data'), SD_BUILD_PROP=str(root / 'build.prop'),
               LC_ALL='C')
    ldd, closure = dependencies(compiler, env)
    cmd = [str(compiler), '--host', '--instruction-set=arm64',
           '--compiler-filter=' + args.filter, '-j' + str(args.jobs),
           '--runtime-arg', '-Xmx1536m', '--boot-image=' + image,
           '--runtime-arg', '-Xbootclasspath:' + boot,
           '--runtime-arg', '-Xbootclasspath-locations:' + locations,
           '--dex-file=' + str(args.apk), '--dex-location=' + str(location),
           '--oat-file=' + str(args.output / 'base.odex'),
           '--class-loader-context=' + actual_context,
           '--stored-class-loader-context=' + stored_context]
    if app.get('debuggable'):
        cmd.append('--debuggable')
    key_input = dict(schema='saildroid-app-aot-key-v1', package=app['package'],
                     apk_sha256=app['apkSha256'], dex_location=str(location),
                     boot_order=names, logical_boot_locations=locations,
                     inputs={n: v['sha256'] for n, v in files.items()},
                     compiler_sha256=reference['compiler_sha256'],
                     compiler_dependencies=closure, isa='arm64', compiler_filter=args.filter,
                     class_loader_context=args.class_loader_context,
                     shared_libraries=shared_libraries,
                     debuggable=bool(app.get('debuggable')))
    key = hashlib.sha256(json.dumps(key_input, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    recipe = dict(schema='saildroid-app-aot-build-v1', cache_key=key, identity=key_input,
                  command=cmd, reference=str(args.reference), reference_sha256=digest(args.reference),
                  component_manifest=str(args.component_manifest),
                  component_manifest_sha256=digest(args.component_manifest),
                  runtime_config_sha256=digest(args.runtime_config),
                  app_record_sha256=digest(args.app_record), wrapper_sha256=digest(__file__),
                  environment={k: env[k] for k in ('LD_LIBRARY_PATH', 'ANDROID_ROOT', 'ANDROID_DATA', 'SD_BUILD_PROP')},
                  sources=files, dex_entries=dex, compiler_ldd=ldd,
                  compiler_closure_scope='ELF DT_NEEDED closure; dlopen-only plugins not guaranteed',
                  started_epoch=time.time(), target_acceptance='not-tested',
                  install_preconditions=dict(package=app['package'], apk=str(location),
                      apk_sha256=app['apkSha256'], signers=app['signers'],
                      runtime_sha256=files['lib/runtime.jar']['sha256'],
                      runtime_inputs={n: v['sha256'] for n, v in files.items()},
                      shared_library_context=stored_context,
                      shared_libraries=shared_libraries,
                      no_owned_runtime_processes=True, preserve_previous_cache=True,
                      atomically_switch_complete_directory=True, verify_target_art_acceptance=True))
    write(args.output / 'recipe.json', recipe)
    print('APP_AOT=validated|package=' + app['package'] + '|filter=' + args.filter + '|key=' + key, flush=True)
    started = time.monotonic()
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    result = dict(recipe, passed=False)
    child = None
    try:
        with (args.output / 'compile.log').open('wb', buffering=0) as stream:
            child = subprocess.Popen(cmd, env=env, stdout=stream, stderr=subprocess.STDOUT,
                                     start_new_session=True)
            try:
                rc = child.wait(timeout=args.timeout)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
                raise TimeoutError('Compiler exceeded bounded timeout')
        result['returncode'] = rc
        require(rc == 0, 'dex2oat failed; inspect compile.log')
        result['files'] = {n: dict(sha256=digest(args.output / n), bytes=(args.output / n).stat().st_size)
                           for n in ('base.odex', 'base.vdex')}
        require(all(v['bytes'] > 0 for v in result['files'].values()), 'Empty cache output')
        result['emitted_class_loader_context'] = verify_stored_context(
            args.output / 'base.odex', stored_context, shared_libraries)
        require(digest(args.apk) == app['apkSha256'], 'APK changed during compilation')
        input_files(reference, component, root)
        require(shared_context(args, app, component) == (actual_context, stored_context, shared_libraries),
                'Shared context changed during compilation')
        require(digest(compiler) == reference['compiler_sha256'], 'Compiler changed during compilation')
        require(all(digest(p) == v['sha256'] for p, v in closure.items()),
                'Compiler dependency changed during compilation')
        result['passed'] = True
        write(args.output / 'saidroid-cache-manifest.json',
              dict(schema='saidroid-app-aot-cache-v2', cache_key=key,
                   identity=key_input, files=result['files'],
                   install_preconditions=recipe['install_preconditions'],
                   target_acceptance='not-tested'))
    except BaseException as error:
        if child and child.poll() is None:
            os.killpg(child.pid, signal.SIGKILL)
            child.wait()
        result['error'] = repr(error)
        raise
    finally:
        after = resource.getrusage(resource.RUSAGE_CHILDREN)
        result.update(seconds=time.monotonic() - started,
                      resource=dict(user_cpu_seconds=after.ru_utime-before.ru_utime,
                                    system_cpu_seconds=after.ru_stime-before.ru_stime,
                                    child_max_rss_kib=after.ru_maxrss,
                                    minor_faults=after.ru_minflt-before.ru_minflt,
                                    major_faults=after.ru_majflt-before.ru_majflt),
                      finished_epoch=time.time())
        write(args.output / 'result.json', result)
    print('APP_AOT=compiled|' + json.dumps({k: result[k] for k in
          ('passed', 'cache_key', 'seconds', 'resource', 'files')}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ('reference', 'component-manifest', 'runtime-config', 'app-record', 'apk', 'output'):
        parser.add_argument('--' + flag, type=lambda v: Path(v).absolute(), required=True)
    parser.add_argument('--class-loader-context', required=True,
                        help='Explicitly confirmed PCL context; non-empty contexts require a manifest')
    parser.add_argument('--shared-library-context', type=lambda v: Path(v).absolute(),
                        help='Pinned ordered component JAR inputs and actual target release paths')
    parser.add_argument('--input-root', type=lambda v: Path(v).absolute(),
                        help='Byte-verified final payload boot inputs; compiler provenance still uses the reference')
    parser.add_argument('--filter', choices=('quicken', 'speed'), default='quicken')
    parser.add_argument('--jobs', type=int, choices=range(1, 9), default=4)
    parser.add_argument('--timeout', type=int, default=2400)
    args = parser.parse_args()
    require(0 < args.timeout <= 7200, 'Timeout must be positive and at most two hours')
    compile_cache(args)


if __name__ == '__main__':
    main()
