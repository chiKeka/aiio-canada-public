# CAL-3 Phase 1 and South Windsong: bounded Alberta pilot

Evidence cut-off: October 3, 2026. Review-candidate evidence only; no released
model inputs or independent-review verdict are changed by this brief.

The pilot pairs a named AI tenant's portion of CAL-3 Phase 1 with identifiable
site electricity assets and an awarded public school project. It is suitable
for auditing scope, dates, contractual exposure and conditional schedule
sensitivity. Available records do not quantify AI-induced public cost or
establish that the two projects share electrical crews or capacity.

## Source-backed accounting and identity

| Link | Primary evidence | Supported statement | Remaining boundary |
| --- | --- | --- | --- |
| AI phase | [eStruxture, May 14, 2026](https://www.estruxture.com/press-releases/estruxture-announces-coreweave-as-anchor-tenant-for-cal-3-its-landmark-ai-ready-facility-in-alberta) | CoreWeave signed for an unspecified portion of Phase 1 capacity; service targeted second half of 2026. | Tenant share and Phase 1 budget undisclosed; target is not commissioning evidence. |
| Site electrical service | [Operator data sheet, p. 2](https://info.estruxture.com/hubfs/Data%20Sheets/eStruxture_Datasheet_CAL3%20EN%20V2%202025.pdf) | Fortis power provider; multiple 15 MW utility lines feed dedicated electrical lineups; redundant 2N standby topology. | Design disclosure, not measured demand or proof of incremental network investment. Filename does not establish publication day. |
| Standby asset | [AUC current applications](https://www.auc.ab.ca/regulatory_documents/current-applications/) | Application 31020-A001, CAL-3 Emergency Standby Generators, registered August 28, 2026; applicant eStruxture Data Centers. | Application is not approval. Filing and attachments require authenticated eFiling access and were not acquired. |
| CAL-3 identity bridge | [County development notice, p. 2](https://www.rockyview.ca/media/2274) | PRDP20251314 at 200 High Plains Common, file 06412044; data-centre scope. | No retained servicing obligation or incremental road/water/transmission budget. |
| School owner | [Rocky View Schools, June 3, 2025, p. 1](https://www.rockyview.ab.ca/download/513802) | South Windsong school: design complete, EllisDon award, expected spring 2025 start, expected fall 2027 opening, 905 spaces. | Whole-school award does not identify uncommitted electrical/civil scope or repricing exposure. |
| School delivery milestone | [EllisDon, March 31, 2025](https://www.ellisdon.com/news/ellisdon-achieves-financial-close-on-alberta-s-p3-schools-bundle-5-project) | P3 Schools Bundle #5 financial close; consortium design/build/finance/maintenance award includes Airdrie school. | Contractor calls Airdrie K–8; later owner calls South Windsong K–9. Retain publisher-specific labels and reconcile by named project/site. |
| School current status | [Rocky View Schools status](https://www.rockyview.ab.ca/about-rvs/building-our-student-spaces) | Reports construction began spring 2025; site 560 Osborne Drive SW; expected 2027 opening. | Undated page: October 3 retrieval is not a dated progress observation. |

The CAL-3 registry's CAD 750 million refers to the facility envelope, not
CoreWeave's share or Phase 1. The operator's broader CAD 1 billion Alberta
investment claim is not a phase budget. Neither is observed realized expenditure.
The data sheet distinguishes 90 MW total and 70 MW critical design ratings;
these are not the number of 15 MW feeds or generator nameplate capacity.
Secondary reports of standby unit counts, 66.75 MW generation and 45 MW staging
are excluded pending the primary filing.

The [November 2025 County report](https://www.rockyview.ca/media/2672) lists
CAD 24,004,484 for new building scope, while the [April 2026 report](https://www.rockyview.ca/media/3090)
lists CAD 5,149,630 for alteration/improvement scope at the same parcel. These
permit estimates must not be added to each other or to the facility budget
without scope overlap reconciliation. They are neither actual payments nor
separately priced enabling infrastructure.

For the enabling ledger, a service-line/lineup row and standby-application row
can be linked to ABMP_11416/CAL-3. Separate incremental cost, baseline or
already-funded scope, in-service milestones and payer allocation remain
unknown. Fortis as provider does not identify the payer; eStruxture as applicant
does not establish government or ratepayer subsidy. Standby equipment may be
inside AI facility CAPEX, so adding it again would risk double counting.

## Conditional planning contract

A scenario may ask how additional electrical package demand, competing private
work, assumed mobility and scheduling policy change delivery of a protected
school package under specified capacity. Every package duration, normalized
paid-hour requirement and capacity candidate is an assumption until sourced.
Actual electrical hours and relevant contractor capacity are unknown. Proximity
in the Calgary/Airdrie/Rocky View area defines an acquisition candidate, not an
empirically shared workforce pool.

Fall 2027 is an owner opening target with seasonal precision. A numerical
finish month or electrical package deadline must be labelled a scenario bound;
it cannot be converted into a September contractual commitment. Whole-school
award and financial close do not establish remaining uncommitted school scope.
Unknown exposure prevents a school-level CAD escalation or overhead estimate.
Even a modeled schedule impact would depend on package sequencing, procurement
windows and contract risk allocation that have not been acquired.

## Reproducible scenario sensitivity

The [frozen threshold artifact](../../data/pilots/alberta-cal3-windsong-thresholds-v0.1.json)
contains 1,620 discrete cases across ten capacity candidates (including unknown),
six AI release shifts, three private-demand multipliers, three mobility additions
and three allocation policies. It pins the evidence contract, implementations
and source hashes. The cases, threshold groups and file hashes were independently
reproduced from the same input; this establishes computational reproduction,
not empirical calibration or independent model approval.

The full-grid assumptions use school work 100, other private work 50 and AI work
100 normalized paid-work units; January 2026 releases; a school protection bound
at month 20 (September 2027); and a 36-month horizon. September is a scenario
interpretation of fall, not a school contract date. The UI's smaller, selected-
control grid is exported separately and must not be mistaken for this full grid.

At private multiplier 1, no mobility and no AI shift:

| Assumed base supply (units/month) | Pro-rata school completion, without / with AI | Scenario incremental delay | School target with AI |
| --- | --- | --- | --- |
| Unknown | Unknown / unknown | Unknown | Unknown |
| 7.5 | Month 20 / month 34 | 14 months | Not met |
| 10 | Month 20 / month 25 | 5 months | Not met |
| 12.5 | Month 20 / month 20 | 0 months | Met |

The minimum successful **tested** base supply is 12.5 units/month for pro-rata
and AI-first policies at zero shift. Protecting background work lowers it to
7.5, while also protecting other private work; it is not a public-only policy.
With five assumed mobility units/month, pro-rata's minimum tested base supply
falls to 7.5, meaning **12.5 total** units/month. Neither value measures available
workers, spare capacity, contractor shortages or an optimum between grid points.
The artifact's reference supply of 10 is an assumed scenario reference, so its
additional-supply fields are not gaps from measured regional supply.

Staggering is not uniformly beneficial in this implementation. For pro-rata,
private multiplier 1 and zero mobility, the tested base-supply thresholds for
AI shifts of 0, 3, 6, 9, 12 and 21 months are respectively 12.5, 15, 15, 20, 20
and 7.5. Shifting releases changes overlap with the assumed school workload;
all packages preserve their total work. A 21-month shift places AI releases
after the protected school bound and misses the assumed 2026 AI phase window.
It cannot be presented as an evidenced feasible mitigation. Finite horizon
non-completion retains tail work rather than treating it as complete.

Dollar escalation and overhead remain null in every pilot case because the
school's exposed uncommitted amount and contractual basis are unknown. The
scenario has no conversion from normalized units to actual paid hours, workers,
CAD or probability. The unknown-capacity default remains unknown even when
mobility is assumed; an assumed addition cannot establish unknown base supply.

## Validation and later causal research

The frozen public-proxy comparison remains approximately **2.35% worse than
baseline-only on held-out MAE**. Named sources do not reverse that result or
validate a new executive cost estimate. See [the frozen comparison](../methodology/full-schedule-proxy-comparison.md)
and [pending-review validation packet](../methodology/narrow-planning-validation-packet.md).
The packet keeps independent review pending and makes no reviewer verdict.

A later causal study would require dated phase and enabling-asset vintages,
priced scope, payer commitments, realized trade demand and capacities,
project-specific procurement/outcome panels and an identified comparison design.
A school opening target is not actual delay; a registered generator application
is not completed supply; observed project accounting is not a causal estimate.

## Receipts and acquisition gaps

Field claims derive from the primary source notes, retained bytes and hashed
receipts in `data/review-candidates/alberta-pilot-2026-10-03/sources/`:
[enabling-source notes](../pilot-enabling-source-notes.md) and
[public-project source notes](../pilot-public-source-notes.md).
Successful retrieval proves acquisition, not historical page availability.
Raw source redistribution remains review-gated; receipt provenance does not
promote these candidates to release evidence.

The actionable next documents are the AUC filing/decision; Fortis connection
agreement or priced upgrade scope; County servicing conditions; Phase 1 scope
and package calendar; the named school's electrical/civil bid, award and
installation records; exposed remaining scope and escalation/risk-transfer
terms; and evidence of genuinely overlapping trade demand and relevant supply.
Authenticated filing access and independent review remain external blockers.
No third parties were contacted and no costs, payer shares or reviewer decisions
were supplied by inference.

## Follow-up primary evidence (October 3, 2026)

The evidence ledger now includes the County’s actual CAL3 permit conditions: meter payment by the Applicant/Owner, conditional extra service-capacity purchases beyond the preallocated 2.56m³/day, water/wastewater ties and pre-occupancy offsite-servicing requirements. These obligations are scoped charges and prerequisites, not a priced enabling-asset budget or proven Phase 1 allocation. Whole-asset costs and ultimate payer shares remain unknown. See [permit and Fortis follow-up](../pilot-enabling-source-followup.md).

South Windsong’s official $64.3m estimated whole-project envelope and the owner’s DBFM responsibilities are captured. Province financial statements identify September 2027 bundle completion/payment-start timing (issuer-primary web extract only, full retrieval403). These do not price the school electrical package or remaining uncommitted public exposure. The governing agreement and schedules could not be retrieved. See [contract follow-up](../pilot-public-source-followup.md).

JobBank reports approximately 6,290 Calgary installation electricians and 88% construction employment share; workforce baseyear is unspecified. Historical shortage and forward outlook periods are preserved separately. No public source establishes actual paid-hour availability, contractor backlog or a site-specific crew overlap. Stock is not converted to capacity. See [capacity follow-up](../pilot-capacity-source-followup.md). Scenario results remain unchanged after these contextual additions.
