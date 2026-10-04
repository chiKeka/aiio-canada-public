# Executive assessment records

Open **Brief** to review the current assessment. **Print / Save PDF** prints the brief; **Download snapshot** saves a JSON envelope on the user's device. No project information is uploaded by this feature.

The snapshot contains project inputs, monthly prices, monthly cash flows and totals, selected month/driver, scenario graph output, evidence context and sources, planning limitations, and the pinned comparison. It is detached from subsequent dashboard edits. Missing results disable export; different price bases withhold the comparison delta.

Verify a downloaded snapshot from this repository:

```sh
npm run snapshot:verify -- path/to/aiio-assessment-snapshot.json
```

The verifier checks SHA-256 over the exact UTF-8 `payload` string and recomputes the cash flow from the stored monthly prices and spending profile. It does not execute the payload. The checksum detects accidental changes; it is not a signature, source authentication, calibration approval, or causal validation. Someone who changes a record can also recompute its checksum.

This is a preserved output record, not an executable historical model archive. The included research-release manifest identifies the underlying release, not the application's current Git commit. The schema and cash-flow contract identify the record/calculation formats. A future incompatible calculation contract must fail verification until explicitly supported.

**Share inputs** remains a convenient editable URL. It does not preserve outputs, pinned comparisons, or a historical model, and may produce different results after data or code updates. Retain the downloaded snapshot with the printed brief for a fixed record.

Run `npm run test:planning` for record/reconciliation checks and `npm run test:executive` against a running production application (default `http://127.0.0.1:3002`) for the interaction/export workflow. The latter runs in the release quality gate.
