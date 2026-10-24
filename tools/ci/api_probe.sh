#!/usr/bin/env bash
# CI helper: dumps javap signatures of selected Minecraft / NeoForge classes into $1 (a file),
# so that code can be written against the exact 1.21.11 API without a local build.
OUT="$1"; : > "$OUT"
JAR=""
for j in $(find ~/.gradle /home/runner/.gradle /root/.gradle -name '*.jar' -size +15M 2>/dev/null | sort -u); do
  if unzip -l "$j" 2>/dev/null | grep -q 'net/minecraft/world/level/block/entity/BlockEntity.class'; then
    echo "candidate: $j" >> "$OUT"; JAR="$j"
  fi
done
echo "using: $JAR" >> "$OUT"
[ -z "$JAR" ] && exit 0
CLASSES="$(cat "$(dirname "$0")/api_probe_classes.txt")"
for c in $CLASSES; do
  echo "===== $c" >> "$OUT"
  javap -p -cp "$JAR" "$c" >> "$OUT" 2>&1 || true
done
