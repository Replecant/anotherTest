"""Ancient Venusian ruins: stepped pyramids, ziggurats, abandoned villages and jungle shrines of a vanished civilisation.

Generates every asset and data file of the ruins content:
  * block textures / models / blockstates / item definitions for the carved stone of the ruins (venusian_*),
  * artifact item sprites (idol, glyph tablet, sun-disk fragment, amulet),
  * loot tables (block drops, chests, archaeology, the dart trap), tags and recipes,
  * structure templates (.nbt, written with the NBT writer of station.py) and the world-gen data that places them in
    the Venus dimension: template pools, processor lists (weathering), structures, structure sets and biome tags.

Called from gen_resources.main(); EN / RU are merged into the lang files.

Template conventions (template-local X east, Z south, Y up; the entrance of a building faces north, -Z):
  * a structure is a dict {(x, y, z): (block id, {properties}, nbt-or-None)}; positions not listed keep the world;
  * layer G of a single-piece structure is the terrain surface layer (start_height = -G), everything below is
    buried foundation;
  * village houses have one foundation layer (y = 0 replaces the surface) and their street jigsaw at y = 1 in the
    doorway; streets are flat terrain-matching pieces with their jigsaws at y = 1.
"""
import gzip
import math
import os
import random

from gen_resources import ASSETS, DATA, MOD, ROOT, new, save, shaped, shapeless, cooking, tag, write_json
from furniture import add_to_tag
from venus import (B, MOSS, P, FROND, LEAF, generated, get, item, line, mix, model, blockstate, put, shade, simple,
                   smooth_noise, tex, tonal, voronoi)
from station import Compound, Int, List, Str, TAG_COMPOUND, TAG_INT, DATA_VERSION, nbt_bytes, nbt_parse

HERE = os.path.dirname(os.path.abspath(__file__))

# =====================================================================================================================
# Palette: greenish-grey temple masonry, ochre limestone carvings, turquoise inlays, gold sun motifs
# =====================================================================================================================
GREY = [(58, 68, 62), (74, 86, 78), (90, 103, 92), (106, 119, 106), (124, 136, 120)]
OCH = [(104, 84, 54), (128, 106, 68), (150, 127, 84), (171, 148, 100), (192, 171, 122)]
TURQ = [(22, 90, 96), (36, 130, 130), (66, 172, 164), (132, 216, 198)]
GOLD = [(118, 74, 22), (174, 120, 34), (218, 168, 54), (246, 210, 104), (255, 240, 176)]
INK = (40, 44, 38)
CLAY = [(110, 58, 34), (146, 80, 44), (178, 106, 58), (204, 138, 80)]
JADE = [(26, 70, 56), (40, 104, 78), (64, 140, 100), (112, 182, 132)]
MORTAR = (48, 54, 48)


def pick(pal, i):
    return pal[max(0, min(len(pal) - 1, i))]


# =====================================================================================================================
# Block textures
# =====================================================================================================================

def brick_courses(seed, pal, joints=((7, 15), (3, 11), (5, 13), (1, 9)), mortar=MORTAR):
    """Courses of 4px-tall dressed blocks with irregular joints, lit from the top-left (vanilla stone-brick style)."""
    rnd = random.Random(seed)
    base = tonal(seed, pal[1:4], [30, 45, 25], octaves=((4, 0.5), (8, 0.3)), jitter=0.5)
    img = new()
    for row in range(4):
        y0 = row * 4
        js = joints[row % len(joints)]
        tone = {}
        for y in range(y0, y0 + 4):
            for x in range(16):
                if y == y0 + 3 or x in js:
                    put(img, x, y, mortar)
                    continue
                cell = sum(1 for j in js if x > j)
                if cell not in tone:
                    tone[cell] = rnd.choice((-6, -2, 0, 3, 6))
                c = shade(get(base, x, y), tone[cell])
                left_joint = (x - 1) % 16 in js
                right_joint = (x + 1) % 16 in js
                if y == y0 or left_joint:
                    c = shade(c, 14)
                elif y == y0 + 2 or right_joint:
                    c = shade(c, -12)
                put(img, x, y, c)
    return img


def tex_temple_bricks():
    return brick_courses(301, GREY)


def tex_cracked_bricks():
    img = brick_courses(301, GREY)
    rnd = random.Random(305)
    for sx, sy, steps in ((3, 0, 9), (11, 6, 10), (6, 10, 6)):
        x, y = sx, sy
        for _ in range(steps):
            put(img, x, y, (30, 34, 30), True)
            put(img, x + 1, y, shade(get(img, x + 1, y), -18), True)
            x += rnd.choice((-1, 0, 1, 1))
            y += 1
    return img


def tex_mossy_bricks():
    img = brick_courses(301, GREY)
    rnd = random.Random(306)
    noise = smooth_noise(rnd, 16, 16, 4)
    for y in range(16):
        for x in range(16):
            v = noise[y][x] + (0.38 if y < 4 else 0.0) - y * 0.02 + rnd.random() * 0.18
            if v > 0.74:
                put(img, x, y, MOSS[min(3, int((v - 0.74) * 8) + 1)])
            elif v > 0.66:
                put(img, x, y, MOSS[0])
    for x in (2, 6, 9, 13):   # drips
        for y in range(3, 3 + rnd.randint(1, 5)):
            if get(img, x, y - 1)[:3] in MOSS:
                put(img, x, y, MOSS[1] if y % 2 else MOSS[0])
    return img


def ashlar(seed, pal=OCH, bevel=True):
    """One large dressed limestone block with a bevelled border; tiled it reads as fitted ashlar masonry."""
    img = tonal(seed, pal[1:5], [8, 34, 44, 14], octaves=((2, 0.6), (4, 0.4), (8, 0.15)), jitter=0.12)
    rnd = random.Random(seed + 1)
    if bevel:
        for i in range(16):
            put(img, i, 0, shade(pal[4], 6))
            put(img, 0, i, shade(pal[4], 0))
            put(img, i, 15, pal[0])
            put(img, 15, i, pal[0])
        put(img, 0, 15, pal[1])
        put(img, 15, 0, pal[2])
    for _ in range(7):   # weathering pits
        x, y = rnd.randrange(2, 14), rnd.randrange(2, 14)
        put(img, x, y, pal[1])
        if rnd.random() < 0.5:
            put(img, x + 1, y, pal[2])
    return img


def tex_carved_stone():
    return ashlar(311)


GLYPHS = [
    # 0: the sun-eye spiral
    ["..######..",
     ".#......#.",
     "#..####..#",
     "#.#....#.#",
     "#.#.TT.#.#",
     "#.#.TT##.#",
     "#.#......#",
     "#..######.",
     ".#.......#",
     "..#######."],
    # 1: the feathered serpent's head
    ["....####..",
     "..##....#.",
     ".#..TT...#",
     "#...TT..#.",
     "#.......#.",
     "#.##.##..#",
     "#.#.#.#..#",
     ".#.......#",
     "..#.#.#.#.",
     "...#.#.#.."],
    # 2: the stepped fret
    ["##########",
     "#........#",
     "#.######.#",
     "#.#....#.#",
     "#.#.##.#.#",
     "#.#.#T.#.#",
     "#.#.####.#",
     "#.#......#",
     "#.########",
     "#........."],
    # 3: the three-eyed mask
    [".########.",
     "#...TT...#",
     "#...TT...#",
     "#.TT..TT.#",
     "#.TT..TT.#",
     "#........#",
     "#.######.#",
     "#.#.##.#.#",
     "#........#",
     ".########."],
]


def stamp_glyph(img, glyph, ox, oy, raised=OCH[4], shadow=OCH[0], inlay=TURQ):
    """Draws a glyph bitmap as a raised carving with a cast shadow; T pixels are turquoise inlay."""
    h, w = len(glyph), len(glyph[0])
    for y in range(h):
        for x in range(w):
            ch = glyph[y][x]
            if ch == "#":
                put(img, ox + x + 1, oy + y + 1, shadow)
    for y in range(h):
        for x in range(w):
            ch = glyph[y][x]
            if ch == "#":
                put(img, ox + x, oy + y, raised)
            elif ch == "T":
                put(img, ox + x, oy + y, inlay[2] if (x + y) % 2 else inlay[1])


def tex_glyph(i):
    img = ashlar(321 + i)
    # recessed panel
    for y in range(2, 14):
        for x in range(2, 14):
            put(img, x, y, shade(get(img, x, y), -26))
    for i2 in range(2, 14):
        put(img, i2, 2, OCH[0])
        put(img, 2, i2, OCH[0])
        put(img, i2, 13, OCH[4])
        put(img, 13, i2, OCH[4])
    stamp_glyph(img, GLYPHS[i], 3, 3, raised=OCH[3], shadow=(70, 56, 36))
    return img


def tex_inlaid_side():
    img = ashlar(331)
    # turquoise mosaic band with a gold-edged stepped fret
    fret = ["..##....##....##",
            "#.##.##.##.##.##",
            "#....##....##...",
            "######.#####.###"]
    for y in range(4, 12):
        for x in range(16):
            put(img, x, y, TURQ[1] if (x // 2 + y // 2) % 2 else TURQ[2])
            if (x + y) % 4 == 0:
                put(img, x, y, TURQ[0])
    for y, row in enumerate(fret):
        for x, ch in enumerate(row):
            if ch == "#":
                put(img, x, 6 + y, GOLD[2] if y < 2 else GOLD[1])
    for x in range(16):
        put(img, x, 3, GOLD[3])
        put(img, x, 12, GOLD[1])
        put(img, x, 4, TURQ[0])
        put(img, x, 11, TURQ[0])
    return img


def tex_pillar_side():
    img = new()
    rnd = random.Random(341)
    base = tonal(341, OCH[1:5], [20, 40, 28, 12], jitter=0.4)
    for y in range(16):
        for x in range(16):
            k = x % 4
            c = get(base, x, y)
            c = shade(c, (14, 4, -6, -16)[k])
            put(img, x, y, c)
    for y in (0, 1, 14, 15):   # drum bands with a gold line
        for x in range(16):
            put(img, x, y, OCH[3] if y in (0, 15) else OCH[1])
    for x in range(16):
        put(img, x, 1, GOLD[2] if x % 4 else GOLD[1])
        put(img, x, 14, OCH[0])
    for _ in range(4):
        put(img, rnd.randrange(16), rnd.randrange(3, 13), OCH[0])
    return img


def tex_pillar_top():
    img = ashlar(342, bevel=False)
    for y in range(16):
        for x in range(16):
            d = math.hypot(x - 7.5, y - 7.5)
            if 6.6 < d < 7.6:
                put(img, x, y, OCH[0])
            elif 5.6 < d <= 6.6:
                put(img, x, y, OCH[4])
            elif 2.6 < d < 3.5:
                put(img, x, y, OCH[1])
            elif d <= 1.2:
                put(img, x, y, TURQ[1])
    return img


def tex_sun_disc():
    img = ashlar(351)
    cx = cy = 7.5
    for y in range(16):
        for x in range(16):
            dx, dy = x - cx, y - cy
            d = math.hypot(dx, dy)
            a = math.atan2(dy, dx)
            ray = (math.cos(a * 8) + 1) / 2
            if d < 4.7:
                c = GOLD[3] if d < 3.6 else GOLD[2]
                if dx + dy < -2.5:
                    c = GOLD[4] if d < 4 else c
                put(img, x, y, c)
            elif d < 5.4:
                put(img, x, y, GOLD[1])
            elif d < 7.6 and ray > 0.55 + (d - 5.4) * 0.16:
                put(img, x, y, GOLD[2] if d < 6.6 else GOLD[1])
    # a stern Tonatiuh-like face: heavy brows, square turquoise eyes, a fanged open mouth with a jutting tongue
    for x in (5, 6, 9, 10):
        put(img, x, 5, GOLD[0])
        put(img, x, 6, TURQ[2] if x in (6, 9) else TURQ[1])
    put(img, 7, 7, GOLD[1])
    put(img, 8, 7, GOLD[1])
    for x in range(6, 10):
        put(img, x, 9, (70, 30, 24))
    put(img, 6, 10, GOLD[4])
    put(img, 9, 10, GOLD[4])
    put(img, 7, 10, (150, 50, 40))
    put(img, 8, 10, (150, 50, 40))
    put(img, 7, 11, (120, 40, 30))
    put(img, 8, 11, (120, 40, 30))
    return img


def tex_altar_side():
    img = ashlar(361, GREY, bevel=False)
    for x in range(16):   # rim
        put(img, x, 0, GOLD[3] if x % 3 else GOLD[2])
        put(img, x, 1, GOLD[1])
        put(img, x, 5, GREY[0])
    for x in range(16):
        for y in range(2, 5):
            put(img, x, y, OCH[2] if (x + (y == 3)) % 4 else TURQ[1])
    # a frieze of little skull-like glyph faces on the pedestal
    for gx in (4, 10):
        for (x, y) in ((gx - 1, 8), (gx, 8), (gx + 1, 8), (gx - 1, 9), (gx + 1, 9), (gx - 1, 10), (gx, 10), (gx + 1, 10),
                       (gx, 11)):
            put(img, x, y, OCH[3])
        put(img, gx, 9, INK)
    for x in range(16):
        put(img, x, 15, GREY[0])
    return img


def tex_altar_top():
    img = ashlar(362, GREY)
    for y in range(16):
        for x in range(16):
            d = math.hypot(x - 7.5, y - 7.5)
            if d < 4.6:
                put(img, x, y, (52, 34, 30) if d < 3.6 else (78, 56, 44))
            elif d < 5.5:
                put(img, x, y, GOLD[2] if (x + y) % 2 else GOLD[1])
    put(img, 6, 6, (98, 40, 32))
    put(img, 8, 7, (98, 40, 32))
    put(img, 7, 9, (86, 34, 28))
    return img


def tex_stele_front():
    img = ashlar(371, OCH, bevel=False)
    for y in range(16):
        put(img, 0, y, OCH[4])
        put(img, 15, y, OCH[0])
    # two small glyphs stacked in a column with a turquoise divider
    small = [[".####.", "#.TT.#", "#....#", "#.##.#", ".#..#."],
             ["######", "#....#", "#.##.#", "#.#T.#", "#.####"]]
    stamp_glyph(img, small[0], 5, 1, raised=OCH[4], shadow=OCH[0])
    for x in range(3, 13):
        put(img, x, 7, TURQ[1])
    stamp_glyph(img, small[1], 5, 9, raised=OCH[4], shadow=OCH[0])
    return img


def tex_urn():
    """Urn sheet: rows 0-9 body, 10-12 neck, 13-15 rim/lid (UV-mapped by the model)."""
    img = tonal(381, CLAY, [15, 40, 30, 15], jitter=0.35)
    for x in range(16):
        put(img, x, 2, INK)
        put(img, x, 7, INK)
        for y in (3, 4, 5, 6):
            zig = (x + (y - 3)) % 4 == 0 or (x - (y - 3)) % 4 == 0
            put(img, x, y, TURQ[1] if zig else CLAY[3])
        put(img, x, 10, CLAY[0])
        put(img, x, 13, INK)
        put(img, x, 14, CLAY[3])
    return img


def tex_urn_top():
    img = tonal(382, CLAY, [15, 40, 30, 15], jitter=0.35)
    for y in range(16):
        for x in range(16):
            if math.hypot(x - 7.5, y - 7.5) < 2.6:
                put(img, x, y, (40, 26, 22))
    return img


TEXTURES = {
    "venusian_temple_bricks": tex_temple_bricks,
    "venusian_cracked_temple_bricks": tex_cracked_bricks,
    "venusian_mossy_temple_bricks": tex_mossy_bricks,
    "venusian_carved_stone": tex_carved_stone,
    "venusian_glyph_stone_0": lambda: tex_glyph(0),
    "venusian_glyph_stone_1": lambda: tex_glyph(1),
    "venusian_glyph_stone_2": lambda: tex_glyph(2),
    "venusian_glyph_stone_3": lambda: tex_glyph(3),
    "venusian_inlaid_stone": tex_inlaid_side,
    "venusian_pillar": tex_pillar_side,
    "venusian_pillar_top": tex_pillar_top,
    "venusian_sun_disc": tex_sun_disc,
    "venusian_altar_side": tex_altar_side,
    "venusian_altar_top": tex_altar_top,
    "venusian_stele": tex_stele_front,
    "venusian_urn": tex_urn,
    "venusian_urn_top": tex_urn_top,
}


# =====================================================================================================================
# Item sprites
# =====================================================================================================================

def sprite(rows, colors):
    img = new()
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != "." and ch in colors:
                put(img, x, y, colors[ch])
    return img


def item_idol():
    rows = ["................",
            ".....oooooo.....",
            "....ogGGGGgo....",
            "...ogGjjjjGgo...",
            "...oGjYjjYjGo...",
            "...oGjjjjjjGo...",
            "...ogjjkkjjgo...",
            "....oggjjggo....",
            "...ojjjjjjjjo...",
            "..ojjJjjjjJjjo..",
            "..ojJjTTTTjJjo..",
            "..ojjjjjjjjjjo..",
            "...ojjjjjjjjo...",
            "...ojjoooojjo...",
            "...ooo....ooo...",
            "................"]
    return sprite(rows, {"o": (24, 40, 34), "g": GOLD[1], "G": GOLD[2], "j": JADE[2], "J": JADE[3], "Y": GOLD[4],
                         "k": JADE[0], "T": TURQ[2]})


def item_tablet():
    rows = ["................",
            "................",
            "..oooooooooo....",
            "..oSSSSSSSSso...",
            "..oSdSdddSSsoo..",
            "..oSSSSSSdSSso..",
            "..oSddSdSSSSso..",
            "..oSSSSSSSSSso..",
            "..oSdSddSdSSso..",
            "..oSSSSSSSSSso..",
            "..oSddSSdSSsso..",
            "..oSSSSSSSsso...",
            "..oSdSSSsooo....",
            "..osssssoo......",
            "..ooooooo.......",
            "................"]
    img = sprite(rows, {"o": (34, 40, 34), "S": GREY[3], "s": GREY[1], "d": GREY[0]})
    put(img, 4, 4, TURQ[2])
    put(img, 9, 8, TURQ[2])
    return img


def item_fragment():
    img = new()
    cx, cy = 3.5, 12.5
    for y in range(16):
        for x in range(16):
            d = math.hypot(x - cx, y - cy)
            a = math.atan2(cy - y, x - cx)
            if not (-0.1 < a < 1.75):
                continue
            ray = (math.cos(a * 10) + 1) / 2
            broken = d > 6.5 + 2.2 * math.sin(a * 5 + 1) + (1.4 if a > 1.2 else 0)
            if d < 7.2 and not broken:
                put(img, x, y, GOLD[3] if d < 5.5 else GOLD[2])
            elif d < 10.5 and ray > 0.6 and not d > 9.5 + 1.4 * math.sin(a * 7):
                put(img, x, y, GOLD[2] if d < 9 else GOLD[1])
    out = img.copy()
    for y in range(16):
        for x in range(16):
            if img.getpixel((x, y))[3] and any(
                    not (0 <= x + dx < 16 and 0 <= y + dy < 16) or img.getpixel((x + dx, y + dy))[3] == 0
                    for dx, dy in ((1, 0), (0, 1))):
                put(out, x, y, GOLD[0])
    put(out, 5, 9, GOLD[4])
    put(out, 6, 10, GOLD[4])
    put(out, 2, 11, TURQ[2])
    return out


def item_amulet():
    rows = ["....cc....cc....",
            "...c........c...",
            "...c........c...",
            "....c......c....",
            ".....c....c.....",
            "......cgGc......",
            ".....oGGGGo.....",
            "....oGtTTtGo....",
            "...oGtTWTTtGo...",
            "...oGtTTTTtGo...",
            "...oGttkkttGo...",
            "....oGttttGo....",
            ".....oGGGGo.....",
            "......oGGo......",
            ".......oo.......",
            "................"]
    return sprite(rows, {"c": (112, 72, 42), "o": GOLD[0], "g": GOLD[1], "G": GOLD[2], "t": TURQ[1], "T": TURQ[2],
                         "W": TURQ[3], "k": (24, 40, 44)})


ITEM_TEXTURES = {
    "venusian_idol": item_idol,
    "glyph_tablet": item_tablet,
    "sun_disk_fragment": item_fragment,
    "ancient_amulet": item_amulet,
}


# =====================================================================================================================
# Models, blockstates, item definitions
# =====================================================================================================================
BRICKS = "venusian_temple_bricks"
CRACKED = "venusian_cracked_temple_bricks"
MOSSY = "venusian_mossy_temple_bricks"
BSTAIRS = "venusian_temple_brick_stairs"
BSLAB = "venusian_temple_brick_slab"
CARVED = "venusian_carved_stone"
CSTAIRS = "venusian_carved_stone_stairs"
CSLAB = "venusian_carved_stone_slab"
GLYPH = "venusian_glyph_stone"
INLAID = "venusian_inlaid_stone"
PILLAR = "venusian_pillar"
SUN = "venusian_sun_disc"
STELE = "venusian_stele"
ALTAR = "venusian_altar"
URN = "venusian_urn"
BLOCKS = [BRICKS, CRACKED, MOSSY, BSTAIRS, BSLAB, CARVED, CSTAIRS, CSLAB, GLYPH, INLAID, PILLAR, SUN, STELE, ALTAR, URN]
ITEMS = ["venusian_idol", "glyph_tablet", "sun_disk_fragment", "ancient_amulet"]
HORIZONTAL_Y = {"north": 0, "east": 90, "south": 180, "west": 270}


def stairs_and_slab(stairs, slab, full):
    textures = {"bottom": tex(full), "side": tex(full), "top": tex(full)}
    for suffix, parent in (("", "stairs"), ("_inner", "inner_stairs"), ("_outer", "outer_stairs")):
        model(f"{stairs}{suffix}", {"parent": f"minecraft:block/{parent}", "textures": textures})
    base_y = {"east": 0, "south": 90, "west": 180, "north": 270}
    variants = {}
    for facing, by in base_y.items():
        for half in ("bottom", "top"):
            for shape in ("straight", "inner_left", "inner_right", "outer_left", "outer_right"):
                m = P("block/" + stairs + ("_inner" if shape.startswith("inner") else
                                           "_outer" if shape.startswith("outer") else ""))
                if half == "bottom":
                    y = by - 90 if shape.endswith("_left") else by
                else:
                    y = by + 90 if shape.endswith("_right") else by
                v = {"model": m}
                if half == "top":
                    v["x"] = 180
                if y % 360:
                    v["y"] = y % 360
                if len(v) > 1:
                    v["uvlock"] = True
                variants[f"facing={facing},half={half},shape={shape}"] = v
    blockstate(stairs, {"variants": variants})
    item(stairs, P(f"block/{stairs}"))
    model(slab, {"parent": "minecraft:block/slab", "textures": textures})
    model(f"{slab}_top", {"parent": "minecraft:block/slab_top", "textures": textures})
    blockstate(slab, {"variants": {"type=bottom": {"model": P(f"block/{slab}")},
                                   "type=double": {"model": P(f"block/{full}")},
                                   "type=top": {"model": P(f"block/{slab}_top")}}})
    item(slab, P(f"block/{slab}"))


def el(frm, to, faces, shade_=True):
    e = {"from": frm, "to": to, "faces": faces}
    if not shade_:
        e["shade"] = False
    return e


def f(uv, texture, cull=None):
    out = {"uv": uv, "texture": texture}
    if cull:
        out["cullface"] = cull
    return out


def boxel(frm, to, side, top, bottom=None, cull_bottom=False, side_uv=None):
    x0, y0, z0 = frm
    x1, y1, z1 = to
    suv = side_uv or [x0, 16 - y1, x1, 16 - y0]
    zuv = side_uv or [z0, 16 - y1, z1, 16 - y0]
    return el(frm, to, {
        "north": f(suv, side), "south": f(suv, side), "west": f(zuv, side), "east": f(zuv, side),
        "up": f([x0, z0, x1, z1], top), "down": f([x0, z0, x1, z1], bottom or top, "down" if cull_bottom else None)})


def block_models():
    for name in (BRICKS, CRACKED, MOSSY, CARVED):
        simple(name)
    stairs_and_slab(BSTAIRS, BSLAB, BRICKS)
    stairs_and_slab(CSTAIRS, CSLAB, CARVED)
    # glyph stone: one model per glyph, picked by the "glyph" property
    for i in range(4):
        model(f"{GLYPH}_{i}", {"parent": "minecraft:block/cube_column",
                               "textures": {"side": tex(f"{GLYPH}_{i}"), "end": tex(CARVED)}})
    blockstate(GLYPH, {"variants": {f"glyph={i}": {"model": P(f"block/{GLYPH}_{i}")} for i in range(4)}})
    item(GLYPH, P(f"block/{GLYPH}_0"))
    simple(INLAID, parent="minecraft:block/cube_column", textures={"side": tex(INLAID), "end": tex(CARVED)})
    # pillar (axis)
    model(PILLAR, {"parent": "minecraft:block/cube_column",
                   "textures": {"end": tex("venusian_pillar_top"), "side": tex(PILLAR)}})
    model(f"{PILLAR}_horizontal", {"parent": "minecraft:block/cube_column_horizontal",
                                   "textures": {"end": tex("venusian_pillar_top"), "side": tex(PILLAR)}})
    blockstate(PILLAR, {"variants": {
        "axis=x": {"model": P(f"block/{PILLAR}_horizontal"), "x": 90, "y": 90},
        "axis=y": {"model": P(f"block/{PILLAR}")},
        "axis=z": {"model": P(f"block/{PILLAR}_horizontal"), "x": 90}}})
    item(PILLAR, P(f"block/{PILLAR}"))
    # sun disc: relief on the front (north in the model), carved stone elsewhere
    model(SUN, {"parent": "minecraft:block/orientable",
                "textures": {"front": tex(SUN), "side": tex(CARVED), "top": tex(CARVED)}})
    blockstate(SUN, {"variants": {f"facing={d}": {"model": P(f"block/{SUN}"), **({"y": r} if r else {})}
                                  for d, r in HORIZONTAL_Y.items()}})
    item(SUN, P(f"block/{SUN}"))
    # stele: a thick upright slab with glyph columns on both faces
    front, side = "#front", "#side"
    model(STELE, {"parent": "minecraft:block/block", "textures": {"particle": tex(STELE), "front": tex(STELE),
                                                                   "side": tex(CARVED)},
                  "elements": [el([2, 0, 5], [14, 16, 11], {
                      "north": f([2, 0, 14, 16], front), "south": f([2, 0, 14, 16], front),
                      "west": f([5, 0, 11, 16], side), "east": f([5, 0, 11, 16], side),
                      "up": f([2, 5, 14, 11], side, "up"), "down": f([2, 5, 14, 11], side, "down")})]})
    blockstate(STELE, {"variants": {f"facing={d}": {"model": P(f"block/{STELE}"), **({"y": r} if r else {})}
                                    for d, r in HORIZONTAL_Y.items()}})
    item(STELE, P(f"block/{STELE}"))
    # altar: pedestal under a wide offering table
    model(ALTAR, {"parent": "minecraft:block/block",
                  "textures": {"particle": tex("venusian_altar_side"), "side": tex("venusian_altar_side"),
                               "top": tex("venusian_altar_top"), "base": tex(CARVED)},
                  "elements": [
                      boxel([3, 0, 3], [13, 9, 13], "#side", "#base", cull_bottom=True, side_uv=[3, 6, 13, 15]),
                      boxel([1, 9, 1], [15, 13, 15], "#side", "#top", "#base", side_uv=[1, 0, 15, 4])]})
    blockstate(ALTAR, {"variants": {"": {"model": P(f"block/{ALTAR}")}}})
    item(ALTAR, P(f"block/{ALTAR}"))
    # urn: bulbous body, neck and rim
    model(URN, {"parent": "minecraft:block/block",
                "textures": {"particle": tex(URN), "urn": tex(URN), "top": tex("venusian_urn_top")},
                "elements": [
                    boxel([3, 0, 3], [13, 10, 13], "#urn", "#top", cull_bottom=True, side_uv=[0, 0, 10, 10]),
                    boxel([5, 10, 5], [11, 13, 11], "#urn", "#top", side_uv=[0, 10, 6, 13]),
                    boxel([4, 13, 4], [12, 15, 12], "#urn", "#top", side_uv=[0, 13, 8, 15])]})
    blockstate(URN, {"variants": {"": {"model": P(f"block/{URN}")}}})
    item(URN, P(f"block/{URN}"))
    for name in ITEMS:
        generated(name, P(f"item/{name}"))


def textures():
    for name, fn in TEXTURES.items():
        save(fn(), "block", name)
    for name, fn in ITEM_TEXTURES.items():
        save(fn(), "item", name)


# =====================================================================================================================
# Loot tables, tags, recipes
# =====================================================================================================================

def loot_block(name, pools):
    write_json(os.path.join(DATA, "loot_table", "blocks", name + ".json"),
               {"type": "minecraft:block", "pools": pools, "random_sequence": f"{MOD}:blocks/{name}"})


def self_pool(name, functions=None):
    e = {"type": "minecraft:item", "name": P(name)}
    if functions:
        e["functions"] = functions
    return {"rolls": 1, "bonus_rolls": 0, "entries": [e], "conditions": [{"condition": "minecraft:survives_explosion"}]}


def block_loot():
    for b in BLOCKS:
        if b in (BSLAB, CSLAB):
            loot_block(b, [self_pool(b, [
                {"function": "minecraft:set_count", "add": False, "count": 2.0,
                 "conditions": [{"condition": "minecraft:block_state_property", "block": P(b),
                                 "properties": {"type": "double"}}]},
                {"function": "minecraft:explosion_decay"}])])
        else:
            loot_block(b, [self_pool(b)])


def count(lo, hi=None):
    if hi is None or hi == lo:
        return {"function": "minecraft:set_count", "add": False, "count": float(lo)}
    return {"function": "minecraft:set_count", "add": False,
            "count": {"type": "minecraft:uniform", "min": float(lo), "max": float(hi)}}


def it(name, weight, lo=1, hi=None, extra=None):
    e = {"type": "minecraft:item", "name": name if ":" in name else P(name), "weight": weight}
    fns = []
    if lo != 1 or (hi and hi != 1):
        fns.append(count(lo, hi))
    fns += extra or []
    if fns:
        e["functions"] = fns
    return e


def empty(weight):
    return {"type": "minecraft:empty", "weight": weight}


def rolls(lo, hi=None):
    return float(lo) if hi is None else {"type": "minecraft:uniform", "min": float(lo), "max": float(hi)}


def chest(name, pools, kind="minecraft:chest"):
    write_json(os.path.join(DATA, "loot_table", *name.split("/")) + ".json",
               {"type": kind, "pools": [{"rolls": r, "bonus_rolls": 0.0, "entries": e} for r, e in pools],
                "random_sequence": f"{MOD}:{name}"})


TABLET_LORES = 6   # item.retrocosmos.glyph_tablet.lore_N: "translations" pencilled in by the lost expedition


def tablets(weight):
    """Glyph tablets, each carrying one of the expedition's pencilled translations as its lore."""
    out = []
    for i in range(TABLET_LORES):
        out.append(it("glyph_tablet", max(1, weight // TABLET_LORES), extra=[{
            "function": "minecraft:set_lore", "mode": "replace_all",
            "lore": [{"translate": f"item.{MOD}.glyph_tablet.lore_{i}", "color": "gray", "italic": True}]}]))
    return out


JOURNAL_PAGES = 4


def journal(weight):
    return {"type": "minecraft:item", "name": "minecraft:written_book", "weight": weight, "functions": [
        {"function": "minecraft:set_book_cover", "title": {"raw": "Expedition Log"}, "author": "Dr. H. Calloway",
         "generation": 3},
        {"function": "minecraft:set_written_book_pages", "mode": "replace_all",
         "pages": [{"raw": {"translate": f"book.{MOD}.expedition_log.page_{i}"}} for i in range(JOURNAL_PAGES)]},
        {"function": "minecraft:set_name", "target": "custom_name",
         "name": {"translate": f"book.{MOD}.expedition_log.title", "italic": False, "color": "yellow"}}]}


def chest_loot():
    artifacts = [it("venusian_idol", 6), it("sun_disk_fragment", 10, 1, 3), it("ancient_amulet", 2)] + tablets(12)
    precious = [it("minecraft:gold_ingot", 14, 2, 6), it("minecraft:gold_nugget", 16, 4, 12),
                it("minecraft:emerald", 12, 1, 4), it("minecraft:diamond", 3, 1, 2), it("minecraft:raw_gold", 8, 1, 3),
                it("minecraft:iron_ingot", 10, 1, 4), it("minecraft:lapis_lazuli", 8, 2, 7)]
    grave = [it("minecraft:bone", 12, 1, 4), it("minecraft:rotten_flesh", 4, 1, 3), it("minecraft:string", 6, 1, 3),
             it("minecraft:arrow", 4, 2, 6), it("minecraft:candle", 4, 1, 3)]
    expedition = [it("rocket_fuel_canister", 3), it("empty_fuel_canister", 6), it("vacuum_tube", 5, 1, 2),
                  it("aluminum_ingot", 5, 1, 3), it("minecraft:torch", 8, 2, 6), it("minecraft:bread", 6, 1, 3),
                  it("minecraft:compass", 2), journal(4)]
    chest("chests/venusian_pyramid_tomb", [
        (rolls(2, 4), artifacts + [it("ancient_amulet", 3)]),
        (rolls(3, 6), precious + [it("minecraft:golden_apple", 3), it("minecraft:enchanted_book", 3, extra=[
            {"function": "minecraft:enchant_randomly"}])]),
        (rolls(2, 4), grave)])
    chest("chests/venusian_pyramid_temple", [
        (rolls(1, 3), artifacts),
        (rolls(2, 4), precious + grave),
        (rolls(0, 1), expedition + [empty(10)])])
    chest("chests/venusian_ziggurat_treasury", [
        (rolls(3, 5), artifacts + [it("ancient_amulet", 2)]),
        (rolls(4, 7), precious + [it("minecraft:gold_block", 2), it("minecraft:emerald", 6, 3, 8),
                                  it("minecraft:golden_horse_armor", 2), it("minecraft:enchanted_book", 3, extra=[
                                      {"function": "minecraft:enchant_randomly"}])]),
        (rolls(1, 2), expedition)])
    chest("chests/venusian_expedition_cache", [
        (rolls(3, 5), expedition + [it("rocket_fuel_canister", 4), it("minecraft:paper", 6, 1, 4),
                                    it("minecraft:iron_pickaxe", 1), it("minecraft:spyglass", 1)]),
        (1.0, [journal(1)]),
        (rolls(0, 2), tablets(6) + [it("sun_disk_fragment", 2)])], kind="minecraft:chest")
    chest("chests/venusian_village", [
        (rolls(1, 3), tablets(10) + [it("sun_disk_fragment", 4), it("venusian_idol", 2), empty(6)]),
        (rolls(2, 5), [it("minecraft:gold_nugget", 12, 2, 8), it("minecraft:iron_nugget", 10, 2, 9),
                       it("minecraft:emerald", 6, 1, 2), it("minecraft:bone", 10, 1, 3), it("minecraft:string", 6, 1, 2),
                       it("minecraft:flint", 6, 1, 3), it("minecraft:clay_ball", 6, 2, 5), it("minecraft:wheat_seeds", 4, 1, 4),
                       it("minecraft:lapis_lazuli", 4, 1, 4), it("minecraft:bowl", 4)])])
    chest("chests/venusian_shrine", [
        (rolls(1, 2), [it("sun_disk_fragment", 8), it("venusian_idol", 3), it("ancient_amulet", 1)] + tablets(6)),
        (rolls(1, 4), [it("minecraft:gold_nugget", 14, 2, 9), it("minecraft:emerald", 6, 1, 3),
                       it("minecraft:gold_ingot", 4, 1, 2), it("minecraft:candle", 6, 1, 2), it("minecraft:bone", 8, 1, 2),
                       empty(4)])])
    chest("chests/venusian_dart_trap", [(1.0, [it("minecraft:arrow", 1, 4, 7)])], kind="minecraft:chest")
    chest("archaeology/venusian_ruins", [
        (1.0, [it("glyph_tablet", 4), it("sun_disk_fragment", 4), it("venusian_idol", 1), it("minecraft:gold_nugget", 6, 1, 3),
               it("minecraft:emerald", 2), it("minecraft:bone", 4), it("minecraft:flower_pot", 2), it("minecraft:brick", 3),
               it("minecraft:lapis_lazuli", 2)])], kind="minecraft:archaeology")


def tags():
    blocks = [P(b) for b in BLOCKS]
    add_to_tag("block/mineable/pickaxe", blocks)
    for kind in ("block", "item"):
        add_to_tag(f"{kind}/stairs", [P(BSTAIRS), P(CSTAIRS)])
        add_to_tag(f"{kind}/slabs", [P(BSLAB), P(CSLAB)])
    # processor helpers: what weathering may knock out of village walls
    tag("block/venusian_crumbling", [P(BRICKS), P(CRACKED), P(MOSSY), P(CARVED), P(BSLAB), P(CSLAB),
                                     "retrocosmos:venus_cobblestone"], namespace=MOD)
    tag("block/venusian_rubble", ["minecraft:gravel"], namespace=MOD)


def stonecut(name, ingredient, result, n=1):
    write_json(os.path.join(DATA, "recipe", name + ".json"), {
        "type": "minecraft:stonecutting", "ingredient": P(ingredient), "result": {"id": P(result), "count": n}})


def recipes():
    shaped(BRICKS, ["SS", "SS"], {"S": CARVED}, BRICKS, count=4, category="building")
    shapeless(f"{MOSSY}_from_vines", [BRICKS, "venus_hanging_vines"], MOSSY, category="building")
    shapeless(f"{MOSSY}_from_moss", [BRICKS, "venus_moss"], MOSSY, category="building")
    cooking(f"{CRACKED}_from_smelting", "smelting", BRICKS, CRACKED, 0.1, 200)
    for stairs, slab, full in ((BSTAIRS, BSLAB, BRICKS), (CSTAIRS, CSLAB, CARVED)):
        shaped(stairs, ["S  ", "SS ", "SSS"], {"S": full}, stairs, count=4, category="building")
        shaped(slab, ["SSS"], {"S": full}, slab, count=6, category="building")
        stonecut(f"{stairs}_from_stonecutting", full, stairs)
        stonecut(f"{slab}_from_stonecutting", full, slab, 2)
    shaped(PILLAR, ["S", "S"], {"S": CARVED}, PILLAR, count=2, category="building")
    for b in (GLYPH, INLAID, PILLAR, STELE, BRICKS):
        stonecut(f"{b}_from_stonecutting", CARVED, b)
    stonecut(f"{BSTAIRS}_from_carved_stonecutting", CARVED, BSTAIRS)
    stonecut(f"{BSLAB}_from_carved_stonecutting", CARVED, BSLAB, 2)
    shaped(SUN, [" F ", "FSF", " G "], {"F": "sun_disk_fragment", "S": CARVED, "G": "minecraft:glowstone_dust"}, SUN,
           category="building")
    shaped(ALTAR, ["SSS", " C ", "CCC"], {"S": CSLAB, "C": CARVED}, ALTAR, category="decorations")
    shaped(URN, ["B B", "B B", " B "], {"B": "minecraft:brick"}, URN, category="decorations")
    shapeless("gold_nuggets_from_sun_disk_fragment", ["sun_disk_fragment"], "minecraft:gold_nugget", count=5)


# =====================================================================================================================
# Structure builder
# =====================================================================================================================
AIR = "minecraft:air"
HORIZ = ("north", "east", "south", "west")
DIRS = {"north": (0, -1), "south": (0, 1), "west": (-1, 0), "east": (1, 0)}
OPP = {"north": "south", "south": "north", "west": "east", "east": "west"}


def R(name):
    return name if ":" in name else f"{MOD}:{name}"


def st(name, **props):
    return (R(name) if not name.startswith("minecraft:") else name, {k: str(v).lower() for k, v in props.items()}, None)


def stairs(name, facing, half="bottom", shape="straight"):
    return st(name, facing=facing, half=half, shape=shape, waterlogged=False)


def slab(name, kind="bottom"):
    return st(name, type=kind, waterlogged=False)


def glyph(i):
    return st(GLYPH, glyph=i % 4)


def faced(name, facing):
    return st(name, facing=facing)


def chest_state(facing, table):
    return ("minecraft:chest", {"facing": facing, "type": "single", "waterlogged": "false"},
            Compound({"id": Str("minecraft:chest"), "LootTable": Str(f"{MOD}:{table}")}))


def barrel_state(table, facing="up"):
    return ("minecraft:barrel", {"facing": facing, "open": "false"},
            Compound({"id": Str("minecraft:barrel"), "LootTable": Str(f"{MOD}:{table}")}))


def dispenser_state(facing, table="chests/venusian_dart_trap"):
    return ("minecraft:dispenser", {"facing": facing, "triggered": "false"},
            Compound({"id": Str("minecraft:dispenser"), "LootTable": Str(f"{MOD}:{table}")}))


def jigsaw_state(facing, name, target, pool, final_state="minecraft:air", vertical=None):
    orientation = f"{facing}_up" if vertical is None else f"{vertical}_{facing}"
    return ("minecraft:jigsaw", {"orientation": orientation},
            Compound({"id": Str("minecraft:jigsaw"), "name": Str(name), "target": Str(target), "pool": Str(pool),
                      "final_state": Str(final_state), "joint": Str("aligned" if vertical is None else "rollable")}))


def vine_state(*walls):
    return ("minecraft:vine", {d: ("true" if d in walls else "false") for d in ("north", "east", "south", "west", "up")},
            None)


S_AIR = (AIR, {}, None)
S_BRICK = st(BRICKS)
S_CRACKED = st(CRACKED)
S_MOSSY = st(MOSSY)
S_CARVED = st(CARVED)
S_INLAID = st(INLAID)
S_PILLAR = st(PILLAR, axis="y")
S_MOSS = st("venus_moss")
S_SOIL = st("venus_soil")
S_COBBLE = st("venus_cobblestone")
S_URN = st(URN)
S_ALTAR = st(ALTAR)
S_WEB = st("minecraft:cobweb")

FULL = {R(b) for b in (BRICKS, CRACKED, MOSSY, CARVED, GLYPH, INLAID, PILLAR, SUN)} | {
    R(b) for b in ("venus_stone", "venus_cobblestone", "venus_stone_bricks", "venus_moss", "venus_soil", "venus_mud",
                   "venus_black_rock", "venus_log", "venus_planks")} | {
    "minecraft:gravel", "minecraft:suspicious_gravel", "minecraft:white_wool", "minecraft:barrel", "minecraft:dispenser",
    "minecraft:bone_block", "minecraft:moss_block"}
STONE_WALL = {R(b) for b in (BRICKS, CRACKED, MOSSY, CARVED, GLYPH, INLAID, PILLAR)}
PLANTABLE = {R("venus_moss"), R("venus_soil"), R("venus_mud")}
KEEP = {"minecraft:chest", "minecraft:barrel", "minecraft:dispenser", "minecraft:jigsaw", "minecraft:stone_pressure_plate"}


class Ruin:
    """A structure template under construction."""

    def __init__(self, name, size, seed, ground=0):
        self.name = name
        self.W, self.H, self.D = size
        self.b = {}
        self.rnd = random.Random(seed)
        self.seed = seed
        self.G = ground
        self.protect = set()          # positions decay must never touch (stairs, doorways, loot)

    def inside(self, x, y, z):
        return 0 <= x < self.W and 0 <= y < self.H and 0 <= z < self.D

    def set(self, x, y, z, state):
        if self.inside(x, y, z):
            self.b[(x, y, z)] = state

    def fill(self, x0, y0, z0, x1, y1, z1, state):
        for x in range(min(x0, x1), max(x0, x1) + 1):
            for y in range(min(y0, y1), max(y0, y1) + 1):
                for z in range(min(z0, z1), max(z0, z1) + 1):
                    self.set(x, y, z, state() if callable(state) else state)

    def name_at(self, x, y, z):
        s = self.b.get((x, y, z))
        return s[0] if s else None

    def full(self, x, y, z):
        return self.name_at(x, y, z) in FULL

    def open_(self, x, y, z):
        """Air in the finished structure (explicit air or a position the template leaves to the world above ground)."""
        n = self.name_at(x, y, z)
        return n == AIR or (n is None and y > self.G)

    def remove(self, x, y, z):
        if (x, y, z) in self.protect or self.name_at(x, y, z) in KEEP:
            return False
        if (x, y, z) in self.b:
            self.b[(x, y, z)] = S_AIR
            return True
        return False

    def tall_plant(self, x, y, z, name):
        self.set(x, y, z, st(name, half="lower"))
        self.set(x, y + 1, z, st(name, half="upper"))

    # ---------------------------------------------------------------- decay helpers
    def blob(self, cx, cy, cz, r, ymin=None, rubble=True, squash=1.0):
        """Collapses an irregular blob of masonry; the debris piles up on the surfaces below."""
        rnd = random.Random(self.seed * 31 + cx * 7 + cy * 13 + cz)
        ymin = self.G + 1 if ymin is None else ymin
        removed = []
        R_ = int(r) + 2
        for x in range(cx - R_, cx + R_ + 1):
            for y in range(max(ymin, cy - R_), cy + R_ + 1):
                for z in range(cz - R_, cz + R_ + 1):
                    d = math.sqrt((x - cx) ** 2 + ((y - cy) / squash) ** 2 + (z - cz) ** 2)
                    wob = 0.9 * math.sin(x * 1.7 + z * 0.9 + self.seed) + 0.7 * math.cos(y * 1.3 + x * 0.5)
                    if d + wob * 0.6 + rnd.random() * 0.8 < r and self.name_at(x, y, z) not in (None, AIR):
                        if self.remove(x, y, z):
                            removed.append((x, y, z))
        if rubble:
            cols = {}
            for (x, y, z) in removed:
                cols[(x, z)] = max(cols.get((x, z), -1), y)
            for (x, z), _y in cols.items():
                if rnd.random() < 0.45:
                    self.drop_rubble(x + rnd.choice((-1, 0, 0, 1)), z + rnd.choice((-1, 0, 0, 1)), _y, rnd)
        return removed

    def surface_y(self, x, z, start):
        """Highest y <= start whose block is full and has open space above (or None)."""
        for y in range(min(start, self.H - 2), self.G - 1, -1):
            if self.full(x, y, z) and self.open_(x, y + 1, z):
                return y
            if not self.open_(x, y, z) and not self.full(x, y, z):
                return None
        return None

    def drop_rubble(self, x, z, start, rnd):
        y = self.surface_y(x, z, start)
        if y is None or (x, y + 1, z) in self.protect:
            return
        pick_ = rnd.random()
        if pick_ < 0.35:
            state = slab(rnd.choice((BSLAB, CSLAB, BSLAB)))
        elif pick_ < 0.45:
            state = S_COBBLE
        elif pick_ < 0.75:
            state = rnd.choice((S_CRACKED, S_CRACKED, S_CARVED))
        elif pick_ < 0.88:
            state = stairs(rnd.choice((BSTAIRS, CSTAIRS)), rnd.choice(HORIZ))
        else:
            state = S_MOSSY
        if self.name_at(x, y + 1, z) in (None, AIR):
            self.set(x, y + 1, z, state)

    def jag_tops(self, prob, names=STONE_WALL, ymin=None):
        """Knocks single blocks off exposed wall tops for a ragged silhouette."""
        rnd = random.Random(self.seed + 77)
        ymin = self.G + 2 if ymin is None else ymin
        for (x, y, z), s in sorted(self.b.items()):
            if y >= ymin and s[0] in names and self.open_(x, y + 1, z) and rnd.random() < prob:
                self.remove(x, y, z)

    def sky(self, x, y, z):
        """Open to the sky above (y)."""
        return all(self.open_(x, yy, z) and self.name_at(x, yy, z) in (None, AIR) for yy in range(y + 1, self.H))

    def erode_columns(self, prob, max_drop, ymin=2):
        """Lowers the crown of walls column by column (smoothly varying), so walls end in broken, stepped tops."""
        rnd = random.Random(self.seed + 141)
        noise = smooth_noise(random.Random(self.seed + 142), 32, 32, 4)
        cols = {}
        for (x, y, z), st_ in self.b.items():
            if st_[0] in STONE_WALL or st_[0] in (R(BSLAB), R(CSLAB)):
                cols[(x, z)] = max(cols.get((x, z), -1), y)
        for (x, z), top in sorted(cols.items()):
            if rnd.random() > prob:
                continue
            drop = int(noise[z % 32][x % 32] * (max_drop + 1.2))
            for y in range(top, max(ymin, top - drop) - 1, -1):
                n = self.name_at(x, y, z)
                if n in STONE_WALL or n in (R(BSLAB), R(CSLAB)):
                    self.remove(x, y, z)

    def mossify(self, prob, turf=0.0, ymin=None):
        """Moss over exposed tops: bricks turn mossy, some horizontal surfaces become turf (venus_moss)."""
        rnd = random.Random(self.seed + 91)
        noise = smooth_noise(random.Random(self.seed + 92), 64, 64, 8)
        ymin = self.G if ymin is None else ymin
        for (x, y, z), s in sorted(self.b.items()):
            if y < ymin or s[0] not in STONE_WALL or (x, y, z) in self.protect or not self.open_(x, y + 1, z):
                continue
            n = noise[z % 64][x % 64] + rnd.random() * 0.35
            if turf and n > 1.15 - turf and self.sky(x, y, z) and s[0] in (R(BRICKS), R(CRACKED), R(MOSSY), R(CARVED)):
                self.b[(x, y, z)] = S_MOSS
            elif n > 1.05 - prob and s[0] == R(BRICKS):
                self.b[(x, y, z)] = S_MOSSY

    def plants(self, prob, ymin=None, tall=0.25, ferns=True):
        rnd = random.Random(self.seed + 101)
        ymin = self.G if ymin is None else ymin
        for (x, y, z), s in sorted(self.b.items()):
            if y < ymin or s[0] not in PLANTABLE or not self.open_(x, y + 1, z) or (x, y + 1, z) in self.protect:
                continue
            if self.name_at(x, y + 1, z) not in (None, AIR) or rnd.random() > prob or not self.sky(x, y, z):
                continue
            r = rnd.random()
            if ferns and r < tall and self.open_(x, y + 2, z) and self.name_at(x, y + 2, z) in (None, AIR):
                self.tall_plant(x, y + 1, z, rnd.choice(("venus_giant_fern", "venus_giant_fern", "venus_tree_fern")))
            elif r < 0.55:
                self.set(x, y + 1, z, st("venus_sedge"))
            elif r < 0.75:
                self.set(x, y + 1, z, st("venus_horsetail"))
            elif r < 0.88:
                self.set(x, y + 1, z, st("venus_cycad"))
            else:
                self.set(x, y + 1, z, st("venus_fire_lily"))

    def wall_vines(self, prob, ymin=None, max_len=7):
        """Vanilla vines creeping down exposed wall faces from their top edge."""
        rnd = random.Random(self.seed + 111)
        ymin = self.G + 1 if ymin is None else ymin
        for (x, y, z), s in sorted(self.b.items()):
            if s[0] not in STONE_WALL or y < ymin + 1:
                continue
            for d, (dx, dz) in DIRS.items():
                vx, vz = x + dx, z + dz
                if not (self.open_(vx, y, vz) and self.name_at(vx, y, vz) in (None, AIR)):
                    continue
                if not self.open_(x, y + 1, z) and self.full(x, y + 1, z):
                    continue      # only start at the top edge of a wall
                if rnd.random() > prob:
                    continue
                n = rnd.randint(2, max_len)
                yy = y
                while n > 0 and yy >= ymin and self.full(x, yy, z) and self.name_at(vx, yy, vz) in (None, AIR) \
                        and self.open_(vx, yy, vz) and (vx, yy, vz) not in self.protect:
                    self.set(vx, yy, vz, vine_state(OPP[d]))
                    yy -= 1
                    n -= 1

    def hanging_vines(self, prob, ymin=None, max_len=4, explicit_only=False):
        """Venusian lianas hanging from ceilings, lintels and overhangs."""
        rnd = random.Random(self.seed + 121)
        ymin = self.G + 1 if ymin is None else ymin
        for (x, y, z), s in sorted(self.b.items()):
            if s[0] not in FULL or y - 1 < ymin:
                continue
            below = self.name_at(x, y - 1, z)
            if below not in (None, AIR) or (explicit_only and below is None) or not self.open_(x, y - 1, z):
                continue
            if (x, y - 1, z) in self.protect or rnd.random() > prob:
                continue
            n = rnd.randint(1, max_len)
            yy = y - 1
            chain = []
            while len(chain) < n and yy >= ymin and self.name_at(x, yy, z) in (None, AIR) and self.open_(x, yy, z) \
                    and (x, yy, z) not in self.protect and self.open_(x, yy - 1, z):
                chain.append(yy)
                yy -= 1
            for i, cy in enumerate(chain):
                self.set(x, cy, z, st("venus_hanging_vines", tip=(i == len(chain) - 1)))

    def cobwebs(self, prob, boxes):
        rnd = random.Random(self.seed + 131)
        for (x0, y0, z0, x1, y1, z1) in boxes:
            for x in range(x0, x1 + 1):
                for y in range(y0, y1 + 1):
                    for z in range(z0, z1 + 1):
                        if self.name_at(x, y, z) != AIR or (x, y, z) in self.protect:
                            continue
                        walls = sum(self.full(x + dx, y, z + dz) for dx, dz in DIRS.values()) + self.full(x, y + 1, z)
                        if walls >= 3 and rnd.random() < prob:
                            self.set(x, y, z, S_WEB)

    def perimeter_stairs(self, y, x0, z0, x1, z1, name):
        """A sloping skirt: bottom stairs around a rectangle, high side inwards, corners as outer stairs."""
        for x in range(x0 + 1, x1):
            self.set(x, y, z0, stairs(name, "south"))
            self.set(x, y, z1, stairs(name, "north"))
        for z in range(z0 + 1, z1):
            self.set(x0, y, z, stairs(name, "east"))
            self.set(x1, y, z, stairs(name, "west"))
        self.set(x0, y, z0, stairs(name, "south", shape="outer_left"))
        self.set(x1, y, z0, stairs(name, "south", shape="outer_right"))
        self.set(x0, y, z1, stairs(name, "north", shape="outer_right"))
        self.set(x1, y, z1, stairs(name, "north", shape="outer_left"))

    def protect_box(self, x0, y0, z0, x1, y1, z1):
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                for z in range(z0, z1 + 1):
                    self.protect.add((x, y, z))


# =====================================================================================================================
# The stepped pyramid ("Temple of the Sleeping Sun")
# =====================================================================================================================

def build_pyramid():
    """A Mesoamerican-style stepped pyramid: four talud-tablero tiers, a monumental stairway with balustrades, a
    three-door temple with a roof comb crowned by a glowing sun disc, and - like Palenque's Temple of the
    Inscriptions - a hidden switchback stair from the sanctuary down to a corbel-vaulted burial chamber."""
    W, H, D, G = 27, 27, 31, 3
    s = Ruin("venusian_pyramid", (W, H, D), seed=4401, ground=G)
    cx, cz = 13, 17
    rnd = s.rnd
    # foundation and plaza
    s.fill(0, 0, 4, W - 1, G - 1, D - 1, S_BRICK)
    s.fill(5, 0, 0, 21, G - 1, 3, S_BRICK)
    s.fill(0, G, 4, W - 1, G, D - 1, S_CARVED)
    s.fill(5, G, 0, 21, G, 3, S_CARVED)
    for x in range(W):          # a ring of temple bricks frames the plaza
        for z in (4, D - 1):
            s.set(x, G, z, S_BRICK)
    for z in range(4, D):
        s.set(0, G, z, S_BRICK)
        s.set(W - 1, G, z, S_BRICK)
    # tiers: half sizes 12, 10, 8, 6, three blocks high each
    tops = []
    for i, h in enumerate((12, 10, 8, 6)):
        y0 = G + 1 + 3 * i
        x0, x1, z0, z1 = cx - h, cx + h, cz - h, cz + h
        s.fill(x0, y0, z0, x1, y0 + 2, z1, S_BRICK)
        s.perimeter_stairs(y0, x0, z0, x1, z1, BSTAIRS)          # talud
        for x in range(x0, x1 + 1):                               # tablero frieze and cornice
            for z in (z0, z1):
                s.set(x, y0 + 1, z, glyph(x // 2) if (x - x0) % 4 == 2 else S_BRICK)
                s.set(x, y0 + 2, z, S_CARVED)
        for z in range(z0, z1 + 1):
            for x in (x0, x1):
                s.set(x, y0 + 1, z, glyph(z // 2 + 1) if (z - z0) % 4 == 2 else S_BRICK)
                s.set(x, y0 + 2, z, S_CARVED)
        for x, z in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)):
            s.set(x, y0 + 1, z, S_CARVED)
        tops.append(y0 + 2)
    top = tops[-1]                                                # y of the summit platform blocks (15)
    # the grand stairway (north face), 7 wide, with sloping balustrades
    for k in range(top - G):
        y, z = G + 1 + k, k
        for x in range(cx - 3, cx + 4):
            s.fill(x, G, z, x, y - 1, z, S_BRICK)
            s.set(x, y, z, stairs(CSTAIRS, "south"))
            s.protect.add((x, y, z))
            s.protect.add((x, y + 1, z))
            s.protect.add((x, y + 2, z))
        for x in (cx - 4, cx + 4):
            s.fill(x, G, z, x, y, z, S_CARVED)
            s.set(x, y + 1, z, stairs(CSTAIRS, "south"))
    # two serpent-head newels at the foot of the stair
    for x in (cx - 4, cx + 4):
        s.set(x, G + 1, 0, S_CARVED)
        s.set(x, G + 2, 0, glyph(1))
        s.set(x, G + 3, 0, slab(CSLAB))
    # ---------------------------------------------------------------- the summit temple
    ty = top + 1                                                  # temple floor walking level (16)
    tx0, tx1, tz0, tz1 = cx - 4, cx + 4, 13, 21
    s.fill(tx0, ty, tz0, tx1, ty + 4, tz1, S_BRICK)
    s.fill(tx0 + 1, ty, tz0 + 1, tx1 - 1, ty + 4, tz1 - 1, S_AIR)
    for x in range(tx0, tx1 + 1):
        for z in (tz0, tz1):
            s.set(x, ty + 4, z, S_INLAID)
    for z in range(tz0, tz1 + 1):
        for x in (tx0, tx1):
            s.set(x, ty + 4, z, S_INLAID)
    for x, z in ((tx0, tz0), (tx1, tz0), (tx0, tz1), (tx1, tz1)):
        s.fill(x, ty, z, x, ty + 3, z, S_CARVED)
    # facade: three doorways between pillars, a carved lintel
    for x in range(tx0 + 1, tx1):
        s.set(x, ty + 3, tz0, S_CARVED)
        if x in (cx - 2, cx, cx + 2):
            s.fill(x, ty, tz0, x, ty + 2, tz0, S_AIR)
            s.protect_box(x, ty, tz0, x, ty + 2, tz0)
        else:
            s.fill(x, ty, tz0, x, ty + 2, tz0, S_PILLAR)
    s.set(cx, ty + 3, tz0, glyph(3))
    # corbel vault inside and the flat roof
    for x in range(tx0 + 1, tx1):
        for z in range(tz0 + 1, tz1):
            if x in (tx0 + 1, tx1 - 1) or z in (tz0 + 1, tz1 - 1):
                s.set(x, ty + 4, z, S_CARVED)
    s.fill(tx0, ty + 5, tz0, tx1, ty + 5, tz1, S_BRICK)
    for x in range(tx0, tx1 + 1):
        for z in (tz0, tz1):
            s.set(x, ty + 5, z, slab(CSLAB))
    for z in range(tz0, tz1 + 1):
        for x in (tx0, tx1):
            s.set(x, ty + 5, z, slab(CSLAB))
    # inner wall between the portico and the sanctuary
    s.fill(tx0 + 1, ty, 16, tx1 - 1, ty + 3, 16, S_BRICK)
    s.fill(cx, ty, 16, cx, ty + 2, 16, S_AIR)
    s.protect_box(cx, ty, 16, cx, ty + 2, 16)
    for x in (cx - 2, cx + 2):
        s.set(x, ty + 1, 16, glyph(x))
    # roof comb: an openwork crest with the sun disc facing the stairway
    rz = 17
    for x in range(tx0 + 1, tx1):
        s.set(x, ty + 6, rz, S_CARVED)
        s.set(x, ty + 7, rz, S_CARVED if x % 2 == 1 else S_AIR)
    for x in range(cx - 2, cx + 3):
        s.set(x, ty + 8, rz, S_CARVED)
    s.set(cx, ty + 8, rz, faced(SUN, "north"))
    s.set(cx - 1, ty + 9, rz, slab(CSLAB))
    s.set(cx, ty + 9, rz, S_CARVED)
    s.set(cx + 1, ty + 9, rz, slab(CSLAB))
    s.set(cx, ty + 10, rz, slab(CSLAB))
    s.protect.add((cx, ty + 8, rz))
    # sanctuary furnishings
    s.set(cx, ty, 18, S_ALTAR)
    s.set(cx, ty + 2, tz1, faced(SUN, "north"))
    s.set(cx - 2, ty + 1, tz1, glyph(0))
    s.set(cx + 2, ty + 1, tz1, glyph(2))
    s.set(tx0 + 1, ty, 17, S_URN)
    s.set(tx1 - 1, ty, 17, chest_state("west", "chests/venusian_pyramid_temple"))
    s.set(tx0 + 1, ty, tz0 + 1, S_URN)
    s.set(tx1 - 1, ty, tz0 + 2, faced(STELE, "west"))
    s.set(tx0 + 1, ty, tz0 + 2, barrel_state("chests/venusian_expedition_cache"))
    s.protect_box(cx, ty, 17, cx, ty + 2, 18)
    # ---------------------------------------------------------------- the hidden stair and the tomb
    # flight A: from the sanctuary floor westwards down (z = 19..20), step at (x, y = x)
    for x in range(10, 16):
        for z in (19, 20):
            s.set(x, x, z, stairs(BSTAIRS, "east"))
            s.fill(x, x + 1, z, x, x + 3, z, S_AIR)
            s.protect_box(x, x, z, x, x + 3, z)
    s.set(11, ty, 19, slab(CSLAB))   # the displaced lid of the shaft
    s.set(11, ty, 20, slab(CSLAB))
    # landing
    s.fill(8, 9, 19, 9, 9, 23, S_BRICK)
    s.fill(8, 10, 19, 9, 12, 23, S_AIR)
    s.protect_box(8, 10, 19, 9, 12, 23)
    s.set(7, 11, 21, faced(SUN, "east"))           # a glowing relief lights the turn of the stair
    # flight B: eastwards down (z = 22..23)
    for x in range(10, 15):
        y = 18 - x
        for z in (22, 23):
            s.set(x, y, z, stairs(BSTAIRS, "west"))
            s.fill(x, y + 1, z, x, y + 3, z, S_AIR)
            s.protect_box(x, y, z, x, y + 3, z)
    # the burial chamber: x 15..19, z 13..23, walking level G+1, corbelled to y = G+6
    cy = G + 1
    s.fill(15, cy, 13, 19, cy + 3, 23, S_AIR)
    s.fill(16, cy + 4, 13, 18, cy + 4, 23, S_AIR)
    s.fill(17, cy + 5, 13, 17, cy + 5, 23, S_AIR)
    s.protect_box(15, cy, 13, 19, cy + 1, 23)
    for z in range(14, 23, 2):
        s.set(14, cy + 1, z, glyph(z // 2))
        s.set(20, cy + 1, z, glyph(z // 2 + 2))
    s.set(17, cy + 2, 12, faced(SUN, "south"))
    s.set(17, cy + 1, 12, S_INLAID)
    s.set(16, cy + 1, 12, S_INLAID)
    s.set(18, cy + 1, 12, S_INLAID)
    # sarcophagus with a carved lid, one lid slab pushed aside
    for x in (16, 17, 18):
        for z in range(16, 21):
            s.set(x, cy, z, S_CARVED if x == 17 else glyph(z))
            s.set(x, cy + 1, z, slab(CSLAB))
    s.set(17, cy + 1, 20, S_AIR)
    s.set(18, cy + 1, 20, S_AIR)
    s.set(19, cy, 20, slab(CSLAB))
    s.set(18, cy + 1, 20, ("minecraft:skeleton_skull", {"rotation": "8", "powered": "false"}, None))
    s.set(17, cy + 1, 20, ("minecraft:bone_block", {"axis": "z"}, None))
    # grave goods
    s.set(15, cy, 13, chest_state("east", "chests/venusian_pyramid_tomb"))
    s.set(19, cy, 13, chest_state("west", "chests/venusian_pyramid_tomb"))
    for p in ((15, cy, 15), (19, cy, 15), (19, cy, 18), (15, cy, 18), (19, cy, 22)):
        s.set(*p, S_URN)
    for p in ((16, cy, 14), (18, cy, 14), (16, cy, 22)):
        s.set(*p, ("minecraft:candle", {"candles": str(rnd.randint(1, 3)), "lit": "false", "waterlogged": "false"}, None))
    s.set(15, cy, 21, ("minecraft:skeleton_skull", {"rotation": "3", "powered": "false"}, None))
    # the dart trap at the chamber door
    s.set(16, cy, 23, ("minecraft:stone_pressure_plate", {"powered": "false"}, None))
    s.set(16, cy, 24, dispenser_state("north"))
    # ---------------------------------------------------------------- ruin it
    s.blob(25, G + 5, 29, 5.2)                   # the south-east corner has slumped
    s.blob(4, G + 9, 6, 2.6)
    s.blob(23, G + 3, 7, 2.2)
    s.blob(tx1, ty + 5, tz1 - 1, 2.4, ymin=ty + 3)   # part of the roof fell in
    s.blob(tx0 + 1, ty + 7, rz, 1.6, ymin=ty + 6)    # and a wing of the crest
    for k in range(top - G):                      # worn steps
        for x in range(cx - 3, cx + 4):
            r = rnd.random()
            if r < 0.07:
                s.b[(x, G + 1 + k, k)] = slab(CSLAB)
            elif r < 0.11:
                s.b[(x, G + 1 + k, k)] = stairs(BSTAIRS, "south")
    s.jag_tops(0.05, ymin=G + 2)
    s.mossify(0.55, turf=0.35)
    s.plants(0.35)
    s.wall_vines(0.16)
    s.hanging_vines(0.25, ymin=G + 2)
    s.cobwebs(0.35, [(15, cy, 13, 19, cy + 5, 23), (8, 10, 19, 9, 12, 23)])
    return s


# =====================================================================================================================
# Validation and NBT output
# =====================================================================================================================
BOOL = ("true", "false")
STAIR_SCHEMA = {"facing": HORIZ, "half": ("top", "bottom"), "waterlogged": BOOL,
                "shape": ("straight", "inner_left", "inner_right", "outer_left", "outer_right")}
VANILLA = {
    AIR: {}, "minecraft:structure_void": {}, "minecraft:cobweb": {}, "minecraft:gravel": {}, "minecraft:white_wool": {},
    "minecraft:moss_block": {}, "minecraft:moss_carpet": {}, "minecraft:flower_pot": {},
    "minecraft:suspicious_gravel": {"dusted": ("0", "1", "2", "3")},
    "minecraft:chest": {"facing": HORIZ, "type": ("single", "left", "right"), "waterlogged": BOOL},
    "minecraft:barrel": {"facing": HORIZ + ("up", "down"), "open": BOOL},
    "minecraft:dispenser": {"facing": HORIZ + ("up", "down"), "triggered": BOOL},
    "minecraft:stone_pressure_plate": {"powered": BOOL},
    "minecraft:vine": {d: BOOL for d in ("north", "east", "south", "west", "up")},
    "minecraft:skeleton_skull": {"rotation": tuple(str(i) for i in range(16)), "powered": BOOL},
    "minecraft:candle": {"candles": ("1", "2", "3", "4"), "lit": BOOL, "waterlogged": BOOL},
    "minecraft:bone_block": {"axis": ("x", "y", "z")},
    "minecraft:campfire": {"facing": HORIZ, "lit": BOOL, "signal_fire": BOOL, "waterlogged": BOOL},
    "minecraft:oak_fence": {d: BOOL for d in ("north", "east", "south", "west", "waterlogged")},
    "minecraft:jigsaw": {"orientation": tuple(f"{a}_{b}" for a, b in (
        ("down", "east"), ("down", "north"), ("down", "south"), ("down", "west"), ("up", "east"), ("up", "north"),
        ("up", "south"), ("up", "west"), ("west", "up"), ("east", "up"), ("north", "up"), ("south", "up")))},
    "minecraft:lantern": {"hanging": BOOL, "waterlogged": BOOL},
    "minecraft:white_carpet": {},
    "minecraft:ladder": {"facing": HORIZ, "waterlogged": BOOL},
}
_states_cache = {}


def mod_variants(short):
    if short not in _states_cache:
        path = os.path.join(ASSETS, "blockstates", short + ".json")
        if not os.path.exists(path):
            _states_cache[short] = None
        else:
            import json
            with open(path, encoding="utf-8") as fh:
                _states_cache[short] = json.load(fh).get("variants")
    return _states_cache[short]


MOD_SCHEMAS = {   # blocks with properties the blockstate file does not list
    R("venus_leaves"): {"distance": tuple(str(i) for i in range(1, 8)), "persistent": BOOL, "waterlogged": BOOL},
}


def validate(ruin):
    problems = set()
    for pos, (name, props, nbt) in ruin.b.items():
        if not ruin.inside(*pos):
            problems.add(f"{pos} outside the template")
        if name.startswith("minecraft:"):
            schema = VANILLA.get(name)
            if schema is None:
                problems.add(f"{name}: not in the vanilla schema table")
            elif set(props) != set(schema) or any(v not in schema[k] for k, v in props.items()):
                problems.add(f"{name}{props}: invalid for {schema}")
        else:
            if name in MOD_SCHEMAS:
                schema = MOD_SCHEMAS[name]
                if set(props) != set(schema) or any(v not in schema[k] for k, v in props.items()):
                    problems.add(f"{name}{props}: invalid for {schema}")
                continue
            short = name.split(":", 1)[1]
            variants = mod_variants(short)
            if variants is None:
                problems.add(f"{name}: no blockstate")
                continue
            if short.endswith("_stairs"):
                if set(props) != set(STAIR_SCHEMA) or any(v not in STAIR_SCHEMA[k] for k, v in props.items()):
                    problems.add(f"{name}{props}: bad stairs")
                continue
            if short.endswith("_slab"):
                if set(props) != {"type", "waterlogged"}:
                    problems.add(f"{name}{props}: bad slab")
                continue
            key = ",".join(f"{k}={v}" for k, v in sorted(props.items()))
            if key not in variants:
                problems.add(f"{name}[{key}]: no such variant")
    if problems:
        raise SystemExit(f"ruins.py: {ruin.name} has invalid blocks:\n  " + "\n  ".join(sorted(problems)[:60]))


def to_nbt(ruin):
    palette_index, palette, blocks = {}, List([], TAG_COMPOUND), List([], TAG_COMPOUND)
    for (x, y, z) in sorted(ruin.b, key=lambda c: (c[1], c[2], c[0])):
        name, props, nbt = ruin.b[(x, y, z)]
        key = (name, tuple(sorted(props.items())))
        if key not in palette_index:
            palette_index[key] = len(palette)
            entry = Compound({"Name": Str(name)})
            if props:
                entry["Properties"] = Compound({Str(k): Str(v) for k, v in sorted(props.items())})
            palette.append(entry)
        entry = Compound({"pos": List([Int(x), Int(y), Int(z)], TAG_INT), "state": Int(palette_index[key])})
        if nbt is not None:
            entry["nbt"] = nbt
        blocks.append(entry)
    return Compound({"DataVersion": Int(DATA_VERSION),
                     "size": List([Int(ruin.W), Int(ruin.H), Int(ruin.D)], TAG_INT),
                     "palette": palette, "blocks": blocks,
                     "entities": List(getattr(ruin, "entity_nbt", lambda: [])(), TAG_COMPOUND)})


def write_template(ruin, path):
    validate(ruin)
    root = to_nbt(ruin)
    file = os.path.join(DATA, "structure", *path.split("/")) + ".nbt"
    os.makedirs(os.path.dirname(file), exist_ok=True)
    with gzip.GzipFile(file, "wb", mtime=0) as fh:
        fh.write(nbt_bytes(root))
    with gzip.open(file, "rb") as fh:
        _, back = nbt_parse(fh.read())
    assert len(back["blocks"]) == len(root["blocks"]) and list(back["size"]) == [ruin.W, ruin.H, ruin.D]
    return len(root["blocks"])


# =====================================================================================================================
# Entry point
# =====================================================================================================================
TEMPLATES = {}     # template path -> builder, filled below


def build_all():
    return {path: fn() for path, fn in TEMPLATES.items()}


def generate():
    textures()
    block_models()
    block_loot()
    chest_loot()
    tags()
    recipes()
    total = 0
    for path, ruin in build_all().items():
        total += write_template(ruin, path)
    worldgen()
    print(f"ruins: generated {len(TEMPLATES)} templates, {total} blocks")
    import oinstein
    oinstein.generate()


# =====================================================================================================================
# The ziggurat ("House of the Seven Suns")
# =====================================================================================================================

def niched_terrace(s, x0, z0, x1, z1, ya, yb, seed):
    """A solid terrace whose walls are articulated by fluted pilasters and recessed niches (period 4), on a carved
    plinth, under a turquoise frieze and a carved cornice."""
    s.fill(x0, ya, z0, x1, yb, z1, S_BRICK)
    rnd = random.Random(seed)
    faces = [((x, z0), (0, 1), x - x0) for x in range(x0, x1 + 1)] + [((x, z1), (0, -1), x - x0) for x in range(x0, x1 + 1)] + \
            [((x0, z), (1, 0), z - z0) for z in range(z0, z1 + 1)] + [((x1, z), (-1, 0), z - z0) for z in range(z0, z1 + 1)]
    for (x, z), (ix, iz), off in faces:
        corner = x in (x0, x1) and z in (z0, z1)
        s.set(x, ya, z, S_CARVED)
        s.set(x, yb, z, S_CARVED)
        if yb - ya >= 4:
            s.set(x, yb - 1, z, S_INLAID)
        top = yb - (2 if yb - ya >= 4 else 1)
        if corner or off % 4 == 0:
            s.fill(x, ya + 1, z, x, top, z, S_PILLAR)
        else:
            s.fill(x, ya + 1, z, x, top, z, S_AIR)
            back = (x + ix, z + iz)
            for y in range(ya + 1, top + 1):
                s.set(back[0], y, back[1], glyph(rnd.randrange(4)) if rnd.random() < 0.08 else S_BRICK)


def stair_run(s, xs, z_of, y_of, n, facing, fill_to, protect=True, name=CSTAIRS, along="z"):
    """A straight flight: step k at (x, y_of(k), z_of(k)) for each x in xs (or swapped axes when along == 'x')."""
    for k in range(n):
        for w in xs:
            if along == "z":
                x, z = w, z_of(k)
            else:
                x, z = z_of(k), w
            y = y_of(k)
            s.fill(x, fill_to, z, x, y - 1, z, S_BRICK)
            s.set(x, y, z, stairs(name, facing))
            if protect:
                s.protect_box(x, y, z, x, y + 2, z)


def balustrade(s, x, z, y):
    s.fill(x, y - 1, z, x, y, z, S_CARVED)


def ruin_tree(s, x, y, z, height, rnd):
    """A small venus tree that took root on the ruin (persistent leaves)."""
    for k in range(height):
        s.set(x, y + k, z, st("venus_log", axis="y"))
    leaves = st("venus_leaves", distance=1, persistent=True, waterlogged=False)
    top = y + height
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            for dy in (-1, 0, 1):
                d = abs(dx) + abs(dz) + abs(dy) * 1.5
                if d <= 2.6 + rnd.random() * 0.8 and s.name_at(x + dx, top + dy, z + dz) in (None, AIR):
                    s.set(x + dx, top + dy, z + dz, leaves)
    s.set(x, top - 1, z, st("venus_log", axis="y"))


def expedition_camp(s, x, y, z):
    """The abandoned camp of an earlier expedition from Earth: a canvas tent, a supply barrel and a cold fire."""
    fence = lambda **kw: ("minecraft:oak_fence", {d: ("true" if kw.get(d) else "false")
                                                  for d in ("north", "east", "south", "west")} | {"waterlogged": "false"}, None)
    for dz in range(3):
        s.set(x, y, z + dz, st("minecraft:white_wool"))
        s.set(x + 2, y, z + dz, st("minecraft:white_wool"))
        s.set(x + 1, y + 1, z + dz, st("minecraft:white_wool"))
        s.set(x + 1, y, z + dz, S_AIR)
    s.set(x + 1, y, z + 1, ("minecraft:white_carpet", {}, None))
    s.set(x + 1, y, z + 2, barrel_state("chests/venusian_expedition_cache"))
    s.set(x + 3, y, z, fence())
    s.set(x + 1, y, z - 1, ("minecraft:campfire", {"facing": "north", "lit": "false", "signal_fire": "false",
                                                    "waterlogged": "false"}, None))
    s.protect_box(x, y, z - 1, x + 3, y + 1, z + 2)


def build_ziggurat():
    """A Mesopotamian-style ziggurat: three niched terraces, a monumental triple stairway converging on the first
    terrace, a ceremonial gate, hanging gardens, a summit shrine under a great sun disc, and inside the first
    terrace a pillared hall with a treasury and an archive. One corner has slumped, the hall roof has caved in, and
    an Earth expedition's camp was abandoned on the first terrace."""
    W, H, D, G = 45, 34, 41, 3
    s = Ruin("venusian_ziggurat", (W, H, D), seed=5507, ground=G)
    rnd = s.rnd
    cx = 22
    s.fill(0, 0, 0, W - 1, G - 1, D - 1, S_BRICK)
    s.fill(0, G, 0, W - 1, G, D - 1, S_CARVED)
    for x in range(0, W, 2):
        for z in range(0, 7, 3):
            s.set(x, G, z, S_BRICK)
    # terraces
    niched_terrace(s, 2, 8, 42, 38, G + 1, G + 8, 1)
    niched_terrace(s, 8, 14, 36, 34, G + 9, G + 14, 2)
    niched_terrace(s, 13, 20, 31, 30, G + 15, G + 19, 3)
    t1, t2, t3 = G + 8, G + 14, G + 19          # top block y of each terrace (11, 17, 22)
    # ---------------------------------------------------------------- the triple stairway
    stair_run(s, range(cx - 2, cx + 3), lambda k: k, lambda k: G + 1 + k, t1 - G, "south", G)
    for k in range(t1 - G):
        for x in (cx - 3, cx + 3):
            balustrade(s, x, k, G + 2 + k)
    for x in (cx - 3, cx + 3):
        s.fill(x, G + 1, 0, x, G + 2, 0, S_CARVED)
        s.set(x, G + 3, 0, glyph(1))
    # lateral stairs along the facade, rising towards the centre
    stair_run(s, (6, 7), lambda k: 8 + k, lambda k: G + 1 + k, t1 - G, "east", G, along="x")
    stair_run(s, (6, 7), lambda k: 36 - k, lambda k: G + 1 + k, t1 - G, "west", G, along="x")
    for k in range(t1 - G):
        balustrade(s, 8 + k, 5, G + 2 + k)
        balustrade(s, 36 - k, 5, G + 2 + k)
    for x0, x1 in ((16, 18), (26, 28)):          # landings
        s.fill(x0, G, 5, x1, t1, 7, S_BRICK)
        s.fill(x0, t1, 5, x1, t1, 7, S_CARVED)
        s.protect_box(x0, t1 + 1, 5, x1, t1 + 2, 7)
        for x in range(x0, x1 + 1):
            s.set(x, t1 + 1, 5, slab(CSLAB))
    # second and third flights
    stair_run(s, range(cx - 2, cx + 3), lambda k: 9 + k, lambda k: t1 + 1 + k, t2 - t1, "south", t1)
    for k in range(t2 - t1):
        for x in (cx - 3, cx + 3):
            balustrade(s, x, 9 + k, t1 + 2 + k)
    stair_run(s, range(cx - 1, cx + 2), lambda k: 16 + k, lambda k: t2 + 1 + k, t3 - t2, "south", t2)
    for k in range(t3 - t2):
        for x in (cx - 2, cx + 2):
            balustrade(s, x, 16 + k, t2 + 2 + k)
    # the gate of the second terrace
    for x in (cx - 4, cx + 4):
        s.fill(x, t2 + 1, 15, x, t2 + 4, 15, S_PILLAR)
        s.set(x, t2 + 5, 15, S_CARVED)
    for x in range(cx - 4, cx + 5):
        s.set(x, t2 + 5, 15, S_CARVED if abs(x - cx) > 1 else S_INLAID)
    s.set(cx, t2 + 6, 15, faced(SUN, "north"))
    s.set(cx - 1, t2 + 6, 15, slab(CSLAB))
    s.set(cx + 1, t2 + 6, 15, slab(CSLAB))
    s.protect_box(cx - 3, t2 + 1, 15, cx + 3, t2 + 3, 15)
    # ---------------------------------------------------------------- the summit shrine
    sy = t3 + 1
    x0, x1, z0, z1 = 16, 28, 22, 28
    s.fill(x0, sy, z0, x1, sy + 4, z1, S_BRICK)
    s.fill(x0 + 1, sy, z0 + 1, x1 - 1, sy + 3, z1 - 1, S_AIR)
    s.fill(x0 + 2, sy + 4, z0 + 2, x1 - 2, sy + 4, z1 - 2, S_AIR)
    for x in range(x0, x1 + 1):
        for z in (z0, z1):
            s.set(x, sy + 3, z, S_INLAID)
        if (x - x0) % 3 == 0:
            for z in (z0, z1):
                s.fill(x, sy, z, x, sy + 2, z, S_PILLAR)
    for z in range(z0, z1 + 1):
        for x in (x0, x1):
            s.set(x, sy + 3, z, S_INLAID)
    s.fill(x0, sy + 5, z0, x1, sy + 5, z1, S_BRICK)
    for x in range(x0, x1 + 1):         # crenellated roof edge (almenas)
        for z in (z0, z1):
            s.set(x, sy + 6, z, S_CARVED if x % 2 == 0 else slab(CSLAB))
    for z in range(z0, z1 + 1):
        for x in (x0, x1):
            s.set(x, sy + 6, z, S_CARVED if z % 2 == 0 else slab(CSLAB))
    s.fill(cx - 1, sy, z0, cx + 1, sy + 2, z0, S_AIR)
    s.protect_box(cx - 1, sy, z0, cx + 1, sy + 2, z0 + 1)
    s.fill(cx - 2, sy + 3, z0, cx + 2, sy + 3, z0, S_CARVED)
    # the great sun disc above the door
    s.fill(cx - 1, sy + 6, z0, cx + 1, sy + 8, z0, S_CARVED)
    s.set(cx, sy + 7, z0, faced(SUN, "north"))
    s.set(cx, sy + 9, z0, slab(CSLAB))
    s.set(cx, sy + 2, z1 - 1, S_CARVED)
    s.set(cx, sy + 2, z1, faced(SUN, "north"))
    s.set(cx, sy + 2, z1 - 1, S_AIR)
    s.set(cx, sy, z1 - 2, S_ALTAR)
    for x in (cx - 3, cx + 3):
        s.set(x, sy, z1 - 1, faced(STELE, "north"))
    s.set(x0 + 1, sy, z1 - 1, chest_state("east", "chests/venusian_ziggurat_treasury"))
    s.set(x1 - 1, sy, z1 - 1, S_URN)
    s.set(x1 - 1, sy, z0 + 1, S_URN)
    s.set(x0 + 1, sy, z0 + 1, S_URN)
    # ---------------------------------------------------------------- inside the first terrace
    hy = G + 1
    s.fill(14, hy, 18, 30, hy + 5, 30, S_AIR)                        # the pillared hall
    s.fill(15, hy + 6, 19, 29, hy + 6, 29, S_AIR)
    s.protect_box(14, hy, 18, 30, hy + 1, 30)
    for x in (18, 26):
        for z in (20, 24, 28):
            s.fill(x, hy, z, x, hy + 5, z, S_PILLAR)
            s.set(x, hy + 6, z, S_CARVED)
    for z in range(19, 30, 3):
        s.set(13, hy + 2, z, glyph(z))
        s.set(31, hy + 2, z, glyph(z + 1))
    s.set(13, hy + 3, 24, faced(SUN, "east"))
    s.set(31, hy + 3, 20, faced(SUN, "west"))
    s.set(31, hy + 3, 28, faced(SUN, "west"))
    s.set(cx, hy, 24, S_ALTAR)
    for x in (cx - 1, cx + 1):
        s.set(x, hy, 24, faced(STELE, "east" if x > cx else "west"))
    # east entrance corridor (open) and west corridor (choked with rubble)
    s.fill(31, hy, 23, 42, hy + 3, 25, S_AIR)
    s.protect_box(31, hy, 23, 42, hy + 2, 25)
    s.fill(42, hy + 4, 22, 42, hy + 4, 26, S_CARVED)
    s.fill(2, hy, 23, 13, hy + 3, 25, S_AIR)
    for x in range(2, 9):
        for z in range(23, 26):
            for y in range(hy, hy + 1 + (9 - x) // 3):
                s.set(x, y, z, rnd.choice((S_COBBLE, S_CRACKED, st("minecraft:gravel"), S_BRICK)))
    # treasury (north) and archive (south)
    s.fill(19, hy, 12, 25, hy + 3, 16, S_AIR)
    s.fill(cx, hy, 17, cx, hy + 2, 17, S_AIR)
    s.protect_box(cx, hy, 16, cx, hy + 2, 18)
    s.set(19, hy, 12, chest_state("east", "chests/venusian_ziggurat_treasury"))
    s.set(25, hy, 12, chest_state("west", "chests/venusian_pyramid_tomb"))
    for p in ((20, hy, 12), (24, hy, 12), (19, hy, 16), (25, hy, 16), (19, hy, 14)):
        s.set(*p, S_URN)
    s.set(cx, hy + 2, 11, faced(SUN, "south"))
    s.set(cx, hy + 1, 11, S_INLAID)
    s.fill(19, hy, 32, 25, hy + 3, 36, S_AIR)
    s.fill(cx, hy, 31, cx, hy + 2, 31, S_AIR)
    s.protect_box(cx, hy, 30, cx, hy + 2, 32)
    for x in range(19, 26):
        s.set(x, hy + 1, 37, glyph(x))
        s.set(x, hy + 2, 37, glyph(x + 2))
    for z in range(32, 37):
        s.set(18, hy + 1, z, glyph(z))
        s.set(26, hy + 1, z, glyph(z + 1))
    for x in (20, 24):
        for z in (33, 35):
            s.set(x, hy, z, faced(STELE, "east"))
    s.set(cx, hy, 36, chest_state("north", "chests/venusian_pyramid_temple"))
    s.set(cx, hy + 2, 37, faced(SUN, "north"))
    # ---------------------------------------------------------------- gardens, camp, ruin
    for (bx0, bz0, bx1, bz1) in ((9, 16, 11, 32), (33, 16, 35, 32), (14, 32, 30, 33)):
        s.fill(bx0, t2, bz0, bx1, t2, bz1, S_SOIL)
    expedition_camp(s, 37, t1 + 1, 30)
    s.blob(34, t2 + 3, 17, 4.6)                  # the north-east corner of the upper terraces slumped
    s.blob(4, G + 6, 37, 4.4)
    s.blob(41, G + 4, 10, 2.6)
    s.blob(26, hy + 6, 27, 2.8, ymin=hy + 5)     # the hall roof caved in
    ruin_tree(s, 10, t2 + 1, 27, 4, rnd)
    ruin_tree(s, 33, t2 + 1, 23, 3, rnd)
    ruin_tree(s, 4, t1 + 1, 12, 5, rnd)
    for x in range(24, 29):
        for z in range(25, 30):
            if abs(x - 26) + abs(z - 27) <= 2:
                s.set(x, hy, z, S_SOIL if (x + z) % 2 else S_MOSS)
    s.tall_plant(26, hy + 1, 27, "venus_tree_fern")
    s.set(25, hy + 1, 27, st("venus_horsetail"))
    s.set(27, hy + 1, 26, st("venus_sedge"))
    for k in range(t1 - G):
        for x in range(cx - 2, cx + 3):
            if rnd.random() < 0.08:
                s.b[(x, G + 1 + k, k)] = slab(CSLAB)
    s.jag_tops(0.06, ymin=G + 3)
    s.mossify(0.5, turf=0.3)
    s.plants(0.3)
    s.wall_vines(0.12)
    s.hanging_vines(0.18, ymin=G + 2)
    s.cobwebs(0.25, [(19, hy, 12, 25, hy + 3, 16), (19, hy, 32, 25, hy + 3, 36), (14, hy, 18, 30, hy + 6, 30)])
    return s


# =====================================================================================================================
# Jungle shrines (three variants, one buried foundation layer: G = 1)
# =====================================================================================================================

def build_shrine_temple():
    """A small stepped shrine: a cella with a pillared portico on a two-step platform; altar and sun disc inside."""
    s = Ruin("venusian_shrine_temple", (9, 9, 11), seed=6101, ground=1)
    G = 1
    s.fill(0, 0, 0, 8, 0, 10, S_BRICK)
    s.fill(0, G, 1, 8, G, 10, S_CARVED)
    s.fill(1, G + 1, 3, 7, G + 1, 10, S_BRICK)
    s.perimeter_stairs(G + 1, 1, 3, 7, 10, BSTAIRS)
    for x in range(3, 6):
        s.set(x, G, 0, stairs(CSTAIRS, "south"))
        s.set(x, G + 1, 2, stairs(CSTAIRS, "south"))
        s.set(x, G + 1, 3, S_CARVED)
        s.protect_box(x, G + 1, 0, x, G + 4, 3)
    cy = G + 2
    s.fill(2, cy, 5, 6, cy + 2, 9, S_BRICK)
    s.fill(3, cy, 6, 5, cy + 2, 8, S_AIR)
    s.fill(4, cy, 5, 4, cy + 1, 5, S_AIR)
    s.protect_box(4, cy, 4, 4, cy + 1, 6)
    for x in (2, 6):
        s.fill(x, cy, 4, x, cy + 2, 4, S_PILLAR)
    s.fill(2, cy + 3, 4, 6, cy + 3, 9, S_BRICK)
    for x in range(2, 7):
        s.set(x, cy + 3, 4, S_INLAID)
    for z in range(4, 10):
        s.set(2, cy + 4, z, slab(CSLAB))
        s.set(6, cy + 4, z, slab(CSLAB))
    s.set(4, cy + 4, 4, faced(SUN, "north"))
    s.set(4, cy + 4, 5, S_CARVED)
    s.set(4, cy + 1, 9, faced(SUN, "north"))
    s.set(4, cy + 2, 5, glyph(3))
    s.set(4, cy, 8, S_ALTAR)
    s.set(3, cy, 6, S_URN)
    s.set(5, cy, 8, chest_state("west", "chests/venusian_shrine"))
    s.set(3, cy, 8, st("minecraft:candle", candles=2, lit=False, waterlogged=False))
    s.blob(6, cy + 3, 9, 1.8, ymin=cy + 2)
    s.jag_tops(0.08, ymin=cy + 3)
    s.mossify(0.6, turf=0.4)
    s.plants(0.5)
    s.wall_vines(0.3)
    s.hanging_vines(0.35)
    s.cobwebs(0.3, [(3, cy, 6, 5, cy + 2, 8)])
    return s


def build_shrine_steles():
    """A ring of carved stelae around a round dais and altar; a strongbox lies buried beneath the altar."""
    s = Ruin("venusian_shrine_steles", (13, 6, 13), seed=6202, ground=1)
    G, c = 1, 6
    rnd = s.rnd
    for x in range(13):
        for z in range(13):
            d = math.hypot(x - c, z - c)
            if d <= 6.2:
                s.set(x, 0, z, S_BRICK)
                s.set(x, G, z, S_CARVED if d < 2.6 or (d > 4.4 and d < 5.6) else
                      (S_MOSS if rnd.random() < 0.45 else S_BRICK))
    for x in range(c - 1, c + 2):
        for z in range(c - 1, c + 2):
            s.set(x, G + 1, z, S_CARVED)
    s.perimeter_stairs(G + 1, c - 2, c - 2, c + 2, c + 2, CSTAIRS)
    s.fill(c - 1, G + 1, c - 1, c + 1, G + 1, c + 1, S_CARVED)
    s.set(c, G + 2, c, S_ALTAR)
    s.set(c, 0, c, chest_state("north", "chests/venusian_shrine"))
    s.protect.add((c, 0, c))
    for i in range(8):
        a = i * math.pi / 4
        x, z = round(c + 5 * math.sin(a)), round(c - 5 * math.cos(a))
        facing = min(DIRS, key=lambda d: (x + DIRS[d][0] - c) ** 2 + (z + DIRS[d][1] - c) ** 2)
        s.set(x, G, z, S_CARVED)
        if i in (3, 6):          # toppled
            s.set(x, G + 1, z, slab(CSLAB))
            s.set(x + (1 if x < c else -1), G + 1, z, slab(CSLAB))
            continue
        s.set(x, G + 1, z, faced(STELE, facing))
        if i % 2 == 0:
            s.set(x, G + 2, z, faced(STELE, facing))
            s.set(x, G + 3, z, slab(CSLAB))
    s.set(c - 3, G + 1, c + 3, S_URN)
    s.set(c + 3, G + 1, c - 2, S_URN)
    s.mossify(0.5, turf=0.3)
    s.plants(0.55)
    return s


def build_shrine_head():
    """A colossal carved head, half sunk into the jungle floor; its open mouth leads into a tiny offering chamber."""
    s = Ruin("venusian_shrine_head", (9, 11, 9), seed=6303, ground=1)
    G = 1
    s.fill(0, 0, 0, 8, G, 8, S_CARVED)
    for x in range(9):
        for z in range(9):
            if (x in (0, 8) or z in (0, 8)) and s.rnd.random() < 0.6:
                s.set(x, G, z, S_MOSS)
    x0, z0 = 1, 2                     # head occupies x 1..7, z 2..7, y G+1..G+7
    for x in range(7):
        for z in range(6):
            for y in range(7):
                corner = (x in (0, 6)) + (z in (0, 5)) + (y == 6)
                if corner >= 2 and not (y < 6 and z == 0):
                    continue
                s.set(x0 + x, G + 1 + y, z0 + z, S_CARVED)
    fy = G + 1
    face = [  # rows from the top (y = fy+6) to the chin (y = fy), columns x 0..6, on the face plane z = z0
        "BIIIIIB",
        "CCCgCCC",
        "CeECEeC",
        "CCCNCCC",
        "CCLMLCC",
        "CCLMLCC",
        ".CCCCC.",
    ]
    for row, line_ in enumerate(face):
        y = fy + 6 - row
        for x, ch in enumerate(line_):
            p = (x0 + x, y, z0)
            if ch == ".":
                s.b.pop(p, None)
            elif ch == "B":
                s.set(*p, S_INLAID)
            elif ch == "I":
                s.set(*p, S_INLAID)
            elif ch == "g":
                s.set(*p, glyph(0))
            elif ch == "e":
                s.set(*p, S_AIR)
                s.set(p[0], y, z0 + 1, S_INLAID)
            elif ch == "E":
                s.set(*p, stairs(CSTAIRS, "south", half="top"))
            elif ch == "N":
                s.set(*p, S_CARVED)
                s.set(p[0], y, z0 - 1, stairs(CSTAIRS, "north"))
                s.set(p[0], y + 1, z0 - 1, slab(CSLAB, "top"))
            elif ch == "L":
                s.set(*p, stairs(CSTAIRS, "north", half="top" if row == 4 else "bottom"))
            elif ch == "M":
                s.set(*p, S_AIR)
    # ear spools
    for x in (x0 - 1, x0 + 7):
        s.set(x, fy + 3, z0 + 2, faced(SUN, "west" if x < x0 else "east"))
        s.set(x, fy + 2, z0 + 2, S_CARVED)
    # the offering chamber behind the mouth
    s.fill(x0 + 2, fy, z0 + 1, x0 + 4, fy + 2, z0 + 3, S_AIR)
    s.set(x0 + 3, fy, z0 + 1, S_AIR)
    s.protect_box(x0 + 3, fy, z0, x0 + 3, fy + 1, z0 + 1)
    s.set(x0 + 3, fy, z0 + 3, chest_state("north", "chests/venusian_shrine"))
    s.set(x0 + 2, fy, z0 + 3, S_URN)
    s.set(x0 + 4, fy, z0 + 2, st("minecraft:candle", candles=3, lit=False, waterlogged=False))
    s.set(x0 + 3, fy + 2, z0 + 4, faced(SUN, "north"))
    # moss cap and a fern sprouting from the crown
    for x in range(x0 + 1, x0 + 6):
        for z in range(z0 + 1, z0 + 5):
            if s.name_at(x, fy + 6, z) == R(CARVED) and s.rnd.random() < 0.7:
                s.set(x, fy + 6, z, S_MOSS)
    s.set(x0 + 3, fy + 6, z0 + 3, S_SOIL)
    s.tall_plant(x0 + 3, fy + 7, z0 + 3, "venus_tree_fern")
    s.mossify(0.5)
    s.plants(0.5)
    s.wall_vines(0.35, max_len=5)
    return s


# =====================================================================================================================
# The abandoned village (jigsaw): a plaza, terrain-following streets and ruined houses
# =====================================================================================================================
VILLAGE = "venusian_village"
STREET = f"{MOD}:venusian_street"
LOT = f"{MOD}:venusian_lot"
HOUSE = f"{MOD}:venusian_house"
POOL_STREETS = f"{MOD}:{VILLAGE}/streets"
POOL_ENDS = f"{MOD}:{VILLAGE}/street_ends"
POOL_HOUSES = f"{MOD}:{VILLAGE}/houses"


def street_jigsaw(facing):
    return jigsaw_state(facing, STREET, STREET, POOL_STREETS)


def lot_jigsaw(facing):
    return jigsaw_state(facing, LOT, HOUSE, POOL_HOUSES)


def build_plaza():
    """The village square: a stepped dais with an altar, four stelae, broken colonnade, urns; streets leave on
    all four sides."""
    N, c = 21, 10
    s = Ruin(f"{VILLAGE}_plaza", (N, 6, N), seed=7101, ground=0)
    rnd = s.rnd
    for x in range(N):
        for z in range(N):
            d = max(abs(x - c), abs(z - c))
            r = rnd.random()
            if d == 10 and r < 0.35:
                continue
            s.set(x, 0, z, S_BRICK if d in (3, 7) else S_MOSS if r < 0.18 else S_CARVED)
    s.fill(c - 2, 1, c - 2, c + 2, 1, c + 2, S_CARVED)
    s.perimeter_stairs(1, c - 2, c - 2, c + 2, c + 2, CSTAIRS)
    s.fill(c - 1, 1, c - 1, c + 1, 1, c + 1, S_CARVED)
    s.set(c, 2, c, S_ALTAR)
    for (x, z, f) in ((c, c - 5, "north"), (c, c + 5, "south"), (c - 5, c, "west"), (c + 5, c, "east")):
        s.set(x, 1, z, faced(STELE, f))
        s.set(x, 2, z, faced(STELE, f))
    for i, (x, z) in enumerate(((3, 3), (17, 3), (3, 17), (17, 17), (3, 10), (17, 10), (10, 3), (10, 17))):
        if (x, z) in ((10, 3), (10, 17), (3, 10), (17, 10)):
            continue
        h = (4, 2, 3, 1)[i % 4]
        s.fill(x, 1, z, x, h, z, S_PILLAR)
        s.set(x, h + 1, z, slab(CSLAB))
        s.set(x + 1, 1, z + (1 if z < c else -1), slab(CSLAB))
    for (x, z) in ((6, 13), (14, 7), (13, 14)):
        s.set(x, 1, z, S_URN)
    for d in ("north", "south", "west", "east"):
        dx, dz = DIRS[d]
        x, z = c + dx * c, c + dz * c
        s.set(x, 0, z, S_CARVED)
        s.set(x, 1, z, street_jigsaw(d))
        s.protect.add((x, 1, z))
    s.mossify(0.5, turf=0.25)
    s.plants(0.3, tall=0.2)
    return s


def street_surface(s, rnd):
    for (x, y, z), st_ in list(s.b.items()):
        if y == 0:
            r = rnd.random()
            s.b[(x, y, z)] = (S_CARVED if r < 0.5 else S_BRICK if r < 0.7 else S_CRACKED if r < 0.8 else
                              S_MOSS if r < 0.93 else S_COBBLE)


def build_street(kind):
    """Terrain-following street pieces, 5 wide; the outer columns are kerbstones."""
    sizes = {"long": (5, 13), "short": (5, 7), "crossing": (5, 5), "turn": (5, 5), "tee": (5, 5), "end": (5, 3),
             "end_stele": (5, 4)}
    w, d = sizes[kind]
    s = Ruin(f"{VILLAGE}_street_{kind}", (w, 3 if kind == "end_stele" else 2, d), seed=7200 + len(kind) * 7 + d, ground=0)
    rnd = s.rnd
    s.fill(0, 0, 0, w - 1, 0, d - 1, S_CARVED)
    street_surface(s, rnd)
    jig = []
    if kind in ("long", "short"):
        jig += [(2, 0, "north"), (2, d - 1, "south")]
        lots = (3, 9) if kind == "long" else (3,)
        for z in lots:
            jig += [(0, z, "west", "lot"), (4, z, "east", "lot")]
    elif kind == "crossing":
        jig += [(2, 0, "north"), (2, 4, "south"), (0, 2, "west"), (4, 2, "east")]
    elif kind == "turn":
        jig += [(2, 0, "north"), (4, 2, "east")]
    elif kind == "tee":
        jig += [(2, 0, "north"), (0, 2, "west"), (4, 2, "east")]
    else:
        jig += [(2, 0, "north")]
        if kind == "end":
            s.set(1, 1, 2, slab(CSLAB))
            s.set(3, 1, 1, S_URN if rnd.random() < 0.5 else slab(BSLAB))
        else:
            s.set(2, 0, 3, S_CARVED)
            s.set(2, 1, 3, faced(STELE, "north"))
            s.set(2, 2, 3, slab(CSLAB))
    for j in jig:
        x, z, f = j[0], j[1], j[2]
        s.set(x, 1, z, lot_jigsaw(f) if len(j) > 3 else street_jigsaw(f))
    return s


def house_jigsaw(s, x):
    s.set(x, 1, 0, jigsaw_state("north", HOUSE, LOT, "minecraft:empty"))
    s.protect_box(x, 1, 0, x, 2, 1)


def shell(s, x0, z0, x1, z1, h, floor=S_CARVED, wall=S_BRICK):
    s.fill(x0, 0, z0, x1, 0, z1, floor)
    for y in range(1, h + 1):
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                edge = x in (x0, x1) or z in (z0, z1)
                corner = x in (x0, x1) and z in (z0, z1)
                s.set(x, y, z, (S_CARVED if corner else wall) if edge else S_AIR)
    for x in range(x0, x1 + 1):
        for z in (z0, z1):
            s.set(x, h + 1, z, slab(CSLAB))
    for z in range(z0, z1 + 1):
        for x in (x0, x1):
            s.set(x, h + 1, z, slab(CSLAB))


def door(s, x, z, h=2):
    s.fill(x, 1, z, x, h, z, S_AIR)
    s.set(x, h + 1, z, S_CARVED)
    s.protect_box(x, 1, z, x, h, z)


def finish_house(s, prob_moss=0.5):
    s.erode_columns(0.8, 3)
    s.jag_tops(0.12, ymin=2)
    s.mossify(prob_moss, turf=0.3)
    s.plants(0.35)
    s.wall_vines(0.25, max_len=4)
    s.hanging_vines(0.2, ymin=2, max_len=2)


def build_house(kind):
    rnd = random.Random(7300 + len(kind))
    if kind == "hut":
        s = Ruin(f"{VILLAGE}_house_hut", (7, 7, 8), seed=7301)
        s.fill(2, 0, 0, 4, 0, 0, S_CARVED)
        shell(s, 0, 1, 6, 7, 4)
        door(s, 3, 1)
        for z in (4,):
            s.set(0, 2, z, S_AIR)
            s.set(6, 2, z, S_AIR)
        for x in range(1, 6):            # corbelled roof, mostly fallen
            for z in range(2, 7):
                if x in (1, 5) or z in (2, 6):
                    s.set(x, 5, z, slab(BSLAB))
        s.set(4, 1, 5, ("minecraft:campfire", {"facing": "south", "lit": "false", "signal_fire": "false",
                                               "waterlogged": "false"}, None))
        s.set(1, 1, 6, S_URN)
        s.set(5, 1, 2, slab(CSLAB))
        s.set(1, 1, 2, st("minecraft:gravel"))
        s.blob(6, 4, 7, 2.2, ymin=2)
        house_jigsaw(s, 3)
    elif kind == "longhouse":
        s = Ruin(f"{VILLAGE}_house_longhouse", (11, 7, 9), seed=7302)
        s.fill(4, 0, 0, 6, 0, 0, S_CARVED)
        shell(s, 0, 1, 10, 8, 4)
        s.fill(5, 1, 4, 5, 4, 7, S_BRICK)          # the partition behind a small vestibule
        door(s, 5, 1)
        door(s, 8, 1)
        s.set(5, 2, 4, glyph(2))
        s.set(9, 1, 7, chest_state("west", "chests/venusian_village"))
        s.set(9, 1, 2, S_URN)
        s.set(6, 1, 7, S_URN)
        s.set(6, 2, 8, faced(SUN, "north"))
        for x in range(1, 5):
            for z in range(2, 8):
                if rnd.random() < 0.3:
                    s.set(x, 1, z, st("minecraft:gravel"))
        s.blob(2, 4, 5, 3.0, ymin=2)
        house_jigsaw(s, 5)
    elif kind == "courtyard":
        s = Ruin(f"{VILLAGE}_house_courtyard", (11, 6, 12), seed=7303)
        s.fill(4, 0, 0, 6, 0, 0, S_CARVED)
        shell(s, 0, 1, 10, 11, 3)
        s.fill(3, 0, 4, 7, 0, 8, S_SOIL)
        for x in range(3, 8):
            for z in range(4, 9):
                for y in range(1, 5):
                    s.set(x, y, z, S_AIR) if (x, y, z) in s.b else None
        for x in range(2, 9):            # inner court walls with openings
            for z in (3, 9):
                s.fill(x, 1, z, x, 3, z, S_BRICK)
        for z in range(3, 10):
            for x in (2, 8):
                s.fill(x, 1, z, x, 3, z, S_BRICK)
        for p in ((5, 3), (5, 9), (2, 6), (8, 6)):
            s.fill(p[0], 1, p[1], p[0], 2, p[1], S_AIR)
            s.protect_box(p[0], 1, p[1], p[0], 2, p[1])
        door(s, 5, 1, 2)
        s.tall_plant(5, 1, 6, "venus_tree_fern")
        s.set(4, 1, 7, st("venus_horsetail"))
        s.set(9, 1, 10, chest_state("west", "chests/venusian_village"))
        s.set(1, 1, 10, S_URN)
        s.set(1, 1, 2, S_URN)
        s.set(9, 1, 2, faced(STELE, "west"))
        s.blob(10, 3, 1, 2.0, ymin=2)
        house_jigsaw(s, 5)
    elif kind == "tower":
        s = Ruin(f"{VILLAGE}_house_tower", (7, 11, 8), seed=7304)
        s.fill(2, 0, 0, 4, 0, 0, S_CARVED)
        c = (3, 4)
        for x in range(7):
            for z in range(1, 8):
                d = math.hypot(x - c[0], z - c[1])
                if d <= 3.3:
                    s.set(x, 0, z, S_CARVED)
                    for y in range(1, 10):
                        s.set(x, y, z, S_BRICK if d > 2.3 else S_AIR)
        for y in (4, 7):
            for x in range(1, 6):
                for z in range(2, 7):
                    if math.hypot(x - c[0], z - c[1]) <= 2.3 and (x, z) != (4, 5):
                        s.set(x, y, z, slab(BSLAB, "top"))
        for y in range(1, 9):
            s.set(4, y, 6, st("minecraft:ladder", facing="north", waterlogged=False))
        for y in (4, 7):
            s.set(4, y, 5, S_AIR)
        s.set(4, 1, 6, st("minecraft:ladder", facing="north", waterlogged=False))
        door(s, 3, 1)
        for y in (3, 6, 9):
            s.set(0, y, 4, S_AIR)
            s.set(6, y, 4, S_AIR)
        s.set(2, 8, 4, S_URN)
        s.set(2, 1, 5, S_URN)
        s.set(3, 9, 7, faced(SUN, "north"))
        s.blob(5, 9, 2, 2.6, ymin=6)
        house_jigsaw(s, 3)
    elif kind == "temple":
        s = Ruin(f"{VILLAGE}_house_temple", (9, 7, 10), seed=7305)
        s.fill(0, 0, 0, 8, 0, 9, S_CARVED)
        s.fill(1, 1, 2, 7, 1, 9, S_BRICK)
        s.perimeter_stairs(1, 1, 2, 7, 9, BSTAIRS)
        s.fill(2, 2, 4, 6, 2, 9, S_BRICK)
        s.perimeter_stairs(2, 2, 4, 6, 9, BSTAIRS)
        for k, z in enumerate((1, 2, 3)):
            s.set(4, 1 + k, z, stairs(CSTAIRS, "south"))
            s.fill(4, 1, z, 4, k, z, S_CARVED) if k else None
        s.fill(3, 3, 5, 5, 3, 8, S_CARVED)
        s.set(4, 4, 7, S_ALTAR)
        s.set(4, 4, 8, faced(STELE, "north"))
        s.set(4, 5, 8, faced(SUN, "north"))
        s.set(3, 4, 8, S_URN)
        s.set(5, 4, 5, st("minecraft:candle", candles=2, lit=False, waterlogged=False))
        s.protect_box(4, 1, 0, 4, 5, 6)
        s.mossify(0.5, turf=0.35)
        s.plants(0.4)
        s.wall_vines(0.2)
        s.set(4, 1, 0, jigsaw_state("north", HOUSE, LOT, "minecraft:empty"))
        return s
    elif kind == "rubble":
        s = Ruin(f"{VILLAGE}_house_rubble", (7, 4, 7), seed=7306)
        s.fill(0, 0, 0, 6, 0, 6, S_CARVED)
        for x in range(7):
            for z in range(1, 7):
                edge = x in (0, 6) or z in (1, 6)
                if edge and rnd.random() < 0.8:
                    for y in range(1, 1 + rnd.randint(0, 2)):
                        s.set(x, y, z, rnd.choice((S_BRICK, S_CRACKED, S_CARVED)))
                elif not edge and rnd.random() < 0.4:
                    s.set(x, 1, z, rnd.choice((st("minecraft:gravel"), slab(BSLAB), S_COBBLE)))
        s.set(3, 1, 1, S_AIR)
        s.set(2, 1, 4, S_URN)
        house_jigsaw(s, 3)
        s.mossify(0.5, turf=0.4)
        s.plants(0.6)
        return s
    elif kind == "workshop":
        s = Ruin(f"{VILLAGE}_house_workshop", (9, 6, 8), seed=7307)
        s.fill(0, 0, 0, 8, 0, 7, S_CARVED)
        s.fill(0, 1, 7, 8, 3, 7, S_BRICK)
        s.fill(0, 1, 3, 0, 3, 7, S_BRICK)
        s.fill(8, 1, 3, 8, 3, 7, S_BRICK)
        for x in (0, 3, 5, 8):
            s.fill(x, 1, 1, x, 3, 1, S_PILLAR)
        s.fill(0, 4, 1, 8, 4, 7, slab(BSLAB))
        s.fill(1, 1, 5, 2, 2, 6, S_CARVED)           # the kiln
        s.set(1, 1, 5, ("minecraft:campfire", {"facing": "north", "lit": "false", "signal_fire": "false",
                                               "waterlogged": "false"}, None))
        for p in ((6, 1, 6), (7, 1, 6), (7, 2, 6), (7, 1, 5)):
            s.set(*p, S_URN)
        s.set(4, 1, 6, chest_state("north", "chests/venusian_village"))
        s.set(5, 1, 4, slab(CSLAB))
        s.blob(1, 4, 2, 2.4, ymin=3)
        s.blob(8, 4, 6, 1.8, ymin=3)
        house_jigsaw(s, 4)
    elif kind == "garden":
        s = Ruin(f"{VILLAGE}_house_garden", (7, 3, 8), seed=7308)
        s.fill(0, 0, 0, 6, 0, 7, S_SOIL)
        s.fill(2, 0, 0, 4, 0, 1, S_CARVED)
        for x in range(7):
            for z in range(1, 8):
                if (x in (0, 6) or z in (1, 7)) and (x, z) != (3, 1):
                    s.set(x, 1, z, S_BRICK if rnd.random() < 0.8 else slab(BSLAB))
        s.fill(3, 0, 2, 3, 0, 6, S_CARVED)
        s.set(3, 1, 6, S_URN)
        house_jigsaw(s, 3)
        s.mossify(0.5)
        s.plants(0.9, tall=0.4)
        return s
    finish_house(s)
    return s


# =====================================================================================================================
# World generation: pools, processors, structures, structure sets, biome tags
# =====================================================================================================================
HOUSE_WEIGHTS = {"hut": 6, "longhouse": 4, "courtyard": 3, "tower": 2, "temple": 2, "rubble": 5, "workshop": 3,
                 "garden": 3}
STREET_WEIGHTS = {"long": 5, "short": 4, "crossing": 2, "turn": 2, "tee": 2}
SHRINES = {"temple": (build_shrine_temple, 4), "steles": (build_shrine_steles, 3), "head": (build_shrine_head, 2)}

TEMPLATES.update({
    "venusian_pyramid/pyramid": build_pyramid,
    "venusian_ziggurat/ziggurat": build_ziggurat,
    f"{VILLAGE}/plaza": build_plaza,
})
for _k, (_fn, _w) in SHRINES.items():
    TEMPLATES[f"venusian_shrine/{_k}"] = _fn
for _k in STREET_WEIGHTS:
    TEMPLATES[f"{VILLAGE}/streets/{_k}"] = (lambda k=_k: build_street(k))
for _k in ("end", "end_stele"):
    TEMPLATES[f"{VILLAGE}/street_ends/{_k}"] = (lambda k=_k: build_street(k))
for _k in HOUSE_WEIGHTS:
    TEMPLATES[f"{VILLAGE}/houses/{_k}"] = (lambda k=_k: build_house(k))


def wg(kind, name, obj):
    write_json(os.path.join(DATA, "worldgen", kind, *name.split("/")) + ".json", obj)


def rule(block, out, p, out_props=None):
    o = {"Name": R(out)}
    if out_props:
        o["Properties"] = out_props
    return {"input_predicate": {"predicate_type": "minecraft:random_block_match", "block": R(block), "probability": p},
            "location_predicate": {"predicate_type": "minecraft:always_true"}, "output_state": o}


PROTECT = {"processor_type": "minecraft:protected_blocks", "value": "#minecraft:features_cannot_replace"}


def processors():
    weather = [rule(BRICKS, CRACKED, 0.12), rule(BRICKS, MOSSY, 0.12), rule(CARVED, CRACKED, 0.02),
               rule(BSTAIRS, "minecraft:air", 0.03), rule(URN, "minecraft:air", 0.25)]
    wg("processor_list", "venusian_weathering", {"processors": [
        {"processor_type": "minecraft:rule", "rules": weather}, PROTECT]})
    wg("processor_list", "venusian_village_decay", {"processors": [
        {"processor_type": "minecraft:block_rot", "integrity": 0.9, "rottable_blocks": f"#{MOD}:venusian_crumbling"},
        {"processor_type": "minecraft:rule", "rules": [rule(BRICKS, CRACKED, 0.2), rule(BRICKS, MOSSY, 0.25),
                                                        rule(CARVED, "venus_moss", 0.06), rule(URN, "minecraft:air", 0.3)]},
        {"processor_type": "minecraft:capped", "limit": 2, "delegate": {"processor_type": "minecraft:rule", "rules": [{
            "input_predicate": {"predicate_type": "minecraft:tag_match", "tag": f"{MOD}:venusian_rubble"},
            "location_predicate": {"predicate_type": "minecraft:always_true"},
            "output_state": {"Name": "minecraft:suspicious_gravel", "Properties": {"dusted": "0"}},
            "block_entity_modifier": {"type": "minecraft:append_loot",
                                      "loot_table": f"{MOD}:archaeology/venusian_ruins"}}]}},
        PROTECT]})
    wg("processor_list", "venusian_street", {"processors": [
        {"processor_type": "minecraft:rule", "rules": [rule(CARVED, "venus_moss", 0.2), rule(CARVED, "venus_soil", 0.08),
                                                        rule(BRICKS, CRACKED, 0.3)]},
        PROTECT]})


def element(location, processors_, projection="rigid"):
    return {"element_type": "minecraft:single_pool_element", "location": f"{MOD}:{location}",
            "processors": f"{MOD}:{processors_}", "projection": projection}


def pool(name, entries, fallback="minecraft:empty"):
    wg("template_pool", name, {"elements": [{"element": e, "weight": w} for e, w in entries], "fallback": fallback})


def structure(name, start_pool, biomes_tag, start_height, adaptation, size=1, max_dist=80):
    wg("structure", name, {
        "type": "minecraft:jigsaw", "biomes": f"#{MOD}:has_structure/{biomes_tag}", "step": "surface_structures",
        "spawn_overrides": {}, "terrain_adaptation": adaptation, "start_pool": f"{MOD}:{start_pool}", "size": size,
        "start_height": {"absolute": start_height}, "project_start_to_heightmap": "WORLD_SURFACE_WG",
        "max_distance_from_center": max_dist, "use_expansion_hack": False})


def structure_set(name, structure_, spacing, separation, salt, exclusion=None):
    """retrocosmos:exclusive_spread (random spread that keeps clear of several other sets, see
    oinstein/ExclusiveSpreadPlacement.java); exclusion = [(other set, chunks), ...]."""
    placement = {"type": f"{MOD}:exclusive_spread", "spacing": spacing, "separation": separation, "salt": salt}
    if exclusion:
        placement["exclusion_zones"] = [{"other_set": f"{MOD}:{o}", "chunk_count": n} for o, n in exclusion]
    wg("structure_set", name, {"structures": [{"structure": f"{MOD}:{structure_}", "weight": 1}],
                               "placement": placement})


STRUCTURES = {
    # name: (biomes, start height, terrain adaptation, jigsaw depth, spacing, separation, salt, exclusion)
    # spacing in chunks, roughly doubled after play-testing: ruins should be finds, not a city
    "venusian_pyramid": (("venus_jungle", "venus_cycad_plains"), -3, "beard_box", 1, 64, 28, 471103221,
                         [("oinstein_institute", 10)]),
    "venusian_ziggurat": (("venus_cycad_plains", "venus_volcanic_highlands"), -3, "beard_box", 1, 96, 40, 471103222,
                          [("venusian_pyramids", 10), ("oinstein_institute", 10)]),
    "venusian_ruined_village": (("venus_jungle", "venus_cycad_plains"), 0, "beard_thin", 5, 72, 32, 471103223,
                                [("venusian_pyramids", 8), ("oinstein_institute", 10)]),
    "venusian_shrine": (("venus_jungle", "venus_fern_swamp", "venus_glowcap_hollows"), -1, "beard_thin", 1, 40, 16,
                        471103224, [("venusian_ruined_villages", 5), ("oinstein_institute", 6)]),
}
SET_NAMES = {"venusian_pyramid": "venusian_pyramids", "venusian_ziggurat": "venusian_ziggurats",
             "venusian_ruined_village": "venusian_ruined_villages", "venusian_shrine": "venusian_shrines"}


def worldgen():
    processors()
    pool("venusian_pyramid/start", [(element("venusian_pyramid/pyramid", "venusian_weathering"), 1)])
    pool("venusian_ziggurat/start", [(element("venusian_ziggurat/ziggurat", "venusian_weathering"), 1)])
    pool("venusian_shrine/start", [(element(f"venusian_shrine/{k}", "venusian_weathering"), w)
                                   for k, (_fn, w) in SHRINES.items()])
    pool(f"{VILLAGE}/plazas", [(element(f"{VILLAGE}/plaza", "venusian_village_decay"), 1)])
    pool(f"{VILLAGE}/streets", [(element(f"{VILLAGE}/streets/{k}", "venusian_street", "terrain_matching"), w)
                                for k, w in STREET_WEIGHTS.items()], fallback=f"{MOD}:{VILLAGE}/street_ends")
    pool(f"{VILLAGE}/street_ends", [(element(f"{VILLAGE}/street_ends/{k}", "venusian_street", "terrain_matching"), w)
                                    for k, w in (("end", 3), ("end_stele", 1))])
    pool(f"{VILLAGE}/houses", [(element(f"{VILLAGE}/houses/{k}", "venusian_village_decay"), w)
                               for k, w in HOUSE_WEIGHTS.items()])
    starts = {"venusian_pyramid": "venusian_pyramid/start", "venusian_ziggurat": "venusian_ziggurat/start",
              "venusian_ruined_village": f"{VILLAGE}/plazas", "venusian_shrine": "venusian_shrine/start"}
    for name, (biomes, h, adapt, depth, spacing, sep, salt, excl) in STRUCTURES.items():
        tag(f"worldgen/biome/has_structure/{name}", [R(b) for b in biomes], namespace=MOD)
        structure(name, starts[name], name, h, adapt, size=depth, max_dist=80 if depth > 1 else 64)
        structure_set(SET_NAMES[name], name, spacing, sep, salt, excl)


# =====================================================================================================================
# Language
# =====================================================================================================================
NAMES = {
    BRICKS: ("Venusian Temple Bricks", "Венерианские храмовые кирпичи"),
    CRACKED: ("Cracked Venusian Temple Bricks", "Потрескавшиеся венерианские храмовые кирпичи"),
    MOSSY: ("Mossy Venusian Temple Bricks", "Замшелые венерианские храмовые кирпичи"),
    BSTAIRS: ("Venusian Temple Brick Stairs", "Ступени из венерианских храмовых кирпичей"),
    BSLAB: ("Venusian Temple Brick Slab", "Плита из венерианских храмовых кирпичей"),
    CARVED: ("Venusian Carved Stone", "Венерианский тёсаный камень"),
    CSTAIRS: ("Venusian Carved Stone Stairs", "Ступени из венерианского тёсаного камня"),
    CSLAB: ("Venusian Carved Stone Slab", "Плита из венерианского тёсаного камня"),
    GLYPH: ("Venusian Glyph Stone", "Венерианский камень с глифами"),
    INLAID: ("Venusian Inlaid Frieze", "Венерианский мозаичный фриз"),
    PILLAR: ("Venusian Pillar", "Венерианская колонна"),
    SUN: ("Venusian Sun Disc", "Венерианский солнечный диск"),
    STELE: ("Venusian Stele", "Венерианская стела"),
    ALTAR: ("Venusian Altar", "Венерианский алтарь"),
    URN: ("Venusian Urn", "Венерианская урна"),
}
ITEM_NAMES = {
    "venusian_idol": ("Venusian Idol", "Венерианский идол",
                      "A squat jade god with golden eyes. It feels warm.",
                      "Приземистый нефритовый божок с золотыми глазами. Он тёплый на ощупь."),
    "glyph_tablet": ("Glyph Tablet", "Табличка с глифами",
                     "Undeciphered Venusian glyphs.", "Нерасшифрованные венерианские глифы."),
    "sun_disk_fragment": ("Sun Disk Fragment", "Осколок солнечного диска",
                          "Hammered gold from a shattered sun disc.", "Чеканное золото расколотого солнечного диска."),
    "ancient_amulet": ("Ancient Amulet", "Древний амулет",
                       "Turquoise set in gold. Its eye seems to follow you.",
                       "Бирюза в золоте. Кажется, его глаз следит за вами."),
}
TABLET_TEXT = [
    ("\"...and the Sun went down into the Sea of Steam, and did not rise again.\" - H.C.",
     "«...и Солнце сошло в Парящее море и более не взошло». — Х.К."),
    ("\"Count of the priest-kings: forty and seven. The last has no name.\" - H.C.",
     "«Счёт царей-жрецов: сорок и семь. У последнего нет имени». — Х.К."),
    ("\"Feed the great lizards at the gate, lest they enter.\" (?)",
     "«Кормите великих ящеров у врат, дабы не вошли». (?)"),
    ("\"Our ships of fire went up to the Blue Star and found it empty.\" Earth?!",
     "«Огненные ладьи наши поднялись к Голубой звезде и нашли её пустой». Земля?!"),
    ("A star map. Venus, the Sun... and a third circle, crossed out.",
     "Звёздная карта. Венера, Солнце... и третий круг, зачёркнутый."),
    ("\"Here sleeps the Keeper of the Seven Suns. Do not wake him.\"",
     "«Здесь спит Хранитель Семи Солнц. Не будите его»."),
]
JOURNAL = [
    ("Venus Expedition No. 2, 1957. Day 41. The ruins are older than anything on Earth. Brennan swears the glyphs "
     "move when you are not looking at them.",
     "Венерианская экспедиция №2, 1957 год. День 41-й. Эти руины древнее всего, что есть на Земле. Бреннан клянётся, "
     "что глифы шевелятся, когда на них не смотришь."),
    ("Day 44. Found the stair under the sanctuary floor. The air below is dry and cold. We left a canister of fuel "
     "at the landing for the trip back.",
     "День 44-й. Нашли лестницу под полом святилища. Внизу сухой и холодный воздух. Оставили на площадке канистру "
     "топлива на обратный путь."),
    ("Day 47. Kowalski stepped on a plate in the tomb doorway. Darts. He'll live. MIND THE THRESHOLD.",
     "День 47-й. Ковальски наступил на плиту у входа в гробницу. Дротики. Жить будет. ОСТОРОЖНО, ПОРОГ."),
    ("Day 52. The big lizards are circling the camp. Rocket fuel low. If anyone finds this - the ziggurat to the "
     "east holds the rest of our supplies. God speed. - Dr. H. Calloway",
     "День 52-й. Большие ящеры кружат вокруг лагеря. Топлива мало. Если кто-нибудь найдёт это — остальные припасы "
     "в зиккурате к востоку. Храни вас Бог. — Д-р Х. Кэллоуэй"),
]
assert len(TABLET_TEXT) == TABLET_LORES and len(JOURNAL) == JOURNAL_PAGES

EN = {f"block.{MOD}.{k}": v[0] for k, v in NAMES.items()}
RU = {f"block.{MOD}.{k}": v[1] for k, v in NAMES.items()}
for _k, (_en, _ru, _len, _lru) in ITEM_NAMES.items():
    EN[f"item.{MOD}.{_k}"], RU[f"item.{MOD}.{_k}"] = _en, _ru
    EN[f"item.{MOD}.{_k}.lore"], RU[f"item.{MOD}.{_k}.lore"] = _len, _lru
for _i, (_en, _ru) in enumerate(TABLET_TEXT):
    EN[f"item.{MOD}.glyph_tablet.lore_{_i}"], RU[f"item.{MOD}.glyph_tablet.lore_{_i}"] = _en, _ru
for _i, (_en, _ru) in enumerate(JOURNAL):
    EN[f"book.{MOD}.expedition_log.page_{_i}"], RU[f"book.{MOD}.expedition_log.page_{_i}"] = _en, _ru
EN[f"book.{MOD}.expedition_log.title"] = "Expedition Log"
RU[f"book.{MOD}.expedition_log.title"] = "Дневник экспедиции"


# =====================================================================================================================
# Self-check: the loot rooms must be reachable on foot
# =====================================================================================================================
PASSABLE = {AIR, "minecraft:vine", "minecraft:cobweb", "minecraft:candle", "minecraft:stone_pressure_plate",
            "minecraft:white_carpet", "minecraft:ladder"} | {R(n) for n in (
    "venus_hanging_vines", "venus_sedge", "venus_horsetail", "venus_cycad", "venus_fire_lily", "venus_giant_fern",
    "venus_tree_fern")}


def reachable(ruin, start):
    def passable(x, y, z):
        n = ruin.name_at(x, y, z)
        return (n is None and y > ruin.G) or n in PASSABLE

    def standable(x, y, z):
        n = ruin.name_at(x, y, z)
        return (n is None and y <= ruin.G) or (n is not None and n not in PASSABLE)

    seen = {start}
    todo = [start]
    while todo:
        x, y, z = todo.pop()
        for dx, dz in DIRS.values():
            for dy in (1, 0, -1, -2, -3):
                p = (x + dx, y + dy, z + dz)
                if not ruin.inside(*p) or p in seen:
                    continue
                if passable(*p) and passable(p[0], p[1] + 1, p[2]) and standable(p[0], p[1] - 1, p[2]) \
                        and (dy <= 0 or passable(x, y + 2, z)):
                    seen.add(p)
                    todo.append(p)
                    break
    return seen


def check_reach(ruin, start, targets):
    seen = reachable(ruin, start)
    missing = [t for t in targets if not any((t[0] + dx, t[1], t[2] + dz) in seen
                                             for dx, dz in list(DIRS.values()) + [(0, 0)])]
    if missing:
        raise SystemExit(f"ruins.py: {ruin.name}: unreachable from {start}: {missing}")


# Dr. Oinstein's outposts and Institute are generated by tools/oinstein.py (on top of this builder); its lang joins ours.
import oinstein as _oinstein  # noqa: E402  (when oinstein is imported first it merges its lang itself)

if hasattr(_oinstein, "EN"):
    EN.update(_oinstein.EN)
    RU.update(_oinstein.RU)
