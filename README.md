# Head Soccer AI

An agent that plays [Head Soccer](https://apps.apple.com/us/app/head-soccer/id487119327) (D&D Dream) **from screen pixels only** and presses the on-screen buttons, aiming to beat the in-game CPU consistently. It runs first on the Android emulator on a Mac and later on a physical iPhone/iPad.

> **Status:** Phase 0 (feasibility) complete: [results](docs/experiments/2026-10-01-f0-feasibility.md). Next: Phase 1, measuring the game. See the [master plan](docs/PLAN.md) (Spanish) and the [architecture decision records](docs/adr/).

## How it works (planned)

```
game frames ─▶ perception ─▶ state estimator ─▶ policy ─▶ touch actuation ─▶ game
                (vision)     (tracking + physics)  (RL)     (multitouch)
```

- **Perception** turns each frame into a compact game state: ball, players, power gauges, score and clock.
- **The policy is trained with reinforcement learning in a purpose-built simulator.** The simulator's physics are calibrated against recordings of the real game. This follows the approach RLGym/RocketSim used for Rocket League, with the difference that here the state comes from vision instead of game memory.
- **A single policy covers every character.** It is conditioned on the character and the opponent instead of training one model per character.

## Scope and ethics

- **Offline modes against the CPU only.** The agent is never used in online multiplayer.
- **No game assets** (sprites, screenshots, datasets) are committed to this repository. Only code, metrics and short demo clips are.

## Development

Requirements: macOS on Apple Silicon and [uv](https://docs.astral.sh/uv/).

```bash
uv sync                      # create the environment
uv run pre-commit install    # enable git hooks
uv run pytest                # run tests
scripts/setup_android.sh     # install the Android SDK, emulator and the project AVD
scripts/start_emulator.sh    # boot the emulator (Guest ANGLE, gRPC control endpoint)
scripts/install_game.sh      # install your own pinned copy of the game (see ADR-0007)
```

## License

[Apache-2.0](LICENSE). Head Soccer is a trademark of D&D Dream Corp.; this is an independent, non-commercial research project not affiliated with or endorsed by D&D Dream.
