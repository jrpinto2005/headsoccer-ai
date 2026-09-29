#!/usr/bin/env bash
# Compile tools/eglprobe and run it inside the running emulator (no APK needed).
#
# Usage: scripts/egl_probe.sh [r g b a depth stencil]
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
ANDROID_HOME="${ANDROID_HOME:-$HOME/Library/Android/sdk}"
ANDROID_JAR="$ANDROID_HOME/platforms/android-34/android.jar"
ADB="$ANDROID_HOME/platform-tools/adb"
JAVA_HOME="$(/usr/libexec/java_home -v 17+)"
export JAVA_HOME

build="$(mktemp -d)"
trap 'rm -rf "$build"' EXIT
"$JAVA_HOME/bin/javac" --release 11 -cp "$ANDROID_JAR" -d "$build" "$root/tools/eglprobe/EglProbe.java"
"$ANDROID_HOME/cmdline-tools/latest/bin/d8" --min-api 26 --lib "$ANDROID_JAR" --output "$build" "$build"/*.class

"$ADB" push -q "$build/classes.dex" /data/local/tmp/eglprobe.dex
"$ADB" shell CLASSPATH=/data/local/tmp/eglprobe.dex app_process /system/bin EglProbe "$@"
