# South Windsong P3 cost and contract follow-up

Review-only follow-up acquired October 3, 2026. This supplements
[pilot-public-source-notes.md](pilot-public-source-notes.md); it changes no
canonical data contract or published output. Sources and attempts are preserved
under `data/review-candidates/alberta-pilot-2026-10-03/sources/public-followup-*`.

## What is now verified

The [official Alberta Major Projects South Windsong school record,
11248](https://majorprojects.alberta.ca/details/New-K-8-School-in-Windsong-SW-Airdrie/11248)
identifies a 2025–2027 construction schedule and **$64.3 million estimated
project cost**, with Alberta Infrastructure as developer, EllisDon
Infrastructure Alberta P3SB5 General Partnership as contractor, and GEC
Architecture as architect. This is a school-specific estimated project envelope.
It is not an observed final outturn, priced electrical package, remaining
uncommitted amount, escalation allowance or evidence of a cost attributable to
CAL3. The page does not establish the estimate's price basis or scope inclusions.
The downloaded HTML was checked for the amount, schedule and P3SB5 identity.

The [Alberta Infrastructure P3 overview](https://www.alberta.ca/public-private-partnerships)
identifies the southwest Airdrie school within the six-school bundle contracted
with Ellis Don Infrastructure in March 2025. It sets out DBFM delivery,
anticipated 2027 opening and maintenance through September 2057; the school
jurisdictions own the schools, while Alberta monitors contractor performance.
This is direct public-owner confirmation of delivery responsibilities and the
bundle timeline. It does not disclose which party bears a particular inflation,
change-order or delay cost.

The Province's [2024–25 annual report filed with the US
SEC](https://www.sec.gov/Archives/edgar/data/810961/000119312525155469/d52186dex991.htm),
consolidated financial statements Note 8, corroborates the P3SB5 counterparty,
March 2025 contract month, September 2027 scheduled completion and September
2027 start of capital payments. These are bundle-level scheduled milestones,
not dates of school-specific electrical work or observed completion. The report
is issuer-primary material on a regulator host; its relevant facts were read
through the web tool and retained as `web-extract.json`. Direct full-HTML
retrieval returned HTTP 403, explicitly preserved in its receipt.

| Acquisition item | Captured evidence | Permitted interpretation |
| --- | --- | --- |
| School estimate | Project 11248, $64.3m | School-specific estimated envelope, basis unresolved |
| Governing bundle | Southwest Airdrie listed in March 2025 EllisDon DBFM bundle | Named asset is inside awarded bundle; do not classify entire school as uncommitted |
| Financial/payment timing | Provincial report Note 8: completion/payment start September 2027 | Bundle schedule context, not an electrical installation window |
| Ownership/maintenance | Jurisdiction owns; private partner maintains through September 2057 | Responsibility context; not a verified escalation-risk allocation clause |
| Remaining exposed public scope | No quantified amount established | Unknown; neither zero nor the full estimated project cost |
| Civil/electrical pricing dates | No dated subaward record established | Unknown; whole-contract month cannot replace package procurement window |
| Price index/escalation mechanism | Governing schedules unavailable in this acquisition | Unknown; do not apply CPI/BCPI automatically |

## Governing documents identified, contents not obtained

Alberta's official P3 overview links the following 2025 bundle documents:

- [Value-for-money assessment and project report: public-private partnership
  bundle of six schools](https://open.alberta.ca/publications/value-for-money-assessment-and-project-report-public-private-partnership-bundle-of-six-schools).
- [Agreement to design, build, finance and maintain six new schools in
  Alberta](https://open.alberta.ca/publications/agreement-dbfm-six-new-schools),
  including the indexed [main agreement
  resource](https://open.alberta.ca/publications/agreement-dbfm-six-new-schools/resource/4c79a5db-419a-456a-9bba-b6db6e2c5c6a).
- [RFQ](https://open.alberta.ca/publications/request-for-qualifications-design-build-finance-maintenance-seven-new-schools)
  and [RFP](https://open.alberta.ca/publications/request-for-proposals-design-build-finance-maintain-seven-new-schools).
  Their URL labels say seven schools, whereas the awarded overview says six.
  Their contents must be checked before reconciling procurement scope or dates.
- Indexed [Schedule 17 —
  Subcontractors](https://open.alberta.ca/dataset/0523e484-16d3-403d-9db2-c2092fb536dc/resource/da729c0c-636d-479d-9ed0-7a5d0dbe71da/download/infra-agreement-dbfm-six-new-schools-2025-schedule-17.pdf).
  The title alone does not establish contractor names, award dates, prices or
  remaining uncommitted work.

The catalog endpoints returned HTTP 403 to the web tool. Direct main-agreement,
Schedule 17 and value-for-money retrieval attempts timed out in the local
acquisition; those failed receipts contain no raw-document hash. Identification
of the governing document is verified by the captured owner's links. Its
clauses, financial schedules and monetary risk allocations are **not verified**.
No generic P3 risk-allocation assumption is promoted into a governing fact.

The similar 2026 six-school agreement belongs to Concert-Bird's Bundle #6,
including Bayview, and must not be substituted for EllisDon Bundle #5. Older
2019/2021 school-bundle value-for-money reports likewise cannot establish the
2025 South Windsong payment or risk-transfer rules.

## Reviewable model treatment

Retain $64.3m only as `estimated_project_envelope` with the October 3 retrieval
and official URL. Retain scheduled September 2027 bundle completion/payment
start separately from the board's school opening target and private CAL3
milestones. Keep `exposed_cost`, priced-package amount, installation windows,
indexation and payer liability unknown until the agreement and applicable
change/risk provisions or procurement records establish them. An awarded DBFM
bundle is evidence that responsibilities have been contracted; it does not prove
that every future price increase is borne by government or that government has
no residual exposure.

Once accessible, review the executed agreement's definitions and payment/change
schedules together: fixed construction payment, service-payment indexation,
variation/change-in-law/relief/compensation events, completion/delay remedies,
site services and owner exclusions. Then reconcile school-specific allocation
against the six-school aggregate. Bundle totals cannot be divided equally or
allocated by school count without a documented rule.

## Receipt verification

Successful downloaded source hashes:

- `public-followup-p3-overview/page.html`:
  `39eea9dd536b5387db377f8c5181c6a574dfb061b7e58550512afddb5947e1f3`.
- `public-followup-windsong-cost-estimate/page.html`:
  `d2e748df8c53196f2481ba239443f43672bc8974d2b35988b77b7dcc3677da85`.

The issuer-primary web extract has its own hash in the SEC receipt; it is not
presented as a hash of the unavailable full annual-report download. No third
party was contacted, and no paywall, account or private authorization was used.
