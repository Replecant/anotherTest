#!/usr/bin/env bash
# Nature's Quirks checks on the headless game-test server log ($1), on top of the generic mod checks in build.yml.
LOG="$1"
grep -q "Nature's Quirks: the Overworld got a little stranger" "$LOG" || { echo "::error::Mod did not load"; exit 1; }
