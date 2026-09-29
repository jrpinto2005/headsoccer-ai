# 0004. Pin the game version

- **Status:** Accepted
- **Date:** 2026-09-28

## Context

The simulator is calibrated against measurements of the real game. An update could silently change physics, UI layout or CPU behavior and invalidate the calibration, the perception models and every evaluation result.

## Decision

- Target **Head Soccer 7.1.5** (latest as of June 2026).
- Disable auto-updates for the game in the emulator's Play Store.
- Keep an AVD snapshot of the known-good install.
- Record the game version in every dataset manifest and evaluation report.

## Consequences

- Results are comparable over time.
- A future version upgrade is an explicit, measured migration: re-run the Phase 1 measurements and the evaluation suite.
- If the game ever forces an update to stay playable, we write a new ADR.

## Alternatives considered

- **Always use the latest version:** breaks reproducibility and calibration without notice.
