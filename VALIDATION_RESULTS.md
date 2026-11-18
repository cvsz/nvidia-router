# Validation Results

Evidence for the refactor implementation is tied to the exact tested code commit.

## Refactor implementation

- Base branch: `main`
- Feature branch: `refactor/openmausbot-router-architecture`
- Validated code commit: `9df4fc92ab3d7fb46da066dd49c80120ba68fc40`
- Environment: GitHub-hosted Ubuntu runner, Python 3.14.10
- Local execution: **NOT RUN**; validation was performed by GitHub Actions.

## Automated results

| Gate | Result | Evidence |
|---|---|---|
| Ruff lint | **PASS** | [CI/CD run](https://github.com/cvsz/zrouter/actions/runs/44236819938) |
| Ruff format | **PASS** | [CI/CD run](https://github.com/cvsz/zrouter/actions/runs/44236819938) |
| Pytest | **PASS — 82 tests, 7 subtests** | [CI/CD run](https://github.com/cvsz/zrouter/actions/runs/44236819938) |
| PyInstaller Linux CLI | **PASS** | [Build artifact run](https://github.com/cvsz/zrouter/actions/runs/44236819938) |
| CodeQL: Python + GitHub Actions | **PASS** | [CodeQL run](https://github.com/cvsz/zrouter/actions/runs/44236819945) |
| Release job | **SKIPPED intentionally** | No release authorization was requested |

## Not verified

- Docker image build and runtime smoke test
- Windows executable build
- Live NVIDIA NIM requests, provider failover against real upstreams, and end-to-end streaming cancellation
- GUI/TUI runtime behavior on desktop platforms
- Production deployment, load testing, and external provider pricing verification

## Security limitations

- The bot vault remains plaintext JSON. POSIX permissions are restricted to directory `0700` and file `0600`; this does not provide encryption or protect against the same OS user, root, or compromised processes.
- Model discovery does not prove pricing. New models remain `free=false` and `pricing_status=unverified` until explicitly curated.
- Remote plaintext HTTP provider endpoints are rejected; only loopback HTTP is allowed.

## Phase 2 — bot models and storage extraction

- Scope: extract 3 bot enums and 17 serializable domain models (20 public types) into `zrouter_bot_models.py`.
- Extract `Vault`, `Memory`, and bot-home storage paths into `zrouter_bot_storage.py`.
- Compatibility: `zrouter_bot.py` re-exports the previous model names, storage classes, and path constants; existing imports remain supported.
- Packaging: added both modules to `pyproject.toml`, Docker runtime/web images, Makefile lint/source bundle targets, and PyInstaller dependency discovery.
- Regression coverage: tests verify all 20 model re-exports, model serialization round trips, storage class re-exports, and memory persistence.
- Validated code commit: `13e366f338317837201d270bf212e30e59adf67d`.
- [CI/CD run](https://github.com/cvsz/zrouter/actions/runs/44247416747): **PASS** — Ruff lint/format, **87 tests passed and 27 subtests passed**, Linux PyInstaller executable build, artifact upload.
- [CodeQL run](https://github.com/cvsz/zrouter/actions/runs/44247416878): **PASS** — Python and GitHub Actions.
- Local execution: not run in this session; validation was performed by GitHub Actions.

## Evidence policy

The automated results above apply to the validated code commit listed above. Any later code change requires a new validation run. Documentation-only updates do not change the tested runtime code.
