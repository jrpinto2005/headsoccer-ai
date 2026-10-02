# F0 feasibility spikes — 2026-10-01

**Setup:**
- **Host:** M3, 8 GB RAM.
- **Emulator:** 37.1.11, AVD on Android 15 ATD (API 35) with `-gpu host -feature GuestAngle` (ADR-0007), 1080×1920 panel used in landscape.
- **Game:** Head Soccer 7.1.5, fresh account, Arcade, South Korea vs. South Korea (CPU).
- **Code:** all measurements use `hsai.emulator` over gRPC with a session token.

## 1. Rendering compatibility

The game needs an EGL config with exact RGB565 and stencil ≥ 8 (cocos2d-x 2.x). Only Guest ANGLE exposes one. Full table in [ADR-0007](../adr/0007-guest-angle-android-15.md). Tool: [`scripts/egl_probe.sh`](../../scripts/egl_probe.sh).

## 2. Screen capture

Tool: [`scripts/spikes/capture_benchmark.py`](../../scripts/spikes/capture_benchmark.py). Each run streamed for 8 s with `streamScreenshot` in RGB888 during live play.

| Requested width | Delivered frame | FPS | Dropped (seq gaps) | Capture latency p50/p95/p99 | Inter-frame p50/p95 |
|---|---|---|---|---|---|
| native | 1920×1080 | 59.6 | 0 | 4.3 / 4.8 / 6.7 ms | 16.7 / 17.6 ms |
| 960 | 1920×1080 | 59.6 | 0 | 4.3 / 7.1 / 13.2 ms | 16.7 / 18.8 ms |
| 640 | 1920×1080 | 59.5 | 0 | 4.2 / 5.8 / 12.7 ms | 16.7 / 18.4 ms |

- The emulator ignores the requested downscale for streamed frames, so downscaling happens on the host.
- Native full-HD capture keeps up with the game's 60 Hz with no drops.
- "Capture latency" is the time from the emulator's frame-produced timestamp to Python receiving the frame.

## 3. Multitouch actuation

We held RIGHT and, while it was held, tapped JUMP and then KICK. Each of those taps was a separate finger in one `streamInputEvent` stream. In the captured frames:
- the game highlights each pressed button;
- the player walks right and jumps.

So simultaneous touches register correctly.

**Coordinates:** frames arrive upright, and touches are in the panel's natural orientation. In landscape, frame `(x, y)` maps to touch `(1079 − y, x)`. Verified with the pointer-location overlay and `getevent`; implemented in `hsai.emulator.coords.TouchMapper`.

**Pitfall:** taps that land while a popup is still animating in are ignored. Menu automation must wait for a settled screen and verify the effect of each tap.

## 4. End-to-end input latency

Tool: [`scripts/spikes/input_latency.py`](../../scripts/spikes/input_latency.py).

**Method:**
- 40 presses, alternating L and R, with random 150–350 ms gaps to decorrelate from vsync.
- Latency is measured until the first captured frame in which the game draws the button highlighted.
- That covers touch injection, the game's input handling and rendering, and capture.

| Interval | p50 | p95 | p99 |
|---|---|---|---|
| touch → game frame produced | 59.7 ms | 66.1 ms | 68.9 ms |
| touch → frame received in Python | 64.4 ms | 72.0 ms | 73.8 ms |

All 40 presses were detected.

**Implications:**
- The game sees an action about 4 frames after the agent sends it, with roughly 10 ms of spread.
- Perception and policy add an estimated ~10 ms on top, for a total of about 75–85 ms.
- The simulator must model a 4–5 frame action delay and randomize it within the measured distribution (ADR-0001).
- The real game, not our tooling, dominates the budget. Capture is ~4 ms.

## 5. Resources

- **API 35 image with Google Play:** under host memory pressure, the guest (2.5 GB, 1.3 GB available) hit `system`/`systemui` ANRs on first boot.
- **ATD image:** boots in 15 s, leaves 1.78 GB available in the guest, and ran the game with 0 ANRs.
- **Host:** swap usage was already above 6 GB with other apps open. Long runs should close heavy host apps.

## 6. First observations of the game

- **Fresh account:** the starting character is South Korea, and the first Arcade opponent is also South Korea, so the vertical slice is a mirror match.
- **Idle baseline:** with our player idle, the first match ended 2–5 for the CPU.
- **HUD:** power bars, flags, a 60 s clock and the score at the top, plus a row of round icons below the score whose meaning is still to be determined.
- **On-screen buttons:** L and R at the bottom left; POWER, KICK and JUMP at the bottom right.
- **Interruptions:**
  - a promo banner for another D&D Dream game appears at launch and has to be closed;
  - without Play services, the game only logs a warning and shows no dialog.
