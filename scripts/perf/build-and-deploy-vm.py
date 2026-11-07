#!/usr/bin/env python3
"""Build a perf release from the worktree and deploy it to the phone (VM side).

    python3 scripts/perf/build-and-deploy-vm.py perf2 [--from-product DIR]

Holds no lock itself: run it only while holding scripts/devlock.sh.
"""
import subprocess, sys
from pathlib import Path

REPO = Path('/media/psf/Home/WorkSpace/saidroid-next')


def main():
    tag = sys.argv[1]
    extra = sys.argv[2:]
    subprocess.run([sys.executable, str(REPO / 'scripts/perf/close-owned-vm.py')], check=True)
    subprocess.run([sys.executable, str(REPO / 'scripts/perf/build-perf-release-vm.py'), tag] + extra,
                   check=True)
    subprocess.run([sys.executable, str(REPO / 'scripts/perf/deploy-perf-release-vm.py'), tag],
                   check=True)
    subprocess.run([sys.executable, str(REPO / 'scripts/perf/close-owned-vm.py')], check=True)


if __name__ == '__main__':
    main()
