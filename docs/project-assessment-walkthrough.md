# Owner-assessment walkthrough

Open [the live owner assessment](https://aiio-canada.vercel.app/project-scenario?view=assessment), or `/project-scenario?view=assessment` on your local app. The live deployment is independent of this public repository snapshot.

## Load and inspect the example

Select **Load hypothetical $50M school example**. The project type is a school, the budget is CAD $50 million and the electrical package has CAD $8 million of remaining exposed value. Other example fields, including paid labour hours and resource-pool assumptions, are supplied by the preset: inspect them rather than silently treating them as observed evidence.

The result becomes **conditional**. An unloaded/default assessment is qualitative when necessary inputs are missing. A conditional calculation means the entered assumptions are sufficient for that calculation; it does not mean the displayed cost or delay has been empirically validated. Read the evidence status as well as the result.

## Separate contract exposure from capacity

Open **1. Packages**, then **Electrical package**. Change **Electrical commitment** to fixed. The remaining exposed value clears to zero and the package's price-escalation result becomes zero. Its assumed delay need not disappear: locking a price does not establish that a contractor or resource is available.

Restore variable commitment and enter `8000000` in **Electrical remaining exposed value (CAD)** if you want to return to the financial example. Clear **Electrical paid labour hours** to see an incomplete assessment return to qualitative output instead of inventing a numerical delay. Reload the preset to reset all example inputs.

## Inspect the record

Choose **Export current assessment JSON**. The record contains the current configuration and result together. Changing free-text project location alone does not create evidence of a shared contractor catchment. Use the resource matching inputs and source evidence explicitly.

## Screenshot provenance

The README images were captured on 4 October 2026 from the live assessment after loading the hypothetical school preset, using fresh browser contexts at desktop 1440 × 1000 and mobile 390 × 844. They show synthetic example inputs, with no personal session, client record or browser chrome. They illustrate the interface at that date, not a validated project outcome or a guarantee that a later deployment is identical.

For local development and contribution checks, see [CONTRIBUTING.md](../CONTRIBUTING.md). For source exclusions and optional acquisition rules, see [PUBLIC_SNAPSHOT.md](../PUBLIC_SNAPSHOT.md).
