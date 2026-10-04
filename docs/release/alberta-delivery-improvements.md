# Alberta delivery improvements

## Implemented

- Evidence-first home page, fixed-baseline change comparison, source attention, completion-year chart and regional coverage table.
- Existing project scenario at `/project-scenario`, linked from shared navigation; executive currency rounded to one decimal in millions.
- `/delivery` supports region filtering, explicit milestone verification gaps, campus/phase classification, sourced quarterly package records for data centres and infrastructure, regional contractor paid/committed capacity, supplier confirmations and procurement release planning.
- Reviewed action register with owners, dates, status, evidence and substantiated benefits. Draft editor validates and exports updates for review. Drafts are not shared persistent edits; the versioned register is authoritative.
- Procurement benchmark range chart, collapsed source cadence, standalone product copy and year formatting.

## Evidence workflow

`data/governance/alberta-delivery-register.json` is the reviewed record. `npm run delivery:validate` validates it before every production build. Exported drafts can replace this file only after review; then rebuild/deploy. Never mark actions complete without an owner and supporting evidence. Never assign cost or schedule benefits without evidence and a stated basis.

Milestone values are null until sourced. A non-null milestone needs `status`, HTTPS `source`, and ISO `verifiedOn`. Construction-only cost needs `value`, `source`, `verifiedOn`; it is separate from announced investment. `campusId` and `recordKind` require analyst verification; current records are unverified and are not summed as unique campuses.

Package records need `projectId`, `projectName`, `projectKind` (`data_centre` or `infrastructure`), `region`, `trade` (civil/electrical/mechanical/utility/commissioning), `start`/`end` (`YYYY-Qn`), `basis` (`reported`/`inferred`), `source`, and `verifiedOn`. Opening years do not become observed package schedules. Current package coverage is empty.

Capacity records need `contractor`, `region`, `trade`, `quarter`, `paidHours`, `committedHours`, `source`, and `verifiedOn`. Use the same paid-hour definition and time/geography scope; document qualification and mobilization limits at the source. Available hours = max(0, paid minus committed). Do not add overlapping contractor records or treat employment stock as spare capacity.

Supplier records need `supplier`, `equipment`, `specification`, `region`, `slotStatus`, `requiredOnSite`, `leadWeeks`, `freightWeeks`, `testingWeeks`, `source`, and `verifiedOn`. Record quote validity and manufacturing confirmation in the source; confirmation is not inferred from an external benchmark. Latest release subtracts the three durations from required-on-site, excluding design/approval and purchasing administration. No critical-path delay is inferred.

The comparison baseline is `data/governance/alberta-comparison-baseline.json`, initially the published 2026-09-05 bundle. Rebuilds never move it. To compare adjacent releases, the reviewer archives the outgoing published bundle as this baseline alongside the incoming release. Stable project IDs detect additions/removals/revisions; labour, prices, capital and benchmarks are also compared. A removed record is not classified as cancelled. Current evidence remains loaded from the integrity-checked snapshot.

## External evidence still required

Actual financing/permit/utility verification, regional contractor confirmations, package schedules, physical material quantities and supplier available output must be acquired and reviewed. No such commercial evidence is fabricated. Independent calibration/model review remains outstanding; deployment is not approval of causal cost or delay estimates.

This change does not create authenticated collaboration or a shared database. The existing reviewed Git publication process owns authoritative updates. No supplier outreach, credential access or publication is implied by a draft export.

## Verification completed

- Delivery comparison, date arithmetic, capacity missingness and register validation tests: 5 passed.
- Existing planning tests: 14 passed; PowerPoint tests: 5 passed; construction refresh tests passed.
- Research suite: 249 passed.
- Lint, Next.js production build and Sites build passed.
- Local HTTP checks confirmed the overview response; delivery route and legacy-link redirect checked separately. No interactive browser audit or live supplier verification is claimed.
- Changes are prepared in the existing working tree. No new deployment, push or merge was performed for this improvement pass.
