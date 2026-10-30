#!/usr/bin/env python3
"""Art for the Retro Cosmos furniture & decor pack: textures, texture animations, block models,
blockstates and item model definitions. Called from gen_resources.main() via generate().

Everything is authored for facing=north (front toward -Z) and rotated in the blockstates.
Textures are drawn in "block space" (1 texel = 1/16 block) and elements use the vanilla default
UV projection unless a face carries a detail texture (screens, dials, clock face, neon tubes).
"""
import math
import os

from PIL import Image, ImageDraw

from gen_resources import (ASSETS, MOD, BLACK, GLASS, GLASS_L, NAVY, ORANGE, ORANGE_L, RED, RED_D, RED_L, STEEL,
                           STEEL_D, TEAL, TEAL_D, TEAL_L, YELLOW, item_def, new, noise_fill, outline, px, rgba, save,
                           shade, write_json)

# Furniture palette: the shared cream / white / chrome tones are toned down here so large enamel and
# chrome areas sit at vanilla quartz / white-concrete brightness (<= ~226) instead of glowing next to
# vanilla blocks. Only small specular glints and emissive (lit) textures go brighter.
CREAM = (226, 216, 190)
CREAM_D = (192, 180, 150)
CREAM_L = (234, 226, 204)
WHITE = (224, 224, 220)
WHITE_D = (196, 196, 192)
WHITE_DD = (166, 168, 166)
WHITE_L = (230, 230, 226)
CHROME = (194, 202, 210)
CHROME_D = (128, 138, 150)
CHROME_L = (226, 232, 238)

# extra palette for furniture
WALNUT = (122, 76, 46)
WALNUT_D = (84, 50, 30)
WALNUT_L = (158, 106, 66)
BRASS = (214, 168, 76)
BRASS_D = (150, 110, 44)
BRASS_L = (244, 216, 140)
GRILLE = (62, 48, 34)
GRILLE_L = (206, 170, 92)
SCREEN_OFF = (36, 46, 44)
SCREEN_OFF_L = (70, 86, 84)
TUBE_OFF = (150, 152, 158)
TUBE_OFF_D = (88, 90, 96)
BULB_OFF = (206, 208, 204)
BULB_ON = (255, 244, 198)
BULB_ON_L = (255, 255, 236)

BLOCKS_DIR = os.path.join(ASSETS, "models", "block")
ITEMS_DIR = os.path.join(ASSETS, "models", "item")
STATES_DIR = os.path.join(ASSETS, "blockstates")

TEXTURES = []   # (name, frames) for the preview sheet


def tex(name, img):
    """Saves a static block texture and remembers it for the preview sheet."""
    save(img, "block", name)
    TEXTURES.append((name, 1))


def tex_anim(name, frames, frametime, interpolate=False):
    """Saves a vertical frame strip + .mcmeta animation."""
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


def T(name):
    return f"{MOD}:block/{name}"


# ----------------------------------------------------------------------------
# Textures
# ----------------------------------------------------------------------------

def chrome_plain(seed=21):
    """Polished chrome: horizon-line reflection (light sky band, dark ground band)."""
    img = new()
    noise_fill(img, CHROME, 3, seed)
    rows = {0: CHROME_L, 1: CHROME_L, 2: CHROME, 6: CHROME_D, 7: CHROME_D, 8: STEEL, 9: CHROME_D,
            12: CHROME_L, 13: CHROME_L, 15: CHROME_D}
    for y, c in rows.items():
        for x in range(16):
            px(img, [(x, y)], c)
    return img


def chrome_ribbed(seed=22):
    img = new()
    noise_fill(img, CHROME, 3, seed)
    for x in range(16):
        c = (CHROME_L, CHROME, CHROME_D, CHROME)[x % 4]
        for y in range(16):
            px(img, [(x, y)], c)
    return img


def chrome_trim_end():
    img = new()
    noise_fill(img, CHROME, 3, 23)
    d = ImageDraw.Draw(img)
    for r, c in ((0, CHROME_D), (2, CHROME_L), (4, CHROME_D), (6, CHROME_L)):
        d.rectangle((r, r, 15 - r, 15 - r), outline=rgba(c))
    px(img, [(7, 7), (8, 7), (7, 8), (8, 8)], STEEL)
    return img


def upholstery(base, dark, light, seed):
    """Tufted vinyl: diamond seams with buttons at the crossings."""
    img = new()
    noise_fill(img, base, 5, seed)
    for y in range(16):
        for x in range(16):
            if (x + y) % 8 == 0 or (x - y) % 8 == 0:
                px(img, [(x, y)], dark)
    for (x, y) in [(0, 0), (8, 0), (4, 4), (12, 4), (0, 8), (8, 8), (4, 12), (12, 12)]:
        px(img, [(x, y)], light)
    return img


def upholstery_piped(base, dark, light, seed):
    """Smooth cushion face with a cream piping line along the top (sofa seat/back fronts)."""
    img = new()
    noise_fill(img, base, 4, seed)
    for x in range(16):
        px(img, [(x, 0)], light)
        px(img, [(x, 1)], CREAM)
        px(img, [(x, 15)], dark)
    for y in range(3, 15, 1):
        px(img, [(5, y), (10, y)], dark)
    return img


def cream_formica():
    """Cream laminate with the classic atomic 'boomerang & starburst' print."""
    img = new()
    noise_fill(img, CREAM, 3, 31)
    for (x, y, c) in [(2, 3, TEAL_D), (10, 2, RED), (6, 9, NAVY), (13, 11, TEAL_D), (1, 13, RED)]:
        px(img, [(x, y), (x + 1, y + 1), (x + 2, y + 1), (x + 2, y + 2)], c)   # little boomerangs
    for (x, y) in [(7, 4), (3, 8), (12, 7), (9, 13)]:
        px(img, [(x, y - 1), (x, y + 1), (x - 1, y), (x + 1, y)], BLACK)
        px(img, [(x, y)], BRASS)
    return img


def walnut(seed=41):
    img = new()
    noise_fill(img, WALNUT, 5, seed)
    for y in range(16):
        for x in range(16):
            v = int(2.5 + 2.4 * math.sin(x * 0.9 + y * 0.35 + seed))
            if v == 0:
                px(img, [(x, y)], WALNUT_D)
            elif v == 4:
                px(img, [(x, y)], WALNUT_L)
    return img


def teal_plastic():
    img = new()
    noise_fill(img, TEAL, 3, 43)
    for x in range(16):
        px(img, [(x, 0)], TEAL_L)
        px(img, [(x, 15)], TEAL_D)
    return img


def cream_bakelite():
    img = new()
    noise_fill(img, CREAM, 2, 44)
    for x in range(16):
        px(img, [(x, 0)], CREAM_L)
        px(img, [(x, 15)], CREAM_D)
    return img


def flat(color, var=2, seed=50):
    img = new()
    noise_fill(img, color, var, seed)
    return img


def bulb(on):
    img = new()
    if on:
        noise_fill(img, BULB_ON, 3, 45)
        d = ImageDraw.Draw(img)
        d.ellipse((3, 3, 12, 12), fill=rgba(BULB_ON_L))
    else:
        noise_fill(img, BULB_OFF, 3, 46)
        d = ImageDraw.Draw(img)
        d.ellipse((3, 3, 12, 12), fill=rgba((222, 224, 220)))
        px(img, [(4, 4), (5, 4)], (236, 236, 234))
    return img


def lava_lamp_frames(on):
    """Rocket table lamp body (uv 4..12 x 0..16 is shown): rising lava blobs."""
    frames = []
    n = 8 if on else 1
    for f in range(n):
        img = new()
        if on:
            noise_fill(img, (250, 190, 70), 4, 60)
            bg = ImageDraw.Draw(img)
            blobs = [(8, 3, 3, 4, RED), (6, 11, 2, 3, RED_L), (10, 9, 2, 2, RED), (7, 15, 3, 2, RED_L)]
            for (cx, cy, rx, ry, c) in blobs:
                cy = (cy - f * 2) % 16
                for yy in (cy, cy + 16, cy - 16):
                    bg.ellipse((cx - rx, yy - ry, cx + rx, yy + ry), fill=rgba(c))
            for x in range(16):
                px(img, [(4, (x * 3) % 16)], (255, 230, 170))   # glass glint column
        else:
            noise_fill(img, (46, 70, 92), 4, 61)
            bg = ImageDraw.Draw(img)
            for (cx, cy, rx, ry) in [(8, 13, 3, 2), (7, 15, 4, 1)]:
                bg.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=rgba((110, 40, 46)))
            for y in range(16):
                px(img, [(4, y)], (90, 120, 140))
        frames.append(img)
    return frames


def tv_screen_off():
    img = new()
    noise_fill(img, TEAL, 2, 70)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((1, 1, 14, 14), radius=3, fill=rgba(SCREEN_OFF))
    for i in range(3, 8):
        px(img, [(i, 10 - i + 3)], SCREEN_OFF_L)
    px(img, [(3, 3), (4, 3), (3, 4)], (96, 112, 110))
    return img


def tv_screen_frames():
    """Colour-bar test pattern with a rolling dark scanline band and faint snow."""
    bars = [(192, 192, 192), (220, 220, 40), (40, 210, 210), (40, 200, 40), (210, 40, 210), (220, 40, 40), (40, 40, 220)]
    frames = []
    for f in range(8):
        img = new()
        noise_fill(img, TEAL, 2, 70)
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((1, 1, 14, 14), radius=3, fill=rgba(BLACK))
        for y in range(2, 14):
            for x in range(2, 14):
                if y < 10:
                    c = bars[min(6, (x - 2) * 7 // 12)]
                else:
                    c = (16, 16, 16) if (x // 2) % 2 == (y // 2) % 2 else (235, 235, 230) if x < 8 else (20, 20, 70)
                if (x + y * 3 + f * 5) % 11 == 0:
                    c = shade(c, 40)
                if (y + f) % 12 in (2, 3):   # rolling scan band
                    c = shade(c, -70)
                elif y % 2 == 1:
                    c = shade(c, -18)
                px(img, [(x, y)], c)
        frames.append(img)
    return frames


def tv_front():
    """Block-space front: walnut frame, speaker grille and knobs on the right of the screen."""
    img = walnut(71)
    d = ImageDraw.Draw(img)
    d.rectangle((12, 3, 14, 7), fill=rgba(GRILLE))
    for y in range(3, 8):
        for x in range(12, 15):
            if (x + y) % 2 == 0:
                px(img, [(x, y)], GRILLE_L)
    px(img, [(13, 9), (13, 11)], CHROME)
    px(img, [(12, 9), (12, 11)], CHROME_D)
    px(img, [(14, 9), (14, 11)], CHROME_L)
    px(img, [(13, 13)], RED)   # power light
    return img


def radio_side():
    img = cream_bakelite()
    for x in range(16):
        px(img, [(x, 7)], RED)
    return img


def radio_front(lit, frame=0):
    """Block-space front (x 2..14, y 0..9 of the block = texels 2..14 x 7..16)."""
    img = cream_bakelite()
    d = ImageDraw.Draw(img)
    # chrome foot strip and the red shoulder line (row 8 sits on the upper, inset box)
    for x in range(2, 14):
        px(img, [(x, 15)], CHROME)
        px(img, [(x, 8)], RED)
    # round speaker grille on the left
    d.ellipse((3, 9, 7, 13), fill=rgba(GRILLE), outline=rgba(CHROME))
    for y in range(10, 13):
        for x in range(4, 7):
            if (x + y) % 2 == 0:
                px(img, [(x, y)], GRILLE_L)
    # dial window on the right
    glow = (255, 214, 120) if lit else (120, 104, 72)
    d.rectangle((9, 9, 13, 11), fill=rgba(glow), outline=rgba(CHROME_D))
    for x in range(10, 13):
        px(img, [(x, 11)], (120, 90, 40) if lit else (90, 78, 56))
    needle_x = 10 + [0, 1, 2, 3, 3, 2, 1, 0][frame % 8]
    px(img, [(needle_x, 9), (needle_x, 10)], RED)
    if lit:
        px(img, [(9, 9)], (255, 240, 190))
        px(img, [(8, 14)], ORANGE_L)   # warm tube glow through the vent
    else:
        px(img, [(8, 14)], CREAM_D)
    return img


def clock_face():
    img = new()
    d = ImageDraw.Draw(img)
    d.ellipse((0, 0, 15, 15), fill=rgba(CREAM), outline=rgba(BRASS))
    for i in range(12):
        a = math.radians(i * 30)
        x, y = 7.5 + 6.2 * math.sin(a), 7.5 - 6.2 * math.cos(a)
        px(img, [(round(x), round(y))], BLACK if i % 3 == 0 else (110, 100, 80))
    # hands at ten past ten
    d.line((7, 7, 5, 4), fill=rgba(BLACK))
    d.line((7, 7, 11, 5), fill=rgba(BLACK))
    px(img, [(7, 7), (8, 7), (7, 8), (8, 8)], BRASS)
    px(img, [(7, 7)], BRASS_L)
    return img


def clock_second_frames():
    frames = []
    for f in range(12):
        img = new()
        a = math.radians(f * 30)
        d = ImageDraw.Draw(img)
        d.line((7.5, 7.5, 7.5 + 6 * math.sin(a), 7.5 - 6 * math.cos(a)), fill=rgba(RED))
        px(img, [(7, 7)], RED)
        frames.append(img)
    return frames


def clock_rim():
    img = new()
    noise_fill(img, CREAM, 2, 80)
    return img


def brass():
    img = new()
    noise_fill(img, BRASS, 6, 81)
    for x in range(16):
        px(img, [(x, 0), (x, 1)], BRASS_L)
        px(img, [(x, 14), (x, 15)], BRASS_D)
    return img


def neon_back():
    img = new()
    noise_fill(img, (28, 28, 32), 3, 90)
    d = ImageDraw.Draw(img)
    d.rectangle((2, 1, 13, 14), outline=rgba(STEEL))
    for (x, y) in [(3, 2), (12, 2), (3, 13), (12, 13)]:
        px(img, [(x, y)], CHROME)
    return img


def neon_tubes(lit, frame=0):
    """Block-space tube art (texels x 2..14, y 1..15): rocket, orbit ring, stars; transparent elsewhere."""
    img = new()
    if lit:
        red, body, ring, ring_hi, star_c, flame = ((255, 90, 90), (255, 236, 200), (110, 255, 240),
                                                   (230, 255, 252), (255, 230, 90), (255, 170, 60))
        halo_r, halo_t = (72, 26, 34), (22, 58, 62)
    else:
        red = body = ring = ring_hi = star_c = flame = TUBE_OFF
        halo_r = halo_t = None
    d = ImageDraw.Draw(img)
    # orbit ring (ellipse tilted = drawn as a wide ellipse)
    d.ellipse((2, 6, 13, 11), outline=rgba(ring))
    if lit:   # chasing highlight segment on the ring
        pts = [(x, y) for y in range(6, 12) for x in range(2, 14) if img.getpixel((x, y))[3]]
        pts.sort(key=lambda p: math.atan2(p[1] - 8.5, p[0] - 7.5))
        n = len(pts)
        for k in range(3):
            px(img, [pts[(frame * 3 + k) % n]], ring_hi)
    # rocket body
    for y in range(3, 12):
        px(img, [(6, y), (9, y)], red)
    px(img, [(7, 2), (8, 2), (7, 12), (8, 12)], red)
    px(img, [(7, 5), (8, 5), (7, 6), (8, 6)], body)
    # fins
    px(img, [(5, 10), (4, 11), (10, 10), (11, 11)], red)
    # flame (flickers)
    if frame % 2 == 0 or not lit:
        px(img, [(7, 13), (8, 13), (7, 14)], flame)
    else:
        px(img, [(7, 13), (8, 13), (8, 14)], flame)
    # stars
    for (x, y) in [(3, 3), (12, 4), (4, 13), (12, 13)]:
        px(img, [(x, y)], star_c if (not lit or (x + y + frame) % 3) else ring_hi)
    if lit:   # dim halo pixels next to the tubes
        src = img.copy()
        for y in range(16):
            for x in range(2, 14):
                if src.getpixel((x, y))[3] == 0 and 1 <= y <= 14:
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < 16 and 0 <= ny < 16 and src.getpixel((nx, ny))[3]:
                            c = src.getpixel((nx, ny))[:3]
                            px(img, [(x, y)], halo_r if c[0] > c[2] else halo_t)
                            break
    return img


def porthole():
    img = new()
    noise_fill(img, STEEL, 4, 100)
    d = ImageDraw.Draw(img)
    for (x, y) in [(1, 1), (14, 1), (1, 14), (14, 14)]:
        px(img, [(x, y)], CHROME_D)
        px(img, [(x + (1 if x == 1 else -1), y)], STEEL_D)
    d.ellipse((1, 1, 14, 14), fill=rgba(CHROME), outline=rgba(CHROME_D))
    d.ellipse((2, 2, 13, 13), outline=rgba(CHROME_L))
    for i in range(8):
        a = math.radians(i * 45 + 22.5)
        px(img, [(round(7.5 + 6 * math.sin(a)), round(7.5 - 6 * math.cos(a)))], STEEL_D)
    d.ellipse((3, 3, 12, 12), fill=rgba(GLASS, 120), outline=rgba(STEEL_D))
    for i in range(4, 9):
        img.putpixel((i, 12 - i + 1), rgba(GLASS_L, 180))
    img.putpixel((5, 5), rgba(GLASS_L, 210))
    img.putpixel((6, 5), rgba(GLASS_L, 210))
    return img


def checkered_tile():
    img = new()
    for y in range(16):
        for x in range(16):
            white = ((x // 4) + (y // 4)) % 2 == 0
            c = (222, 222, 216) if white else (34, 32, 36)
            if x % 4 == 3 or y % 4 == 3:
                c = (198, 198, 192) if white else (22, 20, 24)
            px(img, [(x, y)], c)
    return img


def turquoise_panel():
    img = new()
    noise_fill(img, TEAL, 4, 110)
    for i in range(16):
        px(img, [(i, 0), (0, i)], TEAL_L)
        px(img, [(i, 15), (15, i)], TEAL_D)
    # starburst motif
    for i in range(8):
        a = math.radians(i * 45)
        L = 5 if i % 2 == 0 else 3
        for r in range(2, L + 1):
            px(img, [(round(7.5 + r * math.sin(a)), round(7.5 - r * math.cos(a)))], CREAM)
        if i % 2 == 0:
            px(img, [(round(7.5 + (L + 1) * math.sin(a)), round(7.5 - (L + 1) * math.cos(a)))], BRASS)
    px(img, [(7, 7), (8, 7), (7, 8), (8, 8)], BRASS)
    return img


def cream_panel_side():
    img = new()
    noise_fill(img, CREAM, 3, 111)
    for x in range(16):
        px(img, [(x, 0)], CREAM_L)
        px(img, [(x, 15)], CREAM_D)
        px(img, [(x, 10)], CHROME_L)
        px(img, [(x, 11)], CHROME)
        px(img, [(x, 12)], CHROME_D)
    return img


def cream_panel_end():
    img = new()
    noise_fill(img, CREAM, 3, 112)
    for i in range(16):
        px(img, [(i, 0), (0, i)], CREAM_L)
        px(img, [(i, 15), (15, i)], CREAM_D)
    return img


# --- flat item sprites for the wall pieces -----------------------------------

def clock_item_sprite():
    img = new()
    d = ImageDraw.Draw(img)
    for i in range(16):
        a = math.radians(i * 22.5)
        L = 7.5 if i % 2 == 0 else 5.5
        d.line((7.5, 7.5, 7.5 + L * math.sin(a), 7.5 - L * math.cos(a)), fill=rgba(BRASS))
    for i in range(0, 16, 2):
        a = math.radians(i * 22.5)
        px(img, [(round(7.5 + 7.2 * math.sin(a)), round(7.5 - 7.2 * math.cos(a)))], CHROME_L)
    face = clock_face().resize((9, 9), Image.NEAREST)
    img.alpha_composite(face, (3, 3))
    d.ellipse((3, 3, 11, 11), outline=rgba(BRASS_D))
    outline(img, BRASS_D)
    return img


def neon_item_sprite():
    img = neon_back()
    img.alpha_composite(neon_tubes(True, 0))
    outline(img, STEEL_D)
    return img


def stool_chrome():
    """Vanilla-style chrome for cuboid sides: flat tone with a vertical highlight stripe."""
    img = new()
    for y in range(16):
        for x in range(16):
            c = CHROME
            if x in (6, 7):
                c = CHROME_L
            elif x in (9, 10):
                c = CHROME_D
            px(img, [(x, y)], c)
    return img


def chrome_top():
    """Concentric rings (block space) so stepped discs read as turned chrome from above."""
    img = new()
    for y in range(16):
        for x in range(16):
            r = int(max(abs(x - 7.5), abs(y - 7.5)))
            c = (CHROME, CHROME_L, CHROME_D, CHROME, CHROME_L, CHROME, CHROME_L, CHROME_D)[r]
            px(img, [(x, y)], c)
    return img


def tufted(base, dark, light):
    """Flat vinyl with an 8-px tuft grid: seams on 7/15, buttons on 3/11. Same on every face."""
    img = new()
    for y in range(16):
        for x in range(16):
            c = base
            if x % 8 == 7 or y % 8 == 7:
                c = dark
            elif x % 8 == 3 and y % 8 == 3:
                c = dark
            elif (x % 8, y % 8) in ((2, 3), (3, 2)):
                c = light
            px(img, [(x, y)], c)
    return img


def shell_white():
    img = new()
    for y in range(16):
        for x in range(16):
            px(img, [(x, y)], WHITE if y < 13 else WHITE_D)
    return img


def shell_white_top():
    img = new()
    for y in range(16):
        for x in range(16):
            px(img, [(x, y)], WHITE_L)
    return img


def generate_textures():
    tex("stool_chrome", stool_chrome())
    tex("chrome_top", chrome_top())
    tex("red_tufted", tufted(RED, RED_D, RED_L))
    tex("teal_tufted", tufted(TEAL, TEAL_D, TEAL_L))
    tex("shell_white", shell_white())
    tex("shell_white_top", shell_white_top())
    tex("furn_chrome", chrome_plain())
    tex("chrome_trim", chrome_ribbed())
    tex("chrome_trim_end", chrome_trim_end())
    tex("teal_upholstery", upholstery(TEAL, TEAL_D, TEAL_L, 1))
    tex("teal_upholstery_front", upholstery_piped(TEAL, TEAL_D, TEAL_L, 2))
    tex("cream_formica", cream_formica())
    tex("table_edge", chrome_ribbed(24))
    tex("walnut", walnut())
    tex("teal_plastic", teal_plastic())
    tex("cream_bakelite", cream_bakelite())
    tex("bulb_off", bulb(False))
    tex("bulb_on", bulb(True))
    tex("lamp_cone_red", flat(RED, 4, 51))
    tex("lava_lamp_off", lava_lamp_frames(False)[0])
    tex_anim("lava_lamp_on", lava_lamp_frames(True), 6, interpolate=True)
    tex("tv_front", tv_front())
    tex("tv_screen_off", tv_screen_off())
    tex_anim("tv_screen_on", tv_screen_frames(), 3)
    tex("radio_side", radio_side())
    tex("radio_front", radio_front(False))
    tex_anim("radio_front_on", [radio_front(True, f) for f in range(8)], 8, interpolate=True)
    tex("clock_face", clock_face())
    tex("clock_rim", clock_rim())
    tex("brass", brass())
    tex_anim("clock_seconds", clock_second_frames(), 20)
    tex("neon_back", neon_back())
    tex("neon_tubes_off", neon_tubes(False))
    tex_anim("neon_tubes_on", [neon_tubes(True, f) for f in range(6)], 5)
    tex("porthole_window", porthole())
    tex("checkered_tile", checkered_tile())
    tex("turquoise_panel", turquoise_panel())
    tex("cream_panel_side", cream_panel_side())
    tex("cream_panel_end", cream_panel_end())
    save(clock_item_sprite(), "item", "starburst_clock")
    save(neon_item_sprite(), "item", "neon_rocket_sign")


# ----------------------------------------------------------------------------
# Model builder
# ----------------------------------------------------------------------------

ALL_FACES = ("north", "south", "east", "west", "up", "down")


def clamp16(v):
    return max(0.0, min(16.0, v))


def default_uv(face, frm, to):
    """Vanilla default UV projection of an element onto one of its faces."""
    x0, y0, z0 = frm
    x1, y1, z1 = to
    uv = {
        "down": (x0, 16 - z1, x1, 16 - z0),
        "up": (x0, z0, x1, z1),
        "north": (16 - x1, 16 - y1, 16 - x0, 16 - y0),
        "south": (x0, 16 - y1, x1, 16 - y0),
        "west": (z0, 16 - y1, z1, 16 - y0),
        "east": (16 - z1, 16 - y1, 16 - z0, 16 - y0),
    }[face]
    return [clamp16(v) for v in uv]


def num(v):
    v = round(float(v), 3)
    return int(v) if v == int(v) else v


class Model:
    def __init__(self, textures, particle, ao=True, render_type=None, display=None):
        self.textures = {k: T(v) for k, v in textures.items()}
        self.textures["particle"] = T(particle)
        self.elements = []
        self.ao = ao
        self.render_type = render_type
        self.display = display

    def box(self, frm, to, tex, faces=ALL_FACES, face_tex=None, uv=None, face_uv=None, rot=None, shade=None, name=None,
            cull=False):
        """Adds a cuboid. tex / face_tex are texture keys (without '#'). rot = (axis, angle, origin).
        cull=True adds a cullface to every face lying on the block boundary (full-block pieces)."""
        face_tex = face_tex or {}
        face_uv = face_uv or {}
        out = {}
        for f in faces:
            # skip the degenerate faces of a zero-thickness plane
            if (f in ("north", "south") and frm[2] == to[2] and (frm[0] == to[0] or frm[1] == to[1])) or \
               (f in ("east", "west") and frm[0] == to[0] and (frm[1] == to[1] or frm[2] == to[2])) or \
               (f in ("up", "down") and frm[1] == to[1] and (frm[0] == to[0] or frm[2] == to[2])):
                continue
            u = face_uv.get(f, uv) or default_uv(f, frm, to)
            out[f] = {"uv": [num(v) for v in u], "texture": "#" + face_tex.get(f, tex)}
            if cull and not rot and {"north": frm[2] == 0, "south": to[2] == 16, "west": frm[0] == 0,
                                     "east": to[0] == 16, "down": frm[1] == 0, "up": to[1] == 16}[f]:
                out[f]["cullface"] = f
        e = {"from": [num(v) for v in frm], "to": [num(v) for v in to], "faces": out}
        if name:
            e["name"] = name
        if rot:
            axis, angle, origin = rot
            e["rotation"] = {"origin": [num(v) for v in origin], "axis": axis, "angle": num(angle)}
        if shade is False:
            e["shade"] = False
        self.elements.append(e)
        return e

    def glow(self, frm, to, tex, face="north", uv=None, lit=True):
        """A single-face plane for an emissive detail (screen, oven window, dial glass). Only this face
        carries shade:false (and only when lit), so the surrounding casing keeps normal shading."""
        return self.box(frm, to, tex, faces=(face,), face_uv={face: uv} if uv else None, shade=False if lit else None)

    def octagon(self, frm, to, tex, axis="y", **kw):
        """A box plus a slightly smaller copy rotated 45 degrees: reads as a round disc / cylinder."""
        self.box(frm, to, tex, **kw)
        c = [(a + b) / 2 for a, b in zip(frm, to)]
        half = [(b - a) / 2 for a, b in zip(frm, to)]
        i, j = {"y": (0, 2), "z": (0, 1), "x": (1, 2)}[axis]
        f2, t2 = list(frm), list(to)
        for k in (i, j):
            f2[k] = c[k] - half[k] * 0.87
            t2[k] = c[k] + half[k] * 0.87
        kw2 = dict(kw)
        kw2["rot"] = (axis, 45, c)
        self.box(f2, t2, tex, **kw2)

    def write(self, name):
        m = {"textures": self.textures}
        if self.render_type:
            m["render_type"] = self.render_type
        if not self.ao:
            m["ambientocclusion"] = False
        if self.display:
            m["display"] = self.display
        m["elements"] = self.elements
        write_json(os.path.join(BLOCKS_DIR, name + ".json"), m)
        return name


# --- blockstate helpers -------------------------------------------------------

FACINGS = (("north", 0), ("east", 90), ("south", 180), ("west", 270))


def state_simple(name, model=None):
    write_json(os.path.join(STATES_DIR, name + ".json"), {"variants": {"": {"model": T(model or name)}}})


def state_lit(name):
    write_json(os.path.join(STATES_DIR, name + ".json"), {"variants": {
        "lit=false": {"model": T(name)}, "lit=true": {"model": T(name + "_on")}}})


def state_facing(name, lit=False):
    variants = {}
    for facing, rot in FACINGS:
        for l in (("false", "true") if lit else (None,)):
            v = {"model": T(name + ("_on" if l == "true" else ""))}
            if rot:
                v["y"] = rot
            key = f"facing={facing}" + (f",lit={l}" if l else "")
            variants[key] = v
    write_json(os.path.join(STATES_DIR, name + ".json"), {"variants": variants})


def state_axis(name):
    write_json(os.path.join(STATES_DIR, name + ".json"), {"variants": {
        "axis=y": {"model": T(name)},
        "axis=z": {"model": T(name + "_horizontal"), "x": 90},
        "axis=x": {"model": T(name + "_horizontal"), "x": 90, "y": 90}}})


def block_item(name, model=None):
    item_def(name, T(model or name))


def flat_item(name):
    write_json(os.path.join(ITEMS_DIR, name + ".json"),
               {"parent": "minecraft:item/generated", "textures": {"layer0": f"{MOD}:item/{name}"}})
    item_def(name, f"{MOD}:item/{name}")


# ----------------------------------------------------------------------------
# Block models
# ----------------------------------------------------------------------------

def sputnik_rods(m, center, rods, bulb_size, bulb_tex, rod_tex="chrome", rod_w=0.5):
    """rods = [(axis, length, rot) ...]: a rod from the centre along +axis (or both ways if length<0 ... see below).
    Each rod carries a bulb at its tip; rotation (axis, angle) is applied about the centre."""
    cx, cy, cz = center
    for (direction, length, rot) in rods:
        dx, dy, dz = direction
        hw = rod_w / 2
        hb = bulb_size / 2
        # rod from centre to tip
        tip = (cx + dx * length, cy + dy * length, cz + dz * length)
        frm = [min(cx + dx * 0.5, tip[0]) - (hw if dx == 0 else 0), min(cy + dy * 0.5, tip[1]) - (hw if dy == 0 else 0),
               min(cz + dz * 0.5, tip[2]) - (hw if dz == 0 else 0)]
        to = [max(cx + dx * 0.5, tip[0]) + (hw if dx == 0 else 0), max(cy + dy * 0.5, tip[1]) + (hw if dy == 0 else 0),
              max(cz + dz * 0.5, tip[2]) + (hw if dz == 0 else 0)]
        r = (rot[0], rot[1], center) if rot else None
        m.box(frm, to, rod_tex, rot=r)
        bf = [tip[0] + dx * hb - hb, tip[1] + dy * hb - hb, tip[2] + dz * hb - hb]
        bt = [tip[0] + dx * hb + hb, tip[1] + dy * hb + hb, tip[2] + dz * hb + hb]
        m.box(bf, bt, bulb_tex, rot=r, shade=False if bulb_tex == "bulb_on" else None)


def atomic_floor_lamp(lit):
    b = "bulb_on" if lit else "bulb_off"
    m = Model({"chrome": "furn_chrome", "ribbed": "chrome_trim", "bulb_on": "bulb_on", "bulb_off": "bulb_off",
               "red": "lamp_cone_red"}, "furn_chrome")
    m.octagon((5, 0, 5), (11, 0.75, 11), "chrome")
    m.box((7.5, 0.75, 7.5), (8.5, 12, 8.5), "ribbed")
    c = (8, 13, 8)
    m.octagon((6.75, 11.75, 6.75), (9.25, 14.25, 9.25), "chrome")
    rods = []
    for d in ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1)):
        rods.append((d, 3.5, None))
        rods.append((d, 3.0, ("y", 45)))
    rods.append(((0, 1, 0), 2.0, None))
    for d, ax in (((1, 0, 0), "z"), ((-1, 0, 0), "z"), ((0, 0, 1), "x"), ((0, 0, -1), "x")):
        rods.append((d, 2.8, (ax, 45 if d in ((-1, 0, 0), (0, 0, 1)) else -45)))   # four rods tilted up
        rods.append((d, 2.4, (ax, -45 if d in ((-1, 0, 0), (0, 0, 1)) else 45)))   # four tilted down
    sputnik_rods(m, c, rods, 1.25, b)
    return m.write("atomic_floor_lamp" + ("_on" if lit else ""))


def rocket_table_lamp(lit):
    body = "lava_on" if lit else "lava_off"
    m = Model({"chrome": "furn_chrome", "lava_on": "lava_lamp_on", "lava_off": "lava_lamp_off", "red": "lamp_cone_red",
               "ribbed": "chrome_trim"}, "furn_chrome")
    m.octagon((5, 0, 5), (11, 0.75, 11), "chrome")
    m.box((6.5, 0.75, 6.5), (9.5, 2, 9.5), "ribbed")
    # glass body: 2 texels per block unit of the lava texture (uv 4..12 horizontally, full height)
    side_uv = {f: [4, 0, 12, 16] for f in ("north", "south", "east", "west")}
    m.box((6, 2, 6), (10, 9, 10), body, face_uv=side_uv, shade=False if lit else None)
    # chrome nose cone
    m.box((6.5, 9, 6.5), (9.5, 10.5, 9.5), "chrome")
    m.box((7.25, 10.5, 7.25), (8.75, 12, 8.75), "chrome")
    m.box((7.75, 12, 7.75), (8.25, 13, 8.25), "chrome")
    # three red fins
    for (f, t) in (((4.75, 0.75, 7.5), (6, 4.5, 8.5)), ((10, 0.75, 7.5), (11.25, 4.5, 8.5)), ((7.5, 0.75, 10), (8.5, 4.5, 11.25))):
        m.box(f, t, "red")
    # small switch on the front of the base
    m.box((7.5, 0.75, 4.75), (8.5, 1.5, 5), "red")
    return m.write("rocket_table_lamp" + ("_on" if lit else ""))


def sputnik_chandelier(lit):
    b = "bulb_on" if lit else "bulb_off"
    m = Model({"chrome": "furn_chrome", "bulb_on": "bulb_on", "bulb_off": "bulb_off"}, "furn_chrome")
    m.box((7.5, 13, 7.5), (8.5, 16, 8.5), "chrome")
    m.octagon((6, 9, 6), (10, 13, 10), "chrome")
    c = (8, 11, 8)
    rods = []
    # four main arms drooping 22.5 degrees
    rods.append(((1, 0, 0), 5.0, ("z", -22.5)))
    rods.append(((-1, 0, 0), 5.0, ("z", 22.5)))
    rods.append(((0, 0, 1), 5.0, ("x", 22.5)))
    rods.append(((0, 0, -1), 5.0, ("x", -22.5)))
    # four diagonal arms (horizontal, rotated 45 about y), a little shorter
    for d in ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1)):
        rods.append((d, 4.2, ("y", 45)))
    # four arms steeply down (45) and one straight down
    rods.append(((1, 0, 0), 3.6, ("z", -45)))
    rods.append(((-1, 0, 0), 3.6, ("z", 45)))
    rods.append(((0, 0, 1), 3.6, ("x", 45)))
    rods.append(((0, 0, -1), 3.6, ("x", -45)))
    rods.append(((0, -1, 0), 3.2, None))
    # four short arms up
    rods.append(((1, 0, 0), 3.0, ("z", 45)))
    rods.append(((-1, 0, 0), 3.0, ("z", -45)))
    rods.append(((0, 0, 1), 3.0, ("x", -45)))
    rods.append(((0, 0, -1), 3.0, ("x", 45)))
    sputnik_rods(m, c, rods, 1.75, b)
    return m.write("sputnik_chandelier" + ("_on" if lit else ""))


def diner_stool():
    """Vanilla-style: stepped chrome base, column, chrome seat rim with the red cushion inset on top."""
    m = Model({"chrome": "stool_chrome", "top": "chrome_top", "red": "red_tufted"}, "red_tufted")
    caps = {"up": "top", "down": "top"}
    m.box((4, 0, 4), (12, 1, 12), "chrome", face_tex=caps)
    m.box((5, 1, 5), (11, 2, 11), "chrome", faces=("north", "south", "east", "west", "up"), face_tex=caps)
    m.box((7, 2, 7), (9, 8, 9), "chrome", faces=("north", "south", "east", "west"))
    m.box((3, 8, 3), (13, 9, 13), "chrome", face_tex=caps)
    m.box((4, 9, 4), (12, 10, 12), "red", faces=("north", "south", "east", "west", "up"))
    return m.write("diner_stool")


def egg_chair():
    """Vanilla-style egg chair: chrome pedestal, stepped white bowl, teal cushion, white shell with
    teal lining opening to the front (north)."""
    m = Model({"chrome": "stool_chrome", "top": "chrome_top", "shell": "shell_white", "shell_top": "shell_white_top",
               "teal": "teal_tufted"}, "shell_white")
    caps = {"up": "top", "down": "top"}
    sh = {"up": "shell_top", "down": "shell_top"}
    sides = ("north", "south", "east", "west")
    m.box((4, 0, 4), (12, 1, 12), "chrome", face_tex=caps)
    m.box((6, 1, 6), (10, 2, 10), "chrome", faces=sides)
    # bowl, two steps
    m.box((3, 2, 3), (13, 4, 13), "shell", faces=sides + ("down",), face_tex=sh)
    m.box((2, 4, 2), (14, 7, 14), "shell", face_tex=sh)
    # seat cushion
    m.box((3, 7, 3), (13, 8, 12), "teal", faces=("north", "east", "west", "up"))
    # back shell with teal lining, raised back cushion
    m.box((2, 7, 12), (14, 15, 14), "shell", faces=("north", "south", "east", "west", "up"),
          face_tex={"north": "teal", "up": "shell_top"})
    m.box((4, 8, 11), (12, 13, 12), "teal", faces=("north", "east", "west", "up", "down"))
    # side wings
    m.box((2, 7, 8), (4, 14, 12), "shell", faces=("north", "east", "west", "up"), face_tex={"east": "teal", "up": "shell_top"})
    m.box((12, 7, 8), (14, 14, 12), "shell", faces=("north", "east", "west", "up"), face_tex={"west": "teal", "up": "shell_top"})
    # hood (rounded top of the egg)
    m.box((3, 15, 9), (13, 16, 14), "shell", face_tex={"down": "teal", "up": "shell_top"})
    return m.write("egg_chair")


def googie_sofa():
    m = Model({"teal": "teal_upholstery", "front": "teal_upholstery_front", "walnut": "walnut", "chrome": "furn_chrome"},
              "teal_upholstery")
    # splayed tapered chrome legs
    for (x, z, ang) in ((1.5, 1.5, -22.5), (13.5, 1.5, 22.5), (1.5, 13.5, -22.5), (13.5, 13.5, 22.5)):
        m.box((x, 0, z), (x + 1, 3.5, z + 1), "chrome", rot=("z", ang, (x + 0.5, 3.5, z + 0.5)))
    m.box((0, 3, 0.5), (16, 4, 16), "walnut")
    m.box((0, 4, 0), (16, 7, 12), "teal", face_tex={"north": "front"})
    m.box((0, 7, 12), (16, 13, 16), "teal", face_tex={"north": "front"})
    m.box((0, 13, 12.5), (16, 14, 15.5), "teal")
    return m.write("googie_sofa")


def boomerang_table():
    m = Model({"top": "cream_formica", "edge": "table_edge", "chrome": "furn_chrome", "walnut": "walnut"}, "cream_formica")
    sides = {f: "edge" for f in ("north", "south", "east", "west")}
    sides["down"] = "walnut"
    # two arms meeting at the back, forming the boomerang
    m.box((2.5, 10.5, 4.75), (7.5, 12, 13.25), "top", face_tex=sides, rot=("y", 45, (5, 11.25, 9)))
    m.box((8.5, 10.5, 4.75), (13.5, 12, 13.25), "top", face_tex=sides, rot=("y", -45, (11, 11.25, 9)))
    m.box((5.5, 10.5, 9.5), (10.5, 12, 14.5), "top", face_tex=sides, name="vertex")
    # hairpin legs: pairs of thin chrome rods with a bar at the foot
    for (x, z) in ((3.0, 7.0), (13.0, 7.0), (8.0, 12.0)):
        for off in (-0.75, 0.75):
            m.box((x + off - 0.25, 0.5, z - 0.25), (x + off + 0.25, 10.5, z + 0.25), "chrome")
        m.box((x - 1, 0, z - 0.25), (x + 1, 0.5, z + 0.25), "chrome")
    return m.write("boomerang_table")


def atomic_tv(lit):
    screen = "screen_on" if lit else "screen_off"
    m = Model({"walnut": "walnut", "front": "tv_front", "screen_on": "tv_screen_on", "screen_off": "tv_screen_off",
               "teal": "teal_plastic", "chrome": "furn_chrome", "black": "neon_back"}, "walnut")
    for (x, z, ang) in ((2, 4, -22.5), (13, 4, 22.5), (2, 11, -22.5), (13, 11, 22.5)):
        m.box((x, 0, z), (x + 1, 3, z + 1), "chrome", rot=("z", ang, (x + 0.5, 3, z + 0.5)))
    m.box((1, 3, 3), (15, 14, 13), "walnut", face_tex={"north": "front"})
    # CRT box protruding from the cabinet with a teal bezel
    m.box((2, 4, 2), (12, 13, 3), "teal", faces=("east", "west", "up", "down"))
    m.glow((2, 4, 2), (12, 13, 2), screen, uv=[0, 0, 16, 16], lit=lit)
    # rabbit-ear antenna
    m.box((7.5, 14, 7.5), (8.5, 14.75, 8.5), "black")
    m.box((7.75, 14.5, 7.75), (8.25, 17.5, 8.25), "chrome", rot=("z", 22.5, (8, 14.5, 8)))
    m.box((7.75, 14.5, 7.75), (8.25, 17.5, 8.25), "chrome", rot=("z", -22.5, (8, 14.5, 8)))
    return m.write("atomic_tv" + ("_on" if lit else ""))


def tube_radio(lit):
    front = "front_on" if lit else "front"
    m = Model({"side": "radio_side", "front": "radio_front", "front_on": "radio_front_on", "cream": "cream_bakelite",
               "red": "lamp_cone_red", "chrome": "furn_chrome"}, "cream_bakelite")
    m.box((2, 0, 5), (14, 7, 11), "side", face_tex={"north": front, "up": "cream", "down": "cream"})
    if lit:   # glowing dial window (texels 9..13 x 9..11 of the front = x 2..7, y 4..7)
        m.glow((2, 4, 4.8), (7, 7, 4.8), front, uv=[9, 9, 14, 12])
    m.box((3, 7, 5), (13, 9, 11), "side", face_tex={"north": front, "up": "cream"})
    m.box((4, 9, 5.5), (12, 9.5, 10.5), "cream")
    # two red knobs under the dial and a chrome carrying handle
    m.box((9.5, 1, 4.5), (10.75, 2.25, 5), "red")
    m.box((11.75, 1, 4.5), (13, 2.25, 5), "red")
    m.box((6, 9.5, 7.5), (10, 10, 8.5), "chrome")
    return m.write("tube_radio" + ("_on" if lit else ""))


def starburst_clock():
    m = Model({"brass": "brass", "chrome": "furn_chrome", "face": "clock_face", "rim": "clock_rim",
               "seconds": "clock_seconds"}, "brass", render_type="minecraft:cutout")
    c = (8, 8, 15.25)
    m.octagon((6.5, 6.5, 15.25), (9.5, 9.5, 16), "chrome", axis="z")
    # 16 rays: 8 long (axis + diagonals) with chrome tips, 8 short in between
    for ang in (0, 45, -45):
        m.box((1.5, 7.75, 15), (14.5, 8.25, 15.5), "brass", rot=("z", ang, c) if ang else None)
        m.box((1, 7.5, 14.9), (1.75, 8.5, 15.6), "chrome", rot=("z", ang, c) if ang else None)
        m.box((14.25, 7.5, 14.9), (15, 8.5, 15.6), "chrome", rot=("z", ang, c) if ang else None)
    m.box((7.75, 1.5, 15), (8.25, 14.5, 15.5), "brass")
    m.box((7.5, 1, 14.9), (8.5, 1.75, 15.6), "chrome")
    m.box((7.5, 14.25, 14.9), (8.5, 15, 15.6), "chrome")
    for ang in (22.5, -22.5):
        m.box((2.75, 7.75, 15.1), (13.25, 8.25, 15.5), "brass", rot=("z", ang, c))
        m.box((7.75, 2.75, 15.1), (8.25, 13.25, 15.5), "brass", rot=("z", ang, c))
    # cream face (octagonal) with the printed dial, then the animated second hand plane
    m.box((5.4, 5.4, 14.4), (10.6, 10.6, 15), "rim", rot=("z", 45, (8, 8, 14.7)))
    m.box((5, 5, 14.3), (11, 11, 15), "rim", face_tex={"north": "face"}, face_uv={"north": [0, 0, 16, 16]})
    m.box((5, 5, 14.2), (11, 11, 14.2), "seconds", faces=("north",), face_uv={"north": [0, 0, 16, 16]})
    return m.write("starburst_clock")


def neon_rocket_sign(lit):
    tubes = "tubes_on" if lit else "tubes_off"
    m = Model({"back": "neon_back", "tubes_on": "neon_tubes_on", "tubes_off": "neon_tubes_off", "chrome": "furn_chrome"},
              "neon_back", render_type="minecraft:cutout")
    m.box((2, 1, 15.25), (14, 15, 16), "back", face_uv={"north": [2, 1, 14, 15]})
    for (x, y) in ((3, 2), (12, 2), (3, 13), (12, 13)):
        m.box((x, y, 14.6), (x + 1, y + 1, 15.25), "chrome")
    m.box((2, 1, 14.5), (14, 15, 14.5), tubes, faces=("north", "south"), face_uv={"north": [2, 1, 14, 15], "south": [2, 1, 14, 15]},
          shade=False if lit else None)
    return m.write("neon_rocket_sign" + ("_on" if lit else ""))


def full_blocks():
    write_json(os.path.join(BLOCKS_DIR, "porthole_window.json"),
               {"parent": "minecraft:block/cube_all", "render_type": "minecraft:translucent",
                "textures": {"all": T("porthole_window")}})
    write_json(os.path.join(BLOCKS_DIR, "checkered_tile.json"),
               {"parent": "minecraft:block/cube_all", "textures": {"all": T("checkered_tile")}})
    write_json(os.path.join(BLOCKS_DIR, "turquoise_panel.json"),
               {"parent": "minecraft:block/cube_all", "textures": {"all": T("turquoise_panel")}})
    write_json(os.path.join(BLOCKS_DIR, "cream_panel.json"),
               {"parent": "minecraft:block/cube_column",
                "textures": {"end": T("cream_panel_end"), "side": T("cream_panel_side")}})
    write_json(os.path.join(BLOCKS_DIR, "chrome_trim.json"),
               {"parent": "minecraft:block/cube_column",
                "textures": {"end": T("chrome_trim_end"), "side": T("chrome_trim")}})
    write_json(os.path.join(BLOCKS_DIR, "chrome_trim_horizontal.json"),
               {"parent": "minecraft:block/cube_column_horizontal",
                "textures": {"end": T("chrome_trim_end"), "side": T("chrome_trim")}})


# ----------------------------------------------------------------------------

def generate():
    generate_textures()

    for lit in (False, True):
        atomic_floor_lamp(lit)
        rocket_table_lamp(lit)
        sputnik_chandelier(lit)
        atomic_tv(lit)
        tube_radio(lit)
        neon_rocket_sign(lit)
    diner_stool()
    egg_chair()
    googie_sofa()
    boomerang_table()
    starburst_clock()
    full_blocks()

    state_lit("atomic_floor_lamp")
    state_facing("rocket_table_lamp", lit=True)
    state_lit("sputnik_chandelier")
    state_simple("diner_stool")
    state_facing("egg_chair")
    state_facing("googie_sofa")
    state_facing("boomerang_table")
    state_facing("atomic_tv", lit=True)
    state_facing("tube_radio", lit=True)
    state_facing("starburst_clock")
    state_facing("neon_rocket_sign", lit=True)
    for b in ("porthole_window", "checkered_tile", "turquoise_panel", "cream_panel"):
        state_simple(b)
    state_axis("chrome_trim")

    # items: lit look for the light sources, flat sprites for the two wall pieces
    for name, model in (("atomic_floor_lamp", "atomic_floor_lamp_on"), ("rocket_table_lamp", "rocket_table_lamp_on"),
                        ("sputnik_chandelier", "sputnik_chandelier_on"), ("diner_stool", None), ("egg_chair", None),
                        ("googie_sofa", None), ("boomerang_table", None), ("atomic_tv", "atomic_tv_on"),
                        ("tube_radio", "tube_radio_on"), ("porthole_window", None), ("checkered_tile", None),
                        ("turquoise_panel", None), ("cream_panel", None), ("chrome_trim", None)):
        block_item(name, model)
    flat_item("starburst_clock")
    flat_item("neon_rocket_sign")


if __name__ == "__main__":
    generate()
