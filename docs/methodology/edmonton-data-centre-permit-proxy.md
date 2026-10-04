# Edmonton data-centre permit activity proxy

Status: implemented descriptive intake; not an authorizing AI-construction treatment.

## Research purpose

The [City of Edmonton General Building Permits dataset](https://data.edmonton.ca/Urban-Planning-Economy/General-Building-Permits/24uj-dj8v)
provides a municipal activity screen between announced projects and realized
construction. It can show that a permit was issued for work whose public
description explicitly references a data centre, but it cannot establish that
the work is AI-related, that the reported value was spent, how many labour hours
were used, or whether construction was completed.

The artifact therefore improves exposure discovery without changing the causal
publication gate. It is a treatment proxy, not the treatment required by
estimand E2.

## Retrieval contract

The source-specific adapter retrieves dataset metadata and a broad server-side
keyword screen from Socrata dataset `24uj-dj8v`. The query selects only:

- system row ID and permit issue date;
- job category, building type and work type;
- job description for local classification;
- publisher-estimated construction value and floor area; and
- the occupancy-granted trend field.

The API query excludes address, legal description, coordinates and geometry.
The normalized publication file additionally excludes neighbourhood and the
free-text job description. It retains a description hash and controlled matched
terms so a reviewer with the raw retrieval can reproduce the classification.

The 2026-09-01 retrieval contains 85 broad-screen records and is locked by:

- response hash: `sha256:f4da956ae985c7eb9abb9cd993407c57bfdf23a8191bba77605e20482d9b6f17`;
- metadata hash: `sha256:174d1a521ec80021a45de782f239ffa51f3cbde4a775b2157fd6b7cc32422d07`; and
- query, retrieval timestamp and archive paths in the committed manifest.

## Classification contract

Classification is deterministic and inferred:

1. Exact word-boundary matches for `data centre`, `data center`, `server farm`,
   `colocation` or `hyperscale` become `data_centre_candidate` records.
2. A word-boundary `server` reference without a data-centre phrase remains
   `server_reference_context`; a server room in a school or office is not
   silently promoted to a data-centre facility.
3. Broad-query substring matches without either controlled pattern are excluded.
   This prevents terms such as `servery` and `Observer Lane` from becoming false
   data-centre records.
4. AI specificity is tested separately. A data-centre phrase does not imply AI.

Every data-centre candidate requires human review before any model ingestion.

## Real-data feasibility result

| Measure | Result | Interpretation |
| --- | ---: | --- |
| Broad keyword screen | 85 | Retrieval candidates, not data centres |
| Explicit data-centre references | 17 | Inferred permit-activity candidates |
| Candidates issued since 2018 | 7 | Recent descriptive screen |
| Generic server references | 62 | Context only |
| Excluded substring false positives | 6 | Classifier exclusions |
| Explicit AI references | 0 | AI specificity is not observed |
| Candidate occupancy dates available | 0 | No completion proxy for the 17 candidates |
| Candidate permits with reported value | 17 | Publisher estimates, not realized spend |
| Candidate reported-value aggregate | $13.34M | Includes fit-outs, maintenance, expansion and one demolition permit; not capex |

The one demolition candidate is flagged separately. The non-demolition
reported-value aggregate is $13.21M, but neither total is used as scenario
calibration or an AI investment measure.

## Occupancy field boundary

The City states that occupancy-granted dates are available only for qualifying
recent permits and are intended for trend analysis, not legal confirmation of
occupancy. Two of the 85 broad-screen rows have this field; none of the 17
data-centre candidates do. AIIO therefore retains occupancy as an observed trend
proxy and keeps construction completion status unobserved.

## Publication boundary

The machine report sets all authorizing fields to `false`:

```text
realized AI-construction treatment: not authorized
realized construction spend: not authorized
construction completion outcome: not authorized
AI-attributable effect: not authorized
```

The permit screen may support descriptive timing, source discovery and manual
case review. It cannot produce an AI-attributable cost or schedule estimate.
