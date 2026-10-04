# Contributing to AIIO Canada

Useful contributions make the evidence easier to inspect or the application easier to use without overstating what the research establishes. Start with an existing [good first issue](https://github.com/chiKeka/aiio-canada-public/issues?q=is%3Aissue%20is%3Aopen%20label%3A%22good%20first%20issue%22), or describe a concrete improvement in an issue before undertaking a large change.

## Set up and check

Follow the [README quickstart](README.md#run-locally) with Node.js 22.13+, npm and Python 3.12+. `npm ci` uses the committed lockfile and vendored dependency patches. Do not replace those patches merely to make installation easier.

Run the checks relevant to your change:

```bash
npm run lint
npx tsc --noEmit
npm run test:project-assessment
npm run research:validate
npm run research:test:public
npm run build
```

The public research runner currently discovers 269 tests: 264 pass and five source-dependent tests are explicitly skipped because their original archives are withheld. The full `research:test` command is for a separately licensed local research environment; missing-source failures are not permission to restore excluded archives.

For the owner-assessment browser check, start the app in another terminal, then run:

```bash
AIIO_BASE_URL=http://localhost:3000 npm run test:project-assessment-browser
```

The browser helper uses installed Google Chrome/Chromium where available. Set `CHROME_EXECUTABLE` to your browser executable if needed; otherwise a compatible Playwright Chromium installation is required. Use the actual local port printed by Next.js.

**Known preflight limitation:** `npm run public:check` currently rejects a normal Git checkout because its export guard rejects any `.git` directory. It can verify an export made with `git archive`; fixing this without weakening the publication boundary is [starter issue #1](https://github.com/chiKeka/aiio-canada-public/issues/1). This limitation does not block the app or the public research test runner.

## Find the relevant code

| Area | Location |
| --- | --- |
| Pages and interactive views | `app/`, `components/` |
| Browser checks and publication boundary | `scripts/` |
| JavaScript model tests | `tests/` |
| Python evidence and scenario pipeline | `research/src/`, `research/tests/` |
| Retained inputs and model outputs | `data/` |
| Source availability and rights | `publication/`, `THIRD_PARTY_DATA.md` |
| Methods and research limits | `docs/methodology/`, `docs/release/` |

## Keep changes reviewable

Use a branch and a focused pull request. Explain the concrete problem, changed behaviour and checks performed; include desktop/mobile screenshots for visible changes. A draft PR is useful while implementation or evidence is incomplete. Do not submit empty changes for profile activity.

Keep observed values, assumptions and scenario outputs distinct. Preserve provenance, suppression flags, unavailable-source states and pending review gates. Numerical or methodological changes need an explanation and appropriate model tests, not just a screenshot.

Do not commit credentials, session cookies, private deployment bindings, personal contacts, private project documents or copied publisher pages. Source availability is not redistribution permission. Follow [PUBLIC_SNAPSHOT.md](PUBLIC_SNAPSHOT.md) before any optional acquisition and keep excluded raw material out of public commits. Deployment/refresh templates are documentation; activating them is a separate operational decision.

Respect the [Apache licence](LICENSE) for original contributions and retain third-party licence notices. Public issues and pull requests should contain only information you are comfortable publishing.
