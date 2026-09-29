# 0005. Tooling and repository standards

- **Status:** Accepted
- **Date:** 2026-09-28

## Context

This is a long-lived, public portfolio project that mixes real-time systems, computer vision and RL. It needs reproducible environments and experiments, and it needs to be approachable for readers.

## Decision

- **Environment:**
  - Python 3.12 managed by **uv**, with a locked `uv.lock` and a `src/` layout (package `hsai`).
  - Native arm64 toolchain on the Mac: arm64 Homebrew first in `PATH`, uv-managed CPython.
- **Quality:**
  - **ruff** for lint and format, **pyright** (standard mode) and **pytest**.
  - **pre-commit** runs the locked tool versions.
  - **GitHub Actions** CI on every push and PR.
  - Tests that need an emulator are marked `emulator` and skipped in CI.
- **Experiments and data** (introduced when first needed):
  - Hydra for configs;
  - Weights & Biases for experiment tracking;
  - DVC with a cloud bucket for datasets.
- **Documentation:**
  - ADRs for decisions.
  - Code, README and ADRs in **English** for a wider audience.
  - The working plan ([PLAN.md](../PLAN.md)) in Spanish.
- **License:** Apache-2.0.
  - Any dependency with a copyleft license (for example AGPL-3.0 detectors) needs an explicit ADR before it is adopted.
- **Compute budget:**
  - $0 through Phase 3 (Mac plus free Colab).
  - About $10–30/month from Phase 4, spent on hourly GPU rentals for large RL runs.

## Consequences

- A fresh clone plus `uv sync` reproduces the environment exactly.
- Heavier tools (Hydra, W&B, DVC) are added in the phase that needs them, not up front.

## Alternatives considered

- **Poetry or conda:** slower, and uv's Python management covers our needs.
- **mypy:** pyright is faster and has better inference. Either would do.
- **MLflow:** self-hosting overhead. W&B's free tier covers a personal project.
