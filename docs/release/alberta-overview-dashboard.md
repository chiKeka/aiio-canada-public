# Alberta overview dashboard

Construction now opens on **Alberta overview**. This view presents all metrics in the Alberta delivery presentation: project counts and stages, reported investment and missing-cost coverage, reported completion years and missing-date coverage, the complete project register, the current-year capital plan, six occupation employment/vacancy observations, recruitment/entrant/retirement/shortfall forecasts, all eight Calgary/Edmonton component price changes, six competing infrastructure categories and combined schedule overlap, and eight equipment lead-time ranges.

The civil/electrical/mechanical/utility intersections, schedule/cost pathways, mitigation trade-offs and delivery priorities also appear as tables and cards. Qualitative guidance is shared between the dashboard and PowerPoint through `docs/research/alberta-delivery-guidance.json`, published in the briefing evidence file. Project aggregates use `lib/alberta-evidence-summary.mjs` in both consumers. All other metrics use the same published benchmark and briefing inputs. Refresh these with `npm run construction:publish` and rebuild/deploy; exports do not refresh research themselves.

Source links, periods, units, vacancy quality flags, missing values and interpretation limits appear alongside the relevant metrics. Definitions explain the aggregates and changes. Evidence is rendered on the server and passed into the existing tabbed workspace; no presentation/ZIP library is shipped into the dashboard client. The scenario model remains in its own tab and cannot change the evidence overview.

Validation: the local browser test checks all presentation headline metrics, every price component, full inventory coverage, analytical-table content, keyboard/accessible table structure, desktop/mobile overflow and tab isolation. The current 16 export/model regression tests, type checking, targeted lint and production build are also checked. No production deployment is included in this change.

Run the browser coverage check with `node scripts/alberta-overview-test.mjs` while the development server runs on localhost:3002.

Update: automatic refresh and request-time loading supersede the manual snapshot delivery described above. See [Alberta overview refresh](alberta-overview-refresh.md) for source cadences, review boundaries and activation.
