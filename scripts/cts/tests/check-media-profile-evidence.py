#!/usr/bin/env python3
"""Exercise provenance rejection against retained real calibration evidence."""
from pathlib import Path
import argparse
import copy
import hashlib
import json
import shutil
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from media_profile_validation import REPO, digest, merge_profiles, validate_profile, xml_for

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('profile', type=Path)
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
assert not args.output.exists()
original = validate_profile(args.profile, args.source)
cases = []
with tempfile.TemporaryDirectory(prefix='media-profile-contract-', dir=REPO / 'build') as temporary:
    temporary = Path(temporary)
    merged = temporary / 'merged'
    merge_profiles([args.profile], args.source, merged)
    assert (merged / 'media_codecs_performance.xml').read_bytes() == (args.profile / 'media_codecs_performance.xml').read_bytes()
    validate_profile(merged, args.source)
    cases.append('original_20_actual_rounds_and_single_group_merge')

    def reject(name, change, regenerate=False):
        folder = temporary / name
        shutil.copytree(args.profile, folder)
        points = json.loads((folder / 'samples.json').read_text())
        report = json.loads((folder / 'provenance.json').read_text())
        change(points, report, folder)
        report['actual_rounds'] = len(points)
        (folder / 'samples.json').write_text(json.dumps(points))
        if regenerate:
            xml, _ = xml_for(points, args.source)
            (folder / 'media_codecs_performance.xml').write_text(xml)
            report['xml_sha256'] = digest(folder / 'media_codecs_performance.xml')
        (folder / 'provenance.json').write_text(json.dumps(report))
        try:
            validate_profile(folder, args.source)
        except (AssertionError, ValueError, KeyError, FileNotFoundError):
            cases.append(name)
        else:
            raise AssertionError('Accepted tampered profile: ' + name)

    reject('nineteen_samples', lambda p, r, f: p.pop())
    reject('reused_measurement', lambda p, r, f: p.__setitem__(1, copy.deepcopy(p[0])))
    reject('relabelled_identical_log', lambda p, r, f: p[1].update(round=0, run_id='another-name'))
    reject('invented_fps_with_recomputed_xml', lambda p, r, f: p[0].update(fps=p[0]['fps'] * 2), True)
    reject('invented_latency', lambda p, r, f: p[0].update(p95_us=p[0]['p95_us'] + 1))
    reject('wrong_source_line', lambda p, r, f: p[0].update(source_line=p[0]['source_line'] + 1))
    reject('unrelated_request', lambda p, r, f: p[0].update(request_sha256='0' * 64))
    reject('wrong_result', lambda p, r, f: p[0].update(result_sha256='0' * 64))
    reject('wrong_log', lambda p, r, f: p[0].update(source_log_sha256='0' * 64))
    reject('underpopulated_other_size', lambda p, r, f: p[-1].update(width=640, height=360))
    reject('mixed_runtime', lambda p, r, f: p[-1].update(runtime='/home/art/releases/api29-r184-native-candidate'))
    reject('mixed_boot', lambda p, r, f: r['implementation_identity'].update(boot='00000000-0000-0000-0000-000000000000'))
    reject('wrong_native_library', lambda p, r, f: r['implementation_identity']['host_encoder'].update(sha256='0' * 64))
    reject('no_identity_mapping', lambda p, r, f: r['implementation_identity'].update(host_codec_processes=[]))
    reject('wrong_original_tool', lambda p, r, f: r.update(source_sha256='0' * 64))
    reject('altered_python_port', lambda p, r, f: (f / 'aosp-pure-functions-python3.py').write_text('pass\n'))
    reject('no_holdout_required', lambda p, r, f: r.update(independent_holdout_required=False))
    reject('forged_xml_even_with_new_hash', lambda p, r, f: (
        (f / 'media_codecs_performance.xml').write_text('<MediaCodecs/>\n'),
        r.update(xml_sha256=digest(f / 'media_codecs_performance.xml'))))
    reject('outside_repository_evidence', lambda p, r, f: p[0].update(source_log='/etc/hosts'))
    try:
        merge_profiles([args.profile, args.profile], args.source, temporary / 'duplicate-groups')
    except AssertionError:
        cases.append('duplicate_group_merge')
    else:
        raise AssertionError('Accepted duplicate profile groups')

record = dict(scope='Actual retained original calibration logs as positive control; host-only tamper checks, not CTS',
              passed=True, actual_rounds=len(original['points']), actual_runs=len(original['sources']),
              cases=cases, profile_sha256=original['profile_sha256'],
              source_sha256=digest(args.source),
              validator_sha256=digest(Path(__file__).resolve().parents[1] / 'media_profile_validation.py'))
args.output.write_text(json.dumps(record, indent=2) + '\n')
print('MEDIA_PROFILE_EVIDENCE_CONTRACT=PASS|checks=' + str(len(cases)) + '|real_original_rounds=' + str(len(original['points'])))
