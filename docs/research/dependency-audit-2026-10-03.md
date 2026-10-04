# Dependency audit triage — 2026-10-03

**Latest status:** the late-October3 follow-up replaces both remaining vulnerable leaf implementations with tested, source-auditable local forks. Full and production npm audits report zero findings after a clean locked install. This supersedes the residual blocker described in the earlier triage below. npm does not audit local code: the additional provenance/runtime-resolution/security gate is required. See [local remediation](dependency-security-remediation-2026-10-03.md). Empirical validation and independent review gates remain pending; no merge/deployment is authorized.

The initial `npm audit --omit=dev --json` reported 15 vulnerable package entries (1 critical, 12 high, 2 moderate). These are package entries, including propagated dependency findings, rather than 15 independent advisories. The original report is `local review evidence (not bundled)` in the review workspace. `npm explain`, application import searches, upstream registry metadata, and `origin/main` lockfile comparisons underpin this triage. This document does not claim deployment exploitability has been proved or disproved.

## Baseline and exposure

All audited leaf package versions were already present in the remote baseline lockfile: Next 16.3.3, braces 3.0.3, micromatch 4.0.8, fast-glob 3.3.3, shadcn 4.18.0, vinext 1.0.0-beta.8, brace-expansion 5.0.9, fast-uri 3.1.6, hono 4.13.5, ip-address 10.7.0 and undici 7.29.0. They were not introduced by the construction improvements. These are the initial versions; the supported patches and final audit are recorded below.

| Dependency path | Observed use and implication |
| --- | --- |
| Direct `next` | Native production server framework. No `next/og` or `ImageResponse` use was found in app/components/lib/scripts. Patch to 16.3.6 or later compatible 16.x regardless; absence of a direct import is not a runtime reachability proof. |
| `shadcn → fast-glob → micromatch → braces` and `shadcn → ts-morph → @ts-morph/common → fast-glob` | Component generation/CLI tooling declared as a production dependency. The initial JavaScript import search found none; follow-up confirmed app/globals.css imports shadcn/tailwind.css, which is retained. Installed-package audit classifies it production; ordinary application request handling is not shown to invoke this glob parser. |
| `vinext → vite-plugin-commonjs → vite-plugin-dynamic-import → fast-glob → micromatch → braces` | Sites build/dev transform chain. Native `next start` does not invoke the vinext command. The alternative Sites build needs separate validation and artifact inspection. |
| `shadcn → @modelcontextprotocol/sdk → hono / express-rate-limit → ip-address` and `shadcn → socks → ip-address` | CLI/MCP/network tooling; no application imports found. This is not evidence that an MCP server is deployed. |
| `shadcn → undici`, `shadcn → @dotenvx/dotenvx → undici`, plus dev `miniflare → undici` | Tooling HTTP/client paths. Shared dependency also appears in dev Cloudflare tooling. A production audit can still include the shared package via shadcn. |
| `react-server-dom-webpack → webpack → schema-utils → ajv → fast-uri`, also shadcn SDK/config chains | Build/schema URI processing. The peer dependency is installed with production dependencies; request-level reachability was not established. |
| `shadcn → ts-morph → @ts-morph/common → minimatch → brace-expansion` | Tooling glob expansion, separate from the unpatched `braces` package. |

## Supported patch options and residual gate

The audit ranges identify compatible patch targets: Next ≥16.3.6; brace-expansion ≥5.0.12; fast-uri ≥3.1.8; hono ≥4.13.7; ip-address >10.7.0; undici ≥7.29.1 within their existing major lines. Confirm released versions, parent constraints, lock resolution, clean install, both supported builds and numerical/browser checks before accepting patches. A transitive override must be documented and tested, particularly where Miniflare pins an exact undici version.

**No released braces fix was available when checked.** The [upstream advisory](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm) lists all versions through 3.0.3 and no patched version. Official npm registry checks returned braces latest 3.0.3, micromatch latest 4.0.8 with braces `^3.0.3`, shadcn latest 4.21.1 still using fast-glob `^3.3.3` and ts-morph `^26.0.0`, and vinext latest 1.0.1 still using vite-plugin-commonjs `^0.10.4`. Upgrading those direct packages does not itself remove this chain. Registry metadata: [braces](https://registry.npmjs.org/braces/latest), [micromatch](https://registry.npmjs.org/micromatch/latest), [shadcn](https://registry.npmjs.org/shadcn/latest), [vinext](https://registry.npmjs.org/vinext/latest).

Do not run `npm audit fix --force`: its suggested shadcn 1.0.0 and vinext 0.0.15 replacements are substantial downgrades, not compatibility-tested patches. Safe future options are an upstream depth-guard patch, a maintained compatible dependency replacement with build tests, or a separately reviewed toolchain change. Merely moving CLI packages to devDependencies changes audit classification, not their build-time risk; this triage does not perform that change or declare risk accepted.

Before deployment, retain the final audit as a release check. Any residual high finding needs an explicit reviewer disposition supported by build/runtime reachability evidence or a tested remediation. This draft implementation does not authorize AIIO deployment or approve an exception.

## Applied patches and final audit

The implementation applied Next 16.3.3 → 16.3.8, brace-expansion 5.0.9 → 5.0.12, fast-uri 3.1.6 → 3.1.8, hono 4.13.5 → 4.13.12 and ip-address 10.7.0 → 10.7.3. Undici is overridden to 7.29.1: Miniflare pins 7.29.0 exactly, so an ordinary update cannot replace that vulnerable copy. This is a same-major patch; its engine requirement is Node ≥20.18.1, compatible with this project's Node ≥22.13.0. A second scoped override patches Miniflare's sharp0.35.2pin to0.35.4. Both overrides require native/Sites build and local emulation validation; neither suppresses audits.

The final production report `local review evidence (not bundled)` contains **9 high, 0 critical, 0 moderate** package entries, all tracing to the single unpatched braces advisory. Entries are braces, micromatch, fast-glob, @ts-morph/common, ts-morph, shadcn, vite-plugin-dynamic-import, vite-plugin-commonjs and vinext. The full dependency report `local review evidence (not bundled)` contains **13 entries: 9 high and 4 moderate**, with no critical entries. The additional four development package entries are esbuild, @esbuild-kit/core-utils, @esbuild-kit/esm-loader and drizzle-kit. Findings are retained, not suppressed.

| Additional dev chain | Actual advisory and affected range | Assessment / option |
| --- | --- | --- |
| wrangler / @cloudflare/vite-plugin → miniflare → sharp 0.35.2 | [GHSA-rgj7-g3m4-5g8c](https://github.com/advisories/GHSA-rgj7-g3m4-5g8c), sharp <0.35.4; references libheif [GHSA-g89c-p67h-r497](https://github.com/advisories/GHSA-g89c-p67h-r497) and [GHSA-2jg2-4ch7-h545](https://github.com/advisories/GHSA-2jg2-4ch7-h545) | Remediated with a narrowly scoped Miniflare sharp 0.35.4 override. Next's optional Sharp dependency also resolves to the patched0.35.4copy. Native and Sites builds and local Cloudflare emulation are verified; no broad Miniflare/toolchain upgrade was forced. |
| drizzle-kit → @esbuild-kit/esm-loader → @esbuild-kit/core-utils → nested esbuild | [GHSA-67mh-4wv8-2f99](https://github.com/advisories/GHSA-67mh-4wv8-2f99), esbuild ≤0.24.2 | Database developer tooling; the advisory concerns the esbuild development server. Modern top-level esbuild does not remove the old nested copy. Update/replace this legacy loader chain with compatibility tests; no application import or exposed esbuild development server was found. |

**Release remains blocked** until the residual affected chains are removed or patched upstream, or an explicit reviewed risk acceptance establishes the relevant build/runtime boundaries. No risk acceptance, audit suppression, forced downgrade, merge or AIIO deployment occurred as part of this implementation. Final numerical/build/browser results are reported by the implementation owner separately.

## Initial advisories

### brace-expansion

- [brace-expansion: Quadratic-time expansion of the `{a},b}` rewrite causes CPU denial of service](https://github.com/advisories/GHSA-q2hr-2g5m-vwhr) — moderate; initial affected range `>=4.0.0 <5.0.12`.
- [brace-expansion: DoS via uncontrolled recursion on nested brace groups causing stack exhaustion](https://github.com/advisories/GHSA-qhr7-859c-m2p7) — high; initial affected range `>=4.0.0 <5.0.11`.
- [brace-expansion: DoS via uncontrolled recursion in parseCommaParts causing stack exhaustion](https://github.com/advisories/GHSA-6j4f-fj2g-mc7p) — high; initial affected range `>=4.0.0 <5.0.10`.

### braces

- [braces vulnerable to stack-exhaustion denial of service through deeply nested patterns](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm) — high; initial affected range `<=3.0.3`.

### fast-uri

- [fast-uri vulnerable to authority injection via an unvalidated port in serialize](https://github.com/advisories/GHSA-qw65-cvwx-89v3) — high; initial affected range `>=3.0.0 <3.1.7`.
- [fast-uri vulnerable to host confusion via an unclosed bracket in the URI authority](https://github.com/advisories/GHSA-58mr-gqgx-xq4g) — high; initial affected range `=3.1.6`.
- [fast-uri vulnerable to inconsistent host case normalization via percent-encoded octets](https://github.com/advisories/GHSA-hrr3-gc8f-f4qj) — moderate; initial affected range `>=3.0.0 <3.1.8`.

### hono

- [hono/jsx renders plain strings unescaped in boundary components, leading to XSS](https://github.com/advisories/GHSA-hxh3-vqpv-xpqv) — moderate; initial affected range `<4.13.7`.

### ip-address

- [ip-address: isInSubnet() and isHostInSubnet() compare addresses of different families as if they shared an address space, allowing an allowlist check to admit an address outside its range](https://github.com/advisories/GHSA-j6r3-76f7-8jcv) — moderate; initial affected range `<=10.7.0`.
- [ip-address: Address6 builds a parse diagnostic proportional to the input with no length bound, allowing a single long string to stall or crash the process](https://github.com/advisories/GHSA-h3mg-xc3c-68pw) — moderate; initial affected range `<=10.7.0`.

### next

- [Next.js: Remote Code Execution in next/og ImageResponse](https://github.com/advisories/GHSA-vcvr-r3jv-pc5j) — critical; initial affected range `>=16.2.0 <16.3.6`.

### undici

- [undici vulnerable to Denial of Service via unhandled error in WebSocket permessage-deflate decompression](https://github.com/advisories/GHSA-3wwx-pv8p-q78v) — moderate; initial affected range `>=7.28.0 <7.29.1`.
- [undici vulnerable to Denial of Service via orphaned RetryHandler response body](https://github.com/advisories/GHSA-pmjh-fq2x-6v4x) — moderate; initial affected range `>=7.11.0 <7.29.1`.
- [undici vulnerable to downstream response splitting via retry interceptor](https://github.com/advisories/GHSA-r53p-7pc4-xj5r) — low; initial affected range `>=7.0.0 <7.29.1`.
- [undici vulnerable to Denial of Service via unrequested WebSocket subprotocol](https://github.com/advisories/GHSA-rfgv-xxqx-mfg5) — high; initial affected range `>=7.0.0 <7.29.1`.
- [undici vulnerable to Denial of Service via unbounded decompression of compressed responses](https://github.com/advisories/GHSA-3xpg-4rpp-hhhm) — moderate; initial affected range `>=7.15.0 <7.29.1`.
- [undici vulnerable to cross-user cookie disclosure via Set-Cookie caching in shared caches](https://github.com/advisories/GHSA-2jfj-6hjv-fm6j) — moderate; initial affected range `>=7.0.0 <7.29.1`.
- [undici vulnerable to response truncation via oversized chunked responses in the dump interceptor](https://github.com/advisories/GHSA-2gqq-gqf2-x968) — low; initial affected range `>=7.1.0 <7.29.1`.
- [undici vulnerable to TLS certificate validation bypass via dropped connect options in BalancedPool](https://github.com/advisories/GHSA-w293-vg96-wgc3) — high; initial affected range `>=7.24.1 <7.29.1`.
- [undici vulnerable to caching and replay of unsafe HTTP method responses](https://github.com/advisories/GHSA-8436-99hf-9mmv) — low; initial affected range `>=7.0.0 <7.29.1`.
- [undici vulnerable to Denial of Service via WebSocketStream unclean close](https://github.com/advisories/GHSA-rx4f-c7p8-82vq) — moderate; initial affected range `>=7.0.0 <7.29.1`.


The versioned audit snapshot is `data/reviews/dependency_audit_2026_10_03.json`, binding the initial base and patched lock hashes and exact advisory inventory.
