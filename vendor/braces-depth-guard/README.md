# @aiio/braces-depth-guard 1.0.0

Private local fork of `braces@3.0.3`, under the retained upstream MIT license.
This package has its own identity and version. It is **not** an upstream braces
release, and it does not imply that npm's advisory database has approved a fix.

## Origin and audit record

Copied the installed `braces@3.0.3` implementation (`index.js`, every `lib/*.js`),
MIT LICENSE and README. `UPSTREAM-README.md` retains the original README.
`upstream-provenance.json` records original file SHA-256 hashes and the root
lockfile's registry tarball URL and SHA-512 integrity:

- Tarball: https://registry.npmjs.org/braces/-/braces-3.0.3.tgz
- Integrity: `sha512-yQbXgO/OSZVD2IsiLlro+7Hf6Q18EJrKSEsdoMzKePKXct3gvD8oLcOQdIzGupr5Fj+EDe8gO/lxc1BzfMpxvA==`
- Source: https://github.com/micromatch/braces/tree/3.0.3
- Advisory: https://github.com/advisories/GHSA-vfj7-8cjw-p6xm

`upstream.patch` is the exact unified diff for implementation and package/README
changes, including the new guard. `patch-manifest.json` separately hashes the
fork's files. Do not compare patched bytes against the upstream hash map.
`upstream-fixtures.json` captures 130 ordinary pattern/option combinations from
the original installed implementation before replacement (650 method results).
Upstream authorship and license notices remain unchanged. Dependency
`fill-range` remains `^7.1.1`.

## Security boundary

The parser rejects a 65th nested brace **or parenthesis** container with a
`SyntaxError` before adding it to the parser stack. The fixed nesting ceiling is
64 across mixed containers, including unbalanced patterns. Quotes, escapes and
square-bracket literals still follow upstream parsing rules; literal delimiters
do not consume nesting depth. Upstream's 10,000-character maximum remains.
Options cannot increase or disable the security bound.

Every `lib/compile`, `lib/expand` and `lib/stringify` entry validates the AST
iteratively before recursive work, including direct `require` calls and
internal calls. Root depth is zero; 64 nested containers and their terminal text
leaf are allowed. The traversal follows `nodes` edges only; legal `parent` and
`prev` backreferences are ignored. Child-edge cycles fail with `SyntaxError`.
Malformed child arrays/text values also fail closed. Validation is bounded at
131,072 node visits, including repeated visits of shared DAG subtrees. This
prevents a small shared graph from creating unbounded preflight work. No
`RangeError` is caught after stack exhaustion.

Expand's two upward parent-chain loops also enforce 64 hops. This prevents
malformed caller-supplied parent cycles from hanging expansion without rejecting
the parser's normal parent/prev reference cycles. Generated expansion-array
recursion remains bounded by the validated AST depth for normal string nodes.

The ordinary public API and results are retained for supported inputs within
these bounds. Inputs exceeding the fixed limit now throw intentionally. This
mitigates the advisory's nesting/recursive-walker stack-exhaustion path; it is
not a general execution sandbox or a guarantee against combinatorial expansion.
Existing `rangeLimit` behavior is unchanged, including upstream's explicit
option to disable it. Accessor/proxy code supplied as AST objects is caller code
and is outside this plain-data AST contract.

## Verification and maintenance

Run `node --test tests/braces-security.test.mjs` from the repository root.
Tests cover deep brace/paren/mixed patterns below the character limit, the
64/65 boundary, public and direct-library AST methods, child cycles, legal
backreferences, malformed parent cycles, bounded shared-DAG validation, normal
API parity, and existing range limits. CI must verify the installed fork bytes
against `patch-manifest.json` and execute these tests; a clean npm audit alone
cannot establish coverage for a renamed local package. Root dependency/lockfile
integration is managed separately from this source patch.

Reassess this fork when upstream ships an independently reviewed remedy.
Changing any fork file requires updating the exact patch and fork manifest and
rerunning installed-package verification and attack tests. Never relabel the
fork as a purported patched upstream release.
