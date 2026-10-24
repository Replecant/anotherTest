"""Data for the "Atomic Home" furniture & decor pack: recipes, loot, tags, lang.

Art (models, textures, blockstates, item definitions) lives in furniture_art.py.
"""
import json
import os

from gen_resources import MOD, ROOT, loot_self, shaped, write_json


def add_to_tag(path, values, namespace="minecraft"):
    """Appends values to a tag file that the main generator may already have written."""
    file = os.path.join(ROOT, "data", namespace, "tags", *path.split("/")) + ".json"
    existing = []
    if os.path.exists(file):
        with open(file, encoding="utf-8") as f:
            existing = json.load(f).get("values", [])
    write_json(file, {"replace": False, "values": existing + [v for v in values if v not in existing]})

BLOCKS = ["atomic_floor_lamp", "rocket_table_lamp", "sputnik_chandelier", "diner_stool", "egg_chair", "googie_sofa",
          "boomerang_table", "atomic_tv", "tube_radio", "starburst_clock", "neon_rocket_sign", "porthole_window",
          "checkered_tile", "turquoise_panel", "cream_panel", "chrome_trim"]

PICKAXE = ["atomic_floor_lamp", "rocket_table_lamp", "sputnik_chandelier", "diner_stool", "boomerang_table",
           "starburst_clock", "neon_rocket_sign", "porthole_window", "checkered_tile", "turquoise_panel", "cream_panel",
           "chrome_trim"]
AXE = ["atomic_tv", "tube_radio"]


def generate():
    for b in BLOCKS:
        loot_self(b)
    add_to_tag("block/mineable/pickaxe", [f"{MOD}:{b}" for b in PICKAXE])
    add_to_tag("block/mineable/axe", [f"{MOD}:{b}" for b in AXE])

    A = "aluminum_plate"
    shaped("atomic_floor_lamp", ["GAG", " A ", " I "],
           {"G": "minecraft:glowstone", "A": A, "I": "aluminum_ingot"}, "atomic_floor_lamp", category="building")
    shaped("rocket_table_lamp", [" R ", "RGR", " A "],
           {"R": "minecraft:red_dye", "G": "minecraft:glowstone", "A": A}, "rocket_table_lamp", category="building")
    shaped("sputnik_chandelier", [" N ", "AGA", "A A"],
           {"N": "minecraft:iron_nugget", "G": "minecraft:glowstone", "A": A}, "sputnik_chandelier", category="building")
    shaped("diner_stool", ["RRR", " A ", " A "],
           {"R": "minecraft:red_wool", "A": A}, "diner_stool", count=2, category="building")
    shaped("egg_chair", ["WWW", "WCW", " A "],
           {"W": "minecraft:white_wool", "C": "minecraft:cyan_wool", "A": A}, "egg_chair", category="building")
    shaped("googie_sofa", ["C  ", "CCC", "A A"],
           {"C": "minecraft:cyan_wool", "A": A}, "googie_sofa", count=2, category="building")
    shaped("boomerang_table", ["SSS", " A ", "A A"],
           {"S": "minecraft:birch_slab", "A": A}, "boomerang_table", category="building")
    shaped("atomic_tv", ["AVA", "PGP", "P P"],
           {"A": A, "V": "vacuum_tube", "P": "#minecraft:planks", "G": "minecraft:glass_pane"}, "atomic_tv",
           category="building")
    shaped("tube_radio", ["PPP", "VNV", "PPP"],
           {"P": "#minecraft:planks", "V": "vacuum_tube", "N": "minecraft:note_block"}, "tube_radio", category="building")
    shaped("starburst_clock", [" G ", "GCG", " G "],
           {"G": "minecraft:gold_nugget", "C": "minecraft:clock"}, "starburst_clock", category="building")
    shaped("neon_rocket_sign", ["GLG", "GRG", "GLG"],
           {"G": "minecraft:glass_pane", "L": "minecraft:glowstone_dust", "R": "minecraft:redstone"}, "neon_rocket_sign",
           category="building")
    shaped("porthole_window", [" A ", "AGA", " A "],
           {"A": A, "G": "minecraft:glass"}, "porthole_window", count=2, category="building")
    shaped("checkered_tile", ["WB", "BW"],
           {"W": "minecraft:white_concrete", "B": "minecraft:black_concrete"}, "checkered_tile", count=4, category="building")
    shaped("turquoise_panel", ["CC", "CC"], {"C": "minecraft:cyan_concrete"}, "turquoise_panel", count=4,
           category="building")
    shaped("cream_panel", ["SS", "SS"], {"S": "minecraft:smooth_sandstone"}, "cream_panel", count=4, category="building")
    shaped("chrome_trim", ["A", "A", "A"], {"A": A}, "chrome_trim", count=3, category="building")


EN = {
    "itemGroup.retrocosmos.home": "Retro Cosmos: Atomic Home",
    "block.retrocosmos.atomic_floor_lamp": "Atomic Floor Lamp",
    "block.retrocosmos.rocket_table_lamp": "Rocket Table Lamp",
    "block.retrocosmos.sputnik_chandelier": "Satellite Chandelier",
    "block.retrocosmos.diner_stool": "Diner Stool",
    "block.retrocosmos.egg_chair": "Egg Chair",
    "block.retrocosmos.googie_sofa": "Googie Sofa",
    "block.retrocosmos.boomerang_table": "Boomerang Coffee Table",
    "block.retrocosmos.atomic_tv": "Atomic Age Television",
    "block.retrocosmos.tube_radio": "Tube Radio",
    "block.retrocosmos.starburst_clock": "Starburst Wall Clock",
    "block.retrocosmos.neon_rocket_sign": "Neon Rocket Sign",
    "block.retrocosmos.porthole_window": "Porthole Window",
    "block.retrocosmos.checkered_tile": "Checkered Diner Tile",
    "block.retrocosmos.turquoise_panel": "Turquoise Panel",
    "block.retrocosmos.cream_panel": "Cream Panel",
    "block.retrocosmos.chrome_trim": "Chrome Trim",
}

RU = {
    "itemGroup.retrocosmos.home": "Ретрокосмос: Атомный дом",
    "block.retrocosmos.atomic_floor_lamp": "Атомный торшер",
    "block.retrocosmos.rocket_table_lamp": "Настольная лампа «Ракета»",
    "block.retrocosmos.sputnik_chandelier": "Люстра «Спутник связи»",
    "block.retrocosmos.diner_stool": "Табурет закусочной",
    "block.retrocosmos.egg_chair": "Кресло-яйцо",
    "block.retrocosmos.googie_sofa": "Диван в стиле гуги",
    "block.retrocosmos.boomerang_table": "Журнальный столик «Бумеранг»",
    "block.retrocosmos.atomic_tv": "Телевизор атомной эры",
    "block.retrocosmos.tube_radio": "Ламповый радиоприёмник",
    "block.retrocosmos.starburst_clock": "Настенные часы «Звёздный взрыв»",
    "block.retrocosmos.neon_rocket_sign": "Неоновая вывеска «Ракета»",
    "block.retrocosmos.porthole_window": "Окно-иллюминатор",
    "block.retrocosmos.checkered_tile": "Шахматная плитка закусочной",
    "block.retrocosmos.turquoise_panel": "Бирюзовая панель",
    "block.retrocosmos.cream_panel": "Кремовая панель",
    "block.retrocosmos.chrome_trim": "Хромированный молдинг",
}
