#!/usr/bin/env bash
# Reproducible Android SDK + emulator setup for Head Soccer AI (macOS on Apple Silicon).
# Idempotent: re-running only installs or fixes what is missing.
#
# Usage: scripts/setup_android.sh
# Env:   ANDROID_HOME (default ~/Library/Android/sdk), AVD_NAME (default hsai)
set -euo pipefail

ANDROID_HOME="${ANDROID_HOME:-$HOME/Library/Android/sdk}"
AVD_NAME="${AVD_NAME:-hsai}"

# Pinned bootstrap; sdkmanager then manages everything else under ANDROID_HOME.
CMDLINE_TOOLS_BUILD="15859902"
CMDLINE_TOOLS_SHA256="835b62a26162b229b441d1f6d4680383815a270809eb33522c0d480fa5002c4e"

# Android 14 with Google Play, so the game is installed from the official store (ADR-0002).
SYSTEM_IMAGE="system-images;android-34;google_apis_playstore;arm64-v8a"

if [[ "$(uname -s)" != "Darwin" || "$(uname -m)" != "arm64" ]]; then
  echo "error: this script targets macOS on Apple Silicon" >&2
  exit 1
fi

# sdkmanager needs Java 17+. Scoped to this script so the user's global JAVA_HOME is untouched.
if ! JAVA_HOME="$(/usr/libexec/java_home -v 17+ 2>/dev/null)"; then
  echo "error: a JDK >= 17 is required (e.g. brew install --cask temurin)" >&2
  exit 1
fi
export JAVA_HOME ANDROID_HOME

SDKMANAGER="$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager"
AVDMANAGER="$ANDROID_HOME/cmdline-tools/latest/bin/avdmanager"

if [[ ! -x "$SDKMANAGER" ]]; then
  echo "==> Installing Android command-line tools (build $CMDLINE_TOOLS_BUILD)"
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' EXIT
  zip="$tmp/cmdline-tools.zip"
  curl -fL --progress-bar -o "$zip" \
    "https://dl.google.com/android/repository/commandlinetools-mac_arm64-${CMDLINE_TOOLS_BUILD}_latest.zip"
  echo "$CMDLINE_TOOLS_SHA256  $zip" | shasum -a 256 -c -
  unzip -q "$zip" -d "$tmp"
  mkdir -p "$ANDROID_HOME/cmdline-tools"
  rm -rf "$ANDROID_HOME/cmdline-tools/latest"
  mv "$tmp/cmdline-tools" "$ANDROID_HOME/cmdline-tools/latest"
fi

echo "==> Android SDK licenses (review and accept)"
"$SDKMANAGER" --licenses

echo "==> Installing platform-tools, emulator and $SYSTEM_IMAGE"
"$SDKMANAGER" --install "platform-tools" "emulator" "$SYSTEM_IMAGE"

if ! "$AVDMANAGER" list avd -c | grep -qx "$AVD_NAME"; then
  echo "==> Creating AVD '$AVD_NAME'"
  # "no" answers the "custom hardware profile?" prompt; the profile is set below.
  echo "no" | "$AVDMANAGER" create avd --name "$AVD_NAME" --package "$SYSTEM_IMAGE"
fi

config="$HOME/.android/avd/$AVD_NAME.avd/config.ini"

set_cfg() {
  local key="$1" value="$2"
  if grep -q "^${key}[[:space:]]*=" "$config"; then
    sed -i '' "s|^${key}[[:space:]]*=.*|${key}=${value}|" "$config"
  else
    echo "${key}=${value}" >>"$config"
  fi
}

echo "==> Applying hardware profile to $config"
# 1080x1920 (16:9): headroom for sub-pixel physics measurements in F1; capture can
# request downscaled frames. 2 GB guest RAM because the host only has 8 GB.
set_cfg hw.lcd.width 1080
set_cfg hw.lcd.height 1920
set_cfg hw.lcd.density 420
set_cfg skin.name 1080x1920
set_cfg skin.dynamic yes
set_cfg showDeviceFrame no
set_cfg hw.ramSize 2048
set_cfg vm.heapSize 256
set_cfg disk.dataPartition.size 8G
set_cfg hw.gpu.enabled yes
set_cfg hw.gpu.mode host
set_cfg hw.keyboard yes
set_cfg PlayStore.enabled true
# The agent needs neither; keep the host microphone and camera out of the guest.
set_cfg hw.audioInput no
set_cfg hw.camera.back none
set_cfg hw.camera.front none

echo "==> Installed SDK packages"
"$SDKMANAGER" --list_installed

echo
echo "Done. Start the emulator with: scripts/start_emulator.sh"
