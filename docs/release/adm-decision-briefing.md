# ADM decision briefing

The revised deck has 13 core slides plus all 49 Infrastructure-developer overlap records and all 19 core data-centre records in appendices. The dated inventory does not prove legal ownership or current package phases. The developer match is exact and incomplete schedules remain outside the overlap count.

Shared calculations live in `lib/adm-analysis.mjs`; `components/adm-decision-brief.tsx` presents them on the home page. `scripts/build-adm-evidence.py` derives the Infrastructure exposure and enabling-power screen from canonical CSVs, called by the construction publisher. AESO process statements remain reviewed, dated references and are not silently refreshed.

Low/high labour cases assume pipeline realization 25/75%, construction share 30/50%, labour share 30/40%, paid-hour cost $100/$80, five years, 1,840 paid hours per FTE-year and electrician/HVAC payroll shares of 20/10%. These are analyst stress assumptions, not calibrated productivity data. Gross average FTE is neither net hiring nor a shortage. The historical workforce denominator provides scale only. No peak date is inferred.

Capital-plan stress is plan × exposed share × price movement. Component rows independently apply the observed movement to 25% of the plan; they are not summed. The 10% illustrative shock yields $106.87M, $267.175M and $534.35M at 10%, 25% and 50% exposure. This is not an AI-attributable premium and is not an addition to a baseline already containing the same inflation.

The decision deck is a dated, reviewed artifact, separate from the existing dynamic evidence-only export. The dashboard hides its download link if the construction snapshot revision, shared analysis results or ADM evidence change. Regeneration requires the presentation source in `presentation-work/alberta-adm/build.mjs` and visual inspection, followed by publishing an updated download receipt. Do not relabel the existing dynamic evidence-only endpoint as the new decision deck.

Visual review covered all rendered slides, with a correction to the closing table and short final appendix page. Native tables and three charts passed structural/layout checks. This was not a native PowerPoint application test. New calculation tests and construction refresh regression tests passed; application production build passed. No deployment was performed in this revision.
