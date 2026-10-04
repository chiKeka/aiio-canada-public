"""Frozen, non-authorizing planning review packet and evidence checks."""
from __future__ import annotations
import csv
import hashlib
import json
import math
from datetime import date
from pathlib import Path
from .schemas import ValidationError
from .planning_benchmark import quarter

COMPARISON = 'data/model-runs/full_schedule_proxy_comparison_v0.2.json'
PERMIT_REVIEW = 'data/reviews/edmonton_included_permit_review_v0.2.json'
OUTPUT = 'data/reviews/planning_validation_packet_v0.1.json'


def resolve_overlap(records: list[dict], links: list[dict]) -> dict:
    """Deduplicate only evidence-confirmed, same-scope inclusion in a project budget.

    Candidate facility identity alone never proves budget overlap. Unknowns retain
    a conservative union range rather than silently adding both as observed spend.
    """
    by_id = {r['id']: r for r in records}
    if len(by_id) != len(records):
        raise ValidationError('duplicate evidence record ID')
    amounts = {key: float(row['amount_cad']) for key, row in by_id.items()}
    if any(not math.isfinite(v) or v < 0 for v in amounts.values()):
        raise ValidationError('invalid evidence amount')
    excluded, unresolved = set(), []
    seen = set()
    for link in links:
        permit, project = link['permit_id'], link['project_id']
        if permit not in by_id or project not in by_id or permit == project or permit in seen:
            raise ValidationError('invalid or ambiguous overlap link')
        seen.add(permit)
        if by_id[permit]['kind'] != 'permit' or by_id[project]['kind'] != 'project':
            raise ValidationError('overlap requires permit and project')
        if link.get('status') == 'confirmed_included_scope':
            if not link.get('evidence') or amounts[permit] > amounts[project]:
                raise ValidationError('confirmed overlap needs evidence and compatible amounts')
            excluded.add(permit)
        else:
            unresolved.append(permit)
    retained = [key for key in by_id if key not in excluded]
    upper = sum(amounts[key] for key in retained)
    # All unlinked permits remain unresolved as well.
    unresolved = sorted(set(unresolved) | {k for k in retained if by_id[k]['kind'] == 'permit' and k not in seen})
    lower = max([amounts[k] for k in retained] or [0]) if unresolved else upper
    return {'retained_ids': retained, 'excluded_ids': sorted(excluded),
            'unresolved_ids': unresolved, 'union_lower_cad': lower, 'union_upper_cad': upper,
            'status': 'unresolved' if unresolved else 'resolved', 'observed_spending': False}


def align_milestones(start: str, end: str, milestones: list[dict]) -> dict:
    lo, hi = date.fromisoformat(start), date.fromisoformat(end)
    if hi < lo:
        raise ValidationError('reversed construction schedule')
    dated = []
    for row in milestones:
        if not row.get('evidence') or row.get('kind') not in ('construction_start', 'completion'):
            continue  # permit issue is never construction start
        actual = date.fromisoformat(row['date'])
        planned = lo if row['kind'] == 'construction_start' else hi
        dated.append({'kind': row['kind'], 'date': actual.isoformat(),
                      'deviation_days': (actual - planned).days, 'evidence': row['evidence']})
    return {'status': 'assessed' if dated else 'not_assessed', 'milestones': dated,
            'expenditure_timing_validated': False}


def check_rolling_origin(predictions: list[dict]) -> dict:
    keys = set()
    for row in predictions:
        target = quarter(row['target_quarter'])
        cutoff = quarter(row['information_cutoff'])
        if quarter(row['training_end']) > cutoff or cutoff >= quarter(row['forecast_origin']) or quarter(row['forecast_origin']) >= target:
            raise ValidationError('rolling-origin future-information leakage')
        key = (row['geography_id'], row['asset_class'], target)
        if key in keys:
            raise ValidationError('duplicate held-out prediction')
        keys.add(key)
    return {'status': 'pass' if keys else 'not_assessed', 'heldout_rows': len(keys),
            'heldout_quarters': len({key[2] for key in keys})}


def build_packet(root: Path) -> dict:
    comparison = json.loads((root / COMPARISON).read_text())
    review = json.loads((root / PERMIT_REVIEW).read_text())
    paths = {COMPARISON, PERMIT_REVIEW, 'data/processed/alberta_ai_projects.csv', 'research/src/aiio/validation_packet.py',
             'data/model/alberta_quarterly_planning_benchmark_contract_v0.1.json',
             'data/model/full_schedule_proxy_comparison_contract_v0.2.json'}
    for manifest in ('input_manifest', 'implementation_manifest'):
        for name, expected in comparison.get(manifest, {}).items():
            path = (root / name).resolve()
            if not path.is_relative_to(root.resolve()) or not path.is_file():
                raise ValidationError('packet input outside repository or missing')
            digest = 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != expected:
                raise ValidationError(f'comparison source drift: {name}')
            paths.add(name)
    with (root / 'data/processed/alberta_ai_projects.csv').open(newline='') as handle:
        projects = [r for r in csv.DictReader(handle) if r['ai_relevance'] == 'core_data_centre' and r['stage'] == 'Under Construction' and r['estimated_cost_cad']]
    overlap = resolve_overlap(
        [{'id': r['project_id'], 'kind': 'project', 'amount_cad': r['estimated_cost_cad']} for r in projects]
        + [{'id': r['permit_proxy_id'], 'kind': 'permit', 'amount_cad': r['reported_construction_value_cad']} for r in review['records']], [])
    hashes = {p: 'sha256:' + hashlib.sha256((root / p).read_bytes()).hexdigest() for p in sorted(paths)}
    arms = {name: {'metrics': arm['metrics'], 'checks': arm['point_error_checks'],
                  'time_partition': check_rolling_origin(arm['predictions'])} for name, arm in comparison['arms'].items()}
    return {'schema_version': '1.0.0', 'packet_id': 'AIIO_NARROW_PLANNING_REVIEW_0_1',
            'status': 'independent_review_pending_validation_withheld',
            'supported_use': {'scope': comparison['scope'], 'allowed': ['source audit', 'assumption sensitivity', 'retrospective benchmark diagnostics'],
                              'excluded': ['project cost or delay forecast', 'AI causal attribution', 'fiscal commitment estimate'],
                              'design': 'retrospective exploratory; known test quarters are not fresh confirmation'},
            'threshold_basis': 'Existing frozen benchmark contract; provisional, pending independent review',
            'thresholds': json.loads((root / 'data/model/alberta_quarterly_planning_benchmark_contract_v0.1.json').read_text()).get('acceptance_criteria', {}),
            'arms': arms, 'source_leave_one_out': {'project_source_removed': 'permit_only', 'permit_source_removed': 'project_only',
                'individual_project_leave_one_out': 'not_assessed: only one costed project; dropping it cannot establish generalization'},
            'milestone_alignment': align_milestones('2024-01-01', '2026-12-31', []),
            'overlap': {**overlap, 'candidate_record_count': len(review['records']),
                'reason': 'Unconfirmed facility identities and no evidence of inclusion in project budgets; frozen proxy unchanged'},
            'review_request': ['Confirm permit scope and budget overlap links with cited evidence.',
                'Supply dated CAL-3 construction/completion milestones and publication vintages.',
                'Assess frozen baseline comparisons and predeclared thresholds; do not select the best arm after seeing results.',
                'Approve or reject only the supported-use domain; bind any reviewer receipt to this packet hash.'],
            'independent_review': {'status': 'pending', 'reviewer': None, 'verdict': None},
            'validated_estimate_allowed': False, 'input_manifest': hashes}


def verify_packet(root: Path, packet: dict) -> None:
    for name, expected in packet['input_manifest'].items():
        path = (root / name).resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file() or 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValidationError(f'frozen packet drift: {name}')
