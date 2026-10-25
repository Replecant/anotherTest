#!/usr/bin/env python3
"""Art for Retro Cosmos Stage 2 "flight + system map": GUI textures only (no models, no data).
Called from gen_resources.main() via generate().

  gui/system_map/frame.png      320x200  orrery screen panel (Googie bezel, star viewport, phosphor info CRT)
  gui/system_map/<body>.png     pulp-illustration sprites of the invented Vesper system
                                (vesper, cinder, mirage, homestead, lantern, verdigris, goliath, halo, belt_rock, freedom_station)
  gui/system_map/selection.png  24x24    amber targeting reticle
  gui/system_map/lock.png       7x9      chrome padlock
  gui/system_map/button.png     80x48    push-button, 3 states (normal / hover / disabled), 80x16 each
  gui/flight_hud.png            160x40   launch telemetry panel
  gui/flight_hud_bar.png        148x6    fuel bar fill
  entity/rocket_plume.png       16x64    exhaust flame strip (nozzle at the top)
  gui/cockpit.png               480x270  first-person capsule interior overlay (porthole glass transparent)
"""
import math
import random

from PIL import Image, ImageDraw

from gen_resources import (AMBER_LAMP, BLACK, CHROME, CHROME_D, CHROME_L, CREAM, CREAM_D, NAVY, NAVY_L, ORANGE,
                           ORANGE_L, RED, RED_D, RED_L, STEEL, STEEL_D, TEAL, TEAL_D, TEAL_L, WHITE, YELLOW, new, px,
                           rgba, save, shade)

# extra palette
SPACE = (10, 14, 38)          # deep navy space
SPACE_L = (22, 30, 70)
CRT_BG = (10, 26, 16)         # matches ConsoleScreen.CRT_BG
CRT_EDGE = (20, 60, 36)
BAKELITE = (40, 36, 36)
BAKELITE_L = (90, 84, 80)
AMBER = (255, 193, 77)
AMBER_D = (196, 128, 32)


# ----------------------------------------------------------------------------
# shared drawing bits
# ----------------------------------------------------------------------------

def starburst(d, cx, cy, r, color, dot=CREAM, step=45, r2=None):
    """Atomic-age starburst: long rays every `step` degrees, short rays in between, bright centre dot."""
    r2 = r2 if r2 is not None else max(1, r // 2)
    for a in range(0, 360, step):
        d.line((cx, cy, cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))), fill=rgba(color))
        a2 = a + step / 2
        d.line((cx, cy, cx + r2 * math.cos(math.radians(a2)), cy + r2 * math.sin(math.radians(a2))),
               fill=rgba(color))
    d.point((cx, cy), fill=rgba(dot))


def lamp(d, x, y, color, size=4):
    d.ellipse((x, y, x + size, y + size), fill=rgba(color), outline=rgba(BLACK))
    d.point((x + 1, y + 1), fill=rgba(tuple(min(255, c + 70) for c in color)))


def rivet(img, x, y):
    px(img, [(x, y)], CHROME_L)
    px(img, [(x + 1, y), (x, y + 1)], CHROME)
    px(img, [(x + 1, y + 1)], CHROME_D)


def scanlines(img, box, every=2, delta=-6):
    x0, y0, x1, y1 = box
    for y in range(y0, y1 + 1):
        if (y - y0) % every:
            continue
        for x in range(x0, x1 + 1):
            r, g, b, a = img.getpixel((x, y))
            img.putpixel((x, y), (max(0, r + delta), max(0, g + delta), max(0, b + delta), a))


def vignette(img, box, strength=26):
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    rx, ry = (x1 - x0) / 2, (y1 - y0) / 2
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            t = min(1.0, math.hypot((x - cx) / rx, (y - cy) / ry))
            k = int(strength * t * t)
            r, g, b, a = img.getpixel((x, y))
            img.putpixel((x, y), (max(0, r - k), max(0, g - k), max(0, b - k), a))


def crt_glass(img, d, box, bg=CRT_BG):
    """Dark phosphor screen with a faint edge glow, scanlines and vignette."""
    x0, y0, x1, y1 = box
    d.rectangle(box, fill=rgba(bg))
    scanlines(img, box, every=2, delta=-4)
    vignette(img, box, strength=10)
    d.rectangle(box, outline=rgba(CRT_EDGE))
    # a soft phosphor bloom in the top-left corner (like the console tube)
    for i, c in enumerate(((16, 40, 24), (13, 33, 20))):
        d.line((x0 + 1 + i, y0 + 1 + i, x1 - 1 - i, y0 + 1 + i), fill=rgba(c))
        d.line((x0 + 1 + i, y0 + 1 + i, x0 + 1 + i, y1 - 1 - i), fill=rgba(c))


def star_field(img, box, seed=7):
    x0, y0, x1, y1 = box
    rnd = random.Random(seed)
    for _ in range(((x1 - x0) * (y1 - y0)) // 55):
        x, y = rnd.randint(x0 + 1, x1 - 1), rnd.randint(y0 + 1, y1 - 1)
        k = rnd.random()
        if k < 0.6:
            c = (62, 72, 120)
        elif k < 0.9:
            c = (110, 124, 180)
        else:
            c = (196, 206, 236)
            if rnd.random() < 0.5:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    px(img, [(x + dx, y + dy)], (70, 84, 140))
        px(img, [(x, y)], c)


# ----------------------------------------------------------------------------
# A. system map
# ----------------------------------------------------------------------------

def map_frame():
    W, H = 320, 200
    img = new(W, H)
    d = ImageDraw.Draw(img)
    # bezel: cream bakelite, black edge, chrome inner trim
    d.rounded_rectangle((0, 0, W - 1, H - 1), radius=8, fill=rgba(CREAM), outline=rgba(BLACK))
    d.rounded_rectangle((1, 1, W - 2, H - 2), radius=7, outline=rgba(CHROME_L))
    d.rounded_rectangle((2, 2, W - 3, H - 3), radius=6, outline=rgba(CHROME))
    d.rounded_rectangle((3, 3, W - 4, H - 4), radius=5, outline=rgba(CREAM_D))
    # faint bakelite grain
    rnd = random.Random(3)
    for y in range(4, H - 4):
        for x in range(4, W - 4):
            if rnd.random() < 0.08:
                px(img, [(x, y)], (234, 226, 200))

    # title plate x=8..311, y=6..17
    d.rectangle((8, 6, 311, 17), fill=rgba((246, 240, 220)), outline=rgba(CHROME_D))
    d.line((9, 7, 310, 7), fill=rgba(CHROME_L))
    d.line((9, 16, 310, 16), fill=rgba(CREAM_D))
    d.rectangle((9, 7, 13, 16), fill=rgba(RED))
    d.line((13, 7, 13, 16), fill=rgba(RED_D))
    d.rectangle((306, 7, 310, 16), fill=rgba(TEAL))
    d.line((306, 7, 306, 16), fill=rgba(TEAL_D))
    for x in range(18, 302, 6):          # dotted guide line under the title
        px(img, [(x, 16)], CHROME_D)

    # map viewport x=8..215, y=22..191 : dark bakelite bezel + chrome lip + navy space
    d.rectangle((6, 20, 217, 193), fill=rgba(BAKELITE), outline=rgba(BLACK))
    d.rectangle((7, 21, 216, 192), outline=rgba(BAKELITE_L))
    vp = (8, 22, 215, 191)
    d.rectangle(vp, fill=rgba(SPACE))
    # nebulous depth: slightly lighter band across the middle
    for y in range(vp[1], vp[3] + 1):
        t = 1 - abs((y - 106) / 90)
        if t > 0:
            c = (SPACE[0] + int(5 * t), SPACE[1] + int(7 * t), SPACE[2] + int(14 * t))
            d.line((vp[0], y, vp[2], y), fill=rgba(c))
    star_field(img, vp, seed=11)
    scanlines(img, vp, every=3, delta=-5)
    vignette(img, vp, strength=22)
    d.rectangle(vp, outline=rgba((30, 40, 84)))
    # corner tick marks on the glass (radar-screen feel)
    for (x, y, sx, sy) in ((9, 23, 1, 1), (214, 23, -1, 1), (9, 190, 1, -1), (214, 190, -1, -1)):
        d.line((x, y, x + sx * 5, y), fill=rgba(TEAL_D))
        d.line((x, y, x, y + sy * 5), fill=rgba(TEAL_D))

    # chrome divider between viewport and info panel (x=218..221)
    d.rectangle((218, 20, 221, 193), fill=rgba(CHROME))
    d.line((218, 20, 218, 193), fill=rgba(CHROME_L))
    d.line((221, 20, 221, 193), fill=rgba(CHROME_D))

    # info panel x=222..311, y=22..191 : bakelite bezel + phosphor CRT
    d.rectangle((222, 20, 313, 193), fill=rgba(BAKELITE), outline=rgba(BLACK))
    d.rectangle((223, 21, 312, 192), outline=rgba(BAKELITE_L))
    crt_glass(img, d, (222, 22, 311, 191))
    # recessed bay for the button (x=227..306, y=170..185)
    d.rectangle((225, 168, 308, 187), fill=rgba((6, 16, 10)), outline=rgba((14, 40, 24)))
    d.line((226, 169, 307, 169), fill=rgba((4, 10, 6)))

    # ornaments: starbursts + lamps in the bottom strip, rivets in the corners
    for cx in (18, 301):
        starburst(d, cx, 196, 3, RED, dot=CREAM, step=45, r2=2)
    for i, c in enumerate((RED, AMBER_LAMP, (120, 230, 120), TEAL)):
        lamp(d, 232 + i * 9, 194, c, size=4)
    for x in range(30, 212, 2):
        px(img, [(x, 196)], CHROME_D)
    for (x, y) in ((4, 4), (315, 4), (4, 195), (315, 195)):
        rivet(img, x, y)
    # top strip: tiny chrome studs either side of the title plate
    for x in range(40, 300, 40):
        px(img, [(x, 3)], CHROME_D)
    return img


def planet(size, base, dark, light, outline_c=(14, 10, 24), bands=None, spots=None, seed=1, w=None):
    """Pulp-illustration planet: flat disc, lit from upper-left with a crescent terminator, 1px dark outline.
    bands: list of (y_offset_fraction, color, thickness) horizontal stripes clipped to the disc."""
    w = w or size
    img = new(w, size)
    r = (size - 2) / 2.0
    cx, cy = (w - 1) / 2.0, (size - 1) / 2.0
    for y in range(size):
        for x in range(w):
            dx, dy = x - cx, y - cy
            dist = math.hypot(dx, dy)
            if dist > r + 0.5:
                continue
            c = base
            if bands:
                for (fy, col, th) in bands:
                    if abs(dy - fy * r) <= th / 2.0:
                        c = col
            if spots:
                for (sx, sy, sr, col) in spots:
                    if math.hypot(dx - sx * r, dy - sy * r) <= sr * r:
                        c = col
            # terminator: lower-right third goes dark, upper-left gets a highlight
            lit = (-dx - dy) / (r * 1.41)
            if lit < -0.45:
                c = dark if c == base else tuple(int(v * 0.7) for v in c)
            elif lit > 0.62 and dist < r - 0.4:
                c = light
            if dist > r - 0.6:
                c = outline_c
            img.putpixel((x, y), rgba(c))
    return img


def belt_rock():
    """3x3 pebble: lit top-left, dark bottom-right rim (no room for a full outline at this size)."""
    img = new(3, 3)
    O, B, L = (34, 26, 28), (132, 112, 92), (190, 170, 146)
    for (x, y), c in {(1, 0): B, (0, 1): B, (1, 1): L, (2, 1): O, (1, 2): O, (0, 0): L, (2, 2): O, (2, 0): O, (0, 2): O}.items():
        img.putpixel((x, y), rgba(c))
    for (x, y) in ((2, 0), (0, 2)):
        img.putpixel((x, y), (34, 26, 28, 120))
    return img


def freedom_station():
    """Freedom Station: a tiny Googie wheel station - white/chrome ring on a hub, red accent, blue panel glint."""
    img = new(11, 11)
    O = (18, 14, 28)
    Wt, Wd, Ch, Cd = (246, 246, 242), (196, 200, 206), (214, 222, 230), (120, 130, 144)
    rows = [
        "....OOO....",
        "..OOWWWOO..",
        ".OWdO.OdWO.",
        ".OW.....WO.",
        "OW..OCO..WO",
        "OW.OCRCO.WO",
        "OW..OCO..WO",
        ".OW.....WO.",
        ".OWdO.OdWO.",
        "..OOWWWOO..",
        "....OOO....",
    ]
    pal = {"O": O, "W": Wt, "d": Wd, "C": Ch, "R": RED, "c": Cd}
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                img.putpixel((x, y), rgba(pal[ch]))
    # ring shading: lower-right of the ring goes grey, top-left stays white
    for (x, y) in ((8, 7), (7, 8), (6, 9), (9, 5), (9, 6), (5, 9)):
        if img.getpixel((x, y))[3]:
            img.putpixel((x, y), rgba(Wd))
    # four spokes from hub to ring (dark chrome)
    px(img, [(5, 2), (5, 3), (5, 7), (5, 8), (2, 5), (3, 5), (7, 5), (8, 5)], Cd)
    px(img, [(5, 1), (1, 5), (9, 5), (5, 9)], Wt)
    # solar panel glint (blue) on the top-right spoke, antenna tip top-left
    px(img, [(7, 3), (8, 2)], (70, 130, 220))
    px(img, [(7, 2)], (160, 200, 250))
    px(img, [(4, 4)], (255, 240, 220))
    return img


def selection():
    img = new(24, 24)
    d = ImageDraw.Draw(img)
    L = 7
    for (x, y, sx, sy) in ((0, 0, 1, 1), (23, 0, -1, 1), (0, 23, 1, -1), (23, 23, -1, -1)):
        d.line((x, y, x + sx * L, y), fill=rgba(AMBER))
        d.line((x, y, x, y + sy * L), fill=rgba(AMBER))
        d.line((x + sx, y + sy, x + sx * (L - 2), y + sy), fill=rgba(AMBER_D))
        d.line((x + sx, y + sy, x + sx, y + sy * (L - 2)), fill=rgba(AMBER_D))
        px(img, [(x, y)], (255, 236, 170))
    # centre cross-hair ticks
    px(img, [(11, 1), (12, 1), (11, 22), (12, 22), (1, 11), (1, 12), (22, 11), (22, 12)], AMBER_D)
    return img


def lock():
    img = new(7, 9)
    d = ImageDraw.Draw(img)
    # shackle
    d.rectangle((1, 0, 5, 4), outline=rgba(CHROME_D))
    px(img, [(2, 0), (3, 0), (4, 0), (1, 1), (5, 1)], CHROME_L)
    px(img, [(1, 2), (5, 2), (1, 3), (5, 3)], CHROME)
    px(img, [(2, 1), (3, 1), (4, 1), (2, 2), (3, 2), (4, 2), (2, 3), (3, 3), (4, 3)], (0, 0, 0, 0))
    # body
    d.rectangle((0, 4, 6, 8), fill=rgba(CHROME), outline=rgba(STEEL_D))
    d.line((1, 4, 5, 4), fill=rgba(CHROME_L))
    d.line((1, 8, 5, 8), fill=rgba(CHROME_D))
    px(img, [(1, 5)], CHROME_L)
    px(img, [(3, 6), (3, 7)], STEEL_D)
    return img


def button():
    img = new(80, 48)
    d = ImageDraw.Draw(img)
    states = (
        (RED, RED_L, RED_D, (255, 160, 150)),
        ((244, 96, 84), (255, 150, 132), RED_D, (255, 222, 206)),
        ((126, 124, 122), (158, 156, 152), (82, 80, 78), (186, 184, 180)),
    )
    for i, (base, light, dark, gloss) in enumerate(states):
        y = i * 16
        # chrome bezel ring
        d.rounded_rectangle((0, y, 79, y + 15), radius=5, fill=rgba(CHROME), outline=rgba(BLACK))
        d.line((2, y + 1, 77, y + 1), fill=rgba(CHROME_L))
        d.line((2, y + 14, 77, y + 14), fill=rgba(CHROME_D))
        # cap
        d.rounded_rectangle((2, y + 2, 77, y + 13), radius=4, fill=rgba(base), outline=rgba(dark))
        d.line((4, y + 3, 75, y + 3), fill=rgba(light))
        d.line((4, y + 12, 75, y + 12), fill=rgba(dark))
        px(img, [(5, y + 4), (6, y + 4), (7, y + 4), (5, y + 5)], gloss)
        px(img, [(74, y + 4), (73, y + 4), (72, y + 4), (74, y + 5)], gloss)
        if i == 2:
            # disabled: hatch the cap faintly
            for x in range(6, 74, 4):
                px(img, [(x, y + 8), (x + 1, y + 9)], (112, 110, 108))
    return img




# --- Solar System bodies (restored) ---

def solar_sun():
    img = new(32, 32)
    d = ImageDraw.Draw(img)
    cx = cy = 15.5
    # glow halo
    for rr, a in ((13, 36), (11, 60), (9, 96)):
        d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=(255, 170, 40, a))
    # rays: 8 long, 8 short, retro-illustration style
    for i in range(16):
        a = math.radians(i * 22.5)
        ln = 15 if i % 2 == 0 else 11
        col = ORANGE if i % 2 == 0 else ORANGE_L
        d.line((cx + 7 * math.cos(a), cy + 7 * math.sin(a), cx + ln * math.cos(a), cy + ln * math.sin(a)),
               fill=rgba(col))
    d.ellipse((cx - 8, cy - 8, cx + 8, cy + 8), fill=rgba((18, 10, 10)))
    d.ellipse((cx - 7, cy - 7, cx + 7, cy + 7), fill=rgba(ORANGE))
    d.ellipse((cx - 6, cy - 6, cx + 6, cy + 6), fill=rgba(YELLOW))
    d.ellipse((cx - 4, cy - 4, cx + 4, cy + 4), fill=rgba((252, 232, 120)))
    d.ellipse((cx - 5, cy - 5, cx - 2, cy - 2), fill=rgba((255, 250, 200)))
    px(img, [(12, 19), (13, 20), (19, 12), (20, 13)], ORANGE)
    # a wink of a 1950s "face": two eye dots and a smile
    px(img, [(13, 14), (18, 14)], (120, 60, 20))
    px(img, [(13, 18), (14, 19), (15, 19), (16, 19), (17, 19), (18, 18)], (120, 60, 20))
    return img


def solar_saturn():
    img = planet(16, (226, 196, 128), (122, 96, 58), (250, 236, 190), w=28,
                 bands=((-0.35, (206, 170, 104), 1), (0.25, (204, 162, 92), 2)))
    d = ImageDraw.Draw(img)
    back = img.copy()
    # ring: ellipse 26x8 centred, tilted look via two colours; the front half is drawn over the planet
    ring = new(28, 16)
    rd = ImageDraw.Draw(ring)
    rd.ellipse((1, 4, 26, 11), outline=rgba((14, 10, 24)))
    rd.ellipse((2, 5, 25, 10), fill=rgba((214, 180, 120)), outline=rgba((236, 214, 160)))
    rd.ellipse((4, 6, 23, 9), fill=(0, 0, 0, 0), outline=rgba((160, 120, 70)))
    rd.ellipse((6, 7, 21, 8), fill=(0, 0, 0, 0))
    rd.ellipse((5, 6, 22, 9), fill=(0, 0, 0, 0))
    # paste: back half behind, front half in front
    for y in range(16):
        for x in range(28):
            p = ring.getpixel((x, y))
            if p[3] == 0:
                continue
            if y <= 7 and back.getpixel((x, y))[3]:
                continue  # behind the planet
            img.putpixel((x, y), p)
    d.point((14, 7), fill=rgba((14, 10, 24)))
    return img


def solar_earth():
    img = planet(14, (62, 132, 210), (26, 60, 120), (170, 214, 250),
                 spots=((-0.15, -0.3, 0.32, (92, 170, 92)), (0.3, 0.35, 0.28, (92, 170, 92)),
                        (0.5, -0.2, 0.18, (240, 244, 250))))
    px(img, [(7, 4), (8, 5), (4, 9)], (120, 200, 120))
    return img


def solar_moon():
    img = new(6, 6)
    O, B, D, L = (14, 10, 24), (206, 206, 196), (150, 150, 142), (244, 244, 238)
    rows = ["..OO..", ".OLBO.", "OLBBDO", "OBBDDO", ".OBDO.", "..OO.."]
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                img.putpixel((x, y), rgba({"O": O, "B": B, "D": D, "L": L}[ch]))
    px(img, [(2, 3)], D)
    return img


def generate_solar_bodies():
    save(solar_sun(), "gui", "system_map", "sun")
    save(planet(10, (190, 180, 166), (104, 96, 88), (240, 234, 224),
                spots=((0.3, -0.3, 0.2, (140, 128, 118)), (-0.4, 0.3, 0.16, (140, 128, 118)))),
         "gui", "system_map", "mercury")
    save(planet(12, (236, 196, 110), (150, 110, 46), (252, 238, 190),
                bands=((-0.3, (226, 176, 92), 1), (0.4, (222, 170, 86), 1))),
         "gui", "system_map", "venus")
    save(solar_earth(), "gui", "system_map", "earth")
    save(solar_moon(), "gui", "system_map", "moon")
    save(planet(12, (214, 92, 56), (120, 44, 26), (248, 170, 130),
                spots=((0.0, -0.75, 0.3, (242, 236, 226)), (0.25, 0.2, 0.24, (160, 62, 40)))),
         "gui", "system_map", "mars")
    save(planet(24, (226, 186, 140), (124, 92, 60), (250, 232, 200),
                bands=((-0.55, (196, 140, 96), 2), (-0.15, (206, 150, 102), 2), (0.3, (190, 130, 90), 3),
                       (0.7, (200, 150, 110), 1)),
                spots=((0.35, 0.3, 0.16, (214, 90, 60)),)),
         "gui", "system_map", "jupiter")
    save(solar_saturn(), "gui", "system_map", "saturn")


def generate_system_map():
    save(map_frame(), "gui", "system_map", "frame")
    generate_solar_bodies()
    for name, fn in (("belt_rock", belt_rock), ("freedom_station", freedom_station)):
        save(fn(), "gui", "system_map", name)
    save(selection(), "gui", "system_map", "selection")
    save(lock(), "gui", "system_map", "lock")
    save(button(), "gui", "system_map", "button")


# ----------------------------------------------------------------------------
# B. flight HUD
# ----------------------------------------------------------------------------

def flight_hud():
    W, H = 160, 40
    img = new(W, H)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, W - 1, H - 1), radius=4, fill=rgba(BAKELITE), outline=rgba(BLACK))
    d.rounded_rectangle((1, 1, W - 2, H - 2), radius=3, outline=rgba(CHROME_D))
    # cream title strip y=0..9 (inside the outline) with red / teal end caps
    d.rounded_rectangle((1, 1, W - 2, 9), radius=3, fill=rgba(CREAM))
    d.line((2, 9, W - 3, 9), fill=rgba(CREAM_D))
    d.line((2, 10, W - 3, 10), fill=rgba(CHROME_D))
    d.rectangle((2, 2, 7, 8), fill=rgba(RED))
    d.line((7, 2, 7, 8), fill=rgba(RED_D))
    d.rectangle((W - 8, 2, W - 3, 8), fill=rgba(TEAL))
    d.line((W - 8, 2, W - 8, 8), fill=rgba(TEAL_D))
    px(img, [(2, 2), (W - 3, 2)], CREAM)
    # CRT body
    crt_glass(img, d, (3, 12, W - 4, H - 4))
    # fuel track: recessed, bar fills x=6..153, y=30..35
    d.rectangle((5, 29, 154, 36), fill=rgba((16, 18, 20)), outline=rgba(CHROME_D))
    d.line((6, 29, 153, 29), fill=rgba(BLACK))
    d.line((5, 30, 5, 35), fill=rgba(BLACK))
    for i in range(1, 10):
        x = 6 + int(i * 148 / 10)
        px(img, [(x, 35)], (56, 60, 64))
    # corner rivets
    for (x, y) in ((3, 13), (W - 4, 13), (3, 37), (W - 4, 37)):
        px(img, [(x, y)], CHROME)
    return img


def flight_hud_bar():
    img = new(148, 6)
    for x in range(148):
        t = x / 147.0
        base = tuple(int(ORANGE[i] + (ORANGE_L[i] - ORANGE[i]) * t) for i in range(3))
        for y in range(6):
            if y == 0:
                c = tuple(min(255, v + 50) for v in base)
            elif y == 1:
                c = tuple(min(255, v + 22) for v in base)
            elif y == 5:
                c = tuple(int(v * 0.62) for v in base)
            elif y == 4:
                c = tuple(int(v * 0.84) for v in base)
            else:
                c = base
            img.putpixel((x, y), rgba(c))
    # ticks every 10%
    for i in range(1, 10):
        x = int(i * 148 / 10)
        px(img, [(x, 4), (x, 5)], (150, 70, 20))
    return img


# ----------------------------------------------------------------------------
# C. rocket plume
# ----------------------------------------------------------------------------

def rocket_plume():
    W, H = 16, 64
    img = new(W, H)
    rnd = random.Random(99)
    cx = 8.0
    for y in range(H):
        t = y / (H - 1)
        hw = 7.0 * (1 - t) ** 0.7 + 1.0 + rnd.uniform(-0.9, 0.9) * (0.25 + t)
        hw = max(0.8, hw)
        for x in range(W):
            dx = abs(x + 0.5 - cx)
            if dx > hw:
                continue
            e = dx / hw                     # 0 core .. 1 edge
            heat = (1 - t) ** 0.9 * (1 - e * e * 0.9)
            if heat > 0.66:
                c = (255, 252, 236)
            elif heat > 0.46:
                c = (255, 234, 110)
            elif heat > 0.30:
                c = (255, 168, 40)
            elif heat > 0.16:
                c = (240, 88, 30)
            else:
                c = (196, 36, 30)
            a = 255 if t < 0.35 else int(255 * (1 - (t - 0.35) / 0.65) ** 0.8)
            if e > 0.75:
                a = int(a * 0.72)
            if rnd.random() < 0.10 * (t + e):
                a = int(a * 0.55)
            img.putpixel((x, y), (c[0], c[1], c[2], max(0, min(255, a))))
    # shock diamonds in the core
    for y in (5, 12, 19):
        px(img, [(7, y), (8, y), (7, y + 1), (8, y + 1), (6, y + 1), (9, y + 1)], (255, 255, 255))
        px(img, [(7, y + 3), (8, y + 3)], (255, 214, 90))
    return img


# ----------------------------------------------------------------------------
# D. first-person cockpit overlay
# ----------------------------------------------------------------------------

def dial(d, img, cx, cy, r, needle_deg, face=(236, 232, 220), accent=RED):
    d.ellipse((cx - r - 1, cy - r - 1, cx + r + 1, cy + r + 1), fill=rgba(CHROME), outline=rgba(BLACK))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=rgba(face), outline=rgba(STEEL_D))
    for a in range(-220, 41, 26):
        ra = math.radians(a)
        d.line((cx + (r - 3) * math.cos(ra), cy + (r - 3) * math.sin(ra),
                cx + (r - 1) * math.cos(ra), cy + (r - 1) * math.sin(ra)), fill=rgba(BLACK))
    # red zone at the end of the scale
    for a in range(10, 41, 4):
        ra = math.radians(a)
        px(img, [(int(round(cx + (r - 2) * math.cos(ra))), int(round(cy + (r - 2) * math.sin(ra))))], accent)
    ra = math.radians(needle_deg)
    d.line((cx, cy, cx + (r - 2) * math.cos(ra), cy + (r - 2) * math.sin(ra)), fill=rgba(RED_D))
    d.ellipse((cx - 1, cy - 1, cx + 1, cy + 1), fill=rgba(BLACK))
    px(img, [(cx - r + 2, cy - r + 3)], CHROME_L)   # glass glint


def toggle(d, x, y, on):
    d.rectangle((x, y, x + 4, y + 8), fill=rgba(STEEL_D), outline=rgba(BLACK))
    d.ellipse((x, y + 2, x + 4, y + 6), fill=rgba(CHROME_D))
    if on:
        d.rectangle((x + 1, y - 2, x + 3, y + 3), fill=rgba(CHROME), outline=rgba(CHROME_D))
        d.point((x + 2, y - 2), fill=rgba(CHROME_L))
    else:
        d.rectangle((x + 1, y + 5, x + 3, y + 10), fill=rgba(CHROME), outline=rgba(CHROME_D))
        d.point((x + 2, y + 10), fill=rgba(CHROME_D))


def cockpit():
    """480x270 overlay drawn at 240x135 and scaled x2 (chunky pixels); glass of the porthole is transparent."""
    W, H = 240, 135
    img = new(W, H)
    d = ImageDraw.Draw(img)
    rnd = random.Random(4)
    # bulkhead: cream enamel with faint grain
    d.rectangle((0, 0, W - 1, H - 1), fill=rgba(CREAM))
    for y in range(H):
        for x in range(W):
            if rnd.random() < 0.10:
                px(img, [(x, y)], (232, 224, 198))
    # structural ribs: vertical chrome stiffeners at the sides
    for x in (34, 205):
        d.rectangle((x, 30, x + 2, 100), fill=rgba(CHROME))
        d.line((x, 30, x, 100), fill=rgba(CHROME_L))
        d.line((x + 2, 30, x + 2, 100), fill=rgba(CHROME_D))
    # horizontal panel seams on the bulkhead
    for y in (64,):
        d.line((37, y, 204, y), fill=rgba(CREAM_D))
        d.line((37, y + 1, 204, y + 1), fill=rgba((248, 242, 224)))
    # top band (HUD zone, 60 screen px): dark bakelite with a chrome lip and a recessed vent grille
    d.rectangle((0, 0, W - 1, 29), fill=rgba(BAKELITE))
    d.line((0, 29, W - 1, 29), fill=rgba(CHROME_L))
    d.line((0, 30, W - 1, 30), fill=rgba(CHROME_D))
    d.line((0, 28, W - 1, 28), fill=rgba((28, 24, 24)))
    for x in range(6, W, 12):
        px(img, [(x, 3)], BAKELITE_L)
        px(img, [(x, 25)], BAKELITE_L)
    for y in range(8, 22, 3):
        d.line((100, y, 140, y), fill=rgba((28, 24, 24)))
        d.line((100, y + 1, 140, y + 1), fill=rgba(BAKELITE_L))
    # padded upholstery: red at left, teal at right, tufted
    for (x0, x1, base, dark, light) in ((2, 30, RED, RED_D, RED_L), (209, 237, TEAL, TEAL_D, TEAL_L)):
        d.rounded_rectangle((x0, 34, x1, 96), radius=4, fill=rgba(base), outline=rgba(BLACK))
        d.rounded_rectangle((x0 + 1, 35, x1 - 1, 95), radius=3, outline=rgba(light))
        mid = shade(base, -14)
        # quilted diamonds: soft seams, a dark button with a highlight
        for (bx, by) in [(x0 + 7 + i * 14, 44 + j * 16) for i in range(2) for j in range(4)]:
            if bx < x1 - 4:
                for k in range(1, 7):
                    px(img, [(x, y) for (x, y) in ((bx - k, by - 7 + k), (bx + k, by - 7 + k), (bx - k, by + 7 - k),
                                                   (bx + k, by + 7 - k)) if 37 <= y <= 93 and x0 + 2 < x < x1 - 2], mid)
                px(img, [(bx, by), (bx + 1, by), (bx, by + 1)], dark)
                px(img, [(bx - 1, by - 1)], light)
                px(img, [(bx, by - 1), (bx - 1, by)], shade(dark, 30))
    # rivets on the bulkhead around the porthole
    for (x, y) in [(42, 36), (42, 62), (42, 96), (197, 36), (197, 62), (197, 96), (70, 34), (170, 34),
                   (54, 96), (186, 96)]:
        rivet(img, x, y)

    # porthole: rounded trapezoid (narrower at the top), chrome bezel 5px, transparent glass
    cx, top, bot = 120.0, 33.0, 102.0
    cy = (top + bot) / 2
    b = (bot - top) / 2

    def half_width(y):
        t = (y - top) / (bot - top)
        return 62 + 12 * t          # 62 at the top .. 74 at the bottom

    def inside(x, y, shrink):
        a = half_width(y) - shrink
        bb = b - shrink
        if a <= 0 or bb <= 0:
            return False
        return (abs(x - cx) / a) ** 3.2 + (abs(y - cy) / bb) ** 3.2 <= 1.0

    for y in range(H):
        for x in range(W):
            xc, yc = x + 0.5, y + 0.5
            if inside(xc, yc, 5):
                img.putpixel((x, y), (0, 0, 0, 0))
            elif inside(xc, yc, 4):
                img.putpixel((x, y), rgba((12, 10, 14)))        # glass seal (dark)
            elif inside(xc, yc, 3):
                img.putpixel((x, y), rgba(CHROME_D))
            elif inside(xc, yc, 1):
                img.putpixel((x, y), rgba(CHROME))
            elif inside(xc, yc, 0):
                img.putpixel((x, y), rgba(CHROME_L if (xc < cx) or (yc < cy) else CHROME_D))
            elif inside(xc, yc, -1):
                img.putpixel((x, y), rgba(BLACK))
    # bezel bolts around the porthole
    for i in range(16):
        a = math.radians(i * 22.5 + 11)
        # find the bezel point along this angle
        for r in range(90, 0, -1):
            xx, yy = cx + r * math.cos(a), cy + r * math.sin(a) * 0.62
            if inside(xx, yy, 1.5):
                px(img, [(int(xx), int(yy))], CHROME_L)
                px(img, [(int(xx) + 1, int(yy) + 1)], STEEL_D)
                break
    # faint glass glint streak (alpha ~40) in the upper-left of the glass
    for i in range(22):
        x, y = 70 + i, 62 - i
        if inside(x + 0.5, y + 0.5, 7):
            img.putpixel((x, y), (255, 255, 255, 40))
            if inside(x + 1.5, y + 0.5, 7):
                img.putpixel((x + 1, y), (255, 255, 255, 40))
    for i in range(10):
        x, y = 92 + i, 50 - i
        if inside(x + 0.5, y + 0.5, 7):
            img.putpixel((x, y), (255, 255, 255, 34))

    # dashboard (y=100..134): dark bakelite deck with a chrome rail, cream instrument faces
    d.rectangle((0, 100, W - 1, H - 1), fill=rgba(BAKELITE))
    d.rectangle((0, 100, W - 1, 102), fill=rgba(CHROME))
    d.line((0, 100, W - 1, 100), fill=rgba(CHROME_L))
    d.line((0, 103, W - 1, 103), fill=rgba(BLACK))
    for y in range(104, H, 2):
        d.line((0, y, W - 1, y), fill=rgba((46, 42, 42)))
    # left instrument cluster: three dials on a cream plate
    d.rounded_rectangle((6, 106, 92, 132), radius=3, fill=rgba(CREAM), outline=rgba(BLACK))
    d.line((7, 107, 91, 107), fill=rgba(CHROME_L))
    dial(d, img, 20, 119, 9, -150)
    dial(d, img, 49, 119, 9, -60)
    dial(d, img, 78, 119, 9, -110)
    # label strips under the dials
    for x in (14, 43, 72):
        d.rectangle((x, 129, x + 12, 130), fill=rgba(NAVY))
    # centre: switch bank + indicator lamps
    d.rounded_rectangle((98, 106, 150, 132), radius=3, fill=rgba((222, 212, 186)), outline=rgba(BLACK))
    d.line((99, 107, 149, 107), fill=rgba(CHROME_L))
    for i, on in enumerate((True, False, True, True, False, True)):
        toggle(d, 103 + i * 8, 112, on)
    for i, c in enumerate((RED, AMBER_LAMP, (120, 230, 120), TEAL, AMBER_LAMP, (120, 230, 120))):
        lamp(d, 103 + i * 8, 125, c, size=3)
    # right: small green CRT with a phosphor trace, plus a red guarded switch
    d.rounded_rectangle((156, 105, 200, 133), radius=3, fill=rgba(BAKELITE), outline=rgba(BLACK))
    d.rounded_rectangle((157, 106, 199, 132), radius=2, outline=rgba(BAKELITE_L))
    crt_glass(img, d, (159, 108, 197, 130))
    for x in range(161, 196):
        y = 119 + int(round(4 * math.sin((x - 161) / 3.2)))
        px(img, [(x, y)], (92, 255, 138))
        px(img, [(x, y + 1)], (46, 138, 74))
    for x in range(161, 196, 4):
        px(img, [(x, 119)], (30, 90, 50))
    # red guarded switch and a brass plate
    d.rectangle((208, 108, 232, 130), fill=rgba(CREAM), outline=rgba(BLACK))
    d.line((209, 109, 231, 109), fill=rgba(CHROME_L))
    d.rectangle((214, 113, 226, 123), fill=rgba(RED), outline=rgba(RED_D))
    d.rectangle((216, 115, 224, 117), fill=rgba(RED_L))
    d.line((214, 124, 226, 124), fill=rgba(BLACK))
    d.rectangle((211, 126, 229, 128), fill=rgba(NAVY))
    # chrome rivets along the deck edge
    for x in range(4, W, 16):
        rivet(img, x, 133)
    return img.resize((W * 2, H * 2), Image.NEAREST)


def generate():
    generate_system_map()
    save(flight_hud(), "gui", "flight_hud")
    save(flight_hud_bar(), "gui", "flight_hud_bar")
    save(rocket_plume(), "entity", "rocket_plume")
    save(cockpit(), "gui", "cockpit")


if __name__ == "__main__":
    generate()
