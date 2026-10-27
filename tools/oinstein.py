"""Dr. Oinstein - the mad scientist of Venus and his Institute (the planet's antagonist storyline).

Generates the assets and data of Oinstein's blocks (laser barrier and emitter, riveted / hazard steel, Tesla coil,
brain jar, three propaganda posters), his insignia banner pattern, the laser damage type, loot tables, lore books and
signs, and - with the structure builder of ruins.py - his structures on Venus:
  * oinstein_capture_camp / oinstein_field_lab / oinstein_relay_pylon / oinstein_checkpoint: the outposts (one
    structure set "oinstein_outposts", spread with retrocosmos:exclusive_spread away from tribal camps, ruins and the
    Institute),
  * oinstein_complex: the Oinstein Institute, exactly one per world (concentric_rings, count 1), its laboratory
    entrance sealed by an unbreakable laser barrier.

Called from ruins.generate(); EN / RU are merged into ruins.EN / RU.

Mobs of the other Venus agents (hominid_novus, hominus_sapiens, atomic_sentry, atomic_automaton) are written into the
templates as entities (unknown ids are skipped by the template loader); structure spawn_overrides with them are only
written once those entity ids are registered in Java (or with OINSTEIN_SPAWNS=1 / 0).
"""
import math
import os
import random

from PIL import Image

from gen_resources import ASSETS, DATA, MOD, new, shaped, tag, write_json
from furniture import add_to_tag
from furniture_art import Model, T, block_item, state_simple, tex, tex_anim
import station_furniture_art as sfa
import ruins as R_
from ruins import AIR, DIRS, FULL, HORIZ, OPP, Ruin, S_AIR, barrel_state, chest_state, st, write_template
from station import Compound, List, Str, Int, Byte, TAG_COMPOUND, TAG_DOUBLE, TAG_INT
from venus import P, put, tonal

HERE = os.path.dirname(os.path.abspath(__file__))
JAVA = os.path.join(HERE, "..", "src", "main", "java", "com", "replecant", "retrocosmos")

# =====================================================================================================================
# Palette: gunmetal, chrome, concrete, hazard yellow, laser red, specimen green
# =====================================================================================================================
STEEL = [(40, 44, 50), (56, 61, 68), (74, 80, 88), (94, 100, 108), (122, 128, 136)]
CHROME = [(110, 116, 124), (150, 156, 164), (190, 196, 204), (232, 236, 240)]
HAZ_Y = (226, 178, 36)
HAZ_YD = (176, 132, 22)
HAZ_K = (34, 32, 30)
LASER = [(120, 10, 8), (200, 24, 16), (255, 64, 40), (255, 150, 120), (255, 230, 220)]
COPPER = [(110, 56, 36), (160, 86, 52), (204, 120, 74), (236, 168, 120)]
GOO = [(40, 120, 40), (80, 190, 60), (150, 240, 110)]
BRAIN = [(150, 70, 90), (204, 110, 130), (240, 160, 176)]
BONE = [(176, 168, 140), (216, 208, 178), (244, 238, 214)]
NAVY = (26, 30, 52)
RED = (196, 32, 36)
RED_D = (130, 20, 24)
CYAN = (90, 220, 230)


def Tm(name):
    return f"{MOD}:{name}"


# =====================================================================================================================
# The insignia: a stylised atom over an ape skull
# =====================================================================================================================
SKULL = ["...BBBBB...",
         "..BBBBBBB..",
         ".BBBBBBBBB.",
         "BBBBBBBBBBB",
         "BDDBBBBBDDB",
         "BDDDBBBDDDB",
         ".BDBBDBBDB.",
         "..BBDBDBB..",
         "..BBBBBBB..",
         "..BDBDBDB..",
         "...BBBBB..."]


def draw_skull(img, ox, oy, bone=BONE, dark=None, outline=None):
    for y, row in enumerate(SKULL):
        for x, ch in enumerate(row):
            if ch == "B":
                c = bone[2] if y < 3 else bone[1] if y < 8 else bone[0]
                if x in (0, 10) or (y > 6 and x in (2, 8)):
                    c = bone[0]
                put(img, ox + x, oy + y, c)
            elif ch == "D" and dark:
                put(img, ox + x, oy + y, dark)
    if outline:
        pts = {(ox + x, oy + y) for y, row in enumerate(SKULL) for x, ch in enumerate(row) if ch != "."}
        for (x, y) in list(pts):
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + dx, y + dy)
                if q not in pts and 0 <= q[0] < img.width and 0 <= q[1] < img.height and img.getpixel(q)[3] < 255:
                    put(img, q[0], q[1], outline)


def draw_atom(img, cx, cy, rx, ry, ring, nucleus, steps=None):
    """Three thin orbits (0, +60, -60 degrees) around a nucleus; one pixel per step along each orbit."""
    steps = steps or int(8 * rx)
    pts = set()
    for k in range(3):
        a = k * math.pi / 3
        for i in range(steps):
            t = 2 * math.pi * i / steps
            x, y = rx * math.cos(t), ry * math.sin(t)
            pts.add((int(math.floor(cx + x * math.cos(a) - y * math.sin(a))),
                     int(math.floor(cy + x * math.sin(a) + y * math.cos(a)))))
    for (x, y) in pts:
        put(img, x, y, ring)
    r = max(1, int(rx / 6))
    for dx in range(-r, r):
        for dy in range(-r, r):
            put(img, int(cx) + dx, int(cy) + dy, nucleus)


# =====================================================================================================================
# Block textures
# =====================================================================================================================

def riveted(seed, base=STEEL, plates=((0, 0, 16, 8), (0, 8, 8, 16), (8, 8, 16, 16))):
    img = tonal(seed, base[1:4], [25, 50, 25], octaves=((4, 0.5), (8, 0.3)), jitter=0.3)
    for (x0, y0, x1, y1) in plates:
        for x in range(x0, x1):
            put(img, x, y0, base[4])
            put(img, x, y1 - 1, base[0])
        for y in range(y0, y1):
            put(img, x0, y, base[3])
            put(img, x1 - 1, y, base[0])
        for (rx, ry) in ((x0 + 2, y0 + 2), (x1 - 3, y0 + 2), (x0 + 2, y1 - 3), (x1 - 3, y1 - 3)):
            put(img, rx, ry, CHROME[2])
            put(img, rx + 1, ry + 1, base[0])
    return img


def tex_hazard():
    img = riveted(902)
    for y in range(1, 15):
        for x in range(1, 15):
            put(img, x, y, HAZ_Y if ((x + y) // 4) % 2 == 0 else HAZ_K)
            if ((x + y) // 4) % 2 == 0 and (x + y) % 4 == 3:
                put(img, x, y, HAZ_YD)
    for (rx, ry) in ((1, 1), (14, 1), (1, 14), (14, 14)):
        put(img, rx, ry, CHROME[2])
    return img


def laser_frames(n=8):
    frames = []
    rows = (2, 6, 10, 13)
    for f in range(n):
        img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
        rnd = random.Random(1000 + f)
        pulse = 0.5 + 0.5 * math.sin(2 * math.pi * f / n)
        for y in range(16):
            for x in range(16):
                haze = 40 + int(25 * pulse) + int(12 * math.sin((x + f * 2) * 0.9 + y * 0.6))
                img.putpixel((x, y), (*LASER[1], max(20, haze)))
        for i, y in enumerate(rows):
            for x in range(16):
                wob = math.sin((x + f * 2 + i * 3) * 0.8)
                core = LASER[4] if wob > 0.2 else LASER[3]
                img.putpixel((x, y), (*core, 235))
                for dy, a in ((-1, 150), (1, 150)):
                    if 0 <= y + dy < 16:
                        img.putpixel((x, y + dy), (*LASER[2], int(a * (0.75 + 0.25 * pulse))))
        for _ in range(3):   # sparks running along the beams
            y = rnd.choice(rows)
            x = (rnd.randrange(16) + f * 3) % 16
            img.putpixel((x, y), (255, 255, 255, 255))
        frames.append(img)
    return frames


def tex_emitter_side():
    img = riveted(911, plates=((0, 0, 16, 16),))
    for y in range(16):
        put(img, 3, y, STEEL[0])
        put(img, 12, y, STEEL[0])
    for y in range(5, 11):
        for x in range(5, 11):
            put(img, x, y, STEEL[0])
    for y in range(6, 10):
        for x in range(6, 10):
            put(img, x, y, LASER[3] if (x, y) in ((7, 7), (8, 7)) else LASER[2] if 6 < x < 9 and 6 < y < 9 else LASER[1])
    for x in range(4, 12):
        put(img, x, 0, HAZ_Y if x % 2 else HAZ_K)
        put(img, x, 15, HAZ_Y if x % 2 else HAZ_K)
    return img


def tex_emitter_lens():
    img = new()
    for y in range(16):
        for x in range(16):
            d = math.hypot(x - 7.5, y - 7.5)
            if d < 7.5:
                put(img, x, y, LASER[4] if d < 2 else LASER[3] if d < 4 else LASER[2] if d < 6 else LASER[1])
    return img


def tex_emitter_top():
    img = riveted(912, plates=((0, 0, 16, 16),))
    for y in range(4, 12):
        for x in range(4, 12):
            put(img, x, y, HAZ_Y if ((x + y) // 2) % 2 else HAZ_K)
    return img


def tex_coil():
    img = new()
    for y in range(16):
        for x in range(16):
            c = COPPER[(y % 2) + (1 if x < 6 else 0) + (1 if x < 3 else 0)]
            if x > 12:
                c = COPPER[0]
            put(img, x, y, c)
    return img


def tex_chrome():
    img = tonal(921, CHROME[0:4], [15, 35, 35, 15], jitter=0.2,
                field=lambda x, y: -0.06 * (x + y))
    return img


def tex_jar_glass():
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for y in range(16):
        for x in range(16):
            a = 50
            if x in (0, 15) or y in (0, 15):
                a = 140
            if x in (2, 3) and 2 < y < 13:
                a = 170
            img.putpixel((x, y), (210, 240, 220, a))
    return img


def tex_goo():
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    rnd = random.Random(931)
    for y in range(16):
        for x in range(16):
            c = GOO[1] if (x + y) % 5 else GOO[2]
            img.putpixel((x, y), (*c, 150))
    for _ in range(6):
        img.putpixel((rnd.randrange(16), rnd.randrange(16)), (*GOO[2], 230))
    return img


def tex_brain():
    img = tonal(941, BRAIN, [30, 45, 25], octaves=((8, 0.6), (4, 0.3)), jitter=0.2)
    for x in range(16):
        put(img, x, 7, BRAIN[0])
    for y in range(16):
        put(img, 8, y, BRAIN[0])
    return img


def tex_concrete_label():
    return riveted(951)


def poster_insignia():
    img = new(16, 32)
    sfa.bands(img, [(0, 31, NAVY)])
    for y in range(32):
        for x in range(16):
            if (x + y) % 7 == 0:
                put(img, x, y, (34, 40, 66))
    draw_atom(img, 8, 8, 7.0, 1.6, CYAN, RED)
    draw_skull(img, 3, 15, dark=NAVY)
    for y in range(28, 31):
        for x in range(1, 15):
            put(img, x, y, HAZ_Y if ((x + y) // 2) % 2 == 0 else HAZ_K)
    sfa.poster_frame(img)
    return img


def poster_better_ape():
    img = new(16, 32)
    sfa.bands(img, [(0, 15, HAZ_Y), (16, 31, (236, 210, 140))])
    # an ape head with a glass brain dome
    head = ["....GGGGGG......",
            "...GgggggggG....",
            "...GgBBBBggG....",
            "....GBBBBBG.....",
            "...FFFFFFFFF....",
            "..FFfffffffFF...",
            "..FfKfffKffF....",
            "..FFfffffffF....",
            "...FMMMMMMF.....",
            "...FMWMWMMF.....",
            "....FFFFFF......"]
    pal = {"G": CHROME[2], "g": (190, 240, 210), "B": BRAIN[1], "F": (92, 60, 40), "f": (150, 110, 80),
           "K": (20, 20, 20), "M": (200, 150, 120), "W": (250, 250, 240)}
    for y, row in enumerate(head):
        for x, ch in enumerate(row):
            if ch in pal:
                put(img, x + 2, y + 2, pal[ch])
    sfa.text(img, None, 16, "NEW", RED)
    sfa.text(img, None, 23, "APE!", RED_D)
    sfa.poster_frame(img)
    return img


def poster_restricted():
    img = new(16, 32)
    sfa.bands(img, [(0, 31, (232, 228, 214))])
    for y in range(32):
        for x in range(16):
            if y < 3 or y > 28:
                put(img, x, y, HAZ_Y if ((x + y) // 2) % 2 == 0 else HAZ_K)
    draw_skull(img, 3, 5, dark=RED_D)
    # lightning bolts either side
    for (x, y) in ((1, 6), (2, 7), (1, 8), (2, 9), (13, 6), (14, 7), (13, 8), (14, 9)):
        put(img, x, y, RED)
    sfa.text(img, None, 18, "STOP", RED, condensed=True)
    sfa.text(img, None, 24, "OUT", HAZ_K)
    sfa.poster_frame(img)
    return img


POSTERS = {"oinstein_poster_insignia": poster_insignia, "oinstein_poster_better_ape": poster_better_ape,
           "oinstein_poster_restricted": poster_restricted}


def banner_pattern_images():
    """White masks for the banner (front 20x40 at 1,1) and shield (front 12x22 at 1,1) layouts."""
    W = (255, 255, 255)
    ban = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    big = Image.new("RGBA", (20, 40), (0, 0, 0, 0))
    draw_atom(big, 10, 11, 9.0, 2.6, W, W)
    sk = Image.new("RGBA", (11, 11), (0, 0, 0, 0))
    draw_skull(sk, 0, 0, bone=[W, W, W])
    sk = sk.resize((16, 16), Image.NEAREST)
    big.alpha_composite(sk, (2, 20))
    for (x, y) in [(x, y) for y in range(40) for x in range(20)]:
        if big.getpixel((x, y))[3]:
            ban.putpixel((1 + x, 1 + y), (255, 255, 255, 255))
    shield = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    small = Image.new("RGBA", (12, 22), (0, 0, 0, 0))
    draw_atom(small, 6, 5, 5.5, 1.4, W, W)
    draw_skull(small, 0, 11, bone=[W, W, W])
    for y in range(22):
        for x in range(12):
            if small.getpixel((x, y))[3]:
                shield.putpixel((1 + x, 1 + y), (255, 255, 255, 255))
    return ban, shield


# =====================================================================================================================
# Models, blockstates, items, data
# =====================================================================================================================
BARRIER = "laser_barrier"
EMITTER = "laser_emitter"
RSTEEL = "oinstein_riveted_steel"
HSTEEL = "oinstein_hazard_steel"
TESLA = "tesla_coil"
JAR = "brain_jar"
BLOCKS = [BARRIER, EMITTER, RSTEEL, HSTEEL, TESLA, JAR] + list(POSTERS)


def write_block_textures():
    tex_anim(BARRIER, laser_frames(), 2, interpolate=True)
    tex("laser_emitter_side", tex_emitter_side())
    tex("laser_emitter_top", tex_emitter_top())
    tex("laser_emitter_lens", tex_emitter_lens())
    tex(RSTEEL, riveted(901, plates=((0, 0, 16, 16),)))
    tex(HSTEEL, tex_hazard())
    tex("tesla_coil_winding", tex_coil())
    tex("oinstein_chrome", tex_chrome())
    tex("brain_jar_glass", tex_jar_glass())
    tex("brain_jar_goo", tex_goo())
    tex("brain_jar_brain", tex_brain())
    for name, fn in POSTERS.items():
        art = fn()
        tex(f"{name}_upper", art.crop((0, 0, 16, 16)))
        tex(f"{name}_lower", art.crop((0, 16, 16, 32)))
    ban, shield = banner_pattern_images()
    for kind, img in (("banner", ban), ("shield", shield)):
        path = os.path.join(ASSETS, "textures", "entity", kind, "oinstein.png")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        img.save(path)


def emissive(e):
    e["light_emission"] = 15
    e["shade"] = False
    return e


def write_models():
    # the beam: one translucent emissive sheet through the middle of the block, along x (turned for axis=z)
    m = Model({"beam": BARRIER}, BARRIER, ao=False, render_type="minecraft:translucent")
    emissive(m.box((0, 0, 8), (16, 16, 8), "beam", faces=("north", "south")))
    m.write(BARRIER)
    m = Model({}, BARRIER, render_type="minecraft:translucent")
    m.write(f"{BARRIER}_off")
    variants = {}
    for axis, rot in (("x", 0), ("z", 90)):
        for powered in ("true", "false"):
            v = {"model": T(BARRIER if powered == "true" else f"{BARRIER}_off")}
            if rot:
                v["y"] = rot
            variants[f"axis={axis},powered={powered}"] = v
    write_json(os.path.join(ASSETS, "blockstates", BARRIER + ".json"), {"variants": variants})
    write_json(os.path.join(ASSETS, "items", BARRIER + ".json"),
               {"model": {"type": "minecraft:model", "model": T(BARRIER)}})
    # emitter post with glowing lenses on all four sides
    for lit in (True, False):
        m = Model({"side": "laser_emitter_side", "top": "laser_emitter_top", "lens": "laser_emitter_lens"},
                  "laser_emitter_side")
        m.box((4, 0, 4), (12, 16, 12), "side", face_tex={"up": "top", "down": "top"},
              face_uv={f: [4, 0, 12, 16] for f in HORIZ} | {"up": [4, 4, 12, 12], "down": [4, 4, 12, 12]})
        for f, frm, to in (("north", (6, 6, 3.9), (10, 10, 4)), ("south", (6, 6, 12), (10, 10, 12.1)),
                           ("west", (3.9, 6, 6), (4, 10, 10)), ("east", (12, 6, 6), (12.1, 10, 10))):
            e = m.box(frm, to, "lens", faces=(f,), face_uv={f: [0, 0, 16, 16]})
            if lit:
                emissive(e)
        m.write(EMITTER + ("" if lit else "_off"))
    write_json(os.path.join(ASSETS, "blockstates", EMITTER + ".json"), {"variants": {
        "powered=true": {"model": T(EMITTER)}, "powered=false": {"model": T(f"{EMITTER}_off")}}})
    block_item(EMITTER)
    for name in (RSTEEL, HSTEEL):
        write_json(os.path.join(ASSETS, "models", "block", name + ".json"),
                   {"parent": "minecraft:block/cube_all", "textures": {"all": T(name)}})
        state_simple(name)
        block_item(name)
    # Tesla coil: steel base, copper winding, chrome toroid
    m = Model({"steel": RSTEEL, "coil": "tesla_coil_winding", "chrome": "oinstein_chrome"}, "tesla_coil_winding")
    m.box((4, 0, 4), (12, 4, 12), "steel")
    m.box((6, 4, 6), (10, 12, 10), "coil")
    m.octagon((3, 12, 3), (13, 15, 13), "chrome")
    m.box((7.5, 15, 7.5), (8.5, 16, 8.5), "chrome")
    m.write(TESLA)
    state_simple(TESLA)
    block_item(TESLA)
    # brain in a jar
    m = Model({"glass": "brain_jar_glass", "goo": "brain_jar_goo", "brain": "brain_jar_brain", "chrome": "oinstein_chrome",
               "steel": RSTEEL}, "brain_jar_glass", render_type="minecraft:translucent")
    m.box((5, 0, 5), (11, 1, 11), "steel")
    m.box((6, 2, 6), (10, 7, 10), "brain")
    emissive(m.box((5.2, 1, 5.2), (10.8, 10, 10.8), "goo"))
    m.box((5, 1, 5), (11, 12, 11), "glass")
    m.box((4.5, 12, 4.5), (11.5, 14, 11.5), "chrome")
    m.write(JAR)
    state_simple(JAR)
    block_item(JAR)
    for name in POSTERS:
        sfa.poster_models(name)
        sfa.state_facing_half(name)
        sfa.poster_item_model(name)


# =====================================================================================================================
# Security clearance: three keycards and the reader that switches a barrier grid off
# =====================================================================================================================
READER = "keycard_reader"
# level: (card name, colour, dark colour, where the card is kept)
CLEARANCE = {"a": ("keycard_alpha", (204, 40, 40), (122, 18, 22)),
             "b": ("keycard_beta", (46, 96, 210), (22, 46, 120)),
             "c": ("keycard_gamma", (52, 164, 70), (22, 92, 34))}
READER_STATUS = ("locked", "denied", "granted")
LETTERS = {"a": [".#.", "#.#", "###", "#.#", "#.#"], "b": ["##.", "#.#", "##.", "#.#", "##."],
           "c": [".##", "#..", "#..", "#..", ".##"]}
MINI_ATOM = [".###.", "#.#.#", "##o##", "#.#.#", ".###."]
CARD_HOLES = {"a": "#.##.#.#.#", "b": "##.#.##..#", "c": "#..##.#.##"}
CREAM = [(178, 166, 132), (222, 212, 180), (242, 236, 212)]


def keycard_sprite(level):
    """A punched security card: cream stock with a clipped corner, the clearance band with the Institute atom and
    the level letter, a gold contact and a row of punched holes (a different code per level)."""
    _name, col, dark = CLEARANCE[level]
    img = new()
    x0, x1, y0, y1 = 1, 14, 3, 12
    band = y0 + 5
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            k = (x - x0) + (y - y0)
            if k < 2:
                continue                                    # the clipped corner
            edge = x in (x0, x1) or y in (y0, y1) or k == 2
            if y <= band:
                c = dark if edge else (col if (x + y) % 5 else tuple(min(255, v + 18) for v in col))
            else:
                c = CREAM[0] if edge else CREAM[2] if y == band + 1 else CREAM[1]
            put(img, x, y, c)
    for gy, row in enumerate(MINI_ATOM):
        for gx, ch in enumerate(row):
            if ch == "#":
                put(img, 3 + gx, y0 + 1 + gy, CREAM[2])
            elif ch == "o":
                put(img, 3 + gx, y0 + 1 + gy, (255, 226, 110))
    for gy, row in enumerate(LETTERS[level]):
        for gx, ch in enumerate(row):
            if ch == "#":
                put(img, 10 + gx, y0 + 1 + gy, (250, 250, 244))
    for (x, y) in ((2, 10), (3, 10), (2, 11), (3, 11)):
        put(img, x, y, (232, 186, 60) if (x + y) % 2 else (196, 150, 40))
    for i, ch in enumerate(CARD_HOLES[level]):
        if ch == "#":
            put(img, 5 + i // 2 * 2 + (i % 2), 10 + (i % 2), (58, 50, 42))
    return img


def tex_reader_front(level):
    """The reader face (uv 3..13 x 1..15): steel housing, the clearance band and letter, the lamp socket, the card
    slot in its chrome bezel, a keypad and a hazard strip."""
    _name, col, dark = CLEARANCE[level]
    img = riveted(961, base=[(30, 33, 38), (44, 48, 54), (58, 63, 70), (74, 80, 88), (96, 102, 110)],
                  plates=((3, 1, 13, 15),))
    for y in range(2, 7):
        for x in range(4, 12):
            put(img, x, y, dark if y in (2, 6) else col)
    for gy, row in enumerate(LETTERS[level]):
        for gx, ch in enumerate(row):
            if ch == "#":
                put(img, 9 + gx, 2 + gy, (250, 250, 244))
    for y in range(3, 6):                                  # lamp socket (the lamp element sits on it)
        for x in range(4, 8):
            put(img, x, y, (20, 20, 22))
    for x in range(5, 11):
        put(img, x, 7, CHROME[2])
        put(img, x, 8, (8, 8, 10))
        put(img, x, 9, CHROME[1])
    for (x, y) in ((5, 11), (7, 11), (9, 11), (5, 12), (7, 12), (9, 12)):
        put(img, x, y, CHROME[3])
        put(img, x + 1, y, STEEL[0])
    for x in range(4, 12):
        put(img, x, 14, HAZ_Y if x % 2 else HAZ_K)
    return img


def tex_reader_lamp(status):
    c = {"locked": [(150, 92, 10), (220, 150, 30), (255, 210, 90)], "denied": [(160, 10, 8), (255, 40, 30), (255, 170, 150)],
         "granted": [(20, 130, 30), (70, 240, 90), (200, 255, 200)]}[status]
    img = new()
    for y in range(16):
        for x in range(16):
            d = math.hypot(x - 6.5, y - 6.5)
            put(img, x, y, c[2] if d < 3 else c[1] if d < 8 else c[0])
    return img


def write_keycard_assets():
    from gen_resources import save
    from furniture_art import flat_item
    for level, (name, _c, _d) in CLEARANCE.items():
        save(keycard_sprite(level), "item", name)
        flat_item(name)
        tex(f"{READER}_front_{level}", tex_reader_front(level))
    tex(f"{READER}_body", riveted(962, base=[(30, 33, 38), (44, 48, 54), (58, 63, 70), (74, 80, 88), (96, 102, 110)],
                                  plates=((0, 0, 16, 16),)))
    for status in READER_STATUS:
        tex(f"{READER}_lamp_{status}", tex_reader_lamp(status))
    variants = {}
    for level in CLEARANCE:
        for status in READER_STATUS:
            model = f"{READER}_{level}_{status}"
            m = Model({"body": f"{READER}_body", "front": f"{READER}_front_{level}", "lamp": f"{READER}_lamp_{status}"},
                      f"{READER}_body")
            m.box((3, 1, 14), (13, 15, 16), "body", face_tex={"north": "front"}, face_uv={"north": [3, 1, 13, 15]})
            e = m.box((9, 10, 13.5), (12, 13, 14), "lamp", faces=("north", "east", "west", "up", "down"), uv=[4, 4, 12, 12])
            emissive(e)
            m.box((5, 7, 13.6), (11, 9, 14), "body", faces=("north", "up", "down", "east", "west"),
                  face_tex={"north": "front"}, face_uv={"north": [5, 7, 11, 9]})
            m.write(model)
            for facing, rot in sfa_facings():
                v = {"model": T(model)}
                if rot:
                    v["y"] = rot
                variants[f"facing={facing},level={level},status={status}"] = v
    write_json(os.path.join(ASSETS, "blockstates", READER + ".json"), {"variants": variants})
    block_item(READER, f"{READER}_a_locked")


def sfa_facings():
    return (("north", 0), ("east", 90), ("south", 180), ("west", 270))


def write_data():
    write_json(os.path.join(DATA, "damage_type", "laser.json"),
               {"message_id": f"{MOD}.laser", "exhaustion": 0.1, "scaling": "never"})
    write_json(os.path.join(DATA, "banner_pattern", "oinstein.json"),
               {"asset_id": f"{MOD}:oinstein", "translation_key": f"block.{MOD}.banner.oinstein"})
    add_to_tag("banner_pattern/no_item_required", [f"{MOD}:oinstein"])
    add_to_tag("block/mineable/pickaxe", [P(RSTEEL), P(HSTEEL), P(TESLA)])
    add_to_tag("block/needs_stone_tool", [P(RSTEEL), P(HSTEEL)])
    for t in ("block/dragon_immune", "block/wither_immune", "block/features_cannot_replace"):
        add_to_tag(t, [P(BARRIER), P(EMITTER), P(READER)])
    for b in (RSTEEL, HSTEEL, TESLA, JAR) + tuple(POSTERS):
        pools = [{"rolls": 1, "bonus_rolls": 0, "entries": [{"type": "minecraft:item", "name": P(b)}],
                  "conditions": [{"condition": "minecraft:survives_explosion"}]}]
        if b in POSTERS:
            pools[0]["conditions"].append({"condition": "minecraft:block_state_property", "block": P(b),
                                           "properties": {"half": "lower"}})
        write_json(os.path.join(DATA, "loot_table", "blocks", b + ".json"),
                   {"type": "minecraft:block", "pools": pools, "random_sequence": f"{MOD}:blocks/{b}"})
    shaped(RSTEEL, ["III", "INI", "III"], {"I": "minecraft:iron_ingot", "N": "minecraft:iron_nugget"}, RSTEEL, count=8,
           category="building")
    shaped(HSTEEL, ["SY", "YS"], {"S": RSTEEL, "Y": "minecraft:yellow_dye"}, HSTEEL, count=4, category="building")
    shaped(TESLA, [" I ", " C ", "SRS"], {"I": "minecraft:iron_ingot", "C": "minecraft:copper_ingot", "S": RSTEEL,
                                          "R": "minecraft:redstone"}, TESLA, category="decorations")
    chest_loot()


# =====================================================================================================================
# Loot
# =====================================================================================================================
OPTIONAL_ITEMS = ("atomic_scrap", "control_collar", "brain_flask")   # other agents' items, used once they exist


def mod_item_exists(name):
    for root, _dirs, files in os.walk(JAVA):
        for f in files:
            if f.endswith(".java"):
                with open(os.path.join(root, f), encoding="utf-8") as fh:
                    if f'"{name}"' in fh.read():
                        return True
    return False


def lab_notes(weight):
    return {"type": "minecraft:item", "name": "minecraft:written_book", "weight": weight, "functions": [
        {"function": "minecraft:set_book_cover", "title": {"raw": "Lab Notes"}, "author": "Dr. Oinstein",
         "generation": 1},
        {"function": "minecraft:set_written_book_pages", "mode": "replace_all",
         "pages": [{"raw": {"translate": f"book.{MOD}.oinstein_notes.page_{i}"}} for i in range(len(NOTES_PAGES))]},
        {"function": "minecraft:set_name", "target": "custom_name",
         "name": {"translate": f"book.{MOD}.oinstein_notes.title", "italic": False, "color": "red"}}]}


def chest_loot():
    it = R_.it
    extra = [it(n, 6, 1, 4 if n == "atomic_scrap" else 1) for n in OPTIONAL_ITEMS if mod_item_exists(n)]
    core = [it("atomic_core", 3)] if mod_item_exists("atomic_core") else []
    blaster = [it("ray_blaster", 1)] if mod_item_exists("ray_blaster") else []
    base = [it("minecraft:iron_ingot", 14, 2, 6), it("minecraft:redstone", 14, 3, 9), it("minecraft:copper_ingot", 12, 2, 8),
            it("minecraft:iron_nugget", 10, 4, 12), it("minecraft:gold_nugget", 6, 2, 6), it("vacuum_tube", 6, 1, 3),
            it("aluminum_ingot", 6, 1, 4), it("minecraft:glass_bottle", 5, 1, 3), it("minecraft:bread", 5, 1, 3),
            it("minecraft:quartz", 5, 2, 6)] + extra
    R_.chest("chests/oinstein_outpost", [
        (R_.rolls(3, 6), base),
        (R_.rolls(0, 1), [lab_notes(3), it("empty_fuel_canister", 3), it("rocket_fuel_canister", 1), R_.empty(4)])])
    R_.chest("chests/oinstein_lab", [
        (R_.rolls(3, 6), base + [it("minecraft:redstone_block", 3), it("minecraft:experience_bottle", 6, 1, 4),
                                 it("guidance_computer", 1)] + core + [it("minecraft:potion", 4, extra=[
                                     {"function": "minecraft:set_potion", "id": "minecraft:strength"}])]),
        (1.0, [lab_notes(1)]),
        (R_.rolls(0, 2), [it("glyph_tablet", 3), it("venusian_idol", 1), R_.empty(4)])])
    R_.chest("chests/oinstein_armory", [
        (R_.rolls(4, 7), base + [it("minecraft:iron_block", 2), it("minecraft:diamond", 2, 1, 2),
                                 it("minecraft:golden_apple", 2), it("titanium_ingot", 5, 1, 4),
                                 it("minecraft:iron_chestplate", 2), it("minecraft:crossbow", 2),
                                 it("minecraft:arrow", 6, 4, 12)] + core),
        (R_.rolls(0, 1), [lab_notes(2), it("ancient_amulet", 1), R_.empty(3)] + blaster)])
    # the commander's locker of a capture camp (A), relay pylon (B) and field lab (C): the card is guaranteed
    for level, (card, _c, _d) in CLEARANCE.items():
        R_.chest(f"chests/oinstein_keycard_{level}", [
            (1.0, [it(card, 1)]),
            (R_.rolls(2, 4), base),
            (R_.rolls(0, 1), [lab_notes(2), it("minecraft:experience_bottle", 2, 1, 3), R_.empty(3)])])
    # the expedition's gear, taken off the prisoners: canisters, instruments, rations, their notes
    R_.chest("chests/oinstein_confiscated", [
        (R_.rolls(4, 7), [it("rocket_fuel_canister", 8, 1, 3), it("liquid_oxygen_canister", 8, 1, 3),
                          it("empty_fuel_canister", 6, 1, 3), it("vacuum_tube", 6, 1, 4), it("guidance_computer", 2),
                          it("minecraft:spyglass", 4), it("minecraft:compass", 5), it("minecraft:clock", 5),
                          it("minecraft:map", 4), it("minecraft:bread", 8, 2, 6), it("minecraft:cooked_beef", 5, 1, 4),
                          it("minecraft:torch", 6, 4, 12), it("aluminum_ingot", 4, 1, 4), it("minecraft:paper", 5, 2, 8),
                          it("minecraft:glass_bottle", 4, 1, 3)]),
        (R_.rolls(0, 1), [it("space_helmet", 2), it("space_boots", 2), R_.empty(4)])])
    # the Director's own safe in the lower laboratory
    R_.chest("chests/oinstein_director", [
        (R_.rolls(4, 6), base + [it("minecraft:diamond", 4, 1, 3), it("minecraft:gold_ingot", 6, 2, 5),
                                 it("minecraft:golden_apple", 3), it("titanium_ingot", 5, 2, 5),
                                 it("minecraft:experience_bottle", 6, 2, 6)] + core),
        (1.0, [lab_notes(1)] + blaster + [it("minecraft:enchanted_golden_apple", 1)])])


# =====================================================================================================================
# Structure helpers (on top of ruins.Ruin)
# =====================================================================================================================
NOVUS = f"{MOD}:hominid_novus"
SAPIENS = f"{MOD}:hominus_sapiens"
SENTRY = f"{MOD}:atomic_sentry"
AUTOMATON = f"{MOD}:atomic_automaton"
TRIBESMAN = f"{MOD}:tribesman"
MOBS = (NOVUS, SAPIENS, SENTRY, AUTOMATON)


class Double(float):
    tag = TAG_DOUBLE


def M(name):
    return "minecraft:" + name


def V(name, **props):
    return st(M(name), **props)


CON = V("gray_concrete")
LCON = V("light_gray_concrete")
WCON = V("white_concrete")
BCON = V("black_concrete")
YCON = V("yellow_concrete")
RCON = V("red_concrete")
IRON = V("iron_block")
GLASS = V("glass")
TINT = V("tinted_glass")
LANTERN_SEA = V("sea_lantern")
RSTEEL_S = st(RSTEEL)
HSTEEL_S = st(HSTEEL)
GRATE = st("floor_grate")
HULL = st("hull_panel")
STRIPE = st("hull_panel_striped")
EMITTER_S = st(EMITTER, powered=True)
TESLA_S = st(TESLA)
JAR_S = st(JAR)
PACKED = V("packed_mud")      # trodden ground: not #minecraft:dirt, so no Venus plants or trees take root
DOUBLE_SLAB = V("smooth_stone_slab", type="double", waterlogged=False)


def barrier(axis):
    return st(BARRIER, axis=axis, powered=True)


def bars():
    return V("iron_bars", north=False, east=False, south=False, west=False, waterlogged=False)


def pane(color=None):
    name = f"{color}_stained_glass_pane" if color else "glass_pane"
    return V(name, north=False, east=False, south=False, west=False, waterlogged=False)


def chain(axis="y"):
    return V("iron_chain", axis=axis, waterlogged=False)   # 1.21.9 renamed minecraft:chain


def pipe(axis):
    return st("chrome_trim", axis=axis)


def lamp():
    return V("redstone_lamp", lit=True)


def light_on():
    return st("ceiling_light", lit=True)


def computer(facing):
    return st("computer_bank", facing=facing, lit=True)


def panel(facing):
    return st("control_panel", facing=facing, lit=True)


def campfire(signal=True):
    return V("campfire", facing="north", lit=True, signal_fire=signal, waterlogged=False)


def poster(s, x, y, z, name, facing):
    s.set(x, y, z, st(name, facing=facing, half="lower"))
    s.set(x, y + 1, z, st(name, facing=facing, half="upper"))


def text_nbt(keys, color="black", glow=False):
    msgs = [Compound({"translate": Str(k)}) if k else Compound({"text": Str("")}) for k in keys]
    msgs += [Compound({"text": Str("")})] * (4 - len(msgs))
    return Compound({"messages": List(msgs, TAG_COMPOUND), "color": Str(color), "has_glowing_text": Byte(1 if glow else 0)})


def sign(facing, lines, color="red", wood="pale_oak", glow=True):
    """A waxed wall sign (attached to the block behind it, opposite to facing) with translatable lines."""
    keys = [f"sign.{MOD}.{l}" if l else None for l in lines]
    return (M(f"{wood}_wall_sign"), {"facing": facing, "waterlogged": "false"},
            Compound({"id": Str("minecraft:sign"), "is_waxed": Byte(1), "front_text": text_nbt(keys, color, glow),
                      "back_text": text_nbt([None] * 4)}))


SIGN_RESTRICTED = ["restricted_1", "restricted_2", "restricted_3", "restricted_4"]
SIGN_SLOGAN = ["slogan_1", "slogan_2", "slogan_3", "slogan_4"]
SIGN_DANGER = ["danger_1", "danger_2", "danger_3", "danger_4"]
SIGN_CHECKPOINT = ["checkpoint_1", "checkpoint_2", "checkpoint_3", "checkpoint_4"]
SIGN_SEALED = ["sealed_1", "sealed_2", "sealed_3", "sealed_4"]


def banner_nbt():
    return Compound({"id": Str("minecraft:banner"), "patterns": List([
        Compound({"pattern": Str("minecraft:border"), "color": Str("black")}),
        Compound({"pattern": Str(f"{MOD}:oinstein"), "color": Str("white")})], TAG_COMPOUND)})


def wall_banner(facing):
    return (M("red_wall_banner"), {"facing": facing}, banner_nbt())


def standing_banner(rotation):
    return (M("red_banner"), {"rotation": str(rotation)}, banner_nbt())


def book_item(book):
    title, pages = BOOKS[book]
    return Compound({"id": Str("minecraft:written_book"), "count": Int(1), "components": Compound({
        "minecraft:written_book_content": Compound({
            "title": Compound({"raw": Str(title)}), "author": Str("Dr. Oinstein"), "generation": Int(0),
            "pages": List([Compound({"raw": Compound({"translate": Str(f"book.{MOD}.{book}.page_{i}")})})
                           for i in range(pages)], TAG_COMPOUND),
            "resolved": Byte(0)}),
        "minecraft:custom_name": Compound({"translate": Str(f"book.{MOD}.{book}.title"), "italic": Byte(0),
                                           "color": Str("red")})})})


def lectern(facing, book):
    return (M("lectern"), {"facing": facing, "has_book": "true", "powered": "false"},
            Compound({"id": Str("minecraft:lectern"), "Book": book_item(book), "Page": Int(0)}))


def locker(facing, table, name="commander_locker"):
    """A named loot chest ("Commander's Locker"): where an outpost keeps its security card."""
    return (M("chest"), {"facing": facing, "type": "single", "waterlogged": "false"},
            Compound({"id": Str("minecraft:chest"), "LootTable": Str(f"{MOD}:{table}"),
                      "CustomName": Compound({"translate": Str(f"container.{MOD}.{name}"), "italic": Byte(0)})}))


def reader(facing, level):
    """A keycard reader on the wall (attached to the block behind it, opposite to facing)."""
    return st(READER, facing=facing, level=level, status="locked")


def data_marker(name):
    """A DATA structure block: the template piece replaces it at placement (AttachedTemplatePiece.handleDataMarker)."""
    return (M("structure_block"), {"mode": "data"},
            Compound({"id": Str("minecraft:structure_block"), "mode": Str("DATA"), "metadata": Str(name)}))


class Base(Ruin):
    """A Ruin with entities: Oinstein's people (and his captives) standing in the template."""

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.entities = []

    def mob(self, x, y, z, eid, **extra):
        nbt = Compound({"id": Str(eid), "PersistenceRequired": Byte(1)})
        for k, v in extra.items():
            nbt[k] = v
        self.entities.append(((x, y, z), nbt))

    def captive(self, x, y, z, specimen=False):
        extra = {"Captive": Byte(1), "Role": Str(self.rnd.choice(("hunter", "gatherer", "hunter", "shaman")))}
        if specimen:
            extra.update(NoAI=Byte(1), Silent=Byte(1), Invulnerable=Byte(1))
        self.mob(x, y, z, TRIBESMAN, **extra)

    def entity_nbt(self):
        out = []
        for (x, y, z), nbt in self.entities:
            out.append(Compound({"pos": List([Double(x + 0.5), Double(y), Double(z + 0.5)], TAG_DOUBLE),
                                 "blockPos": List([Int(x), Int(y), Int(z)], TAG_INT), "nbt": nbt}))
        return out

    def ring(self, x0, z0, x1, z1, y, state):
        for x in range(x0, x1 + 1):
            for z in (z0, z1):
                self.set(x, y, z, state() if callable(state) else state)
        for z in range(z0, z1 + 1):
            for x in (x0, x1):
                self.set(x, y, z, state() if callable(state) else state)

    def walls(self, x0, z0, x1, z1, y0, y1, state):
        for y in range(y0, y1 + 1):
            self.ring(x0, z0, x1, z1, y, state)

    def box(self, x0, y0, z0, x1, y1, z1, wall, floor=None, roof=None):
        """A hollow building: walls, floor at y0-1 and roof at y1+1 (if given), air inside."""
        self.fill(x0 + 1, y0, z0 + 1, x1 - 1, y1, z1 - 1, S_AIR)
        self.walls(x0, z0, x1, z1, y0, y1, wall)
        if floor:
            self.fill(x0, y0 - 1, z0, x1, y0 - 1, z1, floor)
        if roof:
            self.fill(x0, y1 + 1, z0, x1, y1 + 1, z1, roof)


PANES = {M("iron_bars")} | {M(f"{c}_stained_glass_pane") for c in ("lime", "red", "black", "light_blue", "gray")} | {
    M("glass_pane")}
SOLID_EXTRA = {M(n) for n in ("gray_concrete", "light_gray_concrete", "white_concrete", "black_concrete",
                              "yellow_concrete", "red_concrete", "iron_block", "glass", "tinted_glass", "sea_lantern",
                              "redstone_lamp", "redstone_block", "smooth_stone", "hay_block", "coarse_dirt",
                              "polished_andesite", "lime_stained_glass", "black_stained_glass", "red_stained_glass",
                              "bookshelf", "blast_furnace", "packed_mud", "cut_copper", "mud_bricks")} | {
    P(n) for n in (RSTEEL, HSTEEL, "floor_grate", "hull_panel", "hull_panel_striped", "aluminum_block", "titanium_block",
                   "cargo_crate", "reactor_core", "computer_bank", "tape_archive")} | {M("smooth_stone_slab")}
FULL.update(SOLID_EXTRA)


def connect_panes(s):
    for (x, y, z), (name, props, nbt) in list(s.b.items()):
        if name in PANES:
            p = dict(props)
            for d, (dx, dz) in DIRS.items():
                n = s.name_at(x + dx, y, z + dz)
                p[d] = "true" if (n in PANES or (n in FULL and n != M("smooth_stone_slab"))) else "false"
            s.b[(x, y, z)] = (name, p, nbt)


WALL_HUNG = {M("pale_oak_wall_sign"), M("dark_oak_wall_sign"), M("red_wall_banner"), M("ladder")} | {P(p) for p in POSTERS} | {
    P("control_panel"), P("wall_sconce"), P("poster_freedom"), P(READER), M("lever")}
NEEDS_FLOOR = {M("rail"), M("lectern"), M("campfire"), M("red_banner"), M("lantern"), P(JAR), P(TESLA), M("chest"),
               M("barrel"), P("computer_bank"), P("lab_sink"), P("tape_archive"), P("crew_bunk"), P("crew_locker"),
               P("radar_scope"), M("lightning_rod"), M("end_rod"), M("cauldron"), M(f"{'red'}_bed"), M("iron_door"),
               P("captain_chair"), P("diner_stool"), P("oxygen_tank_rack"), P("supply_cabinet")}


def audit(s):
    """Supports: wall-hung pieces need a full block behind them, floor pieces something solid below; no gravity
    blocks; every entity stands in open space on something solid."""
    problems = []
    gravity = {M(n) for n in ("sand", "red_sand", "gravel", "anvil")}
    for (x, y, z), (name, props, _n) in s.b.items():
        if name in gravity or name.endswith("concrete_powder"):
            problems.append(f"gravity block {name} at {(x, y, z)}")
        if name in WALL_HUNG and props.get("half") != "upper":
            dx, dz = DIRS[OPP[props["facing"]]]
            if not s.full(x + dx, y, z + dz):
                problems.append(f"{name} at {(x, y, z)} hangs on nothing")
        if name in NEEDS_FLOOR and props.get("half", "lower") == "lower" and props.get("facing") not in ("up", "down") \
                and not (name in (M("end_rod"), M("lightning_rod")) and props.get("facing") in ("east", "west", "north", "south")):
            below = s.name_at(x, y - 1, z)
            if not (below in FULL or (below is None and y - 1 <= s.G) or (below or "").endswith("_slab")
                    or below in (M("hay_block"), P(RSTEEL)) or below == name):
                problems.append(f"{name} at {(x, y, z)} stands on {below}")
    for (x, y, z), nbt in s.entities:
        feet = s.name_at(x, y, z)
        head = s.name_at(x, y + 1, z)
        below = s.name_at(x, y - 1, z)
        tall = nbt["id"] in (AUTOMATON, NOVUS) and s.name_at(x, y + 2, z) not in (None, AIR)
        if feet not in (None, AIR) or head not in (None, AIR) or tall:
            problems.append(f"entity {nbt['id']} at {(x, y, z)} is stuck in {feet}/{head}")
        if not (s.full(x, y - 1, z) or (below is None and y - 1 <= s.G) or (below or "").endswith("_slab")
                or below in (M("iron_trapdoor"),)):
            problems.append(f"entity {nbt['id']} at {(x, y, z)} floats over {below}")
    barriers = [p for p, st_ in s.b.items() if st_[0] in (P(BARRIER), P(EMITTER))]
    for (x, y, z), nbt in s.entities:
        if any(abs(bx - x) <= 2 and abs(bz - z) <= 2 and -3 <= by - y <= 3 for (bx, by, bz) in barriers):
            problems.append(f"entity {nbt['id']} at {(x, y, z)} stands next to a laser barrier")
    if problems:
        raise SystemExit(f"oinstein.py: {s.name}:\n  " + "\n  ".join(problems[:40]))


# vanilla property schemas the Oinstein templates use (checked by ruins.validate)
_B = ("true", "false")
_H = ("north", "east", "south", "west")
for _n in ("gray_concrete", "light_gray_concrete", "white_concrete", "black_concrete", "yellow_concrete", "red_concrete",
           "iron_block", "glass", "tinted_glass", "sea_lantern", "redstone_block", "smooth_stone", "coarse_dirt",
           "polished_andesite", "lime_stained_glass", "black_stained_glass", "red_stained_glass", "bookshelf",
           "packed_mud", "cut_copper", "water", "gray_carpet", "red_carpet"):
    R_.VANILLA[M(_n)] = {}
R_.VANILLA[M("water")] = {"level": tuple(str(i) for i in range(16))}
for _n in ("iron_bars", "glass_pane", "lime_stained_glass_pane", "red_stained_glass_pane", "black_stained_glass_pane",
           "light_blue_stained_glass_pane", "gray_stained_glass_pane"):
    R_.VANILLA[M(_n)] = {d: _B for d in ("north", "east", "south", "west", "waterlogged")}
R_.VANILLA.update({
    M("iron_chain"): {"axis": ("x", "y", "z"), "waterlogged": _B},
    M("redstone_lamp"): {"lit": _B},
    M("hay_block"): {"axis": ("x", "y", "z")},
    M("smooth_stone_slab"): {"type": ("top", "bottom", "double"), "waterlogged": _B},
    M("polished_andesite_slab"): {"type": ("top", "bottom", "double"), "waterlogged": _B},
    M("polished_andesite_stairs"): R_.STAIR_SCHEMA,
    M("lightning_rod"): {"facing": _H + ("up", "down"), "powered": _B, "waterlogged": _B},
    M("end_rod"): {"facing": _H + ("up", "down")},
    M("rail"): {"shape": ("north_south", "east_west", "ascending_east", "ascending_west", "ascending_north",
                          "ascending_south", "south_east", "south_west", "north_west", "north_east"), "waterlogged": _B},
    M("lectern"): {"facing": _H, "has_book": _B, "powered": _B},
    M("pale_oak_wall_sign"): {"facing": _H, "waterlogged": _B},
    M("dark_oak_wall_sign"): {"facing": _H, "waterlogged": _B},
    M("red_wall_banner"): {"facing": _H},
    M("red_banner"): {"rotation": tuple(str(i) for i in range(16))},
    M("iron_trapdoor"): {"facing": _H, "half": ("top", "bottom"), "open": _B, "powered": _B, "waterlogged": _B},
    M("blast_furnace"): {"facing": _H, "lit": _B},
    M("cauldron"): {},
    M("red_bed"): {"facing": _H, "occupied": _B, "part": ("head", "foot")},
    M("lever"): {"face": ("floor", "wall", "ceiling"), "facing": _H, "powered": _B},
    M("dark_oak_fence_gate"): {"facing": _H, "in_wall": _B, "open": _B, "powered": _B},
    M("structure_block"): {"mode": ("save", "load", "corner", "data")},
    M("iron_door"): {"facing": _H, "half": ("upper", "lower"), "hinge": ("left", "right"), "open": _B, "powered": _B},
    M("mud_bricks"): {},
    M("polished_blackstone_stairs"): R_.STAIR_SCHEMA,
})


# =====================================================================================================================
# Lore: books, signs, names (EN / RU)
# =====================================================================================================================
JOURNAL_PAGES = [
    ("LAB JOURNAL - Dr. A. Oinstein. Day 1 on Venus. The hominids of this jungle are a gift: strong backs, nimble "
     "hands, and minds as empty as a fresh notebook. I shall fill them.",
     "ЛАБОРАТОРНЫЙ ЖУРНАЛ - д-р А. Ойнштайн. День 1-й на Венере. Здешние гоминиды - настоящий подарок: крепкие "
     "спины, ловкие руки и пустые, как новая тетрадь, головы. Я их заполню."),
    ("Day 112. Specimen 14 survived the serum. Twice the muscle, half the patience. I name the type HOMINID NOVUS. "
     "It obeys whoever holds the whistle. I hold the whistle.",
     "День 112-й. Образец 14 пережил сыворотку. Вдвое больше мышц, вдвое меньше терпения. Нарекаю тип HOMINID NOVUS. "
     "Он слушается того, у кого свисток. Свисток у меня."),
    ("Day 260. Brain-flask grafts at last! Specimen 31 recited the periodic table and then shot an assistant. A "
     "success. HOMINUS SAPIENS walks. A better ape for a better tomorrow!",
     "День 260-й. Наконец-то пересадка мозга в колбу! Образец 31 прочитал таблицу Менделеева, а затем застрелил "
     "ассистента. Успех. HOMINUS SAPIENS ходит. Лучшая обезьяна ради лучшего завтра!"),
    ("Day 301. The Earth expedition is snooping around the ruins. The barrier stays up. Nobody enters the lower "
     "laboratory. NOBODY. Not even you, Kessler - I know you read this.",
     "День 301-й. Земная экспедиция рыщет у руин. Барьер не отключать. В нижнюю лабораторию не входит никто. НИКТО. "
     "Даже вы, Кесслер, - я знаю, что вы это читаете."),
]
ORDERS_PAGES = [
    ("STANDING ORDERS. 1. Capture hominids alive. Damaged specimens are deducted from your rations.",
     "ПОСТОЯННЫЙ ПРИКАЗ. 1. Ловить гоминидов живыми. Повреждённые образцы вычитаются из вашего пайка."),
    ("2. Sentries hold their posts. Automatons patrol. Novus units do not eat the specimens. 3. Laser barriers "
     "stay ON. Touching them is a firing offence. Literally.",
     "2. Часовые держат посты. Автоматоны патрулируют. Особям Новус не есть образцы. 3. Лазерные барьеры НЕ "
     "выключать. Прикосновение карается увольнением. Буквально."),
    ("4. Visitors from Earth are to be welcomed warmly - into Cage 3. Glory to science! - Dr. A. Oinstein, "
     "Director, Oinstein Institute.",
     "4. Гостей с Земли встречать радушно - в клетке №3. Слава науке! - д-р А. Ойнштайн, директор Института "
     "Ойнштайна."),
]
NOTES_PAGES = [
    ("Field notes, outpost 7. Serum batch V-9: three Novus, one fatality, one tail (?). The doctor is pleased.",
     "Полевые заметки, аванпост 7. Сыворотка партии V-9: трое Новус, один погибший, у одного вырос хвост (?). "
     "Доктор доволен."),
    ("Relay pylons must stay powered - the Institute barrier draws on all of them. If a pylon goes dark, run.",
     "Ретрансляционные пилоны должны быть под током - барьер Института питается от всех сразу. Если пилон погас - "
     "бегите."),
]
CLEARANCE_PAGES = [
    ("SECURITY OFFICE - MEMO 12. Clearance for the Institute is by punched card only. Readers stand beside every "
     "barrier. One card per level; cards are NOT to be copied, lent or eaten.",
     "ОТДЕЛ БЕЗОПАСНОСТИ - ПАМЯТКА 12. Допуск в Институт - только по перфокарте. Считыватели стоят у каждого "
     "барьера. Одна карта на уровень; карты НЕ копировать, НЕ одалживать и НЕ есть."),
    ("LEVEL A (red): the main gate. Each capture camp commandant keeps one in his locker.\n\nLEVEL B (blue): the "
     "central building. Locked in the generator shed of every relay pylon.",
     "УРОВЕНЬ A (красная): главные ворота. Хранится в шкафчике коменданта каждого лагеря захвата.\n\nУРОВЕНЬ B "
     "(синяя): центральный корпус. Заперта в генераторной каждого ретрансляционного пилона."),
    ("LEVEL C (green): the lift to the lower laboratory. Kept by the chief researcher of each field laboratory.\n\n"
     "Checkpoints hold NO cards. Lose yours and you join the specimens. - Security Office",
     "УРОВЕНЬ C (зелёная): лифт в нижнюю лабораторию. Хранится у старшего научного сотрудника каждой полевой "
     "лаборатории.\n\nНа КПП карт НЕТ. Потеряешь свою - пополнишь ряды образцов. - Отдел безопасности"),
]
FINAL_PAGES = [
    ("FINAL ENTRY. So. They came through the gate, the hall, even my lift. Clever apes. I have always admired "
     "clever apes. I make them.",
     "ПОСЛЕДНЯЯ ЗАПИСЬ. Итак. Они прошли ворота, корпус и даже мой лифт. Умные обезьяны. Я всегда восхищался "
     "умными обезьянами. Я их делаю."),
    ("Serum V-OMEGA is perfected: thrice the muscle, ten times the mind, and a temper I can only call "
     "magnificent. I have tested it on no one. Yet.",
     "Сыворотка V-ОМЕГА доведена до совершенства: втрое больше мышц, вдесятеро больше ума и характер, который "
     "иначе как великолепным не назовёшь. Я ни на ком её не испытывал. Пока."),
    ("If they corner me, I shall test it on myself - and greet them from the cockpit of the Walker in the Main "
     "Laboratory. Let science decide who is the better ape.",
     "Если меня загонят в угол, я испытаю её на себе - и встречу их из кабины Шагохода в Главной лаборатории. "
     "Пусть наука решит, кто из нас лучшая обезьяна."),
    ("To whoever reads this: you are about to witness the next step of evolution. Try not to scream. "
     "- Dr. A. Oinstein, Director",
     "Тому, кто это читает: сейчас вы увидите следующий шаг эволюции. Постарайтесь не кричать. "
     "- д-р А. Ойнштайн, директор"),
]
BOOKS = {"oinstein_journal": ("Lab Journal", len(JOURNAL_PAGES)),
         "oinstein_orders": ("Standing Orders", len(ORDERS_PAGES)),
         "oinstein_clearance": ("Security Clearance", len(CLEARANCE_PAGES)),
         "oinstein_final": ("Final Entry", len(FINAL_PAGES))}
SIGNS = {
    "restricted_1": ("RESTRICTED", "ЗАПРЕТНАЯ ЗОНА"), "restricted_2": ("PROPERTY OF", "СОБСТВЕННОСТЬ"),
    "restricted_3": ("DR. OINSTEIN", "Д-РА ОЙНШТАЙНА"), "restricted_4": ("KEEP OUT!", "НЕ ВХОДИТЬ!"),
    "slogan_1": ("OINSTEIN INSTITUTE", "ИНСТИТУТ ОЙНШТАЙНА"), "slogan_2": ("A BETTER APE", "ЛУЧШАЯ ОБЕЗЬЯНА"),
    "slogan_3": ("FOR A BETTER", "РАДИ ЛУЧШЕГО"), "slogan_4": ("TOMORROW", "ЗАВТРА"),
    "danger_1": ("DANGER!", "ОПАСНО!"), "danger_2": ("LASER BARRIER", "ЛАЗЕРНЫЙ БАРЬЕР"),
    "danger_3": ("10 000 VOLTS", "10 000 ВОЛЬТ"), "danger_4": ("DO NOT TOUCH", "НЕ ПРИКАСАТЬСЯ"),
    "checkpoint_1": ("CHECKPOINT", "КОНТРОЛЬНЫЙ ПУНКТ"), "checkpoint_2": ("HALT!", "СТОЙ!"),
    "checkpoint_3": ("PAPERS, PLEASE", "ПРЕДЪЯВИТЕ ПРОПУСК"), "checkpoint_4": ("- OINSTEIN INST.", "- ИНСТИТУТ О."),
    "sealed_1": ("LOWER LABORATORY", "НИЖНЯЯ ЛАБОРАТОРИЯ"), "sealed_2": ("CLEARANCE", "ДОПУСК"),
    "sealed_3": ("LEVEL C ONLY", "ТОЛЬКО УРОВЕНЬ C"), "sealed_4": ("- THE DIRECTOR", "- ДИРЕКТОР"),
    "mainlab_1": ("MAIN LABORATORY", "ГЛАВНАЯ"), "mainlab_2": ("", "ЛАБОРАТОРИЯ"),
    "mainlab_3": ("DIRECTOR ONLY", "ТОЛЬКО ДЛЯ"), "mainlab_4": ("KEEP OUT!", "ДИРЕКТОРА"),
    "office_1": ("DR. A. OINSTEIN", "Д-Р А. ОЙНШТАЙН"), "office_2": ("DIRECTOR", "ДИРЕКТОР"),
    "office_3": ("KNOCK", "СТУЧАТЬ"), "office_4": ("AND WAIT", "И ЖДАТЬ"),
    "brains_1": ("BRAIN BANK", "БАНК МОЗГОВ"), "brains_2": ("DO NOT TAP", "НЕ СТУЧАТЬ"),
    "brains_3": ("THE JARS", "ПО БАНКАМ"), "brains_4": ("", ""),
    "card_a_1": ("SECURITY", "ПОСТ"), "card_a_2": ("INSERT CARD", "ВСТАВЬТЕ КАРТУ"),
    "card_a_3": ("LEVEL A", "УРОВЕНЬ A"), "card_a_4": ("(RED)", "(КРАСНАЯ)"),
    "card_b_1": ("SECURITY", "ПОСТ"), "card_b_2": ("INSERT CARD", "ВСТАВЬТЕ КАРТУ"),
    "card_b_3": ("LEVEL B", "УРОВЕНЬ B"), "card_b_4": ("(BLUE)", "(СИНЯЯ)"),
}
SIGN_MAINLAB = ["mainlab_1", "mainlab_2", "mainlab_3", "mainlab_4"]
SIGN_OFFICE = ["office_1", "office_2", "office_3", "office_4"]
SIGN_BRAINS = ["brains_1", "brains_2", "brains_3", "brains_4"]
SIGN_CARD = {lv: [f"card_{lv}_{i}" for i in range(1, 5)] for lv in ("a", "b")}
NAMES = {
    BARRIER: ("Laser Barrier", "Лазерный барьер"),
    EMITTER: ("Laser Emitter", "Лазерный излучатель"),
    RSTEEL: ("Riveted Steel", "Клёпаная сталь"),
    HSTEEL: ("Hazard Steel", "Сталь с предупредительной разметкой"),
    TESLA: ("Tesla Coil", "Катушка Теслы"),
    JAR: ("Brain in a Jar", "Мозг в банке"),
    "oinstein_poster_insignia": ("Oinstein Institute Poster", "Плакат «Институт Ойнштайна»"),
    "oinstein_poster_better_ape": ("\"New Ape!\" Poster", "Плакат «Новая обезьяна!»"),
    "oinstein_poster_restricted": ("\"Stop - Keep Out\" Poster", "Плакат «Стой - не входить»"),
    READER: ("Keycard Reader", "Считыватель карт допуска"),
}
EN = {f"block.{MOD}.{k}": v[0] for k, v in NAMES.items()}
RU = {f"block.{MOD}.{k}": v[1] for k, v in NAMES.items()}
CARD_TEXT = {  # level: (EN letter colour, RU colour, EN barrier, RU barrier)
    "a": ("red", "красная", "the main gate", "главные ворота"),
    "b": ("blue", "синяя", "the central building", "центральный корпус"),
    "c": ("green", "зелёная", "the lift to the lower laboratory", "лифт в нижнюю лабораторию")}
for _lv, (_card, _c, _d) in CLEARANCE.items():
    _ec, _rc, _eb, _rb = CARD_TEXT[_lv]
    L = _lv.upper()
    EN[f"item.{MOD}.{_card}"], RU[f"item.{MOD}.{_card}"] = f"Security Card — Level {L}", f"Карта допуска — уровень {L}"
    EN[f"item.{MOD}.{_card}.lore"] = f"Oinstein Institute, level {L} ({_ec}): opens {_eb}"
    RU[f"item.{MOD}.{_card}.lore"] = f"Институт Ойнштайна, уровень {L} ({_rc}): открывает {_rb}"
EN.update({f"message.{MOD}.keycard.required": "ACCESS DENIED - %s required",
           f"message.{MOD}.keycard.granted": "ACCESS GRANTED - barrier disengaged",
           f"message.{MOD}.keycard.open": "Access granted. The barrier is down.",
           f"container.{MOD}.commander_locker": "Commander's Locker",
           f"container.{MOD}.director_safe": "Director's Safe",
           f"container.{MOD}.researcher_locker": "Chief Researcher's Locker"})
RU.update({f"message.{MOD}.keycard.required": "ДОСТУП ЗАПРЕЩЁН - нужна %s",
           f"message.{MOD}.keycard.granted": "ДОСТУП РАЗРЕШЁН - барьер отключён",
           f"message.{MOD}.keycard.open": "Доступ разрешён. Барьер снят.",
           f"container.{MOD}.commander_locker": "Шкафчик коменданта",
           f"container.{MOD}.director_safe": "Сейф директора",
           f"container.{MOD}.researcher_locker": "Шкафчик старшего научного сотрудника"})
EN[f"block.{MOD}.banner.oinstein"], RU[f"block.{MOD}.banner.oinstein"] = "Oinstein Insignia", "Эмблема Ойнштайна"
for _c in ("white", "orange", "magenta", "light_blue", "yellow", "lime", "pink", "gray", "light_gray", "cyan", "purple",
           "blue", "brown", "green", "red", "black"):
    EN[f"block.{MOD}.banner.oinstein.{_c}"] = f"{_c.replace('_', ' ').title()} Oinstein Insignia"
    RU[f"block.{MOD}.banner.oinstein.{_c}"] = "Эмблема Ойнштайна"
EN[f"death.attack.{MOD}.laser"] = "%1$s was fried by a laser barrier"
RU[f"death.attack.{MOD}.laser"] = "%1$s поджарен лазерным барьером"
EN[f"death.attack.{MOD}.laser.player"] = "%1$s was fried by a laser barrier whilst fighting %2$s"
RU[f"death.attack.{MOD}.laser.player"] = "%1$s поджарен лазерным барьером, сражаясь с %2$s"
for _k, (_en, _ru) in SIGNS.items():
    EN[f"sign.{MOD}.{_k}"], RU[f"sign.{MOD}.{_k}"] = _en, _ru
for _book, _pages in (("oinstein_journal", JOURNAL_PAGES), ("oinstein_orders", ORDERS_PAGES), ("oinstein_notes", NOTES_PAGES),
                      ("oinstein_clearance", CLEARANCE_PAGES), ("oinstein_final", FINAL_PAGES)):
    for _i, (_en, _ru) in enumerate(_pages):
        EN[f"book.{MOD}.{_book}.page_{_i}"], RU[f"book.{MOD}.{_book}.page_{_i}"] = _en, _ru
EN.update({f"book.{MOD}.oinstein_journal.title": "Dr. Oinstein's Lab Journal",
           f"book.{MOD}.oinstein_orders.title": "Standing Orders", f"book.{MOD}.oinstein_notes.title": "Lab Notes",
           f"book.{MOD}.oinstein_clearance.title": "Security Clearance Memo",
           f"book.{MOD}.oinstein_final.title": "Dr. Oinstein's Final Entry"})
RU.update({f"book.{MOD}.oinstein_journal.title": "Лабораторный журнал д-ра Ойнштайна",
           f"book.{MOD}.oinstein_orders.title": "Постоянный приказ", f"book.{MOD}.oinstein_notes.title": "Лабораторные заметки",
           f"book.{MOD}.oinstein_clearance.title": "Памятка о допуске",
           f"book.{MOD}.oinstein_final.title": "Последняя запись д-ра Ойнштайна"})
EN.update({f"structure.{MOD}.oinstein_complex": "Oinstein Institute"})
RU.update({f"structure.{MOD}.oinstein_complex": "Институт Ойнштайна"})


# =====================================================================================================================
# Outposts (G = 1: y = 0 foundation, y = 1 replaces the surface)
# =====================================================================================================================

def watchtower(s, x0, z0, top, ladder_side="east"):
    """A 5x5 steel watchtower: four legs, a grated platform at y=top with a railing, a searchlight and a ladder."""
    G = s.G
    for (x, z) in ((x0, z0), (x0 + 4, z0), (x0, z0 + 4), (x0 + 4, z0 + 4)):
        s.fill(x, G, z, x, top - 1, z, RSTEEL_S)
    for y in range(G + 3, top, 3):          # cross bracing
        for x in range(x0 + 1, x0 + 4):
            s.set(x, y, z0, chain("x"))
            s.set(x, y, z0 + 4, chain("x"))
        for z in range(z0 + 1, z0 + 4):
            s.set(x0, y, z, chain("z"))
            s.set(x0 + 4, y, z, chain("z"))
    s.fill(x0, top, z0, x0 + 4, top, z0 + 4, GRATE)
    s.ring(x0, z0, x0 + 4, z0 + 4, top + 1, bars)
    s.fill(x0 + 1, top + 1, z0 + 1, x0 + 3, top + 3, z0 + 3, S_AIR)
    for (x, z) in ((x0, z0), (x0 + 4, z0), (x0, z0 + 4), (x0 + 4, z0 + 4)):
        s.fill(x, top + 1, z, x, top + 3, z, RSTEEL_S)
    for (x, z) in ((x0, z0), (x0 + 4, z0), (x0, z0 + 4), (x0 + 4, z0 + 4)):
        s.set(x, top + 4, z, V("smooth_stone_slab", type="bottom", waterlogged=False))
    s.set(x0, top + 2, z0, LANTERN_SEA)            # searchlight head on the front corner
    s.set(x0 + 4, top + 2, z0, LANTERN_SEA)
    # ladder up the inside of one leg: the ladder hangs on the leg, the platform has a hatch above it
    lx, lz = x0 + 1, z0 + 4
    for y in range(G + 1, top + 1):
        s.set(lx, y, lz, V("ladder", facing="east", waterlogged=False))
    s.protect.add((lx, top, lz))
    s.set(lx, top + 1, lz, S_AIR)
    s.mob(x0 + 2, top + 1, z0 + 2, SENTRY)




def gate(s, x, y, z, facing):
    """The cage gate: a closed fence gate under an open bar; the captives walk free once a player opens it."""
    s.set(x, y, z, V("dark_oak_fence_gate", facing=facing, in_wall=False, open=False, powered=False))
    s.set(x, y + 1, z, S_AIR)
    s.protect.add((x, y, z))


def cage(s, x0, z0, w=4, d=4, captives=1):
    G = s.G
    s.fill(x0, G, z0, x0 + w - 1, G, z0 + d - 1, GRATE)
    for y in range(G + 1, G + 4):
        s.ring(x0, z0, x0 + w - 1, z0 + d - 1, y, bars)
    for (x, z) in ((x0, z0), (x0 + w - 1, z0), (x0, z0 + d - 1), (x0 + w - 1, z0 + d - 1)):
        s.fill(x, G + 1, z, x, G + 3, z, RSTEEL_S)
    s.fill(x0 + 1, G + 1, z0 + 1, x0 + w - 2, G + 3, z0 + d - 2, S_AIR)
    s.fill(x0, G + 4, z0, x0 + w - 1, G + 4, z0 + d - 1, RSTEEL_S)
    gate(s, x0 + 1, G + 1, z0, "north")
    for i in range(captives):
        s.captive(x0 + 1 + i % (w - 2), G + 1, z0 + 1 + (i // (w - 2)) % (d - 2))


def truck(s, x0, z0, facing_north=True):
    """A 1950s flatbed truck (3 wide, 8 long, cab at the north end) loaded with crates."""
    G = s.G
    for z in range(z0, z0 + 8):
        s.set(x0 + 1, G + 1, z, IRON)
        for x in (x0, x0 + 2):
            s.set(x, G + 1, z, BCON if z - z0 in (1, 2, 5, 6) else S_AIR)
        for x in range(x0, x0 + 3):
            s.set(x, G + 2, z, RCON if z - z0 < 3 else RSTEEL_S)
    for x in range(x0, x0 + 3):
        s.set(x, G + 3, z0, GLASS)
        s.set(x, G + 3, z0 + 1, RCON)
        s.set(x, G + 3, z0 + 2, RCON)
        s.set(x, G + 4, z0 + 1, RCON)
        s.set(x, G + 4, z0 + 2, RCON)
    s.set(x0 + 1, G + 4, z0, RCON)
    s.set(x0, G + 2, z0 - 1, V("end_rod", facing="north"))
    s.set(x0 + 2, G + 2, z0 - 1, V("end_rod", facing="north"))
    s.set(x0, G + 3, z0 + 4, st("cargo_crate"))
    s.set(x0 + 2, G + 3, z0 + 4, st("cargo_crate"))
    s.set(x0 + 1, G + 3, z0 + 6, st("cargo_crate"))
    s.set(x0, G + 3, z0 + 7, barrel_state("chests/oinstein_outpost"))
    s.set(x0 + 2, G + 3, z0 + 6, st("cargo_crate"))
    s.set(x0, G + 4, z0 + 4, st("cargo_crate"))


def build_capture_camp():
    """A capture camp: a steel palisade, cages full of captive tribesmen, a watchtower with a sentry, a supply
    truck and crate depot, and a guard hut with the standing orders."""
    W, D = 25, 24
    s = Base("oinstein_capture_camp", (W, 14, D), seed=8101, ground=1)
    G = s.G
    rnd = s.rnd
    s.fill(0, 0, 1, W - 1, 0, D - 1, CON)
    for x in range(W):
        for z in range(1, D):
            if rnd.random() < 0.55:
                s.set(x, G, z, PACKED if rnd.random() < 0.7 else CON)
    # palisade
    for x in range(W):
        for z in (1, D - 1):
            s.fill(x, G + 1, z, x, G + 3, z, bars())
            s.set(x, G + 4, z, chain("x"))
    for z in range(1, D):
        for x in (0, W - 1):
            s.fill(x, G + 1, z, x, G + 3, z, bars())
            s.set(x, G + 4, z, chain("z"))
    for x in range(0, W, 4):
        for z in (1, D - 1):
            s.fill(x, G + 1, z, x, G + 4, z, RSTEEL_S)
    for z in range(1, D, 4):
        for x in (0, W - 1):
            s.fill(x, G + 1, z, x, G + 4, z, RSTEEL_S)
    for z in (1, D - 1):
        for x in (0, W - 1):
            s.fill(x, G + 1, z, x, G + 4, z, RSTEEL_S)
    # the gate (north, 3 wide) between hazard posts
    gx = W // 2
    s.fill(gx - 1, G + 1, 1, gx + 1, G + 4, 1, S_AIR)
    for x in (gx - 2, gx + 2):
        s.fill(x, G + 1, 1, x, G + 5, 1, HSTEEL_S)
    s.fill(gx - 2, G + 5, 1, gx + 2, G + 5, 1, HSTEEL_S)
    s.set(gx, G + 5, 0, sign("north", SIGN_RESTRICTED))
    s.set(gx - 3, G + 2, 0, wall_banner("north"))
    s.fill(gx - 3, G + 1, 1, gx - 3, G + 3, 1, RSTEEL_S)
    s.set(gx + 3, G + 2, 0, wall_banner("north"))
    s.fill(gx + 3, G + 1, 1, gx + 3, G + 3, 1, RSTEEL_S)
    s.protect_box(gx - 1, G + 1, 0, gx + 1, G + 3, 2)
    # cages along the east side
    for i, z in enumerate((4, 9, 14)):
        cage(s, 18, z, 4, 4, captives=2 if i == 1 else 1)
    # watchtower in the north-west corner
    watchtower(s, 2, 3, G + 7)
    # truck and crate depot (south-west)
    truck(s, 3, 13)
    for (x, z, h) in ((8, 19, 2), (9, 19, 1), (8, 20, 1), (10, 20, 3), (11, 20, 1)):
        s.fill(x, G + 1, z, x, G + h, z, st("cargo_crate"))
    s.set(9, G + 1, 20, barrel_state("chests/oinstein_outpost"))
    # guard hut (south-east): concrete, a desk, the orders on a lectern, a chest
    s.box(15, G + 1, 18, 22, G + 3, 22, CON, floor=None, roof=RSTEEL_S)
    s.fill(15, G, 18, 22, G, 22, CON)
    s.fill(18, G + 1, 18, 18, G + 2, 18, S_AIR)
    s.protect_box(18, G + 1, 17, 18, G + 2, 19)
    s.set(19, G + 2, 18, GLASS)
    s.set(16, G + 2, 18, GLASS)
    s.set(16, G + 1, 21, lectern("east", "oinstein_orders"))
    s.set(21, G + 1, 21, locker("west", "chests/oinstein_keycard_a"))     # the commandant's locker: card A
    s.set(21, G + 1, 19, computer("west"))
    s.set(18, G + 3, 20, light_on())
    poster(s, 19, G + 1, 21, "oinstein_poster_better_ape", "north")
    s.set(17, G + 1, 17, wall_banner("north"))
    # forces
    s.mob(gx - 1, G + 1, 3, NOVUS)
    s.mob(gx + 1, G + 1, 3, NOVUS)
    s.set(13, G + 1, 6, standing_banner(rnd.randrange(16)))
    s.set(13, G + 1, 8, campfire(False))
    return s


def build_field_lab():
    """A half-buried concrete field laboratory: specimen tanks (one holds a tribesman), a brain-jar shelf, computer
    banks and a Tesla coil; reached down a stair trench through an airlock door."""
    W, D, G = 17, 20, 3
    s = Base("oinstein_field_lab", (W, 11, D), seed=8202, ground=G)
    rnd = s.rnd
    x0, x1, z0, z1 = 1, 15, 5, 19
    s.fill(x0, 0, z0, x1, 0, z1, CON)
    s.box(x0, 1, z0, x1, 4, z1, CON, roof=CON)
    s.ring(x0, z0, x1, z1, 5, HSTEEL_S)
    s.fill(x0 + 1, 6, z0 + 1, x1 - 1, 6, z1 - 1, S_AIR)
    for x in range(x0, x1 + 1, 2):        # hazard band below the roof and a concrete berm
        s.set(x, 4, z0, YCON)
    s.fill(x0 + 1, 0, z0 + 1, x1 - 1, 0, z1 - 1, LCON)
    for z in range(z0 + 1, z1):
        for x in range(x0 + 1, x1):
            if (x + z) % 2:
                s.set(x, 0, z, WCON)
    # earth berm against the outside walls (camouflage)
    for z in range(z0 - 1, z1 + 2):
        for x in range(x0 - 1, x1 + 2):
            if s.name_at(x, 1, z) is None and s.inside(x, 1, z) and z >= z0:
                for y in range(1, G + 1):
                    s.set(x, y, z, st("venus_soil"))
                s.set(x, G + 1, z, st("venus_moss")) if rnd.random() < 0.6 else None
    # stair trench to the door (north)
    dx = 8
    for x in (dx - 2, dx + 2):
        s.fill(x, 0, 0, x, G, z0 - 1, CON)
    for k, (z, y) in enumerate(((0, 3), (1, 2), (2, 1))):
        for x in range(dx - 1, dx + 2):
            s.fill(x, 0, z, x, y - 1, z, CON)
            s.set(x, y, z, V("polished_andesite_stairs", facing="south", half="bottom", shape="straight",
                                 waterlogged=False))
            s.fill(x, y + 1, z, x, y + 4, z, S_AIR)
    for z in (3, 4):
        for x in range(dx - 1, dx + 2):
            s.set(x, 0, z, CON)
            s.fill(x, 1, z, x, 4, z, S_AIR)
    s.fill(dx - 1, 5, 3, dx + 1, 5, 4, HSTEEL_S)
    s.set(dx, 1, z0, st("airlock_door", facing="north", half="lower", hinge="left", open=False))
    s.set(dx, 2, z0, st("airlock_door", facing="north", half="upper", hinge="left", open=False))
    s.set(dx - 1, 3, z0 - 1, sign("north", SIGN_RESTRICTED))
    s.set(dx + 1, 3, z0 - 1, wall_banner("north"))
    s.protect_box(dx - 1, 1, 0, dx + 1, 4, z0 + 1)
    # inside: specimen tanks along the west wall
    for z in (8, 11, 14):
        s.set(2, 1, z, IRON)
        s.set(2, 4, z, IRON)
        specimen = z == 14
        for y in (2, 3):
            s.set(2, y, z, S_AIR if specimen else V("water", level=0))
            s.set(3, y, z, V("lime_stained_glass") if specimen else GLASS)
            s.set(2, y, z - 1, GLASS)
            s.set(2, y, z + 1, GLASS)
        s.set(3, 1, z, RSTEEL_S)
        s.set(3, 4, z, RSTEEL_S)
        if specimen:
            s.set(2, 2, z, S_AIR)
            s.set(2, 3, z, S_AIR)
            s.captive(2, 2, z, specimen=True)
    # brain-jar shelf (east wall)
    for z in range(8, 15):
        s.set(14, 2, z, V("smooth_stone_slab", type="top", waterlogged=False))
        if z % 2 == 0:
            s.set(14, 3, z, JAR_S)
        s.set(14, 1, z, st("tape_archive", facing="west") if z % 3 == 0 else S_AIR)
    # computers and the coil
    for x in (10, 11, 12):
        s.set(x, 1, z0 + 1, computer("south"))
    s.set(8, 1, 12, RSTEEL_S)
    s.set(8, 2, 12, TESLA_S)
    s.set(6, 1, 17, st("lab_sink", facing="north"))
    s.set(5, 1, 18, lectern("north", "oinstein_journal"))
    s.set(10, 1, 18, chest_state("north", "chests/oinstein_lab"))
    s.set(11, 1, 18, st("cargo_crate"))
    s.set(14, 1, 18, locker("west", "chests/oinstein_keycard_c", "researcher_locker"))   # card C
    s.set(12, 1, 18, V("smooth_stone_slab", type="double", waterlogged=False))   # operating table
    s.set(12, 1, 17, V("smooth_stone_slab", type="double", waterlogged=False))
    for (x, z) in ((5, 9), (11, 9), (5, 15), (11, 15)):
        s.set(x, 4, z, light_on())
    poster(s, 9, 2, 18, "oinstein_poster_insignia", "north")
    s.set(13, 2, 18, wall_banner("north"))
    s.mob(8, 1, 9, SAPIENS)
    s.mob(dx + 3, G + 1, 2, NOVUS)
    # roof furniture: green skylights over the lab, vent stacks, a radio mast, sandbagged hatches
    for x in range(5, 12):
        for z in (10, 11, 13, 14):
            s.set(x, 5, z, V("lime_stained_glass"))
    for (x, z) in ((3, 16), (13, 12)):
        s.set(x, 5, z, HSTEEL_S)
    for (x, z) in ((4, 8), (12, 16)):
        s.fill(x, 6, z, x, 7, z, pipe("y"))
    for y in range(6, 10):
        s.set(13, y, 8, V("lightning_rod", facing="up", powered=False, waterlogged=False) if y == 9 else IRON if y == 6
              else chain("y"))
    s.set(13, 10, 8, V("end_rod", facing="up"))
    return s


def build_relay_pylon():
    """A relay pylon: a steel lattice tower crowned by a Tesla coil and a red beacon, a generator shed, cables, a
    fenced yard and two sentries."""
    W, D = 17, 17
    s = Base("oinstein_relay_pylon", (W, 28, D), seed=8303, ground=1)
    G = s.G
    c = 8
    s.fill(0, 0, 0, W - 1, 0, D - 1, CON)
    s.fill(c - 3, G, c - 3, c + 3, G, c + 3, CON)
    top = G + 20
    tiers = ((G + 1, G + 6, 3), (G + 7, G + 13, 2), (G + 14, top - 1, 1))
    for (y0, y1, hw) in tiers:
        for y in range(y0, y1 + 1):
            for (x, z) in ((c - hw, c - hw), (c + hw, c - hw), (c - hw, c + hw), (c + hw, c + hw)):
                s.set(x, y, z, RSTEEL_S)
        # a steel collar at the top of each tier ties the legs to the narrower ones above
        s.ring(c - hw, c - hw, c + hw, c + hw, y1, RSTEEL_S)
        for y in range(y0 + 2, y1 - 1, 3):
            for t in range(-hw + 1, hw):
                for (x, z, a) in ((c + t, c - hw, "x"), (c + t, c + hw, "x"), (c - hw, c + t, "z"), (c + hw, c + t, "z")):
                    s.set(x, y, z, bars())
    for (x, z) in ((c - 3, c - 3), (c + 3, c - 3), (c - 3, c + 3), (c + 3, c + 3)):
        s.set(x, G, z, HSTEEL_S)
    s.fill(c - 1, top, c - 1, c + 1, top, c + 1, GRATE)
    s.ring(c - 1, c - 1, c + 1, c + 1, top + 1, bars)
    s.set(c, top + 1, c, RSTEEL_S)
    s.set(c, top + 2, c, TESLA_S)
    s.set(c - 1, top + 1, c - 1, V("redstone_block"))
    s.set(c - 1, top + 2, c - 1, lamp())
    s.set(c + 1, top + 1, c + 1, V("redstone_block"))
    s.set(c + 1, top + 2, c + 1, lamp())
    for y in range(top + 3, top + 6):
        s.set(c, y, c, V("lightning_rod", facing="up", powered=False, waterlogged=False) if y == top + 5 else chain("y"))
    s.set(c + 1, top + 1, c, S_AIR)
    s.mob(c + 1, top + 1, c, SENTRY)
    # generator shed (south-west) and cables to the pylon
    s.box(1, G + 1, 11, 6, G + 3, 15, CON, roof=RSTEEL_S)
    s.fill(1, G, 11, 6, G, 15, CON)
    s.fill(4, G + 1, 11, 4, G + 2, 11, S_AIR)
    s.protect_box(4, G + 1, 10, 4, G + 2, 12)
    s.set(3, G + 1, 13, st("reactor_core", lit=True))
    s.set(2, G + 1, 14, computer("east"))
    s.set(5, G + 1, 14, barrel_state("chests/oinstein_outpost"))
    s.set(5, G + 1, 12, locker("west", "chests/oinstein_keycard_b"))      # the shed locker: card B
    s.set(2, G + 1, 12, V("blast_furnace", facing="east", lit=False))
    s.set(4, G + 3, 13, light_on())
    s.set(3, G + 2, 10, sign("north", SIGN_DANGER))
    for x in range(4, c - 2):
        s.set(x, G + 5, 11, chain("x"))
    s.set(3, G + 4, 11, RSTEEL_S)
    s.set(3, G + 5, 11, IRON)
    # fence with a gate on the north side
    for x in range(W):
        for z in (0, D - 1):
            s.fill(x, G + 1, z, x, G + 2, z, bars())
    for z in range(D):
        for x in (0, W - 1):
            s.fill(x, G + 1, z, x, G + 2, z, bars())
    for x in range(0, W, 4):
        for z in (0, D - 1):
            s.fill(x, G + 1, z, x, G + 3, z, RSTEEL_S)
    for z in range(0, D, 4):
        for x in (0, W - 1):
            s.fill(x, G + 1, z, x, G + 3, z, RSTEEL_S)
    s.fill(c - 1, G + 1, 0, c + 1, G + 2, 0, S_AIR)
    s.fill(12, G + 1, 12, 12, G + 1, 12, S_AIR)
    s.set(c + 2, G + 1, 2, standing_banner(8))
    s.mob(10, G + 1, 13, AUTOMATON)
    return s


def build_checkpoint():
    """A road checkpoint: a striped road, a guard booth with windows and a searchlight, a boom barrier, hazard
    barricades, and its guards."""
    W, D = 15, 13
    s = Base("oinstein_checkpoint", (W, 9, D), seed=8404, ground=1)
    G = s.G
    s.fill(0, 0, 0, W - 1, 0, D - 1, CON)
    for z in range(D):                    # the road runs north-south, x 5..9
        for x in range(5, 10):
            s.set(x, G, z, CON if x not in (5, 9) else LCON)
        if z % 3 != 2:
            s.set(7, G, z, YCON)
    # booth (west)
    s.box(1, G + 1, 4, 3, G + 3, 7, CON, roof=RSTEEL_S)
    s.fill(1, G, 4, 3, G, 7, CON)
    for z in (5, 6):
        s.set(3, G + 2, z, pane())
        s.set(1, G + 2, z, pane())
    s.fill(2, G + 1, 7, 2, G + 2, 7, S_AIR)
    s.protect_box(2, G + 1, 7, 2, G + 2, 8)
    s.set(2, G + 1, 5, computer("east"))
    s.set(2, G + 1, 6, lectern("south", "oinstein_clearance"))   # which outpost keeps which card
    s.set(2, G + 3, 6, light_on())
    s.set(2, G + 4, 5, RSTEEL_S)
    s.set(2, G + 5, 5, LANTERN_SEA)
    s.set(2, G + 2, 3, sign("north", SIGN_CHECKPOINT, color="black", glow=False))
    s.set(1, G + 1, 8, barrel_state("chests/oinstein_outpost"))
    # boom barrier across the road
    s.fill(4, G + 1, 6, 4, G + 2, 6, HSTEEL_S)
    for x in range(5, 10):
        s.set(x, G + 2, 6, V("end_rod", facing="east"))
    s.fill(10, G + 1, 6, 10, G + 1, 6, HSTEEL_S)
    # barricades (east) and a sentry post
    for (x, z) in ((11, 2), (12, 2), (11, 10), (12, 10), (13, 6)):
        s.set(x, G + 1, z, HSTEEL_S)
    s.fill(11, G + 1, 5, 13, G + 1, 7, RSTEEL_S)
    s.fill(11, G + 2, 5, 13, G + 2, 7, GRATE)
    s.ring(11, 5, 13, 7, G + 3, bars)
    s.set(12, G + 3, 6, S_AIR)
    s.mob(12, G + 3, 6, SENTRY)
    s.set(13, G + 1, 8, standing_banner(12))
    s.mob(6, G + 1, 3, NOVUS)
    return s


# =====================================================================================================================
# World generation
# =====================================================================================================================
OUTPOSTS = {
    # name: (builder, ground layers G, weight)
    "oinstein_capture_camp": (build_capture_camp, 1, 3),
    "oinstein_field_lab": (build_field_lab, 3, 3),
    "oinstein_relay_pylon": (build_relay_pylon, 1, 2),
    "oinstein_checkpoint": (build_checkpoint, 1, 2),
}
OUTPOST_BIOMES = ("venus_jungle", "venus_cycad_plains", "venus_fern_swamp", "venus_volcanic_highlands")
LAND_BIOMES = ("venus_jungle", "venus_cycad_plains", "venus_fern_swamp", "venus_volcanic_highlands",
               "venus_glowcap_hollows")
COMPLEX = "oinstein_complex"


# Mobs cleared by the coordinator for structure spawn_overrides (a missing entity id would break registry loading).
# OINSTEIN_SPAWNS=1 / 0 forces all / none.
SPAWNS_ENABLED = set(MOBS)


def entity_registered(name):
    import re
    pat = re.compile(r'register\(\s*"' + re.escape(name) + '"')
    for root, _dirs, files in os.walk(JAVA):
        for f in files:
            if f.endswith(".java"):
                with open(os.path.join(root, f), encoding="utf-8") as fh:
                    if pat.search(fh.read()):
                        return True
    return False


def registered_entities():
    flag = os.environ.get("OINSTEIN_SPAWNS")
    if flag == "1":
        return set(MOBS)
    if flag == "0":
        return set()
    return {m for m in SPAWNS_ENABLED if entity_registered(m.split(":")[1])}


def spawn_overrides(weights):
    present = registered_entities()
    spawns = [{"type": m, "weight": w, "minCount": lo, "maxCount": hi} for m, (w, lo, hi) in weights.items()
              if m in present]
    if not spawns:
        return {}
    return {"monster": {"bounding_box": "piece", "spawns": spawns}}


# Reinforcements inside the Institute only; OinsteinSpawns.java lets one in four through and caps the garrison
# at 8 of his forces within 48 blocks.
COMPLEX_SPAWNS = {SENTRY: (3, 1, 1), AUTOMATON: (3, 1, 1), NOVUS: (5, 1, 1), SAPIENS: (2, 1, 1)}


def wg(kind, name, obj):
    write_json(os.path.join(DATA, "worldgen", kind, name + ".json"), obj)


def jigsaw_structure(name, pool, biomes_tag, start_height, adaptation, overrides, dry_search=0, sea_margin=0, extra=None):
    extra_pieces = {"extra_pieces": extra} if extra else {}
    wg("structure", name, extra_pieces | {
        "type": f"{MOD}:dry_jigsaw", "dry_search_chunks": dry_search,
        # the Institute's solid paving and beard_box keep a low site dry; the outposts must stay above the sea
        # (the half-buried field lab by its own depth, or the aquifer floods its stair trench)
        "sea_level_margin": sea_margin, "biomes": f"#{MOD}:has_structure/{biomes_tag}", "step": "surface_structures",
        "spawn_overrides": overrides, "terrain_adaptation": adaptation, "start_pool": f"{MOD}:{pool}", "size": 1,
        "start_height": {"absolute": start_height}, "project_start_to_heightmap": "WORLD_SURFACE_WG",
        "max_distance_from_center": 80, "use_expansion_hack": False})


def single_pool(name, location, processors="oinstein_wear"):
    wg("template_pool", name, {"elements": [{"weight": 1, "element": {
        "element_type": "minecraft:single_pool_element", "location": f"{MOD}:{location}",
        "processors": f"{MOD}:{processors}", "projection": "rigid"}}], "fallback": "minecraft:empty"})


def zones(*pairs):
    return [{"other_set": f"{MOD}:{s}", "chunk_count": n} for s, n in pairs]


def worldgen():
    wg("processor_list", "oinstein_wear", {"processors": [
        {"processor_type": "minecraft:rule", "rules": [R_.rule(RSTEEL, RSTEEL, 0.0)]},
        {"processor_type": "minecraft:protected_blocks", "value": "#minecraft:features_cannot_replace"},
        # the station furniture does not rotate itself: turn its facing with the structure (posters, panels...)
        {"processor_type": f"{MOD}:furniture_facing"}]})
    tag("worldgen/biome/has_structure/oinstein_outpost", [P(b) for b in OUTPOST_BIOMES], namespace=MOD)
    entries = []
    for name, (_fn, G, weight) in OUTPOSTS.items():
        single_pool(f"{name}/start", f"oinstein/{name}")
        # outposts keep only their placed garrison: no spawn overrides (a solo player should be able to clear one)
        jigsaw_structure(name, f"{name}/start", "oinstein_outpost", -G, "beard_thin", {}, sea_margin=G - 1)
        entries.append({"structure": f"{MOD}:{name}", "weight": weight})
    wg("structure_set", "oinstein_outposts", {"structures": entries, "placement": {
        "type": f"{MOD}:exclusive_spread", "spacing": 56, "separation": 24, "salt": 731940117,
        "exclusion_zones": zones(("tribal_camps", 4), ("venusian_pyramids", 6), ("venusian_ziggurats", 6),
                                 ("venusian_ruined_villages", 6), ("oinstein_institute", 12))}})
    # the Institute: one per world, a journey away from spawn
    tag("worldgen/biome/has_structure/oinstein_complex", [P(b) for b in LAND_BIOMES] + [P("venus_steaming_sea")],
        namespace=MOD)
    # plains and jungle: the paving keeps their trees out of the yard (highland cinder cones would not care)
    tag("worldgen/biome/oinstein_complex_preferred", [P(b) for b in ("venus_cycad_plains", "venus_jungle")],
        namespace=MOD)
    single_pool(f"{COMPLEX}/start", f"oinstein/{COMPLEX}")
    # the lower laboratory: a template piece attached under the start piece (no terrain adaptation, its own shell)
    lab = [{"template": f"{MOD}:oinstein/{LAB}", "offset": list(LAB_INFO["origin"])}]
    jigsaw_structure(COMPLEX, f"{COMPLEX}/start", COMPLEX, -1, "beard_box", spawn_overrides(COMPLEX_SPAWNS), dry_search=2,
                     sea_margin=-64, extra=lab)
    wg("structure_set", "oinstein_institute", {"structures": [{"structure": f"{MOD}:{COMPLEX}", "weight": 1}],
                                               "placement": {"type": "minecraft:concentric_rings", "distance": 12,
                                                             "spread": 1, "count": 1, "salt": 731940118,
                                                             "preferred_biomes": f"#{MOD}:oinstein_complex_preferred"}})


TEMPLATES = {f"oinstein/{n}": fn for n, (fn, _g, _w) in OUTPOSTS.items()}


def clear_above(s, layers=3):
    """Explicit air over the open ground of a template: vegetation that a neighbouring chunk's features placed on the
    terrain before this part of the structure was built would otherwise stand on the steel and concrete."""
    columns = {(x, z) for (x, y, z) in s.b}
    for (x, z) in columns:
        if (x, s.G, z) not in s.b and (x, s.G - 1, z) in s.b:
            s.b[(x, s.G, z)] = PACKED      # bare ground over a foundation: trodden earth, not the old (planted) topsoil
        for y in range(s.G + 1, s.G + 1 + layers):
            if s.inside(x, y, z) and (x, y, z) not in s.b:
                s.b[(x, y, z)] = S_AIR


def finish(s):
    if not getattr(s, "underground", False):
        clear_above(s)
    connect_panes(s)
    audit(s)
    return s


def generate():
    write_block_textures()
    write_models()
    write_keycard_assets()
    write_data()
    total = 0
    for path, fn in TEMPLATES.items():
        total += write_template(finish(fn()), path)
    worldgen()
    write_prison_anchors()
    print(f"oinstein: generated {len(TEMPLATES)} templates, {total} blocks; spawn overrides for "
          f"{sorted(m.split(':')[1] for m in registered_entities()) or 'none'}")


# =====================================================================================================================
# The Oinstein Institute (G = 1)
# =====================================================================================================================

def hazard_band(s, x0, z0, x1, z1, y):
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if x in (x0, x1) or z in (z0, z1):
                s.set(x, y, z, YCON if ((x + z) // 2) % 2 == 0 else BCON)


def guard_tower(s, x0, z0, size, top, lights=True, sentry=True):
    """A concrete guard tower with a hazard band, an open steel platform, a railing, searchlights and a sentry."""
    G = s.G
    x1, z1 = x0 + size - 1, z0 + size - 1
    s.fill(x0, G, z0, x1, top - 1, z1, CON)
    s.fill(x0 + 1, G + 1, z0 + 1, x1 - 1, top - 1, z1 - 1, S_AIR)
    hazard_band(s, x0, z0, x1, z1, G + 1)
    s.ring(x0, z0, x1, z1, top - 2, WCON)
    s.fill(x0, top, z0, x1, top, z1, GRATE)
    s.ring(x0, z0, x1, z1, top + 1, bars)
    for (x, z) in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)):
        s.fill(x, top + 1, z, x, top + 2, z, RSTEEL_S)
        if lights:
            s.set(x, top + 3, z, LANTERN_SEA)
    # a ladder up the inside
    for y in range(G + 1, top + 1):
        s.set(x0 + 1, y, z0 + 1, V("ladder", facing="south", waterlogged=False))
    s.set(x0 + 1, top + 1, z0 + 1, S_AIR)
    if sentry:
        s.mob(x0 + size // 2, top + 1, z0 + size // 2, SENTRY)


def cooling_tower(s, cx, cz, y0, height, r_base, r_waist, r_top):
    """A hyperboloid concrete cooling tower on open arches, with smoking fires (signal campfires) in its basin."""
    def radius(h):
        t = h / height
        waist = 0.55
        if t < waist:
            return r_waist + (r_base - r_waist) * ((waist - t) / waist) ** 2
        return r_waist + (r_top - r_waist) * ((t - waist) / (1 - waist)) ** 2

    R = int(r_base) + 2
    for h in range(height):
        r = radius(h)
        y = y0 + h
        for x in range(cx - R, cx + R + 1):
            for z in range(cz - R, cz + R + 1):
                d = math.hypot(x - cx, z - cz)
                if abs(d - r) <= 0.75:
                    if h < 3 and int((math.atan2(z - cz, x - cx) + math.pi) * 8 / math.pi) % 2 == 0:
                        continue                         # arches at the foot
                    c = RCON if height - 5 <= h < height - 3 else WCON if h % 6 == 0 else LCON
                    s.set(x, y, z, c)
                elif d < r - 0.75:
                    s.set(x, y, z, S_AIR)
    G = s.G
    for x in range(cx - R, cx + R + 1):
        for z in range(cz - R, cz + R + 1):
            d = math.hypot(x - cx, z - cz)
            if d < 4.5:
                s.set(x, G, z, V("water", level=0))
                s.set(x, G - 1, z, CON)
            elif d < r_base - 1:
                s.set(x, G, z, CON)
    for i in range(8):
        a = i * math.pi / 4
        x, z = round(cx + 6 * math.cos(a)), round(cz + 6 * math.sin(a))
        s.set(x, G, z, V("hay_block", axis="y"))
        s.set(x, G + 1, z, campfire(True))


def smokestack(s, x0, z0, top):
    G = s.G
    s.fill(x0, G, z0, x0 + 2, top, z0 + 2, RCON)
    for y in range(G, top + 1):
        if (y // 4) % 2 == 1:
            s.ring(x0, z0, x0 + 2, z0 + 2, y, WCON)
    s.fill(x0 + 1, G + 1, z0 + 1, x0 + 1, top, z0 + 1, S_AIR)
    s.set(x0 + 1, G, z0 + 1, V("hay_block", axis="y"))
    s.set(x0 + 1, G + 1, z0 + 1, campfire(True))
    s.ring(x0, z0, x0 + 2, z0 + 2, top, BCON)
    s.set(x0, top - 6, z0 + 1, V("redstone_block"))


def pipeline(s, pts, y, support_every=6):
    """Twin chrome pipes along a polyline of (x, z) corners at height y, on steel trestles."""
    G = s.G
    for (xa, za), (xb, zb) in zip(pts, pts[1:]):
        if xa == xb:
            for z in range(min(za, zb), max(za, zb) + 1):
                for dx in (0, 1):
                    if s.name_at(xa + dx, y, z) in (None, AIR):
                        s.set(xa + dx, y, z, pipe("z"))
                if (z - min(za, zb)) % support_every == 0:
                    for dx in (0, 1):
                        for yy in range(G + 1, y):
                            if s.name_at(xa + dx, yy, z) in (None, AIR):
                                s.set(xa + dx, yy, z, RSTEEL_S if dx == 0 else S_AIR)
        else:
            for x in range(min(xa, xb), max(xa, xb) + 1):
                for dz in (0, 1):
                    if s.name_at(x, y, za + dz) in (None, AIR):
                        s.set(x, y, za + dz, pipe("x"))
                if (x - min(xa, xb)) % support_every == 0:
                    for yy in range(G + 1, y):
                        if s.name_at(x, yy, za) in (None, AIR):
                            s.set(x, yy, za, RSTEEL_S)


def cage_wagon(s, x0, z, y):
    """A cage wagon standing on the track: grated floor, iron-bar cage, steel roof, a captive inside."""
    for x in range(x0, x0 + 5):
        for dz in (-1, 0, 1):
            s.set(x, y, z + dz, GRATE if dz == 0 or x in (x0, x0 + 4) else BCON)
    for yy in (y + 1, y + 2):
        s.ring(x0, z - 1, x0 + 4, z + 1, yy, bars)
        s.fill(x0 + 1, yy, z, x0 + 3, yy, z, S_AIR)
    for x in range(x0, x0 + 5):
        for dz in (-1, 0, 1):
            s.set(x, y + 3, z + dz, RSTEEL_S)
    gate(s, x0 + 2, y + 1, z - 1, "north")
    s.captive(x0 + 2, y + 1, z)


def build_complex():
    """The Oinstein Institute: a walled industrial compound with guard towers and searchlights, a reactor hall,
    smokestacks and a cooling tower, pipelines, a loading yard with cage wagons and a gantry crane, barracks and an
    armory, and in the middle the great entrance hall of the (future) underground laboratory - its portal and the
    lift inside both sealed by laser barriers, the foyer visible through them."""
    N, H, G = 96, 34, 1
    s = Base(COMPLEX, (N, H, N), seed=9001, ground=G)
    rnd = s.rnd
    s.fill(0, 0, 0, N - 1, 0, N - 1, CON)
    # yard paving: concrete slabs in a 4-block grid
    for x in range(N):
        for z in range(N):
            s.set(x, G, z, LCON if (x % 8 in (0, 7) or z % 8 in (0, 7)) else CON)
            if rnd.random() < 0.05:
                s.set(x, G, z, PACKED)
    # the access road from the gate to the hall
    for z in range(0, 41):
        for x in range(43, 53):
            s.set(x, G, z, BCON if x not in (43, 52) else YCON)
    # ------------------------------------------------------------ perimeter wall
    W0, W1 = 2, N - 3
    for y in range(G + 1, G + 9):
        for t in (0, 1):
            s.ring(W0 + t, W0 + t, W1 - t, W1 - t, y, CON if y > G + 1 else (YCON if t == 0 else CON))
    for i in range(W0, W1 + 1):
        for (x, z) in ((i, W0), (i, W1), (W0, i), (W1, i)):
            s.set(x, G + 1, z, YCON if (i // 2) % 2 == 0 else BCON)
            s.set(x, G + 7, z, WCON)
            s.set(x, G + 9, z, RSTEEL_S if i % 2 == 0 else S_AIR)
    for i in range(W0 + 1, W1):
        for (x, z) in ((i, W0 + 1), (i, W1 - 1), (W0 + 1, i), (W1 - 1, i)):
            s.set(x, G + 9, z, S_AIR)
    # towers: corners, mid-sides
    T = 6
    for (x, z) in ((0, 0), (N - T, 0), (0, N - T), (N - T, N - T), (0, 45), (N - T, 45), (45, N - T)):
        guard_tower(s, x, z, T, G + 14, sentry=z == 0)        # only the front corners are manned
    # ------------------------------------------------------------ the main gate (north, sealed)
    gx0, gx1 = 44, 51
    for (tx0, tx1) in ((37, 43), (52, 58)):
        s.fill(tx0, G, 1, tx1, G + 16, 8, CON)
        s.fill(tx0 + 1, G + 1, 2, tx1 - 1, G + 15, 7, S_AIR)
        hazard_band(s, tx0, 1, tx1, 8, G + 1)
        s.ring(tx0, 1, tx1, 8, G + 12, WCON)
        s.fill(tx0, G + 17, 1, tx1, G + 17, 8, GRATE)
        s.ring(tx0, 1, tx1, 8, G + 18, bars)
        for (x, z) in ((tx0, 1), (tx1, 1)):
            s.set(x, G + 18, z, RSTEEL_S)
            s.set(x, G + 19, z, LANTERN_SEA)
        for y in range(G + 1, G + 18):
            s.set(tx0 + 1, y, 7, V("ladder", facing="north", waterlogged=False))
        s.set(tx0 + 1, G + 18, 7, S_AIR)
        s.mob((tx0 + tx1) // 2, G + 18, 4, SENTRY)
        for y in (G + 9, G + 10):
            for x in range(tx0 + 2, tx1 - 1):
                s.set(x, y, 1, TINT)
    s.fill(gx0 - 1, G + 1, 1, gx1 + 1, G + 12, 4, CON)          # gate block and lintel
    s.fill(gx0, G, 1, gx1, G + 6, 4, S_AIR)
    s.fill(gx0, G, 1, gx1, G, 8, HSTEEL_S)
    for x in range(gx0 - 1, gx1 + 2):
        s.set(x, G + 7, 1, HSTEEL_S)
    for y in range(G + 1, G + 8):
        s.set(gx0 - 1, y, 1, HSTEEL_S)
        s.set(gx1 + 1, y, 1, HSTEEL_S)
    for y in range(G + 1, G + 7):
        s.set(gx0, y, 2, EMITTER_S)
        s.set(gx1, y, 2, EMITTER_S)
        for x in range(gx0 + 1, gx1):
            s.set(x, y, 2, barrier("x"))
    for y in range(G + 1, G + 7):
        for x in range(gx0, gx1 + 1):
            s.set(x, y, 3, S_AIR)
            s.set(x, y, 4, S_AIR)
    s.set(gx0 + 2, G + 9, 0, sign("north", SIGN_RESTRICTED))
    s.set(gx1 - 2, G + 9, 0, sign("north", SIGN_SLOGAN, color="black", glow=False))
    s.set(gx0 + 3, G + 9, 0, wall_banner("north"))
    s.set(gx1 - 3, G + 9, 0, wall_banner("north"))
    s.fill(gx0 - 1, G + 9, 1, gx1 + 1, G + 11, 1, CON)
    s.set(gx0 - 2, G + 3, 0, sign("north", SIGN_DANGER))
    for x in (36, 59):
        s.set(x, G + 2, 1, S_AIR)
    poster(s, 35, G + 2, 1, "oinstein_poster_restricted", "north")
    poster(s, 60, G + 2, 1, "oinstein_poster_restricted", "north")
    poster(s, 33, G + 2, 1, "oinstein_poster_better_ape", "north")
    poster(s, 62, G + 2, 1, "oinstein_poster_insignia", "north")
    for x in (31, 64):
        s.set(x, G + 4, 1, wall_banner("north"))
    s.set(42, G + 2, 0, reader("north", "a"))          # clearance A switches the gate barrier off
    s.set(41, G + 2, 0, sign("north", SIGN_CARD["a"], color="black", glow=False))
    s.protect_box(gx0, G, 0, gx1, G + 6, 4)
    # ------------------------------------------------------------ the Institute hall (lab entrance)
    hx0, hx1, hz0, hz1, top = 32, 63, 40, 64, G + 15
    s.fill(hx0, G, hz0, hx1, top, hz1, CON)
    s.fill(hx0 + 1, G + 1, hz0 + 1, hx1 - 1, G + 9, hz1 - 1, S_AIR)
    for x in range(hx0, hx1 + 1):                 # facade bands and high windows
        for y in (G + 11, G + 12, G + 13):
            if 3 < x - hx0 < hx1 - hx0 - 3 and (x - hx0) % 3 != 0:
                s.set(x, y, hz0, TINT if y != G + 12 else V("black_stained_glass"))
        s.set(x, G + 10, hz0, WCON)
        s.set(x, top, hz0, HSTEEL_S)
        s.set(x, G + 1, hz0, YCON if (x // 2) % 2 == 0 else BCON)
    s.fill(hx0 + 1, G + 10, hz0 + 1, hx1 - 1, top - 1, hz1 - 1, S_AIR)
    s.fill(hx0 + 1, G + 10, hz0 + 1, hx1 - 1, G + 10, hz1 - 1, CON)      # upper floor slab
    s.fill(hx0 + 2, G + 10, hz0 + 4, hx1 - 2, G + 10, hz0 + 6, GLASS)    # gallery light well
    for x in range(hx0 + 2, hx1 - 1, 4):
        s.set(x, top - 1, hz0 + 8, light_on())
    # roof: steel edge, skylight, antenna array
    s.fill(hx0 + 6, top, hz0 + 8, hx1 - 6, top, hz1 - 6, GLASS)
    for x in (hx0 + 3, hx1 - 3):
        for y in range(top + 1, top + 8):
            s.set(x, y, hz1 - 3, chain("y") if y < top + 7 else V("lightning_rod", facing="up", powered=False,
                                                                     waterlogged=False))
        s.set(x, top + 1, hz1 - 3, IRON)
    s.set(hx0 + 16, top + 1, hz1 - 4, st("radar_scope", facing="north", lit=True))
    # the portal: a hazard-striped blast frame and the laser barrier
    px0, px1 = 42, 53
    s.fill(px0, G + 1, hz0, px1, G + 9, hz0, HSTEEL_S)
    s.fill(px0 + 1, G + 1, hz0, px1 - 1, G + 8, hz0, S_AIR)
    for y in range(G + 1, G + 9):
        s.set(px0 + 1, y, hz0, EMITTER_S)
        s.set(px1 - 1, y, hz0, EMITTER_S)
        for x in range(px0 + 2, px1 - 1):
            s.set(x, y, hz0, barrier("x"))
    for x in range(px0 - 2, px1 + 3):              # canopy over the portal
        for z in (hz0 - 1, hz0 - 2):
            s.set(x, G + 10, z, RSTEEL_S)
    s.set(px0 - 1, G + 4, hz0 - 1, sign("north", SIGN_RESTRICTED))
    s.set(px0 - 1, G + 2, hz0 - 1, reader("north", "b"))   # clearance B: the portal of the central building
    s.set(px0 - 2, G + 2, hz0 - 1, sign("north", SIGN_CARD["b"], color="black", glow=False))
    s.set(px1 + 1, G + 4, hz0 - 1, sign("north", SIGN_DANGER))
    s.set(px0 - 2, G + 4, hz0 - 1, wall_banner("north"))
    s.set(px1 + 2, G + 4, hz0 - 1, wall_banner("north"))
    for x in (px0 - 4, px1 + 3):
        poster(s, x, G + 2, hz0 - 1, "oinstein_poster_insignia", "north")
    s.set(47, G + 12, hz0 - 1, wall_banner("north"))
    s.set(48, G + 12, hz0 - 1, wall_banner("north"))
    s.set(47, G + 12, hz0, CON)
    s.set(48, G + 12, hz0, CON)
    # foyer: checkered floor, reception, lecterns, specimen tanks, pillars, the sealed lift
    for x in range(hx0 + 1, hx1):
        for z in range(hz0 + 1, hz1):
            s.set(x, G, z, WCON if (x + z) % 2 else BCON)
    for x in (37, 42, 53, 58):
        for z in (46, 53):
            s.fill(x, G + 1, z, x, G + 9, z, IRON)
    for x in range(44, 52):
        s.set(x, G + 1, 50, DOUBLE_SLAB)
    s.set(46, G + 1, 51, computer("south"))
    s.set(49, G + 1, 51, computer("south"))
    s.set(44, G + 1, 47, lectern("north", "oinstein_journal"))
    s.set(51, G + 1, 47, lectern("north", "oinstein_orders"))
    for x in (hx0 + 1, hx1 - 1):
        for z in (44, 48, 52, 56):
            s.set(x, G + 1, z, IRON)
            s.set(x, G + 4, z, IRON)
            for y in (G + 2, G + 3):
                s.set(x, y, z, V("water", level=0) if z != 52 else S_AIR)
            for dz in (-1, 1):
                for y in (G + 2, G + 3):
                    s.set(x, y, z + dz, GLASS)
            dx = 1 if x == hx0 + 1 else -1
            for y in (G + 2, G + 3):
                s.set(x + dx, y, z, V("lime_stained_glass"))
            s.set(x + dx, G + 1, z, RSTEEL_S)
            s.set(x + dx, G + 4, z, RSTEEL_S)
            if z == 52:
                s.captive(x, G + 2, z, specimen=True)
    s.set(38, G + 1, 58, RSTEEL_S)
    s.set(38, G + 2, 58, TESLA_S)
    s.set(57, G + 1, 58, RSTEEL_S)
    s.set(57, G + 2, 58, TESLA_S)
    for (x, z) in ((40, 42), (55, 42)):
        s.set(x, G + 1, z, DOUBLE_SLAB)
        s.set(x, G + 2, z, JAR_S)
    poster(s, 40, G + 2, hz1 - 1, "oinstein_poster_better_ape", "north")
    poster(s, 55, G + 2, hz1 - 1, "oinstein_poster_insignia", "north")
    for x in (44, 51):
        s.set(x, G + 5, hz1 - 1, wall_banner("north"))
    # the lift: a recess in the back wall behind a second barrier
    lx0, lx1 = 45, 50
    s.fill(lx0 - 1, G + 1, hz1 - 3, lx1 + 1, G + 7, hz1 - 1, HSTEEL_S)
    s.fill(lx0, G, hz1 - 3, lx1, G + 6, hz1 - 1, S_AIR)
    s.fill(lx0, G - 1, hz1 - 3, lx1, G - 1, hz1 - 1, GRATE)
    s.fill(lx0, G, hz1 - 2, lx1, G, hz1 - 1, S_AIR)
    for y in range(G, G + 7):
        s.set(lx0, y, hz1 - 3, EMITTER_S)
        s.set(lx1, y, hz1 - 3, EMITTER_S)
        for x in range(lx0 + 1, lx1):
            s.set(x, y, hz1 - 3, barrier("x"))
    s.set(lx0 + 2, G + 4, hz1, CON)
    s.set(lx0 + 1, G + 7, hz1 - 4, sign("north", SIGN_SEALED))
    s.set(lx1 - 1, G + 7, hz1 - 4, sign("north", SIGN_DANGER))
    for x in (lx0 + 1, lx1 - 1):
        s.set(x, G + 7, hz1 - 3, HSTEEL_S)
    s.set(lx0 + 2, G + 5, hz1 - 1, lamp())
    s.set(lx0 + 2, G + 5, hz1, V("redstone_block"))
    s.set(lx0 - 1, G + 2, hz1 - 4, reader("north", "c"))   # clearance C: the lift down to the lower laboratory
    # the lift shaft: its spiral stair (in the lower-laboratory template) starts at the recess floor
    s.fill(LAB_STAIR_TOP[0], G - 1, hz1 - 2, LAB_STAIR_TOP[1], G - 1, hz1 - 1, S_AIR)
    s.mob(47, G + 1, 55, SAPIENS)
    s.protect_box(px0, G, hz0 - 2, px1, G + 8, hz0 + 1)
    # ------------------------------------------------------------ reactor hall with its dome
    rx0, rz0, rx1, rz1 = 8, 8, 27, 27
    s.fill(rx0, G, rz0, rx1, G + 10, rz1, CON)
    s.fill(rx0 + 1, G + 1, rz0 + 1, rx1 - 1, G + 10, rz1 - 1, S_AIR)
    hazard_band(s, rx0, rz0, rx1, rz1, G + 1)
    s.ring(rx0, rz0, rx1, rz1, G + 10, WCON)
    cxr, czr = (rx0 + rx1) / 2, (rz0 + rz1) / 2
    for h in range(0, 8):
        r = 9.5 * math.sqrt(max(0.0, 1 - (h / 8.0) ** 2))
        for x in range(rx0, rx1 + 1):
            for z in range(rz0, rz1 + 1):
                d = math.hypot(x - cxr, z - czr)
                if d <= r:
                    inner = d < r - 1.2 and h < 7
                    s.set(x, G + 11 + h, z, S_AIR if inner else (GLASS if h in (2, 3) and int(d) % 2 else WCON))
    for (x, z) in ((13, 13), (22, 13), (13, 22), (22, 22)):
        s.set(x, G + 1, z, HSTEEL_S)
        s.set(x, G + 2, z, st("reactor_core", lit=True))
        s.set(x, G + 3, z, st("reactor_core", lit=True))
        s.fill(x, G + 4, z, x, G + 9, z, pipe("y"))
    for x in range(14, 22):
        s.set(x, G + 9, 13, pipe("x"))
        s.set(x, G + 9, 22, pipe("x"))
    s.set(17, G + 1, 17, chest_state("north", "chests/oinstein_lab"))
    s.set(18, G + 1, 17, st("cargo_crate"))
    s.set(17, G + 1, rz0 + 1, computer("south"))
    s.set(18, G + 1, rz0 + 1, computer("south"))
    s.fill(17, G + 1, rz1, 18, G + 3, rz1, S_AIR)
    s.set(17, G + 1, rz1, st("airlock_door", facing="south", half="lower", hinge="left", open=False))
    s.set(17, G + 2, rz1, st("airlock_door", facing="south", half="upper", hinge="left", open=False))
    s.set(18, G + 1, rz1, st("airlock_door", facing="south", half="lower", hinge="right", open=False))
    s.set(18, G + 2, rz1, st("airlock_door", facing="south", half="upper", hinge="right", open=False))
    s.set(16, G + 3, rz1 + 1, sign("south", SIGN_DANGER))
    s.set(19, G + 3, rz1 + 1, wall_banner("south"))
    # smokestacks
    smokestack(s, 30, 9, H - 4)
    smokestack(s, 30, 22, H - 6)
    # cooling tower
    cooling_tower(s, 74, 20, G + 1, 26, 10.5, 6.5, 8.0)
    # pipelines: reactor -> cooling tower, reactor -> hall
    pipeline(s, [(28, 17), (63, 17)], G + 6)
    pipeline(s, [(18, 29), (18, 52), (31, 52)], G + 5)
    pipeline(s, [(64, 52), (84, 52), (84, 33)], G + 7)
    # ------------------------------------------------------------ loading yard: tracks, wagons, gantry crane
    for z in (72, 79):
        for x in range(60, W1 - 1):
            s.set(x, G + 1, z, V("rail", shape="east_west", waterlogged=False))
    cage_wagon(s, 64, 72, G + 1)
    cage_wagon(s, 71, 72, G + 1)
    cage_wagon(s, 80, 79, G + 1)
    for (x, z) in ((61, 68), (61, 83), (88, 68), (88, 83)):
        s.fill(x, G + 1, z, x, G + 13, z, RSTEEL_S)
    for x in range(61, 89):
        s.set(x, G + 14, 68, HSTEEL_S)
        s.set(x, G + 14, 83, HSTEEL_S)
    for z in range(68, 84):
        s.set(76, G + 15, z, YCON)
    s.fill(75, G + 14, 74, 77, G + 14, 76, RSTEEL_S)
    for y in range(G + 7, G + 14):
        s.set(76, y, 75, chain("y"))
    s.set(76, G + 6, 75, IRON)
    s.set(76, G + 5, 75, st("cargo_crate"))
    for (x, z, h) in ((64, 88, 2), (65, 88, 1), (66, 88, 3), (64, 87, 1), (70, 88, 2), (86, 64, 2), (87, 64, 1)):
        s.fill(x, G + 1, z, x, G + h, z, st("cargo_crate"))
    s.set(67, G + 1, 88, barrel_state("chests/oinstein_outpost"))
    s.set(85, G + 1, 64, barrel_state("chests/oinstein_outpost"))
    # ------------------------------------------------------------ barracks and armory (south-west)
    bx0, bz0, bx1, bz1 = 8, 62, 30, 74
    s.fill(bx0, G, bz0, bx1, G + 6, bz1, CON)
    s.fill(bx0 + 1, G + 1, bz0 + 1, bx1 - 1, G + 5, bz1 - 1, S_AIR)
    hazard_band(s, bx0, bz0, bx1, bz1, G + 1)
    for x in range(bx0 + 2, bx1 - 1, 3):
        s.set(x, G + 3, bz0, TINT)
        s.set(x, G + 3, bz1, TINT)
    s.fill(19, G + 1, bz0, 19, G + 3, bz0, S_AIR)
    for x in range(bx0 + 2, bx1 - 1, 3):
        if x in (17, 20):
            continue
        s.set(x, G + 1, bz1 - 1, st("crew_bunk", facing="south", part="foot"))
        s.set(x, G + 1, bz1 - 1, V("red_bed", facing="south", occupied=False, part="head"))
        s.set(x, G + 1, bz1 - 2, V("red_bed", facing="south", occupied=False, part="foot"))
        s.set(x, G + 1, bz0 + 1, st("supply_cabinet", facing="south"))
    for x in range(bx0 + 3, bx1, 5):
        s.set(x, G + 5, (bz0 + bz1) // 2, light_on())
    poster(s, bx0 + 1, G + 2, (bz0 + bz1) // 2, "oinstein_poster_better_ape", "east")
    s.set(bx1 - 1, G + 1, (bz0 + bz1) // 2, lectern("west", "oinstein_orders"))
    s.set(18, G + 3, bz0 - 1, wall_banner("north"))
    s.set(20, G + 3, bz0 - 1, wall_banner("north"))
    s.mob(14, G + 1, 68, NOVUS)
    ax0, az0, ax1, az1 = 8, 78, 20, 88
    s.fill(ax0, G, az0, ax1, G + 5, az1, CON)
    s.fill(ax0 + 1, G + 1, az0 + 1, ax1 - 1, G + 4, az1 - 1, S_AIR)
    hazard_band(s, ax0, az0, ax1, az1, G + 5)
    s.fill(14, G + 1, az0, 14, G + 3, az0, S_AIR)
    s.set(14, G + 1, az0, st("airlock_door", facing="north", half="lower", hinge="left", open=False))
    s.set(14, G + 2, az0, st("airlock_door", facing="north", half="upper", hinge="left", open=False))
    s.set(10, G + 1, az1 - 1, chest_state("north", "chests/oinstein_armory"))
    s.set(17, G + 1, az1 - 1, chest_state("north", "chests/oinstein_armory"))
    for x in range(11, 17):
        s.set(x, G + 1, az1 - 1, st("cargo_crate"))
    s.set(13, G + 3, az0 - 1, sign("north", SIGN_RESTRICTED))
    s.set(14, G + 4, (az0 + az1) // 2, light_on())
    # specimen pens along the south wall
    for i, x in enumerate(range(34, 58, 6)):
        cage(s, x, 84, 5, 5, captives=1 + i % 2)
    s.mob(46, G + 1, 81, NOVUS)
    # lamp posts
    for (x, z) in ((40, 12), (55, 12), (40, 28), (55, 28), (30, 40), (66, 40), (30, 78), (58, 70), (88, 58)):
        s.fill(x, G + 1, z, x, G + 4, z, V("lightning_rod", facing="up", powered=False, waterlogged=False))
        s.set(x, G + 5, z, LANTERN_SEA)
    # the garrison of the yard (with the towers, the barracks and the pens: 13 on the surface, one in the foyer)
    for (x, z) in ((47, 14), (70, 45), (46, 76)):
        s.mob(x, G + 1, z, AUTOMATON)
    for (x, z) in ((45, 8), (50, 8)):
        s.mob(x, G + 1, z, NOVUS)
    s.mob(78, G + 1, 40, SAPIENS)
    s.mob(30, G + 1, 58, SENTRY)
    for (x, z) in ((42, 36), (53, 36), (42, 20), (53, 20)):
        s.set(x, G + 1, z, standing_banner(8))
    return s


TEMPLATES[f"oinstein/{COMPLEX}"] = build_complex


# =====================================================================================================================
# The lower laboratory and the Main Laboratory (the boss arena), under the Institute
# =====================================================================================================================
# Drawn in the Institute's coordinates (x, z as in build_complex; y relative to its foundation: the yard is y = 1),
# then stored as its own template "oinstein/oinstein_lower_lab". DryJigsawStructure attaches it under the start piece
# (extra_pieces, offset = the lab origin), as an AttachedTemplatePiece: placed as it is, with no terrain adaptation, and
# wrapped in a riveted-steel shell so that no cave water or lava gets in.
LAB = "oinstein_lower_lab"
FY = -30                     # the floor blocks of the lab (walk level -29: 31 blocks under the yard)
LAB_STAIR_TOP = (45, 48)     # the stair opening in the lift recess floor (y 0, z 62..63)
ANCHOR = (13, FY + 1, 24)    # retrocosmos:oinstein_boss_anchor: on the arena floor in front of the hangar bay (the
                             # Strider's 28-block leash then covers the whole hall; 3 x 5 x 3 kept free round it)
LAB_INFO = {}
LAB_MARKERS = {"oinstein_boss_anchor": ANCHOR}


class FreeBase(Base):
    """A Base without bounds (negative coordinates allowed); relocate() turns it into a template."""

    def inside(self, x, y, z):
        return True


def relocate(free):
    xs, ys, zs = zip(*free.b)
    ox, oy, oz = min(xs), min(ys), min(zs)
    out = Base(free.name, (max(xs) - ox + 1, max(ys) - oy + 1, max(zs) - oz + 1), seed=free.seed, ground=-999)
    out.b = {(x - ox, y - oy, z - oz): v for (x, y, z), v in free.b.items()}
    out.entities = [((x - ox, y - oy, z - oz), nbt) for (x, y, z), nbt in free.entities]
    out.origin = (ox, oy, oz)
    out.underground = True
    return out


class LabRoom:
    def __init__(self, x0, z0, x1, z1, h, wall=CON, floor=CON, ceil=RSTEEL_S):
        self.x0, self.z0, self.x1, self.z1, self.h = x0, z0, x1, z1, h
        self.wall, self.floor, self.ceil = wall, floor, ceil

    def shell(self, s):
        s.fill(self.x0 - 1, FY, self.z0 - 1, self.x1 + 1, FY + self.h + 1, self.z1 + 1, self.wall)
        s.fill(self.x0 - 1, FY, self.z0 - 1, self.x1 + 1, FY, self.z1 + 1, self.floor)
        s.fill(self.x0 - 1, FY + self.h + 1, self.z0 - 1, self.x1 + 1, FY + self.h + 1, self.z1 + 1, self.ceil)

    def hollow(self, s):
        s.fill(self.x0, FY + 1, self.z0, self.x1, FY + self.h, self.z1, S_AIR)

    def band(self, s, y=FY + 1):
        hazard_band(s, self.x0 - 1, self.z0 - 1, self.x1 + 1, self.z1 + 1, y)


def opening(s, x0, z0, x1, z1, h, along, frame=True):
    """A doorway through the wall(s) x0..x1 / z0..z1 (h tall; along = the axis one walks through it), framed in
    hazard steel."""
    s.fill(x0, FY + 1, z0, x1, FY + h, z1, S_AIR)
    if frame:
        if along == "x":                               # through an x wall: the frame posts stand north and south
            for x in range(x0, x1 + 1):
                for z in (z0 - 1, z1 + 1):
                    s.fill(x, FY + 1, z, x, FY + h + 1, z, HSTEEL_S)
                s.fill(x, FY + h + 1, z0, x, FY + h + 1, z1, HSTEEL_S)
        else:
            for z in range(z0, z1 + 1):
                for x in (x0 - 1, x1 + 1):
                    s.fill(x, FY + 1, z, x, FY + h + 1, z, HSTEEL_S)
                s.fill(x0, FY + h + 1, z, x1, FY + h + 1, z, HSTEEL_S)


def tank(s, x, z, dx, specimen):
    """A specimen tank in a wall column: iron base and cap, glass sides, a green-lit front (dx = towards the room)."""
    s.set(x, FY + 1, z, IRON)
    s.set(x, FY + 4, z, IRON)
    s.set(x, FY + 5, z, pipe("y"))
    for y in (FY + 2, FY + 3):
        s.set(x, y, z, S_AIR if specimen else V("water", level=0))
        s.set(x + dx, y, z, V("lime_stained_glass") if specimen else GLASS)
        s.set(x, y, z - 1, GLASS)
        s.set(x, y, z + 1, GLASS)
    s.set(x + dx, FY + 1, z, RSTEEL_S)
    s.set(x + dx, FY + 4, z, RSTEEL_S)
    for dz in (-1, 1):
        s.set(x, FY + 1, z + dz, RSTEEL_S)
        s.set(x, FY + 4, z + dz, RSTEEL_S)
    if specimen:
        s.captive(x, FY + 2, z, specimen=True)


def holding_cell(s, x0, x1, z0, z1, bars_x, gate_facing):
    """A barred holding cell off the corridor with one caged (Captive) tribesman behind a fence gate."""
    s.fill(x0, FY + 1, z0, x1, FY + 3, z1, S_AIR)
    for z in range(z0, z1 + 1):
        s.fill(bars_x, FY + 1, z, bars_x, FY + 3, z, bars())
    gz = (z0 + z1) // 2
    s.set(bars_x, FY + 1, gz, V("dark_oak_fence_gate", facing=gate_facing, in_wall=False, open=False, powered=False))
    s.set(bars_x, FY + 2, gz, S_AIR)
    s.set((x0 + x1) // 2, FY + 3, (z0 + z1) // 2 + 1, light_on())
    s.set(x0 if bars_x > x1 else x1, FY + 1, z1, V("hay_block", axis="y"))      # a straw bed
    s.captive((x0 + x1) // 2, FY + 1, gz)


def lab_shaft(s):
    """The lift shaft: an 8 x 8 steel well with a square spiral stair round a lit core, from the recess floor (y 0)
    down to the laboratory (two turns, four steps per side and a landing in each corner)."""
    x0, z0 = 43, 56
    s.fill(x0 - 1, FY, z0 - 1, x0 + 8, -1, z0 + 8, RSTEEL_S)
    s.fill(x0, FY + 1, z0, x0 + 7, -1, z0 + 7, S_AIR)
    s.fill(x0, FY, z0, x0 + 7, FY, z0 + 7, GRATE)
    for y in range(FY + 1, 0):
        if (y - FY) % 6 == 3:                          # hazard bands and lamps on the walls
            s.ring(x0 - 1, z0 - 1, x0 + 8, z0 + 8, y, lambda: HSTEEL_S)
        if (y - FY) % 6 == 0:
            for (x, z) in ((x0 - 1, z0 + 3), (x0 + 8, z0 + 4), (x0 + 3, z0 - 1), (x0 + 4, z0 + 8)):
                s.set(x, y, z, LANTERN_SEA)
    s.fill(x0 + 2, FY + 1, z0 + 2, x0 + 5, -1, z0 + 5, RSTEEL_S)             # the core
    for y in range(FY + 3, 0, 4):
        for (x, z) in ((x0 + 2, z0 + 3), (x0 + 5, z0 + 4), (x0 + 3, z0 + 5), (x0 + 4, z0 + 2)):
            s.set(x, y, z, LANTERN_SEA)
    corners = {"SE": (x0 + 6, z0 + 6), "SW": (x0, z0 + 6), "NW": (x0, z0), "NE": (x0 + 6, z0)}
    flights = {   # name: (cells per step, in walking order (downwards), the facing of the stairs (uphill))
        "S": ([[(x, z0 + 6), (x, z0 + 7)] for x in range(x0 + 5, x0 + 1, -1)], "east"),
        "W": ([[(x0, z), (x0 + 1, z)] for z in range(z0 + 5, z0 + 1, -1)], "south"),
        "N": ([[(x, z0), (x, z0 + 1)] for x in range(x0 + 2, x0 + 6)], "west"),
        "E": ([[(x0 + 6, z), (x0 + 7, z)] for z in range(z0 + 2, z0 + 6)], "north"),
    }
    order = ["S", "SW", "W", "NW", "N", "NE", "E", "SE"]
    y, i = 0, 0                                         # the first landing (SE, y 0) is the recess floor itself
    while True:
        part = order[i % len(order)]
        i += 1
        if part in corners:
            y -= 1
            cx, cz = corners[part]
            for dx in (0, 1):
                for dz in (0, 1):
                    s.set(cx + dx, y, cz + dz, GRATE)
            if y <= FY:
                return corners[part]
            continue
        steps, facing = flights[part]
        for cells in steps:
            y -= 1
            for (x, z) in cells:
                s.set(x, y, z, V("polished_andesite_stairs", facing=facing, half="bottom", shape="straight",
                                 waterlogged=False))


def lab_arena(s, room):
    """The Main Laboratory: a 40 x 40 hall, 16 high - the raised hangar bay of the Walker on the west side under a
    gantry, cover pillars and barricades on the floor, Tesla coils round the edges, catwalks along the walls."""
    x0, z0, x1, z1 = room.x0, room.z0, room.x1, room.z1
    top = FY + room.h
    for x in range(x0, x1 + 1):                          # floor: concrete slabs in a 6-block grid
        for z in range(z0, z1 + 1):
            s.set(x, FY, z, LCON if (x - x0) % 6 == 0 or (z - z0) % 6 == 0 else CON)
    room.band(s)
    s.ring(x0 - 1, z0 - 1, x1 + 1, z1 + 1, FY + 8, lambda: WCON)
    for x in range(x0 + 2, x1 - 1, 6):                   # ceiling lights
        for z in range(z0 + 2, z1 - 1, 6):
            s.set(x, top + 1, z, LANTERN_SEA)
    # the hangar bay: raised two blocks, hazard edge, stairs down the whole front, a gantry crane over it
    bx1, bz0, bz1 = 6, 14, 35
    s.fill(x0, FY + 1, bz0, bx1, FY + 1, bz1, CON)
    s.fill(x0, FY + 2, bz0, bx1, FY + 2, bz1, GRATE)
    for z in range(bz0, bz1 + 1):
        s.set(bx1, FY + 2, z, HSTEEL_S)
        s.set(bx1 + 1, FY + 1, z, V("polished_blackstone_stairs", facing="west", half="bottom", shape="straight",
                                    waterlogged=False))
    for x in range(x0, bx1 + 1):
        for z in (bz0, bz1):
            s.set(x, FY + 2, z, HSTEEL_S)
    gy = FY + 13
    for (x, z) in ((x0 + 1, bz0 - 1), (bx1 - 1, bz0 - 1), (x0 + 1, bz1 + 1), (bx1 - 1, bz1 + 1)):
        s.fill(x, FY + 1, z, x, gy, z, RSTEEL_S)
        s.set(x, FY + 1, z, HSTEEL_S)
    for x in (x0 + 1, bx1 - 1):
        s.fill(x, gy, bz0 - 1, x, gy, bz1 + 1, HSTEEL_S)
        for z in range(bz0 + 3, bz1 - 2, 5):
            s.set(x, gy, z, LANTERN_SEA)
            s.fill(x, gy - 3, z + 2, x, gy - 1, z + 2, chain("y"))
    for z in (bz0 - 1, bz1 + 1):
        s.fill(x0 + 1, gy, z, bx1 - 1, gy, z, HSTEEL_S)
    s.fill(x0 + 2, gy, 23, bx1 - 2, gy, 26, RSTEEL_S)   # the crane trolley over the Walker
    s.fill(2, gy - 2, 24, 2, gy - 1, 24, chain("y"))
    s.set(2, gy - 3, 24, IRON)
    # the back wall: the hangar door in a hazard frame, banners
    for z in range(bz0 + 3, bz1 - 2):
        for y in range(FY + 3, FY + 13):
            edge = z in (bz0 + 3, bz1 - 3) or y == FY + 12
            s.set(x0 - 1, y, z, HSTEEL_S if edge else (RSTEEL_S if (y - FY) % 3 else IRON))
    for z in (bz0 + 1, bz1 - 1):
        s.set(x0, FY + 8, z, wall_banner("east"))
    # cover: full-height steel pillars and low hazard barricades
    for (cx, cz) in ((14, 12), (14, 37), (27, 12), (27, 37), (21, 24)):
        s.fill(cx - 1, FY + 1, cz - 1, cx + 1, top, cz + 1, RSTEEL_S)
        hazard_band(s, cx - 1, cz - 1, cx + 1, cz + 1, FY + 1)
        hazard_band(s, cx - 1, cz - 1, cx + 1, cz + 1, FY + 2)
        for (dx, dz) in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            s.set(cx + dx, FY + 7, cz + dz, LANTERN_SEA)
            s.set(cx + dx, FY + 12, cz + dz, LANTERN_SEA)
    for (bx, bz, along) in ((31, 18, "z"), (31, 29, "z"), (10, 8, "x"), (10, 41, "x"), (20, 17, "x"), (20, 31, "x")):
        for k in range(3):
            x, z = (bx + k, bz) if along == "x" else (bx, bz + k)
            s.set(x, FY + 1, z, HSTEEL_S)
            s.set(x, FY + 2, z, RSTEEL_S if k != 1 else V("smooth_stone_slab", type="bottom", waterlogged=False))
    # serum vats in the corners by the bay
    for (vx, vz) in ((x0 + 2, z0 + 2), (x0 + 2, z1 - 2)):
        s.fill(vx - 1, FY + 1, vz - 1, vx + 1, FY + 1, vz + 1, HSTEEL_S)
        s.fill(vx - 1, FY + 2, vz - 1, vx + 1, FY + 6, vz + 1, V("lime_stained_glass"))
        s.fill(vx - 1, FY + 7, vz - 1, vx + 1, FY + 7, vz + 1, RSTEEL_S)
        s.fill(vx, FY + 8, vz, vx, top, vz, pipe("y"))
    # specimen tanks along the north and south walls (the Strider "smashes" two at a quarter health): glass round a
    # one-block core - water, or a sleeping specimen (a Captive tribesman, freed when the Director falls)
    for (tx, tz) in ((15, z0 + 2), (23, z0 + 2), (31, z0 + 2), (15, z1 - 2), (23, z1 - 2), (31, z1 - 2)):
        specimen = tx == 23
        s.fill(tx - 1, FY + 1, tz - 1, tx + 1, FY + 1, tz + 1, IRON)
        s.fill(tx - 1, FY + 2, tz - 1, tx + 1, FY + 4, tz + 1, GLASS)
        for (dx, dz) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            s.fill(tx + dx, FY + 2, tz + dz, tx + dx, FY + 4, tz + dz, RSTEEL_S)
        s.fill(tx, FY + 2, tz, tx, FY + 4, tz, S_AIR if specimen else V("water", level=0))
        for (dx, dz) in ((0, -1), (0, 1)):
            s.fill(tx + dx, FY + 2, tz + dz, tx + dx, FY + 4, tz + dz, V("lime_stained_glass"))
        s.fill(tx - 1, FY + 5, tz - 1, tx + 1, FY + 5, tz + 1, RSTEEL_S)
        s.fill(tx, FY + 6, tz, tx, FY + 9, tz, pipe("y"))
        if specimen:
            s.captive(tx, FY + 2, tz, specimen=True)
    # Tesla coils round the edges
    for x in (11, 19, 27, 34):
        for z in (z0, z1):
            s.set(x, FY + 1, z, RSTEEL_S)
            s.set(x, FY + 2, z, TESLA_S)
    for z in (19, 30):
        s.set(x1, FY + 1, z, RSTEEL_S)
        s.set(x1, FY + 2, z, TESLA_S)
    # catwalks along the north, south and east walls (3 wide, a railing on the inner edge), ladders at the corners
    cy = FY + 10
    for x in range(bx1 + 2, x1 + 1):
        for z in (z0, z0 + 1, z0 + 2, z1 - 2, z1 - 1, z1):
            s.set(x, cy, z, GRATE)
    for z in range(z0, z1 + 1):
        for x in (x1 - 2, x1 - 1, x1):
            s.set(x, cy, z, GRATE)
    for x in range(bx1 + 2, x1 - 2):
        s.set(x, cy + 1, z0 + 2, bars())
        s.set(x, cy + 1, z1 - 2, bars())
    for z in range(z0 + 2, z1 - 1):
        s.set(x1 - 2, cy + 1, z, bars())
    for x in (bx1 + 2,):
        for z in (z0, z0 + 1, z1 - 1, z1):
            s.set(x - 1, cy + 1, z, bars())
    for x in range(bx1 + 4, x1 - 2, 7):
        for z in (z0 + 2, z1 - 2):
            s.fill(x, cy + 2, z, x, top, z, chain("y"))
    for z in (z0 + 3, z1 - 3):
        for y in range(FY + 1, cy + 1):
            s.set(x1, y, z, V("ladder", facing="west", waterlogged=False))
        s.set(x1, cy + 1, z, S_AIR)
    # control desks along the east wall either side of the entrance
    for z in list(range(10, 17)) + list(range(32, 39)):
        if z % 2 == 0:
            s.set(x1, FY + 3, z, panel("west"))
    s.set(*ANCHOR, data_marker("oinstein_boss_anchor"))


def build_lower_lab():
    """The lower laboratory: the lift shaft, the corridor of specimen tanks and holding cells, the brain bank,
    Dr. Oinstein's office (his final journal), the generator hall and the Main Laboratory with the hangar bay of
    his Walker - five guards in all, none in the arena (that is the Director's)."""
    s = FreeBase(LAB, (0, 0, 0), seed=9101, ground=-999)
    rnd = s.rnd
    corridor = LabRoom(40, 40, 48, 54, 5)
    brains = LabRoom(41, 29, 55, 38, 6, floor=LCON)
    office = LabRoom(58, 29, 66, 38, 5, floor=V("polished_andesite"))
    hall = LabRoom(42, 8, 60, 26, 9, floor=CON)
    vestibule = LabRoom(38, 22, 40, 26, 6, wall=HSTEEL_S, floor=HSTEEL_S)
    arena = LabRoom(-3, 5, 36, 44, 16, floor=CON)
    rooms = [corridor, brains, office, hall, vestibule, arena]
    for r in rooms:
        r.shell(s)
    s.fill(35, FY, 49, 39, FY + 4, 54, CON)            # the holding cells' block west and east of the corridor
    s.fill(49, FY, 49, 53, FY + 4, 54, CON)
    for r in rooms:
        r.hollow(s)
    bottom = lab_shaft(s)
    for r in (corridor, brains, office, hall):
        r.band(s)
    lab_arena(s, arena)
    # ------------------------------------------------ doorways
    opening(s, bottom[0], 55, bottom[0] + 1, 55, 3, "z")         # shaft -> corridor
    opening(s, 42, 39, 46, 39, 4, "z")                           # corridor -> brain bank
    opening(s, 46, 27, 48, 28, 4, "z")                           # brain bank -> generator hall
    opening(s, 56, 33, 57, 34, 3, "x")                           # brain bank -> office
    opening(s, 41, 22, 41, 26, 5, "x")                           # generator hall -> vestibule
    opening(s, 37, 22, 37, 26, 6, "x", frame=False)              # vestibule -> arena (the blast door frame below)
    for z in (21, 27):
        s.fill(37, FY + 1, z, 37, FY + 7, z, HSTEEL_S)
    s.fill(37, FY + 7, 21, 37, FY + 7, 27, HSTEEL_S)
    # ------------------------------------------------ the corridor: specimen tanks and holding cells
    for (x, dx) in ((40, 1), (48, -1)):
        for z in (41, 44, 47):
            tank(s, x, z, dx, specimen=(x, z) in ((40, 41), (48, 44), (40, 47), (48, 47)))
    holding_cell(s, 36, 38, 50, 53, 39, "west")
    holding_cell(s, 50, 52, 50, 53, 49, "east")
    for z in range(40, 55):
        s.set(44, FY, z, YCON if z % 2 else BCON)
    for z in (42, 46, 50, 53):
        s.set(44, FY + 5, z, light_on())
    s.set(44, FY + 5, 40, sign("south", SIGN_BRAINS, color="black", glow=False))
    s.mob(44, FY + 1, 47, NOVUS)
    # ------------------------------------------------ the brain bank
    for z in (32, 35):
        for x in range(43, 54):
            s.set(x, FY + 1, z, computer("south" if z == 32 else "north") if x % 3 == 0 else st("tape_archive",
                  facing="south" if z == 32 else "north"))
            s.set(x, FY + 2, z, V("smooth_stone_slab", type="top", waterlogged=False))
            s.set(x, FY + 3, z, JAR_S)
            s.set(x, FY + 4, z, V("smooth_stone_slab", type="top", waterlogged=False))
            if x % 2:
                s.set(x, FY + 5, z, JAR_S)
            if x % 4 == 1:
                s.set(x, FY + 6, z, chain("y"))
    for x in range(42, 55):
        if x not in (46, 47, 48) and x % 2 == 0:
            s.set(x, FY + 1, 29, computer("south"))
            s.set(x, FY + 2, 29, IRON)
            s.set(x, FY + 3, 29, panel("south"))
    for (x, z) in ((44, 30), (52, 30), (44, 37), (52, 37), (48, 33), (48, 34)):
        s.set(x, FY + 6, z, light_on())
    s.set(41, FY + 1, 30, RSTEEL_S)
    s.set(41, FY + 2, 30, TESLA_S)
    s.set(55, FY + 1, 38, RSTEEL_S)
    s.set(55, FY + 2, 38, TESLA_S)
    s.set(55, FY + 4, 33, sign("west", SIGN_OFFICE, color="black", glow=False))
    poster(s, 41, FY + 2, 36, "oinstein_poster_better_ape", "east")
    s.mob(48, FY + 1, 37, SAPIENS)
    # ------------------------------------------------ Dr. Oinstein's office
    for x in range(60, 65):
        for z in range(31, 37):
            s.set(x, FY + 1, z, V("red_carpet"))
    for z in range(32, 36):
        s.set(62, FY + 1, z, DOUBLE_SLAB)
    s.set(62, FY + 2, 32, JAR_S)
    s.set(62, FY + 2, 33, computer("west"))
    s.set(62, FY + 2, 35, st("space_globe", facing="west"))
    s.set(63, FY + 1, 34, st("captain_chair", facing="west"))
    s.set(60, FY + 1, 30, lectern("west", "oinstein_final"))
    for z in list(range(29, 32)) + list(range(36, 39)):
        s.fill(66, FY + 1, z, 66, FY + 3, z, V("bookshelf"))
    s.set(66, FY + 1, 34, locker("west", "chests/oinstein_director", "director_safe"))
    s.set(66, FY + 1, 32, st("tape_archive", facing="west"))
    s.set(66, FY + 1, 33, IRON)
    s.set(66, FY + 1, 35, st("tape_archive", facing="west"))
    poster(s, 66, FY + 2, 33, "oinstein_poster_insignia", "west")
    s.set(66, FY + 3, 32, wall_banner("west"))
    s.set(66, FY + 3, 35, wall_banner("west"))
    for x in range(59, 66, 2):
        s.set(x, FY + 1, 29, st("tape_archive", facing="south"))
    s.set(58, FY + 1, 38, RSTEEL_S)
    s.set(58, FY + 2, 38, TESLA_S)
    for (x, z) in ((61, 31), (61, 36), (64, 33)):
        s.set(x, FY + 5, z, light_on())
    s.mob(59, FY + 1, 37, SAPIENS)
    # ------------------------------------------------ the generator hall
    for cx in (47, 52, 57):
        for cz in (12, 21):
            hazard_band(s, cx - 2, cz - 2, cx + 2, cz + 2, FY)
            s.fill(cx - 1, FY + 1, cz - 1, cx + 1, FY + 1, cz + 1, RSTEEL_S)
            for (dx, dz) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
                s.fill(cx + dx, FY + 2, cz + dz, cx + dx, FY + 4, cz + dz, HSTEEL_S)
            for (dx, dz) in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                s.fill(cx + dx, FY + 2, cz + dz, cx + dx, FY + 4, cz + dz, bars())
            s.fill(cx, FY + 2, cz, cx, FY + 4, cz, st("reactor_core", lit=True))
            s.fill(cx - 1, FY + 5, cz - 1, cx + 1, FY + 5, cz + 1, V("cut_copper"))
            s.set(cx - 1, FY + 6, cz - 1, TESLA_S)
            s.set(cx + 1, FY + 6, cz + 1, TESLA_S)
            s.fill(cx, FY + 6, cz, cx, FY + 9, cz, pipe("y"))
    for x in range(hall.x0, hall.x1 + 1):
        s.set(x, FY + 8, 17, pipe("x"))
    for x in range(44, 60, 2):
        s.set(x, FY + 1, 8, computer("south"))
        s.set(x + 1, FY + 2, 8, panel("south"))
    for (x, z) in ((42, 8), (60, 8), (60, 26)):
        s.set(x, FY + 1, z, RSTEEL_S)
        s.set(x, FY + 2, z, TESLA_S)
    for x in range(44, 60, 5):
        for z in (10, 17, 24):
            s.set(x, FY + 9, z, light_on())
    s.set(42, FY + 7, 24, sign("east", SIGN_MAINLAB))
    s.set(42, FY + 7, 22, wall_banner("east"))
    s.set(42, FY + 7, 26, wall_banner("east"))
    poster(s, hall.x1, FY + 2, 14, "oinstein_poster_restricted", "west")
    s.mob(50, FY + 1, 17, AUTOMATON)
    s.mob(44, FY + 1, 16, SENTRY)
    # ------------------------------------------------ the vestibule and the Main Laboratory
    for z in range(22, 27):
        for x in range(38, 41):
            s.set(x, FY, z, HSTEEL_S if (x + z) % 2 else BCON)
    s.set(39, FY + 6, 24, light_on())
    # ------------------------------------------------ the shell: riveted steel round everything below the yard
    occupied = set(s.b)
    for (x, y, z) in list(occupied):
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    q = (x + dx, y + dy, z + dz)
                    if q[1] <= -1 and q not in s.b:
                        s.b[q] = RSTEEL_S
    out = relocate(s)
    LAB_INFO["origin"] = out.origin
    LAB_INFO["size"] = (out.W, out.H, out.D)
    LAB_INFO["markers"] = {k: (x - out.origin[0], y - out.origin[1], z - out.origin[2])
                           for k, (x, y, z) in LAB_MARKERS.items()}
    lab_reach(out)
    return out


def lab_reach(s):
    """The way down must work: from the top of the stair to the arena, the office and every room."""
    ox, oy, oz = s.origin
    L = lambda x, y, z: (x - ox, y - oy, z - oz)   # noqa: E731

    def free(p):
        n = s.name_at(*p)
        return n in (AIR, M("ladder"), M("structure_block")) or (n is None and p[1] >= s.H)

    def ground(p):
        n = s.name_at(*p)
        return n is not None and n not in (AIR, M("ladder"), M("structure_block"))

    start = L(47, -1, 62)
    seen, todo = {start}, [start]
    while todo:
        x, y, z = todo.pop()
        steps = [(dx, dy, dz) for dx, dz in DIRS.values() for dy in (1, 0, -1, -2, -3)]
        if s.name_at(x, y, z) == M("ladder") or s.name_at(x, y + 1, z) == M("ladder"):
            steps += [(0, 1, 0), (0, -1, 0)]
        for dx, dy, dz in steps:
            p = (x + dx, y + dy, z + dz)
            if p in seen or not (free(p) and free((p[0], p[1] + 1, p[2]))):
                continue
            if not (ground((p[0], p[1] - 1, p[2])) or s.name_at(*p) == M("ladder")):
                continue
            if dy > 0 and not free((x, y + 2, z)):
                continue
            seen.add(p)
            todo.append(p)
    targets = {"anchor": ANCHOR, "office": (61, FY + 1, 30), "brains": (48, FY + 1, 37), "hall": (50, FY + 1, 15),
               "catwalk": (30, FY + 11, 6), "cell": (44, FY + 1, 51)}
    missing = [k for k, t in targets.items() if L(*t) not in seen]
    if missing:
        raise SystemExit(f"oinstein.py: lower lab: unreachable from the lift: {missing}")


TEMPLATES[f"oinstein/{LAB}"] = build_lower_lab

R_.EN.update(EN)
R_.RU.update(RU)


# =====================================================================================================================
# The prisoner camp of the captured Earth expedition (placed at runtime by OinsteinPrisonCamp.java, not worldgen)
# =====================================================================================================================
# Template "oinstein/oinstein_prison_camp" (41 x 41, y 0 = the solid ground layer of the levelled site, like the
# expedition camp) and its anchors data/retrocosmos/venus_camp/prison_camp.json: size, ground_y, centre, the
# captives (role, name, pos, yaw, cell_door, lever) and the garrison (informational - the mobs are in the template).
PRISON = "oinstein_prison_camp"
PRISON_ANCHORS = os.path.join(DATA, "venus_camp", "prison_camp.json")
PRISON_INFO = {}
# cells: (west x of the 4 x 4 cell, north row?) -> (role, name); the two empty cells stay open-doored rubbish holes
PRISON_CELLS = {(11, True): ("scientist", None), (16, True): ("guard", None), (21, True): ("doctor", "vale"),
                (26, True): None, (11, False): None, (16, False): ("scientist", None), (21, False): ("guard", None),
                (26, False): ("scientist", None)}


def iron_door(x, y, z, s, facing, hinge="left"):
    s.set(x, y, z, V("iron_door", facing=facing, half="lower", hinge=hinge, open=False, powered=False))
    s.set(x, y + 1, z, V("iron_door", facing=facing, half="upper", hinge=hinge, open=False, powered=False))


def prison_cell_block(s, captives):
    """Eight barred 4 x 4 cells either side of a corridor; each cell door is an iron door worked by a lever on the
    post beside it (corridor side) - pull it and the prisoner walks free."""
    x0, x1, z0, z1, top = 9, 31, 8, 21, 4
    s.fill(x0, 0, z0, x1, 0, z1, CON)
    s.box(x0, 1, z0, x1, top, z1, CON, roof=RSTEEL_S)
    hazard_band(s, x0, z0, x1, z1, 1)
    for z in range(9, 21):
        for x in range(10, 31):
            s.set(x, 0, z, LCON if (x + z) % 2 else CON)
    for px in (10, 15, 20, 25, 30):                     # partitions and the solid posts at the bar lines
        for (za, zb) in ((9, 13), (16, 20)):
            s.fill(px, 1, za, px, top, zb, CON)
    for cx in (11, 16, 21, 26):
        for north in (True, False):
            bar_z, inner = (13, (9, 12)) if north else (16, (17, 20))
            lever_z = 14 if north else 15
            for x in range(cx, cx + 4):
                s.fill(x, 1, bar_z, x, top, bar_z, bars())
            iron_door(cx, 1, bar_z, s, "north" if north else "south")
            s.set(cx - 1, 2, lever_z, V("lever", face="wall", facing="south" if north else "north", powered=False))
            # inside: a straw bed and a bucket of a cell; the prisoner by the door
            bz = inner[0] if north else inner[1]
            s.set(cx + 3, 1, bz, V("hay_block", axis="x"))
            who = PRISON_CELLS[(cx, north)]
            if who:
                role, name = who
                pz = 12 if north else 17
                captives.append({"role": role, "name": name, "pos": (cx + 1, 1, pz), "yaw": 0 if north else 180,
                                 "cell_door": (cx, 1, bar_z), "lever": (cx - 1, 2, lever_z)})
    for z in (14, 15):                                  # the corridor: open at the east end
        s.fill(x1, 1, z, x1, 2, z, S_AIR)
    s.protect_box(x1 - 1, 1, 14, x1 + 1, 2, 15)
    for x in (12, 17, 22, 27):
        s.set(x, top, 14, light_on())
    for x in range(11, 30, 4):                         # barred slits high in the outer walls
        s.set(x, 3, z0, bars())
        s.set(x, 3, z1, bars())
    s.set(x1 + 1, 3, 13, sign("east", ["prison_1", "prison_2", "prison_3", "prison_4"]))
    s.set(x1 + 1, 3, 16, wall_banner("east"))
    for x in (12, 20, 28):
        poster(s, x, 1, z1 + 1, ("oinstein_poster_better_ape", "oinstein_poster_insignia", "oinstein_poster_restricted")
               [(x // 8) % 3], "south")


def build_prison_camp():
    """Dr. Oinstein's prisoner camp for the captured Earth expedition: a fenced compound with barbed wire, two
    watchtowers with sentries and searchlights, the cell block (8 cells, 6 prisoners, Dr. Vale in a middle one),
    the interrogation hut, the guards' barracks and the depot of the expedition's confiscated gear."""
    N = 41
    s = Base(PRISON, (N, 16, N), seed=8501, ground=0)
    rnd = s.rnd
    s.fill(0, 0, 0, N - 1, 0, N - 1, PACKED)
    for x in range(N):
        for z in range(N):
            if rnd.random() < 0.25:
                s.set(x, 0, z, V("mud_bricks") if rnd.random() < 0.3 else CON)
    for z in range(22, N):                              # the road from the gate
        for x in (19, 20, 21):
            s.set(x, 0, z, CON if x == 20 else LCON)
    # ------------------------------------------------ the fence: bars, posts, barbed wire on top, the gate
    lo, hi = 1, N - 2
    for i in range(lo, hi + 1):
        for (x, z, axis) in ((i, lo, "x"), (i, hi, "x"), (lo, i, "z"), (hi, i, "z")):
            s.fill(x, 1, z, x, 3, z, bars())
            s.set(x, 4, z, chain(axis))
            if i % 4 == 1:
                s.fill(x, 1, z, x, 4, z, RSTEEL_S)
                s.set(x, 5, z, chain("y"))
    gx = N // 2
    s.fill(gx - 1, 1, hi, gx + 1, 4, hi, S_AIR)
    for x in (gx - 2, gx + 2):
        s.fill(x, 1, hi, x, 5, hi, HSTEEL_S)
    s.fill(gx - 1, 4, hi, gx + 1, 5, hi, HSTEEL_S)
    for x in range(gx - 1, gx + 2):
        s.set(x, 1, hi, V("dark_oak_fence_gate", facing="south", in_wall=False, open=False, powered=False))
    s.set(gx, 4, hi + 1, sign("south", SIGN_RESTRICTED))
    s.set(gx - 3, 2, hi + 1, wall_banner("south"))
    s.set(gx + 3, 2, hi + 1, wall_banner("south"))
    for x in (gx - 3, gx + 3):
        s.fill(x, 1, hi, x, 4, hi, RSTEEL_S)
    s.protect_box(gx - 1, 1, hi - 1, gx + 1, 3, hi + 1)
    # ------------------------------------------------ watchtowers in the north corners (sentries, searchlights)
    watchtower(s, 2, 2, 8)
    watchtower(s, hi - 5, 2, 8)
    # ------------------------------------------------ the cell block
    captives = []
    prison_cell_block(s, captives)
    # ------------------------------------------------ the interrogation hut (south-west)
    s.fill(3, 0, 25, 11, 0, 33, CON)
    s.box(3, 1, 25, 11, 3, 33, CON, roof=RSTEEL_S)
    s.fill(11, 1, 29, 11, 2, 29, S_AIR)
    s.protect_box(10, 1, 29, 12, 2, 29)
    s.set(6, 1, 29, st("captain_chair", facing="east"))             # the prisoner's chair under the lamp
    s.set(8, 1, 29, DOUBLE_SLAB)
    s.set(8, 1, 30, DOUBLE_SLAB)
    s.set(8, 2, 30, st("rocket_table_lamp", facing="west", lit=True))
    s.set(8, 2, 29, st("tape_archive", facing="west"))
    s.set(9, 1, 29, st("diner_stool"))
    s.set(6, 3, 29, light_on())
    s.set(4, 1, 26, st("tape_archive", facing="south"))
    s.set(4, 1, 32, chest_state("east", "chests/oinstein_outpost"))
    poster(s, 4, 1, 29, "oinstein_poster_restricted", "east")
    s.set(12, 2, 31, sign("east", ["interrogation_1", "interrogation_2", "interrogation_3", "interrogation_4"],
                          color="black", glow=False))
    s.mob(9, 1, 31, SAPIENS)
    # ------------------------------------------------ the guards' barracks (south-east)
    s.fill(29, 0, 25, 37, 0, 34, CON)
    s.box(29, 1, 25, 37, 3, 34, CON, roof=RSTEEL_S)
    hazard_band(s, 29, 25, 37, 34, 1)
    s.fill(29, 1, 29, 29, 2, 29, S_AIR)
    s.protect_box(28, 1, 29, 30, 2, 29)
    for z in (26, 28, 31, 33):
        s.set(36, 1, z, V("red_bed", facing="east", occupied=False, part="head"))
        s.set(35, 1, z, V("red_bed", facing="east", occupied=False, part="foot"))
    s.set(30, 1, 33, lectern("east", "oinstein_orders"))
    s.set(30, 1, 26, st("supply_cabinet", facing="east"))
    s.set(33, 3, 29, light_on())
    s.set(33, 1, 30, barrel_state("chests/oinstein_outpost"))
    poster(s, 32, 1, 34 - 1, "oinstein_poster_better_ape", "north")
    # ------------------------------------------------ the depot of the expedition's confiscated gear
    for (x, z) in ((14, 25), (25, 25), (14, 31), (25, 31)):
        s.fill(x, 1, z, x, 3, z, RSTEEL_S)
    s.fill(14, 4, 25, 25, 4, 31, RSTEEL_S)
    s.fill(15, 0, 26, 24, 0, 30, CON)
    for (x, z, h) in ((15, 26, 2), (16, 26, 1), (15, 27, 1), (23, 26, 2), (24, 26, 1), (24, 27, 3), (24, 30, 1)):
        s.fill(x, 1, z, x, h, z, st("cargo_crate"))
    s.set(17, 1, 26, chest_state("south", "chests/oinstein_confiscated"))
    s.set(22, 1, 26, chest_state("south", "chests/oinstein_confiscated"))
    s.set(16, 1, 30, barrel_state("chests/oinstein_outpost"))
    s.set(15, 1, 30, st("oxygen_tank_rack", facing="east"))
    s.set(23, 1, 30, st("radar_scope", facing="north", lit=False))
    s.set(19, 3, 28, light_on())
    s.set(14, 2, 24, sign("north", ["confiscated_1", "confiscated_2", "confiscated_3", "confiscated_4"],
                          color="black", glow=False))
    # ------------------------------------------------ the yard: lamp posts, banners, the garrison
    for (x, z) in ((8, 23), (32, 23), (12, 36), (28, 36), (20, 5)):
        s.fill(x, 1, z, x, 4, z, V("lightning_rod", facing="up", powered=False, waterlogged=False))
        s.set(x, 5, z, LANTERN_SEA)
    s.set(16, 1, 23, standing_banner(8))
    s.set(24, 1, 23, standing_banner(8))
    s.mob(gx, 1, hi - 3, NOVUS)                     # at the gate
    s.mob(13, 1, 14, NOVUS)                         # in the cell corridor
    s.mob(27, 1, 23, AUTOMATON)                     # the yard
    guards = [(p, str(n["id"])) for p, n in s.entities]
    PRISON_INFO.update(captives=captives, guards=guards, size=(s.W, s.H, s.D))
    return s


def write_prison_anchors():
    info = PRISON_INFO
    write_json(PRISON_ANCHORS, {
        "template": f"{MOD}:oinstein/{PRISON}", "size": list(info["size"]), "ground_y": 0,
        "center": [info["size"][0] // 2, 1, info["size"][2] // 2],
        "captives": [{"kind": "expedition_captive", "role": c["role"], **({"name": c["name"]} if c["name"] else {}),
                      "pos": list(c["pos"]), "yaw": c["yaw"], "cell_door": list(c["cell_door"]), "lever": list(c["lever"])}
                     for c in info["captives"]],
        "guards": [{"type": t, "pos": list(p)} for p, t in info["guards"]]})


TEMPLATES[f"oinstein/{PRISON}"] = build_prison_camp
EN.update({"sign.retrocosmos.prison_1": "DETENTION", "sign.retrocosmos.prison_2": "BLOCK E",
           "sign.retrocosmos.prison_3": "EARTH SPECIMENS", "sign.retrocosmos.prison_4": "DO NOT FEED",
           "sign.retrocosmos.interrogation_1": "INTERVIEW", "sign.retrocosmos.interrogation_2": "ROOM",
           "sign.retrocosmos.interrogation_3": "QUESTIONS ARE", "sign.retrocosmos.interrogation_4": "OUR BUSINESS",
           "sign.retrocosmos.confiscated_1": "CONFISCATED", "sign.retrocosmos.confiscated_2": "EARTH GEAR",
           "sign.retrocosmos.confiscated_3": "PROPERTY OF", "sign.retrocosmos.confiscated_4": "THE INSTITUTE"})
RU.update({"sign.retrocosmos.prison_1": "ИЗОЛЯТОР", "sign.retrocosmos.prison_2": "БЛОК Е",
           "sign.retrocosmos.prison_3": "ЗЕМНЫЕ ОБРАЗЦЫ", "sign.retrocosmos.prison_4": "НЕ КОРМИТЬ",
           "sign.retrocosmos.interrogation_1": "КОМНАТА", "sign.retrocosmos.interrogation_2": "ДЛЯ БЕСЕД",
           "sign.retrocosmos.interrogation_3": "ВОПРОСЫ ЗАДАЁМ", "sign.retrocosmos.interrogation_4": "МЫ",
           "sign.retrocosmos.confiscated_1": "КОНФИСКОВАНО", "sign.retrocosmos.confiscated_2": "ЗЕМНОЕ",
           "sign.retrocosmos.confiscated_3": "ИМУЩЕСТВО -", "sign.retrocosmos.confiscated_4": "СОБСТВЕННОСТЬ ИНСТ."})
R_.EN.update(EN)
R_.RU.update(RU)
