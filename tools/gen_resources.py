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
# Palette: 1950s-60s American "atomic age" / Googie / Space Race retro-futurism
# (chrome, white & silver rockets, cherry red, turquoise, cream, navy stars)
# ----------------------------------------------------------------------------
CREAM = (240, 232, 208)
CREAM_D = (206, 194, 164)
WHITE = (242, 242, 238)
WHITE_D = (208, 208, 204)
WHITE_DD = (176, 178, 176)
RED = (208, 44, 48)
RED_D = (142, 28, 34)
RED_L = (236, 92, 86)
NAVY = (42, 62, 118)
NAVY_L = (78, 104, 170)
TEAL = (72, 190, 182)
TEAL_D = (38, 120, 118)
TEAL_L = (140, 226, 216)
ORANGE = (240, 150, 50)
ORANGE_L = (255, 206, 110)
CHROME = (204, 212, 220)
CHROME_D = (132, 142, 154)
CHROME_L = (244, 248, 252)
STEEL = (92, 98, 108)
STEEL_D = (58, 62, 70)
YELLOW = (236, 196, 52)
BLACK = (34, 32, 36)
GLASS = (150, 210, 230)
GLASS_L = (220, 244, 252)
VISOR = (28, 48, 78)
VISOR_L = (62, 110, 150)
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


def star(img, cx, cy, color):
    """Small 5-point-ish star (plus with corners) centred on (cx, cy)."""
    px(img, [(cx, cy - 1), (cx - 1, cy), (cx, cy), (cx + 1, cy), (cx, cy + 1), (cx - 1, cy + 1), (cx + 1, cy + 1)], color)


def launch_pad_top():
    img = new()
    noise_fill(img, STEEL, 4, 99)
    # hazard border (yellow / black)
    for y in range(16):
        for x in range(16):
            if x < 2 or y < 2 or x > 13 or y > 13:
                px(img, [(x, y)], YELLOW if ((x + y) // 2) % 2 == 0 else BLACK)
    # white target ring with a red star in the middle (launch complex marking)
    d = ImageDraw.Draw(img)
    d.ellipse((3, 3, 12, 12), outline=rgba(WHITE))
    d.ellipse((5, 5, 10, 10), fill=rgba(RED))
    star(img, 7, 7, WHITE)
    px(img, [(8, 7), (8, 8), (7, 8)], WHITE)
    return img


def launch_pad_side():
    img = new()
    noise_fill(img, STEEL_D, 5, 98)
    for x in range(16):
        for y in range(0, 3):
            px(img, [(x, y)], YELLOW if ((x + y) // 2) % 2 == 0 else BLACK)
        px(img, [(x, 3)], STEEL)
    # red / white chevron stripe
    for x in range(16):
        px(img, [(x, 9)], WHITE if (x // 4) % 2 == 0 else RED)
        px(img, [(x, 10)], WHITE if (x // 4) % 2 == 0 else RED)
    for (x, y) in [(2, 6), (7, 6), (12, 6), (2, 13), (7, 13), (12, 13)]:
        px(img, [(x, y), (x + 1, y)], CHROME_D)
    return img


def rocket_body():
    """Sleek silver-white hull with panel seams, a cherry-red band and a navy star."""
    img = new()
    noise_fill(img, WHITE, 2, 5)
    for y in range(16):
        px(img, [(0, y), (1, y)], WHITE_D)
        px(img, [(14, y), (15, y)], WHITE_D)
        px(img, [(15, y)], WHITE_DD)
        px(img, [(2, y)], CHROME_L)
    # horizontal panel seam
    for x in range(16):
        px(img, [(x, 4)], WHITE_D)
    # cherry red racing band with chrome trim
    for x in range(16):
        px(img, [(x, 10)], CHROME)
        for y in (11, 12, 13):
            px(img, [(x, y)], RED)
        px(img, [(x, 13)], RED_D)
        px(img, [(x, 14)], CHROME)
    star(img, 7, 7, NAVY)
    return img


def rocket_window():
    img = rocket_body()
    d = ImageDraw.Draw(img)
    # chrome porthole, dark glass with a glint
    d.ellipse((4, 2, 11, 9), fill=rgba(CHROME), outline=rgba(CHROME_D))
    d.ellipse((5, 3, 10, 8), fill=rgba(VISOR))
    px(img, [(6, 4), (7, 4), (6, 5)], GLASS_L)
    px(img, [(8, 6), (9, 7)], VISOR_L)
    return img


def rocket_fin():
    img = new()
    noise_fill(img, RED, 4, 11)
    for y in range(16):
        for x in range(16):
            if y < 4:
                px(img, [(x, y)], RED_L)
            elif y > 12:
                px(img, [(x, y)], RED_D)
    for x in range(16):
        px(img, [(x, 15)], CHROME)
    return img


def rocket_nozzle():
    img = new()
    noise_fill(img, STEEL, 6, 12)
    for x in range(16):
        px(img, [(x, 0)], CHROME)
        px(img, [(x, 15)], STEEL_D)
    for y in range(16):
        if y % 3 == 1:
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
    """Projected texture: rows 0-5 chrome tip, white, red band, white skirt."""
    img = new()
    noise_fill(img, WHITE, 2, 14)
    for y in range(16):
        for x in range(16):
            if y < 6:
                c = CHROME_L if (x + y) % 5 == 0 else CHROME
                if x in (0, 15):
                    c = CHROME_D
                px(img, [(x, y)], c)
            elif 9 <= y <= 12:
                px(img, [(x, y)], RED if y != 12 else RED_D)
            elif y == 6:
                px(img, [(x, y)], CHROME_D)
        px(img, [(0, y), (15, y)], WHITE_D if y >= 6 else CHROME_D)
    return img


def rocket_chrome():
    img = new()
    noise_fill(img, CHROME, 5, 16)
    for y in range(16):
        for x in range(16):
            if (x + y) % 6 == 0:
                px(img, [(x, y)], CHROME_L)
            elif (x + y) % 6 == 3:
                px(img, [(x, y)], CHROME_D)
    return img


def antenna():
    img = rocket_chrome()
    for x in range(16):
        px(img, [(x, 0), (x, 1)], RED)
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
    """Chrome needle nose with a red band at the base."""
    img = new()
    for y in range(2, 14):
        half = (y - 1) // 2
        for x in range(8 - half, 8 + half):
            px(img, [(x, y)], RED if y >= 11 else CHROME)
        px(img, [(8 - half, y)], RED_L if y >= 11 else CHROME_L)
        if y < 11:
            px(img, [(8 + half - 1, y)], CHROME_D)
    for x in range(2, 14):
        px(img, [(x, 13)], RED_D)
    px(img, [(7, 0), (7, 1)], CHROME_D)
    outline(img, STEEL_D)
    return img


def hull_segment():
    img = new()
    for y in range(1, 15):
        for x in range(4, 12):
            px(img, [(x, y)], WHITE)
        px(img, [(4, y)], CHROME_L)
        px(img, [(10, y)], WHITE_D)
        px(img, [(11, y)], WHITE_DD)
    d = ImageDraw.Draw(img)
    d.ellipse((5, 3, 10, 8), fill=rgba(CHROME), outline=rgba(CHROME_D))
    d.ellipse((6, 4, 9, 7), fill=rgba(VISOR))
    px(img, [(6, 4)], GLASS_L)
    for x in range(4, 12):
        px(img, [(x, 10)], CHROME)
        px(img, [(x, 11), (x, 12)], RED)
        px(img, [(x, 13)], CHROME)
    outline(img, STEEL_D)
    return img


def rocket_fin_item():
    """Swept-back cherry-red fin with a chrome trailing edge."""
    img = new()
    for y in range(1, 15):
        w = min(11, (y + 1) * 3 // 4 + 1)
        for x in range(3, 3 + w):
            px(img, [(x, y)], RED)
        px(img, [(3, y)], RED_L)
        px(img, [(3 + w - 1, y)], RED_D)
    for x in range(3, 14):
        px(img, [(x, 14)], CHROME)
    star(img, 6, 10, WHITE)
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
    # label: white with a navy star (full) or a dashed "empty" mark
    d.rectangle((4, 7, 11, 11), fill=rgba(WHITE))
    if full:
        star(img, 7, 9, NAVY)
        px(img, [(10, 8), (10, 10)], RED)
    else:
        px(img, [(5, 9), (7, 9), (9, 9)], CHROME_D)
    outline(img, BLACK)
    return img


def rocket_item():
    """Raygun-gothic silhouette: chrome needle nose, white hull, red band, swept red fins."""
    img = new()
    # chrome needle & nose
    px(img, [(7, 0)], CHROME_D)
    px(img, [(7, 1), (7, 2), (8, 2)], CHROME_L)
    px(img, [(6, 3), (7, 3), (8, 3), (9, 3)], CHROME)
    px(img, [(9, 3)], CHROME_D)
    # body
    for y in range(4, 13):
        for x in range(6, 10):
            px(img, [(x, y)], WHITE)
        px(img, [(6, y)], CHROME_L)
        px(img, [(9, y)], WHITE_D)
    # porthole
    px(img, [(7, 5), (8, 5), (7, 6), (8, 6)], VISOR)
    px(img, [(7, 5)], GLASS_L)
    # red band
    for x in range(6, 10):
        px(img, [(x, 9)], RED)
        px(img, [(x, 10)], RED_D)
    # swept fins
    px(img, [(5, 8), (5, 9), (5, 10), (4, 10), (5, 11), (4, 11), (3, 11), (5, 12), (4, 12), (3, 12), (2, 12),
             (4, 13), (3, 13), (2, 13)], RED)
    px(img, [(10, 8), (10, 9), (10, 10), (11, 10), (10, 11), (11, 11), (12, 11), (10, 12), (11, 12), (12, 12),
             (13, 12), (11, 13), (12, 13), (13, 13)], RED)
    px(img, [(5, 8), (10, 8), (2, 13), (13, 13)], RED_L)
    # engine bell & flame
    px(img, [(6, 13), (9, 13)], STEEL_D)
    px(img, [(7, 13), (8, 13)], STEEL)
    px(img, [(6, 14), (7, 14), (8, 14), (9, 14)], ORANGE)
    px(img, [(7, 15), (8, 15)], ORANGE_L)
    outline(img, BLACK)
    return img


def suit_icon(kind):
    """Space suit icons: white suit, red gloves / boots, chrome rings, turquoise chest unit."""
    img = new()
    d = ImageDraw.Draw(img)
    if kind == "helmet":
        # white dome, chrome neck ring, dark faceplate with a glint
        d.ellipse((2, 1, 13, 12), fill=rgba(WHITE), outline=rgba(WHITE_D))
        d.rectangle((2, 11, 13, 14), fill=rgba(CHROME), outline=rgba(CHROME_D))
        d.rectangle((4, 4, 11, 10), fill=rgba(VISOR))
        px(img, [(4, 4), (11, 4), (4, 10), (11, 10)], WHITE)
        px(img, [(5, 5), (6, 5), (5, 6)], GLASS_L)
        px(img, [(9, 8), (10, 8), (10, 7)], VISOR_L)
        for x in range(7, 9):
            px(img, [(x, 1), (x, 2)], RED)
        px(img, [(7, 13), (8, 13)], RED)
    elif kind == "suit":
        d.rectangle((4, 2, 11, 14), fill=rgba(WHITE))
        d.rectangle((1, 3, 3, 11), fill=rgba(WHITE))
        d.rectangle((12, 3, 14, 11), fill=rgba(WHITE))
        d.rectangle((6, 1, 9, 2), fill=rgba(CHROME))
        # chest control unit
        d.rectangle((5, 4, 10, 8), fill=rgba(TEAL), outline=rgba(TEAL_D))
        px(img, [(6, 5)], RED)
        px(img, [(9, 5)], (120, 230, 120))
        px(img, [(6, 7), (7, 7), (8, 7), (9, 7)], CREAM)
        # belt
        for x in range(4, 12):
            px(img, [(x, 11)], CHROME)
        px(img, [(7, 11), (8, 11)], RED)
        # shoulder bands and red gloves
        px(img, [(1, 3), (2, 3), (3, 3), (12, 3), (13, 3), (14, 3)], TEAL)
        px(img, [(1, 9), (2, 9), (3, 9), (12, 9), (13, 9), (14, 9)], CHROME)
        d.rectangle((1, 10, 3, 12), fill=rgba(RED))
        d.rectangle((12, 10, 14, 12), fill=rgba(RED))
        px(img, [(4, 3), (4, 13), (11, 13)], WHITE_D)
    elif kind == "leggings":
        d.rectangle((4, 1, 11, 3), fill=rgba(WHITE))
        for x in range(4, 12):
            px(img, [(x, 2)], CHROME)
        px(img, [(7, 2), (8, 2)], RED)
        d.rectangle((4, 4, 7, 14), fill=rgba(WHITE))
        d.rectangle((8, 4, 11, 14), fill=rgba(WHITE))
        for y in range(4, 15):
            px(img, [(7, y)], WHITE_D)
            px(img, [(8, y)], WHITE_DD)
        px(img, [(5, 9), (6, 9), (9, 9), (10, 9), (5, 10), (6, 10), (9, 10), (10, 10)], TEAL)
        for y in range(4, 9):
            px(img, [(4, y), (11, y)], RED)
    elif kind == "boots":
        d.rectangle((2, 5, 6, 13), fill=rgba(RED))
        d.rectangle((9, 5, 13, 13), fill=rgba(RED))
        for x in range(2, 7):
            px(img, [(x, 5)], CHROME)
            px(img, [(x + 7, 5)], CHROME)
        d.rectangle((1, 12, 7, 14), fill=rgba(CHROME_D))
        d.rectangle((8, 12, 14, 14), fill=rgba(CHROME_D))
        px(img, [(3, 7), (3, 8), (3, 9), (10, 7), (10, 8), (10, 9)], RED_L)
        px(img, [(2, 13), (3, 13), (9, 13), (10, 13)], CHROME)
    outline(img, STEEL_D)
    return img


# ----------------------------------------------------------------------------
# Armor (equipment) layer textures, 64x32 humanoid UV layout
# ----------------------------------------------------------------------------

# Face indices of a cuboid net: 0 top, 1 bottom, 2 right (outer side of right limbs),
# 3 front, 4 left, 5 back.
TOP, BOTTOM, RIGHT, FRONT, LEFT, BACK = range(6)
FACE_SHADE = {TOP: 14, BOTTOM: -34, RIGHT: -14, FRONT: 0, LEFT: -14, BACK: -8}
GREEN_LAMP = (120, 230, 120)


def shade(c, delta):
    return tuple(max(0, min(255, v + delta)) for v in c)


def fill_box(img, u, v, w, h, d, color_fn, shading=True):
    """Fills the UV net of a cuboid (w x h x d) whose net starts at (u, v).

    color_fn(face, x, y, w, h) returns an RGB colour or None (transparent).
    Faces get consistent lighting: top lighter, bottom darkest, sides darker than the front.
    Armour is rendered with a cutout render type, so every pixel is either fully opaque or
    fully transparent - never semi-transparent.
    """
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
                c = color_fn(idx, x - x0, y - y0, rw, rh)
                if c is None:
                    img.putpixel((x, y), (0, 0, 0, 0))
                else:
                    img.putpixel((x, y), rgba(shade(c, FACE_SHADE[idx]) if shading else c))


def front_dist(face, x, w):
    """Distance of column x from the front edge on a side face (0 = touches the front face)."""
    return (w - 1 - x) if face == RIGHT else x


def suit_layer():
    """Outer layer (64x32): helmet (head + hat overlay), suit (body + arms), boots (legs)."""
    img = new(64, 32)

    # --- helmet: white shell, red top stripe, dark faceplate with a glint, chrome neck ring
    def helmet(face, x, y, w, h):
        if face == BOTTOM:
            return CHROME_D
        if face == TOP:
            return RED if x in (3, 4) else WHITE
        if y == 6:
            return CHROME
        if y == 7:
            return CHROME_D
        if face == FRONT:
            if y == 0:
                return RED if x in (3, 4) else WHITE
            if x in (0, 7):
                return CHROME
            if (x, y) in ((1, 1), (2, 1), (1, 2)):
                return GLASS_L
            if (x, y) in ((2, 2), (3, 1)):
                return VISOR_L
            if (x, y) in ((5, 4), (6, 4), (6, 3)):
                return VISOR_L
            return VISOR
        if face == BACK:
            if x in (3, 4) and y <= 2:
                return RED
            if 2 <= x <= 5 and y in (3, 5):
                return CHROME_D
            if x in (0, 7):
                return WHITE_D
            return WHITE
        # sides: comms earpiece (chrome disc with a red light) behind the faceplate
        fd = front_dist(face, x, w)
        if 2 <= fd <= 4 and 2 <= y <= 4:
            return RED if (fd, y) == (3, 3) else CHROME
        if fd == 0 and y <= 5:
            return CHROME_D
        return WHITE

    fill_box(img, 0, 0, 8, 8, 8, helmet)

    # --- hat overlay (rendered 0.5px further out): only the raised chrome faceplate rim,
    #     everything else transparent so the shell and the visor below show through
    def rim(face, x, y, w, h):
        if face == FRONT:
            if y == 0:
                return CHROME_L
            if y == 6:
                return CHROME
            if x in (0, 7) and y < 6:
                return CHROME
            return None
        if face == TOP:
            return CHROME_L if y == h - 1 else None
        if face in (RIGHT, LEFT):
            fd = front_dist(face, x, w)
            if fd == 0 and y <= 6:
                return CHROME
            if fd == 1 and y == 3:
                return RED
            return None
        return None

    fill_box(img, 32, 0, 8, 8, 8, rim)

    # --- suit body: collar ring, turquoise chest control unit, chrome belt, life-support pack
    def body(face, x, y, w, h):
        if face == TOP:
            return CHROME if 2 <= x <= 5 else WHITE
        if face == BOTTOM:
            return WHITE_D
        if y == 0:
            return CHROME_D if (face in (FRONT, BACK) and x in (0, 7)) else CHROME
        if y == 8:
            if face == FRONT and x in (3, 4):
                return RED
            return CHROME
        if y == 9:
            return RED_D if face == FRONT and x in (3, 4) else CHROME_D
        if face == FRONT:
            if 2 <= x <= 5 and 2 <= y <= 6:
                if x in (2, 5) or y in (2, 6):
                    return TEAL_D
                if y == 3:
                    return RED if x == 3 else GREEN_LAMP
                if y == 4:
                    return TEAL_L
                return CREAM
            if y == 1 and x in (0, 1, 6, 7):
                return RED
            if x in (0, 7):
                return WHITE_D
            return WHITE
        if face == BACK:
            if 1 <= x <= 6 and 1 <= y <= 7:
                if x in (1, 6) or y in (1, 7):
                    return CHROME_D
                if y == 2:
                    return RED
                if y == 7:
                    return CHROME_D
                return CHROME_L if x in (2, 5) else CHROME
            if x in (0, 7):
                return WHITE_D
            return WHITE
        # sides: an orange oxygen hose running from the back pack to the chest unit
        fd = front_dist(face, x, w)
        if fd == 1 and 2 <= y <= 6:
            return ORANGE_L if y == 2 else ORANGE
        if fd == 3:
            return WHITE_D
        return WHITE

    fill_box(img, 16, 16, 8, 12, 4, body)

    # --- arms: turquoise shoulder band, stars & stripes patch on the outer side,
    #     chrome wrist ring, cherry-red gloves
    def arm(face, x, y, w, h):
        if face == TOP:
            return TEAL
        if face == BOTTOM:
            return RED_D
        if y == 0:
            return TEAL
        if y == 1:
            return TEAL_D
        if y == 8:
            return CHROME
        if y >= 9:
            return RED_L if (face == FRONT and y == 9 and x == 0) else RED
        if face == RIGHT and 2 <= y <= 5:
            patch = [[NAVY, NAVY, RED, RED], [NAVY, NAVY, WHITE, WHITE], [RED, RED, RED, RED], [WHITE] * 4]
            c = patch[y - 2][x]
            return NAVY_L if (x, y) == (1, 3) else c
        if face in (FRONT, BACK) and x == 3:
            return WHITE_D
        return WHITE

    fill_box(img, 40, 16, 4, 12, 4, arm)

    # --- boots (legs region of the outer layer): only the bottom four rows are opaque
    def boot(face, x, y, w, h):
        if face == TOP:
            return None
        if face == BOTTOM:
            return RED_D
        if y < 8:
            return None
        if y == 8:
            return CHROME
        if y == 11:
            return RED_D
        if face == FRONT and y == 9 and x == 0:
            return RED_L
        return RED

    fill_box(img, 0, 16, 4, 12, 4, boot)
    return img


def suit_leggings_layer():
    """Inner layer (64x32): trousers - waist with belt on the body, white legs with a red
    racing stripe on the outer side and turquoise knee pads."""
    img = new(64, 32)

    def waist(face, x, y, w, h):
        if face == TOP:
            return None
        if face == BOTTOM:
            return WHITE_D
        if y < 7:
            return None
        if y == 8:
            return RED if (face == FRONT and x in (3, 4)) else CHROME
        if y == 9:
            return RED_D if (face == FRONT and x in (3, 4)) else CHROME_D
        if face in (FRONT, BACK) and x in (0, 7):
            return WHITE_D
        return WHITE

    fill_box(img, 16, 16, 8, 12, 4, waist)

    def leg(face, x, y, w, h):
        if face == TOP:
            return WHITE_D
        if face == BOTTOM:
            return WHITE_DD
        if face == RIGHT and x == 1 and y <= 8:
            return RED
        if face == FRONT and y in (5, 6):
            return TEAL_D if y == 6 else TEAL
        if face == BACK and x == 3:
            return WHITE_D
        if face == LEFT and x == 3:
            return WHITE_D
        return WHITE

    fill_box(img, 0, 16, 4, 12, 4, leg)
    return img


def logo():
    """Googie-style mod logo: turquoise sky, cream starburst, a silver rocket with red fins."""
    import math
    img = Image.new("RGBA", (128, 128), rgba(TEAL))
    d = ImageDraw.Draw(img)
    cx, cy = 64, 64
    # starburst rays
    for i in range(16):
        a = i * math.pi / 8
        r1, r2 = 30, 90
        d.line((cx + r1 * math.cos(a), cy + r1 * math.sin(a), cx + r2 * math.cos(a), cy + r2 * math.sin(a)),
               fill=rgba(CREAM), width=3 if i % 2 == 0 else 1)
    d.ellipse((cx - 34, cy - 34, cx + 34, cy + 34), fill=rgba(NAVY), outline=rgba(CREAM), width=3)
    rnd = random.Random(42)
    for _ in range(30):
        x, y = rnd.randrange(cx - 30, cx + 30), rnd.randrange(cy - 30, cy + 30)
        if (x - cx) ** 2 + (y - cy) ** 2 < 28 ** 2:
            img.putpixel((x, y), rgba(WHITE))
    # boomerang swoosh (orbit) around the globe
    d.arc((cx - 52, cy - 16, cx + 52, cy + 16), start=150, end=390, fill=rgba(RED), width=4)
    # rocket (tilted to the upper right, drawn as polygons)
    body = [(52, 92), (60, 40), (70, 34), (80, 40), (86, 92), (69, 100)]
    d.polygon(body, fill=rgba(WHITE), outline=rgba(WHITE_DD))
    d.polygon([(60, 40), (70, 22), (80, 40)], fill=rgba(CHROME), outline=rgba(CHROME_D))
    d.polygon([(56, 76), (82, 76), (84, 86), (54, 86)], fill=rgba(RED))
    d.ellipse((63, 46, 77, 60), fill=rgba(CHROME), outline=rgba(CHROME_D))
    d.ellipse((66, 49, 74, 57), fill=rgba(VISOR))
    img.putpixel((68, 51), rgba(GLASS_L))
    d.polygon([(54, 70), (40, 100), (54, 94)], fill=rgba(RED), outline=rgba(RED_D))
    d.polygon([(84, 70), (98, 100), (84, 94)], fill=rgba(RED), outline=rgba(RED_D))
    d.polygon([(60, 100), (78, 100), (74, 108), (64, 108)], fill=rgba(STEEL))
    d.polygon([(62, 108), (76, 108), (69, 124)], fill=rgba(ORANGE))
    d.polygon([(66, 108), (72, 108), (69, 118)], fill=rgba(ORANGE_L))
    d.line((70, 10, 70, 22), fill=rgba(CHROME_D), width=2)
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


def swept_fin(axis, side):
    """Three stepped slabs forming a swept-back fin: tall at the hull, short at the tip."""
    steps = [(2, 10), (1, 7), (0, 4)]  # (offset from the block edge, height)
    out = []
    for off, height in steps:
        lo = off if side < 0 else 15 - off
        hi = lo + 1
        if axis == "x":
            out.append(element((lo, 0, 7.5), (hi, height, 8.5), "#fin"))
        else:
            out.append(element((7.5, 0, lo), (8.5, height, hi), "#fin"))
    return out


def rocket_models():
    """Raygun-gothic 'Liberty I': chrome needle nose, white hull with red band, swept red fins.

    Block textures are projected onto the elements (an element's face samples the texture at
    its own block coordinates), so the cone texture is painted as a vertical strip:
    chrome tip, white, red band."""
    t = {"body": f"{MOD}:block/rocket_body", "window": f"{MOD}:block/rocket_window",
         "fin": f"{MOD}:block/rocket_fin", "nozzle": f"{MOD}:block/rocket_nozzle",
         "nozzle_bottom": f"{MOD}:block/rocket_nozzle_bottom", "cone": f"{MOD}:block/rocket_cone",
         "antenna": f"{MOD}:block/rocket_antenna", "chrome": f"{MOD}:block/rocket_chrome"}
    chrome_caps = {"up": "#chrome", "down": "#chrome"}
    bottom = {
        "textures": dict(t, particle=t["body"]),
        "elements": [
            element((3, 3, 3), (13, 16, 13), "#body", faces=("north", "south", "east", "west", "down"),
                    face_tex={"down": "#chrome"}),
            element((4, 1, 4), (12, 3, 12), "#chrome", faces=("north", "south", "east", "west", "down")),
            element((5, 0, 5), (11, 1, 11), "#nozzle", face_tex={"down": "#nozzle_bottom"}),
            *swept_fin("x", -1), *swept_fin("x", 1), *swept_fin("z", -1), *swept_fin("z", 1),
        ],
    }
    middle = {
        "textures": dict(t, particle=t["body"]),
        "elements": [
            element((3, 0, 3), (13, 16, 13), "#body", faces=("north", "south", "east", "west"),
                    face_tex={"north": "#window", "south": "#window"}),
            # porthole mounting plates, raised half a pixel off the hull
            element((4, 7, 2.5), (12, 14, 3), "#chrome", faces=("north", "up", "down", "east", "west"),
                    face_tex={"north": "#window"}),
            element((4, 7, 13), (12, 14, 13.5), "#chrome", faces=("south", "up", "down", "east", "west"),
                    face_tex={"south": "#window"}),
        ],
    }
    top = {
        "textures": dict(t, particle=t["cone"]),
        "elements": [
            element((3, 0, 3), (13, 3, 13), "#body", faces=("north", "south", "east", "west", "up"),
                    face_tex={"up": "#chrome"}),
            element((4, 3, 4), (12, 7, 12), "#cone", face_tex=chrome_caps),
            element((5, 7, 5), (11, 10, 11), "#cone", face_tex=chrome_caps),
            element((6, 10, 6), (10, 13, 10), "#cone", face_tex=chrome_caps),
            element((7, 13, 7), (9, 15, 9), "#cone", face_tex=chrome_caps),
            element((7.5, 15, 7.5), (8.5, 16, 8.5), "#antenna"),
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
# Stage 1b: propellant chain, machines, 3x3 launch complex, Mission Control console
# ----------------------------------------------------------------------------
SHALE = (52, 50, 54)
SHALE_D = (34, 32, 36)
SHALE_L = (74, 72, 78)
OIL = (26, 22, 30)
LOX = (120, 190, 240)
LOX_L = (200, 235, 255)
LOX_D = (50, 110, 170)
ALLOY = (176, 182, 170)
ALLOY_D = (118, 126, 118)
ALLOY_L = (226, 232, 222)
COPPER = (196, 118, 72)
COPPER_L = (236, 170, 120)
AMBER_LAMP = (255, 190, 70)


def oil_shale():
    img = new()
    noise_fill(img, SHALE, 6, 31)
    rnd = random.Random(32)
    for y in range(0, 16, 3):
        for x in range(16):
            if rnd.random() < 0.75:
                px(img, [(x, y)], SHALE_D)
    for y in range(1, 16, 3):
        for x in range(16):
            if rnd.random() < 0.35:
                px(img, [(x, y)], SHALE_L)
    # oily sheen
    for (x, y) in [(3, 5), (4, 5), (10, 8), (11, 8), (12, 8), (6, 13), (7, 13), (13, 2)]:
        px(img, [(x, y)], OIL)
    px(img, [(4, 4), (11, 7), (7, 12)], (90, 70, 110))
    return img


def machine_side(seed):
    """Cream enamel cabinet with a turquoise belt line and chrome trim."""
    img = new()
    noise_fill(img, CREAM, 2, seed)
    for x in range(16):
        px(img, [(x, 0)], CHROME)
        px(img, [(x, 15)], CHROME_D)
        px(img, [(x, 10), (x, 11)], TEAL)
        px(img, [(x, 12)], TEAL_D)
    for y in range(16):
        px(img, [(0, y)], CHROME_L if y < 10 else TEAL_L if y < 12 else CHROME)
        px(img, [(15, y)], CREAM_D if y < 10 else TEAL_D)
    for (x, y) in [(2, 2), (13, 2), (2, 8), (13, 8)]:
        px(img, [(x, y)], CHROME_D)
    return img


def machine_top(seed, accent):
    img = new()
    noise_fill(img, CREAM, 2, seed)
    for i in range(16):
        px(img, [(i, 0), (0, i)], CHROME_L)
        px(img, [(i, 15), (15, i)], CHROME_D)
    d = ImageDraw.Draw(img)
    d.rectangle((3, 3, 12, 12), fill=rgba(CHROME), outline=rgba(CHROME_D))
    d.ellipse((5, 5, 10, 10), fill=rgba(accent))
    px(img, [(6, 6)], CHROME_L)
    return img


def refinery_front(lit):
    img = machine_side(41)
    d = ImageDraw.Draw(img)
    # boiler window with a sight glass and two gauges
    d.rectangle((2, 2, 7, 8), fill=rgba(STEEL_D), outline=rgba(CHROME_D))
    glow = ORANGE if lit else (60, 40, 30)
    d.rectangle((3, 3, 6, 7), fill=rgba(glow))
    if lit:
        px(img, [(4, 4), (5, 5)], ORANGE_L)
        px(img, [(3, 7), (6, 7)], RED)
    d.ellipse((9, 2, 13, 6), fill=rgba(WHITE), outline=rgba(CHROME_D))
    px(img, [(11, 4), (12, 3)], RED if lit else STEEL_D)
    # pipe with valve
    for x in range(9, 15):
        px(img, [(x, 8)], COPPER)
    px(img, [(12, 7), (12, 9)], RED)
    return img


def liquefier_front(lit):
    img = machine_side(42)
    d = ImageDraw.Draw(img)
    # frost-covered compressor window + LOX gauge
    d.rectangle((2, 2, 7, 8), fill=rgba(LOX_D), outline=rgba(CHROME_D))
    d.rectangle((3, 3, 6, 7), fill=rgba(LOX if lit else (70, 100, 130)))
    if lit:
        px(img, [(3, 3), (4, 3), (3, 4), (6, 7)], LOX_L)
        px(img, [(5, 6)], WHITE)
    d.ellipse((9, 2, 13, 6), fill=rgba(WHITE), outline=rgba(CHROME_D))
    px(img, [(11, 4), (10, 3)], LOX_D if lit else STEEL_D)
    # vent grille
    for x in range(9, 15, 2):
        px(img, [(x, 8), (x, 9)], CHROME_D)
    return img


def service_tower():
    """Red / white lattice, transparent in between (cutout render type)."""
    img = new()
    for y in range(16):
        for x in range(16):
            on_frame = x in (0, 1, 14, 15)
            on_bar = y in (0, 15) or (x + y) % 8 == 0 or (x - y) % 8 == 0
            if on_frame or on_bar:
                band_red = (y // 4) % 2 == 0
                c = (RED if band_red else WHITE) if on_frame else CHROME_D
                if on_frame and x in (0, 15):
                    c = RED_D if band_red else WHITE_D
                px(img, [(x, y)], c)
    return img


def launch_pad_steel(seed):
    img = new()
    noise_fill(img, STEEL, 4, seed)
    for (x, y) in [(2, 2), (13, 2), (2, 13), (13, 13)]:
        px(img, [(x, y)], STEEL_D)
        px(img, [(x + 1, y + 1)], CHROME_D)
    return img


def hazard(img, cells):
    for (x, y) in cells:
        px(img, [(x, y)], YELLOW if ((x + y) // 2) % 2 == 0 else BLACK)


def launch_pad_center():
    img = launch_pad_steel(101)
    d = ImageDraw.Draw(img)
    d.ellipse((1, 1, 14, 14), outline=rgba(WHITE))
    d.ellipse((4, 4, 11, 11), fill=rgba(RED))
    star(img, 7, 7, WHITE)
    px(img, [(8, 7), (8, 8), (7, 8)], WHITE)
    return img


def launch_pad_edge():
    """Stripes along the north (top) side, white guide line below them."""
    img = launch_pad_steel(102)
    hazard(img, [(x, y) for x in range(16) for y in range(3)])
    for x in range(16):
        px(img, [(x, 4)], WHITE)
    for x in range(4, 12):
        px(img, [(x, 10)], CHROME_D)
    return img


def launch_pad_corner():
    """Stripes along the north and west sides."""
    img = launch_pad_steel(103)
    hazard(img, [(x, y) for x in range(16) for y in range(16) if x < 3 or y < 3])
    for i in range(4, 16):
        px(img, [(i, 4), (4, i)], WHITE)
    return img


def console_side():
    img = new()
    noise_fill(img, CREAM, 2, 51)
    for x in range(16):
        px(img, [(x, 0)], CHROME_L)
        px(img, [(x, 6), (x, 7)], TEAL)
        px(img, [(x, 8)], TEAL_D)
        px(img, [(x, 15)], CHROME_D)
    for y in range(16):
        px(img, [(0, y)], CHROME)
        px(img, [(15, y)], CREAM_D)
    return img


def console_front():
    """Cabinet front: cream panel, chrome kick plate, a row of bakelite buttons and the name plate."""
    img = console_side()
    d = ImageDraw.Draw(img)
    d.rectangle((2, 1, 13, 4), fill=rgba(NAVY), outline=rgba(CHROME))
    for i, x in enumerate(range(3, 13, 2)):
        px(img, [(x, 2)], WHITE)
    for i, (x, c) in enumerate(zip(range(2, 14, 3), (TEAL, RED, ORANGE, TEAL))):
        d.rectangle((x, 10, x + 1, 12), fill=rgba(c), outline=rgba(BLACK))
    for x in range(16):
        px(img, [(x, 14), (x, 15)], CHROME)
    return img


def console_screen():
    """The CRT face used on the sloped top box of the console model (block texture)."""
    img = new()
    noise_fill(img, CREAM, 2, 52)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((1, 1, 14, 12), radius=2, fill=rgba(BLACK), outline=rgba(CHROME_D))
    d.rounded_rectangle((2, 2, 13, 11), radius=2, fill=rgba((10, 26, 16)))
    g = (92, 255, 138)
    for x in range(3, 13):
        px(img, [(x, 3)], g if x < 10 else (40, 120, 70))
    for x in range(3, 9):
        px(img, [(x, 5)], (40, 140, 70))
    for x in range(3, 11):
        px(img, [(x, 7)], (40, 140, 70))
    for x in range(3, 13, 2):
        px(img, [(x, 9), (x, 10)], g)
    px(img, [(12, 10)], RED)
    for x in range(16):
        px(img, [(x, 14), (x, 15)], CHROME)
    px(img, [(3, 13), (6, 13), (9, 13), (12, 13)], RED)
    return img


def console_top():
    img = new()
    noise_fill(img, CREAM, 2, 53)
    for i in range(16):
        px(img, [(i, 0), (0, i)], CHROME_L)
        px(img, [(i, 15), (15, i)], CHROME_D)
    d = ImageDraw.Draw(img)
    d.rectangle((3, 3, 12, 12), fill=rgba(TEAL), outline=rgba(TEAL_D))
    star(img, 7, 7, CREAM)
    px(img, [(8, 7), (8, 8), (7, 8)], CREAM)
    return img


# --- items ---------------------------------------------------------------

def blend_pile():
    img = new()
    rnd = random.Random(61)
    d = ImageDraw.Draw(img)
    d.ellipse((2, 6, 13, 13), fill=rgba(ALLOY))
    d.ellipse((5, 3, 11, 9), fill=rgba(ALLOY))
    for _ in range(18):
        px(img, [(rnd.randint(3, 12), rnd.randint(5, 12))], rnd.choice([ALU_L, TI, ALLOY_D]))
    px(img, [(6, 4), (7, 4), (5, 6)], ALLOY_L)
    outline(img, ALLOY_D)
    return img


def wiring_harness():
    img = new()
    d = ImageDraw.Draw(img)
    # bundle of wires: red, white, navy, copper
    cols = [RED, WHITE, NAVY, COPPER, RED, WHITE]
    for i, c in enumerate(cols):
        y = 3 + i * 2
        for x in range(2, 14):
            if (x + i) % 5 != 0:
                px(img, [(x, y)], c)
    d.rectangle((5, 2, 7, 14), fill=rgba(BLACK))
    d.rectangle((10, 2, 12, 14), fill=rgba(BLACK))
    px(img, [(6, 3), (11, 3)], CHROME)
    # plug
    d.rectangle((13, 6, 15, 10), fill=rgba(CHROME), outline=rgba(CHROME_D))
    outline(img, BLACK)
    return img


def heat_shield():
    img = new()
    d = ImageDraw.Draw(img)
    d.pieslice((1, 2, 14, 24), start=180, end=360, fill=rgba(TI), outline=rgba(TI_D))
    for x in range(2, 14):
        for y in range(3, 13):
            if (x + y) % 3 == 0 and img.getpixel((x, y))[3] > 0:
                px(img, [(x, y)], (120, 70, 60))
    d.rectangle((1, 12, 14, 14), fill=rgba(CHROME), outline=rgba(CHROME_D))
    px(img, [(4, 4), (5, 4), (3, 6)], TI_L)
    outline(img, STEEL_D)
    return img


def fuel_tank():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((3, 1, 12, 14), radius=3, fill=rgba(WHITE), outline=rgba(WHITE_DD))
    for y in range(2, 14):
        px(img, [(4, y)], CHROME_L)
        px(img, [(11, y)], WHITE_D)
    for x in range(4, 12):
        px(img, [(x, 5)], CHROME)
        px(img, [(x, 8), (x, 9)], RED)
        px(img, [(x, 10)], CHROME)
    px(img, [(7, 0), (8, 0), (7, 15), (8, 15)], CHROME_D)
    outline(img, STEEL_D)
    return img


def combustion_chamber():
    img = new()
    d = ImageDraw.Draw(img)
    d.rectangle((5, 1, 10, 3), fill=rgba(CHROME), outline=rgba(CHROME_D))
    d.rounded_rectangle((3, 4, 12, 12), radius=2, fill=rgba(ALLOY), outline=rgba(ALLOY_D))
    for y in range(5, 12, 2):
        for x in range(4, 12):
            px(img, [(x, y)], ALLOY_L if x % 4 == 0 else ALLOY)
    d.rectangle((5, 12, 10, 14), fill=rgba(ORANGE))
    px(img, [(7, 14), (8, 14)], ORANGE_L)
    px(img, [(2, 6), (13, 6)], COPPER)
    outline(img, BLACK)
    return img


def engine_nozzle():
    img = new()
    d = ImageDraw.Draw(img)
    d.polygon([(6, 1), (9, 1), (13, 13), (2, 13)], fill=rgba(TI), outline=rgba(TI_D))
    for y in (4, 7, 10):
        half = (y - 1) // 3 + 1
        d.line((7 - half, y, 8 + half, y), fill=rgba(TI_D))
    for y in range(2, 13):
        px(img, [(7 - (y - 1) // 3, y)], TI_L)
    d.rectangle((2, 13, 13, 14), fill=rgba(CHROME), outline=rgba(CHROME_D))
    outline(img, STEEL_D)
    return img


def turbopump():
    img = new()
    d = ImageDraw.Draw(img)
    d.ellipse((2, 3, 13, 14), fill=rgba(ALLOY), outline=rgba(ALLOY_D))
    d.ellipse((5, 6, 10, 11), fill=rgba(CHROME_D), outline=rgba(CHROME_L))
    px(img, [(7, 8), (8, 8), (7, 9), (8, 9)], RED)
    for (x, y) in [(4, 5), (11, 5), (4, 12), (11, 12)]:
        px(img, [(x, y)], CHROME_D)
    d.rectangle((6, 0, 9, 3), fill=rgba(COPPER), outline=rgba((120, 70, 40)))
    d.rectangle((12, 7, 15, 9), fill=rgba(COPPER))
    outline(img, BLACK)
    return img


def airframe():
    """Assembled hull without the nose and engine: white cylinder, tanks visible, fins at the bottom."""
    img = new()
    for y in range(1, 14):
        for x in range(5, 11):
            px(img, [(x, y)], WHITE)
        px(img, [(5, y)], CHROME_L)
        px(img, [(10, y)], WHITE_D)
    for x in range(5, 11):
        px(img, [(x, 4)], CHROME)
        px(img, [(x, 9), (x, 10)], RED)
        px(img, [(x, 1)], CHROME_D)
        px(img, [(x, 13)], CHROME_D)
    px(img, [(7, 6), (8, 6), (7, 7), (8, 7)], VISOR)
    px(img, [(7, 6)], GLASS_L)
    px(img, [(4, 10), (4, 11), (3, 12), (4, 12), (2, 13), (3, 13), (4, 13)], RED)
    px(img, [(11, 10), (11, 11), (11, 12), (12, 12), (11, 13), (12, 13), (13, 13)], RED)
    outline(img, STEEL_D)
    return img


def lox_canister():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((3, 4, 12, 14), radius=2, fill=rgba(LOX), outline=rgba(LOX_D))
    d.rectangle((6, 1, 9, 3), fill=rgba(STEEL))
    d.rectangle((5, 3, 10, 4), fill=rgba(STEEL_D))
    d.rectangle((4, 7, 11, 11), fill=rgba(WHITE))
    px(img, [(5, 8), (6, 8), (5, 9), (6, 9), (5, 10), (6, 10)], LOX_D)
    px(img, [(6, 9)], WHITE)
    px(img, [(8, 8), (9, 8), (8, 10), (9, 10), (10, 9), (8, 9)], LOX_D)
    px(img, [(4, 5), (4, 6), (11, 13)], LOX_L)
    outline(img, BLACK)
    return img


def kerosene_canister():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((3, 4, 12, 14), radius=2, fill=rgba(RED), outline=rgba(RED_D))
    d.rectangle((6, 1, 9, 3), fill=rgba(STEEL))
    d.rectangle((5, 3, 10, 4), fill=rgba(STEEL_D))
    d.rectangle((4, 7, 11, 11), fill=rgba(WHITE))
    star(img, 6, 9, NAVY)
    px(img, [(9, 8), (10, 8), (9, 10), (10, 10), (9, 9)], RED_D)
    px(img, [(4, 5), (4, 6)], RED_L)
    outline(img, BLACK)
    return img


# --- GUI art -----------------------------------------------------------------

def panel(d, x0, y0, x1, y1, fill, light, dark):
    d.rectangle((x0, y0, x1, y1), fill=rgba(fill))
    d.line((x0, y0, x1, y0), fill=rgba(light))
    d.line((x0, y0, x0, y1), fill=rgba(light))
    d.line((x0, y1, x1, y1), fill=rgba(dark))
    d.line((x1, y0, x1, y1), fill=rgba(dark))


def slot_box(d, x, y, size=18):
    d.rectangle((x, y, x + size - 1, y + size - 1), fill=rgba((139, 139, 139)))
    d.line((x, y, x + size - 1, y), fill=rgba((55, 55, 55)))
    d.line((x, y, x, y + size - 1), fill=rgba((55, 55, 55)))
    d.line((x, y + size - 1, x + size - 1, y + size - 1), fill=rgba((255, 255, 255)))
    d.line((x + size - 1, y, x + size - 1, y + size - 1), fill=rgba((255, 255, 255)))


def gui_machine():
    img = new(256, 256)
    d = ImageDraw.Draw(img)
    # cream enamel panel with turquoise header band and chrome frame
    d.rounded_rectangle((0, 0, 175, 165), radius=4, fill=rgba(CREAM), outline=rgba(BLACK))
    d.rounded_rectangle((1, 1, 174, 164), radius=3, outline=rgba(CHROME_L))
    d.rectangle((3, 3, 172, 14), fill=rgba(TEAL))
    d.line((3, 15, 172, 15), fill=rgba(TEAL_D))
    for x in range(8, 172, 6):
        px(img, [(x, 4)], TEAL_L)
    d.rectangle((3, 76, 172, 78), fill=rgba(CHROME))
    d.line((3, 79, 172, 79), fill=rgba(CHROME_D))
    # machine panel (darker inset) behind the slots
    panel(d, 24, 18, 150, 72, (226, 216, 190), CHROME_L, CREAM_D)
    # slots: input (56,17) canister (32,35) fuel (56,53) output (116,35)
    slot_box(d, 55, 16)
    slot_box(d, 31, 34)
    slot_box(d, 55, 52)
    d.rounded_rectangle((110, 29, 137, 56), radius=3, fill=rgba(CHROME), outline=rgba(CHROME_D))
    slot_box(d, 115, 34)
    # flame socket
    d.rectangle((56, 35, 70, 49), fill=rgba((90, 86, 80)))
    for y in range(36, 49, 2):
        d.line((57, y, 69, y), fill=rgba((70, 66, 60)))
    # pipe outline from the input to the output
    d.rectangle((79, 34, 102, 50), fill=rgba((120, 118, 112)), outline=rgba(CHROME_D))
    d.polygon([(79, 36), (96, 36), (96, 32), (103, 42), (96, 52), (96, 48), (79, 48)], fill=rgba((150, 148, 142)))
    # stars & stripes decoration on the header
    for i in range(3):
        star(img, 160 + i * 5, 9, CREAM)
    # player inventory slots
    for row in range(3):
        for col in range(9):
            slot_box(d, 7 + col * 18, 83 + row * 18)
    for col in range(9):
        slot_box(d, 7 + col * 18, 141)
    # overlays: flame (176,0) 14x14
    d.polygon([(183, 0), (189, 4), (189, 13), (177, 13), (177, 6)], fill=rgba(ORANGE))
    d.polygon([(183, 4), (187, 8), (186, 13), (180, 13), (180, 8)], fill=rgba(ORANGE_L))
    px(img, [(183, 9), (182, 10), (184, 10)], (255, 240, 200))
    # progress fill (176,14) 24x17: turquoise liquid in the pipe
    d.polygon([(176, 16), (193, 16), (193, 14), (199, 22), (193, 30), (193, 28), (176, 28)], fill=rgba(TEAL))
    d.polygon([(177, 18), (192, 18), (192, 20), (177, 20)], fill=rgba(TEAL_L))
    # emblems (216,0) and (216,20), 24x20
    d.ellipse((218, 1, 237, 18), fill=rgba(RED), outline=rgba(RED_D))
    d.polygon([(227, 3), (232, 11), (227, 16), (222, 11)], fill=rgba(WHITE))
    px(img, [(227, 9), (227, 10), (226, 10), (228, 10)], RED_D)
    d.ellipse((218, 21, 237, 38), fill=rgba(LOX_D), outline=rgba(NAVY))
    for a in range(0, 360, 60):
        import math
        d.line((227, 29, 227 + 7 * math.cos(math.radians(a)), 29 + 7 * math.sin(math.radians(a))), fill=rgba(LOX_L))
    return img


def gui_console():
    img = new(256, 256)
    d = ImageDraw.Draw(img)
    W, H = 232, 200
    # cabinet: cream body, turquoise flanks, chrome trims
    d.rounded_rectangle((0, 0, W - 1, H - 1), radius=6, fill=rgba(CREAM), outline=rgba(BLACK))
    d.rounded_rectangle((1, 1, W - 2, H - 2), radius=5, outline=rgba(CHROME_L))
    d.rectangle((2, 2, 9, H - 3), fill=rgba(TEAL))
    d.rectangle((W - 10, 2, W - 3, H - 3), fill=rgba(TEAL))
    d.line((9, 2, 9, H - 3), fill=rgba(TEAL_D))
    d.line((W - 10, 2, W - 10, H - 3), fill=rgba(TEAL_D))
    # CRT bezel (dark bakelite with rounded corners) around (14,16) 204x132
    d.rounded_rectangle((10, 12, 221, 151), radius=8, fill=rgba((40, 36, 36)), outline=rgba(BLACK))
    d.rounded_rectangle((11, 13, 220, 150), radius=7, outline=rgba((90, 84, 80)))
    d.rounded_rectangle((13, 15, 218, 148), radius=4, fill=rgba((10, 26, 16)), outline=rgba((20, 60, 36)))
    # header plate above the bezel
    d.rectangle((60, 3, 171, 10), fill=rgba(NAVY), outline=rgba(CHROME))
    for x in range(64, 170, 6):
        px(img, [(x, 6)], WHITE)
    # lamp row under the CRT
    d.rectangle((12, 153, 219, 159), fill=rgba(CHROME), outline=rgba(CHROME_D))
    for i, c in enumerate((RED, ORANGE, YELLOW, TEAL, (120, 230, 120), RED, ORANGE, YELLOW, TEAL, (120, 230, 120))):
        x = 16 + i * 20
        d.ellipse((x, 154, x + 4, 158), fill=rgba(c), outline=rgba(BLACK))
    # button bay
    panel(d, 12, 160, 219, 187, (222, 212, 186), CHROME_L, CREAM_D)
    # name plate & starburst
    d.rectangle((70, 189, 161, 197), fill=rgba(NAVY), outline=rgba(CHROME))
    import math
    for a in range(0, 360, 30):
        d.line((40, 193, 40 + 6 * math.cos(math.radians(a)), 193 + 6 * math.sin(math.radians(a))), fill=rgba(RED))
        d.line((191, 193, 191 + 6 * math.cos(math.radians(a)), 193 + 6 * math.sin(math.radians(a))), fill=rgba(RED))
    px(img, [(40, 193), (191, 193)], CREAM)
    return img


def gui_hud():
    """Suit telemetry HUD plate (128x64 sheet): bakelite panel 120x46 at (0,0), gauge glass at (0,48) 100x10."""
    img = new(128, 64)
    d = ImageDraw.Draw(img)
    # panel: dark bakelite with chrome edge and a cream label strip
    d.rounded_rectangle((0, 0, 119, 45), radius=4, fill=rgba((36, 32, 34)), outline=rgba(BLACK))
    d.rounded_rectangle((1, 1, 118, 44), radius=3, outline=rgba(CHROME_D))
    d.rectangle((3, 3, 116, 10), fill=rgba(CREAM))
    d.line((3, 11, 116, 11), fill=rgba(CREAM_D))
    d.rectangle((3, 3, 7, 10), fill=rgba(RED))
    d.rectangle((112, 3, 116, 10), fill=rgba(TEAL))
    # rivets
    for (x, y) in [(3, 14), (116, 14), (3, 41), (116, 41)]:
        px(img, [(x, y)], CHROME)
        px(img, [(x + (1 if x < 60 else -1), y + 1)], CHROME_D)
    # gauge glass track (0,48) 100x10: dark channel with chrome ends and tick marks
    d.rectangle((0, 48, 99, 57), fill=rgba((18, 20, 22)), outline=rgba(CHROME_D))
    for i in range(1, 10):
        x = i * 10
        d.line((x, 49, x, 50 if i % 5 else 52), fill=rgba(CHROME_D))
    px(img, [(1, 49), (98, 49)], CHROME_L)
    # warning lamp sprites (104,48): off / amber / red, 8x8 each
    for i, c in enumerate(((60, 40, 40), AMBER_LAMP, RED)):
        x = 104 + i * 8
        d.ellipse((x, 48, x + 6, 54), fill=rgba(c), outline=rgba(BLACK))
    return img


# --- models / data ----------------------------------------------------------

def machine_models(name):
    tex = {"top": f"{MOD}:block/{name}_top", "side": f"{MOD}:block/{name}_side", "front": f"{MOD}:block/{name}_front"}
    write_json(os.path.join(ASSETS, "models", "block", name + ".json"), {"parent": "minecraft:block/orientable", "textures": tex})
    write_json(os.path.join(ASSETS, "models", "block", name + "_on.json"),
               {"parent": "minecraft:block/orientable", "textures": dict(tex, front=f"{MOD}:block/{name}_front_on")})
    variants = {}
    for facing, rot in (("north", 0), ("east", 90), ("south", 180), ("west", 270)):
        for lit in ("false", "true"):
            v = {"model": f"{MOD}:block/{name}{'_on' if lit == 'true' else ''}"}
            if rot:
                v["y"] = rot
            variants[f"facing={facing},lit={lit}"] = v
    write_json(os.path.join(ASSETS, "blockstates", name + ".json"), {"variants": variants})
    item_def(name, f"{MOD}:block/{name}")


def console_model():
    t = {"side": f"{MOD}:block/console_side", "front": f"{MOD}:block/console_front",
         "screen": f"{MOD}:block/console_screen", "top": f"{MOD}:block/console_top", "particle": f"{MOD}:block/console_side"}
    model = {"textures": t, "elements": [
        element((0, 0, 0), (16, 10, 16), "#side", face_tex={"north": "#front", "up": "#top", "down": "#side"}),
        # sloped CRT housing on top (front face carries the screen)
        element((1, 10, 2), (15, 16, 14), "#side", face_tex={"north": "#screen", "up": "#top"}),
    ]}
    write_json(os.path.join(ASSETS, "models", "block", "mission_control_console.json"), model)
    variants = {}
    for facing, rot in (("north", 0), ("east", 90), ("south", 180), ("west", 270)):
        v = {"model": f"{MOD}:block/mission_control_console"}
        if rot:
            v["y"] = rot
        variants[f"facing={facing}"] = v
    write_json(os.path.join(ASSETS, "blockstates", "mission_control_console.json"), {"variants": variants})
    item_def("mission_control_console", f"{MOD}:block/mission_control_console")


def launch_pad_models():
    for part in ("single", "center", "edge", "corner"):
        write_json(os.path.join(ASSETS, "models", "block", f"launch_pad_{part}.json"), {
            "parent": "minecraft:block/cube_bottom_top",
            "textures": {"top": f"{MOD}:block/launch_pad_{part}" if part != "single" else f"{MOD}:block/launch_pad_top",
                         "bottom": f"{MOD}:block/titanium_block", "side": f"{MOD}:block/launch_pad_side"}})
    variants = {}
    for part in ("single", "center", "edge", "corner"):
        for facing, rot in (("north", 0), ("east", 90), ("south", 180), ("west", 270)):
            v = {"model": f"{MOD}:block/launch_pad_{part}"}
            if rot and part in ("edge", "corner"):
                v["y"] = rot
            variants[f"facing={facing},part={part}"] = v
    write_json(os.path.join(ASSETS, "blockstates", "launch_pad.json"), {"variants": variants})
    item_def("launch_pad", f"{MOD}:block/launch_pad_single")


def service_tower_model():
    write_json(os.path.join(ASSETS, "models", "block", "service_tower.json"),
               {"parent": "minecraft:block/cube_all", "render_type": "minecraft:cutout",
                "textures": {"all": f"{MOD}:block/service_tower"}})
    simple_blockstate("service_tower")
    item_def("service_tower", f"{MOD}:block/service_tower")


def stone_ore_feature(name, block, size, count, lo, hi):
    write_json(os.path.join(DATA, "worldgen", "configured_feature", name + ".json"), {
        "type": "minecraft:ore",
        "config": {"size": size, "discard_chance_on_air_exposure": 0.0, "targets": [
            {"target": {"predicate_type": "minecraft:tag_match", "tag": "minecraft:stone_ore_replaceables"},
             "state": {"Name": f"{MOD}:{block}"}}]}})
    write_json(os.path.join(DATA, "worldgen", "placed_feature", name + ".json"), {
        "feature": f"{MOD}:{name}",
        "placement": [
            {"type": "minecraft:count", "count": count},
            {"type": "minecraft:in_square"},
            {"type": "minecraft:height_range", "height": {
                "type": "minecraft:uniform", "min_inclusive": {"absolute": lo}, "max_inclusive": {"absolute": hi}}},
            {"type": "minecraft:biome"},
        ]})


def has_count(item, count):
    return {"has_" + item: {"trigger": "minecraft:inventory_changed",
                            "conditions": {"items": [{"items": ing(item), "count": {"min": count}}]}}}


def stage1b_textures():
    save(oil_shale(), "block", "oil_shale")
    save(machine_side(41), "block", "fuel_refinery_side")
    save(machine_top(43, ORANGE), "block", "fuel_refinery_top")
    save(refinery_front(False), "block", "fuel_refinery_front")
    save(refinery_front(True), "block", "fuel_refinery_front_on")
    save(machine_side(42), "block", "air_liquefier_side")
    save(machine_top(44, LOX), "block", "air_liquefier_top")
    save(liquefier_front(False), "block", "air_liquefier_front")
    save(liquefier_front(True), "block", "air_liquefier_front_on")
    save(service_tower(), "block", "service_tower")
    save(launch_pad_center(), "block", "launch_pad_center")
    save(launch_pad_edge(), "block", "launch_pad_edge")
    save(launch_pad_corner(), "block", "launch_pad_corner")
    save(console_side(), "block", "console_side")
    save(console_front(), "block", "console_front")
    save(console_screen(), "block", "console_screen")
    save(console_top(), "block", "console_top")

    save(blend_pile(), "item", "aero_alloy_blend")
    save(ingot(ALLOY_D, ALLOY, ALLOY_L), "item", "aero_alloy_ingot")
    save(plate(ALLOY_D, ALLOY, ALLOY_L), "item", "aero_alloy_plate")
    save(wiring_harness(), "item", "wiring_harness")
    save(heat_shield(), "item", "heat_shield")
    save(fuel_tank(), "item", "fuel_tank")
    save(combustion_chamber(), "item", "combustion_chamber")
    save(engine_nozzle(), "item", "engine_nozzle")
    save(turbopump(), "item", "turbopump")
    save(airframe(), "item", "airframe")
    save(lox_canister(), "item", "liquid_oxygen_canister")
    save(kerosene_canister(), "item", "rocket_fuel_canister")

    os.makedirs(os.path.join(ASSETS, "textures", "gui"), exist_ok=True)
    gui_machine().save(os.path.join(ASSETS, "textures", "gui", "machine.png"))
    gui_console().save(os.path.join(ASSETS, "textures", "gui", "console.png"))
    gui_hud().save(os.path.join(ASSETS, "textures", "gui", "hud.png"))


def stage1b_data():
    # models / blockstates / items
    cube_all("oil_shale")
    simple_blockstate("oil_shale")
    item_def("oil_shale", f"{MOD}:block/oil_shale")
    machine_models("fuel_refinery")
    machine_models("air_liquefier")
    console_model()
    launch_pad_models()
    service_tower_model()
    for i in ("aero_alloy_blend", "aero_alloy_ingot", "aero_alloy_plate", "wiring_harness", "heat_shield", "fuel_tank",
              "combustion_chamber", "engine_nozzle", "turbopump", "airframe", "liquid_oxygen_canister"):
        generated_item(i)

    # loot
    for b in ("oil_shale", "service_tower", "fuel_refinery", "air_liquefier", "mission_control_console"):
        loot_self(b)

    # tags
    tag("block/mineable/pickaxe", [f"{MOD}:{b}" for b in ("oil_shale", "service_tower", "fuel_refinery", "air_liquefier",
                                                            "mission_control_console")] + [
        f"{MOD}:{b}" for b in ("bauxite_ore", "deepslate_bauxite_ore", "titanium_ore", "deepslate_titanium_ore",
                               "aluminum_block", "titanium_block", "launch_pad", "rocket")])
    tag("block/needs_stone_tool", [f"{MOD}:bauxite_ore", f"{MOD}:deepslate_bauxite_ore", f"{MOD}:aluminum_block",
                                   f"{MOD}:oil_shale", f"{MOD}:service_tower", f"{MOD}:fuel_refinery",
                                   f"{MOD}:air_liquefier", f"{MOD}:mission_control_console"])
    tag("item/refinery_input", [f"{MOD}:oil_shale"], namespace=MOD)
    tag("item/liquefier_input", ["minecraft:ice", "minecraft:packed_ice", "minecraft:blue_ice", "minecraft:snow_block"], namespace=MOD)
    tag("item/ingots/aero_alloy", [f"{MOD}:aero_alloy_ingot"], namespace="c")
    tag("item/plates/aero_alloy", [f"{MOD}:aero_alloy_plate"], namespace="c")

    # worldgen: oil shale in sedimentary bands
    stone_ore_feature("ore_oil_shale", "oil_shale", 14, 7, 8, 72)

    # recipes: alloy
    shapeless("aero_alloy_blend", ["aluminum_ingot", "aluminum_ingot", "titanium_ingot"], "aero_alloy_blend", count=3)
    cooking("aero_alloy_ingot_from_smelting", "smelting", "aero_alloy_blend", "aero_alloy_ingot", 0.8, 200)
    cooking("aero_alloy_ingot_from_blasting", "blasting", "aero_alloy_blend", "aero_alloy_ingot", 0.8, 100)
    shaped("aero_alloy_plate", ["#", "#"], {"#": "aero_alloy_ingot"}, "aero_alloy_plate")
    # electronics
    shaped("wiring_harness", ["SCS", "CRC", "SCS"],
           {"S": "minecraft:string", "C": "minecraft:copper_ingot", "R": "minecraft:redstone"}, "wiring_harness", count=2)
    # engine
    shaped("combustion_chamber", ["P P", "PFP", "PPP"], {"P": "aero_alloy_plate", "F": "minecraft:fire_charge"}, "combustion_chamber")
    shaped("engine_nozzle", ["T T", "TTT"], {"T": "titanium_plate"}, "engine_nozzle")
    shaped("turbopump", ["A A", "CPC", "AVA"],
           {"A": "aero_alloy_plate", "C": "minecraft:copper_ingot", "P": "minecraft:piston", "V": "vacuum_tube"}, "turbopump")
    shaped("rocket_engine", [" C ", "TPT", " N "],
           {"C": "combustion_chamber", "T": "titanium_plate", "P": "turbopump", "N": "engine_nozzle"}, "rocket_engine")
    # structure
    shaped("heat_shield", ["BBB", "TTT"], {"B": "minecraft:bricks", "T": "titanium_plate"}, "heat_shield")
    shaped("fuel_tank", ["APA", "A A", "APA"], {"A": "aluminum_plate", "P": "aero_alloy_plate"}, "fuel_tank")
    shaped("airframe", ["HTH", "HTH", "FAF"],
           {"H": "hull_segment", "T": "fuel_tank", "F": "rocket_fin", "A": "aero_alloy_plate"}, "airframe")
    # machines & launch complex
    shaped("fuel_refinery", ["ACA", "AGA", "TFT"],
           {"A": "aluminum_plate", "C": "minecraft:copper_ingot", "G": "minecraft:glass", "T": "titanium_plate",
            "F": "minecraft:furnace"}, "fuel_refinery")
    shaped("air_liquefier", ["ACA", "AVA", "TPT"],
           {"A": "aluminum_plate", "C": "minecraft:copper_ingot", "V": "vacuum_tube", "T": "titanium_plate",
            "P": "minecraft:piston"}, "air_liquefier")
    shaped("mission_control_console", ["AGA", "VCV", "TRT"],
           {"A": "aluminum_plate", "G": "minecraft:glass_pane", "V": "vacuum_tube", "C": "guidance_computer",
            "T": "titanium_plate", "R": "minecraft:redstone"}, "mission_control_console")
    shaped("service_tower", ["A A", "BBB", "A A"],
           {"A": "aluminum_plate", "B": "minecraft:iron_bars"}, "service_tower", count=4, category="building")

    # advancements
    advancement("oil_shale", "oil_shale", "root", has_item("oil_shale"))
    advancement("refinery", "fuel_refinery", "oil_shale", has_item("fuel_refinery"))
    advancement("fuel", "rocket_fuel_canister", "refinery", has_item("rocket_fuel_canister"))
    advancement("lox", "liquid_oxygen_canister", "refinery", has_item("liquid_oxygen_canister"))
    advancement("aero_alloy", "aero_alloy_ingot", "titanium", has_item("aero_alloy_ingot"))
    advancement("rocket_engine", "rocket_engine", "aero_alloy", has_item("rocket_engine"))
    advancement("airframe", "airframe", "aero_alloy", has_item("airframe"))
    advancement("rocket", "rocket", "airframe", has_item("rocket"), frame="goal")
    advancement("launch_pad", "launch_pad", "titanium", has_count("launch_pad", 9))
    advancement("launch_complex", "service_tower", "launch_pad", {"pad_complete": {"trigger": "minecraft:impossible"}})
    advancement("console", "mission_control_console", "guidance_computer", has_item("mission_control_console"))
    advancement("countdown", "rocket", "ready_for_launch", {"liftoff": {"trigger": "minecraft:impossible"}}, frame="challenge")
    advancement("canned_air", "liquid_oxygen_canister", "space_suit", {"refilled": {"trigger": "minecraft:impossible"}})


EN_1B = {
    "block.retrocosmos.oil_shale": "Oil Shale",
    "block.retrocosmos.fuel_refinery": "Fuel Refinery",
    "block.retrocosmos.air_liquefier": "Air Liquefier",
    "block.retrocosmos.mission_control_console": "Mission Control Console",
    "block.retrocosmos.service_tower": "Service Tower",
    "item.retrocosmos.aero_alloy_blend": "Aero Alloy Blend",
    "item.retrocosmos.aero_alloy_ingot": "Aero Alloy Ingot",
    "item.retrocosmos.aero_alloy_plate": "Aero Alloy Plate",
    "item.retrocosmos.wiring_harness": "Wiring Harness",
    "item.retrocosmos.heat_shield": "Ablative Heat Shield",
    "item.retrocosmos.fuel_tank": "Propellant Tank",
    "item.retrocosmos.combustion_chamber": "Combustion Chamber",
    "item.retrocosmos.engine_nozzle": "Engine Nozzle",
    "item.retrocosmos.turbopump": "Turbopump",
    "item.retrocosmos.airframe": "Liberty I Airframe",
    "item.retrocosmos.rocket_fuel_canister": "RP-1 Kerosene Canister",
    "item.retrocosmos.liquid_oxygen_canister": "Liquid Oxygen Canister",
    "message.retrocosmos.rocket.fueled": "RP-1 tank: %s / %s",
    "message.retrocosmos.rocket.oxidized": "LOX tank: %s / %s",
    "message.retrocosmos.rocket.fuel_full": "That tank is already full!",
    "message.retrocosmos.checklist.vehicle": "Vehicle on the stand",
    "message.retrocosmos.checklist.pad": "Launch pad complete (%s / %s blocks, 3x3)",
    "message.retrocosmos.checklist.tower": "Service tower beside the pad (%s / %s blocks tall)",
    "message.retrocosmos.checklist.fuel": "RP-1 kerosene loaded (%s / %s)",
    "message.retrocosmos.checklist.oxidizer": "Liquid oxygen loaded (%s / %s)",
    "message.retrocosmos.checklist.go_to_console": "Proceed to the Mission Control console to start the countdown.",
    "message.retrocosmos.console.no_go": "NO-GO: the pre-flight checklist is incomplete. Run the check.",
    "message.retrocosmos.console.countdown_started": "Mission Control: countdown started. All stations, stand by.",
    "message.retrocosmos.console.t_minus": "T-minus %s...",
    "message.retrocosmos.console.ignition": "Ignition sequence start!",
    "message.retrocosmos.console.liftoff": "Zero. We have liftoff!",
    "message.retrocosmos.console.hold": "HOLD, HOLD, HOLD!",
    "message.retrocosmos.console.abort_manual": "Countdown aborted by the flight director.",
    "message.retrocosmos.console.abort_vehicle": "Countdown aborted: the vehicle or the launch complex is no longer GO.",
    "gui.retrocosmos.console.header": "MISSION CONTROL - LIBERTY I",
    "gui.retrocosmos.console.vehicle": "VEHICLE",
    "gui.retrocosmos.console.vehicle_on_pad": "ON STAND, %sm",
    "gui.retrocosmos.console.vehicle_missing": "NOT FOUND",
    "gui.retrocosmos.console.pad": "LAUNCH PAD 3x3",
    "gui.retrocosmos.console.tower": "SERVICE TOWER",
    "gui.retrocosmos.console.fuel": "RP-1 KEROSENE",
    "gui.retrocosmos.console.oxidizer": "LIQUID OXYGEN",
    "gui.retrocosmos.console.suit": "ASTRONAUT SUIT",
    "gui.retrocosmos.console.counting": "COUNTDOWN  %s",
    "gui.retrocosmos.console.all_go": "ALL SYSTEMS GO - READY FOR COUNTDOWN",
    "gui.retrocosmos.console.no_go": "NO-GO - CHECKLIST INCOMPLETE",
    "gui.retrocosmos.console.standby": "STANDING BY - RUN PRE-FLIGHT CHECK",
    "gui.retrocosmos.console.run_check": "RUN CHECK",
    "gui.retrocosmos.console.countdown": "COUNTDOWN",
    "gui.retrocosmos.console.abort": "ABORT",
    "advancements.retrocosmos.oil_shale.title": "Black Gold",
    "advancements.retrocosmos.oil_shale.description": "Mine oil shale, the source of rocket-grade kerosene",
    "advancements.retrocosmos.refinery.title": "Refinery Row",
    "advancements.retrocosmos.refinery.description": "Build a fuel refinery",
    "advancements.retrocosmos.fuel.title": "Atomic-Age Kerosene",
    "advancements.retrocosmos.fuel.description": "Refine a canister of RP-1 kerosene",
    "advancements.retrocosmos.lox.title": "Colder Than Space",
    "advancements.retrocosmos.lox.description": "Liquefy a canister of oxygen in the air liquefier",
    "advancements.retrocosmos.aero_alloy.title": "Jet Age Alloy",
    "advancements.retrocosmos.aero_alloy.description": "Smelt an aero alloy ingot from an aluminum-titanium blend",
    "advancements.retrocosmos.rocket_engine.title": "Ignition Sequence Start",
    "advancements.retrocosmos.rocket_engine.description": "Assemble a rocket engine from a chamber, a turbopump and a nozzle",
    "advancements.retrocosmos.airframe.title": "Airframe",
    "advancements.retrocosmos.airframe.description": "Rivet hull segments, propellant tanks and fins into an airframe",
    "advancements.retrocosmos.launch_pad.title": "Nine Slabs of Steel",
    "advancements.retrocosmos.launch_pad.description": "Collect nine launch pad blocks for a 3x3 pad",
    "advancements.retrocosmos.launch_complex.title": "Launch Complex 1",
    "advancements.retrocosmos.launch_complex.description": "Have Mission Control confirm a complete 3x3 launch pad",
    "advancements.retrocosmos.console.title": "Mission Control",
    "advancements.retrocosmos.console.description": "Build a Mission Control console",
    "advancements.retrocosmos.ready_for_launch.title": "All Systems GO",
    "advancements.retrocosmos.ready_for_launch.description": "Pass the pre-flight checklist: 3x3 pad, service tower, RP-1, LOX, suited up",
    "advancements.retrocosmos.countdown.title": "We Have Liftoff!",
    "advancements.retrocosmos.countdown.description": "Run the countdown to zero from the Mission Control console",
    "advancements.retrocosmos.canned_air.title": "First Breath of Canned Air",
    "advancements.retrocosmos.canned_air.description": "Recharge your pressure suit from a liquid oxygen canister",
    "tooltip.retrocosmos.space_suit.oxygen": "Oxygen: %s%% (%s)",
    "tooltip.retrocosmos.liquid_oxygen_canister": "Right click in the air to recharge the worn pressure suit",
    "message.retrocosmos.oxygen.low": "Oxygen low: %s seconds left!",
    "message.retrocosmos.oxygen.empty": "OXYGEN DEPLETED - recharge the suit!",
    "message.retrocosmos.oxygen.no_suit": "NO PRESSURE SUIT - suffocating!",
    "message.retrocosmos.oxygen.recharged": "Suit oxygen tank recharged by life support",
    "message.retrocosmos.oxygen.refilled": "Suit oxygen tank recharged: 300 s",
    "message.retrocosmos.oxygen.need_suit": "Put the pressure suit on first",
    "message.retrocosmos.oxygen.already_full": "The suit's oxygen tank is already full",
    "message.retrocosmos.oxygen.airless_on": "Airless environment simulation ON - your suit's oxygen now counts down.",
    "message.retrocosmos.oxygen.airless_off": "Airless environment simulation OFF - breathing normally.",
    "command.retrocosmos.on": "on",
    "command.retrocosmos.off": "off",
    "command.retrocosmos.oxygen.toggled": "Airless environment for %s: %s",
    "command.retrocosmos.oxygen.set": "Suit oxygen of %s set to %s seconds",
    "command.retrocosmos.oxygen.no_suit": "%s is not wearing the pressure suit",
    "command.retrocosmos.hud": "Suit telemetry HUD: %s",
    "gui.retrocosmos.hud.title": "TELEMETRY",
    "gui.retrocosmos.hud.vacuum": "VAC",
    "gui.retrocosmos.hud.atmosphere": "ATM",
    "gui.retrocosmos.hud.o2_low": "! O2 LOW - RECHARGE !",
    "gui.retrocosmos.hud.suit_breach": "! SUIT INCOMPLETE !",
}

RU_1B = {
    "block.retrocosmos.oil_shale": "Горючий сланец",
    "block.retrocosmos.fuel_refinery": "Топливный завод",
    "block.retrocosmos.air_liquefier": "Воздухоразделитель",
    "block.retrocosmos.mission_control_console": "Пульт Центра управления",
    "block.retrocosmos.service_tower": "Башня обслуживания",
    "item.retrocosmos.aero_alloy_blend": "Смесь для аэросплава",
    "item.retrocosmos.aero_alloy_ingot": "Слиток аэросплава",
    "item.retrocosmos.aero_alloy_plate": "Пластина аэросплава",
    "item.retrocosmos.wiring_harness": "Жгут проводов",
    "item.retrocosmos.heat_shield": "Абляционный теплозащитный экран",
    "item.retrocosmos.fuel_tank": "Топливный бак",
    "item.retrocosmos.combustion_chamber": "Камера сгорания",
    "item.retrocosmos.engine_nozzle": "Сопло двигателя",
    "item.retrocosmos.turbopump": "Турбонасос",
    "item.retrocosmos.airframe": "Планер «Либерти-1»",
    "item.retrocosmos.rocket_fuel_canister": "Канистра керосина RP-1",
    "item.retrocosmos.liquid_oxygen_canister": "Канистра жидкого кислорода",
    "message.retrocosmos.rocket.fueled": "Бак RP-1: %s / %s",
    "message.retrocosmos.rocket.oxidized": "Бак LOX: %s / %s",
    "message.retrocosmos.rocket.fuel_full": "Этот бак уже полон!",
    "message.retrocosmos.checklist.vehicle": "Ракета на стартовом столе",
    "message.retrocosmos.checklist.pad": "Стартовая площадка собрана (%s / %s блоков, 3x3)",
    "message.retrocosmos.checklist.tower": "Башня обслуживания рядом с площадкой (%s / %s блоков в высоту)",
    "message.retrocosmos.checklist.fuel": "Керосин RP-1 заправлен (%s / %s)",
    "message.retrocosmos.checklist.oxidizer": "Жидкий кислород заправлен (%s / %s)",
    "message.retrocosmos.checklist.go_to_console": "Пройдите к пульту Центра управления, чтобы начать отсчёт.",
    "message.retrocosmos.console.no_go": "NO-GO: предстартовая проверка не пройдена. Запустите проверку.",
    "message.retrocosmos.console.countdown_started": "Центр управления: отсчёт начат. Всем постам — готовность.",
    "message.retrocosmos.console.t_minus": "T-минус %s...",
    "message.retrocosmos.console.ignition": "Зажигание!",
    "message.retrocosmos.console.liftoff": "Ноль. Есть отрыв!",
    "message.retrocosmos.console.hold": "СТОП, СТОП, СТОП!",
    "message.retrocosmos.console.abort_manual": "Отсчёт прерван руководителем полёта.",
    "message.retrocosmos.console.abort_vehicle": "Отсчёт прерван: ракета или стартовый комплекс больше не в готовности.",
    "gui.retrocosmos.console.header": "ЦЕНТР УПР. - ЛИБЕРТИ-1",
    "gui.retrocosmos.console.vehicle": "РАКЕТА",
    "gui.retrocosmos.console.vehicle_on_pad": "НА СТОЛЕ, %s м",
    "gui.retrocosmos.console.vehicle_missing": "НЕ НАЙДЕНА",
    "gui.retrocosmos.console.pad": "ПЛОЩАДКА 3x3",
    "gui.retrocosmos.console.tower": "БАШНЯ ОБСЛУЖ.",
    "gui.retrocosmos.console.fuel": "КЕРОСИН RP-1",
    "gui.retrocosmos.console.oxidizer": "ЖИДКИЙ КИСЛОРОД",
    "gui.retrocosmos.console.suit": "СКАФАНДР",
    "gui.retrocosmos.console.counting": "ОТСЧЁТ  %s",
    "gui.retrocosmos.console.all_go": "ВСЕ СИСТЕМЫ GO - ГОТОВ К ОТСЧЁТУ",
    "gui.retrocosmos.console.no_go": "NO-GO - ПРОВЕРКА НЕ ПРОЙДЕНА",
    "gui.retrocosmos.console.standby": "ОЖИДАНИЕ - ЗАПУСТИТЕ ПРОВЕРКУ",
    "gui.retrocosmos.console.run_check": "ПРОВЕРКА",
    "gui.retrocosmos.console.countdown": "ОТСЧЁТ",
    "gui.retrocosmos.console.abort": "СТОП",
    "advancements.retrocosmos.oil_shale.title": "Чёрное золото",
    "advancements.retrocosmos.oil_shale.description": "Добудьте горючий сланец — источник ракетного керосина",
    "advancements.retrocosmos.refinery.title": "Нефтеперегонный ряд",
    "advancements.retrocosmos.refinery.description": "Постройте топливный завод",
    "advancements.retrocosmos.fuel.title": "Керосин атомной эры",
    "advancements.retrocosmos.fuel.description": "Получите канистру керосина RP-1 на топливном заводе",
    "advancements.retrocosmos.lox.title": "Холоднее космоса",
    "advancements.retrocosmos.lox.description": "Получите канистру жидкого кислорода в воздухоразделителе",
    "advancements.retrocosmos.aero_alloy.title": "Сплав реактивной эры",
    "advancements.retrocosmos.aero_alloy.description": "Выплавьте слиток аэросплава из алюминиево-титановой смеси",
    "advancements.retrocosmos.rocket_engine.title": "Зажигание",
    "advancements.retrocosmos.rocket_engine.description": "Соберите двигатель из камеры сгорания, турбонасоса и сопла",
    "advancements.retrocosmos.airframe.title": "Планер",
    "advancements.retrocosmos.airframe.description": "Соберите планер из секций корпуса, баков и стабилизаторов",
    "advancements.retrocosmos.launch_pad.title": "Девять стальных плит",
    "advancements.retrocosmos.launch_pad.description": "Соберите девять блоков стартовой площадки для стола 3x3",
    "advancements.retrocosmos.launch_complex.title": "Стартовый комплекс №1",
    "advancements.retrocosmos.launch_complex.description": "Пусть Центр управления подтвердит собранную площадку 3x3",
    "advancements.retrocosmos.console.title": "Центр управления",
    "advancements.retrocosmos.console.description": "Постройте пульт Центра управления",
    "advancements.retrocosmos.ready_for_launch.title": "Все системы — GO",
    "advancements.retrocosmos.ready_for_launch.description": "Пройдите предстартовую проверку: площадка 3x3, башня, RP-1, LOX, скафандр",
    "advancements.retrocosmos.countdown.title": "Есть отрыв!",
    "advancements.retrocosmos.countdown.description": "Доведите отсчёт до нуля с пульта Центра управления",
    "advancements.retrocosmos.canned_air.title": "Первый глоток консервированного воздуха",
    "advancements.retrocosmos.canned_air.description": "Заправьте скафандр из канистры жидкого кислорода",
    "tooltip.retrocosmos.space_suit.oxygen": "Кислород: %s%% (%s)",
    "tooltip.retrocosmos.liquid_oxygen_canister": "ПКМ в воздух — заправить надетый скафандр",
    "message.retrocosmos.oxygen.low": "Кислород на исходе: осталось %s с!",
    "message.retrocosmos.oxygen.empty": "КИСЛОРОД КОНЧИЛСЯ — заправьте скафандр!",
    "message.retrocosmos.oxygen.no_suit": "НЕТ СКАФАНДРА — удушье!",
    "message.retrocosmos.oxygen.recharged": "Баллон скафандра заправлен системой жизнеобеспечения",
    "message.retrocosmos.oxygen.refilled": "Баллон скафандра заправлен: 300 с",
    "message.retrocosmos.oxygen.need_suit": "Сначала наденьте скафандр",
    "message.retrocosmos.oxygen.already_full": "Баллон скафандра уже полон",
    "message.retrocosmos.oxygen.airless_on": "Симуляция безвоздушной среды ВКЛ — кислород скафандра пошёл на убыль.",
    "message.retrocosmos.oxygen.airless_off": "Симуляция безвоздушной среды ВЫКЛ — дышите спокойно.",
    "command.retrocosmos.on": "вкл",
    "command.retrocosmos.off": "выкл",
    "command.retrocosmos.oxygen.toggled": "Безвоздушная среда для %s: %s",
    "command.retrocosmos.oxygen.set": "Кислород скафандра %s: %s с",
    "command.retrocosmos.oxygen.no_suit": "%s не в скафандре",
    "command.retrocosmos.hud": "Панель телеметрии скафандра: %s",
    "gui.retrocosmos.hud.title": "ТЕЛЕМЕТРИЯ",
    "gui.retrocosmos.hud.vacuum": "ВАК",
    "gui.retrocosmos.hud.atmosphere": "АТМ",
    "gui.retrocosmos.hud.o2_low": "! МАЛО O2 - ЗАПРАВКА !",
    "gui.retrocosmos.hud.suit_breach": "! СКАФАНДР НЕ ПОЛОН !",
}


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
    save(rocket_chrome(), "block", "rocket_chrome")

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
    save(rocket_item(), "item", "rocket")
    save(suit_icon("helmet"), "item", "space_helmet")
    save(suit_icon("suit"), "item", "space_suit")
    save(suit_icon("leggings"), "item", "space_leggings")
    save(suit_icon("boots"), "item", "space_boots")
    save(suit_layer(), "entity", "equipment", "humanoid", "space_suit")
    save(suit_leggings_layer(), "entity", "equipment", "humanoid_leggings", "space_suit")
    logo().save(os.path.join(ROOT, "retrocosmos_logo.png"))
    stage1b_textures()

    # ---- models / blockstates / item definitions ----
    for b in ("bauxite_ore", "deepslate_bauxite_ore", "titanium_ore", "deepslate_titanium_ore",
              "aluminum_block", "titanium_block"):
        cube_all(b)
        simple_blockstate(b)
        item_def(b, f"{MOD}:block/{b}")
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
    advancement("space_suit", "space_helmet", "titanium",
                {f"has_{p}": {"trigger": "minecraft:inventory_changed", "conditions": {"items": [{"items": ing(p)}]}}
                 for p in ("space_helmet", "space_suit", "space_leggings", "space_boots")}, frame="goal")
    advancement("ready_for_launch", "rocket", "rocket",
                {"checklist_passed": {"trigger": "minecraft:impossible"}}, frame="challenge")

    stage1b_data()

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
    "block.retrocosmos.rocket": "\"Liberty I\" Rocket",
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
    "item.retrocosmos.space_helmet": "Astronaut Helmet",
    "item.retrocosmos.space_suit": "Pressure Suit",
    "item.retrocosmos.space_leggings": "Pressure Suit Trousers",
    "item.retrocosmos.space_boots": "Magnetic Boots",
    "message.retrocosmos.rocket.fueled": "Fuel tanks: %s / %s",
    "message.retrocosmos.rocket.fuel_full": "Fuel tanks are full!",
    "message.retrocosmos.checklist.title": "=== MISSION CONTROL: PRE-FLIGHT CHECKLIST ===",
    "message.retrocosmos.checklist.pad": "Rocket stands on a launch pad",
    "message.retrocosmos.checklist.fuel": "Fuel tanks filled (%s / %s)",
    "message.retrocosmos.checklist.suit": "Astronaut wears the full pressure suit",
    "message.retrocosmos.checklist.ready": "All systems are GO. T-minus zero, ready for liftoff!",
    "message.retrocosmos.checklist.stage2": "Mission Control is still plotting trajectories to other worlds... (Stage 2)",
    "message.retrocosmos.checklist.not_ready": "Launch scrubbed: checklist incomplete.",
    "advancements.retrocosmos.root.title": "Retro Cosmos: Preparation",
    "advancements.retrocosmos.root.description": "Find ore for the Space Age: bauxite or titanium",
    "advancements.retrocosmos.aluminum.title": "Winged Metal",
    "advancements.retrocosmos.aluminum.description": "Smelt an aluminum ingot",
    "advancements.retrocosmos.titanium.title": "Stronger Than Steel",
    "advancements.retrocosmos.titanium.description": "Smelt a titanium ingot from deep ore",
    "advancements.retrocosmos.vacuum_tube.title": "The Warm Glow",
    "advancements.retrocosmos.vacuum_tube.description": "Craft a vacuum tube",
    "advancements.retrocosmos.guidance_computer.title": "Electronic Brain",
    "advancements.retrocosmos.guidance_computer.description": "Assemble an analog guidance computer",
    "advancements.retrocosmos.rocket_engine.title": "Ignition Sequence Start",
    "advancements.retrocosmos.rocket_engine.description": "Build a rocket engine",
    "advancements.retrocosmos.fuel.title": "Atomic-Age Kerosene",
    "advancements.retrocosmos.fuel.description": "Fill a rocket fuel canister",
    "advancements.retrocosmos.space_suit.title": "The Right Stuff",
    "advancements.retrocosmos.space_suit.description": "Obtain every piece of the pressure suit",
    "advancements.retrocosmos.launch_pad.title": "Launch Complex 1",
    "advancements.retrocosmos.launch_pad.description": "Craft a launch pad",
    "advancements.retrocosmos.rocket.title": "Liberty I",
    "advancements.retrocosmos.rocket.description": "Assemble your first rocket",
    "advancements.retrocosmos.ready_for_launch.title": "We Have Liftoff!",
    "advancements.retrocosmos.ready_for_launch.description": "Pass the pre-flight checklist: rocket on the pad, tanks full, suited up",
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
    "block.retrocosmos.rocket": "Ракета «Либерти-1»",
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
    "item.retrocosmos.space_helmet": "Шлем астронавта",
    "item.retrocosmos.space_suit": "Скафандр",
    "item.retrocosmos.space_leggings": "Штаны скафандра",
    "item.retrocosmos.space_boots": "Магнитные ботинки",
    "message.retrocosmos.rocket.fueled": "Топливные баки: %s / %s",
    "message.retrocosmos.rocket.fuel_full": "Баки полны!",
    "message.retrocosmos.checklist.title": "=== ЦЕНТР УПРАВЛЕНИЯ: ПРЕДСТАРТОВАЯ ПРОВЕРКА ===",
    "message.retrocosmos.checklist.pad": "Ракета установлена на стартовую площадку",
    "message.retrocosmos.checklist.fuel": "Баки заправлены (%s / %s)",
    "message.retrocosmos.checklist.suit": "Астронавт в полном скафандре",
    "message.retrocosmos.checklist.ready": "Все системы — GO. Отсчёт окончен, готовность к старту!",
    "message.retrocosmos.checklist.stage2": "Центр управления полётом ещё рассчитывает траектории к другим мирам... (Этап 2)",
    "message.retrocosmos.checklist.not_ready": "Старт отложен: проверка не пройдена.",
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
    "advancements.retrocosmos.rocket_engine.title": "Зажигание",
    "advancements.retrocosmos.rocket_engine.description": "Постройте ракетный двигатель",
    "advancements.retrocosmos.fuel.title": "Керосин атомной эры",
    "advancements.retrocosmos.fuel.description": "Наполните канистру ракетного топлива",
    "advancements.retrocosmos.space_suit.title": "Парень что надо",
    "advancements.retrocosmos.space_suit.description": "Добудьте все части скафандра",
    "advancements.retrocosmos.launch_pad.title": "Стартовый комплекс №1",
    "advancements.retrocosmos.launch_pad.description": "Создайте стартовую площадку",
    "advancements.retrocosmos.rocket.title": "«Либерти-1»",
    "advancements.retrocosmos.rocket.description": "Соберите свою первую ракету",
    "advancements.retrocosmos.ready_for_launch.title": "Есть отрыв!",
    "advancements.retrocosmos.ready_for_launch.description": "Пройдите предстартовую проверку: ракета на площадке, баки полны, скафандр надет",
}


def write_lang():
    EN.update(EN_1B)
    RU.update(RU_1B)
    assert EN.keys() == RU.keys(), set(EN) ^ set(RU)
    write_json(os.path.join(ASSETS, "lang", "en_us.json"), EN)
    write_json(os.path.join(ASSETS, "lang", "ru_ru.json"), RU)


if __name__ == "__main__":
    main()
