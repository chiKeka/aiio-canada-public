"""Render an approved evidence-only intake after verifying its editorial receipt."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--items', type=Path, required=True)
    parser.add_argument('--approval-receipt', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--edition-date', type=date.fromisoformat, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    sys.path.insert(0, str(root / 'research/src'))
    from aiio.digest import build_digest, publish_reviewed_digest
    from aiio.schemas import ValidationError
    if json.loads((root / args.items).read_text()).get('status') != 'approved':
        raise ValidationError('promotion requires an approved intake with a verified editorial receipt')
    result = build_digest(root / args.items, root / args.output, args.edition_date, source_registry_path=root / 'data/registry/sources.json', approval_receipt_path=root / args.approval_receipt)
    publish_reviewed_digest(root, root / args.items, result, root / args.approval_receipt)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
