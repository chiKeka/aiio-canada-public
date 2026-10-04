# Alberta overview refresh

The overview and PowerPoint now load the same atomic, SHA-256-verified evidence bundle at request time. The overview is a dynamic Next.js route. An open, visible page checks the published revision every minute and on focus/visibility return; a new revision triggers a server refresh without resetting unrelated tab state or scroll. Failed checks leave the loaded evidence visible and report the failure. Freshness status is evaluated against the current day, independently of observation dates.

## Source cadence

The existing Monday evidence workflow now includes construction inputs. Its structured feeds are Alberta Major Projects (project register and infrastructure overlap), Statistics Canada JVWS (trade vacancies) and BCPI (construction prices). Checks run at most every seven days; quarterly feeds are checked weekly to detect new releases and revisions. Unchanged source hashes do not regenerate observations. Each source normalizes and validates its downstream outputs in a staging directory before replacing canonical files. Regressed statistical periods and failed parses retain the last successful outputs, with failed-check metadata recorded separately.

Census workforce stock, BuildForce recruitment, the Alberta fiscal plan and SourceBlue equipment ranges use reviewed publications. The policy calls for annual Census verification and monthly review of the other reports. These are review intervals, not promised publication dates. The dashboard flags due reviews; it does not automatically interpret or promote new PDF/article numbers. New reviewed benchmarks and normalized evidence are picked up by publication; rolling fiscal-year and forecast-horizon labels no longer require dashboard code changes.

The source table shows publication cadence, observation period, last successful check or source-verification record, next due date and failed/overdue status. Merely rebuilding or checking a source never advances its observation period.

## Publication and activation

`npm run construction:publish` regenerates the bundle from canonical inputs and source-check receipts. It also runs automatically before `npm run build`. The weekly workflow publishes these artifacts into its existing review PR. A reviewed merge to main uses the existing Vercel Git deployment, which distributes the new bundle to production. The browser then detects that version. No separate manual presentation export or editing of dashboard figures is required.

This change configures the existing workflow; it does not run a live source acquisition, push, merge or production deployment in this session. The workflow changes take effect after they reach the repository's default branch. Local source-check labels still correctly identify their original registry verification when no refresh receipt exists.

## Verification

`npm run test:construction-refresh` checks cadence, failed-source retention, deterministic and atomic publishing, request-time replacement, integrity rejection, stale/review states and new fiscal/forecast vintages without using external services. `npm run test:briefing` checks the matching PowerPoint. `node scripts/construction-refresh-workflow-test.mjs` checks revision-triggered refresh and failure/recovery in the local browser. The overview coverage/accessibility test remains `node scripts/alberta-overview-test.mjs`.
