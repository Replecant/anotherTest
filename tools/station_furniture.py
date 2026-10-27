"""Data for the space station equipment set: recipes, loot, tags, lang. Art lives in station_furniture_art.py."""
import os

from furniture import add_to_tag
from gen_resources import DATA, MOD, loot_self, shaped, write_json

POSTERS = ["poster_liftoff", "poster_vesper", "poster_space_pop", "poster_suit_check", "poster_homestead", "poster_freedom",
           "poster_rangers", "poster_venus_briefing"]
TALL = ["vending_machine", "crew_locker", "station_door", "airlock_door"] + POSTERS
NEW = ["crew_locker", "cargo_crate", "supply_cabinet", "retro_workbench", "galley_stove", "lab_sink", "tape_archive",
       "station_door", "airlock_door"] + POSTERS


def loot_lower_half(name):
    """Two-block-tall blocks drop once, from their lower half."""
    write_json(os.path.join(DATA, "loot_table", "blocks", name + ".json"), {
        "type": "minecraft:block",
        "pools": [{"rolls": 1, "bonus_rolls": 0,
                   "entries": [{"type": "minecraft:item", "name": f"{MOD}:{name}"}],
                   "conditions": [
                       {"condition": "minecraft:block_state_property", "block": f"{MOD}:{name}", "properties": {"half": "lower"}},
                       {"condition": "minecraft:survives_explosion"}]}],
        "random_sequence": f"{MOD}:blocks/{name}"})

BLOCKS = ["control_panel", "radar_scope", "computer_bank", "captain_chair", "crew_bunk", "hydroponic_planter",
          "oxygen_tank_rack", "vending_machine", "star_chart", "ceiling_light", "wall_sconce", "telescope",
          "space_globe", "reactor_core", "floor_grate", "hull_panel", "hull_panel_striped", "hull_window"]


def loot_foot(name):
    """Two-block-long pieces drop once, from their foot part."""
    write_json(os.path.join(DATA, "loot_table", "blocks", name + ".json"), {
        "type": "minecraft:block",
        "pools": [{"rolls": 1, "bonus_rolls": 0,
                   "entries": [{"type": "minecraft:item", "name": f"{MOD}:{name}"}],
                   "conditions": [
                       {"condition": "minecraft:block_state_property", "block": f"{MOD}:{name}", "properties": {"part": "foot"}},
                       {"condition": "minecraft:survives_explosion"}]}],
        "random_sequence": f"{MOD}:blocks/{name}"})


def generate():
    for b in BLOCKS + NEW:
        if b == "crew_bunk":
            loot_foot(b)
        elif b in TALL:
            loot_lower_half(b)
        else:
            loot_self(b)
    add_to_tag("block/mineable/pickaxe", [f"{MOD}:{b}" for b in BLOCKS + NEW if b not in ("crew_bunk",) and b not in POSTERS])
    add_to_tag("block/doors", [f"{MOD}:station_door", f"{MOD}:airlock_door"])
    add_to_tag("item/doors", [f"{MOD}:station_door", f"{MOD}:airlock_door"])
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
    recipes.update({
        "crew_locker": (["AA", "AA", "AA"], {"A": A}, 1),
        "cargo_crate": (["ARA", "A A", "AAA"], {"A": A, "R": "minecraft:red_dye"}, 1),
        "supply_cabinet": (["AAA", "C C", "AAA"], {"A": A, "C": "minecraft:cyan_dye"}, 1),
        "retro_workbench": (["TTT", "ACA", "A A"], {"T": T, "A": A, "C": "minecraft:crafting_table"}, 1),
        "galley_stove": (["AAA", "ASA", "AAA"], {"A": A, "S": "minecraft:smoker"}, 1),
        "lab_sink": (["A A", "AWA", " A "], {"A": A, "W": "minecraft:water_bucket"}, 1),
        "tape_archive": (["AAA", "VBV", "AAA"], {"A": A, "V": V, "B": "minecraft:bookshelf"}, 1),
        "station_door": (["AA", "AG", "AA"], {"A": A, "G": "minecraft:glass_pane"}, 3),
        "airlock_door": (["TT", "TG", "TT"], {"T": T, "G": "minecraft:glass_pane"}, 3),
    })
    dyes = {"poster_liftoff": "minecraft:red_dye", "poster_vesper": "minecraft:orange_dye", "poster_space_pop": "minecraft:pink_dye",
            "poster_suit_check": "minecraft:yellow_dye", "poster_homestead": "minecraft:blue_dye", "poster_freedom": "minecraft:cyan_dye",
            "poster_rangers": "minecraft:lime_dye", "poster_venus_briefing": "minecraft:brown_dye"}
    for poster, dye in dyes.items():
        recipes[poster] = (["P", "D", "P"], {"P": "minecraft:paper", "D": dye}, 1)
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
    "block.retrocosmos.star_chart": "Star Chart",
    "block.retrocosmos.ceiling_light": "Ceiling Light",
    "block.retrocosmos.wall_sconce": "Atomic Wall Sconce",
    "block.retrocosmos.telescope": "Telescope",
    "block.retrocosmos.space_globe": "Earth Globe",
    "block.retrocosmos.reactor_core": "Reactor Core",
    "block.retrocosmos.floor_grate": "Deck Grating",
    "block.retrocosmos.hull_panel": "Hull Plating",
    "block.retrocosmos.hull_panel_striped": "Striped Hull Plating",
    "block.retrocosmos.hull_window": "Panoramic Window",
    "block.retrocosmos.crew_locker": "Crew Locker",
    "block.retrocosmos.cargo_crate": "Cargo Container",
    "block.retrocosmos.supply_cabinet": "Supply Cabinet",
    "block.retrocosmos.retro_workbench": "Station Work Bench",
    "block.retrocosmos.galley_stove": "Galley Oven",
    "block.retrocosmos.lab_sink": "Station Sink",
    "block.retrocosmos.tape_archive": "Tape Archive",
    "block.retrocosmos.station_door": "Station Door",
    "block.retrocosmos.airlock_door": "Airlock Door",
    "block.retrocosmos.poster_liftoff": "Poster \"Liftoff!\"",
    "block.retrocosmos.poster_vesper": "Poster \"Visit Mars\"",
    "block.retrocosmos.poster_space_pop": "Poster \"Drink Space Pop\"",
    "block.retrocosmos.poster_suit_check": "Poster \"Check Your Suit\"",
    "block.retrocosmos.poster_homestead": "Poster \"Home Sweet Home\"",
    "block.retrocosmos.poster_freedom": "Poster \"Freedom Station\"",
    "block.retrocosmos.poster_rangers": "Poster \"The Galaxy Needs You!\"",
    "block.retrocosmos.poster_venus_briefing": "Briefing Board \"Venus\"",
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
    "block.retrocosmos.star_chart": "Звёздная карта",
    "block.retrocosmos.ceiling_light": "Потолочный светильник",
    "block.retrocosmos.wall_sconce": "Атомное бра",
    "block.retrocosmos.telescope": "Телескоп",
    "block.retrocosmos.space_globe": "Глобус Земли",
    "block.retrocosmos.reactor_core": "Активная зона реактора",
    "block.retrocosmos.floor_grate": "Решётчатый настил",
    "block.retrocosmos.hull_panel": "Обшивка корпуса",
    "block.retrocosmos.hull_panel_striped": "Обшивка с полосой",
    "block.retrocosmos.hull_window": "Панорамное окно",
    "block.retrocosmos.crew_locker": "Шкафчик экипажа",
    "block.retrocosmos.cargo_crate": "Грузовой контейнер",
    "block.retrocosmos.supply_cabinet": "Шкаф снабжения",
    "block.retrocosmos.retro_workbench": "Верстак станции",
    "block.retrocosmos.galley_stove": "Печь камбуза",
    "block.retrocosmos.lab_sink": "Раковина станции",
    "block.retrocosmos.tape_archive": "Ленточный архив",
    "block.retrocosmos.station_door": "Дверь станции",
    "block.retrocosmos.airlock_door": "Шлюзовая дверь",
    "block.retrocosmos.poster_liftoff": "Плакат «Старт!»",
    "block.retrocosmos.poster_vesper": "Плакат «Посетите Марс»",
    "block.retrocosmos.poster_space_pop": "Плакат «Пейте Space Pop»",
    "block.retrocosmos.poster_suit_check": "Плакат «Проверь скафандр»",
    "block.retrocosmos.poster_homestead": "Плакат «Дом, милый дом»",
    "block.retrocosmos.poster_freedom": "Плакат «Станция „Свобода“»",
    "block.retrocosmos.poster_rangers": "Плакат «Ты нужен Галактике!»",
    "block.retrocosmos.poster_venus_briefing": "Доска брифинга «Венера»",
}
