"""Reconcile acquired public evidence without changing frozen model inputs."""
import csv
import hashlib
import io
import json
import re
import zipfile
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data/raw/historical_evidence_20260905'
REVIEW = ROOT / 'data/reviews'
PROCESSED = ROOT / 'data/processed'


def digest(path):
    return 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def write_csv(path, rows):
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


class TableRows(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows, self.row, self.cell = [], None, None

    def handle_starttag(self, tag, attrs):
        if tag == 'tr':
            self.row = []
        elif tag in ('td', 'th') and self.row is not None:
            self.cell = []

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag in ('td', 'th') and self.cell is not None:
            self.row.append(' '.join(''.join(self.cell).split()))
            self.cell = None
        elif tag == 'tr' and self.row is not None:
            self.rows.append(self.row)
            self.row = None


def main():
    manifest = json.loads((RAW / 'manifest.json').read_text())
    assert len(manifest) == 25 and all(r.get('status') == 200 for r in manifest)
    for record in manifest:
        assert digest(ROOT / record['path']) == record['sha256']
    write_json(REVIEW / 'historical_bcpi_capture_manifest_v0.1.json', manifest)
    sources = {r['evidence_id']: r for r in manifest}
    observations, releases = [], []
    quarters = ['2023Q4', '2024Q1', '2024Q2', '2024Q3', '2024Q4', '2025Q1', '2025Q2', '2025Q3']
    origins = ['2024-03-31', '2024-06-30', '2024-09-30', '2024-12-31', '2025-03-31', '2025-06-30', '2025-09-30', '2025-12-31']
    for quarter, origin in zip(quarters, origins):
        release = sources[f'bcpi_{quarter}_release']
        table = sources[f'bcpi_{quarter}_table']
        source_csv = sources[f'bcpi_{quarter}_csv']
        html = (ROOT / release['path']).read_text()
        issued = re.search(r'<meta name="dcterms.issued"[^>]*content="([^"]+)"', html)[1]
        modified = re.search(r'<time property="dateModified">\s*([^<]+)', html)[1].strip()
        assert issued <= origin
        # The release must link the table, which must link the exact CSV fetched.
        table_html = (ROOT / table['path']).read_text()
        assert table['url'].rsplit('/', 1)[1] in html
        assert source_csv['url'].rsplit('/', 1)[1] in table_html
        parsed = TableRows()
        parsed.feed(table_html)
        html_rows = [r for r in parsed.rows if r and r[0] in ('Calgary', 'Edmonton')]
        rows = list(csv.reader((ROOT / source_csv['path']).open(encoding='utf-8-sig')))
        selected = [r for r in rows if r and r[0] in ('Calgary', 'Edmonton')]
        assert selected == html_rows, f'CSV/HTML mismatch: {quarter}'
        assert len(selected) == 4
        for index, row in enumerate(selected):
            observations.append(dict(release_quarter=quarter, release_date_claim=issued,
                market=row[0], aggregate='residential' if index < 2 else 'non_residential',
                index_base=rows[2][4], year_prior_index=row[2], previous_quarter_index=row[3],
                release_quarter_index=row[4], published_qoq_percent=row[5], published_yoy_percent=row[6],
                source_url=source_csv['url'], source_sha256=source_csv['sha256'],
                benchmark_asset_mapping='unavailable_aggregate_only', publication_review_status='pending'))
        releases.append(dict(reference_quarter=quarter, forecast_origin=origin, release_date_claim=issued,
            page_modified_date=modified, later_page_modification=modified > issued,
            release_url=release['url'], table_url=table['url'], csv_url=source_csv['url'],
            matched_alberta_rows=4, csv_html_reconciliation='pass',
            historical_exact_content_review='pending', benchmark_asset_coverage=False))
    write_csv(PROCESSED / 'bcpi_daily_alberta_release_observations_v0.1.csv', observations)
    archive = sources['bcpi_archived_18100276']
    with zipfile.ZipFile(ROOT / archive['path']) as zipped:
        source = csv.DictReader(io.TextIOWrapper(zipped.open('18100276.csv'), encoding='utf-8-sig'))
        historical = [r for r in source if r['GEO'].startswith(('Calgary', 'Edmonton'))
            and r['Type of building'] in ('Office building', 'School', 'Institutional buildings [62213]')
            and r['Division'] == 'Division composite' and '2017-01' <= r['REF_DATE'] <= '2024-04']
    assert len(historical) == 180
    write_csv(PROCESSED / 'bcpi_predecessor_alberta_asset_extract_v0.1.csv', historical)
    draft_path = REVIEW / 'edmonton_included_permit_review_v0.1.json'
    draft = json.loads(draft_path.read_text())
    permit_path = ROOT / 'data/raw/edmonton_general_building_permits/2026-09-01_f4da956ae985.json'
    permit_manifest_path = Path(str(permit_path) + '.manifest.json')
    permit_manifest = json.loads(permit_manifest_path.read_text())
    assert digest(permit_path) == permit_manifest['content_hash']
    permits = {r['row_id']: r for r in json.loads(permit_path.read_text())}
    records, totals = [], defaultdict(int)
    for reviewed in draft['records']:
        permit = permits[reviewed['source_row_id']]
        # Match the source adapter's whitespace normalization before hashing.
        cleaned_description = ' '.join(str(permit['job_description']).split())
        description_hash = 'sha256:' + hashlib.sha256(cleaned_description.encode()).hexdigest()
        assert description_hash == reviewed['description_sha256']
        value = int(permit['construction_value'])
        totals[reviewed['work_class']] += value
        records.append(dict(reviewed, issue_date=permit['issue_date'][:10], reported_construction_value_cad=value,
            source_text_hash_verified=True, expansion_screen_candidate=reviewed['work_class'] != 'maintenance',
            ai_specificity='not_established', historical_publication='not_established'))
    assert dict(totals) == {'maintenance': 863000, 'fitout': 185000, 'expansion': 4000000}
    write_json(REVIEW / 'edmonton_included_permit_review_v0.2.json', dict(
        review_id='AIIO_EDMONTON_INCLUDED_PERMIT_REVIEW_0_2', reviewer='Codex source-text and public-source review',
        status='analyst_review_complete_independent_review_pending', prior_review_sha256=digest(draft_path),
        source_manifest=str(permit_manifest_path.relative_to(ROOT)),
        records=records, scope_totals_cad=dict(totals), total_cad=sum(totals.values()),
        maintenance_exclusion_candidate_cad=863000, remaining_candidate_cad=4185000,
        applied_to_model=False, confirmed_independent_events=None,
        linkage_findings=[
            'Rogers: same-facility candidate remains unconfirmed; 2018 alarm and 2020 hall expansion are distinct scopes, not duplicate records.',
            'Wolfpaw: current operator fibre-ring page lists Rice Howard Place; a network point of presence does not establish ownership or historic construction identity.',
            'PowerHouse Group provides design and construction services; company name in a permit does not establish facility ownership.',
            'Cross Cancer cooling and Enbridge like-for-like suppression replacement are maintenance scopes.',
            'Present-day AI marketing cannot establish AI use when any of these six permits was issued.'] ))
    web = json.loads((REVIEW / 'historical_web_capture_sources_v0.1.json').read_text())
    for item in web:
        assert digest(ROOT / item['path']) == item['sha256']
    report = dict(review_id='AIIO_HISTORICAL_EVIDENCE_ACQUISITION_0_1',
        bcpi_releases=releases, acquired_bcpi_raw_artifacts=len(manifest),
        reconciled_daily_alberta_rows=len(observations), predecessor_asset_rows=len(historical),
        predecessor_source_id='STATCAN_BCPI_18100276', predecessor_full_vintage_date_review='pending',
        permit_records_reviewed=len(records), permit_description_hash_checks='pass',
        web_capture_hash_checks='pass', model_replay_authorized=False,
        decision='do_not_rerun_frozen_benchmark_with_incomplete_historical_inputs',
        unresolved=['Release aggregates cannot substitute for office, institutional and school outcomes.',
            'Predecessor extract is one terminal archived version, not eight historical vintages.',
            'Detailed historical releases with complete training coverage remain missing.',
            'CAL-3 announcements do not establish period-specific realized spend or a complete historical project register.',
            'Permit issue dates do not prove historical dataset availability; independent linkage review remains pending.'])
    write_json(ROOT / 'data/model-runs/historical_evidence_acquisition_v0.1.json', report)
    print(json.dumps({k: v for k, v in report.items() if k not in ('bcpi_releases', 'unresolved')}, indent=2))


if __name__ == '__main__':
    main()
