# Provincial power-planning evidence contract

## Purpose

This contract profiles the official electricity-planning evidence available for Ontario, British Columbia and Quebec without manufacturing a common national load metric. It is a source and comparability layer, not a power-system model, transmission needs assessment or calibration of the AI capex scenario.

## Source boundary

Five source artifacts are retained by content hash:

- IESO's corrected 2026 Annual Planning Outlook data tables and Demand Forecast Module;
- BC Hydro's public 2025 Integrated Resource Plan summary; and
- Hydro-Quebec's regulator-filed 2025 supply-plan progress report and February 2026 data-centre announcement.

The Ontario workbook exposes scenario-specific net annual energy, seasonal peak, remaining capacity need and remaining energy need. Numeric workbook observations are checked directly against their worksheet and cell locators using a standard-library XLSX reader.

The Ontario demand module publishes data-centre net annual energy endpoints under reference, high- and low-demand scenarios. The Quebec filing publishes regular electricity sales, winter system peak and data-centre winter peak. The B.C. public summary publishes selected supply actions and named transmission actions, but not a comparable numeric data-centre demand path.

## Quantity contract

Each record carries a quantity type, quantity status, scenario, period, unit, approximation flag, source identifier and source locator. The fact that an official source published a value is observed evidence; the value itself may still be a forecast, outlook, proposed action, conditional action or announcement.

Comparisons are permitted only when the quantity, unit, scenario meaning, time basis and system boundary align. In particular:

- Ontario data-centre annual energy in TWh is not pooled with Quebec data-centre winter peak in MW.
- A planned generation addition, energy acquisition or transmission project is not demand, spare capacity or a reserve margin.
- Quebec regular electricity sales and Ontario net annual energy retain distinct publisher definitions.
- Province-wide demand or capex cannot be converted into a transmission line requirement without project locations, connection studies and a system needs assessment.

## Publication boundary

The current extract is research evidence only. Its source pages and workbook ranges were visually checked during the primary build, but independent extraction review is pending. The profile, scenario-calibration and transmission-requirement gates therefore remain closed.

Official sources:

- https://ieso.ca/Sector-Participants/Planning-and-Forecasting/Annual-Planning-Outlook
- https://www.bchydro.com/toolbar/about/strategies-plans-regulatory/supply-operations/long-term-electricity-planning/integrated-resource-plan.html
- https://www.regie-energie.qc.ca/storage/app/media/Suivis/Suivi%20D-2023-109/etat-davancement-2025.pdf
- https://news.hydroquebec.com/news/press-releases/all-quebec/hydro-quebec-proposing-regie-energie-new-rate-large-data-centres-adjustment-rate-cryptographic-use-applied-blockchains.html
