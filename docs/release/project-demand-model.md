# Project-resolved labour demand

Supersedes the five-year aggregate labour sizing on slides 5–6 and the dashboard. `lib/project-demand-model.mjs` resolves each costed phase into separate source and model schedules. Monthly triangular package allocations conserve full project trade hours. Annual outputs and regional/project contributions retain the input basis. Electrical and HVAC peaks are calculated independently.

Current coverage: seven costed records, three with at least one reported date, four with assigned starts. Twelve missing-cost records remain unquantified. All costed phases proceed in every intensity case; the model does not estimate a probability of delivery. This differs from the previous partial-realization aggregate sensitivity and explains why the new conditional peak is higher.

Model parameters: low/central/high construction shares 30/40/50%, labour shares 30/35/40%, loaded hourly costs $100/$90/$80; electrician/HVAC payroll shares 20/10%; 1,840 paid hours per FTE-year. Default duration 36 months, undated start evidence month +18 months, January/December year conventions. Past proposed starts shift to evidence month. Electrical work spans 25–100% of the field period, HVAC 30–100%, with normalized triangular activity. All of these are explicit, uncalibrated coefficients or timing conventions. A common start for undated projects can concentrate demand and must be checked against actual milestones.

The 2027–2036 run separates pre-horizon, in-horizon and post-horizon electrical hours. Charts display 2027–2032; their tail describes this cohort, not absence of future activity. Central electrical peak ~3,940 annual FTE in 2029; central HVAC peak ~1,926 annual FTE in 2030. These are conditional model results, not confirmed market peaks or workforce shortages.

`/api/construction/demand` returns the model with its evidence revision, schedule register, scenarios and contributions. Dashboard and deck share the same model function. The dated deck download is guarded against changed inputs/results. Four model tests cover conservation, date shifts, missing costs and schedule provenance; application build passed. Native deck tables/charts passed package/layout checks and changed slides were visually inspected. No production deployment or empirical calibration was performed.

## ADM risk review, 6 September 2026

`project-demand-2` and `lib/demand-risk-analysis.mjs` supersede the single-peak framing above. The full-realization case remains an explicit scheduling stress, with annual electrical demand split between reported-year anchors and wholly fallback-scheduled phases. The latter account for $32B. Two independent central-intensity sensitivities show 50% proposed-project volume (construction-stage volume retained), and 48-month durations for wholly undated phases. Neither is a probability forecast. Extending duration conserves hours and changes their timing; reported Malachite dates remain unchanged.

The central HVAC and electrician peaks are 62% and 29% of their respective historical 2021 employed stocks. At half proposed volume, these become 31% and 15%. At 48 months, the peaks are about 1,813 HVAC FTE and 3,503 electrician FTE, both in 2030. Historical stock is not available capacity. Seven Infrastructure-developer records with reported schedules intersect the base stress window, 2029–2030. Municipality pairings are an analytical proximity screen, without allocating multi-location programme costs or claiming shared contractors.

Final outputs: `Alberta_ADM_Decision_Briefing_Risk_Review.pptx` (13 slides) and `Alberta_ADM_Evidence_Appendix_Risk_Review.pptx` (14 slides). Slide 8 explicitly distinguishes the $10.687B provincial plan from Infrastructure's unconfirmed uncommitted envelope and gives a $25M-per-$1B sensitivity at 25% exposure and a 10% shock. The dashboard and JSON export include the same risk calculations; both deck links are guarded by the evidence/model signature. Source mojibake is corrected in display/export while raw records remain intact.

Verification: focused model tests, targeted typed lint, production build, native package/layout checks, rendered review of both decks and XML malformed-text scan. No deployment or empirical calibration performed.

Local production smoke check also passed: home page, three-case risk API with seven intersecting records, matching current deck signature, and both PowerPoint downloads returned successfully. Temporary verification server stopped afterwards.
