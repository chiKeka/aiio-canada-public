"""Offline checks: cadence, failure retention and automatic publication of revised inputs."""
import importlib.util
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import ssl
from urllib.error import HTTPError, URLError
from datetime import date
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('construction_refresh',ROOT/'research/scripts/refresh_construction_evidence.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class ConstructionRefreshTests(unittest.TestCase):
    def test_safe_route_diagnostics_and_bounded_transient_retry(self):
        route='https://www150.statcan.gc.ca/n1/tbl/csv/14100444-eng.zip'
        error=URLError(ConnectionResetError(54, 'sensitive detail'))
        diagnostic=module.failure_diagnostic(error,route)
        self.assertEqual(diagnostic['registered_retrieval_url'],route)
        self.assertEqual(diagnostic['transport_reason_class'],'ConnectionResetError')
        self.assertEqual(diagnostic['transport_errno'],54)
        self.assertNotIn('sensitive',json.dumps(diagnostic))
        calls=[]; waits=[]
        def recover():
            calls.append(True)
            if len(calls)<3:raise error
            return 'last attempt succeeds'
        self.assertEqual(module.fetch_with_retry(recover,'JVWS',route,wait=waits.append),'last attempt succeeds')
        self.assertEqual(waits,[1,2])
        self.assertTrue(module.transient_fetch_error(HTTPError(route,503,'sensitive',{},None)))
        self.assertFalse(module.transient_fetch_error(HTTPError(route,404,'sensitive',{},None)))
        self.assertFalse(module.transient_fetch_error(URLError(ssl.SSLCertVerificationError('certificate'))))
        self.assertEqual(module.failure_diagnostic(HTTPError(route,429,'sensitive',{},None),route)['http_status'],429)

    def test_weekly_checks_and_failed_attempts_do_not_erase_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'data/registry').mkdir(parents=True)
            shutil.copy(ROOT/'data/registry/construction-refresh-policy.json',root/'data/registry/construction-refresh-policy.json')
            calls=[]
            def update(root, source_id, today, old):
                calls.append(source_id)
                return {'content_hash':'sha256:previous','changed':False}
            first=module.refresh(root,date(2026,9,6),update)
            self.assertEqual(len(calls),3)
            module.refresh(root,date(2026,9,12),update)
            self.assertEqual(len(calls),3)
            module.refresh(root,date(2026,9,13),update)
            self.assertEqual(len(calls),6)
            def fail(*args): raise ValueError('not included in report')
            failed=module.refresh(root,date(2026,9,20),fail)
            self.assertEqual(failed['status'],'partial_refresh')
            self.assertEqual(len(failed['failed_source_ids']),3)
            for item in failed['sources'].values():
                self.assertEqual(item['last_success'],'2026-09-13')
                self.assertEqual(item['content_hash'],'sha256:previous')
                self.assertEqual(item['status'],'error')
                self.assertNotIn('not included in report',json.dumps(item))

    def test_project_feed_rebuilds_downstream_outputs_from_archived_data(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        sys.path.insert(0, str(ROOT / 'research/src'))
        raw = ROOT / 'data/raw/alberta_major_projects/2026-08-31_450d7bfc9465.csv'
        if not raw.exists():
            self.skipTest('Archived raw inventory is not distributed in this checkout')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for relative in ['data/registry/sources.json', 'data/model-runs/public_project_exposure_alberta_v0.1.json']:
                target=root/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy(ROOT/relative,target)
            record=SimpleNamespace(archive_path=str(raw), content_hash='sha256:'+hashlib.sha256(raw.read_bytes()).hexdigest(), retrieved_at='2026-09-06T00:00:00Z')
            with patch('aiio.adapters.alberta_projects.fetch_major_projects', return_value=record):
                result=module.update_source(root, 'ALBERTA_MAJOR_PROJECTS', date(2026,9,6), {})
            self.assertTrue(result['changed'])
            output=root/'data/processed/alberta_ai_projects.csv'
            self.assertIn('2026-09-06',output.read_text())
            report=json.loads((root/'data/model-runs/public_project_exposure_alberta_v0.1.json').read_text())
            self.assertGreater(report['screened_project_count'],0)
            before=output.read_bytes()
            with patch('aiio.adapters.alberta_projects.fetch_major_projects', return_value=record), patch('aiio.adapters.alberta_projects.normalize_major_projects', side_effect=ValueError('Schema changed')):
                with self.assertRaises(ValueError):module.update_source(root, 'ALBERTA_MAJOR_PROJECTS', date(2026,9,13), {})
            self.assertEqual(output.read_bytes(),before)

    def test_publication_rebuilds_revision_and_preserves_observation_dates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            paths=['data/processed/public_project_exposure_alberta.csv','data/processed/alberta_ai_projects.csv','docs/research/construction-benchmark-register.json','docs/research/construction-pressure-requirements.md','docs/research/alberta-delivery-guidance.json','lib/construction-model.ts','data/model-runs/labour_recruitment_pressure_canada_v0.1.json','data/model-runs/bcpi_material_cost_screen_alberta_v0.1.json','data/model-runs/public_project_exposure_alberta_v0.1.json','data/registry/sources.json','data/registry/construction-refresh-policy.json']
            for p in paths:
                destination=root/p;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy(ROOT/p,destination)
            def publish():
                subprocess.run([sys.executable,str(ROOT/'scripts/build-construction-inputs.py'),'--root',str(root)],check=True,capture_output=True)
                return json.loads((root/'public/data/construction/snapshot.json').read_text())
            first=publish(); self.assertEqual(first,publish())
            price_path=root/'data/model-runs/bcpi_material_cost_screen_alberta_v0.1.json'
            prices=json.loads(price_path.read_text());prices['period_end']='2026-09-30'
            for row in prices['observations']:
                row['period_end']='2026-09-30';row['year_over_year_percent_change']=2.75
            price_path.write_text(json.dumps(prices))
            second=publish();self.assertNotEqual(first['revision'],second['revision'])
            self.assertEqual(second['revision'],hashlib.sha256(second['payload'].encode()).hexdigest())
            data=json.loads(second['payload']);self.assertEqual(data['evidence']['prices'][0]['year_over_year_percent_change'],2.75)
            self.assertEqual(data['evidence']['labour'][0]['workforce_period_end'],'2021-05-08')
            self.assertEqual(data['manifest']['asOf'],'2026-09-30')
            # A later check does not advance the observation period or invent new values.
            receipt=root/'data/model-runs/construction-source-refresh.json'
            receipt.write_text(json.dumps({'sources':{'STATCAN_BCPI_18100289':{'last_success':'2026-12-01','status':'checked'}}}))
            third=json.loads(publish()['payload'])
            self.assertEqual(third['manifest']['asOf'],'2026-09-30')
            # Failed validation leaves the request-time bundle intact.
            before=(root/'public/data/construction/snapshot.json').read_bytes()
            prices['observations']=[];price_path.write_text(json.dumps(prices))
            with self.assertRaises(subprocess.CalledProcessError):publish()
            self.assertEqual(before,(root/'public/data/construction/snapshot.json').read_bytes())

if __name__=='__main__':unittest.main()
