# GitHub and Vercel deployment

The research application can use a GitHub repository as its source of record and
a Vercel deployment as the public-web release gate. This review snapshot has no
Git history, remote or deployment binding; publishing or connecting it requires
a separate reviewed decision. The application
is a standard Next.js project; Vercel does not require secrets or environment
variables for the current public-data prototype.

## Deployment contract

- Runtime: Node.js 22 or newer.
- Framework preset: Next.js.
- Root directory: repository root.
- Install command: `npm install`.
- Build command: `npm run build`.
- Output directory: managed by Next.js and Vercel.
- Environment variables: none for the current research-prototype release.

The canonical Next.js commands are `npm run dev`, `npm run build`, and
`npm run start`. The alternative Sites build remains available through the
matching `*:sites` scripts. Both targets consume the same application and
published data files.

## Release sequence

1. Run the source, model, accessibility, and publication checks locally.
2. Commit the reviewed source changes.
3. Build the versioned release manifest and workbook from that clean source
   commit.
4. Commit the generated publication artifacts separately. The manifest's
   `code_commit` remains the reviewed source commit that produced them.
5. Push the reviewed branch and merge it through GitHub.
6. The existing Vercel Git integration deploys the merged `main` commit.
7. Verify the Vercel deployment result and inspect the production alias.

This two-commit sequence preserves reproducibility: the publication commit can
contain files generated from the exact source commit recorded in the manifest
without creating a self-referential commit hash.

## Continuous delivery boundary

`.github/workflows/weekly-evidence-refresh.yml` acquires public evidence and
opens a review pull request; it has no Vercel credentials and cannot deploy.
Vercel currently deploys every commit that reaches `main`, independently of
GitHub Actions. Therefore, changes must reach `main` only by reviewed merge.
A hard required-check rule should be enabled if the repository becomes public
or its GitHub plan supports private-repository rulesets. Until then, this is an
operating control rather than a platform-enforced branch rule.

## Public-release boundary

The website must continue to label scenario results as uncalibrated structural
diagnostics. A successful web deployment does not promote scenario-only or
assumed values to observations, forecasts, probabilities, or project-specific
delay estimates.
