"""Offline publication preflight and explicit local-source acquisition boundary."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def check() -> int:
    report = json.loads((ROOT / 'publication/source-availability.json').read_text())
    present = absent = 0
    for item in report['receipts']:
        receipt = ROOT / item['receipt_path']
        raw = receipt.with_name(receipt.name.removesuffix('.manifest.json'))
        if raw.exists():
            expected = item['original_content_hash']
            actual = 'sha256:' + hashlib.sha256(raw.read_bytes()).hexdigest()
            if expected != actual:
                print(f'FAIL: bundled original source hash differs: {raw.relative_to(ROOT)}')
                return 1
            present += 1
        else:
            absent += 1
    if (ROOT / '.git').exists() or (ROOT / '.openai/hosting.json').exists():
        print('FAIL: review export must contain no original Git history or hosting binding')
        return 1
    print(f'Public snapshot: {present} bundled original receipts verified; {absent} original archives unavailable.')
    print('Unavailable raw-source normalization is explicitly blocked; retained observations and scenarios are not newly validated.')
    return 0

def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='operation', required=True)
    sub.add_parser('check')
    source = sub.add_parser('run-source')
    source.add_argument('name')
    source.add_argument('--allow-local-acquisition', action='store_true')
    args = parser.parse_args()
    if args.operation == 'check':
        return check()
    entry = json.loads((ROOT / 'publication/source-commands.json').read_text()).get(args.name)
    if entry is None:
        parser.error('Unknown source-dependent command')
    if not args.allow_local_acquisition:
        print('Source-dependent command withheld in this public review snapshot.')
        print(entry['reason'])
        print('Review publisher terms and privacy requirements in PUBLIC_SNAPSHOT.md.')
        print('If local acquisition/use is permitted, invoke this command with --allow-local-acquisition; do not redistribute downloaded bytes automatically.')
        return 2
    print('Local source acquisition/use explicitly acknowledged. This does not grant redistribution permission.')
    return subprocess.run(entry['command'], shell=True, cwd=ROOT).returncode

if __name__ == '__main__':
    sys.exit(main())
