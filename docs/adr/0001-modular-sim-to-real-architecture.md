# 0001. Modular pipeline with sim-to-real transfer in state space

- **Status:** Accepted
- **Date:** 2026-09-28

## Context

The game only runs in real time, and the host (M3, 8 GB RAM) fits a single instance. At 15 decisions/s that is at most ~1.3M environment steps per day, before menus and ads. Competitive play with PPO typically needs 10⁸–10⁹ steps, which would take months to years on the real game.

## Decision

Split the agent into **perception → state estimation → policy → actuation**.

- The policy consumes a compact, normalized game state in field coordinates, not pixels.
- It is trained with RL in a **purpose-built simulator** whose physics are fitted to real recordings (system identification).
- It is transferred to the real game through the perception stack, with domain randomization over physics, latency and perception noise.

## Consequences

- Training throughput is bounded by the simulator (target ≥10⁶ steps/s on one GPU), not by the game.
- The simulator does not need to look like the game, only to behave like it.
- Each module has its own metrics, so failures can be attributed to a specific module.
- Main risk: the physics gap between simulator and game. Mitigations: system ID, randomization, real-world fine-tuning, and a scripted fallback.
- Requires a measured game specification (Phase 1) before building the simulator.

## Alternatives considered

- **End-to-end RL from pixels on the real game:** not feasible with this sample budget.
- **A world model learned from recordings (DreamerV3/DIAMOND style):** avoids hand-building a simulator, but needs large amounts of real data and is harder to validate. Kept as an optional research track for comparison.
- **Pure behavior cloning of human play:** capped at the demonstrator's level. Used only as a warm start.

Precedent: RLGym + RocketSim (Rocket League), where Nexto was trained in a simulator and deployed in the real game.
