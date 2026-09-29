# 0006. Scope, ethics and game assets

- **Status:** Accepted
- **Date:** 2026-09-28

## Context

A strong game-playing bot can be misused against real players: a Rocket League RL bot was put into ranked matches by third parties. Game art and recordings belong to D&D Dream.

## Decision

- The agent plays **offline modes against the in-game CPU only**. No online multiplayer support will be built, and none will be merged.
- **No game assets are committed:**
  - no sprites, extracted files or APKs;
  - no screenshot or video datasets.
  - Datasets are private (DVC remote). The public repo holds code, metrics, diagrams and short demo clips.
- The game is installed from official stores only.
- The README states that the project is not affiliated with D&D Dream.

## Consequences

- The simulator's debug renderer uses simple shapes, not game art.
- Anyone reproducing the results must record their own data with their own copy of the game. The tooling makes this a single command.

## Alternatives considered

- **Publishing the datasets for reproducibility:** redistributes the developer's art.
