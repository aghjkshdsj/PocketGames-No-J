#!/bin/bash
# Host tests: the app's pure Swift logic compiled for the CI host (Linux or macOS) with the test
# programs in tests/host, no simulator and no device. Each test program exits nonzero on a failure.
#   tests/host/run.sh [<build-dir>]
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
OUT="${1:-${RUNNER_TEMP:-/tmp}/host-tests}"
mkdir -p "$OUT"
# Interpreter address-space policy and the fatal startup line from the Forager device log.
cc -std=c11 -D_POSIX_C_SOURCE=200809L -Wall -Wextra -Werror -pthread \
    -I"$ROOT/App/Sources/Native" "$ROOT/App/Sources/Native/wine_startup.c" \
    "$HERE/wine_startup/main.c" -o "$OUT/wine-startup-tests"
"$OUT/wine-startup-tests" | tee "$OUT/wine-startup-tests.txt"
python3 "$ROOT/tests/wow_window_bounds_test.py"
python3 "$ROOT/tests/compliance_tools_test.py"
python3 "$ROOT/tests/app_store_preparation_test.py"
swiftc --version | head -1
# Sign-in status polling survives app-switch connection loss without replaying
# credentials or ignoring cancellation / the original session deadline.
swiftc -parse-as-library -O -o "$OUT/steam-auth-tests" "$ROOT/App/Sources/Steam/SwiftSteam/Auth/SteamAuthNetwork.swift" "$HERE/steam_auth/main.swift"
"$OUT/steam-auth-tests" | tee "$OUT/steam-auth-tests.txt"
# Steam Cloud saves: path mapping, comparison, sync decisions, backup retention.
swiftc -O -o "$OUT/steam-cloud-tests" "$ROOT/App/Sources/Steam/SteamCloudCore.swift" "$HERE/steam_cloud/main.swift"
"$OUT/steam-cloud-tests" | tee "$OUT/steam-cloud-tests.txt"
swiftc -O -o "$OUT/steam-backup-tests" "$ROOT/App/Sources/Steam/SteamCloudCore.swift" "$ROOT/App/Sources/Steam/SteamCloudBackups.swift" "$HERE/steam_backups/main.swift"
"$OUT/steam-backup-tests" | tee "$OUT/steam-backup-tests.txt"
# DanPort Dock: Steam's UDP/TCP server list for Valve's client, and the config.vdf edit.
swiftc -O -o "$OUT/steam-cm-tests" "$ROOT/App/Sources/Steam/SteamCMList.swift" "$HERE/steam_cm/main.swift"
"$OUT/steam-cm-tests" | tee "$OUT/steam-cm-tests.txt"
# The on-screen controller (stick, D-pad, merging with a physical pad, layouts) and Game settings.
swiftc -O -o "$OUT/touch-pad-tests" "$ROOT/App/Sources/Engine/TouchPadCore.swift" "$ROOT/App/Sources/Engine/GameSettingsCore.swift" "$ROOT/App/Sources/Engine/PadStyleCore.swift" "$HERE/touch_pad/main.swift"
"$OUT/touch-pad-tests" | tee "$OUT/touch-pad-tests.txt"
# Driving the app's UI with a controller: focus moves, repeat on hold, the stick, the menu chord.
swiftc -O -o "$OUT/pad-nav-tests" "$ROOT/App/Sources/Engine/PadNavCore.swift" "$HERE/pad_nav/main.swift"
"$OUT/pad-nav-tests" | tee "$OUT/pad-nav-tests.txt"
