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
for j in ${JARS//:/ }; do unzip -l "$j" | grep -oE 'net/minecraft/world/(attribute|timeline|level/block)/[A-Za-z]+\.class' >> "$OUT"; done
# --- whole vanilla worldgen + dimension data as a tarball (reference for datapack authors) ---
DJ=$(readlink -f $(ls build/moddev/artifacts/*client-extra*.jar 2>/dev/null | head -1))
echo "data jar: $DJ" >> "$OUT"
if [ -n "$DJ" ]; then
  mkdir -p /tmp/vanilla && (cd /tmp/vanilla && unzip -q -o "$DJ" 'data/minecraft/worldgen/*' 'data/minecraft/dimension_type/*' 'data/minecraft/tags/worldgen/*' 'data/minecraft/tags/block/*' 'data/minecraft/tags/entity_type/*' 'assets/minecraft/models/block/*' 'assets/minecraft/blockstates/*' 'data/minecraft/timeline/*' 'data/minecraft/tags/timeline/*' 'assets/minecraft/items/*' 'assets/minecraft/models/item/*' 'assets/minecraft/textures/block/*' 2>/dev/null)
  tar -czf "$(dirname "$OUT")/vanilla_data.tgz" -C /tmp/vanilla . && echo "vanilla data packed" >> "$OUT"
fi
