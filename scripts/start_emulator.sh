#!/usr/bin/env bash
# Start the project AVD with the gRPC control endpoint enabled.
#
# Usage: scripts/start_emulator.sh [extra emulator flags...]
# Env:   ANDROID_HOME (default ~/Library/Android/sdk), AVD_NAME (default hsai),
#        HSAI_GRPC_PORT (default 8554), HSAI_GPU (default host)
set -euo pipefail

ANDROID_HOME="${ANDROID_HOME:-$HOME/Library/Android/sdk}"
AVD_NAME="${AVD_NAME:-hsai}"
HSAI_GRPC_PORT="${HSAI_GRPC_PORT:-8554}"
HSAI_GPU="${HSAI_GPU:-host}"

# -grpc-use-token: the endpoint requires the per-session token the emulator writes to its
# discovery file, so other local processes cannot drive the emulator.
# -feature GuestAngle: GLES runs inside the guest (ANGLE over Vulkan/MoltenVK), which exposes the
# RGB565 EGL config Head Soccer (cocos2d-x 2.x) requires (ADR-0007).
exec "$ANDROID_HOME/emulator/emulator" \
  -avd "$AVD_NAME" \
  -grpc "$HSAI_GRPC_PORT" \
  -grpc-use-token \
  -gpu "$HSAI_GPU" \
  -feature GuestAngle \
  -no-boot-anim \
  "$@"
