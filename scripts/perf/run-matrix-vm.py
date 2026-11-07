#!/usr/bin/env python3
"""Run the whole measurement matrix in one device-lock window (VM side).

    python3 scripts/perf/run-matrix-vm.py perf2        # instrumented release already deployed
    python3 scripts/perf/run-matrix-vm.py perf2 --only qq

Order (QQ scroll/latency first because a cold QQ start is the most expensive):
  1. qq-on        QQ login page, SAILDROID_PERF=1, 20 s window, screenshot
  2. scroll-*     own Activity, 4 modes (heavy/light/blank + real touch swipes)
  3. qq-muted     same QQ run with SAILDROID_PERF unset (gate control)
Then the caller restores r63 and runs `--only qq-muted --tag qq-r63` for the
baseline control (no sampler exists in r63).
"""
import argparse, json, subprocess, sys
from pathlib import Path

REPO = Path('/media/psf/Home/WorkSpace/saidroid-next')
RUN = REPO / 'scripts/perf/run-perf-vm.py'
OUT = REPO / 'build/perf'

RUNS = [
    # QQ calls System.exit(0) a few seconds after its login page appears, so the
    # window is 10 s and the runner reports the measured lifetime instead of
    # pretending a 20 s observation happened.
    ('qq', ['--scenario', 'qq', '--window', '10', '--warmup', '3', '--shot']),
    ('qq-muted', ['--scenario', 'qq', '--window', '10', '--warmup', '3', '--shot',
                  '--no-perf']),
    # Cause first: the same page and the same binary, only the animation driver
    # differs. steps/scheduled/callbacks then say whether the page is drawing and
    # whether a compositor frame callback ever arrives.
    # Pixel-copy microbenchmark: getPixels vs arraycopy vs copyPixelsToBuffer on the
    # device, so the next optimisation is chosen from measured copy costs.
    ('scroll-micro', ['--scenario', 'scroll', '--mode', 'micro', '--window', '6',
                      '--driver', 'none']),
    ('scroll-handler', ['--scenario', 'scroll', '--mode', 'heavy', '--window', '12',
                        '--driver', 'handler']),
    ('scroll-choreographer', ['--scenario', 'scroll', '--mode', 'heavy', '--window', '12',
                              '--driver', 'choreographer', '--shot']),
    ('scroll-both', ['--scenario', 'scroll', '--mode', 'heavy', '--window', '12',
                     '--driver', 'both']),
    # Same binary, different environment: the single-layer fast path off vs on,
    # and vsync-deferred compose on. Pairing these is the P1 before/after.
    # The cleanest frame-pump probe: no scrolling, no scrolling caches, one colour
    # change and one explicit invalidate per tick. If this cannot produce >100
    # frames the pump is the problem and the scrolling scene is innocent.
    ('scroll-pulse-handler', ['--scenario', 'scroll', '--mode', 'pulse', '--window', '12',
                              '--driver', 'handler']),
    ('scroll-pulse-choreographer', ['--scenario', 'scroll', '--mode', 'pulse', '--window', '12',
                                    '--driver', 'choreographer', '--shot']),
    # Two variants of "commit something when the app asks for a frame callback":
    # attach = re-attach the on-screen buffer and damage 1x1 (the compositor has a
    # reason to composite); empty = bare commit (the historical behaviour).
    ('scroll-force-attach', ['--scenario', 'scroll', '--mode', 'pulse', '--window', '12',
                             '--driver', 'handler',
                             '--env', 'SAILDROID_FORCE_FRAME_COMMIT=attach']),
    ('scroll-force-empty', ['--scenario', 'scroll', '--mode', 'pulse', '--window', '12',
                            '--driver', 'handler',
                            '--env', 'SAILDROID_FORCE_FRAME_COMMIT=empty']),
    ('scroll-nofast', ['--scenario', 'scroll', '--mode', 'heavy', '--window', '12',
                       '--driver', 'handler', '--env', 'SAILDROID_NO_FASTPATH=1', '--shot']),
    ('scroll-vsync', ['--scenario', 'scroll', '--mode', 'heavy', '--window', '12',
                      '--driver', 'choreographer',
                      '--env', 'SAILDROID_COMPOSE_ON_VSYNC=1']),
    # Same scene, same binary, one extra copy removed: the UI thread writes the Java
    # pixel array straight into the spare wl_shm buffer (no staging array, no second
    # full-screen memcpy on the window thread).
    ('scroll-direct', ['--scenario', 'scroll', '--mode', 'heavy', '--window', '12',
                       '--driver', 'handler', '--env', 'SAILDROID_DIRECT_SHM=1']),
    ('scroll-pulse-direct', ['--scenario', 'scroll', '--mode', 'pulse', '--window', '12',
                             '--driver', 'handler', '--env', 'SAILDROID_DIRECT_SHM=1']),
    # Direct copy: Bitmap.copyPixelsToBuffer writes straight into the spare wl_shm
    # buffer (ABGR8888). Same binary as everything else, only the env flag differs.
    ('scroll-copy', ['--scenario', 'scroll', '--mode', 'heavy', '--window', '12',
                     '--driver', 'handler', '--env', 'SAILDROID_DIRECT_COPY=1']),
    # If ddrop is high the loss is the two-buffer pipeline, not the copy: same
    # direct copy, one extra wl_shm buffer in flight.
    ('scroll-copy-triple', ['--scenario', 'scroll', '--mode', 'heavy', '--window', '12',
                            '--driver', 'handler', '--env', 'SAILDROID_DIRECT_COPY=1',
                            '--env', 'SAILDROID_TRIPLE_BUFFER=1']),
    # Control for the copy A/B: three buffers, old copy path. Without this run the
    # 21->32 fps jump cannot be attributed to removing the copy rather than to the
    # extra buffer.
    ('scroll-triple-legacy', ['--scenario', 'scroll', '--mode', 'heavy', '--window', '12',
                              '--driver', 'handler', '--env', 'SAILDROID_TRIPLE_BUFFER=1']),
    ('scroll-copy-touch', ['--scenario', 'scroll', '--mode', 'heavy', '--window', '12',
                           '--driver', 'none', '--swipes', '6',
                           '--env', 'SAILDROID_DIRECT_COPY=1', '--env', 'SAILDROID_TRIPLE_BUFFER=1']),
    ('scroll-pulse-copy', ['--scenario', 'scroll', '--mode', 'pulse', '--window', '12',
                           '--driver', 'handler', '--env', 'SAILDROID_DIRECT_COPY=1']),
    # Colour-order oracle: five pure bands. A swapped R/B is a screenshot comparison,
    # not a guess about the ARGB_8888 memory layout.
    ('scroll-color-legacy', ['--scenario', 'scroll', '--mode', 'color', '--window', '4',
                             '--driver', 'none', '--shot']),
    ('scroll-color-copy', ['--scenario', 'scroll', '--mode', 'color', '--window', '4',
                           '--driver', 'none', '--env', 'SAILDROID_DIRECT_COPY=1', '--shot']),
    ('scroll-light', ['--scenario', 'scroll', '--mode', 'light', '--window', '12',
                      '--driver', 'handler']),
    ('scroll-blank', ['--scenario', 'scroll', '--mode', 'blank', '--window', '12',
                      '--driver', 'handler']),
    # Real uinput gestures, nothing else: driver=none means the Activity never
    # invalidates on its own, so every frame in this window was caused by a swipe.
    ('scroll-swipe', ['--scenario', 'scroll', '--mode', 'heavy', '--window', '20',
                      '--driver', 'none', '--swipes', '8', '--shot']),
    ('scroll-touch', ['--scenario', 'scroll', '--mode', 'heavy', '--window', '12',
                      '--driver', 'handler', '--swipes', '4']),
    ('qq-nofast', ['--scenario', 'qq', '--window', '10', '--warmup', '3', '--shot',
                   '--env', 'SAILDROID_NO_FASTPATH=1']),
    ('qq-touch', ['--scenario', 'qq', '--window', '12', '--warmup', '3', '--swipes', '6']),
    # Same QQ binary as qq-r78, only the pixel path differs: the login page must
    # still render (screenshot) and the touch path must still work (swipes).
    ('qq-copy', ['--scenario', 'qq', '--window', '10', '--warmup', '3', '--shot',
                 '--env', 'SAILDROID_DIRECT_COPY=1']),
    ('qq-copy-touch', ['--scenario', 'qq', '--window', '12', '--warmup', '3', '--swipes', '6',
                       '--env', 'SAILDROID_DIRECT_COPY=1']),
    # Optimised path on the real application: QQ's login page with three buffers.
    ('qq-copy-triple', ['--scenario', 'qq', '--window', '10', '--warmup', '3', '--shot',
                        '--env', 'SAILDROID_DIRECT_COPY=1', '--env', 'SAILDROID_TRIPLE_BUFFER=1']),
    # P5 gate control on the optimised path: the same static page with the sampler
    # on and off. Static colour bands give a deterministic screenshot to compare.
    ('scroll-gate-perf', ['--scenario', 'scroll', '--mode', 'color', '--window', '6',
                          '--driver', 'none', '--shot',
                          '--env', 'SAILDROID_DIRECT_COPY=1',
                          '--env', 'SAILDROID_TRIPLE_BUFFER=1']),
    ('scroll-gate-muted', ['--scenario', 'scroll', '--mode', 'color', '--window', '6',
                           '--driver', 'none', '--shot', '--no-perf',
                           '--env', 'SAILDROID_DIRECT_COPY=1',
                           '--env', 'SAILDROID_TRIPLE_BUFFER=1']),
    # P2 wants real gestures on the optimised path, not a synthetic driver.
    ('scroll-swipe-copy-triple', ['--scenario', 'scroll', '--mode', 'heavy', '--window', '20',
                                  '--driver', 'none', '--swipes', '8',
                                  '--env', 'SAILDROID_DIRECT_COPY=1',
                                  '--env', 'SAILDROID_TRIPLE_BUFFER=1']),
    # --- r80: the optimised path is the default, so none of these set an env flag.
    # That is the whole point: P1 has to be proven on the build we intend to ship,
    # not on a build where someone remembered to export two variables.
    # Three independent 12 s windows give the repeatability P1 needs; r79's runs
    # cannot be reused because they came from a different binary.
    ('r80-scroll-1', ['--scenario', 'scroll', '--mode', 'heavy', '--window', '12',
                      '--driver', 'handler', '--shot']),
    ('r80-scroll-2', ['--scenario', 'scroll', '--mode', 'heavy', '--window', '12',
                      '--driver', 'handler', '--shot']),
    ('r80-scroll-3', ['--scenario', 'scroll', '--mode', 'heavy', '--window', '12',
                      '--driver', 'handler', '--shot']),
    # Colour-order oracle: five pure bands. A swapped R/B is a screenshot, not a
    # theory about the ARGB_8888 memory layout.
    ('r80-color', ['--scenario', 'scroll', '--mode', 'color', '--window', '4',
                   '--driver', 'none', '--shot']),
    # The real application on the default path: the login page must still render
    # and the touch path must still reach it.
    ('r80-qq', ['--scenario', 'qq', '--window', '10', '--warmup', '3', '--shot']),
    ('r80-qq-touch', ['--scenario', 'qq', '--window', '12', '--warmup', '3',
                      '--swipes', '4']),
    # P2 on real gestures: driver=none means the Activity never invalidates by
    # itself, so every frame here was caused by a swipe from the touchscreen.
    ('r80-swipe', ['--scenario', 'scroll', '--mode', 'heavy', '--window', '20',
                   '--driver', 'none', '--swipes', '8', '--shot']),
    # Same gesture evidence, but all eight swipes come from ONE long-lived uinput
    # device. Every separate injection creates and destroys an input device, which
    # is exactly the churn lipstick's evdevtouch reacts to, so this run both proves
    # delivery and keeps the compositor out of the hotplug path.
    ('r80-swipe-serve', ['--scenario', 'scroll', '--mode', 'heavy', '--window', '40',
                         '--driver', 'none', '--swipes', '8', '--swipe-serve', '--shot']),
    # P5 gate control on the optimised path: same page, sampler on vs off.
    ('r80-gate-perf', ['--scenario', 'scroll', '--mode', 'color', '--window', '6',
                       '--driver', 'none', '--shot']),
    ('r80-gate-muted', ['--scenario', 'scroll', '--mode', 'color', '--window', '6',
                        '--driver', 'none', '--shot', '--no-perf']),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('release')
    ap.add_argument('--only', action='append', default=None,
                    help='run only these step names (repeatable)')
    args = ap.parse_args()
    selected = [step for step in RUNS if not args.only or step[0] in args.only]
    summary = []
    for name, flags in selected:
        tag = '%s-%s' % (name, args.release)
        command = [sys.executable, str(RUN), '--tag', tag] + flags
        print('\n=== RUN %s\n$ %s' % (tag, ' '.join(command)), flush=True)
        result = subprocess.run(command, capture_output=True, text=True)
        print(result.stdout[-4000:])
        if result.returncode != 0:
            print(result.stderr[-3000:])
            summary.append(dict(tag=tag, ok=False))
            raise SystemExit('run %s failed; device left as-is for inspection' % tag)
        stats = OUT / tag / 'stats.json'
        report = json.loads(stats.read_text()) if stats.exists() else None
        meta = json.loads((OUT / tag / 'meta.json').read_text())
        entry = dict(tag=tag, ok=True, cpu_percent_of_one_core=meta['cpu_percent_of_one_core'],
                     log_bytes_per_second=meta['log_bytes_per_second'],
                     window_seconds=meta['window_seconds'])
        if report:
            entry.update(fps=report['fps'], presents=report['presents_reported'],
                         composes=report['composes_java'],
                         commits_per_vsync=report['commits_per_vsync'],
                         ui_ms_per_vsync=report['ui_thread_ms_per_vsync'],
                         rejected=report['stage_values_rejected'],
                         non_monotonic=report['samples_rejected_non_monotonic'],
                         stages={row['name']: row.get('mean') for row in report['stages']})
        summary.append(entry)
        print(json.dumps(entry, indent=2), flush=True)
    (OUT / ('matrix-%s.json' % args.release)).write_text(json.dumps(summary, indent=2) + '\n')
    print('\nMATRIX', OUT / ('matrix-%s.json' % args.release))


if __name__ == '__main__':
    main()
