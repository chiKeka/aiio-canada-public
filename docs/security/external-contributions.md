# Reviewing external contributions

Contributors should fork this public repository and open a focused pull request. Working on an issue does not require collaborator/write access, credentials or access to the private research repository. A public profile cannot establish a person's identity or guarantee their code is safe; review the submitted change on its merits.

## Before approving a workflow or running code

1. Inspect the complete diff, including renamed/deleted files, and record the exact head SHA. Recheck after every new push.
2. Review executable changes before running anything: dependencies and lockfiles, package lifecycle scripts, Python/Node imports, shell commands, tests, browser fixtures, configuration, workflow/action changes and code loaded by the app. Tests and documentation examples can execute commands too.
3. Never run an unreviewed `npm ci`, build, test, helper script or downloaded artifact on a machine with personal credentials. The current CI uses `npm ci`, which can execute dependency and lifecycle scripts. A green check does not prove benign code.
4. Approve fork workflows only after inspecting the exact diff. Prefer disposable GitHub-hosted runners with read-only tokens and no private data or secrets. Do not copy a fork branch into a privileged branch merely to bypass approval.
5. Keep this public repository separate from private source archives and production. Do not supply real client records, private `.env` files, SSH/cloud credentials or a deployment token to a contributor's code or preview build. Do not promote contributor-generated artifacts into privileged jobs without reviewing their provenance and contents.

For issue #3, the intended scope is an offline checker for the three onboarding documents, fixture tests and its documented command. There is no need for credentials, network requests, workflow edits, source acquisition, deployment changes or new third-party dependencies. Read the checker implementation before executing it, including subprocess/import/path handling and any claimed test harness.

## Maintainer-owned offline path triage

Use the script from a trusted, reviewed base checkout, not a contributor's version. Export filenames through the GitHub PR metadata API without checking out or running the PR:

```bash
gh api --paginate repos/chiKeka/aiio-canada-public/pulls/PR_NUMBER/files --jq '.[].filename' > /tmp/aiio-pr-paths.txt
python3 scripts/review_contribution_paths.py --paths-file /tmp/aiio-pr-paths.txt
```

The helper reads path strings only, performs no network access or subprocess execution, and does not open the named files. It highlights execution/configuration/data-sensitive paths and returns 2 when additional review is indicated. Return 0 means no listed path matched those categories, **not** that the diff is safe. The API listing can omit very large diffs and renamed old paths; inspect the complete Git diff separately. Unknown files require review too.

Run its offline fixture tests with:

```bash
python3 -m unittest discover -s tests -p test_review_contribution_paths.py -v
```

## Workflow boundaries to preserve

Current workflows use `pull_request` and GitHub-hosted runners with explicit read-only permissions. Do not introduce privileged `pull_request_target` or `workflow_run` handling of contributor code/artifacts, self-hosted runners, write tokens or secrets without a separate security review. Workflow approval authorizes execution of that revision, not merging it.

Review third-party actions and verify immutable commit pins against their official upstream repositories before adopting pinning changes. Current workflows use version tags; this policy does not silently change their execution or repository settings. Avoid interpolating PR titles, bodies or branch names into shell source. Treat logs and artifacts as untrusted and potentially public.

## Before merging

Inspect the final head, verify the relevant checks against that head and obtain explicit maintainer approval for that concrete change. Check that the PR did not weaken its own tests or security controls. Preserve source rights/privacy exclusions, scientific limitations and vendor notices. Automatic approvals, previous contributions and issue assignment are not substitutes for review. Deployment is a separate decision.

CODEOWNERS identifies the current maintainer for review routing. **It is not an access-control gate by itself.** Required-review and branch-protection settings must be configured separately; this document does not enable them. On a repository with one maintainer, requiring another approver for that maintainer's own PR can block legitimate work: select an explicit policy rather than granting strangers write access.

## Official guidance

- [Review fork changes before approving workflows](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/approve-runs-from-forks)
- [Least privilege, untrusted checkout and action pinning](https://docs.github.com/en/actions/reference/security/secure-use)
- [Required reviews and status checks](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
