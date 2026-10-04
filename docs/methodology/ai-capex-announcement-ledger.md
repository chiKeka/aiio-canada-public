# Alberta AI-capex announcement ledger

## Research question

What does the current public Alberta project inventory report about AI-relevant data-centre and enabling-power projects, and which fields remain missing before the records can define realized construction treatment?

The ledger answers a narrower question than the causal workstream. It tracks the public announcement pipeline and its data completeness. It does not estimate committed investment, realized spending, construction onset, completion probability, or an AI-attributable effect.

## Source and transformation

Source ID: `ALBERTA_MAJOR_PROJECTS`  
Source: [Alberta Major Projects](https://www.majorprojects.alberta.ca/)  
Input: `data/processed/alberta_ai_projects.csv`  
Artifact: `data/model-runs/alberta_ai_capex_announcement_ledger_v0.1.json`

The upstream adapter retains publisher project ID, name, estimated cost, municipality, schedule text, stage, developer, website, location and any reported power-generation capacity. AI relevance is inferred using the controlled vocabulary documented in `research/src/aiio/adapters/alberta_projects.py`.

The ledger validates source lineage, evidence labels, unique identifiers, numeric fields, schedule ordering and a single as-of date. It then records:

- data-centre and enabling-power classifications separately;
- partial reported-estimated-cost coverage and sums;
- publisher stage counts;
- complete, one-sided and missing schedule-year coverage;
- project-site and location coverage;
- whether the publisher stage merely identifies a construction-activity candidate; and
- null authorizing treatment-onset and treatment-dose fields.

## Current result

The 2026-08-31 snapshot contains 22 AI-relevant records: 19 core data-centre records and three enabling-power records. Ten records report estimated cost. Their partial known sum is $55.41 billion: $49.01 billion for core facilities and $6.40 billion for enabling power. Four records carry an `Under Construction` publisher stage, but none supplies a verified realized construction-start date or realized construction spending by region and period.

Only three records report both start and end years; 14 report at least one schedule year. Twelve records provide a project website. Missing values remain missing and are never treated as zero.

## Aggregation controls

- Enabling-power projects remain separate from core facilities.
- A multi-location project counts as one publisher record.
- The known-cost sum is explicitly partial.
- No stage probability or probability weighting is applied.
- The sealed $50 billion scenario is not inserted into the ledger.
- Publisher stage is not converted into a treatment-onset date.

## Causal-treatment boundary

The E2 attribution contract requires realized AI-construction spending or construction labour hours at a stable region-period unit. This ledger lacks verified realized construction onset and dose. Its `authorizing_treatment_present` field is therefore false, and all AI-attributable cost and schedule effects remain null.

## Reproduction

```bash
npm run treatment:announcement-ledger
npm run research:test
npm run program:audit
```

The artifact stores hashes of its normalized input and implementation. Tests reject duplicate project IDs, source-lineage drift, invalid schedules, unsafe publication flags and any non-null authorizing treatment fields.
