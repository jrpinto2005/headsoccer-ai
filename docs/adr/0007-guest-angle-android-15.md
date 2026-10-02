# 0007. Android 15 ATD image with Guest ANGLE, and a pinned game build

- **Status:** Accepted
- **Date:** 2026-10-01
- **Supersedes:** the system image, GPU mode and install method of [ADR-0002](0002-android-emulator-first.md). The rest of 0002 (emulator first, gRPC capture and input) stands.

## Context

Head Soccer 7.1.5 is a cocos2d-x 2.x game. It crashed on launch with `IllegalArgumentException: No config chosen` because it asks `GLSurfaceView` for an exact RGB565 config with a stencil of at least 8 bits. We measured the EGL configs the guest exposes with [`scripts/egl_probe.sh`](../../scripts/egl_probe.sh):

| Image | GPU mode | Guest EGL configs | RGB565 + D16/S8 match |
|---|---|---|---|
| Android 14 (API 34) Google Play | `host` | 3 (RGB888/RGBA8888, D24S8) | no |
| Android 14 (API 34) Google Play | `swiftshader_indirect` | 3 | no |
| Android 11 (API 30) Google Play | `swiftshader_indirect` | 3 | no |
| Android 16 (API 36) Google Play | `host` + `-feature GuestAngle` | 75 | **yes** |
| Android 15 (API 35) Google Play | `host` + `-feature GuestAngle` | 75 | **yes** |
| Android 15 (API 35) ATD | `host` + `-feature GuestAngle` | 75 | **yes** |

- **Why the first three fail:** gfxstream itself does not filter RGB565. The limit comes from the host GLES translator on macOS.
- **What Guest ANGLE does differently:** it runs GLES inside the guest, on top of Vulkan → MoltenVK → the M3 GPU, and generates its own full config list.
- **Why not API 36:** the emulator warns that Guest ANGLE "is still unstable for API > 35". For API 35 it recommends Guest ANGLE, because hardware OpenGL rendering is deprecated on macOS.

Among the API 35 images, the deciding factor was memory on the 8 GB host:

| API 35 image | Boot | Guest RAM available after boot | First game launch |
|---|---|---|---|
| Google Play | 44 s | 1.32 GB | `system`/`systemui` ANRs; the game never settled |
| ATD (`aosp_atd`) | 15 s | 1.78 GB | Stable in the game window after 15 s, 0 ANRs |

In the Play image, Google Search, Play services and the Play Store took most of the guest's RAM. The game uses none of them.

## Decision

- **Image:** Android 15 (API 35) **ATD** (`system-images;android-35;aosp_atd;arm64-v8a`), started with `-gpu host -feature GuestAngle`. ATD is Google's slimmed image for automated testing and has no Google services.
- **Game install:** the Play-delivered build of 7.1.5 (`base.apk` and `main.340…obb`) is installed by [`scripts/install_game.sh`](../../scripts/install_game.sh).
  - The files were pulled from a Play Store install.
  - They are kept privately under `data/apks/` and never committed.
  - The script verifies their SHA-256. The APK is signed by `CN=D&D Dream`, certificate SHA-256 `F7:25:…:F3:94`.
- **The game can never update itself.** The image has no Play Store, which enforces ADR-0004 by construction.
- **Device preparation for automation:**
  - error and ANR dialogs hidden (`hide_error_dialogs=1`; they are still logged);
  - the immersive-mode hint suppressed;
  - landscape orientation set over gRPC.
- **Touch coordinates:** frames arrive upright, and touches use the panel's natural orientation. In landscape, frame `(x, y)` maps to touch `(1079 − y, x)`. This was verified with Android's pointer-location overlay and `getevent`, and is implemented in `hsai.emulator.coords.TouchMapper`.

## Consequences

- The game renders on the real GPU through MoltenVK, not on a software rasterizer.
- Without Play services the game logs "Google Play services is missing" and shows no dialog. Play Games sign-in and cloud saves are unavailable, which is fine for a fresh, local account.
- **Menus ignore taps while popups animate in.** Menu automation must wait for the screen to settle, then verify the effect of every tap.
- Memory remains the binding constraint on an 8 GB host. Heavy host apps should be closed during long runs.
- Guest ANGLE is newer than the host renderer. Long unattended runs must watch for renderer crashes (the crash buffer and frame stalls).

## Alternatives considered

- **Patching the APK's EGL config chooser:** modifies the developer's software and breaks signature provenance. Rejected (ADR-0006).
- **Older images, SwiftShader or host rendering:** measured above; they do not expose RGB565.
- **API 35 with Google Play:** works, but its memory footprint caused system ANRs on this host.
- **API 36:** works, but the emulator labels Guest ANGLE unstable there.
- **A physical Android phone, Genymotion or BlueStacks Air:** kept as fallbacks; not needed now.
