"""Run refresh in isolation; retain candidates without promoting research vintages."""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import UTC, date, datetime
from pathlib import Path

GENERATED_ROOTS = ('data/raw', 'data/processed', 'data/model-runs', 'data/digests', 'public/data')
ATTEMPTS = ('data/model-runs/construction-source-refresh.json', 'data/model-runs/weekly-source-refresh.json')
EXCLUDED = {'.git', 'node_modules', '.next', '.sites', '__pycache__', '.pytest_cache', '.cache'}


def digest(path: Path) -> str:
    return 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(root: Path) -> dict[str, str]:
    return {str(path.relative_to(root)): digest(path)
            for name in GENERATED_ROOTS for path in (root / name).rglob('*') if path.is_file()}


def atomic_copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + '.review.tmp')
    shutil.copyfile(source, temporary)
    temporary.replace(destination)


def build_operational_inputs(root: Path) -> None:
    subprocess.run([sys.executable, str(root / 'scripts/build-construction-inputs.py'), '--root', str(root)], cwd=root, check=True)


def refresh_for_review(root: Path, edition: str, runner=subprocess.run) -> dict:
    root = root.resolve()
    date.fromisoformat(edition)
    before = inventory(root)
    run_id = datetime.now(UTC).strftime('%Y%m%dT%H%M%S%fZ')
    candidate = root / 'data/review-candidates' / f'weekly-evidence-{edition}-{run_id}'
    candidate.mkdir(parents=True, exist_ok=False)
    with tempfile.TemporaryDirectory(prefix='aiio-review-refresh-') as directory:
        stage = Path(directory) / 'workspace'
        shutil.copytree(root, stage, ignore=lambda folder, names: [n for n in names if n in EXCLUDED or n == 'review-candidates' or (n == 'dist' and Path(folder) == root)])
        if (root / 'node_modules').exists():
            (stage / 'node_modules').symlink_to(root / 'node_modules', target_is_directory=True)
        command = [sys.executable, str(stage / 'research/scripts/weekly_evidence_refresh.py'), '--root', str(stage), '--edition-date', edition]
        # Every generated file writes inside stage; installed dependencies are shared read-only.
        process = runner(command, cwd=stage, capture_output=True, text=True, check=False)
        (candidate / 'refresh.stdout.log').write_text(process.stdout or '')
        (candidate / 'refresh.stderr.log').write_text(process.stderr or '')
        (candidate / 'refresh.log').write_text((process.stdout or '') + '\n--- STDERR ---\n' + (process.stderr or ''))
        after = inventory(stage)
        changed = {name: value for name, value in after.items() if before.get(name) != value}
        for name in changed:
            atomic_copy(stage / name, candidate / name)
        operational = []
        for name in ATTEMPTS:
            if name in changed:
                atomic_copy(stage / name, root / name)
                operational.append(name)
        # Retain raw bytes under the review candidate. Canonical manifests point
        # there, so provenance never points into a deleted temporary workspace.
        for name in changed:
            if not name.startswith('data/raw/') or not name.endswith('.manifest.json'):
                continue
            if name in before:
                continue  # Never overwrite a pinned historical retrieval receipt.
            payload = json.loads((stage / name).read_text())
            for key in ('archive_path', 'metadata_archive_path'):
                if payload.get(key):
                    relative = Path(payload[key])
                    if relative.is_absolute():
                        relative = relative.relative_to(stage)
                    if '..' in relative.parts or relative.is_absolute() or not str(relative).startswith('data/raw/'):
                        raise ValueError('Raw receipt archive path escapes candidate evidence')
                    retained = candidate / relative
                    if not retained.is_file() and (stage / relative).is_file():
                        atomic_copy(stage / relative, retained)
                    if retained.is_file():
                        payload[f'original_{key}'] = str(relative)
                        payload[key] = str(retained.relative_to(root))
            payload['review_status'] = 'candidate_only_not_release_promoted'
            destination = root / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n')
            operational.append(name)
        # These receipts reflect actual attempts independently of candidate model
        # validity. Release freshness and latest approved/review digest stay fixed.
        sys.path.insert(0, str(root / 'research/src'))
        from aiio.source_freshness import build_source_freshness_report
        operational_report = 'public/data/source-receipts.json'
        build_source_freshness_report(root / 'data/registry/sources.json', datetime.now(UTC).date().isoformat(), root / operational_report)
        operational.append(operational_report)
        build_operational_inputs(root)
        operational.extend(['public/data/construction/manifest.json', 'public/data/construction/snapshot.json'])
        from aiio.research_surface import build_research_surface_manifest
        surface_path = 'public/data/research-surface.json'
        build_research_surface_manifest(root, root / surface_path)
        operational.append(surface_path)
        canonical_after = inventory(root)
        illegal = sorted(name for name in set(before) | set(canonical_after)
                         if before.get(name) != canonical_after.get(name) and name not in operational)
        if illegal:
            raise RuntimeError(f'Isolation violated; canonical research changed: {illegal}')
        report = {
            'schema_version': '1.0.0', 'edition_date': edition, 'run_id': run_id,
            'status': 'review_candidate' if process.returncode == 0 else 'partial_candidate_refresh_failed',
            'refresh_exit_code': process.returncode, 'candidate_directory': str(candidate.relative_to(root)),
            'candidate_manifest': changed,
            'local_only_paths': sorted(name for name in changed if name.startswith('data/raw/') and not name.endswith('.manifest.json')),
            'deleted_in_stage': sorted(set(before) - set(after)),
            'canonical_operational_updates': operational,
            'baseline_manifest': {name: before[name] for name in changed if name in before},
            'automatic_model_change': False, 'digest_promoted': False, 'frozen_release_promoted': False,
            'review_boundary': 'Candidates may invalidate frozen input contracts within staging. Canonical research, release, pilot and latest digest remain unchanged. Review and separately version any promotion; this run supplies no independent approval.',
        }
        (candidate / 'manifest.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
        return report


def check_candidates(root: Path) -> dict:
    root = root.resolve()
    sys.path.insert(0, str(root / 'research/src'))
    from aiio.digest import build_digest, validate_digest_cadence
    candidates = []
    for manifest in sorted((root / 'data/review-candidates').glob('weekly-evidence-*/manifest.json')):
        payload = json.loads(manifest.read_text())
        directory = manifest.parent
        if payload.get('schema_version') != '1.0.0':
            raise ValueError('Unknown candidate manifest schema')
        if any(payload.get(flag) is not False for flag in ('automatic_model_change', 'digest_promoted', 'frozen_release_promoted')):
            raise ValueError('Candidate manifest cannot authorize promotion')
        if type(payload.get('refresh_exit_code')) is not int:
            raise ValueError('Candidate exit code must be an integer')
        if (payload.get('status') == 'review_candidate') != (payload['refresh_exit_code'] == 0):
            raise ValueError('Candidate status and refresh exit disagree')
        if payload.get('candidate_directory') != str(directory.relative_to(root)):
            raise ValueError('Candidate directory identity mismatch')
        if payload.get('status') not in ('review_candidate', 'partial_candidate_refresh_failed'):
            raise ValueError('Unknown candidate review state')
        allowed_roots = tuple(name + '/' for name in GENERATED_ROOTS)
        for name in payload['candidate_manifest']:
            if not isinstance(name, str) or not name.startswith(allowed_roots) or '..' in Path(name).parts:
                raise ValueError('Unknown or escaping candidate generated path')
        for name in payload.get('local_only_paths', []):
            if name not in payload['candidate_manifest'] or not name.startswith('data/raw/') or name.endswith('.manifest.json'):
                raise ValueError('Only listed raw archives can be unavailable locally')
        raw_unavailable = []
        for name, expected in payload['candidate_manifest'].items():
            path = (directory / name).resolve()
            if not path.is_relative_to(directory.resolve()):
                raise ValueError('Candidate manifest path escapes its directory')
            if not path.is_file():
                if name in payload.get('local_only_paths', []) and name.startswith('data/raw/') and not name.endswith('.manifest.json'):
                    raw_unavailable.append(name)
                    continue  # Only provenance receipts redistribute; raw evidence remains local.
                raise ValueError(f'Missing candidate artifact: {name}')
            if digest(path) != expected:
                raise ValueError(f'Candidate artifact hash drift: {name}')
        if payload['status'] != 'review_candidate':
            continue  # Partial failures remain diagnostics, never review-ready evidence.
        edition = date.fromisoformat(payload['edition_date'])
        items = directory / 'data/digests/items' / f'{edition}.json'
        source = json.loads(items.read_text())
        if source.get('status') != 'review' or any(item.get('automatic_model_change') for item in source['items']):
            raise ValueError('Candidate digest must remain review-only with no automatic model change')
        with tempfile.TemporaryDirectory(prefix='aiio-candidate-digest-') as temporary:
            rebuilt = build_digest(items, Path(temporary) / 'digest.md', edition,
                                   source_registry_path=root / 'data/registry/sources.json')
        frozen = json.loads((directory / 'data/digests' / f'{edition}.manifest.json').read_text())
        if rebuilt != frozen:
            raise ValueError('Candidate digest manifest does not reproduce against source registry')
        candidates.append({'directory': str(directory.relative_to(root)), 'edition_date': edition.isoformat(), 'raw_archives_not_available_for_byte_verification': raw_unavailable})
    if not candidates:
        raise ValueError('No complete, current, review-only weekly evidence candidate exists')
    latest = max(candidates, key=lambda item: (item['edition_date'], item['directory']))
    latest['cadence'] = validate_digest_cadence(root / latest['directory'] / 'data/digests/items', as_of_date=datetime.now(UTC).date())
    return {'status': 'review_candidates_verified', 'independent_review': 'pending',
            'publication_authorized': False, 'digest_promoted': False, 'candidates': candidates}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--edition-date', type=date.fromisoformat, default=datetime.now(UTC).date())
    parser.add_argument('--check-candidates', action='store_true', help='Read-only candidate hashes, registry and digest cadence audit; no promotion')
    args = parser.parse_args()
    if args.check_candidates:
        print(json.dumps(check_candidates(args.root), indent=2, sort_keys=True))
        return
    report = refresh_for_review(args.root, args.edition_date.isoformat())
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(report['refresh_exit_code'])


if __name__ == '__main__':
    main()
