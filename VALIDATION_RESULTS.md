# Validation Results

This file records evidence for a specific commit. It is not a permanent release attestation.

## Current refactor branch

- Base: `main`
- Branch: `refactor/openmausbot-router-architecture`
- Validation status: **PENDING CI**
- Local test execution: **NOT RUN** (changes were authored through the GitHub repository API; no local checkout/runtime was available in this session)
- Runtime integration: **NOT VERIFIED**
- Docker/package builds: **NOT VERIFIED**

The pull request's GitHub Actions results are the authoritative validation evidence for this change. Update this file only after inspecting the exact workflow run and commit SHA.

## Required gates

| Gate | Required evidence | Status |
|---|---|---|
| Unit tests | Full pytest suite, including provider registry and routing fail-closed tests | Pending |
| Lint | Ruff check | Pending |
| Format | Ruff format check | Pending |
| Build | Python package / CLI build | Pending |
| Security | CodeQL or equivalent scan; manual review of auth, provider URL validation, model allowlist | Pending |
| Runtime | Loopback and authenticated non-loopback smoke tests; streaming disconnect test | Pending |
| Compatibility | CLI, OpenAI-compatible API, GUI/TUI imports, provider config compatibility | Pending |

## Evidence policy

- Record the exact commit SHA and workflow run URL.
- Distinguish passed, failed, skipped, blocked, and not-run checks.
- Do not claim a coverage percentage or production readiness without current machine-generated evidence.
