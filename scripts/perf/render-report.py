#!/usr/bin/env python3
"""Render build/evidence/<label>/report.md from measured stats.json files.

    python3 scripts/perf/render-report.py --label pref1 \
        --run build/perf/qq-perf2 --run build/perf/scroll-heavy-perf2 \
        --gate build/perf/qq-perf2-muted/gate.json

    python3 scripts/perf/render-report.py --label _TEMPLATE --skeleton

No number in the report is typed by hand: everything comes from the stats.json
written by analyze-perf.py, the meta.json written by run-perf-vm.py, or the
gate.json written by check-gate-vm.py. Ordering follows docs/ACCEPTANCE.md:
sampling integrity, per-vsync commit histogram and the UI-thread block come
first; the full stage table and the reproduction commands come after.
"""
import argparse
import datetime
import json
from pathlib import Path

UI_STAGES = ('java_lock', 'draw', 'java_compose_getpixels', 'jni_mutex_wait',
             'jni_int_array_copy')
# These run on the window thread inside publish(), and commit_call already
# contains the memcpy, so they never belong in the UI-thread table.
WINDOW_STAGES = ('shm_memcpy', 'commit_call', 'frame_callback_gap')


def load(path):
    return json.loads(Path(path).read_text())


def fmt(value, digits=2):
    if value is None:
        return '—'
    if isinstance(value, float):
        return ('%.' + str(digits) + 'f') % value
    return str(value)


def stage_row(row):
    return '| %s | %s | %s | %s | %s | %s | %d |' % (
        row['name'], fmt(row.get('mean')), fmt(row.get('p50')), fmt(row.get('p95')),
        fmt(row.get('p99')), fmt(row.get('max')), row.get('rejected', 0))


def run_section(stats, meta):
    lines = []
    hist = stats.get('commits_per_vsync') or {}
    lines.append('### %s — %s' % (stats['label'], (meta or {}).get('scenario', '?')))
    lines.append('')
    lines.append('sampled %s s · frames used %d of %d (warmup skipped %d) · '
                 'commit rate %s/s · presented %s/s'
                 % (fmt(stats.get('seconds_span'), 2), stats['frames_used'],
                    stats['frames_recorded'], stats['skipped_warmup'],
                    fmt(stats.get('fps')), fmt(stats.get('presents_per_second'))))
    lines.append('')
    lines.append('The commit rate is commits divided by the sampled span, not a display '
                 'refresh rate: this compositor only hands out a frame callback when it '
                 'actually composites the surface.')
    lines.append('')
    if stats.get('pump_verdict'):
        lines.append('**Frame pump verdict**: %s (driver steps %s)'
                     % (stats['pump_verdict'], stats.get('app_steps')))
        lines.append('')
    rejects = stats.get('stage_values_rejected') or {}
    lines.append('**Sampling integrity** (P4): records rejected as structurally '
                 'incomplete %d, frames with an out-of-order stage %d (that stage '
                 'dropped, the frame kept), duplicate records %d, meta line %s'
                 % (stats.get('samples_rejected_non_monotonic', 0),
                    stats.get('frames_with_out_of_order_stage', 0),
                    stats.get('duplicate_records', 0),
                    'present' if stats.get('meta_present') else 'MISSING (streamed only)'))
    if rejects:
        lines.append('')
        lines.append('Dropped stage values by stage: %s'
                     % ', '.join('%s %d' % (k, v) for k, v in sorted(rejects.items())))
        if rejects.get('vsync_to_lock'):
            lines.append('')
            lines.append('`vsync_to_lock` drops are expected in this design: the '
                         'callback is delivered by the compositor, so it can arrive '
                         'after the UI thread has already started the next frame. '
                         'The draw/compose stages on those frames stay valid.')
    lines.append('')
    lines.append('Frames the window thread dropped (both buffers busy): **%d**; '
                 'presents reported %s; Java composes %s'
                 % (stats.get('drops_reported', 0), stats.get('presents_reported'),
                    stats.get('composes_java')))
    lines.append('')
    lines.append('**Every-vsync commit histogram** (P3): intervals %s, mean %s, p50 %s, '
                 'p95 %s, max %s' % (hist.get('intervals'), fmt(hist.get('mean')),
                                     fmt(hist.get('p50')), fmt(hist.get('p95')),
                                     hist.get('max')))
    lines.append('')
    lines.append('| commits in one vsync | vsyncs |')
    lines.append('| --- | --- |')
    for key, value in (hist.get('histogram') or {}).items():
        lines.append('| %s | %d |' % (key, value))
    lines.append('')
    ui = stats.get('ui_thread_ms_per_vsync') or {}
    lines.append('**UI-thread blocked per vsync** (P4): mean %s ms, p50 %s ms, p95 %s ms, '
                 'max %s ms' % (fmt(ui.get('mean')), fmt(ui.get('p50')), fmt(ui.get('p95')),
                                fmt(ui.get('max'))))
    lines.append('')
    stages = {row['name']: row for row in stats.get('stages', [])}
    lines.append('| UI-thread segment | mean ms | p50 | p95 | share of UI-thread total |')
    lines.append('| --- | --- | --- | --- | --- |')
    share = stats.get('ui_thread_share') or {}
    for name in UI_STAGES:
        row = stages.get(name)
        if row:
            share_value = share.get(name)
            share_text = '—' if share_value is None else fmt(float(share_value), 1) + '%'
            lines.append('| %s | %s | %s | %s | %s |' % (
                name, fmt(row.get('mean')), fmt(row.get('p50')), fmt(row.get('p95')),
                share_text))
    window_rows = [stages[name] for name in WINDOW_STAGES if name in stages]
    if window_rows:
        lines.append('')
        lines.append('**Window thread, after the UI thread returned** (not part of the '
                     'UI block; `commit_call` already contains `shm_memcpy`):')
        lines.append('')
        lines.append('| stage | mean ms | p50 | p95 | p99 | max |')
        lines.append('| --- | --- | --- | --- | --- | --- |')
        for row in window_rows:
            lines.append('| %s | %s | %s | %s | %s | %s |' % (
                row['name'], fmt(row.get('mean')), fmt(row.get('p50')),
                fmt(row.get('p95')), fmt(row.get('p99')), fmt(row.get('max'))))
    lines.append('')
    lines.append('| stage | mean ms | p50 | p95 | p99 | max | rejected |')
    lines.append('| --- | --- | --- | --- | --- | --- | --- |')
    for row in stats.get('stages', []):
        lines.append(stage_row(row))
    lines.append('')
    one = stats.get('one_time') or {}
    lines.append('One-time costs excluded from the per-frame table: window init %s ms, '
                 'SHM allocation %s ms, touch events injected %s, lost records %s'
                 % (fmt(one.get('window_init_ms')), fmt(one.get('shm_allocation_ms')),
                    one.get('touch_events'), one.get('lost_records')))
    if meta:
        lines.append('')
        lines.append('**Motion provenance**: %s (swipes requested %s, handled %s); '
                     'never compare a self-driven window with an injected one'
                     % (meta.get('scene_driver', 'unknown'), meta.get('swipes_requested'),
                        meta.get('swipes_handled')))
        lines.append('')
        lines.append('Process cost: CPU %s ms over %s s (%s%% of one core), log %s B/s, '
                     '%s log lines at close'
                     % (fmt(meta.get('cpu_ms'), 1), fmt(meta.get('window_seconds'), 2),
                        fmt(meta.get('cpu_percent_of_one_core'), 1),
                        meta.get('log_bytes_per_second'), meta.get('log_lines_at_close')))
    lines.append('')
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--label', required=True)
    ap.add_argument('--run', action='append', default=[])
    ap.add_argument('--gate', default=None)
    ap.add_argument('--skeleton', action='store_true')
    ap.add_argument('--out', default=None)
    args = ap.parse_args()
    out = Path(args.out or ('build/evidence/%s' % args.label))
    out.mkdir(parents=True, exist_ok=True)

    lines = ['# Frame-path performance — %s' % args.label, '',
             'Generated %s by `scripts/perf/render-report.py`; every number below is copied '
             'from the run directories named in the reproduction section.'
             % datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), '']

    if args.skeleton:
        lines += ['_Skeleton: run the matrix, then re-run this generator with --run/--gate._', '']
        lines += ['## 0. What was measured', '', '<pending>', '',
                  '## 1. Sampling integrity and dropped frames', '', '<pending>', '',
                  '## 2. Every-vsync commit histogram', '', '<pending>', '',
                  '## 3. UI-thread block per vsync', '', '<pending>', '',
                  '## 4. Full stage table', '', '<pending>', '',
                  '## 5. One-time costs and process cost', '', '<pending>', '',
                  '## 6. Gate control (sampler off vs baseline)', '', '<pending>', '',
                  '## 7. Reproduction', '', '<pending>', '',
                  '## 8. Not verified', '', '<pending>', '']
    else:
        runs = []
        for run in args.run:
            stats = load(Path(run) / 'stats.json')
            meta_path = Path(run) / 'meta.json'
            meta = load(meta_path) if meta_path.exists() else None
            runs.append((stats, meta))
        lines.append('## 0. What was measured')
        lines.append('')
        for stats, meta in runs:
            lines.append('- `%s` — scenario %s, mode %s, package %s, window %s s'
                         % (stats['label'], (meta or {}).get('scenario', '?'),
                            (meta or {}).get('mode', '?'), (meta or {}).get('package', '?'),
                            fmt((meta or {}).get('window_seconds'), 1)))
        lines.append('')
        for index, (stats, meta) in enumerate(runs):
            lines += run_section(stats, meta)
        lines.append('## 6. Gate control (sampler off vs baseline)')
        lines.append('')
        if args.gate and Path(args.gate).exists():
            gate = load(args.gate)
            lines.append('Verdict: **%s**%s' % (gate['verdict'], '' if not gate['failures']
                                                else ' — ' + '; '.join(gate['failures'])))
            lines.append('')
            lines.append('```json')
            lines.append(json.dumps(gate['checks'], indent=2))
            lines.append('```')
        else:
            lines.append('Not run.')
        lines.append('')
        lines.append('## 7. Reproduction')
        lines.append('')
        lines.append('```sh')
        lines.append('# in the VM (MeeGo Build), repo at /media/psf/Home/WorkSpace/saidroid-next')
        lines.append('scripts/devlock.sh acquire 900 sd-runtime')
        for stats, _ in runs:
            lines.append('python3 scripts/perf/run-perf-vm.py --tag %s   # see meta.json for argv'
                         % stats['label'])
        lines.append('python3 scripts/perf/analyze-perf.py build/perf/<tag>')
        lines.append('python3 scripts/perf/check-gate-vm.py <muted> <baseline>')
        lines.append('scripts/devlock.sh release sd-runtime')
        lines.append('```')
        lines.append('')
        lines.append('## 8. Not verified')
        lines.append('')
        lines.append('- Anything not listed above; GPU/dmabuf path untested on this build.')

    (out / 'report.md').write_text('\n'.join(lines) + '\n')
    print(out / 'report.md')


if __name__ == '__main__':
    main()
