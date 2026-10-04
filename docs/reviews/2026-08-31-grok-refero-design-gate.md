# Grok gate: Refero-inspired AIIO design pass

Date: 2026-08-31  
Scope: local, uncommitted visual-design refinement  
Reviewer: Grok CLI, independent summary-based product-design review  
Verdict: **GO WITH CONDITIONS**

## Conditions

1. Keep Decision Mode as the public briefing surface and Research Mode clearly exploratory so a sandbox view cannot be mistaken for an official position.
2. Carry the unquantified AI-cost caveat through workbench outputs; scenario and sensitivity outputs must never read as point estimates.
3. Preserve the colour semantics: teal for brand emphasis, amber/rust for assumptions and warnings, and the dark surface for the dependency graph.

## Gate response

All three conditions are already enforced in this implementation:

- Decision Mode opens with the project decision and an explicit cost-translation boundary. Research Mode opens with a counterfactual diagnostic warning and labels the sandbox uncalibrated and not a forecast.
- The decision brief states that AI-attributable project cost is not quantified, the estimate is context-only, and graph outputs do not estimate dollars or days.
- The design direction documents the semantic colour lock, and the rendered interface follows it.

## Verification

- Next.js production build: pass.
- Sites/Vinext build: pass.
- Research tests: 56 pass.
- Accessibility audit: zero violations on eight public routes after correcting light-header neutral contrast.
- Browser visual QA: Decision and Research modes rendered with the intended Geist typography and no fresh Next.js console warnings.

Deployment remains intentionally on hold.
