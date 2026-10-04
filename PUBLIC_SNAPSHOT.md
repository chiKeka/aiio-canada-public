# Public snapshot prepared for review

This is a local review export of AIIO Canada, not a newly published repository, deployment or empirically validated release. It contains no original Git history, remote, PR comments, Actions logs/artifacts or private hosting binding. Publication and destination require a separate decision.

## What is bundled

Original application/research code, reviewed normalized observations, explicitly labelled scenarios, public factual summaries, Apache-2.0 for original work, required vendored dependency notices, openly licensed source datasets and source attribution. Methodological limitations and independent-review gates remain in effect.

`publication/source-license-matrix.json` records publisher, canonical URL, recorded terms and bundling status for all registered sources. It is an inventory of recorded terms, not blanket legal clearance. Third-party source materials retain their publisher's terms. `publication/source-availability.json` records original source hashes and whether their bytes are actually bundled.

## What is withheld

Complete BC Hydro HTML, AESO pages/PDF, IESO workbook/PDF, OAGO report and Hydro-Québec/regulatory source documents lacking recorded unrestricted redistribution permission are omitted. Municipal raw permit envelopes and the BC raw inventory are omitted to minimize unnecessary individual contacts and precise-location/provider metadata. Existing normalized research derivatives, factual extracts, URLs and hash receipts remain; they are not recreated or substituted with fake data. Complete historical webpage archives are also omitted.

Personal dissertation/supervisor planning, local research-folder locators, another private repository's name, private hosting binding, old deployment inventories and selected local reviewer-session details are omitted/generalized. Research integrity, AI assistance disclosure, substantive reviewer findings and pending-review status are retained. Historical source commit hashes are provenance receipts; this export does not promise public access to the original history.

## Reproducibility and missing sources

Run `npm ci`, `npm run public:check`, `npm run research:validate`, `npm run research:test:public`, `npm run lint`, and `npm run build`. The public research test entry point runs the original suite with five individually identified source-dependent checks reported as **skipped**, never passed. `npm run research:test` retains the original full-source test suite, which cannot completely pass without the omitted original source archives.

Runtime application calculations use retained normalized inputs. Omitted raw bytes do not disable those existing observations or conditional scenarios. They do limit independent source-file reproduction: IESO cell reconciliation and full provincial raw-intake reconciliation cannot be claimed here. Independent calibration, causal effects and authorization remain withheld.

Historical release manifests and workbook receipts describe original releases, not this transformed snapshot. The new file manifest and derivative/exclusion records supplied with this export identify its exact bytes. Some review packages and the method-lineage/research-surface provenance manifests are regenerated to reconcile public documentation; this changes provenance hashes, not observational/model numerical values or publication authority.

## Optional local source acquisition

Network acquisition is not needed to build the public app and was not run while preparing this snapshot. Source-dependent npm commands first stop with an unavailable-source explanation. Original command definitions are retained in `publication/source-commands.json`.

If a publisher permits your intended local use, review the source's canonical URL and current terms, then explicitly invoke, for example:

```sh
python3 scripts/public_snapshot.py run-source permits:vancouver-fetch --allow-local-acquisition
```

For normalizers, acquire the exact original vintage permitted by its publisher first, and verify it against the receipt. A new current response is a new vintage, not a replacement for a historical source hash. Local acquisition permission is not permission to publish/relicense complete source material. Inspect free text for contacts and personal data before producing public derivatives. Preserve original hashes as source receipts and issue new hashes for sanitised derivatives.

`.gitignore` excludes new raw acquisitions by default. Reviewed open-licensed source blobs intentionally included in this bundle must be staged individually from the reviewed manifest if a fresh repository is later approved; never force-add the entire raw directory. Review the licence matrix and exact manifest again before publishing additional source files.

## Workflow and deployment boundaries

Read-only quality/security workflow definitions remain active templates. Source-refresh and production-monitor workflows are retained under `docs/operations/workflow-templates/*.disabled`; they are not armed for a new destination. Review publisher permissions, source privacy, repository permissions, required checks and deployment destination before separately activating them. No Git/Vercel settings in the private source repository were changed.

Use a verified owner GitHub noreply identity for any later initial commit. No new Git repository or author metadata has been created in this export.

The alternative worker build uses Vinext/Cloudflare without the private Sites hosting-copy plugin or any storage/project binding. It builds locally with `npm run build:sites`; hosted Sites integration would require a separately approved binding and plugin configuration.
