# Information-sector construction-capex treatment screen

## Research question

Can a public Statistics Canada capital-expenditure table supply the realized AI/data-centre construction measure required by AIIO estimand E2?

The answer for this source vintage is **no**. Table 34-10-0035-01 materially improves the regional macro evidence spine, but it does not identify AI or data-centre construction and therefore cannot define treatment onset or dose.

## Source and selection

AIIO retrieves the complete Statistics Canada table [Capital and repair expenditures, non-residential tangible assets, by industry and geography](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=3410003501). The source is annual, covers Canada plus every province and territory from 2006 through 2026, and separates capital construction from machinery/equipment and repairs.

The deterministic screen selects:

- expenditure: `Capital, construction`;
- industry: `Information and cultural industries [51]`;
- geography: Canada and all 13 provinces/territories; and
- years: 2006–2026.

The 294 selected cells retain the publisher DGUID, value, unit and quality symbol. Suppressed values remain blank. The source's 2026 release describes 2024 as revised actual, 2025 as preliminary actual and 2026 as intentions; those statuses remain distinct.

## Why NAICS 51 is not an AI treatment

Statistics Canada's current classification defines NAICS 518210 as computing infrastructure providers, data processing, web hosting and related services. However, the province-level capex table does not publish NAICS 518210. Its finest relevant industry is the much broader NAICS 51 aggregate, which also contains telecommunications, publishing, broadcasting and other information activities.

Consequently, the screen passes only two treatment subconditions:

- construction capital is separately published; and
- historical actual or revised values exist through 2024.

It fails three authorizing conditions:

- industry specificity: NAICS 518210 or project-level data-centre construction is absent;
- temporal resolution: annual rather than quarterly; and
- geography: province/territory rather than CMA or a reconciled electricity-planning region.

The normalized series is therefore a `research_only_broad_sector_capex_proxy`. It may be used as regional information-sector construction context or as a sensitivity control. It may not define AI treatment onset, AI dose, a project-cost increment or schedule-delay effect.

## Alberta evidence

The current Alberta cells report:

| Reference year | Publisher measure status | NAICS 51 capital construction |
| --- | --- | ---: |
| 2023 | Actual or revised | Suppressed |
| 2024 | Actual or revised | $458.6 million |
| 2025 | Preliminary actual | $996.1 million |
| 2026 | Intentions | $832.7 million |

These are broad-sector values, not data-centre values. The increase between vintages cannot be attributed to AI infrastructure.

## Reproducibility and release boundary

Run:

```bash
PYTHONPATH=research/src python3 -m aiio.cli --root . fetch STATCAN_CAPEX_INDUSTRY_GEOGRAPHY_34100035
npm run treatment:capex-screen
```

The source ZIP and retrieval manifest are content-hashed. The report also locks the transformation code and normalized CSV. Tests reject source-schema drift, incomplete geography/year coverage, silent suppression-to-zero conversion and a future appearance of NAICS 518210 until the preregistered selection is explicitly reviewed.

The publication boundary authorizes descriptive broad-sector capex only. `ai_construction_treatment_authorized`, `ai_attributable_effect_authorized`, cost escalation and schedule delay remain false or null.
