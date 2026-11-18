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

## Phase 2 — bot model extraction

- Scope: extract 3 bot enums and 17 serializable domain models (20 public types) from `zrouter_bot.py` into `zrouter_bot_models.py`.
- Compatibility: `zrouter_bot.py` re-exports the same names; no existing import path is intentionally removed.
- Packaging: added the module to `pyproject.toml`, Docker runtime/web images, and Makefile lint/source bundle targets.
- Regression coverage: added `test_zrouter_bot_models.py` for identity of compatibility re-exports and serialization round trips.
- Current implementation commit: `83d7da4fd121f7b0092606d27824d8ef96e9f4c8`.
- CI for this commit: **PENDING**. Do not treat Phase 2 as validated until the matching CI run passes.
- Local execution: not run in this session.

## Evidence policy

The automated results above apply to the validated code commit listed above. Any later code change requires a new validation run. Documentation-only updates do not change the tested runtime code.
