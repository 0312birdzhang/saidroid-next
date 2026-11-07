#!/usr/bin/env python3
"""Turn one raw SailDroid frame record file into the performance table.

    python3 scripts/perf/analyze-perf.py build/perf/qq-base
    python3 scripts/perf/analyze-perf.py build/perf/scroll-heavy --skip-frames 20

Every record is one committed frame (one compose()). Raw fields:
    vsync  last wl_surface_frame (compositor vsync) before this frame's draw
    lock   Surface.lockCanvas entered; lr = it returned (View.draw may start)
    unlock UnlockCanvasAndPost entered -> View.draw / Canvas finished
    present SdWindowHost.present entered -> Java compose + getPixels done
    pdone  int[] copied into native memory (native frame mutex released after)
    mw     UI-thread wait for that native frame mutex
    memcpy measured int[] -> wl_shm byte copy inside publish()
    commit wl_surface_commit returned; release = wl_buffer.release
    ui     UI-thread time for the whole synchronous compose/present cycle
    cinv   ordinal of this commit inside the current vsync interval

Cross-thread timestamps can mix two adjacent frames when the UI thread produces
frames faster than the window thread publishes them. Instead of pretending that
never happens, every record is checked for monotonic order and a per-stage
plausibility bound; rejected samples are counted and printed.
"""
from pathlib import Path
import argparse, json, statistics

STAGE_CAPS = {
    'vsync_to_lock': 200.0, 'draw': 200.0, 'java_lock': 50.0,
    'java_compose_getpixels': 200.0, 'jni_mutex_wait': 50.0,
    'jni_int_array_copy': 100.0, 'commit_call': 50.0, 'shm_memcpy': 100.0,
    'ui_thread_total': 400.0, 'vsync_to_commit': 400.0, 'frame_interval': 1000.0,
    'touch_to_commit': 2000.0, 'commit_to_buffer_release': 1000.0,
    'touch_to_release': 4000.0,
    'compositor_vsync_interval': 1000.0, 'frame_callback_gap': 1000.0,
}


def parse(path):
    meta = {}
    frames = []
    for line in Path(path).read_text(errors='replace').splitlines():
        if not line.startswith('SDPERF='):
            continue
        parts = line.split('|')
        kind = parts[0].split('=', 1)[1]
        fields = {}
        for item in parts[1:]:
            if '=' in item:
                key, value = item.split('=', 1)
                try:
                    fields[key] = int(value)
                except ValueError:
                    fields[key] = value
        if kind == 'meta':
            meta = fields
        elif kind == 'frame':
            frames.append(fields)
    # A record file may carry the same frame twice (a streamed line written at
    # commit time plus a later rewrite); keep the last, richest occurrence.
    seen, unique = {}, []
    for frame in frames:
        seen[frame.get('i')] = frame
    for key in sorted(seen, key=lambda k: (k is None, k)):
        unique.append(seen[key])
    duplicates = len(frames) - len(unique)
    return meta, unique, duplicates


def percentile(values, fraction):
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * fraction
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    weight = position - low
    return ordered[low] * (1 - weight) + ordered[high] * weight


def summarise(name, values, dropped=0, unit='ms'):
    values = [v for v in values if v is not None]
    if not values:
        return dict(name=name, unit=unit, samples=0, rejected=dropped)
    return dict(name=name, unit=unit, samples=len(values), rejected=dropped,
                mean=round(statistics.fmean(values), 2),
                p50=round(percentile(values, 0.50), 2),
                p95=round(percentile(values, 0.95), 2),
                p99=round(percentile(values, 0.99), 2),
                max=round(max(values), 2),
                min=round(min(values), 2))


def ms(delta):
    return None if delta is None else delta / 1e6


def monotonic(sample):
    keys = ('lock', 'lr', 'unlock', 'present', 'pdone', 'commit')
    previous = 0
    for key in keys:
        value = sample.get(key, 0)
        if not value:
            continue
        if value < previous:
            return False
        previous = value
    vsync = sample.get('vsync', 0)
    return not (vsync and sample.get('lock') and sample['lock'] < vsync)


def app_steps(directory):
    """Steps reported by the scroll probe, if its log was kept next to perf.bin."""
    log = directory / 'app.log'
    if not log.exists():
        return None
    steps = None
    for line in log.read_text(errors='replace').splitlines():
        if 'PERFSCROLL=paused|' in line or 'PERFSCROLL=progress|' in line:
            for field in line.split('|'):
                if field.startswith('steps='):
                    try:
                        steps = max(steps or 0, int(field[6:]))
                    except ValueError:
                        pass
    return steps


def pump_verdict(meta, steps):
    """Tell "the view never redrew" apart from "the view redrew but was never
    composited" -- the two hypotheses that one run could not distinguish."""
    locks, unlocks, draws = meta.get('locks'), meta.get('unlocks'), meta.get('jdraws')
    composes = meta.get('composes')
    dschedule, callbacks = meta.get('dsched'), meta.get('fcb')
    if steps is None or locks is None:
        return 'undecided: no app.log steps or no Java pump counters'
    if steps == 0:
        # driver=none: the page never drives itself, so every frame in the window was
        # caused by an injected gesture. Driver steps say nothing here; frame counts do.
        return ('injected-only: 0 self-driven ticks, %s lock(s), %s compose(s) -- frames '
                'came from injected gestures' % (locks, composes))
    if steps > 50 and locks <= 2:
        return ('page-never-redrew: %d driver steps but only %s lock(s) and %s compose(s) '
                '-> the frame pump is innocent, the scene did not invalidate'
                % (steps, locks, composes))
    if locks >= 0.9 * steps and (composes or 0) <= 2:
        return ('redraws-not-composited: %d lock(s) for %d steps but only %s compose(s) '
                '(vsync asks %s, window requests %s, callbacks %s) -> frame pump confirmed'
                % (locks, steps, composes, dschedule, meta.get('rf'), callbacks))
    return ('mixed: %d lock(s), %d unlock(s), %s transaction(s), %s compose(s) for %d steps'
            % (locks, unlocks, draws, composes, steps))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('directory')
    ap.add_argument('--skip-frames', type=int, default=0)
    ap.add_argument('--label', default=None)
    args = ap.parse_args()
    directory = Path(args.directory)
    meta, frames, duplicate_records = parse(directory / 'perf.bin')
    if not frames:
        raise SystemExit('no frame records in %s' % (directory / 'perf.bin'))
    recorded = len(frames)
    frames = frames[args.skip_frames:]
    # Timestamps come from two threads (UI publishes, window thread receives the
    # compositor callback), and our "vsync" is a compositor callback rather than a
    # clock, so a callback can legitimately land after the UI thread already began
    # the next frame. Dropping such frames would throw away the draw/compose
    # stages that are perfectly ordered. Structural checks only; each stage is
    # then validated on its own and out-of-order stages are counted per stage.
    structural = [f for f in frames if f.get('i') is not None and f.get('commit')]
    invalid = len(frames) - len(structural)
    frames = structural
    if not frames:
        raise SystemExit('not enough valid frames after filtering (%d recorded)' % recorded)
    if len(frames) < 2:
        # A run that produced a single frame is exactly the diagnostic case for the
        # frame pump, so still report it -- but never with percentiles or an fps.
        print('WARNING: only %d valid frame(s); percentiles and fps are not reported' % len(frames))

    stages = {}
    rejected = {}

    def collect(name, value):
        if value is None:
            return
        if value < 0 or value > STAGE_CAPS.get(name, 1e9):
            rejected[name] = rejected.get(name, 0) + 1
            return
        stages.setdefault(name, []).append(value)

    for previous, current in zip(frames, frames[1:]):
        collect('frame_interval', ms(current['commit'] - previous['commit']))
    out_of_order = 0
    for current in frames:
        if current['vsync']:
            if current['lock']:
                if current['lock'] >= current['vsync']:
                    collect('vsync_to_lock', ms(current['lock'] - current['vsync']))
                else:
                    out_of_order += 1
                    rejected['vsync_to_lock'] = rejected.get('vsync_to_lock', 0) + 1
            if current['commit'] < current['vsync']:
                rejected['vsync_to_commit'] = rejected.get('vsync_to_commit', 0) + 1
            else:
                collect('vsync_to_commit', ms(current['commit'] - current['vsync']))
        if current['lr']:
            collect('java_lock', ms(current['lr'] - current['lock']))
            collect('draw', ms(current['unlock'] - current['lr']))
        if current['unlock']:
            collect('java_compose_getpixels', ms(current['present'] - current['unlock']))
            collect('jni_mutex_wait', ms(current['mw']))
            collect('jni_int_array_copy',
                    ms(current['pdone'] - current['present'] - current.get('mw', 0)))
            collect('commit_call', ms(current['commit'] - current['pdone']))
            if current.get('ui'):
                collect('ui_thread_total', ms(current['ui']))
        collect('shm_memcpy', ms(current['memcpy']))
        if current['input']:
            collect('touch_to_commit', ms(current['commit'] - current['input']))
        if current.get('gap', -1) >= 0:
            collect('frame_callback_gap', ms(current['gap']))
        if current['release'] and current['release'] > current['commit']:
            collect('commit_to_buffer_release', ms(current['release'] - current['commit']))
        # Input -> buffer release is the closest proxy we have for on-screen: the
        # compositor only releases a buffer after it consumed it. It is not glass
        # time (Lipstick may present on a later commit), so it is reported as
        # input_to_compositor_consumed, never as "input latency on screen".
        if current['input'] and current['release'] and current['release'] > current['input']:
            collect('touch_to_release', ms(current['release'] - current['input']))

    gaps = [f['gap'] for f in frames if f.get('gap', -1) >= 0]
    vsyncs = [f['vsync'] for f in frames if f['vsync']]
    intervals = [ms(b - a) for a, b in zip(vsyncs, vsyncs[1:])]
    if intervals:
        stages['compositor_vsync_interval'] = intervals

    per_vsync = {}
    for frame in frames:
        if frame['vsync']:
            per_vsync[frame['vsync']] = per_vsync.get(frame['vsync'], 0) + 1
    counts = list(per_vsync.values())
    histogram = {}
    for value in counts:
        histogram[value] = histogram.get(value, 0) + 1

    ui_per_vsync = {}
    for frame in frames:
        if frame['vsync'] and frame.get('ui'):
            ui_per_vsync[frame['vsync']] = ui_per_vsync.get(frame['vsync'], 0) + frame['ui']
    ui_sums = [ms(value) for value in ui_per_vsync.values()]

    commits = [f['commit'] for f in frames]
    span = (commits[-1] - commits[0]) / 1e9
    fps = (len(commits) - 1) / span if span > 0 else None

    steps = app_steps(directory)
    table = [summarise(name, values, rejected.get(name, 0)) for name, values in stages.items()]
    total_mean = next((row['mean'] for row in table if row['name'] == 'vsync_to_commit'), None)
    ui_mean = next((row['mean'] for row in table if row['name'] == 'ui_thread_total'), None)
    report = dict(
        label=args.label or directory.name,
        source=str(directory / 'perf.bin'),
        frames_recorded=recorded,
        frames_used=len(frames),
        skipped_warmup=args.skip_frames,
        samples_rejected_non_monotonic=invalid,
        frames_with_out_of_order_stage=out_of_order,
        duplicate_records=duplicate_records,
        meta_present=bool(meta),
        frames_with_callback_gap=len(gaps),
        extra_meta={k: meta.get(k) for k in
                    ('creq', 'cfall', 'fast', 'layers', 'layer_alpha', 'layer_full',
                     'layer_identity', 'presents', 'composes', 'locks', 'unlocks',
                     'jdraws', 'dinit', 'dsched', 'rf', 'fcb', 'fcommit', 'ecommit',
                     'force', 'direct', 'dcopy', 'dmiss', 'ddrop') if k in meta},
        stage_values_rejected=rejected,
        seconds_span=round(span, 3),
        fps=round(fps, 2) if fps else None,
        fps_note='commits / span over every kept frame (not display refresh); '
                 'presents and drops come from the native counters',
        presents_per_second=(round(meta['presents'] / span, 2)
                             if span > 0 and meta.get('presents') else None),
        presents_reported=meta.get('presents'),
        composes_java=meta.get('composes'),
        drops_reported=int(meta.get('dropped', 0)),
        commits_per_vsync=dict(
            intervals=len(counts), mean=round(statistics.fmean(counts), 3) if counts else None,
            p50=round(percentile(counts, 0.5), 3) if counts else None,
            p95=round(percentile(counts, 0.95), 3) if counts else None,
            max=max(counts) if counts else None,
            histogram={str(k): v for k, v in sorted(histogram.items())}),
        ui_thread_ms_per_vsync=(None if not ui_sums else dict(
            mean=round(statistics.fmean(ui_sums), 2),
            p50=round(percentile(ui_sums, 0.5), 2),
            p95=round(percentile(ui_sums, 0.95), 2),
            max=round(max(ui_sums), 2))),
        compose_split=(None if not meta.get('composes') or meta.get('composes') < 0 or
                       meta.get('erase_ns', -1) < 0 else dict(
                           composes=meta['composes'],
                           erase_ms=round(meta.get('erase_ns', 0) / 1e6 / meta['composes'], 2),
                           blit_ms=round(meta.get('blit_ns', 0) / 1e6 / meta['composes'], 2),
                           getpixels_ms=round(meta.get('getpixels_ns', 0) / 1e6 / meta['composes'], 2),
                           present_ms=round(meta.get('jpresent_ns', 0) / 1e6 / meta['composes'], 2))),
        one_time=dict(
            window_init_ms=round(meta.get('init_ns', 0) / 1e6, 2),
            shm_allocation_ms=round(meta.get('alloc_ns', 0) / 1e6, 2),
            touch_events=meta.get('touch', 0),
            lost_records=meta.get('lost', 0)),
        app_steps=steps,
        pump_verdict=pump_verdict(meta, steps),
        stages=table,
        ui_thread_share=(None if not ui_mean else {
            row['name']: round(100.0 * row['mean'] / ui_mean, 1)
            for row in table if row['name'] in
            ('java_lock', 'draw', 'java_compose_getpixels', 'jni_mutex_wait',
             'jni_int_array_copy')
            and row.get('mean') is not None}),
        vsync_to_commit_share=(None if not total_mean else {
            row['name']: round(100.0 * row['mean'] / total_mean, 1)
            for row in table if row['name'] in
            ('vsync_to_lock', 'java_lock', 'draw', 'java_compose_getpixels',
             'jni_mutex_wait', 'jni_int_array_copy', 'commit_call', 'shm_memcpy')
            and row.get('mean') is not None}),
    )
    (directory / 'stats.json').write_text(json.dumps(report, indent=2) + '\n')
    lines = ['# Frame-path measurement: %s' % report['label'], '',
             'frames used %d of %d (skipped warmup %d); span %.3f s; fps %.2f; '
             'drops reported %d; presents %s; Java composes %s'
             % (report['frames_used'], report['frames_recorded'], report['skipped_warmup'],
                report['seconds_span'], report['fps'] or 0, report['drops_reported'],
                report['presents_reported'], report['composes_java']),
             'frames rejected as structurally incomplete: %d; frames with an '
             'out-of-order stage: %d; stage values dropped (out of order or above '
             'cap): %s'
             % (report['samples_rejected_non_monotonic'],
                report['frames_with_out_of_order_stage'],
                json.dumps(report['stage_values_rejected'])),
             'commits per vsync: %s' % json.dumps(report['commits_per_vsync']),
             'UI-thread ms per vsync: %s' % json.dumps(report['ui_thread_ms_per_vsync']),
             'one-time: window init %.2f ms, SHM alloc %.2f ms'
             % (report['one_time']['window_init_ms'], report['one_time']['shm_allocation_ms']),
             '',
             '| stage | n | mean | p50 | p95 | p99 | max | rejected |',
             '|---|---|---|---|---|---|---|---|']
    for row in table:
        if not row.get('samples'):
            continue
        lines.append('| %s | %d | %.2f | %.2f | %.2f | %.2f | %.2f | %d |'
                     % (row['name'], row['samples'], row['mean'], row['p50'], row['p95'],
                        row['p99'], row['max'], row.get('rejected', 0)))
    lines.append('')
    lines.append('share of vsync->commit mean: ' + json.dumps(report['vsync_to_commit_share']))
    if report.get('compose_split'):
        split = report['compose_split']
        lines.append('Java compose split per frame over %d composes: erase %.2f ms, layer blits '
                     '%.2f ms, getPixels %.2f ms, present %.2f ms'
                     % (split['composes'], split['erase_ms'], split['blit_ms'],
                        split['getpixels_ms'], split['present_ms']))
        lines.append('')
    if report.get('extra_meta'):
        lines.append('compose counters: ' + json.dumps(report['extra_meta']))
        lines.append('pump verdict (steps %s): %s' % (report.get('app_steps'), report.get('pump_verdict')))
    if report.get('frames_with_callback_gap'):
        lines.append('frames with a compositor callback before them: %d'
                     % report['frames_with_callback_gap'])
    (directory / 'report.md').write_text('\n'.join(lines) + '\n')
    print('\n'.join(lines))
    print('\nSTATS', directory / 'stats.json')


if __name__ == '__main__':
    main()
