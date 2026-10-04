# CAL-3 Phase 1 enabling-asset source notes

Research cut-off: October 3, 2026. Analyst intake only; publication and independent review remain pending.

CAL-3 has a defensible project-specific electricity-enabling link: the operator
identifies Fortis utility lines feeding dedicated electrical lineups, and the
AUC public applications table identifies its emergency standby-generator
application. Neither establishes an incremental public investment, a separate
asset budget, or a cost allocation to ratepayers. Use unknown amounts and payer
shares rather than allocating a percentage of the data-centre capital estimate.

## Field-level primary evidence

| Primary record | Dated evidence and permitted interpretation | Cost/payer limit |
| --- | --- | --- |
| [eStruxture CAL-3 data sheet, V2 2025, p. 2](https://info.estruxture.com/hubfs/Data%20Sheets/eStruxture_Datasheet_CAL3%20EN%20V2%202025.pdf) | Address 200 High Plains Common; Phase 1 building 205,000 sq. ft. and six halls. Fortis is the named power provider. Service comprises multiple 15 MW utility lines serving dedicated electrical lineups. Backup equipment uses redundant 2N topology. This identifies site-linked distribution/service and standby assets as operator-reported design specifications. | No line count, line/substation asset ID, connection agreement, incremental/baseline split, separate budget, committed payer shares, or energization certificate. The sheet labels 90 MW total and 70 MW critical power; these are design ratings, not measured load. Its filename is not proof of a particular publication day. |
| [AUC current applications](https://www.auc.ab.ca/regulatory_documents/current-applications/) — public table `6266`, captured October 3 | Exact record: application `31020-A001`, proceeding `31020`, applicant eStruxture Data Centers, description CAL-3 Emergency Standby Generators, registration August 28, 2026. The captured table JSON is bound by its receipt, and a one-record extract is retained. | Registration establishes an application, not approval, operating authorization, installed quantity, or a budget. No asset cost/payer split appears in this table. |
| [Rocky View County approved development permits, p. 2](https://www.rockyview.ca/media/2274) | `PRDP20251314`, file `06412044`; office/warehouse accommodating a data centre at 200 High Plains Common, Lot 12, Block 7, Plan 2410651; NE-12-26-29-W4M. The notice gives July 8, 2025 as the appeal deadline. | The notice supplies the site/scope identity bridge. It does not provide a road, water, transmission or substation obligation, servicing agreement, or project-specific public budget. |
| [County November 2025 construction report, issued December 4, 2025, p. 1](https://www.rockyview.ca/media/2672) | `PRBD20255100`; same address/file/parcel; new-construction warehouse/storage classification; 27,263 m²; construction value CAD 24,004,484. Row alignment was visually checked against the PDF. | Permit construction value is a particular building scope estimate. It is not paid expenditure, the total CAL-3 budget, or an enabling-asset budget. |
| [County April 2026 construction report, issued May 5, 2026, p. 1](https://www.rockyview.ca/media/3090) | `PRBD20258056`; same address/file/parcel; alteration/improvement; 4,020 m²; construction value CAD 5,149,630. Row alignment was visually checked against the PDF. | Distinct work class and area. Do not sum this with the preceding permit or the whole-project estimate until overlap/scope reconciliation is available. |
| [eStruxture tenant announcement, May 14, 2026](https://www.estruxture.com/press-releases/estruxture-announces-coreweave-as-anchor-tenant-for-cal-3-its-landmark-ai-ready-facility-in-alberta) | CoreWeave is announced as anchor tenant for an unspecified portion of Phase 1. Target service remains the second half of 2026. | Tenant capacity, construction expenditure, and enabling-asset costs are undisclosed. The broader Alberta investment statement does not revise a comparable CAL-3-only budget. |

## Safe pilot ledger interpretation

Two linked rows are supportable: `CAL3_FORTIS_SERVICE_LINEUPS` (distribution
connections and dedicated lineups, operator design disclosure) and
`CAL3_STANDBY_GENERATORS_31020` (standby facility application, regulator register).
Link both to CAL-3/`ABMP_11416` at the exact site. Leave separate cost, committed
shares, incremental scope and in-service milestones unknown. Fortis as provider
is not evidence that Fortis, ratepayers or government ultimately pay. Likewise,
eStruxture as applicant does not settle financing or reimbursement arrangements.

Standby equipment plausibly belongs inside the data-centre package; that is an
unresolved scope classification, not authority to add another cost to AI CAPEX.
No site-specific road/water expansion or new transmission/substation obligation
was acquired. Same geography does not establish shared crews or displacement of
hospital, school or road work. CAL-3 is adequate for a narrowly labelled link and
milestone audit, but not an empirical public-cost pass-through estimate.

## Primary-access blocker and withheld claims

The AUC site directs application access through its eFiling service. Following
the official link redirected to authentication, so the application and
attachments were not acquired. A secondary discovery page reports 21 standby
units/66.75 MW and staged 45 MW load, but those figures are deliberately excluded
from the primary-verified pilot fields pending the actual filing. Do not replace
the operator's design rating with an unverified application number.

The government Major Projects description says 90 MW generation component,
whereas operator material distinguishes total power and backup equipment. That
inventory phrase alone cannot resolve generation nameplate, continuous supply,
or approvals. Keep design load and generator capacity separate.

The missing documents are the `31020-A001` facility filing/attachments and any
AUC decision, Fortis site connection agreement or project-specific upgrade
record, County development-permit conditions/servicing agreement, and occupancy
or commissioning certificates. No account was created, no credentials changed,
and nobody was contacted.

## Retained evidence

`data/review-candidates/alberta-pilot-2026-10-03/sources/` contains seven successful
acquisition receipts, the AUC application extract and locally retained raw files.
Raw files are ignored from Git pending redistribution review. Receipts bind URLs,
retrieval times, bytes and SHA-256 hashes; they do not establish historical page
contents. The County tables and operator data sheet were rendered and visually
checked. No new source was promoted into released model inputs.
