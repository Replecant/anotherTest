#!/usr/bin/env bash
# CI helper (probe branch only): dumps javap signatures of selected Minecraft / NeoForge classes into $1.
OUT="$1"; : > "$OUT"
JARS=""
for j in $(find ~/.gradle build -name '*.jar' -size +5M 2>/dev/null | sort -u); do
  if unzip -l "$j" 2>/dev/null | grep -qE 'net/minecraft/client/Minecraft.class|net/neoforged/neoforge/common/NeoForge.class'; then
    echo "jar: $j" >> "$OUT"; JARS="$JARS:$j"
  fi
done
for c in $(cat "$(dirname "$0")/api_probe_classes.txt"); do
  echo "===== $c" >> "$OUT"
  javap -p -cp "${JARS#:}" "$c" >> "$OUT" 2>&1 || true
done
