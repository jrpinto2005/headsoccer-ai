# Architecture Decision Records

Each significant decision is recorded as a short ADR: context, decision, consequences, alternatives. ADRs are immutable once accepted: to change a decision, write a new ADR that supersedes the old one.

| ADR | Title | Status |
|---|---|---|
| [0001](0001-modular-sim-to-real-architecture.md) | Modular pipeline with sim-to-real transfer in state space | Accepted |
| [0002](0002-android-emulator-first.md) | Android emulator on Apple Silicon as the first platform | Accepted |
| [0003](0003-single-character-conditioned-policy.md) | One character-conditioned policy instead of one model per character | Accepted |
| [0004](0004-pin-game-version.md) | Pin the game version | Accepted |
| [0005](0005-tooling-and-repo-standards.md) | Tooling and repository standards | Accepted |
| [0006](0006-scope-ethics-and-assets.md) | Scope, ethics and game assets | Accepted |

Pending decisions (to be settled by benchmark or spike): simulator technology (JAX vs. C + PufferLib), detector architecture. See [PLAN.md §4](../PLAN.md).

New ADRs start from [the template](template.md).
