# 0003. One character-conditioned policy instead of one model per character

- **Status:** Accepted
- **Date:** 2026-09-28

## Context

The game has 100+ characters. They share movement, ball physics, jumping, kicking and heading. They differ in:

- five upgradable stats (Speed, Jump, Kick, Power, Dash);
- a unique power shot, often with air, ground and counter-attack variants.

The opponent's power shot changes how to defend as much as our own character changes how to attack.

## Decision

Train **one policy conditioned on (own character, opponent character)**.

- **Inputs:** character embeddings plus normalized stat vectors.
- **Power shots:** a dedicated sub-module decides when and where to trigger ours and how to defend against theirs.
- **Specialists:** a character gets a specialist (fine-tuned from the generalist, optionally distilled back) only when evaluation shows a gap.

**Development starts with a single matchup: South Korea (straight-line power shot) vs. the first Arcade opponent.**

## Consequences

- Shared skills are learned once, from all the data.
- Adding a character means measuring its stats and implementing its power shot in the simulator, not starting a new project.
- The simulator must support per-character parameters and power shot implementations from the start, even while only one matchup is used.

## Alternatives considered

- **One model per character:** duplicates learning of shared skills and splits the data 100 ways. It would also need per-opponent handling, up to 100×100 matchups.

Precedents:
- OpenAI Five used one model across many heroes that share mechanics.
- AlphaStar used separate agents per race, because StarCraft's races are nearly different games. Head Soccer's characters are much closer to the Dota case.
