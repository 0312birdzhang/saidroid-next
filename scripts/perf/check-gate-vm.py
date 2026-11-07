#!/usr/bin/env python3
"""P5 gate-control check: does turning the sampler off leave behaviour identical?

    python3 scripts/perf/check-gate-vm.py build/perf/qq-perf2-muted build/perf/qq-r63

Compares an instrumented run with SAILDROID_PERF unset against the plain baseline
run of the same scene, and writes gate.json next to the muted run:

  * screen.png pixel difference (Pillow in the VM) -- a live page animates, so the
    verdict is on magnitude, not on a single bit;
  * log line count ratio at close (the sampler must not add log volume);
  * the SDSURFACE=/SDWINDOW= marker sequence must be identical;
  * the muted run must not have produced a perf.bin.

Exit code 0 only when every check passes.
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageChops

TOLERANCE = 8
MAX_DIFF_PERCENT = 5.0        # animated widgets legitimately differ a little
MAX_LOG_RATIO_DEVIATION = 0.25


def shot_diff(a_path, b_path):
    a = Image.open(a_path).convert('RGB')
    b = Image.open(b_path).convert('RGB')
    if a.size != b.size:
        return dict(same_size=False, size_a=list(a.size), size_b=list(b.size))
    diff = ImageChops.difference(a, b)
    histogram = diff.histogram()
    total = a.size[0] * a.size[1] * 3
    differing = sum(n for value, n in enumerate(histogram) if value % 256 > TOLERANCE)
    mean = sum(value % 256 * n for value, n in enumerate(histogram)) / total
    bbox = diff.getbbox()
    area = 0.0 if bbox is None else 100.0 * (bbox[2] - bbox[0]) * (bbox[3] - bbox[1]) / (
        a.size[0] * a.size[1])
    return dict(same_size=True, identical=bbox is None,
                channels_over_tolerance_percent=round(100.0 * differing / total, 4),
                mean_abs_channel_diff=round(mean, 4),
                diff_bbox=list(bbox) if bbox else None,
                diff_bbox_area_percent=round(area, 2))


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    muted_dir, baseline_dir = Path(sys.argv[1]), Path(sys.argv[2])
    muted = json.loads((muted_dir / 'meta.json').read_text())
    baseline = json.loads((baseline_dir / 'meta.json').read_text())
    checks, failures = {}, []

    checks['muted_run_has_no_sampler'] = dict(
        muted_perf_enabled=muted.get('perf_enabled'),
        muted_perf_file_exists=(muted_dir / 'perf.bin').exists())
    if muted.get('perf_enabled') or (muted_dir / 'perf.bin').exists():
        failures.append('muted run still had the sampler enabled')

    shots = {}
    for name, path in (('muted', muted_dir), ('baseline', baseline_dir)):
        if (path / 'screen.png').exists():
            shots[name] = path / 'screen.png'
    if len(shots) == 2:
        checks['screen'] = shot_diff(shots['muted'], shots['baseline'])
        if not checks['screen'].get('same_size'):
            failures.append('screenshot sizes differ')
        elif (checks['screen']['channels_over_tolerance_percent'] > MAX_DIFF_PERCENT or
              not checks['screen']['identical'] and
              checks['screen']['diff_bbox_area_percent'] > 95.0):
            failures.append('screenshot content differs beyond tolerance')
    else:
        checks['screen'] = dict(skipped='missing screen.png in one run')
        failures.append('missing screenshot for the pixel comparison')

    lines = dict(muted=muted.get('log_lines_at_close'), baseline=baseline.get('log_lines_at_close'))
    ratio = None
    if lines['muted'] and lines['baseline']:
        ratio = lines['muted'] / lines['baseline']
    checks['log_lines'] = dict(**lines, ratio=None if ratio is None else round(ratio, 3))
    if ratio is None:
        failures.append('log line count missing')
    elif abs(ratio - 1.0) > MAX_LOG_RATIO_DEVIATION:
        failures.append('log volume differs by more than %.0f%%' % (100 * MAX_LOG_RATIO_DEVIATION))

    markers = dict(muted=muted.get('markers'), baseline=baseline.get('markers'))
    checks['markers'] = markers
    if markers['muted'] != markers['baseline']:
        failures.append('SDSURFACE=/SDWINDOW= marker sequence differs')

    result = dict(verdict='PASS' if not failures else 'FAIL', failures=failures,
                  thresholds=dict(pixel_tolerance=TOLERANCE,
                                  max_diff_percent=MAX_DIFF_PERCENT,
                                  max_log_ratio_deviation=MAX_LOG_RATIO_DEVIATION),
                  compared=dict(muted=str(muted_dir), baseline=str(baseline_dir)),
                  checks=checks)
    (muted_dir / 'gate.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if not failures else 1)


if __name__ == '__main__':
    main()
