# Alberta material-cost screening method

## Purpose

This screen describes recent construction bid-price movement in components that
AI facilities and public infrastructure may both use. It is an observed market
baseline, not an estimate of AI-caused inflation or a graph calibration input.

## Source and scope

The screen uses Statistics Canada table 18-10-0289-01, Building Construction
Price Index (BCPI), for Calgary (`CMA_825`) and Edmonton (`CMA_835`). It retains
four published building archetypes:

- factory, used only as an industrial-building proxy;
- institutional buildings;
- schools; and
- bus depots with maintenance and repair facilities, used as a municipal
  operations proxy.

For each archetype it retains concrete, structural-steel framing, electrical,
and heating/ventilation/air-conditioning divisions. The full normalized BCPI
history remains available; the public screen publishes the latest index,
quarter-over-quarter change and year-over-year change.

## Evidence contract

Published BCPI values are `observed`. Percentage changes and index points from
the 2023 base are `inferred` arithmetic transformations. A series must have an
aligned latest period and matching prior observations before a change is shown.
Missing comparisons remain null.

## Interpretation limits

- The factory series is not a data-centre construction index.
- BCPI measures contractor bid-price change for model buildings. It does not
  measure commodity spot prices, physical quantities, lead times, or production
  capacity.
- Calgary and Edmonton remain separate CMAs and do not stand in for all Alberta
  regions.
- Movement in an index cannot identify an AI effect. Causal attribution requires
  a separate empirical design and counterfactual.

