#!/usr/bin/env python3
"""Merge real codec/size measurements; does not install or accept CTS results."""
from pathlib import Path
import argparse
import json
from media_profile_validation import merge_profiles

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--out', type=Path, required=True)
parser.add_argument('profiles', type=Path, nargs='+')
args = parser.parse_args()
print(json.dumps(merge_profiles(args.profiles, args.source, args.out), indent=2))
