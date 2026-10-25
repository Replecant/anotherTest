#!/usr/bin/env python3
"""Art for the Freedom Station interior pack (American retro-futurism / Atomic Age space program):
textures, animations, block models, blockstates and item definitions. Called from gen_resources.main().

Conventions: models authored for facing=north (front toward -Z), rotated in the blockstates. Clean
vanilla-style pixel art: flat tones, 1 texel = 1 model pixel through the default UV projection
(textures are drawn in "block space"); detail faces (screens, charts, panels) carry a full 16x16 texture.
No overlapping coplanar faces: faces that touch another element are omitted.
"""
import math
import os

from PIL import Image, ImageDraw

from gen_resources import (ASSETS, MOD, BLACK, CHROME, CHROME_D, CHROME_L, CREAM, CREAM_D, GLASS, GLASS_L, NAVY,
                           NAVY_L, ORANGE, ORANGE_L, RED, RED_D, RED_L, STEEL, STEEL_D, TEAL, TEAL_D, TEAL_L, WHITE,
                           WHITE_D, WHITE_DD, YELLOW, item_def, new, px, rgba, save, write_json)
from furniture_art import (Model, T, block_item, flat_item, state_axis, state_facing, state_lit, state_simple,
                           BLOCKS_DIR)

# palette additions
BAKELITE = (52, 44, 44)
BAKELITE_L = (84, 72, 70)
BAKELITE_D = (30, 26, 26)
PHOS = (70, 230, 110)
PHOS_D = (22, 72, 40)
PHOS_DD = (12, 36, 24)
PHOS_L = (180, 255, 190)
AMBER = (255, 190, 70)
AMBER_L = (255, 232, 160)
AMBER_D = (150, 96, 20)
LAMP_OFF = (120, 110, 100)
GREEN_LAMP = (90, 220, 110)
LEAF = (72, 160, 64)
LEAF_D = (40, 108, 44)
LEAF_L = (130, 210, 100)
GROW = (236, 120, 255)
GROW_L = (255, 200, 255)
GROW_OFF = (150, 140, 160)
CYAN = (90, 240, 240)
CYAN_L = (210, 255, 255)
CYAN_D = (30, 110, 120)
CYAN_OFF = (36, 70, 80)
BRASS = (214, 168, 76)
BRASS_D = (150, 110, 44)
BRASS_L = (244, 216, 140)
OCEAN = (56, 150, 170)
LAND = (214, 180, 120)
LAND_D = (160, 128, 80)
ICE = (240, 244, 248)
GRATE = (118, 124, 132)
GRATE_L = (160, 166, 174)
GRATE_D = (70, 74, 80)
ENAMEL = (236, 236, 232)
ENAMEL_D = (206, 208, 206)
ENAMEL_L = (250, 250, 248)
ENAMEL_SEAM = (178, 182, 184)

TEXTURES = []


def tex(name, img):
    save(img, "block", name)
    TEXTURES.append((name, 1))


def tex_anim(name, frames, frametime, interpolate=False):
    w, h = frames[0].size
    strip = new(w, h * len(frames))
    for i, f in enumerate(frames):
        strip.paste(f, (0, i * h))
    save(strip, "block", name)
    anim = {"animation": {"frametime": frametime}}
    if interpolate:
        anim["animation"]["interpolate"] = True
    write_json(os.path.join(ASSETS, "textures", "block", name + ".png.mcmeta"), anim)
    TEXTURES.append((name, len(frames)))


def R(img, x0, y0, x1, y1, c):
    """Inclusive rectangle fill."""
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            px(img, [(x, y)], c)


def flat(c, bottom=None, top=None):
    img = new()
    R(img, 0, 0, 15, 15, c)
    if top:
        R(img, 0, 0, 15, 0, top)
    if bottom:
        R(img, 0, 15, 15, 15, bottom)
    return img


# ----------------------------------------------------------------------------
# Textures
# ----------------------------------------------------------------------------

def enamel():
    """Flat white enamel with a darker bottom row (used on every white shell side)."""
    return flat(ENAMEL, bottom=ENAMEL_D, top=ENAMEL_L)


def enamel_top():
    return flat(ENAMEL_L)


def bakelite():
    return flat(BAKELITE, bottom=BAKELITE_D, top=BAKELITE_L)


def steel():
    return flat(STEEL, bottom=STEEL_D, top=(120, 126, 136))


def dial(img, x, y, needle, face=CREAM):
    """4x4 instrument dial at (x, y)."""
    R(img, x, y, x + 3, y + 3, BLACK)
    R(img, x + 1, y + 1, x + 2, y + 2, face)
    px(img, [needle(x, y)], RED)


def control_panel_face(lit, frame=0):
    img = flat(CREAM)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, 15, 15), outline=rgba(CHROME))
    # three big dials
    for i, x in enumerate((1, 6, 11)):
        R(img, x, 1, x + 3, 4, BLACK)
        R(img, x + 1, 2, x + 2, 3, CREAM if not lit else (255, 246, 214))
        px(img, [(x + 1, 2) if i != 1 else (x + 2, 2)], RED)
    # lamp grid, two rows of six
    colors = (RED, AMBER, GREEN_LAMP, AMBER, RED, GREEN_LAMP)
    for row, y in enumerate((6, 8)):
        for i, x in enumerate((2, 4, 6, 9, 11, 13)):
            on = lit and ((i * 3 + row * 5 + frame) % 4 != 0)
            c = colors[(i + row) % 6]
            px(img, [(x, y)], c if on else (LAMP_OFF if lit else (150, 140, 128)))
            if on:
                px(img, [(x + 1, y)], tuple(min(255, v + 60) for v in c))
    # toggle switches row
    for x in (2, 5, 8, 11):
        R(img, x, 10, x + 1, 12, CHROME_D)
        px(img, [(x, 11 if x % 2 == 0 else 10)], BLACK)
        px(img, [(x + 1, 11 if x % 2 == 0 else 10)], CHROME_L)
    px(img, [(14, 10), (14, 12)], RED)
    # red warning bar
    R(img, 1, 14, 14, 14, RED)
    R(img, 7, 14, 8, 14, CREAM if not lit or frame % 2 == 0 else YELLOW)
    return img


def radar_screen(lit, frame=0):
    img = flat(BAKELITE)
    d = ImageDraw.Draw(img)
    bg = PHOS_DD if lit else (20, 28, 26)
    d.ellipse((1, 1, 14, 14), fill=rgba(bg), outline=rgba(CHROME_D))
    grid = PHOS_D if lit else (34, 46, 42)
    d.ellipse((4, 4, 11, 11), outline=rgba(grid))
    for i in range(2, 14):
        px(img, [(i, 7), (7, i)], grid)
    px(img, [(7, 7)], grid)
    if lit:
        # sweep: bright line with a fading trail
        for k, c in ((0, PHOS_L), (1, PHOS), (2, PHOS_D)):
            a = math.radians((frame - k) * 45)
            for r in range(1, 7):
                px(img, [(round(7.5 + r * math.sin(a) - 0.5), round(7.5 - r * math.cos(a) - 0.5))], c)
        px(img, [(7, 7)], PHOS_L)
        for (bx, by, bf) in ((10, 4, 1), (4, 10, 5), (11, 9, 3)):
            if (frame - bf) % 8 < 4:
                px(img, [(bx, by)], PHOS_L if (frame - bf) % 8 < 2 else PHOS)
    return img


def computer_front(lit, frame=0):
    img = flat(CREAM)
    d = ImageDraw.Draw(img)
    R(img, 0, 0, 15, 15, CREAM)
    R(img, 0, 0, 0, 15, CREAM_D)
    R(img, 15, 0, 15, 15, CREAM_D)
    # tape reel bay (dark) with two reels
    R(img, 1, 1, 14, 7, BAKELITE)
    for cx in (4, 11):
        d.ellipse((cx - 3, 1, cx + 3, 7), fill=rgba(CHROME_D), outline=rgba(CHROME))
        d.ellipse((cx - 2, 2, cx + 2, 6), fill=rgba(BAKELITE_D))
        for s in range(3):   # spokes rotate 30 degrees per frame
            a = math.radians(frame * 30 + s * 120)
            px(img, [(round(cx + 1.5 * math.sin(a)), round(4 - 1.5 * math.cos(a)))], CHROME_L)
            px(img, [(round(cx + 2.2 * math.sin(a)), round(4 - 2.2 * math.cos(a)))], CHROME)
        px(img, [(cx, 4)], RED)
    R(img, 7, 1, 8, 7, STEEL_D)   # tape path
    R(img, 7, 3, 8, 3, (150, 120, 90))
    # lamp grid
    R(img, 1, 8, 14, 11, TEAL_D)
    for i, x in enumerate(range(2, 14, 2)):
        for row, y in enumerate((9, 10)):
            on = lit and ((i * 7 + row * 3 + frame * 5) % 5 > 1)
            c = (AMBER, GREEN_LAMP, RED)[(i + row) % 3]
            px(img, [(x, y)], c if on else (TEAL_D if not lit else (60, 90, 90)))
    # teal lower panel with a toggle row and vents
    R(img, 1, 12, 14, 15, TEAL)
    for x in (3, 6, 9, 12):
        px(img, [(x, 13)], CHROME_L)
        px(img, [(x, 14)], CHROME_D)
    px(img, [(1, 12), (14, 12)], TEAL_L)
    return img


def computer_side():
    img = flat(CREAM)
    R(img, 0, 0, 15, 0, (250, 244, 224))
    R(img, 0, 8, 15, 11, TEAL_D)
    R(img, 0, 12, 15, 15, TEAL)
    for y in (2, 4, 6):
        R(img, 3, y, 12, y, CREAM_D)
    return img


def red_enamel():
    return flat(RED, bottom=RED_D, top=RED_L)


def chair_arm_top():
    """Block space: arm pads at x 2..4 and 12..14, z 6..12, with three buttons each."""
    img = flat(RED)
    for x in (2, 13):
        for z in (7, 9, 11):
            px(img, [(x, z)], (AMBER, TEAL_L, CREAM)[(z // 2) % 3])
            px(img, [(x + 1, z)], RED_D)
    return img


def bunk_top():
    """Mattress top (block space): teal with a white sheet fold near the pillow end."""
    img = flat(TEAL)
    R(img, 0, 15, 15, 15, TEAL_D)
    for x in range(16):
        if x % 8 == 7:
            R(img, x, 0, x, 15, TEAL_D)
    R(img, 1, 9, 14, 10, ENAMEL)
    R(img, 1, 11, 14, 11, ENAMEL_D)
    return img


def hydro_top():
    img = flat(CHROME)
    R(img, 1, 1, 14, 14, (74, 60, 50))
    for (x, y) in [(2, 2), (5, 3), (9, 2), (12, 4), (3, 7), (7, 6), (11, 8), (13, 12), (2, 12), (6, 11), (9, 13), (8, 9)]:
        px(img, [(x, y)], (120, 100, 84))
    R(img, 7, 1, 8, 14, (60, 50, 42))
    R(img, 1, 7, 14, 8, (60, 50, 42))
    return img


def hydro_crop():
    """Leafy crop row (block space rows 4..11): cutout."""
    img = new()
    for i, x in enumerate((2, 5, 8, 11)):
        top = 5 if i % 2 == 0 else 6
        R(img, x, top, x + 2, 11, LEAF)
        R(img, x + 1, top - 1, x + 1, 11, LEAF_L)
        px(img, [(x, top), (x + 2, top)], LEAF_L)
        px(img, [(x, 11), (x + 2, 11)], LEAF_D)
        px(img, [(x + 1, top + 1)], LEAF_D)
        if i % 2:
            px(img, [(x, top + 2)], RED)   # a little tomato
    return img


def grow_lamp(on):
    img = flat(CHROME)
    R(img, 1, 7, 14, 8, GROW if on else GROW_OFF)
    if on:
        R(img, 1, 7, 14, 7, GROW_L)
    return img


def o2_tank():
    """Block space: white cylinder sides with a red band and a small label."""
    img = flat(ENAMEL)
    R(img, 0, 15, 15, 15, ENAMEL_D)
    R(img, 0, 5, 15, 6, RED)
    R(img, 0, 7, 15, 7, RED_D)
    for x in range(1, 16, 3):
        px(img, [(x, 10), (x + 1, 10), (x + 1, 11)], NAVY)
    return img


def gauge():
    img = flat(CREAM)
    R(img, 0, 0, 15, 15, BLACK)
    R(img, 1, 1, 14, 14, CREAM)
    R(img, 1, 1, 7, 7, (250, 244, 224))
    R(img, 8, 1, 14, 2, RED)
    return img


def vending_front(lit):
    """Block space front (x 1..15, y 0..16): white upper panel with the rocket logo, lit window, flap."""
    img = flat(RED)
    R(img, 1, 0, 14, 4, ENAMEL)
    R(img, 1, 4, 14, 4, ENAMEL_D)
    # rocket logo
    R(img, 7, 1, 8, 3, RED)
    px(img, [(7, 0), (8, 0)], RED_D)
    px(img, [(6, 3), (9, 3)], RED_D)
    px(img, [(5, 1), (10, 1)], TEAL)
    px(img, [(4, 2), (11, 2)], TEAL)
    px(img, [(3, 1), (12, 1)], AMBER)
    # product window
    glass = (255, 246, 214) if lit else (190, 180, 160)
    R(img, 2, 6, 10, 11, glass)
    R(img, 2, 6, 10, 6, CHROME_L if lit else CHROME)
    for i, x in enumerate((3, 5, 7, 9)):
        c = (RED, TEAL, AMBER, NAVY)[i]
        R(img, x, 8, x, 10, c)
        px(img, [(x, 7)], CHROME)
    R(img, 2, 11, 10, 11, CHROME_D)
    # coin slot / buttons
    R(img, 12, 6, 13, 6, BLACK)
    for y in (8, 10):
        px(img, [(12, y)], AMBER if lit else LAMP_OFF)
        px(img, [(13, y)], CHROME)
    # delivery flap
    R(img, 3, 13, 9, 14, CHROME_D)
    R(img, 3, 13, 9, 13, CHROME_L)
    R(img, 1, 15, 14, 15, RED_D)
    return img


def vending_side():
    img = flat(RED, bottom=RED_D)
    R(img, 0, 0, 15, 4, ENAMEL)
    R(img, 0, 4, 15, 4, ENAMEL_D)
    R(img, 0, 9, 15, 9, ENAMEL)
    return img


def star_chart(lit, frame=0):
    """Block space (x 1..15, y 1..15): dark chart with the amber Vesper star and planet orbits."""
    img = flat(BRASS)
    bg = (24, 30, 56) if lit else (16, 18, 34)
    R(img, 2, 2, 13, 13, bg)
    d = ImageDraw.Draw(img)
    ring = NAVY_L if lit else (40, 48, 80)
    d.ellipse((3, 3, 12, 12), outline=rgba(ring))
    d.ellipse((5, 5, 10, 10), outline=rgba(ring))
    px(img, [(7, 7), (8, 7), (7, 8), (8, 8)], AMBER if lit else AMBER_D)
    px(img, [(8, 7)], AMBER_L if lit else AMBER)
    px(img, [(10, 5)], TEAL_L if lit else TEAL_D)      # inner planet
    px(img, [(4, 10)], (210, 120, 70) if lit else (120, 70, 50))   # outer planet
    px(img, [(12, 8)], ICE if lit else (120, 124, 130))
    stars = [(3, 4), (11, 3), (12, 12), (3, 12), (9, 11), (5, 7)]
    for i, (x, y) in enumerate(stars):
        bright = lit and (i + frame) % 3 == 0
        px(img, [(x, y)], (255, 255, 240) if bright else ((150, 160, 190) if lit else (70, 76, 100)))
    R(img, 5, 13, 10, 13, CREAM if lit else CREAM_D)   # label strip
    return img


def light_panel(on):
    img = flat((255, 250, 232) if on else (200, 200, 196))
    if on:
        R(img, 0, 0, 15, 0, (255, 240, 200))
        R(img, 0, 15, 15, 15, (255, 240, 200))
        R(img, 0, 0, 0, 15, (255, 240, 200))
        R(img, 15, 0, 15, 15, (255, 240, 200))
    else:
        R(img, 0, 0, 15, 15, (200, 200, 196))
        R(img, 0, 0, 15, 0, (220, 220, 216))
        R(img, 0, 15, 15, 15, (170, 170, 168))
    return img


def bulb(on):
    return flat(AMBER_L if on else (214, 210, 200), bottom=AMBER if on else (180, 176, 168),
                top=(255, 255, 240) if on else (232, 230, 224))


def orbit_ring(on):
    """Block space ellipse ring in x 5..11, y 4..12 (cutout)."""
    img = new()
    d = ImageDraw.Draw(img)
    d.ellipse((5, 4, 10, 11), outline=rgba(CHROME_L if on else CHROME))
    px(img, [(7, 4), (8, 11)], CHROME)
    return img


def brass_tube():
    img = flat(BRASS, bottom=BRASS_D, top=BRASS_L)
    for z in (4, 11):
        R(img, 0, z, 15, z, CHROME)
    R(img, 0, 1, 15, 1, CHROME_D)
    for z in range(16):
        px(img, [(1, z)], BRASS_L)
    return img


def lens():
    img = flat(CHROME_D)
    R(img, 1, 1, 14, 14, (40, 60, 90))
    R(img, 2, 2, 5, 5, (120, 170, 210))
    return img


def globe_map():
    """32x32 sheet; the drum wraps texels 0..23 (uv 0..12) of rows 13..18 (uv 6.5..9.5): Homestead's
    teal oceans and tan continents, polar ice at the band edges."""
    img = new(32, 32)
    R(img, 0, 0, 31, 31, OCEAN)
    R(img, 0, 13, 23, 13, (150, 205, 215))
    R(img, 0, 18, 23, 18, (150, 205, 215))
    land = [(1, 14, 5, 16), (3, 16, 4, 17), (8, 14, 9, 14), (11, 15, 16, 17), (13, 14, 14, 14), (19, 14, 22, 15),
            (20, 16, 21, 17)]
    for (x0, y0, x1, y1) in land:
        R(img, x0, y0, x1, y1, LAND)
        px(img, [(x1, y1)], LAND_D)
    px(img, [(2, 15), (12, 16), (21, 15)], (170, 150, 90))
    return img


def globe_frames():
    base = globe_map()
    frames = []
    for f in range(8):
        img = new(32, 32)
        R(img, 0, 0, 31, 31, OCEAN)
        band = base.crop((0, 0, 24, 32))
        img.paste(band, (-3 * f, 0))
        img.paste(band, (24 - 3 * f, 0))
        frames.append(img)
    return frames


def grate_side():
    img = flat(STEEL, bottom=STEEL_D, top=GRATE_L)
    R(img, 0, 7, 15, 7, GRATE_D)
    R(img, 0, 8, 15, 8, GRATE_L)
    return img


def floor_grate():
    img = new()
    for y in range(16):
        for x in range(16):
            if x % 4 == 3 or y % 4 == 3:
                c = GRATE
                if x % 4 == 3 and y % 4 != 3:
                    c = GRATE_L if y % 4 == 0 else GRATE
                if y % 4 == 3 and x % 4 == 0:
                    c = GRATE_D
                px(img, [(x, y)], c)
    for x in range(16):
        px(img, [(x, 0)], GRATE_L)
    return img


def hull_panel(striped=False):
    img = flat(ENAMEL)
    R(img, 0, 0, 15, 0, ENAMEL_L)
    R(img, 0, 15, 15, 15, ENAMEL_SEAM)
    R(img, 15, 0, 15, 15, ENAMEL_SEAM)
    R(img, 0, 7, 14, 7, ENAMEL_D)
    for (x, y) in [(2, 2), (12, 2), (2, 12), (12, 12)]:
        px(img, [(x, y)], ENAMEL_SEAM)
        px(img, [(x, y - 1)], ENAMEL_L)
    if striped:
        R(img, 0, 9, 14, 12, RED)
        R(img, 0, 12, 14, 12, RED_D)
        R(img, 0, 9, 14, 9, RED_L)
    return img


def hull_window():
    img = new()
    R(img, 0, 0, 15, 15, CHROME)
    R(img, 0, 0, 15, 0, CHROME_L)
    R(img, 0, 15, 15, 15, CHROME_D)
    for y in range(2, 14):
        for x in range(2, 14):
            img.putpixel((x, y), rgba(GLASS, 90))
    R(img, 7, 1, 8, 14, CHROME)
    R(img, 1, 1, 14, 1, CHROME_D)
    R(img, 1, 14, 14, 14, CHROME_L)
    R(img, 1, 1, 1, 14, CHROME_D)
    R(img, 14, 1, 14, 14, CHROME_L)
    for (x, y) in [(3, 3), (4, 3), (3, 4), (10, 3), (11, 3), (10, 4)]:
        img.putpixel((x, y), rgba(GLASS_L, 170))
    return img


def reactor_core(lit, frame=0):
    if not lit:
        img = flat(CYAN_OFF)
        R(img, 0, 0, 15, 0, (50, 90, 100))
        R(img, 0, 15, 15, 15, (24, 50, 58))
        R(img, 7, 0, 8, 15, (46, 86, 96))
        return img
    t = (math.sin(frame / 6 * 2 * math.pi) + 1) / 2
    core = tuple(int(a + (b - a) * t) for a, b in zip(CYAN_D, CYAN))
    hot = tuple(int(a + (b - a) * t) for a, b in zip(CYAN, CYAN_L))
    img = flat(core)
    R(img, 6, 0, 9, 15, hot)
    R(img, 7, 0, 8, 15, CYAN_L if t > 0.5 else hot)
    for y in range(0, 16, 4):
        R(img, 0, (y + frame) % 16, 15, (y + frame) % 16, hot)
    return img


def reactor_cage():
    img = flat(CHROME)
    R(img, 0, 0, 15, 0, CHROME_L)
    R(img, 0, 15, 15, 15, CHROME_D)
    for x in (3, 12):
        R(img, x, 0, x, 15, CHROME_D)
    return img


def generate_textures():
    tex("st_enamel", enamel())
    tex("st_enamel_top", enamel_top())
    tex("st_bakelite", bakelite())
    tex("st_steel", steel())
    tex("st_cream", flat(CREAM, bottom=CREAM_D, top=(250, 244, 224)))
    tex("st_teal", flat(TEAL, bottom=TEAL_D, top=TEAL_L))
    tex("st_red", red_enamel())
    tex("control_panel_face", control_panel_face(False))
    tex_anim("control_panel_face_on", [control_panel_face(True, f) for f in range(4)], 8)
    tex("radar_screen", radar_screen(False))
    tex_anim("radar_screen_on", [radar_screen(True, f) for f in range(8)], 4)
    tex("computer_front", computer_front(False))
    tex_anim("computer_front_on", [computer_front(True, f) for f in range(6)], 3)
    tex("computer_side", computer_side())
    tex("chair_arm_top", chair_arm_top())
    tex("bunk_top", bunk_top())
    tex("hydro_top", hydro_top())
    tex("hydro_crop", hydro_crop())
    tex("grow_lamp", grow_lamp(False))
    tex("grow_lamp_on", grow_lamp(True))
    tex("o2_tank", o2_tank())
    tex("gauge", gauge())
    tex("vending_front", vending_front(False))
    tex("vending_front_on", vending_front(True))
    tex("vending_side", vending_side())
    tex("star_chart", star_chart(False))
    tex_anim("star_chart_on", [star_chart(True, f) for f in range(3)], 12)
    tex("light_panel", light_panel(False))
    tex("light_panel_on", light_panel(True))
    tex("sconce_bulb", bulb(False))
    tex("sconce_bulb_on", bulb(True))
    tex("orbit_ring", orbit_ring(False))
    tex("orbit_ring_on", orbit_ring(True))
    tex("brass_tube", brass_tube())
    tex("lens", lens())
    tex_anim("globe", globe_frames(), 12, interpolate=True)
    tex("globe_pole", flat(ICE, bottom=(200, 210, 220)))
    tex("floor_grate", floor_grate())
    tex("grate_side", grate_side())
    tex("hull_panel", hull_panel())
    tex("hull_panel_striped", hull_panel(True))
    tex("hull_window", hull_window())
    tex("reactor_core", reactor_core(False))
    tex_anim("reactor_core_on", [reactor_core(True, f) for f in range(6)], 4, interpolate=True)
    tex("reactor_cage", reactor_cage())
    # flat item sprites for the wall pieces
    save(control_panel_face(True, 1), "item", "control_panel")
    chart = star_chart(True, 0)
    save(chart, "item", "star_chart")
    sconce = new()
    sconce.alpha_composite(orbit_ring(True))
    R(sconce, 7, 7, 9, 9, AMBER_L)
    px(sconce, [(7, 7)], (255, 255, 240)); px(sconce, [(9, 9)], AMBER)
    R(sconce, 6, 12, 10, 13, CHROME)
    save(sconce, "item", "wall_sconce")


# ----------------------------------------------------------------------------
# Models
# ----------------------------------------------------------------------------

SIDES = ("north", "south", "east", "west")
FULL = [0, 0, 16, 16]
CHROME_T = {"chrome": "stool_chrome", "ctop": "chrome_top"}
CAPS = {"up": "ctop", "down": "ctop"}


def control_panel(lit):
    face = "face_on" if lit else "face"
    m = Model({"cream": "st_cream", "face": "control_panel_face", "face_on": "control_panel_face_on", **CHROME_T},
              "st_cream", ao=False)
    m.box((0, 0, 13), (16, 16, 16), "cream", faces=("north", "east", "west", "up", "down"),
          face_tex={"north": face}, face_uv={"north": FULL}, shade=False if lit else None)
    # three protruding chrome knobs under the dials
    for x in (1, 6, 11):
        m.box((x + 1, 1.5, 12.5), (x + 3, 3.5, 13), "chrome", faces=("north", "east", "west", "up", "down"))
    return m.write("control_panel" + ("_on" if lit else ""))


def radar_scope(lit):
    scr = "screen_on" if lit else "screen"
    m = Model({"bak": "st_bakelite", "screen": "radar_screen", "screen_on": "radar_screen_on", "teal": "st_teal",
               "red": "st_red", **CHROME_T}, "st_bakelite", ao=False)
    m.box((2, 0, 2), (14, 2, 14), "bak")
    m.box((3, 2, 4), (13, 10, 13), "bak", faces=SIDES + ("up",))
    m.box((4, 2, 3), (12, 10, 4), "teal", faces=("north", "east", "west", "up"), face_tex={"north": scr},
          face_uv={"north": FULL}, shade=False if lit else None)
    m.box((4, 0.5, 1.5), (5.5, 1.5, 2), "red", faces=("north", "east", "west", "up", "down"))
    m.box((10.5, 0.5, 1.5), (12, 1.5, 2), "chrome", faces=("north", "east", "west", "up", "down"))
    return m.write("radar_scope" + ("_on" if lit else ""))


def computer_bank(lit):
    front = "front_on" if lit else "front"
    m = Model({"side": "computer_side", "front": "computer_front", "front_on": "computer_front_on",
               "cream": "st_cream", "teal": "st_teal"}, "computer_side", ao=False)
    m.box((0, 0, 2), (16, 16, 16), "side", face_tex={"north": front, "up": "cream", "down": "teal"},
          face_uv={"north": FULL}, shade=False if lit else None)
    # a small keyboard shelf
    m.box((2, 3, 1), (14, 4, 2), "teal", faces=("north", "east", "west", "up", "down"))
    return m.write("computer_bank" + ("_on" if lit else ""))


def captain_chair():
    m = Model({"red": "red_tufted", "arm": "chair_arm_top", "redflat": "st_red", **CHROME_T}, "red_tufted")
    m.box((4, 0, 4), (12, 1, 12), "chrome", face_tex=CAPS)
    m.box((7, 1, 7), (9, 6, 9), "chrome", faces=SIDES)
    m.box((3, 6, 3), (13, 7, 13), "chrome", face_tex=CAPS)
    m.box((3, 7, 3), (13, 9, 13), "red", faces=SIDES + ("up",))
    # armrests: chrome support + red pad with buttons on top
    for x in (2, 12):
        m.box((x, 9, 6), (x + 2, 10, 13), "chrome", faces=("north", "south", "east", "west"))
        m.box((x, 10, 6), (x + 2, 11, 13), "redflat", faces=("north", "south", "east", "west", "up"),
              face_tex={"up": "arm"})
    # high back with headrest, chrome back shell
    m.box((3, 9, 11), (13, 15, 14), "red", faces=("north", "east", "west", "up", "south"),
          face_tex={"south": "chrome"})
    m.box((4, 15, 11.5), (12, 16, 13.5), "red", faces=("north", "south", "east", "west", "up"))
    return m.write("captain_chair")


def crew_bunk():
    m = Model({"shell": "st_enamel", "stop": "st_enamel_top", "teal": "teal_tufted", "mat": "bunk_top",
               "cream": "st_cream", "lamp": "sconce_bulb_on", **CHROME_T}, "st_enamel")
    sh = {"up": "stop", "down": "stop"}
    m.box((0, 0, 0), (16, 3, 16), "shell", face_tex=sh)
    m.box((1, 3, 0), (15, 5, 15), "teal", faces=("north", "east", "west", "up"), face_tex={"up": "mat"})
    m.box((3, 5, 11), (13, 6.5, 14.5), "cream", faces=("north", "south", "east", "west", "up"))
    # capsule head shell: back wall, side walls, hood
    m.box((0, 3, 15), (16, 9, 16), "shell", faces=("north", "south", "east", "west", "up"), face_tex=sh)
    m.box((0, 3, 9), (1, 9, 15), "shell", faces=("north", "east", "west", "up"), face_tex=sh)
    m.box((15, 3, 9), (16, 9, 15), "shell", faces=("north", "east", "west", "up"), face_tex=sh)
    m.box((1, 8, 10), (15, 9, 15), "shell", faces=("north", "up", "down"), face_tex=sh)
    # reading lamp on a chrome stalk
    m.box((12.5, 6.5, 14.5), (13.5, 7.5, 15), "chrome", faces=("north", "east", "west", "up", "down"))
    m.box((12, 6, 13.5), (14, 7, 14.5), "lamp", shade=False)
    return m.write("crew_bunk")


def hydroponic_planter(lit):
    lamp = "lamp_on" if lit else "lamp"
    m = Model({"top": "hydro_top", "crop": "hydro_crop", "lamp": "grow_lamp", "lamp_on": "grow_lamp_on", **CHROME_T},
              "hydro_top", ao=False, render_type="minecraft:cutout")
    m.box((0, 0, 0), (16, 4, 16), "chrome", face_tex={"up": "top", "down": "ctop"})
    for z in (4.5, 11.5):
        m.box((1, 4, z), (15, 12, z), "crop", faces=("north", "south"))
    for x in (4.5, 11.5):
        m.box((x, 4, 1), (x, 12, 15), "crop", faces=("east", "west"))
    m.box((0.5, 4, 7.5), (1.5, 13, 8.5), "chrome", faces=SIDES)
    m.box((14.5, 4, 7.5), (15.5, 13, 8.5), "chrome", faces=SIDES)
    m.box((0.5, 13, 7), (15.5, 14, 9), "chrome", face_tex={"down": lamp, "up": "ctop"}, shade=False if lit else None)
    return m.write("hydroponic_planter" + ("_on" if lit else ""))


def oxygen_tank_rack():
    m = Model({"tank": "o2_tank", "stop": "st_enamel_top", "steel": "st_steel", "red": "st_red", "gauge": "gauge",
               **CHROME_T}, "o2_tank")
    m.box((1, 0, 4), (15, 1, 12), "steel")
    m.box((1, 9, 11), (15, 10, 12), "steel", faces=("north", "south", "east", "west", "up", "down"))
    for x in (1.5, 6.5, 11.5):
        m.box((x, 1, 6), (x + 3, 12, 9), "tank", faces=SIDES)
        m.box((x + 0.5, 12, 6.5), (x + 2.5, 13, 8.5), "tank", faces=SIDES + ("up",), face_tex={"up": "stop"})
        m.box((x + 1, 13, 7), (x + 2, 14.5, 8), "chrome", faces=SIDES)
        m.box((x + 0.25, 14.5, 7.25), (x + 2.75, 15, 7.75), "red")
        m.box((x + 1, 9.5, 5.5), (x + 2, 10.5, 6), "gauge", faces=("north", "east", "west", "up", "down"),
              face_tex={"east": "chrome", "west": "chrome", "up": "chrome", "down": "chrome"}, face_uv={"north": FULL})
        m.box((x + 0.5, 4, 5.5), (x + 2.5, 4.5, 6), "steel", faces=("north", "east", "west", "up", "down"))
    return m.write("oxygen_tank_rack")


def vending_machine(lit):
    front = "front_on" if lit else "front"
    m = Model({"side": "vending_side", "front": "vending_front", "front_on": "vending_front_on", "red": "st_red",
               **CHROME_T}, "vending_side", ao=False)
    m.box((1, 0, 2), (15, 16, 15), "side", face_tex={"north": front, "up": "red", "down": "red"},
          shade=False if lit else None)
    m.box((4, 2, 1.5), (12, 3, 2), "chrome", faces=("north", "east", "west", "up", "down"))
    return m.write("vending_machine" + ("_on" if lit else ""))


def star_chart_model(lit):
    face = "chart_on" if lit else "chart"
    m = Model({"brass": "brass", "chart": "star_chart", "chart_on": "star_chart_on"}, "brass", ao=False)
    m.box((1, 1, 15), (15, 15, 16), "brass", faces=("north", "east", "west", "up", "down"),
          face_tex={"north": face}, shade=False if lit else None)
    return m.write("star_chart" + ("_on" if lit else ""))


def ceiling_light(lit):
    panel = "panel_on" if lit else "panel"
    m = Model({"panel": "light_panel", "panel_on": "light_panel_on", **CHROME_T}, "stool_chrome", ao=False)
    m.box((2, 15, 2), (14, 16, 14), "chrome", faces=SIDES + ("down",), face_tex={"down": "ctop"})
    m.box((3, 14, 3), (13, 15, 13), panel, faces=SIDES + ("down",), shade=False if lit else None)
    return m.write("ceiling_light" + ("_on" if lit else ""))


def wall_sconce(lit):
    b = "bulb_on" if lit else "bulb"
    ring = "ring_on" if lit else "ring"
    m = Model({"bulb": "sconce_bulb", "bulb_on": "sconce_bulb_on", "ring": "orbit_ring", "ring_on": "orbit_ring_on",
               **CHROME_T}, "stool_chrome", ao=False, render_type="minecraft:cutout")
    m.box((6, 5, 15), (10, 11, 16), "chrome", faces=("north", "east", "west", "up", "down"))
    m.box((7.5, 7.5, 14), (8.5, 8.5, 15), "chrome", faces=("east", "west", "up", "down"))
    m.box((6.5, 6.5, 12.5), (9.5, 9.5, 14), b, faces=("north", "east", "west", "up", "down"),
          shade=False if lit else None)
    for ang in (45, -45):
        m.box((5, 4, 13.25), (11, 12, 13.25), ring, faces=("north", "south"), rot=("z", ang, (8, 8, 13.25)),
              shade=False if lit else None)
    return m.write("wall_sconce" + ("_on" if lit else ""))


def telescope():
    m = Model({"tube": "brass_tube", "lens": "lens", "bak": "st_bakelite", **CHROME_T}, "brass_tube")
    hub = (8, 9, 8)
    # tripod: two legs splayed sideways (slightly behind), one forward
    m.box((7.5, 0, 9), (8.5, 9.5, 10), "chrome", faces=SIDES + ("down",), rot=("z", 22.5, (8, 9.5, 9.5)))
    m.box((7.5, 0, 9), (8.5, 9.5, 10), "chrome", faces=SIDES + ("down",), rot=("z", -22.5, (8, 9.5, 9.5)))
    m.box((7.5, 0, 7), (8.5, 9.5, 8), "chrome", faces=SIDES + ("down",), rot=("x", -22.5, (8, 9.5, 7.5)))
    m.box((7, 9, 7), (9, 11, 9), "chrome", face_tex=CAPS)
    # tube pointing up-forward (north end lifted 45 degrees)
    m.box((7, 10.5, 3.5), (9, 12.5, 12.5), "tube", faces=SIDES + ("up", "down"), face_tex={"north": "lens", "south": "bak"},
          face_uv={"north": FULL}, rot=("x", 45, (8, 11.5, 8)))
    m.box((7.25, 10.75, 12.5), (8.75, 12.25, 13.5), "bak", faces=SIDES + ("up", "down"), rot=("x", 45, (8, 11.5, 8)))
    m.box((6.5, 11.5, 9.5), (9.5, 12.5, 10.5), "chrome", rot=("x", 45, (8, 11.5, 8)))   # finder-scope saddle
    return m.write("telescope")


def space_globe():
    m = Model({"globe": "globe", "pole": "globe_pole", **CHROME_T}, "globe")
    m.box((5, 0, 5), (11, 1, 11), "chrome", face_tex=CAPS)
    m.box((7.5, 1, 7.5), (8.5, 2.5, 8.5), "chrome", faces=SIDES)
    # globe: 6-wide drum wrapped by the scrolling map (one quarter = 6 texels per face), stepped caps
    m.box((5, 4, 5), (11, 10, 11), "globe", faces=SIDES,
          face_uv={"north": [0, 6.5, 3, 9.5], "west": [3, 6.5, 6, 9.5], "south": [6, 6.5, 9, 9.5], "east": [9, 6.5, 12, 9.5]})
    m.box((6, 3, 6), (10, 4, 10), "pole", faces=SIDES + ("down",))
    m.box((6, 10, 6), (10, 11, 10), "pole", faces=SIDES + ("up",))
    # chrome meridian arc, axis pins
    m.box((7.5, 11, 7.5), (8.5, 12, 8.5), "chrome", faces=SIDES)
    m.box((7.5, 2.5, 7.5), (8.5, 3, 8.5), "chrome", faces=SIDES)
    m.box((3.5, 2.5, 7.5), (4.5, 13, 8.5), "chrome", faces=SIDES + ("up", "down"))
    m.box((4.5, 12, 7.5), (8.5, 13, 8.5), "chrome", faces=("north", "south", "east", "up", "down"))
    m.box((4.5, 2, 7.5), (7.5, 2.5, 8.5), "chrome", faces=("north", "south", "east", "up", "down"))
    return m.write("space_globe")


def reactor_core_model(lit):
    core = "core_on" if lit else "core"
    m = Model({"cage": "reactor_cage", "core": "reactor_core", "core_on": "reactor_core_on", **CHROME_T},
              "reactor_cage", ao=False)
    m.box((1, 0, 1), (15, 2, 15), "cage", face_tex=CAPS)
    m.box((1, 14, 1), (15, 16, 15), "cage", face_tex=CAPS)
    for (x, z) in ((1, 1), (12, 1), (1, 12), (12, 12)):
        m.box((x, 2, z), (x + 3, 14, z + 3), "cage", faces=SIDES)
    m.box((4, 2, 4), (12, 14, 12), core, faces=SIDES, shade=False if lit else None)
    # mid-height chrome hoops between the posts
    m.box((4, 7.5, 1.25), (12, 8.5, 1.75), "chrome", faces=("north", "south", "up", "down"))
    m.box((4, 7.5, 14.25), (12, 8.5, 14.75), "chrome", faces=("north", "south", "up", "down"))
    m.box((1.25, 7.5, 4), (1.75, 8.5, 12), "chrome", faces=("east", "west", "up", "down"))
    m.box((14.25, 7.5, 4), (14.75, 8.5, 12), "chrome", faces=("east", "west", "up", "down"))
    return m.write("reactor_core" + ("_on" if lit else ""))


def full_blocks():
    write_json(os.path.join(BLOCKS_DIR, "floor_grate.json"),
               {"parent": "minecraft:block/cube_bottom_top", "render_type": "minecraft:cutout",
                "textures": {"top": T("floor_grate"), "bottom": T("floor_grate"), "side": T("grate_side")}})
    write_json(os.path.join(BLOCKS_DIR, "hull_panel.json"),
               {"parent": "minecraft:block/cube_all", "textures": {"all": T("hull_panel")}})
    write_json(os.path.join(BLOCKS_DIR, "hull_panel_striped.json"),
               {"parent": "minecraft:block/cube_column",
                "textures": {"end": T("hull_panel"), "side": T("hull_panel_striped")}})
    write_json(os.path.join(BLOCKS_DIR, "hull_window.json"),
               {"parent": "minecraft:block/cube_all", "render_type": "minecraft:translucent",
                "textures": {"all": T("hull_window")}})


# ----------------------------------------------------------------------------

def generate():
    generate_textures()
    for lit in (False, True):
        control_panel(lit)
        radar_scope(lit)
        computer_bank(lit)
        hydroponic_planter(lit)
        vending_machine(lit)
        star_chart_model(lit)
        ceiling_light(lit)
        wall_sconce(lit)
        reactor_core_model(lit)
    captain_chair()
    crew_bunk()
    oxygen_tank_rack()
    telescope()
    space_globe()
    full_blocks()

    state_facing("control_panel", lit=True)
    state_facing("radar_scope", lit=True)
    state_facing("computer_bank", lit=True)
    state_facing("captain_chair")
    state_facing("crew_bunk")
    state_lit("hydroponic_planter")
    state_facing("oxygen_tank_rack")
    state_facing("vending_machine", lit=True)
    state_facing("star_chart", lit=True)
    state_lit("ceiling_light")
    state_facing("wall_sconce", lit=True)
    state_facing("telescope")
    state_facing("space_globe")
    for b in ("floor_grate", "hull_panel", "hull_panel_striped", "hull_window", "reactor_core"):
        if b == "reactor_core":
            state_lit(b)
        else:
            state_simple(b)

    for name, model in (("radar_scope", "radar_scope_on"), ("computer_bank", "computer_bank_on"), ("captain_chair", None),
                        ("crew_bunk", None), ("hydroponic_planter", "hydroponic_planter_on"), ("oxygen_tank_rack", None),
                        ("vending_machine", "vending_machine_on"), ("ceiling_light", "ceiling_light_on"),
                        ("telescope", None), ("space_globe", None), ("floor_grate", None), ("hull_panel", None),
                        ("hull_panel_striped", None), ("hull_window", None), ("reactor_core", "reactor_core_on")):
        block_item(name, model)
    for name in ("control_panel", "star_chart", "wall_sconce"):
        flat_item(name)


if __name__ == "__main__":
    generate()
