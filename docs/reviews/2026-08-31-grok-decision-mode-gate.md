# Decision Mode product gate — 2026-08-31

## Decision

**GO.** Decision Mode is suitable as an executive structural-screening product
surface. It is not a calibrated cost forecast and does not estimate an
AI-attributable project contingency.

## Review sequence

Grok CLI performed two read-only reviews against the implementation,
`public/data/latest.json` and the sealed Alberta graph.

The first review returned **HOLD**. It found that the prototype:

- compared a project only with two peak years instead of the 2027–2036 scenario
  input window;
- applied the global electrician ranking to every asset class;
- combined the common cost-signal ancestry with asset-specific schedule paths;
- placed trade and material nodes at the same graph coordinates; and
- made an unweighted component range the largest quantitative briefing field.

Those findings were treated as model-product defects, not wording issues.

## Corrections verified

- The default 2029–2033 hospital intersects five scenario input years and the
  2032–2033 dominant published path years.
- Hospital, school and government paths resolve to building electricians;
  utilities resolve to power-line trades; roads resolve to the declared
  concrete-trade parent when no dominant release path is published.
- Schedule and common cost branches are separate graph views.
- Current graph layouts have no node collisions and use distinct type columns.
- AI-attributable cost is the leading decision boundary and remains explicitly
  unquantified.
- BCPI is a dated market screen with observed index and inferred-change labels;
  declines use a down indicator rather than a positive bar.
- Project budget is disclosed as briefing context and does not silently change
  analysis.
- The brief includes analysis date, scenario id, release version and source ids.
- Labour, concurrent public projects, AESO power evidence and the unquantified
  regional-macro channel appear side by side without unit fusion.
- Decision and Research surfaces share the release data, graph and bounded-score
  helper.

The second independent review returned **GO WITH CONDITIONS** and no ship
blockers. Its four residual conditions were then closed:

1. dominant-path selection is scoped to the project window;
2. all three AESO sources used in the power card are listed;
3. inner routes no longer claim an active Decision or Research home state; and
4. signal and outcome nodes have distinct future-proof graph columns.

## Validation

- 56 research tests passed.
- Next.js and Sites-compatible production builds passed.
- Lint and diff checks passed.
- Automated WCAG 2 A/AA and 2.1 A/AA checks found zero violations across all
  eight public routes.

## Interpretation boundary

The product can support a watch, diligence and sequencing decision. It cannot
yet answer “add X percent” or “expect Y months.” That translation remains a
separate calibration and validation release gate.
