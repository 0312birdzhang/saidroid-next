#!/usr/bin/env python3
"""Compare two or more analyzed runs side by side (VM or host, no device needed).

    python3 scripts/perf/compare-perf.py build/perf/qq-r63 build/perf/qq-perf2
    python3 scripts/perf/compare-perf.py --stages draw,shm_memcpy build/perf/*perf2

Reads <dir>/stats.json written by analyze-perf.py and prints one markdown table
per metric. Frames-per-second is only printed for runs that actually recorded
frames; a muted (SAILDROID_PERF unset) run legitimately has no fps here, which
is stated instead of being filled with a guess.
"""
from pathlib import Path
import argparse, json

DEFAULT_STAGES = ['vsync_to_lock', 'java_lock', 'draw', 'java_compose_getpixels',
                  'jni_mutex_wait', 'jni_int_array_copy', 'commit_call', 'shm_memcpy',
                  'ui_thread_total', 'vsync_to_commit', 'frame_interval',
                  'compositor_vsync_interval', 'commit_to_buffer_release']


def load(directory):
    stats = Path(directory) / 'stats.json'
    if not stats.exists():
        raise SystemExit('missing %s (run analyze-perf.py first)' % stats)
    return json.loads(stats.read_text())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('directories', nargs='+')
    ap.add_argument('--stages', default=','.join(DEFAULT_STAGES))
    ap.add_argument('--out', default=None)
    args = ap.parse_args()
    stages = [name for name in args.stages.split(',') if name]
    reports = [load(directory) for directory in args.directories]
    labels = [report['label'] for report in reports]
    lines = ['| metric | ' + ' | '.join(labels) + ' |',
             '|---|' + '---|' * len(labels)]
    extra = lambda r, key: (r.get('extra_meta') or {}).get(key)
    rows = [
        ('commit rate /s', lambda r: r['fps'] if r['fps'] is not None else 'n/a'),
        ('presents /s', lambda r: r.get('presents_per_second')),
        ('frames used', lambda r: r['frames_used']),
        ('composes (Java)', lambda r: r['composes_java']),
        ('presents (native)', lambda r: r['presents_reported']),
        ('publish drops', lambda r: r['drops_reported']),
        ('direct-path misses', lambda r: extra(r, 'dmiss')),
        ('direct-path dropped frames', lambda r: extra(r, 'ddrop')),
        ('frames w/ out-of-order stage', lambda r: r.get('frames_with_out_of_order_stage')),
        ('commits/vsync mean', lambda r: r['commits_per_vsync']['mean']),
        ('commits/vsync max', lambda r: r['commits_per_vsync']['max']),
        ('UI ms/vsync p50', lambda r: (r['ui_thread_ms_per_vsync'] or {}).get('p50')),
        ('UI ms/vsync p95', lambda r: (r['ui_thread_ms_per_vsync'] or {}).get('p95')),
    ]
    for name, getter in rows:
        lines.append('| %s | %s |' % (name, ' | '.join(str(getter(r)) for r in reports)))
    for stage in stages:
        row = ['%s mean / p95 (ms)' % stage]
        for report in reports:
            found = next((s for s in report['stages'] if s['name'] == stage), None)
            row.append('%s / %s' % (found['mean'], found['p95'])
                       if found and found.get('samples') else 'n/a')
        lines.append('| ' + ' | '.join(row) + ' |')
    text = '\n'.join(lines) + '\n'
    print(text)
    if args.out:
        Path(args.out).write_text(text)
        print('WROTE', args.out)


if __name__ == '__main__':
    main()
