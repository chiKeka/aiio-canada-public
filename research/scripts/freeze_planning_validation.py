#!/usr/bin/env python3
"""Reproduce a pending-review packet; no model update or reviewer transmission."""
import argparse
import json
from pathlib import Path
from aiio.validation_packet import build_packet, verify_packet, OUTPUT

parser = argparse.ArgumentParser()
parser.add_argument('--check', action='store_true', help='verify frozen hashes and exact reproduction without writing')
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
packet = build_packet(root)
if args.check:
    frozen = json.loads((root / OUTPUT).read_text())
    verify_packet(root, frozen)
    if frozen != packet:
        raise SystemExit('Frozen packet does not reproduce')
else:
    (root / OUTPUT).write_text(json.dumps(packet, indent=2, sort_keys=True) + '\n')
print('Planning validation packet verified; independent review pending; estimates withheld.')
