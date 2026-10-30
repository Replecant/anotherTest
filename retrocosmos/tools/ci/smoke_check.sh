#!/usr/bin/env bash
# Retro Cosmos checks on the headless game-test server log ($1), on top of the generic mod checks in build.yml.
LOG="$1"
grep -q "Retro Cosmos: countdown initiated" "$LOG" || { echo "::error::Mod did not load"; exit 1; }
grep "STATION SMOKE" "$LOG" || true
grep -q "STATION SMOKE OK" "$LOG" || { echo "::error::Freedom Station smoke test failed"; exit 1; }
