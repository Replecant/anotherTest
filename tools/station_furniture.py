"""Data for the space station equipment set: recipes, loot, tags, lang. Art lives in station_furniture_art.py."""
from furniture import add_to_tag
from gen_resources import MOD, loot_self, shaped

BLOCKS = ["control_panel", "radar_scope", "computer_bank", "captain_chair", "crew_bunk", "hydroponic_planter",
          "oxygen_tank_rack", "vending_machine", "star_chart", "ceiling_light", "wall_sconce", "telescope",
          "space_globe", "reactor_core", "floor_grate", "hull_panel", "hull_panel_striped", "hull_window"]


def generate():
    for b in BLOCKS:
        loot_self(b)
    add_to_tag("block/mineable/pickaxe", [f"{MOD}:{b}" for b in BLOCKS if b not in ("crew_bunk",)])
    A, T, V = "aluminum_plate", "titanium_plate", "vacuum_tube"
    G = "minecraft:glass_pane"
    R = "minecraft:redstone"
    recipes = {
        "control_panel": (["VRV", "TGT"], {"V": V, "R": R, "T": T, "G": G}, 1),
        "radar_scope": ([" G ", "VRV", "TTT"], {"G": G, "V": V, "R": "minecraft:compass", "T": T}, 1),
        "computer_bank": (["TVT", "RGR", "TVT"], {"T": T, "V": V, "R": R, "G": "guidance_computer"}, 1),
        "captain_chair": (["W  ", "WWW", " A "], {"W": "minecraft:red_wool", "A": A}, 1),
        "crew_bunk": (["AAA", "CCC", "AAA"], {"A": A, "C": "minecraft:cyan_wool"}, 1),
        "hydroponic_planter": (["LLL", "SDS", "AAA"], {"L": "minecraft:glowstone_dust", "S": "#minecraft:saplings",
                                                       "D": "minecraft:dirt", "A": A}, 2),
        "oxygen_tank_rack": (["OOO", "A A"], {"O": "liquid_oxygen_canister", "A": A}, 1),
        "vending_machine": (["RGR", "RVR", "RIR"], {"R": "minecraft:red_concrete", "G": G, "V": V, "I": "minecraft:iron_block"}, 1),
        "star_chart": (["PPP", "PLP", "PPP"], {"P": "minecraft:paper", "L": "minecraft:glowstone_dust"}, 1),
        "ceiling_light": (["AAA", " G "], {"A": A, "G": "minecraft:glowstone"}, 4),
        "wall_sconce": ([" N ", "NGN", " A "], {"N": "minecraft:gold_nugget", "G": "minecraft:glowstone", "A": A}, 2),
        "telescope": ([" G ", " C ", "A A"], {"G": "minecraft:glass", "C": "minecraft:copper_ingot", "A": A}, 1),
        "space_globe": ([" B ", " A ", "AAA"], {"B": "minecraft:lapis_block", "A": A}, 1),
        "reactor_core": (["TGT", "GDG", "TGT"], {"T": T, "G": "minecraft:glass", "D": "minecraft:diamond"}, 1),
        "floor_grate": (["B B", " B ", "B B"], {"B": "minecraft:iron_bars"}, 4),
        "hull_panel": (["AA", "AA"], {"A": A}, 4),
        "hull_panel_striped": (["H", "R"], {"H": "hull_panel", "R": "minecraft:red_dye"}, 1),
        "hull_window": (["AGA", "GGG", "AGA"], {"A": A, "G": "minecraft:glass"}, 4),
    }
    for name, (pattern, key, count) in recipes.items():
        shaped(name, pattern, key, name, count=count, category="building")


EN = {
    "itemGroup.retrocosmos.station": "Retro Cosmos: Space Station",
    "block.retrocosmos.control_panel": "Instrument Panel",
    "block.retrocosmos.radar_scope": "Radar Scope",
    "block.retrocosmos.computer_bank": "Tape Computer Bank",
    "block.retrocosmos.captain_chair": "Commander's Chair",
    "block.retrocosmos.crew_bunk": "Crew Bunk",
    "block.retrocosmos.hydroponic_planter": "Hydroponic Planter",
    "block.retrocosmos.oxygen_tank_rack": "Oxygen Tank Rack",
    "block.retrocosmos.vending_machine": "Space Pop Vending Machine",
    "block.retrocosmos.star_chart": "Vesper Star Chart",
    "block.retrocosmos.ceiling_light": "Ceiling Light",
    "block.retrocosmos.wall_sconce": "Atomic Wall Sconce",
    "block.retrocosmos.telescope": "Telescope",
    "block.retrocosmos.space_globe": "Homestead Globe",
    "block.retrocosmos.reactor_core": "Reactor Core",
    "block.retrocosmos.floor_grate": "Deck Grating",
    "block.retrocosmos.hull_panel": "Hull Plating",
    "block.retrocosmos.hull_panel_striped": "Striped Hull Plating",
    "block.retrocosmos.hull_window": "Panoramic Window",
}
RU = {
    "itemGroup.retrocosmos.station": "Ретрокосмос: Космическая станция",
    "block.retrocosmos.control_panel": "Приборная панель",
    "block.retrocosmos.radar_scope": "Радарный индикатор",
    "block.retrocosmos.computer_bank": "Ленточная ЭВМ",
    "block.retrocosmos.captain_chair": "Кресло командира",
    "block.retrocosmos.crew_bunk": "Койка экипажа",
    "block.retrocosmos.hydroponic_planter": "Гидропонная грядка",
    "block.retrocosmos.oxygen_tank_rack": "Стойка кислородных баллонов",
    "block.retrocosmos.vending_machine": "Автомат «Space Pop»",
    "block.retrocosmos.star_chart": "Звёздная карта Веспер",
    "block.retrocosmos.ceiling_light": "Потолочный светильник",
    "block.retrocosmos.wall_sconce": "Атомное бра",
    "block.retrocosmos.telescope": "Телескоп",
    "block.retrocosmos.space_globe": "Глобус Хоумстеда",
    "block.retrocosmos.reactor_core": "Активная зона реактора",
    "block.retrocosmos.floor_grate": "Решётчатый настил",
    "block.retrocosmos.hull_panel": "Обшивка корпуса",
    "block.retrocosmos.hull_panel_striped": "Обшивка с полосой",
    "block.retrocosmos.hull_window": "Панорамное окно",
}
