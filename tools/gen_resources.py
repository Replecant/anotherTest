#!/usr/bin/env python3
"""Generates all assets and data for Retro Cosmos (textures, models, recipes, worldgen, loot, lang).

Run from the repository root:  python3 tools/gen_resources.py
"""
import json
import os
import random
from PIL import Image, ImageDraw

MOD = "retrocosmos"
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "main", "resources")
ASSETS = os.path.join(ROOT, "assets", MOD)
DATA = os.path.join(ROOT, "data", MOD)


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")


def save(img, *parts):
    path = os.path.join(ASSETS, "textures", *parts) + ".png"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)


# ----------------------------------------------------------------------------
# Palette: 1950s "atomic age" retro-futurism
# ----------------------------------------------------------------------------
CREAM = (238, 228, 200)
CREAM_D = (205, 192, 160)
RED = (204, 62, 48)
RED_D = (140, 38, 32)
RED_L = (232, 102, 80)
TEAL = (64, 168, 160)
TEAL_D = (36, 108, 108)
TEAL_L = (126, 214, 200)
ORANGE = (240, 150, 50)
ORANGE_L = (255, 206, 110)
CHROME = (200, 208, 214)
CHROME_D = (130, 140, 150)
CHROME_L = (240, 246, 250)
STEEL = (92, 98, 108)
STEEL_D = (58, 62, 70)
YELLOW = (236, 196, 52)
BLACK = (34, 32, 36)
GLASS = (150, 210, 230)
GLASS_L = (220, 244, 252)
ALU = (190, 196, 204)
ALU_D = (138, 146, 156)
ALU_L = (228, 232, 238)
TI = (150, 164, 196)
TI_D = (96, 108, 140)
TI_L = (206, 216, 240)
BAUX = (176, 88, 52)
BAUX_D = (120, 56, 34)
BAUX_L = (214, 132, 84)


def rgba(c, a=255):
    return (c[0], c[1], c[2], a)


def new(w=16, h=16, fill=(0, 0, 0, 0)):
    return Image.new("RGBA", (w, h), fill)


def px(img, pts, color):
    for (x, y) in pts:
        if 0 <= x < img.width and 0 <= y < img.height:
            img.putpixel((x, y), rgba(color))


def noise_fill(img, base, var, seed, box=None):
    rnd = random.Random(seed)
    x0, y0, x1, y1 = box or (0, 0, img.width, img.height)
    for y in range(y0, y1):
        for x in range(x0, x1):
            d = rnd.randint(-var, var)
            img.putpixel((x, y), tuple(max(0, min(255, c + d)) for c in base) + (255,))


def outline(img, color):
    """Adds a 1px outline around opaque pixels (for item sprites)."""
    src = img.copy()
    for y in range(img.height):
        for x in range(img.width):
            if src.getpixel((x, y))[3] == 0:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < img.width and 0 <= ny < img.height and src.getpixel((nx, ny))[3] > 0:
                        img.putpixel((x, y), rgba(color))
                        break


# ----------------------------------------------------------------------------
# Block textures
# ----------------------------------------------------------------------------

def stone(seed, deep=False):
    img = new()
    if deep:
        noise_fill(img, (80, 80, 86), 8, seed)
        rnd = random.Random(seed + 1)
        for y in range(0, 16, 4):
            for x in range(16):
                if rnd.random() < 0.5:
                    px(img, [(x, y)], (64, 64, 70))
    else:
        noise_fill(img, (126, 126, 126), 10, seed)
        rnd = random.Random(seed + 1)
        for _ in range(14):
            px(img, [(rnd.randrange(16), rnd.randrange(16))], (104, 104, 104))
    return img


def ore(seed, deep, dark, mid, light):
    img = stone(seed, deep)
    clusters = [(3, 3), (10, 2), (5, 9), (12, 10), (8, 13)]
    rnd = random.Random(seed + 7)
    for cx, cy in clusters:
        pts = [(cx, cy), (cx + 1, cy), (cx, cy + 1), (cx + 1, cy + 1)]
        if rnd.random() < 0.6:
            pts.append((cx + 2, cy + 1))
        if rnd.random() < 0.6:
            pts.append((cx - 1, cy))
        px(img, pts, mid)
        px(img, [(cx + 1, cy + 1)], dark)
        px(img, [(cx, cy)], light)
    return img


def riveted_panel(base, dark, light, seed):
    img = new()
    noise_fill(img, base, 4, seed)
    # bevelled frame
    for i in range(16):
        px(img, [(i, 0), (0, i)], light)
        px(img, [(i, 15), (15, i)], dark)
    # inner panel seam
    for i in range(2, 14):
        px(img, [(i, 7)], dark)
        px(img, [(i, 8)], light)
    # rivets
    for (x, y) in [(2, 2), (13, 2), (2, 13), (13, 13), (2, 5), (13, 5), (2, 10), (13, 10)]:
        px(img, [(x, y)], light)
        px(img, [(x + 1, y + 1)], dark)
    return img


def launch_pad_top():
    img = new()
    noise_fill(img, STEEL, 5, 99)
    # hazard border
    for y in range(16):
        for x in range(16):
            if x < 2 or y < 2 or x > 13 or y > 13:
                px(img, [(x, y)], YELLOW if ((x + y) // 2) % 2 == 0 else BLACK)
    # target circle
    d = ImageDraw.Draw(img)
    d.ellipse((4, 4, 11, 11), outline=rgba(CREAM))
    px(img, [(7, 7), (8, 8), (7, 8), (8, 7)], RED)
    return img


def launch_pad_side():
    img = new()
    noise_fill(img, STEEL_D, 5, 98)
    for x in range(16):
        for y in range(0, 3):
            px(img, [(x, y)], YELLOW if ((x + y) // 2) % 2 == 0 else BLACK)
    for x in range(16):
        px(img, [(x, 3)], STEEL)
    for (x, y) in [(2, 7), (7, 7), (12, 7), (2, 12), (7, 12), (12, 12)]:
        px(img, [(x, y), (x + 1, y)], CHROME_D)
    return img


def rocket_body():
    img = new()
    noise_fill(img, CREAM, 3, 5)
    for y in range(16):
        px(img, [(0, y)], CREAM_D)
        px(img, [(15, y)], CREAM_D)
    # red racing stripe band
    for x in range(16):
        for y in (11, 12, 13):
            px(img, [(x, y)], RED)
        px(img, [(x, 14)], RED_D)
    # rivet line
    for x in range(1, 16, 3):
        px(img, [(x, 2)], CREAM_D)
    return img


def rocket_window():
    img = rocket_body()
    d = ImageDraw.Draw(img)
    d.ellipse((3, 2, 12, 11), fill=rgba(CHROME_D), outline=rgba(CHROME_L))
    d.ellipse((5, 4, 10, 9), fill=rgba(TEAL_D))
    px(img, [(6, 5), (7, 5), (6, 6)], GLASS_L)
    px(img, [(8, 7), (9, 7)], TEAL)
    return img


def rocket_fin():
    img = new()
    noise_fill(img, RED, 6, 11)
    for i in range(16):
        px(img, [(i, 15 - (i // 4))], RED_D)
        px(img, [(i, 0)], RED_L)
    return img


def rocket_nozzle():
    img = new()
    noise_fill(img, STEEL, 6, 12)
    for x in range(16):
        px(img, [(x, 0)], CHROME)
        px(img, [(x, 15)], STEEL_D)
    for y in range(16):
        if y % 4 == 1:
            for x in range(16):
                px(img, [(x, y)], STEEL_D)
    return img


def rocket_nozzle_bottom():
    img = new()
    noise_fill(img, STEEL_D, 4, 13)
    d = ImageDraw.Draw(img)
    d.ellipse((2, 2, 13, 13), fill=rgba(BLACK), outline=rgba(CHROME_D))
    d.ellipse((5, 5, 10, 10), fill=rgba((90, 40, 20)))
    return img


def rocket_cone():
    img = new()
    noise_fill(img, RED, 5, 14)
    for x in range(16):
        px(img, [(x, 15)], CHROME)
        px(img, [(x, 14)], CHROME_D)
    for y in range(14):
        px(img, [(0, y)], RED_D)
        px(img, [(15, y)], RED_D)
        px(img, [(4, y)], RED_L)
    return img


def antenna():
    img = new()
    noise_fill(img, CHROME, 8, 15)
    return img


# ----------------------------------------------------------------------------
# Item textures
# ----------------------------------------------------------------------------

def ingot(dark, mid, light):
    img = new()
    # isometric-ish ingot like vanilla
    rows = {
        5: (6, 12), 6: (4, 13), 7: (3, 13), 8: (2, 12), 9: (2, 11), 10: (2, 9), 11: (3, 7),
    }
    for y, (a, b) in rows.items():
        for x in range(a, b + 1):
            px(img, [(x, y)], mid)
    for x in range(6, 13):
        px(img, [(x, 5)], light)
    for x in range(4, 12):
        px(img, [(x, 6)], light)
    px(img, [(5, 7), (6, 7), (7, 7)], light)
    for y in range(8, 12):
        px(img, [(2 + (y - 8) // 2, y)], dark)
    for x in range(3, 8):
        px(img, [(x, 11)], dark)
    px(img, [(13, 7), (12, 8), (11, 9), (9, 10), (8, 10)], dark)
    outline(img, tuple(max(0, c - 70) for c in dark))
    return img


def raw_lump(dark, mid, light, seed):
    img = new()
    rnd = random.Random(seed)
    d = ImageDraw.Draw(img)
    d.ellipse((3, 4, 12, 12), fill=rgba(mid))
    d.ellipse((6, 2, 13, 9), fill=rgba(mid))
    for _ in range(10):
        px(img, [(rnd.randint(4, 12), rnd.randint(4, 11))], dark)
    px(img, [(7, 3), (8, 3), (5, 5), (6, 5), (4, 7)], light)
    outline(img, tuple(max(0, c - 60) for c in dark))
    return img


def plate(dark, mid, light):
    img = new()
    for y in range(3, 13):
        for x in range(3, 13):
            px(img, [(x, y)], mid)
    for i in range(3, 13):
        px(img, [(i, 3), (3, i)], light)
        px(img, [(i, 12), (12, i)], dark)
    for (x, y) in [(5, 5), (10, 5), (5, 10), (10, 10)]:
        px(img, [(x, y)], dark)
    outline(img, tuple(max(0, c - 70) for c in dark))
    return img


def vacuum_tube():
    img = new()
    d = ImageDraw.Draw(img)
    # base
    d.rectangle((5, 12, 10, 14), fill=rgba(BLACK))
    px(img, [(6, 15), (9, 15)], CHROME_D)
    # glass bulb
    d.rounded_rectangle((4, 2, 11, 12), radius=3, fill=rgba(GLASS, 170), outline=rgba(GLASS_L))
    # filament glow
    for y in range(5, 11):
        px(img, [(7, y), (8, y)], ORANGE)
    px(img, [(7, 6), (8, 8)], ORANGE_L)
    px(img, [(5, 3), (5, 4)], GLASS_L)
    outline(img, (40, 60, 70))
    return img


def guidance_computer():
    img = new()
    d = ImageDraw.Draw(img)
    d.rectangle((1, 3, 14, 13), fill=rgba(TEAL), outline=rgba(TEAL_D))
    d.rectangle((2, 4, 13, 5), fill=rgba(CREAM))
    # dials
    d.ellipse((2, 7, 6, 11), fill=rgba(CREAM), outline=rgba(BLACK))
    d.ellipse((9, 7, 13, 11), fill=rgba(CREAM), outline=rgba(BLACK))
    px(img, [(4, 8), (4, 9)], RED)
    px(img, [(11, 9), (12, 8)], RED)
    # tubes on top
    px(img, [(4, 1), (4, 2), (7, 1), (7, 2), (10, 1), (10, 2)], ORANGE)
    # lamps
    px(img, [(7, 8)], ORANGE_L)
    px(img, [(7, 10)], (120, 230, 120))
    outline(img, BLACK)
    return img


def nose_cone():
    img = new()
    for y in range(2, 14):
        half = (y - 1) // 2
        for x in range(8 - half, 8 + half):
            px(img, [(x, y)], RED)
        px(img, [(8 - half, y)], RED_L)
    for x in range(2, 14):
        px(img, [(x, 13)], CHROME)
    px(img, [(7, 0), (7, 1)], CHROME)
    outline(img, RED_D)
    return img


def hull_segment():
    img = new()
    for y in range(1, 15):
        for x in range(4, 12):
            px(img, [(x, y)], CREAM)
        px(img, [(4, y)], CREAM_D)
        px(img, [(11, y)], CREAM_D)
    d = ImageDraw.Draw(img)
    d.ellipse((5, 3, 10, 8), fill=rgba(CHROME_D))
    d.ellipse((6, 4, 9, 7), fill=rgba(TEAL_D))
    px(img, [(6, 4)], GLASS_L)
    for x in range(4, 12):
        px(img, [(x, 11), (x, 12)], RED)
    outline(img, (90, 80, 60))
    return img


def rocket_fin_item():
    img = new()
    for y in range(2, 15):
        w = min(11, (y - 1))
        for x in range(3, 3 + w):
            px(img, [(x, y)], RED)
        px(img, [(3, y)], RED_L)
    for x in range(3, 14):
        px(img, [(x, 14)], CHROME)
    outline(img, RED_D)
    return img


def rocket_engine():
    img = new()
    d = ImageDraw.Draw(img)
    d.rectangle((5, 1, 10, 5), fill=rgba(CHROME), outline=rgba(CHROME_D))
    d.polygon([(5, 6), (10, 6), (13, 13), (2, 13)], fill=rgba(STEEL), outline=rgba(STEEL_D))
    for y in (8, 10, 12):
        d.line((3, y, 12, y), fill=rgba(STEEL_D))
    px(img, [(6, 2), (6, 3)], CHROME_L)
    px(img, [(5, 14), (6, 14), (7, 14), (8, 14), (9, 14), (10, 14)], ORANGE)
    px(img, [(7, 15), (8, 15)], ORANGE_L)
    outline(img, BLACK)
    return img


def canister(full):
    img = new()
    d = ImageDraw.Draw(img)
    body = ORANGE if full else CHROME
    dark = (170, 90, 30) if full else CHROME_D
    d.rounded_rectangle((3, 4, 12, 14), radius=2, fill=rgba(body), outline=rgba(dark))
    d.rectangle((6, 1, 9, 3), fill=rgba(STEEL))
    d.rectangle((5, 3, 10, 4), fill=rgba(STEEL_D))
    # label with atom symbol
    d.rectangle((4, 7, 11, 11), fill=rgba(CREAM))
    px(img, [(7, 9), (8, 9)], RED if full else TEAL_D)
    px(img, [(6, 8), (9, 10), (6, 10), (9, 8)], TEAL_D)
    outline(img, BLACK)
    return img


def rocket_item():
    img = new()
    # body
    for y in range(4, 13):
        for x in range(6, 10):
            px(img, [(x, y)], CREAM)
        px(img, [(6, y)], CREAM_D)
    # cone
    px(img, [(7, 1), (8, 1), (7, 2), (8, 2), (6, 3), (7, 3), (8, 3), (9, 3)], RED)
    px(img, [(7, 0)], CHROME)
    # window
    px(img, [(7, 5), (8, 5), (7, 6), (8, 6)], TEAL)
    px(img, [(7, 5)], GLASS_L)
    # stripe
    for x in range(6, 10):
        px(img, [(x, 9)], RED)
    # fins
    px(img, [(5, 10), (4, 11), (5, 11), (3, 12), (4, 12), (5, 12), (3, 13), (4, 13)], RED)
    px(img, [(10, 10), (10, 11), (11, 11), (10, 12), (11, 12), (12, 12), (11, 13), (12, 13)], RED)
    # nozzle & flame
    px(img, [(7, 13), (8, 13)], STEEL)
    px(img, [(7, 14), (8, 14)], ORANGE)
    px(img, [(7, 15)], ORANGE_L)
    outline(img, BLACK)
    return img


def suit_icon(kind):
    img = new()
    d = ImageDraw.Draw(img)
    if kind == "helmet":
        d.ellipse((2, 1, 13, 13), fill=rgba(GLASS, 150), outline=rgba(CHROME_L))
        d.rectangle((3, 11, 12, 14), fill=rgba(CREAM), outline=rgba(CREAM_D))
        px(img, [(5, 3), (4, 4), (4, 5)], GLASS_L)
        px(img, [(6, 12), (7, 12), (8, 12), (9, 12)], ORANGE)
        px(img, [(12, 2), (12, 1)], CHROME)
    elif kind == "suit":
        d.rectangle((4, 2, 11, 14), fill=rgba(CREAM))
        d.rectangle((1, 3, 3, 10), fill=rgba(CREAM))
        d.rectangle((12, 3, 14, 10), fill=rgba(CREAM))
        d.rectangle((6, 5, 9, 8), fill=rgba(TEAL))
        px(img, [(7, 6)], ORANGE_L)
        for x in range(4, 12):
            px(img, [(x, 11)], ORANGE)
        px(img, [(1, 10), (2, 10), (3, 10), (12, 10), (13, 10), (14, 10)], RED)
    elif kind == "leggings":
        d.rectangle((4, 2, 11, 4), fill=rgba(CREAM_D))
        d.rectangle((4, 5, 7, 14), fill=rgba(CREAM))
        d.rectangle((8, 5, 11, 14), fill=rgba(CREAM))
        px(img, [(5, 9), (6, 9), (9, 9), (10, 9)], ORANGE)
    elif kind == "boots":
        d.rectangle((2, 6, 6, 12), fill=rgba(CREAM))
        d.rectangle((9, 6, 13, 12), fill=rgba(CREAM))
        d.rectangle((1, 12, 7, 14), fill=rgba(RED))
        d.rectangle((8, 12, 14, 14), fill=rgba(RED))
        px(img, [(3, 8), (4, 8), (10, 8), (11, 8)], ORANGE)
    outline(img, (70, 60, 50))
    return img


# ----------------------------------------------------------------------------
# Armor (equipment) layer textures, 64x32 humanoid UV layout
# ----------------------------------------------------------------------------

def fill_box(img, u, v, w, h, d, color_fn):
    """Fills the UV net of a cuboid (w x h x d) whose net starts at (u, v)."""
    regions = [
        (u + d, v, w, d),              # top
        (u + d + w, v, w, d),          # bottom
        (u, v + d, d, h),              # right
        (u + d, v + d, w, h),          # front
        (u + d + w, v + d, d, h),      # left
        (u + d + w + d, v + d, w, h),  # back
    ]
    for idx, (x0, y0, rw, rh) in enumerate(regions):
        for y in range(y0, y0 + rh):
            for x in range(x0, x0 + rw):
                img.putpixel((x, y), rgba(color_fn(idx, x - x0, y - y0, rw, rh)))


def suit_layer():
    img = new(64, 32)
    rnd = random.Random(3)

    def fabric(face, x, y, w, h):
        c = CREAM if rnd.random() > 0.12 else CREAM_D
        return c

    # helmet: head cube (8x8x8) at (0,0) - glass visor on the front
    def helmet(face, x, y, w, h):
        if face == 3:  # front
            if 1 <= x <= 6 and 1 <= y <= 5:
                return GLASS_L if (x == 1 or y == 1) else TEAL_D
            return CHROME
        if face in (0,):
            return CHROME_L
        return CHROME if y < h - 2 else ORANGE

    fill_box(img, 0, 0, 8, 8, 8, helmet)
    # hat overlay (32,0) - glass bubble, mostly transparent
    for y in range(0, 16):
        for x in range(32, 64):
            img.putpixel((x, y), (190, 230, 245, 70))

    # body (16,16): 8x12x4 - teal chest panel and orange belt
    def body(face, x, y, w, h):
        if face == 3 and 2 <= x <= 5 and 2 <= y <= 5:
            return TEAL if not (x == 3 and y == 3) else ORANGE_L
        if y in (8, 9):
            return ORANGE
        if face == 5 and 1 <= x <= 6 and 1 <= y <= 6:  # oxygen pack on the back
            return CHROME if x not in (3, 4) else CHROME_D
        return fabric(face, x, y, w, h)

    fill_box(img, 16, 16, 8, 12, 4, body)

    # arms (40,16): 4x12x4 with red cuffs
    def arm(face, x, y, w, h):
        if y >= h - 3:
            return RED
        if y == 4:
            return ORANGE
        return fabric(face, x, y, w, h)

    fill_box(img, 40, 16, 4, 12, 4, arm)

    # legs (0,16): 4x12x4 with red boots
    def leg(face, x, y, w, h):
        if y >= h - 4:
            return RED if y != h - 4 else RED_L
        return fabric(face, x, y, w, h)

    fill_box(img, 0, 16, 4, 12, 4, leg)
    return img


def suit_leggings_layer():
    img = new(64, 32)
    rnd = random.Random(4)

    def fabric(face, x, y, w, h):
        return CREAM if rnd.random() > 0.12 else CREAM_D

    def body(face, x, y, w, h):
        if y >= 7:
            return ORANGE if y in (8, 9) else fabric(face, x, y, w, h)
        return (0, 0, 0)

    fill_box(img, 16, 16, 8, 12, 4, body)
    # clear the non-waist part of the body
    for y in range(16, 32):
        for x in range(16, 40):
            p = img.getpixel((x, y))
            if p[:3] == (0, 0, 0):
                img.putpixel((x, y), (0, 0, 0, 0))

    def leg(face, x, y, w, h):
        if y == 5:
            return ORANGE
        return fabric(face, x, y, w, h)

    fill_box(img, 0, 16, 4, 12, 4, leg)
    return img


def logo():
    img = Image.new("RGBA", (128, 128), rgba((26, 30, 52)))
    d = ImageDraw.Draw(img)
    rnd = random.Random(42)
    for _ in range(40):
        x, y = rnd.randrange(128), rnd.randrange(128)
        img.putpixel((x, y), rgba(CREAM))
    d.ellipse((70, 14, 118, 62), fill=rgba(ORANGE), outline=rgba(ORANGE_L))
    d.ellipse((60, 32, 128, 44), outline=rgba(CREAM), width=2)
    big = rocket_item().resize((96, 96), Image.NEAREST)
    img.alpha_composite(big, (8, 24))
    return img


# ----------------------------------------------------------------------------
# Models
# ----------------------------------------------------------------------------

def cube_all(name, tex=None):
    write_json(os.path.join(ASSETS, "models", "block", name + ".json"),
               {"parent": "minecraft:block/cube_all", "textures": {"all": f"{MOD}:block/{tex or name}"}})


def simple_blockstate(name):
    write_json(os.path.join(ASSETS, "blockstates", name + ".json"),
               {"variants": {"": {"model": f"{MOD}:block/{name}"}}})


def item_def(name, model):
    write_json(os.path.join(ASSETS, "items", name + ".json"), {"model": {"type": "minecraft:model", "model": model}})


def generated_item(name, parent="minecraft:item/generated"):
    write_json(os.path.join(ASSETS, "models", "item", name + ".json"),
               {"parent": parent, "textures": {"layer0": f"{MOD}:item/{name}"}})
    item_def(name, f"{MOD}:item/{name}")


def element(frm, to, tex, faces=("north", "south", "east", "west", "up", "down"), face_tex=None):
    face_tex = face_tex or {}
    return {"from": list(frm), "to": list(to),
            "faces": {f: {"texture": face_tex.get(f, tex)} for f in faces}}


def rocket_models():
    t = {"body": f"{MOD}:block/rocket_body", "window": f"{MOD}:block/rocket_window",
         "fin": f"{MOD}:block/rocket_fin", "nozzle": f"{MOD}:block/rocket_nozzle",
         "nozzle_bottom": f"{MOD}:block/rocket_nozzle_bottom", "cone": f"{MOD}:block/rocket_cone",
         "antenna": f"{MOD}:block/rocket_antenna"}
    bottom = {
        "textures": dict(t, particle=t["body"]),
        "elements": [
            element((3, 3, 3), (13, 16, 13), "#body", faces=("north", "south", "east", "west", "down")),
            element((5, 0, 5), (11, 3, 11), "#nozzle", face_tex={"down": "#nozzle_bottom"}),
            element((0, 0, 7), (3, 9, 9), "#fin"),
            element((13, 0, 7), (16, 9, 9), "#fin"),
            element((7, 0, 0), (9, 9, 3), "#fin"),
            element((7, 0, 13), (9, 9, 16), "#fin"),
        ],
    }
    middle = {
        "textures": dict(t, particle=t["body"]),
        "elements": [
            element((3, 0, 3), (13, 16, 13), "#body", faces=("north", "south", "east", "west"),
                    face_tex={"north": "#window", "south": "#window"}),
        ],
    }
    top = {
        "textures": dict(t, particle=t["cone"]),
        "elements": [
            element((3, 0, 3), (13, 2, 13), "#body", faces=("north", "south", "east", "west", "up")),
            element((4, 2, 4), (12, 6, 12), "#cone"),
            element((5, 6, 5), (11, 11, 11), "#cone"),
            element((6, 11, 6), (10, 14, 10), "#cone"),
            element((7.5, 14, 7.5), (8.5, 16, 8.5), "#antenna"),
        ],
    }
    for part, model in (("bottom", bottom), ("middle", middle), ("top", top)):
        model["ambientocclusion"] = False
        write_json(os.path.join(ASSETS, "models", "block", f"rocket_{part}.json"), model)
    write_json(os.path.join(ASSETS, "blockstates", "rocket.json"), {"variants": {
        "part=bottom": {"model": f"{MOD}:block/rocket_bottom"},
        "part=middle": {"model": f"{MOD}:block/rocket_middle"},
        "part=top": {"model": f"{MOD}:block/rocket_top"},
    }})


def launch_pad_model():
    write_json(os.path.join(ASSETS, "models", "block", "launch_pad.json"), {
        "parent": "minecraft:block/cube_bottom_top",
        "textures": {"top": f"{MOD}:block/launch_pad_top", "bottom": f"{MOD}:block/titanium_block",
                     "side": f"{MOD}:block/launch_pad_side"}})


# ----------------------------------------------------------------------------
# Data
# ----------------------------------------------------------------------------

def loot_self(name):
    write_json(os.path.join(DATA, "loot_table", "blocks", name + ".json"), {
        "type": "minecraft:block",
        "pools": [{"rolls": 1, "bonus_rolls": 0,
                   "entries": [{"type": "minecraft:item", "name": f"{MOD}:{name}"}],
                   "conditions": [{"condition": "minecraft:survives_explosion"}]}],
        "random_sequence": f"{MOD}:blocks/{name}"})


def loot_ore(name, raw):
    write_json(os.path.join(DATA, "loot_table", "blocks", name + ".json"), {
        "type": "minecraft:block",
        "pools": [{"rolls": 1, "bonus_rolls": 0, "entries": [{
            "type": "minecraft:alternatives",
            "children": [
                {"type": "minecraft:item", "name": f"{MOD}:{name}",
                 "conditions": [{"condition": "minecraft:match_tool", "predicate": {"predicates": {
                     "minecraft:enchantments": [{"enchantments": "minecraft:silk_touch", "levels": {"min": 1}}]}}}]},
                {"type": "minecraft:item", "name": f"{MOD}:{raw}",
                 "functions": [
                     {"function": "minecraft:apply_bonus", "enchantment": "minecraft:fortune", "formula": "minecraft:ore_drops"},
                     {"function": "minecraft:explosion_decay"}]},
            ]}]}],
        "random_sequence": f"{MOD}:blocks/{name}"})


def loot_rocket():
    write_json(os.path.join(DATA, "loot_table", "blocks", "rocket.json"), {
        "type": "minecraft:block",
        "pools": [{"rolls": 1, "bonus_rolls": 0,
                   "entries": [{"type": "minecraft:item", "name": f"{MOD}:rocket"}],
                   "conditions": [
                       {"condition": "minecraft:block_state_property", "block": f"{MOD}:rocket",
                        "properties": {"part": "bottom"}},
                       {"condition": "minecraft:survives_explosion"}]}],
        "random_sequence": f"{MOD}:blocks/rocket"})


def ing(x):
    return x if ":" in x or x.startswith("#") else f"{MOD}:{x}"


def shaped(name, pattern, key, result, count=1, category="misc"):
    write_json(os.path.join(DATA, "recipe", name + ".json"), {
        "type": "minecraft:crafting_shaped", "category": category, "pattern": pattern,
        "key": {k: ing(v) for k, v in key.items()},
        "result": {"id": ing(result), "count": count}})


def shapeless(name, ingredients, result, count=1, category="misc"):
    write_json(os.path.join(DATA, "recipe", name + ".json"), {
        "type": "minecraft:crafting_shapeless", "category": category,
        "ingredients": [ing(i) for i in ingredients],
        "result": {"id": ing(result), "count": count}})


def cooking(name, kind, ingredient, result, xp, time):
    write_json(os.path.join(DATA, "recipe", name + ".json"), {
        "type": f"minecraft:{kind}", "category": "misc", "ingredient": ing(ingredient),
        "result": {"id": ing(result)}, "experience": xp, "cookingtime": time})


def tag(path, values, namespace="minecraft"):
    base = os.path.join(ROOT, "data", namespace, "tags", *path.split("/"))
    write_json(base + ".json", {"replace": False, "values": values})


def ore_feature(name, block, deep_block, size, count, lo, hi, shape="trapezoid", air_discard=0.0):
    write_json(os.path.join(DATA, "worldgen", "configured_feature", name + ".json"), {
        "type": "minecraft:ore",
        "config": {"size": size, "discard_chance_on_air_exposure": air_discard, "targets": [
            {"target": {"predicate_type": "minecraft:tag_match", "tag": "minecraft:stone_ore_replaceables"},
             "state": {"Name": f"{MOD}:{block}"}},
            {"target": {"predicate_type": "minecraft:tag_match", "tag": "minecraft:deepslate_ore_replaceables"},
             "state": {"Name": f"{MOD}:{deep_block}"}},
        ]}})
    write_json(os.path.join(DATA, "worldgen", "placed_feature", name + ".json"), {
        "feature": f"{MOD}:{name}",
        "placement": [
            {"type": "minecraft:count", "count": count},
            {"type": "minecraft:in_square"},
            {"type": "minecraft:height_range", "height": {
                "type": f"minecraft:{shape}", "min_inclusive": {"absolute": lo}, "max_inclusive": {"absolute": hi}}},
            {"type": "minecraft:biome"},
        ]})


def advancement(name, icon, parent, criteria, frame="task", background=None, hidden=False):
    display = {"icon": {"id": ing(icon)},
               "title": {"translate": f"advancements.{MOD}.{name}.title"},
               "description": {"translate": f"advancements.{MOD}.{name}.description"},
               "frame": frame, "show_toast": True, "announce_to_chat": True, "hidden": hidden}
    if background:
        display["background"] = background
    adv = {"display": display, "criteria": criteria}
    if parent:
        adv["parent"] = f"{MOD}:stage1/{parent}"
    write_json(os.path.join(DATA, "advancement", "stage1", name + ".json"), adv)


def has_item(*items):
    return {"has_" + items[0]: {"trigger": "minecraft:inventory_changed",
                                "conditions": {"items": [{"items": [ing(i) for i in items] if len(items) > 1 else ing(items[0])}]}}}


# ----------------------------------------------------------------------------

def main():
    # ---- textures ----
    save(ore(1, False, BAUX_D, BAUX, BAUX_L), "block", "bauxite_ore")
    save(ore(2, True, BAUX_D, BAUX, BAUX_L), "block", "deepslate_bauxite_ore")
    save(ore(3, False, TI_D, TI, TI_L), "block", "titanium_ore")
    save(ore(4, True, TI_D, TI, TI_L), "block", "deepslate_titanium_ore")
    save(riveted_panel(ALU, ALU_D, ALU_L, 5), "block", "aluminum_block")
    save(riveted_panel(TI, TI_D, TI_L, 6), "block", "titanium_block")
    save(launch_pad_top(), "block", "launch_pad_top")
    save(launch_pad_side(), "block", "launch_pad_side")
    save(rocket_body(), "block", "rocket_body")
    save(rocket_window(), "block", "rocket_window")
    save(rocket_fin(), "block", "rocket_fin")
    save(rocket_nozzle(), "block", "rocket_nozzle")
    save(rocket_nozzle_bottom(), "block", "rocket_nozzle_bottom")
    save(rocket_cone(), "block", "rocket_cone")
    save(antenna(), "block", "rocket_antenna")

    save(raw_lump(BAUX_D, BAUX, BAUX_L, 1), "item", "raw_aluminum")
    save(raw_lump(TI_D, TI, TI_L, 2), "item", "raw_titanium")
    save(ingot(ALU_D, ALU, ALU_L), "item", "aluminum_ingot")
    save(ingot(TI_D, TI, TI_L), "item", "titanium_ingot")
    save(plate(ALU_D, ALU, ALU_L), "item", "aluminum_plate")
    save(plate(TI_D, TI, TI_L), "item", "titanium_plate")
    save(vacuum_tube(), "item", "vacuum_tube")
    save(guidance_computer(), "item", "guidance_computer")
    save(nose_cone(), "item", "nose_cone")
    save(hull_segment(), "item", "hull_segment")
    save(rocket_fin_item(), "item", "rocket_fin")
    save(rocket_engine(), "item", "rocket_engine")
    save(canister(False), "item", "empty_fuel_canister")
    save(canister(True), "item", "rocket_fuel_canister")
    save(rocket_item(), "item", "rocket")
    save(suit_icon("helmet"), "item", "space_helmet")
    save(suit_icon("suit"), "item", "space_suit")
    save(suit_icon("leggings"), "item", "space_leggings")
    save(suit_icon("boots"), "item", "space_boots")
    save(suit_layer(), "entity", "equipment", "humanoid", "space_suit")
    save(suit_leggings_layer(), "entity", "equipment", "humanoid_leggings", "space_suit")
    logo().save(os.path.join(ROOT, "retrocosmos_logo.png"))

    # ---- models / blockstates / item definitions ----
    for b in ("bauxite_ore", "deepslate_bauxite_ore", "titanium_ore", "deepslate_titanium_ore",
              "aluminum_block", "titanium_block"):
        cube_all(b)
        simple_blockstate(b)
        item_def(b, f"{MOD}:block/{b}")
    launch_pad_model()
    simple_blockstate("launch_pad")
    item_def("launch_pad", f"{MOD}:block/launch_pad")
    rocket_models()
    generated_item("rocket")

    for i in ("raw_aluminum", "raw_titanium", "aluminum_ingot", "titanium_ingot", "aluminum_plate", "titanium_plate",
              "vacuum_tube", "guidance_computer", "nose_cone", "hull_segment", "rocket_fin", "rocket_engine",
              "empty_fuel_canister", "rocket_fuel_canister",
              "space_helmet", "space_suit", "space_leggings", "space_boots"):
        generated_item(i)

    write_json(os.path.join(ASSETS, "equipment", "space_suit.json"), {"layers": {
        "humanoid": [{"texture": f"{MOD}:space_suit"}],
        "humanoid_leggings": [{"texture": f"{MOD}:space_suit"}]}})

    # ---- loot ----
    loot_ore("bauxite_ore", "raw_aluminum")
    loot_ore("deepslate_bauxite_ore", "raw_aluminum")
    loot_ore("titanium_ore", "raw_titanium")
    loot_ore("deepslate_titanium_ore", "raw_titanium")
    for b in ("aluminum_block", "titanium_block", "launch_pad"):
        loot_self(b)
    loot_rocket()

    # ---- tags ----
    all_blocks = [f"{MOD}:{b}" for b in ("bauxite_ore", "deepslate_bauxite_ore", "titanium_ore", "deepslate_titanium_ore",
                                          "aluminum_block", "titanium_block", "launch_pad", "rocket")]
    tag("block/mineable/pickaxe", all_blocks)
    tag("block/needs_stone_tool", [f"{MOD}:bauxite_ore", f"{MOD}:deepslate_bauxite_ore", f"{MOD}:aluminum_block"])
    tag("block/needs_iron_tool", [f"{MOD}:titanium_ore", f"{MOD}:deepslate_titanium_ore", f"{MOD}:titanium_block",
                                  f"{MOD}:launch_pad"])
    tag("item/repairs_space_suit", [f"{MOD}:titanium_ingot"], namespace=MOD)
    tag("item/head_armor", [f"{MOD}:space_helmet"])
    tag("item/chest_armor", [f"{MOD}:space_suit"])
    tag("item/leg_armor", [f"{MOD}:space_leggings"])
    tag("item/foot_armor", [f"{MOD}:space_boots"])
    # common tags for compatibility with other tech mods
    tag("item/ingots/aluminum", [f"{MOD}:aluminum_ingot"], namespace="c")
    tag("item/ingots/titanium", [f"{MOD}:titanium_ingot"], namespace="c")
    tag("item/raw_materials/aluminum", [f"{MOD}:raw_aluminum"], namespace="c")
    tag("item/raw_materials/titanium", [f"{MOD}:raw_titanium"], namespace="c")
    tag("item/plates/aluminum", [f"{MOD}:aluminum_plate"], namespace="c")
    tag("item/plates/titanium", [f"{MOD}:titanium_plate"], namespace="c")
    tag("block/ores/aluminum", [f"{MOD}:bauxite_ore", f"{MOD}:deepslate_bauxite_ore"], namespace="c")
    tag("block/ores/titanium", [f"{MOD}:titanium_ore", f"{MOD}:deepslate_titanium_ore"], namespace="c")

    # ---- worldgen ----
    ore_feature("ore_bauxite", "bauxite_ore", "deepslate_bauxite_ore", 9, 12, -16, 112)
    ore_feature("ore_titanium", "titanium_ore", "deepslate_titanium_ore", 6, 6, -64, 24, air_discard=0.4)
    write_json(os.path.join(DATA, "neoforge", "biome_modifier", "add_ores.json"), {
        "type": "neoforge:add_features", "biomes": "#minecraft:is_overworld",
        "features": [f"{MOD}:ore_bauxite", f"{MOD}:ore_titanium"], "step": "underground_ores"})

    # ---- recipes ----
    for metal, raw in (("aluminum", "raw_aluminum"), ("titanium", "raw_titanium")):
        cooking(f"{metal}_ingot_from_smelting", "smelting", raw, f"{metal}_ingot", 0.7, 200)
        cooking(f"{metal}_ingot_from_blasting", "blasting", raw, f"{metal}_ingot", 0.7, 100)
        shaped(f"{metal}_plate", ["#", "#"], {"#": f"{metal}_ingot"}, f"{metal}_plate")
        shaped(f"{metal}_block", ["###", "###", "###"], {"#": f"{metal}_ingot"}, f"{metal}_block", category="building")
        shapeless(f"{metal}_ingot_from_block", [f"{metal}_block"], f"{metal}_ingot", count=9)
    cooking("aluminum_ingot_from_smelting_ore", "smelting", "bauxite_ore", "aluminum_ingot", 0.7, 200)
    cooking("titanium_ingot_from_smelting_ore", "smelting", "titanium_ore", "titanium_ingot", 1.0, 200)

    shaped("vacuum_tube", [" G ", "GRG", " C "],
           {"G": "minecraft:glass_pane", "R": "minecraft:redstone", "C": "minecraft:copper_ingot"}, "vacuum_tube", count=2)
    shaped("guidance_computer", ["VVV", "RQR", "TTT"],
           {"V": "vacuum_tube", "R": "minecraft:redstone", "Q": "minecraft:compass", "T": "titanium_plate"},
           "guidance_computer")
    shaped("nose_cone", [" A ", "ARA", "A A"],
           {"A": "aluminum_plate", "R": "minecraft:redstone_torch"}, "nose_cone")
    shaped("hull_segment", ["APA", "AGA", "APA"],
           {"A": "aluminum_plate", "P": "titanium_plate", "G": "minecraft:glass_pane"}, "hull_segment")
    shaped("rocket_fin", ["  A", " AA", "TTA"],
           {"A": "aluminum_plate", "T": "titanium_plate"}, "rocket_fin", count=2)
    shaped("rocket_engine", ["TFT", "TBT", "T T"],
           {"T": "titanium_plate", "F": "minecraft:fire_charge", "B": "minecraft:blast_furnace"}, "rocket_engine")
    shaped("empty_fuel_canister", [" I ", "A A", "AAA"],
           {"I": "minecraft:iron_nugget", "A": "aluminum_plate"}, "empty_fuel_canister", count=2)
    shapeless("rocket_fuel_canister", ["empty_fuel_canister", "minecraft:coal", "minecraft:coal",
                                       "minecraft:gunpowder", "minecraft:blaze_powder"], "rocket_fuel_canister")
    shapeless("rocket_fuel_canister_charcoal", ["empty_fuel_canister", "minecraft:charcoal", "minecraft:charcoal",
                                                "minecraft:gunpowder", "minecraft:blaze_powder"], "rocket_fuel_canister")
    shaped("launch_pad", ["YBY", "TTT", "III"],
           {"Y": "minecraft:yellow_concrete", "B": "minecraft:black_concrete", "T": "titanium_plate",
            "I": "minecraft:iron_block"}, "launch_pad", count=4, category="building")
    shaped("rocket", [" N ", "FGF", "HEH"],
           {"N": "nose_cone", "G": "guidance_computer", "H": "hull_segment", "F": "rocket_fin", "E": "rocket_engine"},
           "rocket")
    shaped("space_helmet", ["TTT", "TGT"],
           {"T": "titanium_plate", "G": "minecraft:glass"}, "space_helmet", category="equipment")
    shaped("space_suit", ["W W", "TVT", "WTW"],
           {"T": "titanium_plate", "W": "minecraft:white_wool", "V": "vacuum_tube"}, "space_suit", category="equipment")
    shaped("space_leggings", ["TWT", "W W", "W W"],
           {"T": "titanium_plate", "W": "minecraft:white_wool"}, "space_leggings", category="equipment")
    shaped("space_boots", ["W W", "T T"],
           {"T": "titanium_plate", "W": "minecraft:white_wool"}, "space_boots", category="equipment")

    # ---- advancements: Stage 1 "Preparation" ----
    advancement("root", "rocket", None, has_item("raw_aluminum", "raw_titanium", "bauxite_ore", "titanium_ore"),
                background="minecraft:gui/advancements/backgrounds/stone")
    advancement("aluminum", "aluminum_ingot", "root", has_item("aluminum_ingot"))
    advancement("titanium", "titanium_ingot", "aluminum", has_item("titanium_ingot"))
    advancement("vacuum_tube", "vacuum_tube", "aluminum", has_item("vacuum_tube"))
    advancement("guidance_computer", "guidance_computer", "vacuum_tube", has_item("guidance_computer"))
    advancement("rocket_engine", "rocket_engine", "titanium", has_item("rocket_engine"))
    advancement("fuel", "rocket_fuel_canister", "aluminum", has_item("rocket_fuel_canister"))
    advancement("space_suit", "space_helmet", "titanium",
                {f"has_{p}": {"trigger": "minecraft:inventory_changed", "conditions": {"items": [{"items": ing(p)}]}}
                 for p in ("space_helmet", "space_suit", "space_leggings", "space_boots")}, frame="goal")
    advancement("launch_pad", "launch_pad", "titanium", has_item("launch_pad"))
    advancement("rocket", "rocket", "rocket_engine", has_item("rocket"), frame="goal")
    advancement("ready_for_launch", "rocket", "rocket",
                {"checklist_passed": {"trigger": "minecraft:impossible"}}, frame="challenge")

    # ---- lang ----
    write_lang()


EN = {
    "itemGroup.retrocosmos.main": "Retro Cosmos",
    "block.retrocosmos.bauxite_ore": "Bauxite Ore",
    "block.retrocosmos.deepslate_bauxite_ore": "Deepslate Bauxite Ore",
    "block.retrocosmos.titanium_ore": "Titanium Ore",
    "block.retrocosmos.deepslate_titanium_ore": "Deepslate Titanium Ore",
    "block.retrocosmos.aluminum_block": "Block of Aluminum",
    "block.retrocosmos.titanium_block": "Block of Titanium",
    "block.retrocosmos.launch_pad": "Launch Pad",
    "block.retrocosmos.rocket": "Rocket \"Zarya-1\"",
    "item.retrocosmos.raw_aluminum": "Raw Aluminum",
    "item.retrocosmos.raw_titanium": "Raw Titanium",
    "item.retrocosmos.aluminum_ingot": "Aluminum Ingot",
    "item.retrocosmos.titanium_ingot": "Titanium Ingot",
    "item.retrocosmos.aluminum_plate": "Aluminum Plate",
    "item.retrocosmos.titanium_plate": "Titanium Plate",
    "item.retrocosmos.vacuum_tube": "Vacuum Tube",
    "item.retrocosmos.guidance_computer": "Analog Guidance Computer",
    "item.retrocosmos.nose_cone": "Nose Cone",
    "item.retrocosmos.hull_segment": "Hull Segment",
    "item.retrocosmos.rocket_fin": "Rocket Fin",
    "item.retrocosmos.rocket_engine": "Rocket Engine",
    "item.retrocosmos.empty_fuel_canister": "Empty Fuel Canister",
    "item.retrocosmos.rocket_fuel_canister": "Rocket Fuel Canister",
    "item.retrocosmos.space_helmet": "Space Helmet",
    "item.retrocosmos.space_suit": "Space Suit",
    "item.retrocosmos.space_leggings": "Space Suit Trousers",
    "item.retrocosmos.space_boots": "Magnetic Boots",
    "message.retrocosmos.rocket.fueled": "Fuel tanks: %s / %s",
    "message.retrocosmos.rocket.fuel_full": "Fuel tanks are full!",
    "message.retrocosmos.checklist.title": "=== PRE-FLIGHT CHECKLIST ===",
    "message.retrocosmos.checklist.pad": "Rocket stands on a launch pad",
    "message.retrocosmos.checklist.fuel": "Fuel tanks filled (%s / %s)",
    "message.retrocosmos.checklist.suit": "Cosmonaut wears the full space suit",
    "message.retrocosmos.checklist.ready": "All systems nominal. Ready for launch!",
    "message.retrocosmos.checklist.stage2": "Mission control is still calculating trajectories to other worlds... (Stage 2)",
    "message.retrocosmos.checklist.not_ready": "Launch aborted: checklist incomplete.",
    "advancements.retrocosmos.root.title": "Retro Cosmos: Preparation",
    "advancements.retrocosmos.root.description": "Find ore for the space age: bauxite or titanium",
    "advancements.retrocosmos.aluminum.title": "Winged Metal",
    "advancements.retrocosmos.aluminum.description": "Smelt an aluminum ingot",
    "advancements.retrocosmos.titanium.title": "Stronger Than Steel",
    "advancements.retrocosmos.titanium.description": "Smelt a titanium ingot from deep ore",
    "advancements.retrocosmos.vacuum_tube.title": "The Warm Glow",
    "advancements.retrocosmos.vacuum_tube.description": "Craft a vacuum tube",
    "advancements.retrocosmos.guidance_computer.title": "Electronic Brain",
    "advancements.retrocosmos.guidance_computer.description": "Assemble an analog guidance computer",
    "advancements.retrocosmos.rocket_engine.title": "Ignition Sequence",
    "advancements.retrocosmos.rocket_engine.description": "Build a rocket engine",
    "advancements.retrocosmos.fuel.title": "Atomic-Age Kerosene",
    "advancements.retrocosmos.fuel.description": "Fill a rocket fuel canister",
    "advancements.retrocosmos.space_suit.title": "Dressed for the Void",
    "advancements.retrocosmos.space_suit.description": "Obtain every piece of the space suit",
    "advancements.retrocosmos.launch_pad.title": "Cosmodrome",
    "advancements.retrocosmos.launch_pad.description": "Craft a launch pad",
    "advancements.retrocosmos.rocket.title": "Zarya-1",
    "advancements.retrocosmos.rocket.description": "Assemble your first rocket",
    "advancements.retrocosmos.ready_for_launch.title": "Ready for Launch!",
    "advancements.retrocosmos.ready_for_launch.description": "Pass the pre-flight checklist: rocket on a pad, tanks full, suit on",
}

RU = {
    "itemGroup.retrocosmos.main": "Ретрокосмос",
    "block.retrocosmos.bauxite_ore": "Бокситовая руда",
    "block.retrocosmos.deepslate_bauxite_ore": "Глубинносланцевая бокситовая руда",
    "block.retrocosmos.titanium_ore": "Титановая руда",
    "block.retrocosmos.deepslate_titanium_ore": "Глубинносланцевая титановая руда",
    "block.retrocosmos.aluminum_block": "Алюминиевый блок",
    "block.retrocosmos.titanium_block": "Титановый блок",
    "block.retrocosmos.launch_pad": "Стартовая площадка",
    "block.retrocosmos.rocket": "Ракета «Заря-1»",
    "item.retrocosmos.raw_aluminum": "Необработанный алюминий",
    "item.retrocosmos.raw_titanium": "Необработанный титан",
    "item.retrocosmos.aluminum_ingot": "Алюминиевый слиток",
    "item.retrocosmos.titanium_ingot": "Титановый слиток",
    "item.retrocosmos.aluminum_plate": "Алюминиевая пластина",
    "item.retrocosmos.titanium_plate": "Титановая пластина",
    "item.retrocosmos.vacuum_tube": "Радиолампа",
    "item.retrocosmos.guidance_computer": "Аналоговый вычислитель наведения",
    "item.retrocosmos.nose_cone": "Головной обтекатель",
    "item.retrocosmos.hull_segment": "Секция корпуса",
    "item.retrocosmos.rocket_fin": "Стабилизатор ракеты",
    "item.retrocosmos.rocket_engine": "Ракетный двигатель",
    "item.retrocosmos.empty_fuel_canister": "Пустая топливная канистра",
    "item.retrocosmos.rocket_fuel_canister": "Канистра ракетного топлива",
    "item.retrocosmos.space_helmet": "Гермошлем",
    "item.retrocosmos.space_suit": "Скафандр",
    "item.retrocosmos.space_leggings": "Штаны скафандра",
    "item.retrocosmos.space_boots": "Магнитные ботинки",
    "message.retrocosmos.rocket.fueled": "Топливные баки: %s / %s",
    "message.retrocosmos.rocket.fuel_full": "Баки полны!",
    "message.retrocosmos.checklist.title": "=== ПРЕДСТАРТОВАЯ ПРОВЕРКА ===",
    "message.retrocosmos.checklist.pad": "Ракета установлена на стартовую площадку",
    "message.retrocosmos.checklist.fuel": "Баки заправлены (%s / %s)",
    "message.retrocosmos.checklist.suit": "Космонавт в полном скафандре",
    "message.retrocosmos.checklist.ready": "Все системы в норме. К старту готов!",
    "message.retrocosmos.checklist.stage2": "ЦУП ещё рассчитывает траектории к другим мирам... (Этап 2)",
    "message.retrocosmos.checklist.not_ready": "Старт отменён: проверка не пройдена.",
    "advancements.retrocosmos.root.title": "Ретрокосмос: Подготовка",
    "advancements.retrocosmos.root.description": "Найдите руду космической эры: боксит или титан",
    "advancements.retrocosmos.aluminum.title": "Крылатый металл",
    "advancements.retrocosmos.aluminum.description": "Выплавьте алюминиевый слиток",
    "advancements.retrocosmos.titanium.title": "Прочнее стали",
    "advancements.retrocosmos.titanium.description": "Выплавьте титан из глубинной руды",
    "advancements.retrocosmos.vacuum_tube.title": "Тёплый свет лампы",
    "advancements.retrocosmos.vacuum_tube.description": "Соберите радиолампу",
    "advancements.retrocosmos.guidance_computer.title": "Электронный мозг",
    "advancements.retrocosmos.guidance_computer.description": "Соберите аналоговый вычислитель наведения",
    "advancements.retrocosmos.rocket_engine.title": "Ключ на старт",
    "advancements.retrocosmos.rocket_engine.description": "Постройте ракетный двигатель",
    "advancements.retrocosmos.fuel.title": "Керосин атомной эры",
    "advancements.retrocosmos.fuel.description": "Наполните канистру ракетного топлива",
    "advancements.retrocosmos.space_suit.title": "Одет для пустоты",
    "advancements.retrocosmos.space_suit.description": "Добудьте все части скафандра",
    "advancements.retrocosmos.launch_pad.title": "Космодром",
    "advancements.retrocosmos.launch_pad.description": "Создайте стартовую площадку",
    "advancements.retrocosmos.rocket.title": "«Заря-1»",
    "advancements.retrocosmos.rocket.description": "Соберите свою первую ракету",
    "advancements.retrocosmos.ready_for_launch.title": "Поехали!",
    "advancements.retrocosmos.ready_for_launch.description": "Пройдите предстартовую проверку: ракета на площадке, баки полны, скафандр надет",
}


def write_lang():
    assert EN.keys() == RU.keys()
    write_json(os.path.join(ASSETS, "lang", "en_us.json"), EN)
    write_json(os.path.join(ASSETS, "lang", "ru_ru.json"), RU)


if __name__ == "__main__":
    main()
