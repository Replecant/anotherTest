#!/usr/bin/env python3
"""Generates the assets and data of Nature's Quirks (textures, models, loot, recipes, worldgen, lang).

Run from anywhere:  python3 naturequirks/tools/gen_resources.py   (needs Pillow)

Each feature is a module in tools/ with a generate() function and EN / RU dicts of translations; add it to FEATURES.
The lang files are written last from all of them.
"""
import importlib
import json
import os
import sys

MOD = "naturequirks"
TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(TOOLS, "..", "src", "main", "resources")
ASSETS = os.path.join(ROOT, "assets", MOD)
DATA = os.path.join(ROOT, "data", MOD)

# feature modules, in generation order (missing ones are skipped so features can land independently)
FEATURES = ["stone_head", "flower_creeper", "giant_hive"]

EN = {"itemGroup.naturequirks": "Nature's Quirks"}
RU = {"itemGroup.naturequirks": "Причуды природы"}


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")


def main():
    sys.path.insert(0, TOOLS)
    en, ru = dict(EN), dict(RU)
    for name in FEATURES:
        if not os.path.exists(os.path.join(TOOLS, name + ".py")):
            continue
        module = importlib.import_module(name)
        module.generate()
        en.update(getattr(module, "EN", {}))
        ru.update(getattr(module, "RU", {}))
    write_json(os.path.join(ASSETS, "lang", "en_us.json"), dict(sorted(en.items())))
    write_json(os.path.join(ASSETS, "lang", "ru_ru.json"), dict(sorted(ru.items())))


if __name__ == "__main__":
    main()
