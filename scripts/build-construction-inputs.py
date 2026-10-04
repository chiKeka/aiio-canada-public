"""Publish existing research inputs; no network or model-parameter promotion."""
import argparse
from datetime import date, timedelta
import csv
import hashlib
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
args = parser.parse_args()
root = args.root.resolve()
destination = root / 'public/data/construction'
destination.mkdir(parents=True, exist_ok=True)
with (root / 'data/processed/alberta_ai_projects.csv').open() as source:
    projects = [
        dict(id=r['project_id'], name=r['name'], region=r['municipality'],
             stage=r['stage'], cost=float(r['estimated_cost_cad']) if r['estimated_cost_cad'] else None,
             start=int(r['start_year']) if r['start_year'] else None,
             end=int(r['end_year']) if r['end_year'] else None,
             source=r['project_website'], asOf=r['as_of_date'])
        for r in csv.DictReader(source) if r['ai_relevance'] == 'core_data_centre'
    ]
(destination / 'projects.json').write_text(json.dumps(projects, indent=2))
for source, target in [('construction-benchmark-register.json', 'benchmarks.json'),
                       ('construction-pressure-requirements.md', 'requirements.md')]:
    (destination / target).write_bytes((root / 'docs/research' / source).read_bytes())
evidence_paths = {
    'labour': 'data/model-runs/labour_recruitment_pressure_canada_v0.1.json',
    'prices': 'data/model-runs/bcpi_material_cost_screen_alberta_v0.1.json',
    'capital': 'data/model-runs/public_project_exposure_alberta_v0.1.json',
}
evidence = {key: json.loads((root / name).read_text()) for key, name in evidence_paths.items()}
alberta_labour = [r for r in evidence['labour']['occupation_diagnostics'] if r['geography_id'] == 'PR_48']
factory_prices = [r for r in evidence['prices']['observations'] if r['archetype'] == 'industrial_factory_proxy']
if len(alberta_labour) != 6 or len(factory_prices) != 8 or not projects:
    raise ValueError('Construction evidence coverage changed; review before publishing')
if len({r['vacancy_period_end'] for r in alberta_labour}) != 1 or len({r['period_end'] for r in factory_prices}) != 1:
    raise ValueError('Mixed observation periods require review')

(destination / 'briefing.json').write_text(json.dumps({
    'version': 'alberta-briefing-1',
    'guidance': json.loads((root / 'docs/research/alberta-delivery-guidance.json').read_text()),
    'labour': [row for row in evidence['labour']['occupation_diagnostics'] if row['geography_id'] == 'PR_48'],
    'prices': [row for row in evidence['prices']['observations'] if row['archetype'] == 'industrial_factory_proxy'],
    'capital': {key: evidence['capital'][key] for key in ['window', 'as_of_date', 'screened_project_count', 'asset_class_summaries']},
    'sourceHashes': {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in [*evidence_paths.values(), 'docs/research/alberta-delivery-guidance.json']},
}, indent=2))
files = {name: hashlib.sha256((destination / name).read_bytes()).hexdigest()
         for name in ['projects.json', 'benchmarks.json', 'requirements.md', 'briefing.json']}
files['lib/construction-model.ts'] = hashlib.sha256((root / 'lib/construction-model.ts').read_bytes()).hexdigest()
registry = {s['source_id']: s for s in json.loads((root / 'data/registry/sources.json').read_text())['sources']}
benchmarks = json.loads((destination / 'benchmarks.json').read_text())
policy = json.loads((root / 'data/registry/construction-refresh-policy.json').read_text())
receipt_path = root / 'data/model-runs/construction-source-refresh.json'
receipt = json.loads(receipt_path.read_text()) if receipt_path.exists() else {'sources': {}}
checks = []
periods = {
    'ALBERTA_MAJOR_PROJECTS': max(p['asOf'] for p in projects),
    'STATCAN_JVWS_14100444': max(r['vacancy_period_end'] for r in evidence['labour']['occupation_diagnostics'] if r['geography_id'] == 'PR_48'),
    'STATCAN_CENSUS_OCCUPATION_98100449': max(r['workforce_period_end'] for r in evidence['labour']['occupation_diagnostics'] if r['geography_id'] == 'PR_48'),
    'STATCAN_BCPI_18100289': evidence['prices']['period_end'],
}
for entry in policy['sources']:
    record = receipt['sources'].get(entry['id'], {})
    original = registry.get(entry['id'], {})
    benchmark_source = next((s for s in benchmarks['sources'] if s['id'] == entry['id']), {})
    reviewed = benchmark_source.get('verified_on', original.get('last_verified', benchmarks['as_of']))
    last = record.get('last_success', reviewed)
    checks.append({**entry, 'observationPeriod': periods.get(entry['id'], benchmark_source.get('period', 'Not published')),
                   'lastChecked': last, 'checkBasis': 'Refresh receipt' if record.get('last_success') else 'Source verification record',
                   'lastAttempt': record.get('last_attempt'), 'lastCheckFailed': record.get('status') == 'error',
                   'nextCheckDue': (date.fromisoformat(last) + timedelta(days=entry['checkEveryDays'])).isoformat(),
                   'sourceUrl': original.get('canonical_url', benchmark_source.get('url', ''))})
manifest = {'version': 'construction-0.2', 'asOf': max([benchmarks['as_of'], *periods.values()]), 'sha256': files,
            'refresh': {'scheduler': policy['scheduler'], 'sources': checks,
                        'publication': 'Structured changes enter the existing review PR; merging publishes through the Vercel integration.'}}
(destination / 'manifest.json').write_text(json.dumps(manifest, indent=2))
# The request-time reader consumes one atomic bundle, never a mixture of file versions.
payload = json.dumps({'projects': projects, 'benchmarks': benchmarks,
                      'evidence': json.loads((destination / 'briefing.json').read_text()),
                      'manifest': manifest}, sort_keys=True, separators=(',', ':'))
snapshot = {'revision': hashlib.sha256(payload.encode()).hexdigest(), 'payload': payload}
temporary = destination / 'snapshot.json.tmp'
temporary.write_text(json.dumps(snapshot, separators=(',', ':')))
temporary.replace(destination / 'snapshot.json')
print(f'Published {len(projects)} phase records and the research register with SHA-256 provenance.')

# ADM screen uses the same canonical inventory.
import subprocess
import sys
subprocess.run([sys.executable, str(Path(__file__).resolve().with_name("build-adm-evidence.py")), "--root", str(root)], check=True)
