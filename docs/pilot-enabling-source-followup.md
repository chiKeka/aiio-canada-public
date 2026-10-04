# CAL-3 public enabling-source follow-up

Research capture: 2026-10-03 UTC. Candidate evidence only; no released-data update, new observed Phase 1 budget, causal claim, or independent-review verdict.

## Actual municipal conditions

[County planning package](https://gis.rockyview.ca/planning/PRDP/PRDP20251314_Online_Package.pdf), source `FOLLOWUP_COUNTY_CAL3_PLANNING_PACKAGE`, SHA-256 `ae7965236a50083e05e13cb5b1ba029a0d231514588f0245093d55b33343f4d7`. Printed pages and condition numbers:

| Page / condition | Supported field / allocation | Limit |
|---|---|---|
| 2 / 6 | Applicant/Owner pays meter and remote-transmitter supply/installation before permit release. | Amount and payment unverified. |
| 2 / 8 | Parcel allocation: 2.56 m³/day, subdivision PL20230084 Phase 5b. Owner buys additional capacity if expected demand exceeds allocation. | Actual demand/purchase unknown. |
| 3 / 9, 11 | Wastewater and potable-water designs tie into High Plains Industrial Park; water includes fire protection and assessment of pressure-reduction/backflow needs. | Installed assets/costs unknown. |
| 3–4 / 15 | Applicant/Owner funds required traffic-assessment updates. Offsite-improvement recommendations trigger an Owner development agreement. | Road works and allocation remain conditional. |
| 4 / 17 | Necessary Phase 5b offsite underground/surface infrastructure and County construction-completion certificates precede occupancy. | Construction payer and completion unknown. |
| 5 / 21 | Owner water/wastewater service agreement precedes occupancy/connection; Applicant pays additional capacity if needed. | Agreement/amount unknown. |
| 5 / 26.i | Owner bears construction road-mud cleanup cost. | No priced commitment. |

The package is explicitly a decision notice, not an issued permit. Its first-page February 11, 2025 date conflicts chronologically with later drawing dates; notification is June 17, 2025. Retain both; do not infer final-approval date.

The exact public [County permit-layer query](https://atlasmap.rockyview.ca/arcgis/rest/services/DevMaps/Development_Permits/MapServer/0/query?where=PermitNumber%20%3D%20%27PRDP20251314%27&outFields=*&returnGeometry=false&f=json) links the package and matches parcel roll 06412044, Lot12/Block7/Plan2410651. Its captured status is `Closed-Approved`, stage `Closed`; these administrative labels are not construction/occupancy completion. Source `FOLLOWUP_COUNTY_CAL3_PERMIT_RECORD`, hash `e77981f0e712502d181df477135fdbb7fe3a88871ccf417aa0e2b9283c254c8a`.

Suggested candidate asset identities: `cal3-phase1-site-water-service`, `cal3-phase1-site-wastewater-service`, `high-plains-phase5b-offsite-servicing`. Link them through the permit and parcel. Keep offsite baseline allocation separate from incremental additional capacity. Meter payment is an explicit applicant/owner obligation; additional-capacity payment is conditional; offsite construction payer is unknown. No dollar commitment, named public subsidy, or measured competing demand is established.

## Electricity allocation context

[FortisAlberta 2026 terms](https://www.fortisalberta.com/docs/default-source/default-document-library/2026-customer-terms-and-conditions-of-electric-distribution-service.pdf?sfvrsn=932f981b_6), effective January 1, 2026, approved AUC Decision 30274-D01-2025. Source `FOLLOWUP_FORTIS_CUSTOMER_TERMS_2026`, hash `cb5d808fd5372cd7974ca7ae6d1d5efbe204ca45d049880eba1ce6e21260b7f4`.

Section 7.2.1, printed pages 29–30, calculates customer distribution contribution from extension costs, shared costs and Fortis investment. Extension facilities serve an individual customer; shared costs for demand ≥100kW include proportional shared facilities and attributable system upgrades. Section 7.2 generally requires distribution contributions before design/procurement/construction unless agreed otherwise. Section 7.2.2, pages 30–32, assigns requested optional facilities and prepaid maintenance to the customer; transmission contribution may apply above 2MW, with rules differing between new single/shared delivery points and expansion. This does not establish CAL-3's applicable delivery point, tariff, contract, investment term or contribution.

[Fortis contribution guide](https://www.fortisalberta.com/docs/default-source/default-document-library/2026-fortisalberta-contribution-program.pdf?sfvrsn=9d2d981b_7), source `FOLLOWUP_FORTIS_CONTRIBUTION_GUIDE_2026`, hash `4d3215dc47142604d14f2c739efb09f5bd8acd32a024d3aab3b24a52729a5733`. Printed pages 3–4 explain that Fortis investment is recovered through rates across customers; Fortis retains facilities on its side of the service point even where a customer contributes. The guide excludes Rate65 transmission-connected service and does not override formal terms/calculations. Classify as governing-context evidence, never an observed CAL-3 payer split.

## Public searches and remaining evidence

- AUC current-applications record 31020-A001 establishes registration August 28, 2026 of CAL-3 emergency standby generators. Existing receipt `auc-current-applications-data.manifest.json` remains authoritative for that limited claim.
- [AUC recent updates](https://www.auc.ab.ca/regulatory_documents/recent-updates/) exposes public Ninja table6253. Captured 1,100 rows yielded no `31020` or `estruxture` matches. `followup-auc-recent-updates-search.json` records the scope and no-match result. This is neither a complete eFiling search nor proof of no approval. The official eFiling destination redirects to authentication; no credentials/private access used.
- County advertised notices last three weeks. Its linked ArcGIS experience exposes a public webmap, permit schema and exact-record planning-package URL; receipt chain retained below. No need to infer expired notice availability.
- Public operator/utility/County searches found no signed CAL-3 utility connection contract, capacity-service agreement, development agreement, traffic assessment, issued occupancy certificate, construction-completion certificate or priced enabling-work tender. Discovery search was subsequently rate-limited (HTTP429); absence is limited to searched public routes.
- [Western Electrical projects](https://www.westernelectrical.com/projects/) names Q9 CAL2/CAL3 beginning in 2007, a different project. Receipt `FOLLOWUP_CONTRACTOR_NAME_COLLISION` preserves the disambiguation; do not assign that contractor to eStruxture CAL-3.

Required external documents to resolve actual allocations: CAL-3 connection/service agreements and estimates; approved water/wastewater capacity agreement and meter amount; Phase5b servicing agreement/as-builts and completion certificates; any CAL-3 traffic assessment and executed development agreement. Public evidence supports conditions and dependencies, not whether they were discharged or how costs were financed. No third parties contacted.

## Receipt verification

All ten new `followup-*.manifest.json` receipts verified against exact local raw bytes (SHA-256 and length). Raw captures remain ignored under existing receipt-only redistribution policy. Public schema/configuration/query bodies and recent-index extracts are captured, not only browser snippets. PDF page4 municipal conditions and page30 Fortis terms visually checked alongside text extraction.

Receipts under `data/review-candidates/alberta-pilot-2026-10-03/sources`:

- `followup-fortis-customer-terms-2026.manifest.json`
- `followup-fortis-contribution-guide-2026.manifest.json`
- `followup-auc-recent-updates.manifest.json`
- `followup-auc-recent-updates-data.manifest.json`
- `followup-contractor-name-collision.manifest.json`
- `followup-county-planning-map-config.manifest.json`
- `followup-county-planning-webmap.manifest.json`
- `followup-county-permit-layer.manifest.json`
- `followup-county-cal3-permit-record.manifest.json`
- `followup-county-cal3-planning-package.manifest.json`
