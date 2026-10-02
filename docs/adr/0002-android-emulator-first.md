# 0002. Android emulator on Apple Silicon as the first platform

- **Status:** Accepted; system image, GPU mode and install method superseded by [0007](0007-guest-angle-android-15.md)
- **Date:** 2026-09-28

## Context

Head Soccer ships for iOS and Android only; there is no Mac App Store build. The final target is a physical iPhone/iPad, but iOS offers no supported way to inject multitouch into a third-party app. We need a platform with fast frame capture, programmatic multitouch, and reproducible resets.

## Decision

Use Google's **Android Emulator** with an **Android 14 (API 34) Google Play arm64-v8a** image, provisioned by [`scripts/setup_android.sh`](../../scripts/setup_android.sh).

- Install the game from the Play Store, never from third-party APK sites.
- Drive the emulator through its **gRPC endpoint**:
  - `streamScreenshot` for raw RGBA frames with no video encode/decode;
  - `sendTouch` / `streamInputEvent` for multitouch.
- Require the per-session gRPC token (`-grpc-use-token`).
- Hardware profile:
  - 1080×1920 at 420 dpi, for sub-pixel measurements in Phase 1 (frames can be requested downscaled);
  - 2 GB guest RAM;
  - host GPU.

## Consequences

- Snapshots give reproducible starting states.
- The same machine runs the game, the perception stack and the policy. RAM (8 GB) must be watched.
- `sdkmanager`/`avdmanager` print a deprecation notice in favor of the new `android` CLI. They still work; revisit when the `android` CLI can express the full hardware profile.
- Porting to iOS (Phase 8) needs new capture and actuation layers. The state interface stays the same.

## Alternatives considered

- **BlueStacks or other consumer emulators:** closed, harder to script, and have no gRPC API.
- **A physical Android phone with scrcpy + ADB:** scrcpy adds an H.264 encode/decode, and `adb shell input` is slow and single-touch. No snapshots.
- **An iOS app on Apple Silicon:** not offered for this game.
