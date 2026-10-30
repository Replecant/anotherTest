"""Stone Head: a moai-like carved head of mossy, weathered stone standing on beaches. Feed it any item and it chews it
into a Geode.

generate() writes: the entity texture and model geometry, the geode item (and its "rich" variant model), spawn egg,
loot tables (the head's drops and gameplay/geode), the delicacies item tag, the beach biome tag and spawn modifier.
"""
import math

from PIL import Image

import quirk_models as Q
from quirk_models import B, P

NAME = "stone_head"
ID = f"{Q.MOD}:{NAME}"

# ----------------------------------------------------------------------------
# Geometry (model space: y down, ground at 24, face toward -z). 22 px wide with the ears, 35 px tall.
# ----------------------------------------------------------------------------


def spec():
    parts = [
        # the buried chest and shoulders it stands on
        P("base", None, (0, 24, 0), (0, 0, 0), [
            B(-11, -9, -6, 22, 9, 12, "torso"),
        ]),
        # the head turns a little on its neck (pivot at the top of the chest)
        P("head", "base", (0, -9, 1), (0, 0, 0), [
            B(-9, -26, -6.5, 18, 20, 13, "cranium"),
            B(-9.5, -19, -9.5, 19, 3, 4, "brow"),
            B(-2.5, -16, -10.5, 5, 8, 4, "nose"),
            B(-3.5, -9, -10.5, 7, 2, 4, "nostrils"),
            B(-5, -7, -8.5, 10, 1, 2, "lip"),
            B(-11, -20, -3.5, 2, 13, 4, "ear", side="r"),
            B(9, -20, -3.5, 2, 13, 4, "ear", side="l"),
        ]),
        # coral-white eyes with obsidian pupils that follow you
        P("pupil_r", "head", (-4.5, -13.5, -6.5), (0, 0, 0), [B(-1, -1, -0.6, 2, 2, 1, "pupil")]),
        P("pupil_l", "head", (4.5, -13.5, -6.5), (0, 0, 0), [B(-1, -1, -0.6, 2, 2, 1, "pupil")]),
        # the great chin, hinged under the cheeks: it chews
        P("jaw", "head", (0, -6, -1.5), (0, 0, 0), [
            B(-8, 0, -7.5, 16, 6, 12, "jaw"),
        ]),
    ]
    return {"name": NAME, "tex_w": 128, "parts": parts}


POSES = {
    "chewing": {"jaw": (0.32, 0, 0), "head": (-0.05, 0, 0)},
    "looking": {"head": (0, 0.35, 0), "pupil_r": (0, 0, 0, 1.0, 0.3, 0), "pupil_l": (0, 0, 0, 1.0, 0.3, 0)},
}

# ----------------------------------------------------------------------------
# Texture
# ----------------------------------------------------------------------------

STONE = [(78, 78, 76), (96, 95, 92), (112, 111, 107), (126, 125, 121), (141, 140, 135)]
MOSS = [(62, 82, 34), (80, 104, 40), (100, 128, 46), (122, 150, 56)]
LICHEN = (150, 158, 120)
SHADOW = (52, 51, 50)
CORAL = (226, 220, 202)
CORAL_DARK = (196, 188, 168)
OBSIDIAN = (28, 24, 38)
OBSIDIAN_HI = (92, 76, 128)
MOUTH = (40, 38, 37)


FACE_PARTS = ("cranium", "brow", "nose", "nostrils", "lip", "jaw")


def stone_base(t, seed=3):
    n = Q.value_noise(t.mx, t.my, t.mz, 3.5, seed)
    g = Q.hash3(t.u, t.v, seed)
    # the carved face is smoother than the rough sides, so its features read
    calm = t.face == "north" and t.mat in FACE_PARTS
    k = n * 0.7 + g * 0.3 if calm else n * 0.55 + g * 0.45
    if t.face == "top":
        k += 0.08
    elif t.face == "bottom":
        k -= 0.25
    c = STONE[max(0, min(4, int(k * 5.0)))]
    # weathering cracks: thin dark lines where a second noise crosses its middle
    cr = Q.value_noise(t.mx * 1.0, t.my * 0.6, t.mz * 1.0, 5.0, seed + 9)
    if abs(cr - 0.5) < 0.022 and t.face != "bottom":
        c = Q.shade(c, 0.66)
    return c, g


def moss_amount(t):
    """How mossy this spot is: tops and ledges, the shady lower parts, and patches dripping down the sides."""
    n = Q.value_noise(t.mx, t.my * 0.7, t.mz, 4.0, 21)
    m = n - 0.78
    if t.face == "top":
        m += 0.5
    elif t.face == "bottom":
        m -= 0.6
    else:
        # moss creeps a little way down from the ledges above (top, brow, ears) and up from the sand
        if t.mat in ("cranium", "brow", "ear", "torso"):
            m += max(0.0, 0.2 - (t.ly - t.y0) * 0.1)
        m += max(0.0, (t.my - 19) * 0.05)
    if t.mat in ("pupil", "nostrils", "lip") or t.mat == "nose" and t.face != "top":
        m -= 0.3
    return m


def eye_white(t):
    """The coral eye on the face plane under the brow (cranium north face)."""
    if t.mat != "cranium" or t.face != "north":
        return None
    for cx in (-4.5, 4.5):
        if abs(t.lx - cx) < 3.0 and -14.5 <= t.ly < -12.5:
            return CORAL_DARK if abs(t.lx - cx) > 2.0 else CORAL
        # the deep socket around it, in shadow under the brow
        if abs(t.lx - cx) < 4.0 and -15.0 <= t.ly < -12.0:
            return SHADOW
    return None


def paint(spec, t):
    c, g = stone_base(t)
    m = moss_amount(t)
    if t.mat == "pupil":
        if t.face == "north":
            return (OBSIDIAN_HI if (t.i, t.j) == (0, 0) else OBSIDIAN) + (255,)
        return OBSIDIAN + (255,)
    e = eye_white(t)
    if e:
        return e + (255,)
    # features
    if t.mat == "brow" and t.face == "bottom":
        c = Q.shade(c, 0.62)
    if t.mat == "nostrils" and t.face == "north" and t.j == t.rows - 1 and t.i in (1, t.cols - 2):
        return SHADOW + (255,)
    if t.mat == "nostrils" and t.face == "bottom" and t.i in (1, 2, t.cols - 2, t.cols - 3) and t.j > 1:
        return SHADOW + (255,)
    if t.mat in ("nose", "nostrils"):
        if t.face in ("east", "west"):
            c = Q.shade(c, 0.78)
        elif t.face == "north" and t.mat == "nose":
            # a long lit ridge with darker flanks
            c = Q.shade(Q.mix(c, STONE[3], 0.55), 1.08 if t.i == 2 else 1.0) if 1 <= t.i <= 3 else Q.mix(c, STONE[1], 0.6)
        elif t.face == "north" and t.mat == "nostrils":
            c = Q.mix(c, STONE[3], 0.55) if 1 <= t.i <= t.cols - 2 else Q.mix(c, STONE[1], 0.6)
        elif t.face == "top":
            c = Q.shade(c, 1.12)
    if t.mat == "cranium" and t.face == "north":
        if -16.0 <= t.ly < -15.0:
            c = Q.shade(c, 0.58)  # the deep shadow under the overhanging brow
        elif 2.5 <= abs(t.lx) < 3.5 and -15 <= t.ly <= -7:
            c = Q.shade(c, 0.62)  # the nose's shadow on the cheeks
        elif 3.5 <= abs(t.lx) <= 5.0 and -11 <= t.ly <= -7:
            c = Q.shade(c, 0.86)  # hollow cheeks
        if t.ly < -21 and abs(t.lx) < 7:
            c = Q.shade(c, 1.05)
    if t.mat == "brow" and t.face == "north" and t.j == 0:
        c = Q.shade(c, 1.1)
    if t.mat == "lip" and t.face == "bottom":
        c = MOUTH
    if t.mat == "lip" and t.face == "north":
        c = Q.shade(c, 0.72 if abs(t.lx) < 3.5 else 0.9)  # shade under the nostrils
    if t.mat == "nose" and t.face == "north" and t.i == 0:
        c = Q.shade(c, 0.86)
    if t.mat == "jaw":
        if t.face == "top":
            # the inside of the mouth, seen when it chews: dark, with a row of worn stone teeth at the front
            if t.j >= t.rows - 1:
                return Q.shade(STONE[4], 1.05) + (255,)
            return Q.shade(MOUTH, 0.9 + g * 0.2) + (255,)
        if t.face == "north" and t.j == 0:
            c = Q.shade(c, 0.6)  # the lip line
        if t.face in ("east", "west") and t.j == 0 and t.i < 6:
            c = Q.shade(c, 0.7)
    if t.mat == "cranium" and t.face == "bottom":
        z = t.lz
        return (Q.shade(MOUTH, 0.95) if z < 3 else c) + (255,)
    if t.mat == "ear" and t.face in ("east", "west"):
        outward = (t.face == "west") == (t.feat.get("side") == "r")
        if outward and 1 <= t.i <= t.cols - 2 and 2 <= t.j <= t.rows - 3 and (t.i == 1 or t.j in (2, t.rows - 3)):
            c = Q.shade(c, 0.7)  # the carved inner rim
    if t.mat == "torso":
        # arms carved in low relief down the flanks, long fingers meeting over the belly
        if t.face in ("east", "west") and abs(t.lz - (-3.0 + (t.ly + 9) * 0.55)) < 0.6 and t.ly > -8:
            c = Q.shade(c, 0.72)
        if t.face == "north" and t.ly > -4 and t.ly < -0.5:
            for hx in (-5.5, -3.5, 3.5, 5.5):
                if abs(t.lx - hx) < 0.5:
                    c = Q.shade(c, 0.74)
            if abs(t.lx) > 6.5:
                c = Q.shade(c, 0.85)
        if t.face == "top" and t.lz < -1 and abs(t.lx) < 7.5:
            m -= 0.3  # under the chin: less moss
    if m > 0.0:
        level = min(3, int(m * 6))
        dither = Q.hash3(t.u, t.v, 77)
        if m > 0.08 or dither > 0.5:
            c = MOSS[max(0, min(3, level + (1 if dither > 0.8 else 0)))]
    elif g > 0.992 and t.face != "bottom":
        c = LICHEN
    return c + (255,)


# ----------------------------------------------------------------------------
# Items
# ----------------------------------------------------------------------------

# a lumpy rock in the colours of a vanilla amethyst geode: smooth-basalt crust, a calcite rim around a crack, and
# amethyst crystals inside
GEODE_ROWS = [
    "................",
    "................",
    "......###.......",
    "....##aab##.....",
    "...#aabbbcc#....",
    "..#abbbbcccc#...",
    "..#abbwwwvccd#..",
    ".#abbwqrsvcdd#..",
    ".#abbwpqtsvcd#..",
    ".#bbcwpqrqvdd#..",
    "..#bcvwpqvvdd#..",
    "..#bccvvvvdd#...",
    "...#ccdddddd#...",
    "....##ddd###....",
    "......###.......",
    "................",
]
GEODE_PAL = {"#": (27, 30, 38), "a": (112, 112, 112), "b": (92, 92, 92), "c": (79, 75, 79), "d": (58, 59, 72),
             "w": (237, 236, 230), "v": (201, 201, 196), "p": (84, 57, 138), "q": (111, 79, 171), "r": (141, 106, 204),
             "s": (179, 142, 243), "t": (254, 203, 230)}


def geode_icon(rich=False):
    """The geode item: rough crust with a glinting crack of crystals (the rich one sparkles more)."""
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for y, row in enumerate(GEODE_ROWS):
        for x, ch in enumerate(row):
            if ch == ".":
                continue
            c = GEODE_PAL[ch]
            g = Q.hash3(x, y, 5)
            if ch in "bc" and g > 0.82:
                c = GEODE_PAL["d"]
            elif ch in "bc" and g < 0.1:
                c = GEODE_PAL["a"]
            if rich and ch in "qr" and g > 0.5:
                c = GEODE_PAL["s"]
            img.putpixel((x, y), Q.rgba(c))
    img.putpixel((5, 4), Q.rgba((150, 150, 150)))  # light catching the top of the crust
    if rich:
        for p in ((12, 3), (3, 12), (13, 9)):
            img.putpixel(p, Q.rgba((255, 253, 213)))
        img.putpixel((8, 7), Q.rgba(GEODE_PAL["t"]))
    return img


def egg():
    """A stone egg with a mossy crown and a moai face: heavy brow, coral eyes, long nose, pursed mouth."""
    def paint(x, y):
        g = Q.hash3(x, y, 13)
        c = STONE[3] if g > 0.55 else STONE[2] if g > 0.2 else STONE[1]
        if y <= 3 or (y == 4 and g > 0.4):
            c = MOSS[2] if g > 0.4 else MOSS[1]
        if y == 6 and 3 <= x <= 12:
            c = STONE[4]  # the brow
        if y == 7 and 3 <= x <= 12:
            c = SHADOW
        if y == 8 and x in (4, 5, 10, 11):
            c = CORAL
        if y == 8 and x in (6, 9):
            c = SHADOW
        if 7 <= y <= 11 and x in (7, 8):
            c = STONE[4] if x == 7 else STONE[3]  # the nose ridge
        if 8 <= y <= 11 and x in (6, 9) and y != 8:
            c = STONE[1]
        if y == 12 and 5 <= x <= 10:
            c = SHADOW  # the mouth
        if y >= 13 and g > 0.6:
            c = MOSS[1]
        return c
    return Q.spawn_egg(paint, {(5, 8): OBSIDIAN + (255,), (10, 8): OBSIDIAN + (255,)})


DELICACIES = ["#c:gems", "#c:ingots", "#c:ores", "#c:storage_blocks", "minecraft:amethyst_shard", "minecraft:amethyst_block",
              "minecraft:diamond", "minecraft:emerald", "minecraft:gold_ingot", "minecraft:iron_ingot", "minecraft:copper_ingot",
              "minecraft:netherite_ingot", "minecraft:lapis_lazuli", "minecraft:quartz", "minecraft:raw_iron", "minecraft:raw_gold",
              "minecraft:raw_copper", "minecraft:echo_shard", "minecraft:prismarine_crystals"]


def generate():
    sp = spec()
    tex = Q.build_texture(sp, paint)
    Q.save_png(tex, "entity", NAME, NAME + ".png")
    Q.write_geometry("com.replecant.naturequirks.stonehead.client", "StoneHeadGeometry", [(sp, "create")],
                     "Stone head model: chest, turning head, hinged jaw and two pupils that follow you.")
    Q.save_png(geode_icon(), "item", "geode.png")
    Q.save_png(geode_icon(rich=True), "item", "geode_rich.png")
    # the item model switches to the glittering texture for a geode chewed from a delicacy (custom_model_data flag)
    Q.write_json(f"{Q.ASSETS}/items/geode.json", {"model": {
        "type": "minecraft:condition", "property": "minecraft:custom_model_data", "index": 0,
        "on_true": {"type": "minecraft:model", "model": f"{Q.MOD}:item/geode_rich"},
        "on_false": {"type": "minecraft:model", "model": f"{Q.MOD}:item/geode"}}})
    for n in ("geode", "geode_rich"):
        Q.write_json(f"{Q.ASSETS}/models/item/{n}.json",
                     {"parent": "minecraft:item/generated", "textures": {"layer0": f"{Q.MOD}:item/{n}"}})
    Q.save_png(egg(), "item", NAME + "_spawn_egg.png")
    Q.item_model(NAME + "_spawn_egg")

    Q.loot_table(f"entities/{NAME}", [
        Q.pool([Q.entry("minecraft:cobblestone", 2, 5, functions=[Q.looting(0, 1)])]),
        Q.pool([Q.entry("minecraft:mossy_cobblestone", 1, 3)]),
        Q.pool([Q.entry(f"{Q.MOD}:geode")]),
    ])
    # cracking a geode: a couple of common finds (more with luck), and a rare treat that luck makes likelier
    Q.loot_table("gameplay/geode", [
        Q.pool([
            Q.entry("minecraft:amethyst_shard", 1, 3, weight=30),
            Q.entry("minecraft:quartz", 1, 3, weight=20),
            Q.entry("minecraft:lapis_lazuli", 1, 4, weight=16),
            Q.entry("minecraft:copper_nugget", 3, 7, weight=14),
            Q.entry("minecraft:iron_nugget", 2, 6, weight=16),
            Q.entry("minecraft:gold_nugget", 2, 5, weight=12),
            Q.entry("minecraft:flint", 1, 2, weight=6),
        ], rolls={"type": "minecraft:uniform", "min": 2, "max": 3}, bonus=0.5),
        Q.pool([
            {"type": "minecraft:empty", "weight": 60, "quality": -4},
            Q.entry("minecraft:emerald", 1, 2, weight=14, quality=3),
            Q.entry("minecraft:amethyst_cluster", weight=10, quality=2),
            Q.entry("minecraft:diamond", weight=3, quality=2),
            Q.entry("minecraft:budding_amethyst", weight=1, quality=1),
        ]),
    ], kind="minecraft:gift")
    Q.tag("item", "stone_head_delicacies", [v if not v.startswith("#c:") else {"id": v, "required": False} for v in DELICACIES])
    Q.tag("worldgen/biome", "has_stone_head", ["#minecraft:is_beach", "minecraft:stony_shore"])
    Q.spawn_modifier("stone_head_spawns", f"{Q.MOD}:has_stone_head", ID, 2, 1, 1)


EN = {
    f"entity.{Q.MOD}.{NAME}": "Stone Head",
    f"item.{Q.MOD}.{NAME}_spawn_egg": "Stone Head Spawn Egg",
    f"item.{Q.MOD}.geode": "Geode",
    f"item.{Q.MOD}.geode.rich": "Glittering Geode",
    f"item.{Q.MOD}.geode.desc": "Use to crack it open",
}
RU = {
    f"entity.{Q.MOD}.{NAME}": "Каменная голова",
    f"item.{Q.MOD}.{NAME}_spawn_egg": "Яйцо призыва каменной головы",
    f"item.{Q.MOD}.geode": "Жеода",
    f"item.{Q.MOD}.geode.rich": "Сверкающая жеода",
    f"item.{Q.MOD}.geode.desc": "Используйте, чтобы расколоть",
}


if __name__ == "__main__":
    generate()
