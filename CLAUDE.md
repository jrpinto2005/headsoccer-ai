# Head Soccer AI — notes for Claude

- **Plan and status:** `docs/PLAN.md` (Spanish, the working plan with the phase checklists). Decisions are recorded in `docs/adr/`. Read both before starting work in a new phase.
- **Language:** talk to the user in Spanish. Code, comments, README and ADRs are in English.
- **Quality bar:** pick the best engineering option, not the fastest. Measure before deciding (spikes and benchmarks) and record decisions as ADRs.
- **Environment:** macOS on Apple Silicon (M3, 8 GB RAM). Everything must be native arm64. Python 3.12 via uv.
  - `uv run pytest`, `uv run ruff check`, `uv run ruff format`, `uv run pyright`.
  - Tests that need a running emulator are marked `@pytest.mark.emulator`.
- **Android:** SDK at `~/Library/Android/sdk`, AVD `hsai`, provisioned by `scripts/setup_android.sh` and started by `scripts/start_emulator.sh` (gRPC on 8554 with a token).
- **Never commit game assets** (screenshots, video, sprites, APKs). Data lives outside git (DVC). The agent plays offline vs. the CPU only (ADR-0006).
