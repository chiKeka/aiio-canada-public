# Grok evidence-screen publication gate

Date: 2026-08-31  
Release candidate: 0.6.0-dev  
Scope: Alberta material, public-project and power evidence screens

## Initial publication review

Grok returned `FAIL` when asked to review a summary packet. The review correctly
found that a packet could not independently verify the manually transcribed
AESO chart and that the public 1,200/20,700 quotient was too easy to misread as
a queue-conversion or realization rate. It also required stronger separation of
observations, inferences, nulls and the uncalibrated counterfactual.

## Source-level re-extraction

A separate Grok session inspected the archived PDF, manual extraction JSON and
two archived AESO HTML pages directly. It independently rendered and read the
embedded page-1 chart, recomputed source hashes and checked the source wording.
The source-level verdict was `GO` with no value discrepancies:

| Application-period label | Independently read chart value | Published value |
|---|---:|---:|
| Q2-24 | 5.0 GW | 5,000 MW |
| Q3-24 | 6.4 GW | 6,400 MW |
| Q4-24 | 10.9 GW | 10,900 MW |
| Q1-25 | 14.6 GW | 14,600 MW |
| Q2-25 | 19.8 GW | 19,800 MW |
| Q3-25 | 20.7 GW | 20,700 MW |

The computed PDF SHA-256 matched the extraction record. The archived HTML also
confirmed the 1,200 MW interim limit, the 970 MW and 230 MW executed load
contracts, their reconciliation to 1,200 MW, and that the no-new-reinforcement
language is scoped to the interim approach through 2028 using the existing
transmission system.

This is an independent machine source review, not human peer review. The chart
extraction record names the reviewer type and links back to this disposition.

## Disposition

- Removed the 1,200/20,700 quotient from the public JSON, CSV, website and
  workbook rather than relying on a disclaimer.
- Kept requested load, allocated limit, executed-contract load, connected load
  and forecasts explicitly distinct.
- Kept additional transmission for the $50 billion counterfactual null.
- Tightened the Phase 1 wording and retained its through-2028/existing-system
  scope.
- Published the public-project AI-exclusion rule and excluded-record count so
  the screen cannot be mistaken for an AI-project census.
- Retained the release status as `research-prototype`; the interface identifies
  the program as public research in development.

The evidence screens may proceed to rebuilt-artifact verification. This gate
does not authorize calibrated cost, delay, probability, queue-conversion or
transmission-need claims.
