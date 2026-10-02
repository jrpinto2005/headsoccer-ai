#!/usr/bin/env bash
# Install the pinned Head Soccer build (APK + OBB) on the running emulator (ADR-0004, ADR-0007).
#
# The files are the ones Google Play delivered, pulled from an emulator install. They are
# never committed; keep them in data/apks/<version>/ (gitignored). Checksums are verified
# so every machine runs byte-identical game files.
#
# Usage: scripts/install_game.sh [game_dir]   (default data/apks/headsoccer-7.1.5)
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
dir="${1:-$root/data/apks/headsoccer-7.1.5}"
ADB="${ANDROID_HOME:-$HOME/Library/Android/sdk}/platform-tools/adb"
PKG="com.dnddream.headsoccer.android"
VERSION="7.1.5"
OBB="main.340.$PKG.obb"

# sha256 of the Play-delivered files (APK signed by "CN=D&D Dream", cert SHA-256
# F7:25:00:81:71:6D:29:29:47:BD:F9:8E:82:7E:7E:C2:6E:B7:23:61:61:EC:A6:8C:07:15:0E:F3:6F:0E:F3:94).
cat >"${TMPDIR:-/tmp}/hsai-game.sha256" <<EOF
3f1bb74baddf9dd515afc995d31eaf0f0d548a9fda56a4716f7140467a5770f5  base.apk
c15a06791ec6279cc7d8adf68083cc10e01bed91471d61b38d5952165489876c  $OBB
EOF
(cd "$dir" && shasum -a 256 -c "${TMPDIR:-/tmp}/hsai-game.sha256")

"$ADB" wait-for-device
"$ADB" install -r "$dir/base.apk"
"$ADB" shell mkdir -p "/sdcard/Android/obb/$PKG"
"$ADB" push -q "$dir/$OBB" "/sdcard/Android/obb/$PKG/"

installed="$("$ADB" shell dumpsys package "$PKG" | grep -m1 versionName | cut -d= -f2 | tr -d '\r')"
if [[ "$installed" != "$VERSION" ]]; then
  echo "error: installed version is '$installed', expected $VERSION" >&2
  exit 1
fi

# Nothing may cover the game: suppress the one-time "Viewing full screen" hint and hide
# crash/ANR dialogs (they are still logged in logcat).
"$ADB" shell settings put secure immersive_mode_confirmations confirmed
"$ADB" shell settings put global hide_error_dialogs 1

echo "Head Soccer $VERSION installed."
