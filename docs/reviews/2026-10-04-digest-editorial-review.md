# October 3 digest: internal Codex editorial review

Candidate: weekly-evidence-2026-10-03-20261003T234449593313Z. Internal Codex editorial audit with a separate adapter reproduction. This is not independent empirical model review. Publication scope: the corrected evidence-only digest; original candidate, frozen model inputs and independent-review gates remain unchanged.

## Verdict

Accept counts only as **records classified by the existing keyword-screen adapters**. All four counts reproduce, and all four equal the frozen counts. They are not counts of new projects, unique facilities, AI investment, or evidence of realized spending. Toronto source identity ambiguity blocks interpreting its apparent cost/duration delta as a longitudinal revision.

Recommended wording:

> Municipal APIs were retrieved on October 3, 2026. Existing keyword-screen adapters retain 17 Edmonton, 13 Vancouver, 53 Toronto and 14 Montréal data-centre candidate records, unchanged from the frozen counts. The broader Edmonton screen adds one server-context record that is excluded from the data-centre count; Vancouver contains historical permit-date corrections. Toronto deduplication collapses records sharing a permit number and revision, so its apparent value and milestone change requires identity review. These are administrative permit proxies, not distinct AI projects or realized expenditure. Montréal's normalized records are unchanged.

No adapter change is necessary to publish this bounded editorial statement. Before promoting Toronto to research/model evidence: verify stable identity includes any necessary permit-type/source-record distinction, detect rather than silently overwrite divergent collisions, and archive original query responses so collision counts and winners can be independently reproduced.

## Reproduction and receipts

All four content hashes and byte lengths match local staged raw payloads and manifests; reported row counts match archived arrays. Edmonton metadata hash and byte length also verified. All four reconstructed CSVs are byte-for-byte identical to staged candidate CSVs; Montréal's staged CSV is absent because it is unchanged, and reconstruction matches canonical CSV byte-for-byte.

| City | Broad rows frozen → candidate | DC classified records frozen → candidate | Candidate issue-date range | Normalized duplicate IDs |
|---|---:|---:|---|---:|
| Edmonton | 85 → 86 | 17 → 17 | 2009-06-19 through 2025-11-12 | 0 |
| Vancouver | 55 → 55 | 13 → 13 | 2017-01-24 through 2026-07-30 | 0 |
| Toronto | 59 → 59 | 53 → 53 | 2006-04-18 through 2023-07-13 | 0 after fetch dedup |
| Montréal | 15 → 15 | 14 → 14 | 1995-10-06 through 2022-10-11 | 0 after fetch dedup |

Receipt retrieval times October3 UTC: Edmonton23:47:32; Vancouver23:47:35; Toronto23:47:36; Montréal23:47:37. Capture dates are verification dates, not dates of all underlying observations.

SHA-256:

- Edmonton:7dbe50868340e79cc1ea1f62dc23b043381309558e95df35ad897bc842f43aea
- Vancouver:1cba64a020f24bc0c11cbca79af5c1f8a4bc10424977269a32a9ac85f607a85e
- Toronto:7c2c48c48c1426b78900f1113bc744ff4d5ed3be09d462e65a6464364b1e61db
- Montréal:873c39acca4358ef20566a8445a275c4e8ed915fa10c09a449c0198df9b24bf8

## Actual record and value differences

- Edmonton: new source_row_id1-667311259, issue2026-09-09, CAD1,600,000 declared estimate, interior alteration, classificationserver_reference_only/candidate_statusserver_reference_context. Excluded from17 DC records; no changed or removed existing rows. No actual AI or facility construction established.
- Vancouver BP-2017-06560 (DCcandidate): issue2018-06-15→2018-11-29; elapsed181→348days; year_month correspondingly changed. CAD43,032,456.65 unchanged. This is administrative issuance timing, not observed construction delay. BP-2021-00719 (excludedfalsepositive): issue2021-04-27→2022-04-14; elapsed57→409days; issueyear/month updated; CAD44,000 unchanged. No new/removed normalized IDs.
- Toronto22 148622 STS|00: frozen winner raw_id390910 Drain and Site Service; new winner raw_id13621 Conditional Permit. Same dedup key but different source identities/types. Output application2022-05-18→2022-10-04; issue2024-04-22→2022-12-07; completion2024-07-02→2024-04-22; duration71→502days; valueCAD1,000,000→missing. These cannot be asserted as revisions to the same permit. No new/removed dedup IDs. Candidate aggregate declared-value proxy falls CAD1million solely due to this winner replacement, not demonstrated cost reduction.
- Montréal: no normalized record/value differences.

All four adapters report zero explicit AI references. Candidate declared-value totals: EdmontonCAD13,339,654; VancouverCAD141,771,751.65; TorontoCAD46,565,000; Montréalcosts unavailable (reported sum0 does not mean zero actual construction cost).

## Query / dedup limitations

Edmonton broad keywordquery is capped50000, captured86, no date filter; normalization retains server-only context and false positives. Vancouverquery combines data-centre text with BulkDataStorage category, capped100, captured55, no date filter. Neither count is a week-specific inflow.

Toronto query only q=data center, limit100, receipt63matches, stored59unique PERMIT_NUM+REVISION_NUM keys. Dictionary last-wins fetch dedup can combine different permittypes. Original63response not archived, only its hash; cannot independently reconstruct all4collisions or confirm candidate count across all underlying63. The resulting53screen count is reproducible, but a distinctpermit count is not.

Montréal three query receipts report7+9+6=22matches, stored15unique id_permis keys. Cross-query duplicate removal uses last-wins; original responses retained only as hashes. Their overlap is consistent with repeated keywordmatches, but exact7duplicate dispositions cannot be reconstructed from the archived envelope. No exhaustive census of facilities or additional languages/phrases established.

Dates are candidate-row min/max issue dates, not dataset coverage boundaries. Multiple permits may relate to one project; proxy metadata does not establish realized spend/labour hours or AI use. Toronto cleared-permit completion milestones are administrative; Edmontonoccupancy fields remain proxies. No geographic competition, enabling costs, public-project outcomes or causal escalation inference supported here.

Structured audit: audit.json. Reproduction script: /tmp/aiio-municipal-audit.py. These are review-supporting local files; no repository changes.

## Public-source cross-check

On October 4, the registered Edmonton, Vancouver and Toronto catalogue pages resolved through the web reader. Montréal’s catalogue returned HTTP 403 to that reader; its October 3 successful API receipt and archived bytes support the historical retrieval claim. No claim of current Montréal website availability is made. Adapter counts and revisions were checked against the pinned raw bytes rather than inferred from catalogue landing pages.

## Publication decision

Approve one corrected evidence-only item. Retain screened counts and actual verification dates with identity limitations. Remove the 456 panel/444 association row claims from this digest: those are derived research artifacts, not newly validated outcomes. Reject AI investment, unique-project, construction-delay and realized-cost interpretations. Raw municipal payloads are locally archived and hash checked but excluded from Git; committed manifests and reports permit hash provenance and normalization checks when those bytes are available. Frozen release and empirical/independent-review gates retain their prior hashes.
