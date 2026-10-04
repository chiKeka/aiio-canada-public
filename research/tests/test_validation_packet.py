import copy
import json
import unittest
from pathlib import Path
from aiio.validation_packet import build_packet, verify_packet, resolve_overlap, align_milestones, check_rolling_origin, OUTPUT
from aiio.schemas import ValidationError
ROOT = Path(__file__).resolve().parents[2]

class ValidationPacketTests(unittest.TestCase):
    def test_packet_reproduces_frozen_inputs_and_withholds_authorization(self):
        packet = build_packet(ROOT)
        self.assertEqual(packet, json.loads((ROOT / OUTPUT).read_text()))
        verify_packet(ROOT, packet)
        self.assertFalse(packet['validated_estimate_allowed'])
        self.assertIsNone(packet['independent_review']['verdict'])
        self.assertEqual(packet['thresholds']['minimum_mae_improvement_fraction'], .05)
        self.assertFalse(packet['arms']['combined']['checks']['improvement_over_baseline'])
        tampered = copy.deepcopy(packet)
        tampered['input_manifest'][next(iter(tampered['input_manifest']))] = 'sha256:wrong'
        with self.assertRaises(ValidationError): verify_packet(ROOT, tampered)

    def test_overlap_requires_scope_evidence_not_facility_candidate(self):
        records = [{'id':'P','kind':'project','amount_cad':100}, {'id':'B','kind':'permit','amount_cad':25}]
        unknown = resolve_overlap(records, [{'permit_id':'B','project_id':'P','status':'candidate'}])
        self.assertEqual((unknown['union_lower_cad'],unknown['union_upper_cad']), (100,125))
        self.assertEqual(unknown['status'], 'unresolved')
        link = {'permit_id':'B','project_id':'P','status':'confirmed_included_scope','evidence':'publisher budget scope'}
        resolved = resolve_overlap(records, [link])
        self.assertEqual(resolved['excluded_ids'], ['B'])
        self.assertEqual(resolved['union_upper_cad'],100)
        del link['evidence']
        with self.assertRaises(ValidationError): resolve_overlap(records,[link])
        with self.assertRaises(ValidationError): resolve_overlap(records + [records[0]], [])

    def test_permit_is_not_construction_milestone(self):
        self.assertEqual(align_milestones('2024-01-01','2026-12-31',[{'kind':'permit_issue','date':'2024-05-01','evidence':'permit'}])['status'],'not_assessed')
        report = align_milestones('2024-01-01','2026-12-31',[{'kind':'construction_start','date':'2024-01-11','evidence':'dated official update'}])
        self.assertEqual(report['milestones'][0]['deviation_days'],10)
        self.assertFalse(report['expenditure_timing_validated'])

    def test_backtest_rejects_future_information_and_duplicate_rows(self):
        row={'target_quarter':'2025-Q2','information_cutoff':'2024-Q4','forecast_origin':'2025-Q1','training_end':'2024-Q4','geography_id':'AB','asset_class':'hospital'}
        self.assertEqual(check_rolling_origin([row])['status'],'pass')
        with self.assertRaises(ValidationError): check_rolling_origin([row,row])
        row['training_end']='2025-Q1'
        with self.assertRaises(ValidationError): check_rolling_origin([row])
