"""Space Rangers storyline items: the ranger blaster and its energy cartridges, Professor Oinstein's ID card, his
research notes (the serum catalyst), the five serums and the Ranger Star. Icons, the blue bolt texture, item models,
recipes and lang; called from tools/tribes.py (generate)."""
import math
import os

from PIL import Image

import dinosaurs as D
import tribe_mutants as MU
from gen_resources import ASSETS, MOD, item_def, save, shaped, shapeless, write_json

sprite = MU.sprite

# id, EN, RU, effect colour, description EN, RU (the effects themselves live in Java: tribe/ranger/Serum.java)
SERUMS = [
    ("vigor", "Vigor Serum", "Сыворотка силы", (140, 255, 90),
     "Muscle in a syringe. You will be hungry afterwards.", "Мышцы в шприце. Потом захочется есть."),
    ("swiftness", "Swiftness Serum", "Сыворотка быстроты", (90, 230, 255),
     "Legs like a raptor's - for a while.", "Ноги как у раптора - на время."),
    ("cerebral", "Cerebral Serum", "Церебральная сыворотка", (255, 140, 200),
     "Brighter eyes, quicker hands, a spinning head.", "Зоркие глаза, быстрые руки, кружится голова."),
    ("regeneration", "Regeneration Serum", "Регенерирующая сыворотка", (255, 90, 110),
     "Knits flesh in seconds. Leaves you ravenous.", "Сращивает плоть за секунды. Оставляет зверский голод."),
    ("hide", "Hide Serum", "Сыворотка шкуры", (210, 160, 90),
     "Skin like a dinosaur's. Arms like jelly after.", "Кожа как у динозавра. Потом руки как кисель."),
]


def ranger_blaster():
    rows = ["................",
            "................",
            "........BB......",
            ".......BBBB.....",
            "..kcccccccccclw.",
            ".kclllllllllclwW",
            ".kcddddddddddlw.",
            "..kkccBBBccckk..",
            "....kbbbk.BB....",
            "....kbybk.......",
            "...kbyyyk.......",
            "...kbbybk.......",
            "...kbbbk........",
            "...kkkk.........",
            "................",
            "................"]
    return sprite(rows, {"k": (36, 40, 56), "c": (176, 186, 200), "l": (240, 246, 252), "d": (112, 120, 136),
                         "B": (40, 110, 230), "w": (110, 190, 255), "W": (220, 240, 255),
                         "b": (30, 60, 140), "y": (250, 214, 70)})


def energy_cartridge():
    rows = ["................",
            "................",
            "......kkkk......",
            ".....kllllk.....",
            ".....kccccck....",
            ".....kcwWwck....",
            ".....kcwWwck....",
            ".....kcwWwck....",
            ".....kcwWwck....",
            ".....kccccck....",
            ".....koooook....",
            ".....kddddck....",
            ".....kccccck....",
            "......kkkkk.....",
            "................",
            "................"]
    return sprite(rows, {"k": (60, 34, 24), "c": (196, 112, 68), "l": (238, 168, 120), "d": (140, 76, 44),
                         "o": (70, 70, 80), "w": (60, 150, 255), "W": (200, 240, 255)})


def professor_id():
    rows = ["................",
            "................",
            ".kkkkkkkkkkkkkk.",
            ".kwwwwwwwwwwwwk.",
            ".kwhhhwwgggggwk.",
            ".kwhsswwwwwwwwk.",
            ".kwsLswwgggggwk.",
            ".kwsssww......k.",
            ".kwccccwgggwwwk.",
            ".kwwwwwwwwwwwwk.",
            ".kRRRRRRRRRRRRk.",
            ".kRrrrrRRrrrrRk.",
            ".kkkkkkkkkkkkkk.",
            "................",
            "................",
            "................"]
    img = sprite(rows, {"k": (70, 74, 84), "w": (236, 236, 226), "h": (246, 246, 246), "s": (226, 194, 172),
                        "L": (110, 200, 150), "c": (230, 230, 230), "g": (150, 150, 160), "R": (200, 36, 40),
                        "r": (255, 220, 210)})
    # the atom-and-ape-skull insignia, a 5x3 sketch in the corner
    for (x, y) in ((9, 6), (10, 6), (11, 6), (12, 6), (13, 6)):
        img.putpixel((x, y), (236, 236, 226, 255))
    for (x, y), c in (((10, 7), (214, 52, 48)), ((11, 7), (238, 234, 222)), ((12, 7), (214, 52, 48)),
                      ((11, 6), (90, 240, 220))):
        img.putpixel((x, y), c + (255,))
    # the laminate's glare
    for (x, y) in ((3, 3), (4, 3), (12, 9)):
        img.putpixel((x, y), (255, 255, 255, 255))
    return img


def oinstein_notes():
    rows = ["................",
            "...kkkkkkkkkk...",
            "..kbbbbbbbbbbk..",
            "..kbBBBBBBBBbpk.",
            "..kbBrrrrrBBbpk.",
            "..kbBrwcwrBBbpk.",
            "..kbBrrrrrBBbpk.",
            "..kbBBBBBBBBbpk.",
            "..kbBBBBgBBBbpk.",
            "..kbBBBggGBBbpk.",
            "..kbBBBBgBBBbpk.",
            "..kbBBBBBBBBbpk.",
            "..kbbbbbbbbbbpk.",
            "...kkkkkkkkkpk..",
            "....kkkkkkkkk...",
            "................"]
    img = sprite(rows, {"k": (40, 26, 18), "b": (96, 58, 34), "B": (128, 80, 48), "p": (230, 222, 196),
                        "r": (200, 44, 44), "w": (238, 234, 222), "c": (90, 240, 220), "g": (80, 200, 80),
                        "G": (150, 255, 120)})
    # dog-eared corner, scuffs
    img.putpixel((3, 2), (0, 0, 0, 0))
    for (x, y) in ((6, 10), (10, 4), (5, 11)):
        img.putpixel((x, y), (150, 100, 64, 255))
    return img


def ranger_star():
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    cx, cy = 7.5, 8.0
    for y in range(16):
        for x in range(16):
            dx, dy = x - cx, y - cy
            r = math.hypot(dx, dy)
            a = math.atan2(dy, dx) + math.pi / 2
            # five-pointed star: radius swings between 3.2 and 7.4
            k = (math.cos(5 * a) + 1) / 2
            edge = 3.2 + 4.2 * k ** 1.6
            if r <= edge:
                c = (250, 206, 60) if r < edge - 1.0 else (176, 120, 30)
                if dx + dy < -2 and r < edge - 1.0:
                    c = (255, 240, 150)
                if r < 2.6:
                    c = (40, 100, 220) if r < 1.8 else (230, 236, 250)
                img.putpixel((x, y), c + (255,))
    img.putpixel((7, 8), (220, 240, 255, 255))
    return img


def serum_icon(colour):
    """A chrome syringe, bottom-left to top-right, full of glowing serum of the given colour."""
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    hi = tuple(min(255, int(v * 0.5 + 128)) for v in colour)
    lo = tuple(int(v * 0.6) for v in colour)

    def put(x, y, c):
        if 0 <= x < 16 and 0 <= y < 16:
            img.putpixel((x, y), tuple(int(v) for v in c) + (255,))

    # barrel: a 3-px wide diagonal from (3,12) to (10,5)
    for t in range(8):
        x, y = 3 + t, 12 - t
        put(x - 1, y - 1, (190, 214, 222))  # glass edge
        put(x, y, colour if t > 0 else lo)
        put(x + 1, y + 1, (150, 170, 180))
        put(x, y - 1, hi if t % 3 else colour)
        put(x + 1, y, lo)
    # plunger and thumb rest (bottom left)
    for t in range(3):
        put(1 + t, 14 - t, (160, 166, 176))
    put(0, 13, (60, 64, 74)); put(1, 12, (60, 64, 74)); put(2, 15, (60, 64, 74)); put(3, 14, (60, 64, 74))
    # finger flange
    put(2, 10, (120, 126, 136)); put(5, 13, (120, 126, 136)); put(3, 11, (190, 196, 206)); put(4, 12, (190, 196, 206))
    # needle hub and needle (top right)
    put(11, 4, (120, 126, 136)); put(12, 4, (170, 176, 186)); put(11, 3, (170, 176, 186))
    for t in range(3):
        put(13 + t, 2 - t, (226, 230, 236))
    put(12, 3, (226, 230, 236))
    return img


def bolt_texture_blue():
    """The ranger bolt: the blaster bolt's white-hot core fading through electric blue."""
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for y in range(16):
        for x in range(16):
            dy = abs(y - 7.5) / 7.5
            dx = abs(x - 7.5) / 7.5
            r = math.hypot(dy, dx ** 2.2)
            if r > 1:
                continue
            core = max(0.0, 1 - r * 2.2)
            a = int(255 * (1 - r) ** 0.7)
            c = D.lerp((60, 140, 255), (255, 255, 255), core)
            img.putpixel((x, y), tuple(int(v) for v in c) + (a,))
    return img


ICONS = {"ranger_blaster": ranger_blaster, "energy_cartridge": energy_cartridge, "professor_id": professor_id,
         "oinstein_notes": oinstein_notes, "ranger_star": ranger_star}


def generate():
    save(bolt_texture_blue(), "entity", "tribe", "ranger_bolt")
    for name, fn in ICONS.items():
        save(fn(), "item", name)
        parent = f"{MOD}:item/blaster_template" if name == "ranger_blaster" else "minecraft:item/generated"
        write_json(os.path.join(ASSETS, "models", "item", name + ".json"),
                   {"parent": parent, "textures": {"layer0": f"{MOD}:item/{name}"}})
        item_def(name, f"{MOD}:item/{name}")
    for sid, _en, _ru, colour, _de, _dr in SERUMS:
        name = "serum_" + sid
        save(serum_icon(colour), "item", name)
        write_json(os.path.join(ASSETS, "models", "item", name + ".json"),
                   {"parent": "minecraft:item/generated", "textures": {"layer0": f"{MOD}:item/{name}"}})
        item_def(name, f"{MOD}:item/{name}")
    recipes()


def recipes():
    shaped("energy_cartridge", ["CGC", "RAR", "CGC"],
           {"C": "minecraft:copper_ingot", "G": "minecraft:glass_pane", "R": "minecraft:redstone", "A": f"{MOD}:aluminum_ingot"},
           "energy_cartridge", 8, category="equipment")
    notes, bottle = "oinstein_notes", "minecraft:glass_bottle"
    glowcap, amber = f"{MOD}:venus_glowcap", "venus_amber"
    shapeless("serum_vigor", [notes, bottle, "dino_hide", "raptor_tooth", amber], "serum_vigor")
    shapeless("serum_swiftness", [notes, bottle, "fern_fiber", "fern_fiber", "raptor_tooth", "minecraft:sugar"], "serum_swiftness")
    shapeless("serum_cerebral", [notes, bottle, "brain_flask", glowcap], "serum_cerebral")
    shapeless("serum_regeneration", [notes, bottle, glowcap, glowcap, amber], "serum_regeneration")
    shapeless("serum_hide", [notes, bottle, "dino_hide", "dino_hide", f"{MOD}:cryolite_crystal"], "serum_hide")


EN, RU = {}, {}
for _k, (_en, _ru) in {
    "ranger_blaster": ("Ranger Blaster", "Бластер рейнджера"),
    "ranger_blaster.desc": ("Uses one Energy Cartridge per shot", "Расходует один энергокартридж на выстрел"),
    "ranger_blaster.empty": ("Click! No energy cartridges.", "Щёлк! Нет энергокартриджей."),
    "ranger_blaster.overheat": ("OVERHEATED! Cooling down...", "ПЕРЕГРЕВ! Охлаждение..."),
    "ranger_blaster.heat_desc": ("Overheats after %s rapid shots", "Перегревается после %s выстрелов подряд"),
    "energy_cartridge": ("Energy Cartridge", "Энергокартридж"),
    "professor_id": ("Professor Oinstein's ID Card", "Удостоверение профессора Ойнштайна"),
    "professor_id.lore.0": ("Oinstein Institute of Applied Evolution", "Институт прикладной эволюции Ойнштайна"),
    "professor_id.lore.1": ("DIRECTOR - access to all levels", "ДИРЕКТОР - допуск ко всем уровням"),
    "oinstein_notes": ("Oinstein's Research Notes", "Заметки Ойнштайна"),
    "oinstein_notes.desc": ("Allows synthesizing serums", "Позволяет синтезировать сыворотки"),
    "oinstein_notes.lore": ("Not used up in crafting", "Не расходуется при крафте"),
    "ranger_star": ("Ranger Star", "Звезда рейнджера"),
    "ranger_star.lore.0": ("Awarded by the Space Rangers", "Вручена Космическими рейнджерами"),
    "ranger_star.lore.1": ("for courage beyond the call of duty", "за отвагу сверх долга службы"),
    "serum.effect": ("%s (%s)", "%s (%s)"),
    "serum.after": ("Afterwards: %s", "Потом: %s"),
    "serum.wears_off": ("The serum wears off...", "Действие сыворотки проходит..."),
}.items():
    EN[f"item.{MOD}.{_k}"], RU[f"item.{MOD}.{_k}"] = _en, _ru
for _sid, _en, _ru, _c, _de, _dr in SERUMS:
    EN[f"item.{MOD}.serum_{_sid}"], RU[f"item.{MOD}.serum_{_sid}"] = _en, _ru
    EN[f"item.{MOD}.serum_{_sid}.desc"], RU[f"item.{MOD}.serum_{_sid}.desc"] = _de, _dr
EN[f"entity.{MOD}.ranger_bolt"], RU[f"entity.{MOD}.ranger_bolt"] = "Ranger Bolt", "Заряд рейнджера"
