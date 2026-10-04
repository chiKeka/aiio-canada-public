# Security policy

Please report a suspected credential exposure or security vulnerability through
GitHub's private vulnerability reporting feature. Do not open a public issue
containing secrets, personal information or exploit details.

The repository scans its full reachable history for secrets and audits locked
production dependencies on pushes, pull requests and a weekly schedule.
Machine-specific filesystem paths are rejected by CI.
