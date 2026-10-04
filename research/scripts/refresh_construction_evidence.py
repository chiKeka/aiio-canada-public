"""Refresh structured construction feeds into reviewable outputs; preserve last-good data."""
from __future__ import annotations
import argparse
import csv
import json
import shutil
import sys
import tempfile
import ssl
import time
from urllib.error import HTTPError, URLError
from datetime import date, datetime, UTC, timedelta
from pathlib import Path


def failure_diagnostic(exc: Exception, route: str | None) -> dict:
    """Log the public registered route and typed transport details, never exception text."""
    result = {'registered_retrieval_url': route, 'error_type': type(exc).__name__}
    if isinstance(exc, HTTPError):
        result['http_status'] = exc.code
    elif isinstance(exc, URLError):
        reason = exc.reason
        result['transport_reason_class'] = type(reason).__name__
        if isinstance(getattr(reason, 'errno', None), int):
            result['transport_errno'] = reason.errno
    return result


def transient_fetch_error(exc: Exception) -> bool:
    if isinstance(exc, HTTPError):
        return exc.code == 429 or 500 <= exc.code < 600
    if isinstance(exc, URLError):
        # Retain ordinary certificate verification; TLS failures require investigation.
        return isinstance(exc.reason, OSError) and not isinstance(exc.reason, ssl.SSLError)
    return isinstance(exc, TimeoutError)


def fetch_with_retry(operation, source_id: str, route: str | None, *, attempts: int = 3, wait=time.sleep):
    for attempt in range(1, attempts + 1):
        try:
            return operation()
        except Exception as exc:
            retrying = attempt < attempts and transient_fetch_error(exc)
            print(json.dumps({'source_id': source_id, 'attempt': attempt, 'retrying': retrying, **failure_diagnostic(exc, route)}), file=sys.stderr)
            if not retrying:
                raise
            wait(min(2 ** (attempt - 1), 4))


def is_due(previous: dict, today: date, interval: int) -> bool:
    checked = previous.get('last_success')
    return not checked or today >= date.fromisoformat(checked) + timedelta(days=interval)


def refresh(root: Path, today: date, update=None) -> dict:
    policy = json.loads((root / 'data/registry/construction-refresh-policy.json').read_text())
    receipt_path = root / 'data/model-runs/construction-source-refresh.json'
    previous = json.loads(receipt_path.read_text()) if receipt_path.exists() else {'sources': {}}
    results = dict(previous['sources'])
    registry_path = root / 'data/registry/sources.json'
    routes = {source['source_id']: source.get('retrieval_url') for source in json.loads(registry_path.read_text())['sources']} if registry_path.exists() else {}
    for entry in policy['sources']:
        old = results.get(entry['id'], {})
        if entry['mode'] != 'structured_feed' or not is_due(old, today, entry['checkEveryDays']):
            continue
        try:
            result = (update or update_source)(root, entry['id'], today, old)
            results[entry['id']] = {**{key: value for key, value in result.items() if key not in {'error_type', 'reason', 'http_status', 'transport_reason_class', 'transport_errno'}}, 'last_success': today.isoformat(), 'last_attempt': today.isoformat(), 'status': 'checked', 'review_due': (today + timedelta(days=entry['checkEveryDays'])).isoformat()}
        except Exception as exc:
            # Never publish a failed parse, zero-filled substitute, or sensitive exception text.
            results[entry['id']] = {**{key: value for key, value in old.items() if key not in {'error_type', 'http_status', 'transport_reason_class', 'transport_errno'}}, 'last_attempt': today.isoformat(), 'status': 'error', 'reason': 'source_fetch_or_validation_failed_last_good_retained', **failure_diagnostic(exc, routes.get(entry['id']))}
            print(json.dumps({'source_id': entry['id'], **results[entry['id']]}), file=sys.stderr)
    failed = [source_id for source_id, result in results.items() if result.get('status') == 'error']
    report = {'version': policy['version'], 'status': 'partial_refresh' if failed else 'checks_completed', 'failed_source_ids': failed, 'sources': results}
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = receipt_path.with_suffix('.tmp')
    temporary.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    temporary.replace(receipt_path)
    return report


def update_source(root: Path, source_id: str, today: date, previous: dict) -> dict:
    sys.path.insert(0, str(root / 'research/src'))
    from aiio.registry import load_registry
    from aiio.retrieval import retrieve
    from aiio.adapters.alberta_projects import fetch_major_projects, normalize_major_projects
    from aiio.adapters.statcan import normalize_bcpi_alberta, normalize_jvws_alberta, normalize_jvws_canada
    from aiio.materials import run_material_cost_screen
    from aiio.labour import run_labour_recruitment_pressure
    from aiio.public_projects import run_public_project_exposure
    registry = {s.source_id: s for s in load_registry(root / 'data/registry/sources.json')}
    record = fetch_with_retry(lambda: fetch_major_projects(root / 'data/raw') if source_id == 'ALBERTA_MAJOR_PROJECTS' else retrieve(registry[source_id], root / 'data/raw'), source_id, registry[source_id].retrieval_url)
    raw = Path(record.archive_path)
    if not raw.is_absolute():
        raw = root / raw
    if record.content_hash == previous.get('content_hash'):
        return {**previous, 'retrieved_at': record.retrieved_at, 'changed': False}
    with tempfile.TemporaryDirectory(prefix='construction-feed-') as directory:
        stage = Path(directory)
        outputs = []
        def output(relative):
            path = stage / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            outputs.append((path, root / relative))
            return path
        if source_id == 'ALBERTA_MAJOR_PROJECTS':
            all_projects = output('data/processed/alberta_major_projects.csv')
            ai_projects = output('data/processed/alberta_ai_projects.csv')
            normalize_major_projects(raw, all_projects, ai_projects, today.isoformat())
            with ai_projects.open() as stream:
                if not any(r['ai_relevance'] == 'core_data_centre' for r in csv.DictReader(stream)):
                    raise ValueError('Empty core inventory requires review')
            current = json.loads((root / 'data/model-runs/public_project_exposure_alberta_v0.1.json').read_text())
            run_public_project_exposure(all_projects, output('data/model-runs/public_project_exposure_alberta_v0.1.json'), output('data/processed/public_project_exposure_alberta.csv'), window_start=current['window']['start_year'], window_end=current['window']['end_year'])
        elif source_id == 'STATCAN_BCPI_18100289':
            normalized = output('data/processed/bcpi_alberta.csv')
            normalize_bcpi_alberta(raw, normalized)
            report = run_material_cost_screen(normalized, output('data/model-runs/bcpi_material_cost_screen_alberta_v0.1.json'), output('data/processed/bcpi_material_cost_screen_alberta.csv'))
            old = json.loads((root / 'data/model-runs/bcpi_material_cost_screen_alberta_v0.1.json').read_text())
            if report['period_end'] < old['period_end']:
                raise ValueError('Refusing a regressed price vintage')
        elif source_id == 'STATCAN_JVWS_14100444':
            normalized = output('data/processed/labour_availability_canada.csv')
            normalize_jvws_canada(raw, normalized)
            normalize_jvws_alberta(raw, output('data/processed/labour_availability_alberta.csv'))
            report = run_labour_recruitment_pressure(normalized, root / 'data/processed/labour_workforce_stock_canada.csv', output('data/model-runs/labour_recruitment_pressure_canada_v0.1.json'))
            old = json.loads((root / 'data/model-runs/labour_recruitment_pressure_canada_v0.1.json').read_text())
            if report['vacancy_period_end'] < old['vacancy_period_end']:
                raise ValueError('Refusing a regressed vacancy vintage')
        else:
            raise ValueError('Unsupported structured source')
        # No canonical file is touched until this source and its downstream model validate.
        backups = {}
        try:
            for staged, destination in outputs:
                destination.parent.mkdir(parents=True, exist_ok=True)
                backups[destination] = destination.read_bytes() if destination.exists() else None
                shutil.copyfile(staged, destination.with_suffix(destination.suffix+'.tmp'))
            for _, destination in outputs:
                destination.with_suffix(destination.suffix+'.tmp').replace(destination)
        except Exception:
            for destination, prior in backups.items():
                if prior is None:
                    destination.unlink(missing_ok=True)
                else:
                    destination.write_bytes(prior)
            raise
        finally:
            for _, destination in outputs:
                destination.with_suffix(destination.suffix+'.tmp').unlink(missing_ok=True)
    return {'content_hash': record.content_hash, 'retrieved_at': record.retrieved_at, 'changed': True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--as-of', type=date.fromisoformat, default=datetime.now(UTC).date())
    args = parser.parse_args()
    report = refresh(args.root.resolve(), args.as_of)
    print(json.dumps({'status': report['status'], 'failed_source_ids': report['failed_source_ids'], 'source_checks': report['sources']}, indent=2))
    if report['failed_source_ids']:
        raise SystemExit(1)

if __name__ == '__main__':
    main()
