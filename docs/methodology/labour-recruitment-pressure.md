# Labour recruitment-pressure screening method

## Purpose

The screening layer asks a narrow question: where does currently published unmet labour demand look large relative to the structural stock of workers in the same detailed occupation? It supports source triage and scenario design. It does not estimate spare capacity, displacement, project delay or a causal effect of AI investment.

## Inputs

- Numerator: Statistics Canada Job Vacancy and Wage Survey table 14-10-0444-01, latest published provincial or territorial job-vacancy count for six five-digit NOC 2021 unit groups.
- Denominator: Statistics Canada 2021 Census table 98-10-0449-01, employed persons in the same province or territory and NOC unit group during the May 2–8, 2021 reference week.
- Scope: 13 provinces and territories; Canada totals are excluded. The six occupations map to the four Alberta graph trade nodes.

The Census coordinates hold labour-force status at employed and education, age and gender at their published totals. The selected-coordinate request and response metadata are retained. For 2021 Census products in the `9810*` series, the Web Data Service documents response code `2` as a valid zero filler. Those cells remain numeric zero and carry `census_zero_filler`; they are not treated as missing.

## Metric

For geography (g) and occupation (o):

```text
screen(g,o) = 1,000 × JVWS vacancies(g,o,t_current)
                         / Census employed(g,o,2021-05-02..08)
```

The published label is **cross-vintage vacancies per 1,000 employed persons in the 2021 Census**. It must never be shortened to “vacancy rate.” The numerator and denominator differ by 1,788 days in the current release and come from different statistical programs.

If the vacancy count is unpublished, the diagnostic is null. If the workforce denominator is zero, the diagnostic is null. Missing cells are never imputed. A model-trade aggregate is calculated only when every component NOC has a published vacancy count and a positive workforce denominator.

## Evidence status and analytical boundary

The source counts are `observed`; occupation ratios and all constructed trade-diagnostic rows are `inferred`. Incomplete trade rows publish only their coverage decision and no aggregate ratio. The metric does not calibrate graph-edge weights and is not used to turn structural pressure scores into percentages, costs or schedule delays. It is a screening layer that can prioritize which trades require newer administrative or survey evidence.

The 2021 denominator is also subject to the Census long-form sample design, random rounding and the labour-market conditions of the COVID-19 pandemic’s third wave. A future current-stock bridge must be versioned as a separate transformation before current-capacity language is allowed.

## Release invariants

1. Exactly 78 workforce cells and 78 latest-vacancy cells are present: 13 geographies by six NOCs.
2. Each source geography retains its Statistics Canada DGUID and the matching `PR_<code>` identifier.
3. Workforce zero fillers retain their quality flag; unpublished JVWS values remain null.
4. The occupation diagnostic contains exactly one row for every geography/NOC pair.
5. Trade rankings exclude incomplete component sets.
6. Website and workbook consume the versioned diagnostic output; neither recomputes a less guarded client-side variant.
7. Workbook formula checks reproduce every published non-null occupation ratio and reconcile null cases.
