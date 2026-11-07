"""Reconstruct measured media metadata from retained original-test evidence.

Generation and validation are host-only. Neither function changes the phone,
installs XML, or turns a calibration failure into a passing test.
"""
from pathlib import Path
import collections
import importlib.util
import json
import math
import types

_spec = importlib.util.spec_from_file_location(
    'media_measurements', Path(__file__).with_name('media-performance-profile.py'))
measurements = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(measurements)
digest = measurements.digest
REPO = Path(__file__).resolve().parents[2]
ALIASES = ('/Users/zerox/WorkSpace/saidroid-next',
           '/media/psf/Home/WorkSpace/saidroid-next')
CONFIG_SHA = '498f11cf646dc88fef773017e887dbd3881852d0a244cbe2da970d0745dfd184'
IDENTITY_KEYS = ('boot', 'private_root', 'private', 'host_encoder', 'host_performance_xml')


def evidence_path(value):
    """Resolve the same shared evidence on macOS and its build VM."""
    path = Path(value)
    if not path.is_absolute():
        path = REPO / path
    else:
        for alias in ALIASES:
            try:
                path = REPO / path.relative_to(alias)
                break
            except ValueError:
                continue
    path = path.resolve(strict=True)
    path.relative_to(REPO)
    return path


def group_key(point):
    return (point['codec'], point['mime'], point['width'], point['height'])


def xml_for(points, source):
    generate, ported = measurements.original_generator(source)
    Size = collections.namedtuple('Size', 'width height')
    Size.__str__ = lambda self: '%dx%d' % self
    data = {}
    for point in points:
        assert math.isfinite(point['fps']) and point['fps'] > 0
        codec = point['codec']
        key = (False, codec.lower().startswith('omx.google.'), point['mime'], codec)
        sizes = data.setdefault(key, {})
        sizes.setdefault(Size(point['width'], point['height']), []).append(point['fps'])
    assert data
    return '\n'.join(generate(data, types.SimpleNamespace(ignore=False, dbg=False))) + '\n', ported


def validate_profile(profile, source):
    profile = Path(profile)
    report = json.loads((profile / 'provenance.json').read_text())
    points = json.loads((profile / 'samples.json').read_text())
    assert report['status'] == 'GENERATED_NOT_INSTALLED'
    assert report['source_sha256'] == measurements.SOURCE_SHA
    assert report['required_rounds'] == 20 and report['actual_rounds'] == len(points)
    assert report['independent_holdout_required'] is True
    assert all(p['runtime'] == report['runtime'] for p in points)
    groups = collections.Counter(group_key(p) for p in points)
    assert groups and min(groups.values()) >= 20, 'Each codec/size requires 20 real rounds'
    assert len({(p['run_id'], p['round']) for p in points}) == len(points)
    assert len({(p['source_log_sha256'], p['round']) for p in points}) == len(points), 'Reused log bytes'
    expected_xml, ported = xml_for(points, source)
    assert (profile / 'aosp-pure-functions-python3.py').read_text() == ported
    xml = profile / 'media_codecs_performance.xml'
    assert xml.read_text() == expected_xml and digest(xml) == report['xml_sha256']
    identity = report['implementation_identity']
    assert identity['private_root'] == report['runtime'] and identity['host_codec_processes']
    assert set(identity['private']) == {'libmedia_jni.so', 'libstagefright.so', 'libmediandk.so'}
    assert identity['host_encoder']['path'] == '/system/lib/vndk-28/libstagefright_soft_vpxenc.so'
    assert all(p['mapped_codec'] == identity['host_encoder']['canonical']
               for p in identity['host_codec_processes'])
    identity_evidence = report['implementation_identity_evidence']
    assert len(identity_evidence) >= 2, 'During and after identity records required'
    for name, sha in identity_evidence.items():
        file = evidence_path(name)
        assert digest(file) == sha
        recorded = json.loads(file.read_text())
        assert all(recorded[k] == identity[k] for k in IDENTITY_KEYS)

    # Reparse retained log bytes, request, result and actual original callbacks.
    # Comparing floating-point FPS alone would accept invented or duplicated data.
    sources = {}
    selected = {}
    for point in points:
        log = evidence_path(point['source_log'])
        key = (log, group_key(point))
        if key not in selected:
            codec, mime, width, height = key[1]
            assert codec in ('OMX.google.vp8.encoder', 'OMX.google.vp9.encoder')
            assert mime == 'video/x-vnd.on2.' + codec.split('.')[2]
            run = log.parent
            plan_file = run.parent / 'plan.json'
            if not plan_file.is_file():
                plan_file = run.parent / 'inputs/plan.json'
            plan = json.loads(plan_file.read_text())
            result_file = run / 'run-result.json'
            result = json.loads(result_file.read_text())
            assert result['status'] == 'COMPLETED'
            assert result['boot'] == identity['boot'] == plan['expected_boot']
            assert result['runtime'] == report['runtime'] and result['run'] == plan['label']
            assert plan['official_config_sha256'] == CONFIG_SHA
            assert plan['hidden_api_checks'] is True
            method = 'test%sGoog0Perf%04dx%04d' % (codec.split('.')[2].capitalize(), width, height)
            assert plan['arguments']['class'] == 'android.video.cts.VideoEncoderDecoderTest#' + method
            events_file = run / 'instrumentation-events.jsonl'
            events = [json.loads(line) for line in events_file.read_text().splitlines()]
            tests = [e for e in events if e.get('event') == 'status' and e.get('bundle', {}).get('test')]
            assert len(tests) == 2 and tests[0]['code'] == 1 and tests[1]['code'] in (0, -2)
            assert all(e['bundle']['test'] == method and e['bundle']['class'] ==
                       'android.video.cts.VideoEncoderDecoderTest' for e in tests)
            if tests[1]['code'] == -2:
                message = tests[1]['bundle']['stack'].splitlines()[0]
                assert any(message.startswith('junit.framework.AssertionFailedError: ' + prefix +
                                             codec + ' ' + mime + ' ' + str(width) + 'x' + str(height))
                           for prefix in ('Failed to get achievable frame rates for ',
                                          'Expected achievable frame rates for ')), 'Unrelated test failure'
            assert result['instrumentation']['code'] == -1
            assert result['instrumentation']['run_id'] == plan['label']
            parsed = measurements.collect(run, codec, width, height, report['runtime'])
            assert {p['round'] for p in parsed} == {0, 1}, 'Both original measurement rounds required'
            selected[key] = {p['round']: p for p in parsed}
            sources[str(log.relative_to(REPO))] = dict(
                log_sha256=digest(log), plan_sha256=digest(plan_file),
                result_sha256=digest(result_file), events_sha256=digest(events_file),
                original_test_failed=tests[1]['code'] == -2)
        original = selected[key][point['round']]
        assert set(point) == set(original)
        assert all(point[k] == original[k] for k in point if k != 'source_log'), 'Measurement differs from original log/request/result'
    for (log, group), rounds in selected.items():
        included = {p['round'] for p in points
                    if evidence_path(p['source_log']) == log and group_key(p) == group}
        assert included == set(rounds), 'Partial original round selection'
    if 'groups' in report:
        assert report['groups'] == [dict(codec=k[0], mime=k[1], width=k[2], height=k[3], rounds=n)
                                    for k, n in sorted(groups.items())]
    if 'original_run_evidence' in report:
        assert report['original_run_evidence'] == sources
    if 'input_profiles' in report:
        for name, files in report['input_profiles'].items():
            directory = evidence_path(name)
            assert set(files) == {'samples.json', 'provenance.json',
                                  'aosp-pure-functions-python3.py', 'media_codecs_performance.xml'}
            assert all(digest(directory / name) == sha for name, sha in files.items())
    return dict(report=report, points=points, groups=groups, sources=sources,
                profile_sha256={name: digest(profile / name) for name in
                                ('samples.json', 'provenance.json', 'aosp-pure-functions-python3.py',
                                 'media_codecs_performance.xml')})


def merge_profiles(profiles, source, output):
    """Combine already measured groups, enforcing the minimum separately."""
    profiles = list(map(Path, profiles))
    output = Path(output)
    assert profiles and not output.exists()
    validated = [validate_profile(profile, source) for profile in profiles]
    first = validated[0]['report']
    points = []
    identities = {}
    sources = {}
    inputs = {}
    for profile, value in zip(profiles, validated):
        report = value['report']
        assert all(report['implementation_identity'][k] == first['implementation_identity'][k]
                   for k in IDENTITY_KEYS), 'Mixed boot, root or media implementation'
        assert not set(value['groups']) & {group_key(p) for p in points}, 'Duplicate profile group'
        points.extend(value['points'])
        identities.update(report['implementation_identity_evidence'])
        sources.update(value['sources'])
        inputs[str(profile.resolve())] = value['profile_sha256']
    xml, ported = xml_for(points, source)
    report = {k: v for k, v in first.items() if k not in ('xml_sha256', 'actual_rounds')}
    report.update(actual_rounds=len(points), implementation_identity_evidence=identities,
                  input_profiles=inputs, original_run_evidence=sources,
                  groups=[dict(codec=k[0], mime=k[1], width=k[2], height=k[3], rounds=n)
                          for k, n in sorted(collections.Counter(group_key(p) for p in points).items())])
    output.mkdir(parents=True)
    (output / 'samples.json').write_text(json.dumps(points, indent=2) + '\n')
    (output / 'aosp-pure-functions-python3.py').write_text(ported)
    (output / 'media_codecs_performance.xml').write_text(xml)
    report['xml_sha256'] = digest(output / 'media_codecs_performance.xml')
    (output / 'provenance.json').write_text(json.dumps(report, indent=2) + '\n')
    validate_profile(output, source)
    return report
