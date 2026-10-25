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

from gen_resources import (ASSETS, MOD, BLACK, GLASS, GLASS_L, NAVY, NAVY_L, ORANGE, ORANGE_L, RED, RED_D, RED_L,
                           STEEL, STEEL_D, TEAL, TEAL_D, TEAL_L, VISOR, VISOR_L, YELLOW, item_def, new, px, rgba, save,
                           write_json)
# toned-down furniture whites / creams / chrome (see furniture_art)
from furniture_art import CHROME, CHROME_D, CHROME_L, CREAM, CREAM_D, CREAM_L, WHITE, WHITE_D, WHITE_DD, WHITE_L
from furniture_art import (Model, T, block_item, flat_item, state_axis, state_facing, state_lit, state_simple,
                           BLOCKS_DIR, ITEMS_DIR, STATES_DIR)

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
ICE = (222, 228, 234)
GRATE = (118, 124, 132)
GRATE_L = (160, 166, 174)
GRATE_D = (70, 74, 80)
ENAMEL = (222, 222, 218)
ENAMEL_D = (194, 196, 194)
ENAMEL_L = (230, 230, 226)
ENAMEL_SEAM = (166, 170, 174)

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
    R(img, 0, 0, 15, 0, CREAM_L)
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
    R(img, 1, 1, 7, 7, CREAM_L)
    R(img, 8, 1, 14, 2, RED)
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
                top=(255, 255, 240) if on else (224, 222, 216))


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
    tex("st_cream", flat(CREAM, bottom=CREAM_D, top=CREAM_L))
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
              "st_cream")
    m.box((0, 0, 13), (16, 16, 16), "cream", faces=("north", "east", "west", "up", "down"),
          face_tex={"north": face}, face_uv={"north": FULL})
    # three protruding chrome knobs under the dials
    for x in (1, 6, 11):
        m.box((x + 1, 1.5, 12.5), (x + 3, 3.5, 13), "chrome", faces=("north", "east", "west", "up", "down"))
    return m.write("control_panel" + ("_on" if lit else ""))


def radar_scope(lit):
    scr = "screen_on" if lit else "screen"
    m = Model({"bak": "st_bakelite", "screen": "radar_screen", "screen_on": "radar_screen_on", "teal": "st_teal",
               "red": "st_red", **CHROME_T}, "st_bakelite")
    m.box((2, 0, 2), (14, 2, 14), "bak")
    m.box((3, 2, 4), (13, 10, 13), "bak", faces=SIDES + ("up",))
    m.box((4, 2, 3), (12, 10, 4), "teal", faces=("east", "west", "up"))
    m.glow((4, 2, 3), (12, 10, 3), scr, uv=FULL, lit=lit)
    m.box((4, 0.5, 1.5), (5.5, 1.5, 2), "red", faces=("north", "east", "west", "up", "down"))
    m.box((10.5, 0.5, 1.5), (12, 1.5, 2), "chrome", faces=("north", "east", "west", "up", "down"))
    return m.write("radar_scope" + ("_on" if lit else ""))


def computer_bank(lit):
    front = "front_on" if lit else "front"
    m = Model({"side": "computer_side", "front": "computer_front", "front_on": "computer_front_on",
               "cream": "st_cream", "teal": "st_teal"}, "computer_side")
    m.box((0, 0, 2), (16, 16, 16), "side", face_tex={"north": front, "up": "cream", "down": "teal"},
          face_uv={"north": FULL})
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
    m.box((12, 6, 13.5), (14, 7, 14.5), "lamp")
    return m.write("crew_bunk")


def hydroponic_planter(lit):
    lamp = "lamp_on" if lit else "lamp"
    m = Model({"top": "hydro_top", "crop": "hydro_crop", "lamp": "grow_lamp", "lamp_on": "grow_lamp_on", **CHROME_T},
              "hydro_top", render_type="minecraft:cutout")
    m.box((0, 0, 0), (16, 4, 16), "chrome", face_tex={"up": "top", "down": "ctop"})
    for z in (4.5, 11.5):
        m.box((1, 4, z), (15, 12, z), "crop", faces=("north", "south"))
    for x in (4.5, 11.5):
        m.box((x, 4, 1), (x, 12, 15), "crop", faces=("east", "west"))
    m.box((0.5, 4, 7.5), (1.5, 13, 8.5), "chrome", faces=SIDES)
    m.box((14.5, 4, 7.5), (15.5, 13, 8.5), "chrome", faces=SIDES)
    m.box((0.5, 13, 7), (15.5, 14, 9), "chrome", faces=SIDES + ("up",), face_tex={"up": "ctop"})
    m.glow((0.5, 13, 7), (15.5, 13, 9), lamp, face="down", lit=lit)
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


def star_chart_model(lit):
    face = "chart_on" if lit else "chart"
    m = Model({"brass": "brass", "chart": "star_chart", "chart_on": "star_chart_on"}, "brass")
    m.box((1, 1, 15), (15, 15, 16), "brass", faces=("east", "west", "up", "down"))
    m.glow((1, 1, 15), (15, 15, 15), face, lit=lit)
    return m.write("star_chart" + ("_on" if lit else ""))


def ceiling_light(lit):
    panel = "panel_on" if lit else "panel"
    m = Model({"panel": "light_panel", "panel_on": "light_panel_on", **CHROME_T}, "stool_chrome")
    m.box((2, 15, 2), (14, 16, 14), "chrome", faces=SIDES + ("down",), face_tex={"down": "ctop"})
    m.box((3, 14, 3), (13, 15, 13), panel, faces=SIDES + ("down",), shade=False if lit else None)
    return m.write("ceiling_light" + ("_on" if lit else ""))


def wall_sconce(lit):
    b = "bulb_on" if lit else "bulb"
    ring = "ring_on" if lit else "ring"
    m = Model({"bulb": "sconce_bulb", "bulb_on": "sconce_bulb_on", "ring": "orbit_ring", "ring_on": "orbit_ring_on",
               **CHROME_T}, "stool_chrome", render_type="minecraft:cutout")
    m.box((6, 5, 15), (10, 11, 16), "chrome", faces=("north", "east", "west", "up", "down"))
    m.box((7.5, 7.5, 14), (8.5, 8.5, 15), "chrome", faces=("east", "west", "up", "down"))
    m.box((6.5, 6.5, 12.5), (9.5, 9.5, 14), b, faces=("north", "east", "west", "up", "down"),
          shade=False if lit else None)
    for ang in (45, -45):
        m.box((5, 4, 13.25), (11, 12, 13.25), ring, faces=("north", "south"), rot=("z", ang, (8, 8, 13.25)))
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
              "reactor_cage")
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



# ============================================================================
# v4: crew-life pack (two-tall vending machine, posters, crew locker, cargo crate, supply cabinet,
# workbench, galley stove, lab sink, tape archive, station / airlock doors)
# ============================================================================

LOCKER = (146, 162, 172)
LOCKER_D = (106, 120, 132)
LOCKER_L = (176, 190, 198)
STAINLESS = (172, 178, 184)
STAINLESS_D = (128, 134, 142)
STAINLESS_L = (204, 208, 212)
WATER = (64, 132, 196)
WATER_D = (44, 98, 160)
WATER_L = (130, 190, 230)
MAT = (52, 92, 88)          # workbench linoleum
MAT_D = (36, 66, 64)
MAT_L = (84, 130, 122)
FRAME = (52, 50, 56)        # thin poster frame
SPACE = (20, 24, 52)
SPACE_L = (34, 40, 82)
HOT = (255, 120, 40)
HOT_L = (255, 196, 90)
HOT_D = (170, 50, 20)
HAZARD = (230, 186, 48)

# --- pixel lettering ----------------------------------------------------------
# 3x5 capitals (I and ! are one pixel wide); condensed 2-wide C/E/S and a few lower-case letters are
# used where a word would not fit the 16 px poster width. text() auto-kerns pairs that only touch in
# one pixel (T, I) when a word is still too wide.
FONT5 = {
    "A": [".X.", "X.X", "XXX", "X.X", "X.X"], "B": ["XX.", "X.X", "XX.", "X.X", "XX."],
    "C": [".XX", "X..", "X..", "X..", ".XX"], "D": ["XX.", "X.X", "X.X", "X.X", "XX."],
    "E": ["XXX", "X..", "XX.", "X..", "XXX"], "F": ["XXX", "X..", "XX.", "X..", "X.."],
    "G": [".XX", "X..", "X.X", "X.X", ".XX"], "H": ["X.X", "X.X", "XXX", "X.X", "X.X"],
    "I": ["X", "X", "X", "X", "X"], "K": ["X.X", "X.X", "XX.", "X.X", "X.X"],
    "L": ["X..", "X..", "X..", "X..", "XXX"], "M": ["X.X", "XXX", "XXX", "X.X", "X.X"],
    "N": ["XX.", "X.X", "X.X", "X.X", "X.X"], "O": [".X.", "X.X", "X.X", "X.X", ".X."],
    "P": ["XX.", "X.X", "XX.", "X..", "X.."], "R": ["XX.", "X.X", "XX.", "X.X", "X.X"],
    "S": [".XX", "X..", ".X.", "..X", "XX."], "T": ["XXX", ".X.", ".X.", ".X.", ".X."],
    "U": ["X.X", "X.X", "X.X", "X.X", "XXX"], "V": ["X.X", "X.X", "X.X", "X.X", ".X."],
    "W": ["X.X", "X.X", "X.X", "XXX", "XXX"], "Y": ["X.X", "X.X", ".X.", ".X.", ".X."],
    "!": ["X", "X", "X", ".", "X"], " ": ["..", "..", "..", "..", ".."], "-": ["..", "..", "XX", "..", ".."],
    "0": ["XXX", "X.X", "X.X", "X.X", "XXX"], "7": ["XXX", "..X", ".X.", ".X.", ".X."],
    # lower case (x-height 3)
    "r": ["..", "..", "XX", "X.", "X."], "i": ["X", ".", "X", "X", "X"], "n": ["...", "...", "XX.", "X.X", "X.X"],
    "k": ["X..", "X..", "X.X", "XX.", "X.X"],
}
CONDENSED = {"C": ["XX", "X.", "X.", "X.", "XX"], "E": ["XX", "X.", "XX", "X.", "XX"],
             "S": ["XX", "X.", "XX", ".X", "XX"]}
# 3x4 small capitals for sub-lines
FONT4 = {
    "E": ["XXX", "XX.", "X..", "XXX"], "H": ["X.X", "XXX", "X.X", "X.X"], "M": ["X.X", "XXX", "XXX", "X.X"],
    "O": ["XXX", "X.X", "X.X", "XXX"], "R": ["XX.", "X.X", "XX.", "X.X"], "S": [".XX", "X..", "..X", "XX."],
    "T": ["XXX", ".X.", ".X.", ".X."], "U": ["X.X", "X.X", "X.X", "XXX"], "W": ["X.X", "X.X", "XXX", "XXX"],
    "I": ["X", "X", "X", "X"], "N": ["XX.", "X.X", "X.X", "X.X"], "B": ["XX.", "XXX", "X.X", "XXX"],
    " ": ["..", "..", "..", ".."],
}


def _glyphs(s, font, condensed):
    out = []
    for ch in s:
        g = CONDENSED[ch] if (condensed and ch in CONDENSED and font is FONT5) else font[ch]
        out.append(g)
    return out


def _touch(a, b):
    """Rows where glyph a's last column and glyph b's first column are both inked."""
    return sum(1 for ra, rb in zip(a, b) if ra[-1] == "X" and rb[0] == "X")


def layout(s, font=FONT5, gap=1, condensed=False, max_w=16):
    gl = _glyphs(s, font, condensed)
    gaps = [gap] * (len(gl) - 1)
    width = lambda: sum(len(g[0]) for g in gl) + sum(gaps)
    if width() > max_w:   # auto-kern the pairs that would only share a single pixel
        for i in range(len(gaps)):
            if width() <= max_w:
                break
            if " " not in s[i:i + 2] and _touch(gl[i], gl[i + 1]) <= 1:
                gaps[i] = 0
    return gl, gaps, width()


def text(img, x, y, s, colors, font=FONT5, gap=1, condensed=False, shadow=None, max_w=16):
    if isinstance(colors[0], int):
        colors = [colors]
    gl, gaps, w = layout(s, font, gap, condensed, max_w)
    if x is None:   # centre on the 16 px face
        x = (img.width - w) // 2
    pts_all = []
    cx = x
    for i, g in enumerate(gl):
        c = colors[i % len(colors)]
        pts = [(cx + k, y + r) for r, row in enumerate(g) for k, v in enumerate(row) if v == "X"]
        pts_all.append((pts, c))
        cx += len(g[0]) + (gaps[i] if i < len(gaps) else 0)
    if shadow:
        inked = {p for pts, _ in pts_all for p in pts}
        for pts, _ in pts_all:
            px(img, [(a, b + 1) for (a, b) in pts if (a, b + 1) not in inked], shadow)
    for pts, c in pts_all:
        px(img, pts, c)
    return w


def disc(img, cx, cy, r, c):
    for y in range(img.height):
        for x in range(img.width):
            if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r:
                px(img, [(x, y)], c)


def bands(img, rows):
    """rows = [(y0, y1, colour)] full-width horizontal bands (pixel-art gradient)."""
    for (y0, y1, c) in rows:
        R(img, 0, y0, img.width - 1, y1, c)


def pat(img, x, y, rows, pal):
    """Stamps a hand-drawn pixel pattern: rows of characters, pal maps char -> colour ('.' = leave,
    '_' = punch transparent)."""
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch == ".":
                continue
            if ch == "_":
                img.putpixel((x + i, y + j), (0, 0, 0, 0))
            else:
                px(img, [(x + i, y + j)], pal[ch])


def poster_frame(img, c=FRAME):
    R(img, 0, 0, 15, 0, c)
    R(img, 0, 31, 15, 31, c)
    R(img, 0, 0, 0, 31, c)
    R(img, 15, 0, 15, 31, c)


# --- posters (16x32 each: rows 0..15 = upper block, 16..31 = lower block) -----

def poster_liftoff():
    img = new(16, 32)
    bands(img, [(0, 12, (24, 30, 66)), (13, 18, NAVY), (19, 22, (56, 80, 140)), (23, 25, (150, 104, 120)),
                (26, 31, (222, 142, 82))])
    for (x, y) in ((2, 14), (13, 15), (12, 19), (3, 18), (14, 21)):
        px(img, [(x, y)], CREAM_L)
    # service gantry on the right, swing arm folded back
    for y in range(17, 29):
        px(img, [(13, y)], RED_D)
        px(img, [(14, y)], (96, 26, 30) if y % 2 else RED_D)
    R(img, 11, 20, 12, 20, CHROME_D)
    # the rocket: red nose, white body with a porthole, red band and fins, roaring flame
    pat(img, 5, 13, [
        "..rr..",
        ".rorr.",
        ".lwwd.",
        ".lTtd.",
        ".lwwd.",
        ".lwwd.",
        ".rrrk.",
        ".lwwd.",
        "rlwwdr",
        "rrwwrr",
        "k.gg.k",
    ], {"r": RED, "o": RED_L, "l": WHITE_L, "w": WHITE, "d": WHITE_D, "k": RED_D, "t": TEAL_D, "T": TEAL_L,
        "g": STEEL})
    pat(img, 5, 24, [
        ".yYYy.",
        "..YY..",
        "..oo..",
        "...o..",
    ], {"y": HOT_L, "Y": (255, 240, 190), "o": HOT})
    # billowing exhaust clouds over the pad
    pat(img, 0, 26, [
        "..cc..........cc",
        ".cWWc.cc..cc.cWW",
        "cWWWWcWWccWWcWWW",
        "WWWWWWWWWWWWWWWW",
        "ssssssssssssssss",
    ], {"c": (186, 180, 176), "W": WHITE_D, "s": STEEL})
    poster_frame(img)
    text(img, None, 2, "LIFT", YELLOW, shadow=RED_D)
    text(img, None, 8, "OFF!", YELLOW, shadow=RED_D)
    return img


def poster_vesper():
    img = new(16, 32)
    bands(img, [(0, 9, SPACE), (10, 19, SPACE_L), (20, 31, (52, 36, 84))])
    for (x, y) in ((2, 11), (13, 10), (12, 17), (3, 18), (6, 9), (10, 20), (14, 14), (1, 15)):
        px(img, [(x, y)], (176, 184, 214))
    # the amber star with a soft halo and four spikes
    disc(img, 8, 14, 5.2, (92, 58, 40))
    disc(img, 8, 14, 4.2, AMBER_D)
    disc(img, 8, 14, 3.4, AMBER)
    disc(img, 7.4, 13.4, 2.0, AMBER_L)
    for d in range(5, 8):
        px(img, [(7, 14 - d - 1), (7, 14 + d), (7 - d - 1, 14), (7 + d + 1, 14)], AMBER if d < 7 else AMBER_D)
    # planets: a ringed teal world and a small red one
    disc(img, 13, 20, 1.6, TEAL)
    px(img, [(12, 19)], TEAL_L)
    px(img, [(10, 20), (11, 20), (14, 20), (15, 20)], CREAM_D)
    disc(img, 2.5, 9.5, 1.2, (196, 96, 64))
    px(img, [(2, 9)], (236, 150, 110))
    # cream title band
    R(img, 0, 0, 15, 7, CREAM)
    R(img, 0, 7, 15, 7, CREAM_D)
    poster_frame(img)
    R(img, 1, 1, 14, 6, CREAM)
    text(img, None, 1, "VISIT", RED)
    text(img, None, 20, "VES", AMBER_L, shadow=(120, 60, 30))
    text(img, None, 26, "PER", AMBER_L)
    return img


def poster_space_pop():
    img = new(16, 32)
    bands(img, [(0, 31, RED)])
    # sunburst rays behind the bottle
    for y in range(7, 20):
        for x in range(16):
            a = math.degrees(math.atan2(y + 0.5 - 13, x + 0.5 - 8)) % 360
            if int(a // 15) % 2 == 0:
                px(img, [(x, y)], RED_L)
    # bottle: red cap, glass neck, teal soda, cream label with a little red rocket
    R(img, 7, 6, 8, 6, RED_D)
    R(img, 7, 7, 8, 9, (120, 200, 196))
    px(img, [(7, 7), (7, 8)], (190, 240, 236))
    R(img, 6, 10, 9, 10, (120, 200, 196))
    R(img, 5, 11, 10, 18, TEAL)
    R(img, 5, 11, 5, 18, TEAL_L)
    R(img, 10, 11, 10, 18, TEAL_D)
    R(img, 5, 13, 10, 16, CREAM_L)
    R(img, 10, 13, 10, 16, CREAM_D)
    px(img, [(7, 13), (8, 13), (7, 14), (8, 14), (7, 15), (8, 15)], RED)
    px(img, [(6, 15), (9, 15)], RED_D)
    px(img, [(7, 16), (8, 16)], AMBER)
    R(img, 6, 19, 9, 19, TEAL_D)
    px(img, [(6, 11), (9, 18), (6, 17)], (190, 240, 236))
    poster_frame(img)
    R(img, 0, 1, 15, 5, RED_D)
    text(img, None, 1, "Drink", CREAM_L)
    R(img, 0, 20, 15, 30, CREAM)
    R(img, 0, 20, 15, 20, CREAM_D)
    text(img, None, 21, "SPACE", RED, condensed=True)
    text(img, None, 26, "POP", NAVY)
    return img


def poster_suit_check():
    img = new(16, 32)
    bands(img, [(0, 31, CREAM)])
    # astronaut helmet: white dome, dark visor with a glint, red stripe, chrome collar
    disc(img, 8, 13, 5.3, WHITE_D)
    disc(img, 7.6, 12.6, 4.8, WHITE)
    R(img, 4, 10, 11, 15, VISOR)
    px(img, [(4, 10), (11, 10), (4, 15), (11, 15)], WHITE)
    R(img, 5, 11, 6, 11, VISOR_L)
    px(img, [(5, 12)], VISOR_L)
    px(img, [(9, 14), (10, 14)], (44, 72, 110))
    R(img, 7, 7, 8, 9, RED)
    R(img, 3, 18, 12, 18, CHROME)
    px(img, [(3, 18), (12, 18)], CHROME_D)
    R(img, 1, 19, 14, 19, WHITE_D)
    # hazard-stripe frame
    for i in range(16):
        for (x, y) in ((i, 0), (i, 31)):
            px(img, [(x, y)], HAZARD if (x + y) % 4 < 2 else BLACK)
    for j in range(32):
        for (x, y) in ((0, j), (15, j)):
            px(img, [(x, y)], HAZARD if (x + y) % 4 < 2 else BLACK)
    text(img, None, 2, "CHECK", RED, condensed=True)
    text(img, None, 20, "YOUR", NAVY)
    text(img, None, 26, "SUIT", NAVY)
    return img


def poster_homestead():
    img = new(16, 32)
    bands(img, [(0, 14, (120, 186, 200)), (15, 18, (150, 204, 210)), (19, 31, (176, 214, 206))])
    # the planet rising behind the title: teal oceans, tan continents, polar ice, a cloud streak
    pat(img, 4, 12, [
        "..oooo..",
        ".ooLLoo.",
        "oLLLooLo",
        "oLDooLLo",
        "ooooLLDo",
        "occcccoo",
        ".ooLooo.",
        "..oiio..",
    ], {"o": OCEAN, "L": LAND, "D": LAND_D, "c": (214, 232, 236), "i": ICE})
    px(img, [(4, 15), (5, 13)], (110, 184, 196))
    poster_frame(img)
    R(img, 0, 1, 15, 12, CREAM)
    R(img, 0, 12, 15, 12, CREAM_D)
    text(img, None, 1, "HOME", RED)
    text(img, None, 7, "STEAD", NAVY, condensed=True)
    R(img, 0, 20, 15, 30, LEAF_D)
    R(img, 0, 20, 15, 20, LEAF)
    text(img, None, 21, "SWEET", CREAM_L, condensed=True)
    text(img, None, 26, "HOME", YELLOW)
    return img


def poster_freedom():
    img = new(16, 32)
    bands(img, [(0, 31, SPACE)])
    for (x, y) in ((2, 14), (13, 13), (1, 21), (14, 22), (12, 14), (3, 23)):
        px(img, [(x, y)], (170, 178, 210))
    # von Braun wheel: white rim with lit windows, chrome spokes, red hub; a shuttle docking
    pat(img, 3, 13, [
        "..wwwwww..",
        ".wa.cc.aw.",
        "wa..cc..aw",
        "w...cc...w",
        "wcccrrcccw",
        "wcccrRcccw",
        "w...cc...w",
        "wa..cc..aw",
        ".wa.cc.aw.",
        "..wwwwww..",
    ], {"w": WHITE, "a": AMBER, "c": CHROME_D, "r": RED, "R": RED_D})
    pat(img, 12, 19, ["r.", "wr", "r."], {"r": RED, "w": WHITE})
    poster_frame(img)
    R(img, 0, 1, 15, 12, RED)
    R(img, 0, 12, 15, 12, RED_D)
    text(img, None, 1, "FREE", CREAM_L)
    text(img, None, 7, "DOM", CREAM_L)
    R(img, 0, 23, 15, 30, CREAM)
    text(img, None, 24, "OUR", NAVY, font=FONT4)
    text(img, None, 28, "HOME", RED, font=FONT4)
    return img


POSTERS = {"poster_liftoff": poster_liftoff, "poster_vesper": poster_vesper, "poster_space_pop": poster_space_pop,
           "poster_suit_check": poster_suit_check, "poster_homestead": poster_homestead,
           "poster_freedom": poster_freedom}


POSTER_ITEM_DISPLAY = {
    "gui": {"rotation": [0, 0, 0], "translation": [0, 0, 0], "scale": [1, 1, 1]},
    "ground": {"rotation": [0, 0, 0], "translation": [0, 2, 0], "scale": [0.5, 0.5, 0.5]},
    "head": {"rotation": [0, 180, 0], "translation": [0, 13, 7], "scale": [1, 1, 1]},
    "thirdperson_righthand": {"rotation": [0, 0, 0], "translation": [0, 3, 1], "scale": [0.55, 0.55, 0.55]},
    "firstperson_righthand": {"rotation": [0, -90, 25], "translation": [1.13, 3.2, 1.13], "scale": [0.68, 0.68, 0.68]},
    "fixed": {"rotation": [0, 180, 0], "scale": [1, 1, 1]},
}


def poster_item_model(name):
    """Item model: the poster as a flat 8x16 card (both halves), so the GUI shows the full 16x32 art."""
    m = Model({"lower": f"{name}_lower", "upper": f"{name}_upper"}, f"{name}_upper", display=POSTER_ITEM_DISPLAY)
    for key, y0 in (("lower", 0), ("upper", 8)):
        m.box((4, y0, 8), (12, y0 + 8, 8), key, faces=("north", "south"),
              face_uv={"north": FULL, "south": FULL})
    write_item_model(name, m, gui_light="front")


# --- vending machine (two blocks) ----------------------------------------------

def vend_front(half):
    """Block-space front for x 1..15 of the red cabinet (lower / upper half)."""
    img = flat(RED)
    R(img, 1, 0, 1, 15, RED_L)
    R(img, 14, 0, 14, 15, RED_D)
    if half == "lower":
        # dispenser opening and the kick plate
        R(img, 3, 10, 9, 13, BAKELITE_D)
        R(img, 3, 10, 9, 10, BLACK)
        R(img, 2, 15, 13, 15, RED_D)
        # "price" plate under the coin box
        R(img, 11, 3, 13, 3, CREAM)
        px(img, [(11, 3), (13, 3)], CREAM_D)
        # chrome kick strip
        R(img, 1, 14, 14, 14, CHROME_D)
    else:
        R(img, 1, 13, 14, 13, RED_D)
    return img


def vend_window(lit):
    """Window art, 8 px wide (u 0..8) x 12 rows (v 0..12): two shelves of three bottles."""
    img = new()
    glass = (255, 236, 180) if lit else (78, 64, 66)
    R(img, 0, 0, 7, 11, glass)
    soda = (RED, TEAL, AMBER)
    for shelf, top in enumerate((0, 6)):
        for i, x in enumerate((0, 3, 6)):
            c = soda[(i + shelf) % 3]
            if not lit:
                c = tuple(int(v * 0.55) for v in c)
            px(img, [(x, top + 1), (x + 1, top + 1)], CHROME_D if not lit else CHROME)   # caps
            R(img, x, top + 2, x + 1, top + 4, c)
            px(img, [(x, top + 2)], tuple(min(255, v + 50) for v in c))
        R(img, 0, top + 5, 7, top + 5, CHROME if lit else CHROME_D)   # shelf
    if lit:
        px(img, [(2, 2), (5, 8)], (255, 250, 230))
    else:
        px(img, [(1, 0), (2, 0), (4, 6)], (120, 112, 116))
    return img


def vend_header(lit):
    """16 x 12 marquee (rows 0..11): SPACE over POP with two little stars."""
    img = new()
    bg = (255, 246, 222) if lit else WHITE
    R(img, 0, 0, 15, 11, bg)
    R(img, 0, 11, 15, 11, CREAM_D if not lit else (240, 214, 170))
    text(img, None, 0, "SPACE", RED if not lit else (236, 40, 44), condensed=True)
    text(img, None, 6, "POP", NAVY if not lit else (36, 70, 150))
    star_c = AMBER if lit else AMBER_D
    for (x, y) in ((1, 8), (14, 8)):
        px(img, [(x, y - 1), (x, y + 1), (x - 1, y), (x + 1, y)], star_c)
    return img


def vend_coin(lit):
    """Coin box face (3 x 5 px): coin slot, three selection buttons, return lever."""
    img = flat(CHROME)
    R(img, 1, 1, 1, 2, BLACK)                 # coin slot (u 1, v 1..2)
    px(img, [(0, 1)], CHROME_L)
    px(img, [(2, 1)], CHROME_D)
    for i, c in enumerate((RED, TEAL, AMBER)):
        px(img, [(i, 3)], c if lit else tuple(int(v * 0.7) for v in c))
    R(img, 0, 4, 2, 4, CHROME_D)
    return img


def vend_side(half):
    img = flat(RED)
    if half == "lower":
        R(img, 0, 15, 15, 15, RED_D)
        R(img, 0, 14, 15, 14, CHROME_D)
        R(img, 0, 5, 15, 6, WHITE)          # white sweep stripe
        R(img, 0, 6, 15, 6, WHITE_D)
    else:
        R(img, 0, 0, 15, 0, RED_L)
        R(img, 0, 2, 15, 3, WHITE)
        R(img, 0, 3, 15, 3, WHITE_D)
        # big rocket emblem on the side panel
        R(img, 7, 6, 8, 11, WHITE)
        px(img, [(7, 5), (8, 5)], RED_L)
        px(img, [(7, 4)], WHITE)
        px(img, [(6, 10), (6, 11), (9, 10), (9, 11)], WHITE_D)
        px(img, [(7, 8), (8, 8)], TEAL)
        px(img, [(7, 12), (8, 12)], AMBER)
    return img


def vend_parts(m, half, lit, dy=0):
    """Adds one half of the vending machine to model m (dy shifts it, used for the combined item)."""
    def b(frm, to, *a, **k):
        return m.box((frm[0], frm[1] + dy, frm[2]), (to[0], to[1] + dy, to[2]), *a, **k)

    win = "win_on" if lit else "win"
    if half == "lower":
        b((1.5, 0, 2.5), (14.5, 1, 14.5), "steel", faces=SIDES)
        b((1, 1, 2), (15, 16, 15), "side", faces=("north", "south", "east", "west", "down"),
          face_tex={"north": "front", "south": "red", "down": "red"})
        # glass window (proud of the cabinet) with a chrome bezel
        m.glow((2, 7 + dy, 1.5), (10, 16 + dy, 1.5), win, uv=[0, 3, 8, 12], lit=lit)
        b((1.5, 6.5, 1.25), (10.5, 7, 2), "chrome", faces=("north", "east", "west", "up", "down"))
        b((1.5, 7, 1.25), (2, 16, 2), "chrome", faces=("north", "west", "east"))
        b((10, 7, 1.25), (10.5, 16, 2), "chrome", faces=("north", "west", "east"))
        # coin box
        b((11, 8, 1.5), (14, 13, 2), "chrome", faces=("north", "east", "west", "up", "down"),
          face_tex={"north": "coin_on" if lit else "coin"}, face_uv={"north": [0, 0, 3, 5]})
        # dispenser: chrome hood over the opening and a lip under it
        b((2.5, 6, 1.25), (9.5, 6.5, 2), "chrome", faces=("north", "east", "west", "up", "down"))
        b((2.5, 1.5, 1), (9.5, 2.5, 2), "chrome", faces=("north", "east", "west", "up", "down"))
    else:
        b((1, 0, 2), (15, 3, 15), "side", faces=("north", "south", "east", "west"),
          face_tex={"north": "front", "south": "red"})
        m.glow((2, 0 + dy, 1.5), (10, 3 + dy, 1.5), win, uv=[0, 0, 8, 3], lit=lit)
        b((1.5, 0, 1.25), (2, 3, 2), "chrome", faces=("north", "west", "east"))
        b((10, 0, 1.25), (10.5, 3, 2), "chrome", faces=("north", "west", "east"))
        b((1.5, 3, 1.25), (10.5, 3.5, 2), "chrome", faces=("north", "east", "west", "down"))
        # marquee header: full width, one pixel proud of the cabinet (front face is the glow plane)
        b((0, 3, 1), (16, 15, 15.5), "white", faces=("south", "east", "west", "down"),
          face_tex={"east": "side", "west": "side"})
        m.glow((0, 3 + dy, 1), (16, 15 + dy, 1), "head_on" if lit else "head", uv=[0, 0, 16, 12], lit=lit)
        b((0, 3, 1), (16, 15, 15.5), "white", faces=("up",))
        b((0.5, 15, 1.5), (15.5, 16, 15), "chrome", face_tex={"up": "red"},
          faces=("north", "south", "east", "west", "up"))


VEND_TEX = {"front": None, "side": None, "red": "st_red", "steel": "st_steel", "white": "st_enamel",
            "win": "vending_window", "win_on": "vending_window_on", "head": "vending_header",
            "head_on": "vending_header_on", "coin": "vending_coin", "coin_on": "vending_coin_on", **CHROME_T}


def vending_models():
    for half in ("lower", "upper"):
        for lit in (False, True):
            t = dict(VEND_TEX, front=f"vending_front_{half}", side=f"vending_side_{half}")
            m = Model(t, f"vending_side_{half}")
            vend_parts(m, half, lit)
            m.write(f"vending_machine_{half}" + ("_on" if lit else ""))
    # combined two-tall item model (lit look)
    t = dict(VEND_TEX, front="vending_front_lower", side="vending_side_lower", front_u="vending_front_upper",
             side_u="vending_side_upper")
    m = Model(t, "vending_side_lower", display=TALL_DISPLAY)
    vend_parts(m, "lower", True)
    n = len(m.elements)
    vend_parts(m, "upper", True, dy=16)
    for e in m.elements[n:]:
        for f in e["faces"].values():
            if f["texture"] == "#front":
                f["texture"] = "#front_u"
            elif f["texture"] == "#side":
                f["texture"] = "#side_u"
    write_item_model("vending_machine", m)


TALL_DISPLAY = {
    "gui": {"rotation": [30, 225, 0], "translation": [0, -3.25, 0], "scale": [0.42, 0.42, 0.42]},
    "ground": {"rotation": [0, 0, 0], "translation": [0, 1, 0], "scale": [0.2, 0.2, 0.2]},
    "fixed": {"rotation": [0, 0, 0], "translation": [0, -4, 0], "scale": [0.4, 0.4, 0.4]},
    "head": {"rotation": [0, 0, 0], "translation": [0, -4, 0], "scale": [0.5, 0.5, 0.5]},
    "thirdperson_righthand": {"rotation": [75, 45, 0], "translation": [0, 1, 0], "scale": [0.25, 0.25, 0.25]},
    "thirdperson_lefthand": {"rotation": [75, 45, 0], "translation": [0, 1, 0], "scale": [0.25, 0.25, 0.25]},
    "firstperson_righthand": {"rotation": [0, 45, 0], "translation": [0, -2, 0], "scale": [0.25, 0.25, 0.25]},
    "firstperson_lefthand": {"rotation": [0, 225, 0], "translation": [0, -2, 0], "scale": [0.25, 0.25, 0.25]},
}


def write_item_model(name, m, gui_light=None):
    """Writes a block-style element model as models/item/<name>.json and points the item definition at it."""
    out = {"textures": m.textures}
    if gui_light:
        out["gui_light"] = gui_light
    if m.render_type:
        out["render_type"] = m.render_type
    out["display"] = m.display
    out["elements"] = m.elements
    write_json(os.path.join(ITEMS_DIR, name + ".json"), out)
    item_def(name, f"{MOD}:item/{name}")


# --- crew locker (two blocks) -------------------------------------------------------

def locker_front(half):
    """Block-space front for x 1..15: two narrow doors (seam at x 8), vents, name plates, stripe."""
    img = flat(LOCKER)
    for x in (1, 8):
        R(img, x, 0, x, 15, LOCKER_L)
    for x in (7, 14):
        R(img, x, 0, x, 15, LOCKER_D)
    if half == "upper":
        R(img, 1, 0, 14, 0, LOCKER_L)
        R(img, 1, 1, 14, 1, LOCKER_D)
        for door in (2, 9):
            for y in (3, 5, 7):     # louvred vents
                R(img, door, y, door + 3, y, STEEL_D)
                R(img, door, y + 1, door + 3, y + 1, LOCKER_L)
            R(img, door, 10, door + 3, 11, CREAM)     # name plate
            px(img, [(door, 10), (door + 3, 11)], CREAM_D)
            px(img, [(door + 1, 10), (door + 2, 10)], (90, 84, 76))
        R(img, 1, 13, 14, 13, RED)
        R(img, 1, 14, 14, 14, TEAL)
    else:
        for door in (2, 9):
            for y in (10, 12):
                R(img, door, y, door + 3, y, STEEL_D)
                R(img, door, y + 1, door + 3, y + 1, LOCKER_L)
        px(img, [(6, 6), (9, 6)], BRASS)     # key locks
        R(img, 1, 15, 14, 15, STEEL_D)
    return img


def locker_side(half):
    img = flat(LOCKER)
    R(img, 15, 0, 15, 15, LOCKER_D)     # back edge (z 16 maps to u 16 on east... both sides share)
    if half == "upper":
        R(img, 0, 0, 15, 0, LOCKER_L)
        R(img, 0, 13, 15, 13, RED)
        R(img, 0, 14, 15, 14, TEAL)
    else:
        R(img, 0, 15, 15, 15, STEEL_D)
    return img


def locker_parts(m, half, dy=0):
    def b(frm, to, *a, **k):
        return m.box((frm[0], frm[1] + dy, frm[2]), (to[0], to[1] + dy, to[2]), *a, **k)
    if half == "lower":
        b((1, 0, 3), (15, 16, 16), "side", faces=SIDES + ("down",), face_tex={"north": "front", "down": "steel"})
        # door handles (chrome pulls next to the seam)
        for x in (5.5, 9.5):
            b((x, 9, 2.5), (x + 1, 14, 3), "chrome", faces=("north", "east", "west", "up", "down"))
    else:
        b((1, 0, 3), (15, 15, 16), "side", faces=SIDES, face_tex={"north": "front"})
        b((0.5, 15, 2.5), (15.5, 16, 16), "steel", face_tex={"up": "top"}, faces=SIDES + ("up", "down"))


def locker_models():
    for half in ("lower", "upper"):
        m = Model({"front": f"crew_locker_front_{half}", "side": f"crew_locker_side_{half}", "steel": "st_steel",
                   "top": "crew_locker_top", **CHROME_T}, f"crew_locker_side_{half}")
        locker_parts(m, half)
        m.write(f"crew_locker_{half}")
    m = Model({"front": "crew_locker_front_lower", "side": "crew_locker_side_lower", "front_u": "crew_locker_front_upper",
               "side_u": "crew_locker_side_upper", "steel": "st_steel", "top": "crew_locker_top", **CHROME_T},
              "crew_locker_side_lower", display=TALL_DISPLAY)
    locker_parts(m, "lower")
    n = len(m.elements)
    locker_parts(m, "upper", dy=16)
    for e in m.elements[n:]:
        for f in e["faces"].values():
            if f["texture"] in ("#front", "#side"):
                f["texture"] += "_u"
    write_item_model("crew_locker", m)


def locker_top():
    img = flat(STEEL)
    R(img, 0, 0, 15, 15, (104, 110, 120))
    for x in range(1, 15, 2):
        px(img, [(x, 8)], STEEL_D)
    return img


# --- cargo crate -----------------------------------------------------------------------

def cargo_side():
    img = flat(WHITE)
    R(img, 0, 0, 15, 0, CHROME)
    R(img, 0, 15, 15, 15, CHROME_D)
    R(img, 0, 0, 0, 15, CHROME)
    R(img, 15, 0, 15, 15, CHROME_D)
    # red corner bands (L brackets)
    for (x0, y0, dx, dy) in ((0, 0, 1, 1), (15, 0, -1, 1), (0, 15, 1, -1), (15, 15, -1, -1)):
        for k in range(4):
            px(img, [(x0 + dx * k, y0), (x0, y0 + dy * k), (x0 + dx * k, y0 + dy), (x0 + dx, y0 + dy * k)], RED)
        px(img, [(x0 + dx, y0 + dy)], RED_D)
    # ribs
    R(img, 1, 5, 14, 5, WHITE_D)
    R(img, 1, 11, 14, 11, WHITE_D)
    # stencil: CARGO (two-tone, it is one pixel too wide for gaps) and "this way up" arrows
    text(img, None, 6, "CARGO", [NAVY, RED], gap=0)
    for x in (4, 10):
        px(img, [(x, 12), (x - 1, 13), (x + 1, 13), (x, 13), (x, 14)], NAVY)
    px(img, [(7, 2), (8, 2), (7, 3), (8, 3)], TEAL)    # serial tab
    px(img, [(6, 3), (9, 3)], TEAL_D)
    return img


def cargo_top():
    img = flat(WHITE)
    R(img, 0, 0, 15, 15, WHITE_D)
    R(img, 1, 1, 14, 14, WHITE)
    for (x, y) in ((0, 0), (12, 0), (0, 12), (12, 12)):
        R(img, x, y, x + 3, y + 3, RED)
        R(img, x + 1, y + 1, x + 2, y + 2, RED_D)
    # lifting ring recess and arrows
    R(img, 6, 6, 9, 9, CHROME_D)
    R(img, 7, 7, 8, 8, CHROME)
    for (x, y) in ((7, 3), (8, 3), (7, 12), (8, 12), (3, 7), (3, 8), (12, 7), (12, 8)):
        px(img, [(x, y)], NAVY)
    return img


# --- supply cabinet -------------------------------------------------------------------------

def supply_front():
    img = flat(TEAL)
    R(img, 0, 0, 15, 0, TEAL_L)
    R(img, 0, 15, 15, 15, TEAL_D)
    # two cream doors with an inset panel line
    for x0 in (1, 8):
        R(img, x0, 1, x0 + 6, 13, CREAM)
        R(img, x0, 13, x0 + 6, 13, CREAM_D)
        R(img, x0 + 6, 1, x0 + 6, 13, CREAM_D)
        R(img, x0, 1, x0 + 6, 1, CREAM_L)
        R(img, x0 + 1, 3, x0 + 5, 3, CREAM_D)
        R(img, x0 + 1, 11, x0 + 5, 11, CREAM_D)
    # small brass label plate across the door gap (engraved "lettering")
    R(img, 5, 3, 10, 5, BRASS)
    R(img, 5, 5, 10, 5, BRASS_D)
    R(img, 5, 3, 10, 3, BRASS_L)
    R(img, 6, 4, 9, 4, (110, 80, 36))
    px(img, [(8, 4)], BRASS)
    R(img, 1, 14, 14, 14, TEAL_D)
    px(img, [(1, 2), (1, 12), (14, 2), (14, 12)], CHROME)   # hinges
    return img


def supply_side():
    img = flat(CREAM)
    R(img, 0, 0, 15, 0, CREAM_L)
    R(img, 0, 14, 15, 15, TEAL)
    R(img, 0, 15, 15, 15, TEAL_D)
    R(img, 0, 3, 15, 3, CREAM_D)
    return img


def supply_top():
    img = flat(CREAM)
    R(img, 0, 0, 15, 0, TEAL)
    R(img, 0, 15, 15, 15, TEAL_D)
    R(img, 0, 0, 0, 15, TEAL)
    R(img, 15, 0, 15, 15, TEAL_D)
    return img


# --- retro workbench ---------------------------------------------------------------------------

def bench_front():
    """Cabinet front (x 1..15, y 0..10): three drawers on the left, a door on the right, kick strip."""
    img = flat(CREAM)
    R(img, 1, 6, 14, 15, CREAM)
    for (y0, y1) in ((6, 8), (9, 11), (12, 14)):
        R(img, 2, y0, 7, y1, CREAM_L)
        R(img, 2, y1, 7, y1, CREAM_D)
        R(img, 4, y0 + 1, 5, y0 + 1, CHROME_D)
    R(img, 9, 6, 13, 14, CREAM_L)
    R(img, 13, 6, 13, 14, CREAM_D)
    R(img, 9, 14, 13, 14, CREAM_D)
    R(img, 10, 7, 12, 7, RED)        # red badge strip on the door
    px(img, [(10, 10), (10, 11)], CHROME_D)
    R(img, 1, 15, 14, 15, TEAL_D)
    R(img, 1, 6, 1, 15, CREAM_D)
    R(img, 14, 6, 14, 15, CREAM_D)
    return img


def bench_side():
    img = flat(CREAM)
    R(img, 0, 15, 15, 15, TEAL_D)
    R(img, 0, 6, 15, 6, CREAM_L)
    for y in (9, 11):
        R(img, 4, y, 11, y, CREAM_D)
    R(img, 3, 7, 12, 7, CHROME)
    px(img, [(3, 7), (12, 7)], CHROME_D)
    return img


def bench_top():
    """Work surface: dark teal linoleum inside a chrome edge, with a 3x3 grid hint (4 px cells)."""
    img = flat(MAT)
    R(img, 0, 0, 15, 15, CHROME)
    R(img, 0, 15, 15, 15, CHROME_D)
    R(img, 15, 0, 15, 15, CHROME_D)
    R(img, 1, 1, 14, 14, MAT)
    for k in (5, 10):
        R(img, k, 1, k, 14, MAT_L)
        R(img, 1, k, 14, k, MAT_L)
    for k in (1, 6, 11):    # darker inner corner of each cell (worn mat)
        for j in (1, 6, 11):
            px(img, [(k + 3, j + 3)], MAT_D)
    px(img, [(2, 2), (8, 12), (12, 7)], MAT_D)
    return img


def bench_edge():
    img = flat(CHROME)
    R(img, 0, 0, 15, 0, CHROME_L)
    R(img, 0, 1, 15, 1, CHROME_D)
    R(img, 0, 2, 15, 2, CHROME)
    R(img, 0, 3, 15, 3, RED)
    R(img, 0, 4, 15, 15, CHROME)
    return img


def pegboard():
    """Back tool rack (y 12..16): teal pegboard with tool silhouettes, rows 0..3."""
    img = flat(TEAL_D)
    R(img, 0, 0, 15, 0, CHROME)
    for x in range(1, 16, 3):
        px(img, [(x, 2)], (28, 92, 90))
    px(img, [(2, 1), (2, 2), (2, 3)], CHROME_L)         # spanner
    px(img, [(1, 1), (3, 1)], CHROME)
    px(img, [(5, 1), (5, 2), (6, 1)], RED)              # pliers
    px(img, [(5, 3), (7, 3)], RED_D)
    px(img, [(9, 1), (10, 1), (11, 1), (10, 2), (10, 3)], STEEL)   # hammer
    px(img, [(13, 1), (13, 2)], AMBER)                   # screwdriver
    px(img, [(13, 3)], CHROME)
    return img


# --- galley stove ------------------------------------------------------------------------

def stove_front(lit):
    """Block-space front (x 1..15, y 0..13 -> rows 3..15): control strip, round oven window, kick plate."""
    img = flat(CREAM)
    R(img, 1, 3, 14, 5, CHROME)      # control strip (y 10..13)
    R(img, 1, 3, 14, 3, CHROME_L)
    R(img, 1, 5, 14, 5, CHROME_D)
    px(img, [(13, 4)], AMBER if lit else LAMP_OFF)
    # oven door: cream panel with a round window in a chrome ring (glass within u 5..11, v 8..13)
    R(img, 2, 7, 13, 14, CREAM_L)
    R(img, 2, 14, 13, 14, CREAM_D)
    R(img, 13, 7, 13, 14, CREAM_D)
    g, G, h = ((HOT, HOT_L, (255, 236, 180)) if lit else ((58, 46, 44), (74, 60, 56), (112, 100, 96)))
    pat(img, 4, 7, [
        "..cccc..",
        ".chGggc.",
        "cGGggggc",
        "cGgggggc",
        "cggggggc",
        ".cggggc.",
        "..cddc..",
    ], {"c": CHROME, "d": CHROME_D, "g": g, "G": G, "h": h})
    R(img, 1, 15, 14, 15, CHROME_D)
    return img


def stove_side():
    img = flat(CREAM)
    R(img, 0, 3, 15, 5, CHROME)
    R(img, 0, 3, 15, 3, CHROME_L)
    R(img, 0, 5, 15, 5, CHROME_D)
    R(img, 0, 15, 15, 15, CHROME_D)
    R(img, 0, 2, 15, 2, CREAM_D)
    return img


def stove_hob(lit):
    """Cook-top: brushed steel with four hot plates (glowing coils when lit)."""
    img = flat(STAINLESS)
    R(img, 0, 0, 15, 0, STAINLESS_L)
    R(img, 0, 15, 15, 15, STAINLESS_D)
    coil, mid = ((HOT, HOT_L) if lit else ((84, 80, 82), BLACK))
    plate = [".kkkk.",
             "kcccck",
             "kcmmck",
             "kcmmck",
             "kcccck",
             ".kkkk."]
    for (x, y) in ((1, 1), (9, 1), (1, 8), (9, 8)):
        pat(img, x, y, plate, {"k": BLACK, "c": coil, "m": mid})
    R(img, 1, 14, 14, 14, STAINLESS_D)
    return img


def stove_back():
    img = flat(CHROME)
    R(img, 0, 0, 15, 0, CHROME_L)
    R(img, 0, 3, 15, 3, CHROME_D)
    return img


# --- lab sink ------------------------------------------------------------------------------

def sink_front():
    """Cabinet front (x 1..15, y 0..11 -> rows 5..15): two teal doors with chrome pulls."""
    img = flat(WHITE)
    for x0 in (2, 8):
        R(img, x0, 6, x0 + 5, 14, TEAL)
        R(img, x0, 6, x0 + 5, 6, TEAL_L)
        R(img, x0 + 5, 6, x0 + 5, 14, TEAL_D)
        R(img, x0, 14, x0 + 5, 14, TEAL_D)
    px(img, [(6, 9), (6, 10), (9, 9), (9, 10)], CHROME_L)
    R(img, 1, 15, 14, 15, STEEL)
    return img


def sink_side():
    img = flat(WHITE)
    R(img, 0, 15, 15, 15, STEEL)
    R(img, 0, 5, 15, 5, WHITE_D)
    return img


def stainless():
    img = flat(STAINLESS)
    for y in range(16):
        if y % 3 == 0:
            R(img, 0, y, 15, y, STAINLESS_L)
        elif y % 3 == 2:
            R(img, 0, y, 15, y, (160, 166, 172))
    return img


def water():
    img = flat(WATER)
    for (x, y) in ((4, 4), (5, 4), (10, 6), (11, 6), (6, 9), (7, 9), (8, 9), (11, 10)):
        px(img, [(x, y)], WATER_L)
    for (x, y) in ((3, 7), (9, 8), (5, 10), (12, 4)):
        px(img, [(x, y)], WATER_D)
    return img


# --- tape archive ------------------------------------------------------------------------

def archive_back():
    """Recessed back wall at z=2 (x 1..15): tape reels on the upper shelf, binders on the lower one."""
    img = flat((34, 46, 50))
    # upper bay rows 1..7 (y 8..15): two big reels + a tape canister stack
    reel = ["..ccc..",
            ".cbbbc.",
            "cbbbbbc",
            "cbbhbbc",
            "cbbbbbc",
            ".cbbbc.",
            "..ccc.."]
    for x, tape in ((1, (92, 66, 44)), (8, (60, 46, 36))):
        pat(img, x, 1, reel, {"c": CHROME, "b": tape, "h": CHROME_L})
        px(img, [(x + 1, 2)], CHROME_L)
        px(img, [(x + 2, 3), (x + 4, 5)], (112, 84, 58) if x == 1 else (80, 62, 48))
    # lower bay rows 9..14 (y 1..7): binders with labels
    cols = (RED, NAVY, TEAL, CREAM_D, RED_D, AMBER_D, NAVY_L, TEAL_D, RED, CREAM_D, NAVY, TEAL, AMBER_D, RED_D)
    for i, x in enumerate(range(1, 15)):
        top = 9 + (i * 7 % 3 == 0)
        c = cols[i]
        R(img, x, top, x, 14, c)
        px(img, [(x, 12)], CREAM_L if c not in (CREAM_D,) else BLACK)
    R(img, 11, 10, 13, 14, (34, 46, 50))     # gap with a leaning binder
    px(img, [(11, 12), (12, 11), (13, 10), (12, 12), (13, 11), (11, 13), (12, 13), (13, 12), (13, 13)], TEAL)
    return img


def archive_frame():
    img = flat(CREAM)
    R(img, 0, 0, 15, 0, CREAM_L)
    R(img, 0, 15, 15, 15, CREAM_D)
    return img


def archive_side():
    img = flat(CREAM)
    R(img, 0, 0, 15, 1, TEAL)
    R(img, 0, 14, 15, 15, TEAL)
    R(img, 0, 15, 15, 15, TEAL_D)
    R(img, 0, 8, 15, 8, CREAM_D)
    return img


def archive_shelf():
    img = flat(TEAL)
    R(img, 0, 0, 15, 0, TEAL_L)
    R(img, 0, 15, 15, 15, TEAL_D)
    return img


# --- doors ------------------------------------------------------------------------------

def station_door(part):
    """White enamel sliding-style door: porthole (cutout glass), turquoise stripe, recessed pull slot."""
    img = flat(WHITE)
    R(img, 0, 0, 1, 15, CHROME)          # frame edges (the 3 px edge faces sample columns 0..2)
    R(img, 1, 0, 1, 15, CHROME_D)
    R(img, 14, 0, 15, 15, CHROME_D)
    R(img, 14, 0, 14, 15, CHROME)
    R(img, 2, 0, 2, 15, WHITE_L)
    R(img, 13, 0, 13, 15, WHITE_D)
    if part == "top":
        R(img, 2, 0, 13, 0, WHITE_DD)
        pat(img, 3, 3, [
            "..cccccc..",
            ".cd____dc.",
            "cd______dc",
            "c__g_____c",
            "c_g______c",
            "c________c",
            "c________c",
            "cd______dc",
            ".cd____dc.",
            "..cccccc..",
        ], {"c": CHROME, "d": CHROME_D, "g": GLASS_L})
        R(img, 2, 15, 13, 15, WHITE_D)
    else:
        R(img, 2, 3, 13, 5, TEAL)
        R(img, 2, 3, 13, 3, TEAL_L)
        R(img, 2, 5, 13, 5, TEAL_D)
        R(img, 11, 7, 12, 11, WHITE_DD)       # recessed pull slot
        R(img, 11, 7, 11, 11, STEEL)
        R(img, 2, 13, 13, 15, CHROME)
        R(img, 2, 13, 13, 13, CHROME_L)
        R(img, 2, 15, 13, 15, CHROME_D)
    return img


def airlock_door(part):
    """Heavy red airlock door with chrome frame, bolted porthole, wheel handle and a hazard stripe."""
    img = flat(RED)
    R(img, 0, 0, 2, 15, CHROME)
    R(img, 2, 0, 2, 15, CHROME_D)
    R(img, 13, 0, 15, 15, CHROME)
    R(img, 13, 0, 13, 15, CHROME_D)
    R(img, 3, 0, 3, 15, RED_L)
    R(img, 12, 0, 12, 15, RED_D)
    for y in (3, 12):
        px(img, [(1, y), (14, y)], STEEL_D)            # hinge / latch bolts
    if part == "top":
        R(img, 3, 0, 12, 1, CHROME)
        R(img, 3, 1, 12, 1, CHROME_D)
        pat(img, 3, 3, [
            "..cbccbc..",
            ".cc____cc.",
            "cc______cc",
            "b__g_____b",
            "c_g______c",
            "c________c",
            "b________b",
            "cc______cc",
            ".cc____cc.",
            "..cbccbc..",
        ], {"c": CHROME, "b": STEEL_D, "g": GLASS_L})
    else:
        pat(img, 4, 1, [
            "..cccc..",
            ".c..c.c.",
            "c...c..c",
            "cccchccc",
            "c...c..c",
            ".c..c.c.",
            "..cccc..",
        ], {"c": CHROME, "h": STEEL_D})
        px(img, [(6, 1), (7, 1)], CHROME_L)
        for y in range(10, 13):
            for x in range(3, 13):
                px(img, [(x, y)], HAZARD if (x + y) % 4 < 2 else BLACK)
        R(img, 3, 9, 12, 9, RED_D)
        R(img, 3, 13, 12, 15, CHROME)
        R(img, 3, 13, 12, 13, CHROME_L)
        R(img, 3, 15, 12, 15, CHROME_D)
    return img


def door_item(top, bottom):
    img = new()
    full = new(16, 32)
    full.alpha_composite(top, (0, 0))
    full.alpha_composite(bottom, (0, 16))
    small = full.resize((8, 16), Image.NEAREST)
    for y in range(16):
        for x in range(1, 7):
            if small.getpixel((x, y))[3] == 0:
                small.putpixel((x, y), rgba(GLASS))
    img.alpha_composite(small, (4, 0))
    return img


def door_state(name):
    """Vanilla iron_door blockstate structure (powered omitted: it does not change the model)."""
    base = {"east": 0, "south": 90, "west": 180, "north": 270}
    variants = {}
    for facing in ("east", "north", "south", "west"):
        for half, part in (("lower", "bottom"), ("upper", "top")):
            for hinge in ("left", "right"):
                for opened in ("false", "true"):
                    rot = base[facing]
                    if opened == "true":
                        rot = (rot + (90 if hinge == "left" else 270)) % 360
                    v = {"model": T(f"{name}_{part}_{hinge}" + ("_open" if opened == "true" else ""))}
                    if rot:
                        v["y"] = rot
                    variants[f"facing={facing},half={half},hinge={hinge},open={opened}"] = v
    write_json(os.path.join(STATES_DIR, name + ".json"), {"variants": variants})


def door_models(name):
    for part in ("bottom", "top"):
        for hinge in ("left", "right"):
            for opened in ("", "_open"):
                write_json(os.path.join(BLOCKS_DIR, f"{name}_{part}_{hinge}{opened}.json"),
                           {"parent": f"minecraft:block/door_{part}_{hinge}{opened}", "render_type": "minecraft:cutout",
                            "textures": {"bottom": T(f"{name}_bottom"), "top": T(f"{name}_top")}})


# --- block models ---------------------------------------------------------------------------

def poster_models(name):
    for half in ("lower", "upper"):
        m = Model({"art": f"{name}_{half}", "edge": "poster_edge"}, f"{name}_{half}")
        faces = ("north", "east", "west") + (("down",) if half == "lower" else ("up",))
        m.box((0, 0, 15), (16, 16, 16), "edge", faces=faces, face_tex={"north": "art"}, face_uv={"north": FULL})
        m.write(f"{name}_{half}")


def cargo_crate_model():
    write_json(os.path.join(BLOCKS_DIR, "cargo_crate.json"),
               {"parent": "minecraft:block/cube_column",
                "textures": {"end": T("cargo_crate_top"), "side": T("cargo_crate_side")}})


def supply_cabinet_model():
    m = Model({"front": "supply_cabinet_front", "side": "supply_cabinet_side", "top": "supply_cabinet_top",
               **CHROME_T}, "supply_cabinet_side")
    m.box((0, 0, 0), (16, 16, 16), "side", face_tex={"north": "front", "up": "top", "down": "top"}, cull=True)
    for x in (6, 9.25):
        m.box((x, 7, -0.5), (x + 0.75, 10, 0), "chrome", faces=("north", "east", "west", "up", "down"))
    m.write("supply_cabinet")


def workbench_model():
    m = Model({"front": "retro_workbench_front", "side": "retro_workbench_side", "top": "retro_workbench_top",
               "edge": "retro_workbench_edge", "cream": "st_cream", "peg": "retro_workbench_pegboard",
               "steel": "st_steel", "red": "st_red", **CHROME_T}, "retro_workbench_side")
    m.box((1, 0, 1), (15, 10, 15), "side", faces=SIDES + ("down",), face_tex={"north": "front", "south": "cream", "down": "cream"},
          cull=True)
    m.box((0, 10, 0), (16, 12, 16), "edge", face_tex={"up": "top", "down": "cream"}, cull=True)
    # pegboard tool rack along the back
    m.box((0, 12, 14.5), (16, 16, 16), "peg", faces=("north", "south", "east", "west", "up"),
          face_tex={"south": "cream", "up": "chrome", "east": "chrome", "west": "chrome"},
          face_uv={"north": [0, 0, 16, 4], "south": [0, 0, 16, 4]}, cull=True)
    # bench vise at the front-left corner
    m.box((1.5, 12, 1.5), (5.5, 13, 4.5), "steel")
    m.box((2, 13, 1.5), (5, 14.5, 2.25), "red", faces=("north", "south", "east", "west", "up"))
    m.box((2, 13, 3.5), (5, 14.5, 4.25), "red", faces=("north", "south", "east", "west", "up"))
    m.box((3.25, 13, 0.5), (3.75, 13.5, 1.5), "chrome", faces=("north", "east", "west", "up", "down"))
    m.box((2.25, 13, 0.25), (4.75, 13.5, 0.5), "chrome")
    m.write("retro_workbench")


def galley_stove_model(lit):
    m = Model({"front": "galley_stove_front" + ("_on" if lit else ""), "side": "galley_stove_side",
               "hob": "galley_stove_hob" + ("_on" if lit else ""), "back": "galley_stove_back",
               "cream": "st_cream", "bak": "st_bakelite", **CHROME_T}, "galley_stove_side")
    m.box((1, 0, 1), (15, 13, 15), "side", faces=SIDES + ("down",), face_tex={"north": "front", "down": "cream"},
          cull=True)
    m.box((0, 13, 0), (16, 14, 16), "chrome", faces=SIDES + ("down",), cull=True)
    m.glow((0, 14, 0), (16, 14, 16), "hob", face="up", lit=lit)
    # backsplash with the clock lamp
    m.box((0, 14, 14.5), (16, 16, 16), "back", faces=("north", "south", "east", "west", "up"),
          face_uv={"north": [0, 0, 16, 2], "south": [0, 0, 16, 2]}, cull=True)
    # knobs on the control strip and the oven door handle
    for x in (2.5, 5, 9.5, 12):
        m.box((x, 10.75, 0.25), (x + 1.25, 12, 1), "bak", faces=("north", "east", "west", "up", "down"))
    m.box((3, 8.5, 0), (13, 9, 0.5), "chrome")
    m.box((3, 8.5, 0.5), (3.5, 9, 1), "chrome", faces=("east", "west", "up", "down"))
    m.box((12.5, 8.5, 0.5), (13, 9, 1), "chrome", faces=("east", "west", "up", "down"))
    if lit:   # glowing oven glass (u 5..11, v 8..13 of the front), just proud of the door
        m.glow((5, 3, 0.9), (11, 8, 0.9), "front", uv=[5, 8, 11, 13])
    m.write("galley_stove" + ("_on" if lit else ""))


def lab_sink_model():
    m = Model({"front": "lab_sink_front", "side": "lab_sink_side", "steel": "lab_sink_steel", "water": "lab_sink_water",
               "red": "st_red", "teal": "st_teal", **CHROME_T}, "lab_sink_steel")
    m.box((1, 0, 1), (15, 11, 15), "side", faces=SIDES + ("down",), face_tex={"north": "front"}, cull=True)
    # stainless counter ring around the basin
    m.box((0, 11, 0), (16, 13, 3), "steel", cull=True)
    m.box((0, 11, 12), (16, 13, 16), "steel", cull=True)
    m.box((0, 11, 3), (3, 13, 12), "steel", faces=("east", "west", "up", "down"), cull=True)
    m.box((13, 11, 3), (16, 13, 12), "steel", faces=("east", "west", "up", "down"), cull=True)
    m.box((3, 12.25, 3), (13, 12.25, 12), "water", faces=("up",))
    # backsplash, taps and the gooseneck faucet
    m.box((0, 13, 14.5), (16, 14.5, 16), "steel", faces=("north", "east", "west", "up"), cull=True)
    m.box((4, 13, 13.25), (5.5, 14, 14.5), "red", faces=("north", "east", "west", "up"))
    m.box((10.5, 13, 13.25), (12, 14, 14.5), "teal", faces=("north", "east", "west", "up"))
    m.box((7.5, 13, 13), (8.5, 16, 14), "chrome", faces=("north", "south", "east", "west", "up"))
    m.box((7.5, 15, 9.5), (8.5, 16, 13), "chrome", faces=("north", "east", "west", "up", "down"))
    m.box((7.5, 14, 9.5), (8.5, 15, 10.5), "chrome", faces=("north", "south", "east", "west", "down"))
    m.write("lab_sink")


def tape_archive_model():
    m = Model({"back": "tape_archive_back", "frame": "tape_archive_frame", "side": "tape_archive_side",
               "shelf": "tape_archive_shelf", "top": "supply_cabinet_top"}, "tape_archive_side")
    m.box((0, 0, 2), (16, 16, 16), "side", faces=("north", "south", "east", "west", "up", "down"),
          face_tex={"north": "back", "up": "top", "down": "top"}, cull=True)
    m.box((0, 0, 0), (1, 16, 2), "frame", faces=("north", "east", "west", "up", "down"), face_tex={"west": "side"},
          cull=True)
    m.box((15, 0, 0), (16, 16, 2), "frame", faces=("north", "east", "west", "up", "down"), face_tex={"east": "side"},
          cull=True)
    m.box((1, 15, 0), (15, 16, 2), "frame", faces=("north", "up", "down"), face_tex={"up": "top"}, cull=True)
    m.box((1, 0, 0), (15, 1, 2), "frame", faces=("north", "up", "down"), face_tex={"down": "top"}, cull=True)
    m.box((1, 7, 0), (15, 8, 2), "shelf", faces=("north", "up", "down"), cull=True)
    m.write("tape_archive")


# --- blockstates ---------------------------------------------------------------------------------

def state_facing_half(name, lit=False):
    variants = {}
    for facing, rot in (("north", 0), ("east", 90), ("south", 180), ("west", 270)):
        for half in ("lower", "upper"):
            for l in (("false", "true") if lit else (None,)):
                v = {"model": T(f"{name}_{half}" + ("_on" if l == "true" else ""))}
                if rot:
                    v["y"] = rot
                variants[f"facing={facing},half={half}" + (f",lit={l}" if l else "")] = v
    write_json(os.path.join(STATES_DIR, name + ".json"), {"variants": variants})


def generate_v4_textures():
    tex("vending_front_lower", vend_front("lower"))
    tex("vending_front_upper", vend_front("upper"))
    tex("vending_side_lower", vend_side("lower"))
    tex("vending_side_upper", vend_side("upper"))
    tex("vending_window", vend_window(False))
    tex("vending_window_on", vend_window(True))
    tex("vending_header", vend_header(False))
    tex("vending_header_on", vend_header(True))
    tex("vending_coin", vend_coin(False))
    tex("vending_coin_on", vend_coin(True))
    tex("poster_edge", flat(FRAME))
    for name, fn in POSTERS.items():
        art = fn()
        tex(f"{name}_upper", art.crop((0, 0, 16, 16)))
        tex(f"{name}_lower", art.crop((0, 16, 16, 32)))
    for half in ("lower", "upper"):
        tex(f"crew_locker_front_{half}", locker_front(half))
        tex(f"crew_locker_side_{half}", locker_side(half))
    tex("crew_locker_top", locker_top())
    tex("cargo_crate_side", cargo_side())
    tex("cargo_crate_top", cargo_top())
    tex("supply_cabinet_front", supply_front())
    tex("supply_cabinet_side", supply_side())
    tex("supply_cabinet_top", supply_top())
    tex("retro_workbench_front", bench_front())
    tex("retro_workbench_side", bench_side())
    tex("retro_workbench_top", bench_top())
    tex("retro_workbench_edge", bench_edge())
    tex("retro_workbench_pegboard", pegboard())
    tex("galley_stove_front", stove_front(False))
    tex("galley_stove_front_on", stove_front(True))
    tex("galley_stove_side", stove_side())
    tex("galley_stove_hob", stove_hob(False))
    tex("galley_stove_hob_on", stove_hob(True))
    tex("galley_stove_back", stove_back())
    tex("lab_sink_front", sink_front())
    tex("lab_sink_side", sink_side())
    tex("lab_sink_steel", stainless())
    tex("lab_sink_water", water())
    tex("tape_archive_back", archive_back())
    tex("tape_archive_frame", archive_frame())
    tex("tape_archive_side", archive_side())
    tex("tape_archive_shelf", archive_shelf())
    for name, fn in (("station_door", station_door), ("airlock_door", airlock_door)):
        top, bottom = fn("top"), fn("bottom")
        tex(f"{name}_top", top)
        tex(f"{name}_bottom", bottom)
        save(door_item(top, bottom), "item", name)


def generate_v4():
    generate_v4_textures()
    vending_models()
    state_facing_half("vending_machine", lit=True)
    for name in POSTERS:
        poster_models(name)
        state_facing_half(name)
        poster_item_model(name)
    locker_models()
    state_facing_half("crew_locker")
    cargo_crate_model()
    state_simple("cargo_crate")
    supply_cabinet_model()
    state_facing("supply_cabinet")
    workbench_model()
    state_facing("retro_workbench")
    for lit in (False, True):
        galley_stove_model(lit)
    state_facing("galley_stove", lit=True)
    lab_sink_model()
    state_facing("lab_sink")
    tape_archive_model()
    state_facing("tape_archive")
    for name in ("cargo_crate", "supply_cabinet", "retro_workbench", "galley_stove", "lab_sink", "tape_archive"):
        block_item(name)
    for name in ("station_door", "airlock_door"):
        door_models(name)
        door_state(name)
        flat_item(name)


# ----------------------------------------------------------------------------

def generate():
    generate_textures()
    for lit in (False, True):
        control_panel(lit)
        radar_scope(lit)
        computer_bank(lit)
        hydroponic_planter(lit)
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
                        ("ceiling_light", "ceiling_light_on"),
                        ("telescope", None), ("space_globe", None), ("floor_grate", None), ("hull_panel", None),
                        ("hull_panel_striped", None), ("hull_window", None), ("reactor_core", "reactor_core_on")):
        block_item(name, model)
    for name in ("control_panel", "star_chart", "wall_sconce"):
        flat_item(name)
    generate_v4()


if __name__ == "__main__":
    generate()
