"""Venus: the pulp-era jungle planet under eternal amber clouds (1930s-50s retro sci-fi).

Generates every asset and data file of the Venus content: block textures (Pillow pixel art), models, blockstates,
item definitions, loot tables, tags, recipes, lang entries and the whole dimension (dimension type, timeline,
noise settings with surface rules, biomes, configured/placed features, carvers).

Called from gen_resources.main(); EN / RU are merged into the lang files.

Dinosaur spawns (retrocosmos:raptor / brontosaurus / triceratops / venus_creeper / pteranodon / tyrannosaurus) are
written into the biomes only once dinosaur/ModDinosaurs.java registers those entity ids (an unknown entity id would break biome loading). Force them
on or off with the environment variable VENUS_DINO_SPAWNS=1 / 0.
"""
import json
import math
import os
import random


from gen_resources import (ASSETS, DATA, MOD, cooking, loot_self, new, save, shaped, shapeless, tag,
                           write_json)
from furniture import add_to_tag

HERE = os.path.dirname(os.path.abspath(__file__))
JAVA_DINOS = os.path.join(HERE, "..", "src", "main", "java", "com", "replecant", "retrocosmos", "dinosaur",
                          "ModDinosaurs.java")
DINOS = ("raptor", "brontosaurus", "triceratops", "venus_creeper", "pteranodon", "tyrannosaurus", "plesiosaur",
         "meganeura", "compsognathus", "spore_moth", "ankylosaurus", "deinosuchus")


def P(name):
    return f"{MOD}:{name}"


def B(name, **props):
    """Block state JSON."""
    state = {"Name": name if ":" in name else P(name)}
    if props:
        state["Properties"] = {k: str(v).lower() for k, v in props.items()}
    return state


# =====================================================================================================================
# Pixel-art helpers
# =====================================================================================================================

def clamp(v):
    return max(0, min(255, int(round(v))))


def mix(a, b, t):
    return tuple(clamp(a[i] + (b[i] - a[i]) * t) for i in range(3))


def shade(c, d):
    return tuple(clamp(v + d) for v in c[:3])


def put(img, x, y, c, wrap=False):
    if wrap:
        x %= img.width
        y %= img.height
    if 0 <= x < img.width and 0 <= y < img.height:
        img.putpixel((x, y), (c[0], c[1], c[2], c[3] if len(c) > 3 else 255))


def get(img, x, y):
    return img.getpixel((x % img.width, y % img.height))


def smooth_noise(rnd, w, h, cells):
    """Tileable value noise in [0,1] (bilinear over a cells x cells lattice)."""
    grid = [[rnd.random() for _ in range(cells)] for _ in range(cells)]
    out = []
    for y in range(h):
        row = []
        for x in range(w):
            fx, fy = x * cells / w, y * cells / h
            x0, y0 = int(fx), int(fy)
            tx, ty = fx - x0, fy - y0
            tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
            a = grid[y0 % cells][x0 % cells]
            b = grid[y0 % cells][(x0 + 1) % cells]
            c = grid[(y0 + 1) % cells][x0 % cells]
            d = grid[(y0 + 1) % cells][(x0 + 1) % cells]
            row.append((a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty)
        out.append(row)
    return out


def tonal(seed, palette, weights, w=16, h=16, octaves=((4, 0.55), (8, 0.3)), jitter=0.35, field=None):
    """Vanilla-style texture: a smooth tileable field quantised into a few palette tones by rank."""
    rnd = random.Random(seed)
    layers = [(smooth_noise(rnd, w, h, c), a) for c, a in octaves]
    vals = []
    for y in range(h):
        for x in range(w):
            v = sum(layer[y][x] * a for layer, a in layers) + rnd.random() * jitter
            if field:
                v += field(x, y)
            vals.append((v, x, y))
    order = sorted(vals)
    img = new(w, h)
    total = sum(weights)
    bounds, acc = [], 0.0
    for wt in weights:
        acc += wt / total
        bounds.append(acc)
    n = len(order)
    for i, (_, x, y) in enumerate(order):
        f = (i + 0.5) / n
        k = next(j for j, b in enumerate(bounds) if f <= b + 1e-9)
        put(img, x, y, palette[k])
    return img


def voronoi(seed, count, w=16, h=16):
    rnd = random.Random(seed)
    pts = [(rnd.uniform(0, w), rnd.uniform(0, h)) for _ in range(count)]
    cell = [[0] * w for _ in range(h)]
    edge = [[0.0] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            ds = []
            for i, (px_, py_) in enumerate(pts):
                dx = min(abs(x + 0.5 - px_), w - abs(x + 0.5 - px_))
                dy = min(abs(y + 0.5 - py_), h - abs(y + 0.5 - py_))
                ds.append((dx * dx + dy * dy, i))
            ds.sort()
            cell[y][x] = ds[0][1]
            edge[y][x] = math.sqrt(ds[1][0]) - math.sqrt(ds[0][0])
    return pts, cell, edge


def line(img, x0, y0, x1, y1, c, wrap=False):
    steps = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    for i in range(steps + 1):
        t = i / max(1, steps)
        put(img, int(round(x0 + (x1 - x0) * t)), int(round(y0 + (y1 - y0) * t)), c, wrap)


# =====================================================================================================================
# Palette: amber skies, teal-olive greenery, rust and ochre wood, mauve stone, black volcanic glass
# =====================================================================================================================
STONE = [(84, 70, 82), (101, 86, 97), (116, 100, 109), (133, 117, 123)]
BLACK = [(28, 25, 32), (39, 35, 44), (51, 46, 56), (66, 60, 71)]
MUD = [(56, 41, 40), (69, 52, 47), (83, 63, 55), (99, 77, 66)]
SOIL = [(74, 50, 34), (92, 64, 42), (108, 77, 50), (127, 92, 60)]
MOSS = [(42, 82, 68), (56, 99, 72), (74, 116, 72), (97, 134, 70), (124, 148, 70)]
TAR = [(17, 13, 16), (26, 20, 23), (36, 29, 31)]
BARK = [(58, 38, 31), (76, 49, 37), (94, 61, 43), (114, 77, 53)]
RING = [(138, 92, 54), (158, 108, 63), (178, 126, 74), (196, 146, 88)]
PLANK = [(106, 64, 40), (126, 80, 50), (145, 95, 59), (164, 111, 69)]
LEAF = [(34, 82, 68), (48, 104, 78), (66, 124, 84), (92, 144, 84), (128, 160, 78)]
AMBER_LEAF = [(92, 52, 36), (124, 72, 42), (154, 98, 52), (180, 128, 66), (200, 158, 84)]
FROND = [(34, 84, 66), (48, 104, 74), (70, 124, 76), (100, 140, 70), (132, 150, 66)]
OCHRE = (186, 138, 62)
RUST = (168, 80, 42)
GLOW_CYAN = [(36, 128, 132), (64, 186, 182), (120, 232, 214), (206, 255, 240)]
GLOW_VIOLET = [(92, 52, 150), (142, 86, 214), (196, 140, 255), (240, 214, 255)]
IVORY = [(150, 138, 124), (180, 168, 150), (206, 196, 176), (228, 220, 202)]
LAVA = [(150, 44, 22), (214, 92, 30), (255, 156, 52), (255, 222, 132)]


# =====================================================================================================================
# Block textures
# =====================================================================================================================

def tex_stone():
    img = tonal(11, STONE, [12, 33, 38, 17])
    rnd = random.Random(12)
    for _ in range(3):   # a few hairline fractures
        x, y = rnd.randrange(16), rnd.randrange(16)
        for _ in range(rnd.randint(2, 4)):
            put(img, x, y, STONE[0], True)
            x += rnd.choice((1, 1, 0))
            y += rnd.choice((0, 1))
    return img


def tex_cobble(palette=STONE, seed=21):
    pts, cell, edge = voronoi(seed, 11)
    rnd = random.Random(seed)
    tone = [rnd.choice((1, 2, 2, 3)) for _ in pts]
    img = new()
    for y in range(16):
        for x in range(16):
            if edge[y][x] < 0.9:
                put(img, x, y, palette[0])
                continue
            t = tone[cell[y][x]]
            # light from the top-left: pixels whose upper/left neighbour is mortar get a highlight
            up_edge = edge[(y - 1) % 16][x] < 0.9 or edge[y][(x - 1) % 16] < 0.9
            dn_edge = edge[(y + 1) % 16][x] < 0.9 or edge[y][(x + 1) % 16] < 0.9
            c = palette[min(3, t + 1)] if up_edge else palette[max(1, t - 1)] if dn_edge else palette[t]
            if rnd.random() < 0.08:
                c = shade(c, -8)
            put(img, x, y, c)
    return img


def tex_bricks():
    img = new()
    rnd = random.Random(31)
    mortar = (70, 58, 68)
    for row in range(4):
        y0 = row * 4
        off = 0 if row % 2 == 0 else 4
        for y in range(y0, y0 + 4):
            for x in range(16):
                bx = (x + off) % 8
                if y == y0 + 3 or bx == 7:
                    put(img, x, y, mortar)
                    continue
                c = STONE[2]
                if y == y0 or bx == 0:
                    c = STONE[3]
                elif y == y0 + 2 or bx == 6:
                    c = STONE[1]
                if rnd.random() < 0.12:
                    c = shade(c, rnd.choice((-7, 6)))
                put(img, x, y, c)
    return img


def tex_black_rock(top=False):
    if top:
        pts, cell, edge = voronoi(41, 6)
        rnd = random.Random(42)
        tone = [rnd.choice((1, 2, 2)) for _ in pts]
        img = new()
        for y in range(16):
            for x in range(16):
                c = BLACK[0] if edge[y][x] < 0.8 else BLACK[tone[cell[y][x]]]
                if edge[y][x] >= 0.8 and rnd.random() < 0.1:
                    c = BLACK[3]
                put(img, x, y, c)
        return img
    # sides: rough columnar texture with vertical seams
    img = tonal(43, BLACK, [10, 34, 40, 16], octaves=((4, 0.5), (8, 0.3)),
                field=lambda x, y: 0.35 * math.sin(x * math.pi / 4.0 + 0.6))
    for y in range(16):
        for x in (0, 8):
            if (y * 7 + x) % 5:
                put(img, x, y, BLACK[0])
    rnd = random.Random(44)
    for _ in range(6):    # gas pores
        put(img, rnd.randrange(16), rnd.randrange(16), (20, 18, 24))
    return img


def tex_fumarole(top):
    img = tex_black_rock(top=True) if top else tex_black_rock()
    rnd = random.Random(51 if top else 52)
    if top:
        # a glowing star-shaped crack around the vent
        for k in range(5):
            ang = k * 2 * math.pi / 5 + rnd.uniform(-0.3, 0.3)
            x, y = 7.5, 7.5
            for i in range(7):
                x += math.cos(ang) + rnd.uniform(-0.4, 0.4)
                y += math.sin(ang) + rnd.uniform(-0.4, 0.4)
                put(img, int(x), int(y), LAVA[1] if i > 4 else LAVA[2])
        for x in range(6, 10):
            for y in range(6, 10):
                d = abs(x - 7.5) + abs(y - 7.5)
                put(img, x, y, LAVA[3] if d < 1.5 else LAVA[2])
        put(img, 7, 7, (255, 246, 210))
        put(img, 8, 8, (255, 246, 210))
    else:
        x, y = rnd.randint(3, 6), 0
        while y < 16:
            put(img, x, y, LAVA[2] if rnd.random() < 0.6 else LAVA[1])
            y += 1
            x += rnd.choice((-1, 0, 0, 1))
            x = max(1, min(14, x))
        for _ in range(3):
            put(img, rnd.randrange(16), rnd.randrange(16), LAVA[0])
    return img


def tex_mud():
    img = tonal(61, MUD, [14, 36, 34, 16], octaves=((4, 0.6), (8, 0.25)), jitter=0.25)
    rnd = random.Random(62)
    for _ in range(7):   # wet glints
        x, y = rnd.randrange(16), rnd.randrange(16)
        put(img, x, y, (122, 98, 84))
        if rnd.random() < 0.5:
            put(img, x + 1, y, (108, 86, 74), True)
    return img


def tex_soil():
    img = tonal(71, SOIL, [12, 34, 38, 16])
    rnd = random.Random(72)
    for _ in range(4):   # pebbles of mauve stone
        x, y = rnd.randrange(16), rnd.randrange(16)
        put(img, x, y, STONE[2])
        put(img, x + 1, y, STONE[1], True)
    for _ in range(3):   # pale root threads
        x, y = rnd.randrange(16), rnd.randrange(16)
        for _ in range(3):
            put(img, x, y, (146, 112, 76), True)
            x += 1
            y += rnd.choice((0, 1))
    return img


def tex_moss_top():
    img = tonal(81, MOSS, [10, 26, 32, 22, 10], octaves=((4, 0.45), (8, 0.35)), jitter=0.4)
    rnd = random.Random(82)
    for _ in range(5):   # tiny ochre spore heads
        put(img, rnd.randrange(16), rnd.randrange(16), OCHRE)
    return img


def tex_moss_side():
    img = tex_soil()
    top = tex_moss_top()
    rnd = random.Random(83)
    for x in range(16):
        depth = 2 + rnd.choice((0, 0, 1, 1, 2, 3))
        for y in range(depth):
            c = get(top, x, y)
            if y == depth - 1:
                c = shade(c, -14)
            put(img, x, y, c)
        if rnd.random() < 0.25:   # a strand hanging down
            put(img, x, depth, MOSS[0])
    return img


def tex_tar():
    img = tonal(91, TAR, [30, 45, 25], octaves=((4, 0.6), (8, 0.2)), jitter=0.2)
    rnd = random.Random(92)
    for _ in range(4):   # slow bubbles with glossy highlights
        cx, cy = rnd.randrange(16), rnd.randrange(16)
        r = rnd.choice((1, 2))
        for a in range(0, 360, 30):
            put(img, int(round(cx + r * math.cos(math.radians(a)))), int(round(cy + r * math.sin(math.radians(a)))),
                (46, 38, 38), True)
        put(img, cx - 1 if r > 1 else cx, cy - 1, (98, 86, 80), True)
    for _ in range(5):
        put(img, rnd.randrange(16), rnd.randrange(16), (70, 58, 54))
    return img


def tex_log_side():
    rnd = random.Random(101)
    ridge = [rnd.random() for _ in range(16)]
    img = tonal(102, BARK, [16, 32, 34, 18], octaves=((2, 0.3), (4, 0.25)), jitter=0.2,
                field=lambda x, y: 1.2 * ridge[x] + 0.15 * math.sin(y * 0.9 + x))
    for x in range(16):     # deep vertical furrows
        if ridge[x] < 0.22:
            for y in range(16):
                if (y + x * 3) % 7:
                    put(img, x, y, BARK[0])
    for _ in range(3):      # teal moss and ochre lichen
        x, y = rnd.randrange(16), rnd.randrange(16)
        put(img, x, y, MOSS[1])
        put(img, x, y + 1, MOSS[2], True)
        put(img, x + 1, y + 1, MOSS[0], True)
    for _ in range(3):
        put(img, rnd.randrange(16), rnd.randrange(16), OCHRE)
    return img


def tex_log_top():
    img = new()
    side = tex_log_side()
    rnd = random.Random(111)
    for y in range(16):
        for x in range(16):
            r = math.hypot(x - 7.5, (y - 7.5) * 1.05)
            if x in (0, 15) or y in (0, 15):
                put(img, x, y, get(side, x, y))
                continue
            k = int(r * 0.9 + rnd.random() * 0.4) % 4
            c = RING[[2, 1, 2, 3][k]]
            if r < 1.2:
                c = RING[0]
            put(img, x, y, c)
    for i in range(1, 15):   # inner bark ring
        for (x, y) in ((i, 1), (i, 14), (1, i), (14, i)):
            put(img, x, y, BARK[2] if (i % 3) else BARK[1])
    return img


def tex_planks():
    img = new()
    rnd = random.Random(121)
    for board in range(4):
        y0 = board * 4
        base = rnd.choice((1, 2, 2))
        seam_x = rnd.randrange(4, 12) if board % 2 else rnd.randrange(0, 3)
        for y in range(y0, y0 + 4):
            for x in range(16):
                c = PLANK[base]
                if y == y0 + 3:
                    c = PLANK[0]
                elif y == y0:
                    c = PLANK[min(3, base + 1)]
                elif rnd.random() < 0.18:
                    c = PLANK[max(0, base - 1)] if rnd.random() < 0.6 else PLANK[min(3, base + 1)]
                if x == seam_x and y != y0 + 3:
                    c = PLANK[0]
                put(img, x, y, c)
        put(img, (seam_x + 2) % 16, y0 + 1, (86, 52, 34))   # nail
    return img


def leaf_shape(img, cx, cy, length, width, ang, colors, rnd):
    dx, dy = math.cos(ang), math.sin(ang)
    for t in range(-length, length + 1):
        half = width * math.sqrt(max(0.0, 1 - (t / (length + 0.5)) ** 2))
        for s in range(-int(half + 0.5), int(half + 0.5) + 1):
            x = cx + dx * t - dy * s
            y = cy + dy * t + dx * s
            c = colors[1] if s < 0 else colors[2]
            if abs(s) >= half - 0.5:
                c = colors[0]
            put(img, int(round(x)), int(round(y)), c, True)
    for t in range(-length + 1, length):   # midrib
        put(img, int(round(cx + dx * t)), int(round(cy + dy * t)), colors[3], True)


def tex_leaves(LEAF=LEAF, seed=131):
    img = new(16, 16, (LEAF[0][0], LEAF[0][1], LEAF[0][2], 255))
    rnd = random.Random(seed)
    spots = [(2, 3), (10, 2), (6, 9), (14, 10), (1, 13), (9, 14), (13, 6)]
    for i, (x, y) in enumerate(spots):
        ang = rnd.uniform(0, math.pi)
        dark = i % 2 == 0
        cols = (LEAF[0], LEAF[1] if dark else LEAF[2], LEAF[2] if dark else LEAF[3], LEAF[3] if dark else LEAF[4])
        leaf_shape(img, x, y, rnd.randint(3, 4), 1.8, ang, cols, rnd)
    for _ in range(18):   # holes in the canopy (cut-out)
        x, y = rnd.randrange(16), rnd.randrange(16)
        if get(img, x, y)[:3] == LEAF[0]:
            img.putpixel((x, y), (0, 0, 0, 0))
    put(img, 5, 6, OCHRE)
    put(img, 12, 13, RUST)
    return img


# ---------------------------------------------------------------------------------------------------------------------
# Plants (transparent sprites)
# ---------------------------------------------------------------------------------------------------------------------

def blade(img, x0, y0, height, bend, cols, wrap=False):
    """A grass blade growing up from (x0, y0) with a sideways bend."""
    n = len(cols)
    for i in range(height):
        t = i / max(1, height - 1)
        x = x0 + bend * t * t
        c = cols[min(n - 1, int(t * n))]
        put(img, int(round(x)), y0 - i, c, wrap)


def tex_sedge():
    img = new()
    rnd = random.Random(141)
    cols = [FROND[0], FROND[1], FROND[2], FROND[3], OCHRE]
    for x0 in (1, 3, 4, 6, 7, 9, 10, 12, 14):
        blade(img, x0, 15, rnd.randint(7, 14), rnd.uniform(-3, 3), cols)
    return img


def tex_horsetail():
    img = new()
    rnd = random.Random(151)
    for x0, h, lean in ((3, 11, -1), (6, 15, 0), (10, 13, 1), (13, 9, 1), (8, 7, 0)):
        for i in range(h):
            y = 15 - i
            x = x0 + (lean if i > h * 0.6 else 0)
            joint = i % 3 == 2
            put(img, x, y, (52, 78, 48) if joint else (96, 136, 72) if i % 3 else (118, 150, 78))
            if joint and 2 < i < h - 2:    # whorls of thin needles, drooping
                for side in (-1, 1):
                    if rnd.random() < 0.8:
                        put(img, x + side, y, (78, 116, 62))
                        put(img, x + 2 * side, y + 1, (104, 138, 70))
        tip = x0 + (lean if h > 3 else 0)
        put(img, tip, 15 - h, (150, 112, 62))   # spore cone
        put(img, tip, 14 - h, (182, 140, 78))
    return img


def frond(img, x0, y0, ang, length, cols, droop=0.06, leaflet=2, wrap=False):
    """A pinnate fern frond: a rachis curving under gravity with paired leaflets."""
    x, y = float(x0), float(y0)
    dx, dy = math.cos(ang), math.sin(ang)
    for i in range(length):
        t = i / max(1, length - 1)
        c = cols[min(len(cols) - 1, int(t * (len(cols) - 1)))]
        put(img, int(round(x)), int(round(y)), shade(c, -16), wrap)
        size = max(1, int(round(leaflet * (1 - t * 0.7))))
        if i % 2 == 0 and i > 0:
            nx, ny = -dy, dx
            for s in range(1, size + 1):
                put(img, int(round(x + nx * s + dx * s * 0.4)), int(round(y + ny * s + dy * s * 0.4)), c, wrap)
                put(img, int(round(x - nx * s + dx * s * 0.4)), int(round(y - ny * s + dy * s * 0.4)), shade(c, 10),
                    wrap)
        x += dx
        y += dy
        dy += droop
        norm = math.hypot(dx, dy)
        dx, dy = dx / norm, dy / norm


def tex_giant_fern(top):
    img = new()
    cols = [FROND[1], FROND[2], FROND[3], FROND[4]]
    if top:
        for ang, length, x0 in ((-1.9, 12, 7), (-1.2, 13, 8), (-2.6, 10, 6), (-0.6, 9, 10), (-1.6, 14, 8)):
            frond(img, x0, 15, ang, length, cols, droop=0.08)
    else:
        for x0 in (5, 7, 8, 10):
            for i in range(16):
                put(img, x0 + (1 if i > 10 and x0 < 8 else 0), 15 - i, FROND[0] if i < 5 else FROND[1])
        for ang, length, x0, y0 in ((-2.3, 8, 6, 12), (-0.8, 8, 9, 11), (-2.0, 7, 7, 6), (-1.1, 7, 9, 5)):
            frond(img, x0, y0, ang, length, cols, droop=0.1, leaflet=1)
    return img


def tex_cycad_fronds():
    img = new()
    cols = [FROND[0], FROND[1], FROND[2], FROND[3], FROND[4]]
    for ang, length in ((-0.25, 10), (-2.89, 10), (-0.75, 10), (-2.39, 10), (-1.25, 9), (-1.89, 9), (-1.57, 7)):
        frond(img, 8, 10, ang, length + 1, cols, droop=0.075, leaflet=2)
    for x in range(6, 11):     # the woody cone at the heart of the crown
        put(img, x, 10, OCHRE if x % 2 else (150, 104, 52))
        put(img, x, 11, (120, 86, 48))
    put(img, 7, 9, (206, 160, 80))
    put(img, 8, 9, OCHRE)
    put(img, 9, 9, (206, 160, 80))
    return img


def tex_cycad_trunk():
    img = new()
    for y in range(16):
        for x in range(16):
            # overlapping diamond leaf-base scales, like a pineapple
            u = (x + (y // 2) % 2 * 2) % 4
            v = y % 2
            c = (122, 92, 54) if u in (1, 2) else (90, 66, 40)
            if v == 1 and u == 0:
                c = (66, 48, 32)
            if u == 1 and v == 0:
                c = (150, 116, 68)
            put(img, x, y, c)
    return img


def tex_tree_fern_trunk():
    img = new()
    rnd = random.Random(171)
    for y in range(16):
        for x in range(16):
            c = BARK[1] if (x + y // 3) % 3 else BARK[0]
            if rnd.random() < 0.18:
                c = (110, 82, 52)       # fibrous hairs
            put(img, x, y, c)
    for y in range(1, 16, 4):   # old frond scars
        for x in range((y * 5) % 16, (y * 5) % 16 + 3):
            put(img, x, y, (126, 98, 60), True)
            put(img, x, y + 1, BARK[0], True)
    return img


def tex_tree_fern_crown():
    """32x32 rosette of fronds seen from above (horizontal quad of the tree fern crown)."""
    img = new(32, 32)
    cols = [FROND[1], FROND[2], FROND[3], FROND[4]]
    for k in range(9):
        ang = k * 2 * math.pi / 9 + 0.2
        frond(img, 16, 16, ang, 15, cols, droop=0.0, leaflet=2)
    for x in range(14, 19):
        for y in range(14, 19):
            put(img, x, y, (118, 90, 52) if (x + y) % 2 else (92, 66, 40))
    put(img, 16, 16, (156, 120, 70))
    return img


def tex_tree_fern_fronds():
    """32x32: drooping fronds seen from the side (the crossed quads of the crown use the upper half)."""
    img = new(32, 32)
    cols = [FROND[1], FROND[2], FROND[3], FROND[4]]
    for ang, length in ((-0.5, 15), (-2.64, 15), (-0.95, 12), (-2.2, 12), (-0.15, 13), (-2.99, 13), (-1.57, 6)):
        frond(img, 16, 6, ang, length, cols, droop=0.11, leaflet=2)
    for y in range(4, 9):
        put(img, 15, y, (110, 82, 52))
        put(img, 16, y, (92, 66, 40))
    return img


def tex_tree_fern_item():
    img = new()
    trunk = (92, 64, 40)
    for y in range(7, 16):
        put(img, 7, y, trunk)
        put(img, 8, y, (118, 88, 54))
    cols = [FROND[1], FROND[2], FROND[3], FROND[4]]
    for ang, length in ((-0.4, 8), (-2.74, 8), (-1.0, 7), (-2.14, 7), (-1.57, 5)):
        frond(img, 8, 6, ang, length, cols, droop=0.2, leaflet=1)
    return img


def tex_fire_lily():
    img = new()
    stem = (64, 104, 70)
    for x0, top in ((5, 5), (10, 3)):
        for y in range(top + 2, 16):
            put(img, x0 + (1 if y > 11 and x0 < 8 else 0), y, stem)
    for x0, y0, bend in ((3, 15, -2), (8, 15, 1), (12, 15, 2), (6, 15, -1)):   # strap leaves
        blade(img, x0, y0, 6, bend, [FROND[0], FROND[1], FROND[2]])
    for cx, cy in ((5, 5), (10, 3)):    # trumpet flowers: rust petals, amber throat
        for dx, dy, c in ((-2, -1, RUST), (2, -1, RUST), (-1, -1, (214, 98, 44)), (1, -1, (214, 98, 44)),
                          (0, -1, (240, 170, 70)), (-1, 0, (230, 116, 48)), (0, 0, (255, 206, 96)),
                          (1, 0, (230, 116, 48)), (0, 1, (190, 84, 40)), (-2, -2, (236, 120, 54)),
                          (2, -2, (236, 120, 54)), (0, -2, (250, 138, 60))):
            put(img, cx + dx, cy + dy, c)
    return img


def tex_vines(tip):
    img = new()
    strands = ((4, 0.0, 16), (10, 1.7, 16), (13, 3.1, 11)) if not tip else ((4, 0.0, 12), (10, 1.7, 8), (13, 3.1, 4))
    for x0, phase, length in strands:
        for y in range(length):
            x = x0 + round(math.sin(y * 0.55 + phase) * 1.2)
            put(img, x, y, (58, 90, 56))
            if y % 3 == int(phase) % 3:
                side = 1 if (y // 3) % 2 else -1
                put(img, x + side, y, FROND[2])
                put(img, x + side * 2, y + 1, FROND[3])
                put(img, x + side, y + 1, FROND[1])
        if tip:
            x = x0 + round(math.sin(length * 0.55 + phase) * 1.2)
            put(img, x, length, (58, 90, 56))
            put(img, x + 1, length + 1, (58, 90, 56))
            put(img, x, length + 2, (58, 90, 56))
            if x0 == 10:   # an amber flower bud on the longest-but-one strand
                put(img, x, length + 3, (236, 160, 60))
                put(img, x - 1, length + 3, (210, 120, 48))
                put(img, x, length + 4, (190, 90, 42))
    return img


def mushroom(img, cx, base, stem_h, cap_r, cap_cols, stem_cols):
    for y in range(base - stem_h, base + 1):
        put(img, cx, y, stem_cols[2])
        if cap_r > 1:
            put(img, cx + 1, y, stem_cols[1])
    top = base - stem_h
    w = cap_r
    for dy in range(-max(1, cap_r - 1), 1):
        span = w if dy == 0 else w - 1 - (abs(dy) - 1)
        for dx in range(-span, span + (1 if cap_r > 1 else 0) + 1):
            c = cap_cols[1] if dy == 0 else cap_cols[2]
            if dy == -max(1, cap_r - 1):
                c = cap_cols[3]
            put(img, cx + dx, top + dy, c)
    put(img, cx - w, top, cap_cols[0])
    put(img, cx + w + (1 if cap_r > 1 else 0), top, cap_cols[0])


def tex_glowcap():
    img = new()
    mushroom(img, 5, 15, 7, 4, GLOW_CYAN, IVORY)
    mushroom(img, 11, 15, 4, 3, GLOW_CYAN, IVORY)
    mushroom(img, 14, 15, 1, 1, GLOW_CYAN, IVORY)
    put(img, 3, 5, (255, 255, 255))
    put(img, 10, 9, (255, 255, 255))
    return img


def tex_glowstalk(top):
    img = new()
    stalk = [(110, 92, 132), (140, 120, 160), (176, 156, 196)]
    if not top:
        for y in range(16):
            x = 7 + (1 if y < 6 else 0)
            put(img, x, y, stalk[1])
            put(img, x + 1, y, stalk[0])
        for x0, y0 in ((5, 13), (11, 9), (4, 5)):    # side pods
            line(img, 7, y0 + 2, x0, y0, stalk[1])
            put(img, x0, y0, GLOW_VIOLET[2])
            put(img, x0, y0 - 1, GLOW_VIOLET[3])
            put(img, x0 + 1, y0, GLOW_VIOLET[1])
        for x0, y0 in ((6, 15), (10, 15)):
            line(img, 8, 12, x0, y0, stalk[0])
    else:
        for y in range(6, 16):
            put(img, 8, y, stalk[1])
            put(img, 9, y, stalk[0])
        # a lantern cluster of glowing bulbs
        for cx, cy, r in ((8, 4, 3), (4, 8, 2), (12, 7, 2), (6, 1, 1), (11, 2, 1)):
            for y in range(cy - r, cy + r + 1):
                for x in range(cx - r, cx + r + 1):
                    d = math.hypot(x - cx, y - cy)
                    if d <= r + 0.3:
                        c = GLOW_VIOLET[1] if d > r - 0.7 else GLOW_VIOLET[2]
                        put(img, x, y, c)
            put(img, cx - (1 if r > 1 else 0), cy - (1 if r > 1 else 0), GLOW_VIOLET[3])
        line(img, 8, 9, 4, 8, stalk[2])
        line(img, 9, 9, 12, 7, stalk[2])
    return img


def tex_glowcap_cap():
    img = tonal(191, [(28, 98, 108), GLOW_CYAN[0], GLOW_CYAN[1]], [25, 50, 25], octaves=((4, 0.6),), jitter=0.3)
    rnd = random.Random(192)
    for _ in range(7):   # pale luminous spots
        x, y = rnd.randrange(16), rnd.randrange(16)
        for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
            put(img, x + dx, y + dy, GLOW_CYAN[3] if (dx + dy) == 0 else GLOW_CYAN[2], True)
    return img


def tex_glowcap_inside():
    img = tonal(193, IVORY[1:], [30, 45, 25], octaves=((4, 0.5),), jitter=0.4)
    rnd = random.Random(194)
    for _ in range(10):
        put(img, rnd.randrange(16), rnd.randrange(16), GLOW_CYAN[1])
    return img


def tex_glowcap_stem():
    rnd = random.Random(195)
    col = [rnd.random() for _ in range(16)]
    return tonal(196, IVORY, [12, 30, 38, 20], octaves=((2, 0.3),), jitter=0.25, field=lambda x, y: 1.1 * col[x])


TEXTURES = {
    "venus_stone": tex_stone,
    "venus_cobblestone": tex_cobble,
    "venus_stone_bricks": tex_bricks,
    "venus_black_rock": tex_black_rock,
    "venus_black_rock_top": lambda: tex_black_rock(top=True),
    "venus_fumarole": lambda: tex_fumarole(False),
    "venus_fumarole_top": lambda: tex_fumarole(True),
    "venus_mud": tex_mud,
    "venus_soil": tex_soil,
    "venus_moss_top": tex_moss_top,
    "venus_moss_side": tex_moss_side,
    "venus_tar": tex_tar,
    "venus_log": tex_log_side,
    "venus_log_top": tex_log_top,
    "venus_planks": tex_planks,
    "venus_leaves": tex_leaves,
    "venus_amber_leaves": lambda: tex_leaves(AMBER_LEAF, 137),
    "venus_sedge": tex_sedge,
    "venus_horsetail": tex_horsetail,
    "venus_cycad": tex_cycad_fronds,
    "venus_cycad_trunk": tex_cycad_trunk,
    "venus_fire_lily": tex_fire_lily,
    "venus_tree_fern_trunk": tex_tree_fern_trunk,
    "venus_tree_fern_crown": tex_tree_fern_crown,
    "venus_tree_fern_fronds": tex_tree_fern_fronds,
    "venus_giant_fern_bottom": lambda: tex_giant_fern(False),
    "venus_giant_fern_top": lambda: tex_giant_fern(True),
    "venus_hanging_vines": lambda: tex_vines(False),
    "venus_hanging_vines_tip": lambda: tex_vines(True),
    "venus_glowcap": tex_glowcap,
    "venus_glowstalk_bottom": lambda: tex_glowstalk(False),
    "venus_glowstalk_top": lambda: tex_glowstalk(True),
    "venus_glowcap_block": tex_glowcap_cap,
    "venus_glowcap_block_inside": tex_glowcap_inside,
    "venus_glowcap_stem": tex_glowcap_stem,
}
ITEM_TEXTURES = {
    "venus_tree_fern": tex_tree_fern_item,
}


# =====================================================================================================================
# Models, blockstates, item definitions
# =====================================================================================================================

def model(name, obj):
    write_json(os.path.join(ASSETS, "models", "block", name + ".json"), obj)


def blockstate(name, obj):
    write_json(os.path.join(ASSETS, "blockstates", name + ".json"), obj)


def item(name, model_id):
    write_json(os.path.join(ASSETS, "items", name + ".json"), {"model": {"type": "minecraft:model", "model": model_id}})


def tex(name):
    return f"{MOD}:block/{name}"


def simple(name, parent="minecraft:block/cube_all", textures=None, cutout=False, random_y=False):
    obj = {"parent": parent, "textures": textures or {"all": tex(name)}}
    if cutout:
        obj["render_type"] = "minecraft:cutout"
    model(name, obj)
    if random_y:
        blockstate(name, {"variants": {"": [{"model": P(f"block/{name}"), **({"y": r} if r else {})}
                                            for r in (0, 90, 180, 270)]}})
    else:
        blockstate(name, {"variants": {"": {"model": P(f"block/{name}")}}})
    item(name, P(f"block/{name}"))


def cross_model(name, texture, cutout=True):
    obj = {"parent": "minecraft:block/cross", "textures": {"cross": tex(texture)}}
    if cutout:
        obj["render_type"] = "minecraft:cutout"
    model(name, obj)


def generated(name, texture):
    write_json(os.path.join(ASSETS, "models", "item", name + ".json"),
               {"parent": "minecraft:item/generated", "textures": {"layer0": texture}})
    item(name, P(f"item/{name}"))


def face(uv, texture, cull=None, rot=None):
    f = {"uv": uv, "texture": texture}
    if cull:
        f["cullface"] = cull
    if rot:
        f["rotation"] = rot
    return f


def box(frm, to, texture, uv_side, uv_end, faces=("north", "south", "east", "west", "up", "down")):
    out = {}
    for f in faces:
        out[f] = face(uv_end if f in ("up", "down") else uv_side, texture)
    return {"from": frm, "to": to, "faces": out}


def plane(frm, to, texture, uv, angle=45, faces=("north", "south")):
    return {"from": frm, "to": to, "shade": False,
            "rotation": {"origin": [8, 8, 8], "axis": "y", "angle": angle},
            "faces": {f: face(uv, texture) for f in faces}}


def plant_models():
    for name in ("venus_sedge", "venus_horsetail", "venus_fire_lily", "venus_glowcap"):
        cross_model(name, name)
        blockstate(name, {"variants": {"": {"model": P(f"block/{name}")}}})
        generated(name, tex(name))

    # cycad: a stout scaly trunk under a crown of arching fronds
    model("venus_cycad", {
        "ambientocclusion": False, "render_type": "minecraft:cutout",
        "textures": {"particle": "#fronds", "fronds": tex("venus_cycad"), "trunk": tex("venus_cycad_trunk")},
        "elements": [
            box([5, 0, 5], [11, 6, 11], "#trunk", [5, 10, 11, 16], [5, 5, 11, 11], ("north", "south", "east", "west", "up")),
            plane([-2, 0, 8], [18, 16, 8], "#fronds", [0, 0, 16, 16]),
            plane([8, 0, -2], [8, 16, 18], "#fronds", [0, 0, 16, 16], faces=("east", "west")),
        ]})
    blockstate("venus_cycad", {"variants": {"": {"model": P("block/venus_cycad")}}})
    generated("venus_cycad", tex("venus_cycad"))

    # tree fern: a fibrous trunk carrying a wide umbrella of fronds (the crown reaches out over the neighbours)
    model("venus_tree_fern_bottom", {
        "ambientocclusion": False, "render_type": "minecraft:cutout",
        "textures": {"particle": "#trunk", "trunk": tex("venus_tree_fern_trunk")},
        "elements": [box([6, 0, 6], [10, 16, 10], "#trunk", [6, 0, 10, 16], [6, 6, 10, 10], ("north", "south", "east", "west"))]})
    model("venus_tree_fern_top", {
        "ambientocclusion": False, "render_type": "minecraft:cutout",
        "textures": {"particle": "#crown", "trunk": tex("venus_tree_fern_trunk"),
                     "crown": tex("venus_tree_fern_crown"), "fronds": tex("venus_tree_fern_fronds")},
        "elements": [
            box([6, 0, 6], [10, 10, 10], "#trunk", [6, 6, 10, 16], [6, 6, 10, 10], ("north", "south", "east", "west", "up")),
            {"from": [-8, 10.5, -8], "to": [24, 10.5, 24], "shade": False,
             "faces": {"up": face([0, 0, 16, 16], "#crown"), "down": face([0, 0, 16, 16], "#crown")}},
            plane([-8, 0, 8], [24, 16, 8], "#fronds", [0, 0, 16, 8]),
            plane([8, 0, -8], [8, 16, 24], "#fronds", [0, 0, 16, 8], faces=("east", "west")),
        ]})
    blockstate("venus_tree_fern", {"variants": {"half=lower": {"model": P("block/venus_tree_fern_bottom")},
                                                "half=upper": {"model": P("block/venus_tree_fern_top")}}})
    write_json(os.path.join(ASSETS, "models", "item", "venus_tree_fern.json"),
               {"parent": "minecraft:item/generated", "textures": {"layer0": f"{MOD}:item/venus_tree_fern"}})
    item("venus_tree_fern", P("item/venus_tree_fern"))

    for name in ("venus_giant_fern", "venus_glowstalk"):
        cross_model(f"{name}_bottom", f"{name}_bottom")
        cross_model(f"{name}_top", f"{name}_top")
        blockstate(name, {"variants": {"half=lower": {"model": P(f"block/{name}_bottom")},
                                       "half=upper": {"model": P(f"block/{name}_top")}}})
        generated(name, tex(f"{name}_top"))

    cross_model("venus_hanging_vines", "venus_hanging_vines")
    cross_model("venus_hanging_vines_tip", "venus_hanging_vines_tip")
    blockstate("venus_hanging_vines", {"variants": {"tip=false": {"model": P("block/venus_hanging_vines")},
                                                    "tip=true": {"model": P("block/venus_hanging_vines_tip")}}})
    generated("venus_hanging_vines", tex("venus_hanging_vines_tip"))


def wood_models():
    model("venus_log", {"parent": "minecraft:block/cube_column",
                        "textures": {"end": tex("venus_log_top"), "side": tex("venus_log")}})
    model("venus_log_horizontal", {"parent": "minecraft:block/cube_column_horizontal",
                                   "textures": {"end": tex("venus_log_top"), "side": tex("venus_log")}})
    blockstate("venus_log", {"variants": {
        "axis=x": {"model": P("block/venus_log_horizontal"), "x": 90, "y": 90},
        "axis=y": {"model": P("block/venus_log")},
        "axis=z": {"model": P("block/venus_log_horizontal"), "x": 90}}})
    item("venus_log", P("block/venus_log"))
    model("venus_wood", {"parent": "minecraft:block/cube_column",
                         "textures": {"end": tex("venus_log"), "side": tex("venus_log")}})
    blockstate("venus_wood", {"variants": {
        "axis=x": {"model": P("block/venus_wood"), "x": 90, "y": 90},
        "axis=y": {"model": P("block/venus_wood")},
        "axis=z": {"model": P("block/venus_wood"), "x": 90}}})
    item("venus_wood", P("block/venus_wood"))
    simple("venus_planks")
    simple("venus_leaves", cutout=True)
    simple("venus_amber_leaves", cutout=True)

    planks = {"bottom": tex("venus_planks"), "side": tex("venus_planks"), "top": tex("venus_planks")}
    for suffix, parent in (("", "stairs"), ("_inner", "inner_stairs"), ("_outer", "outer_stairs")):
        model(f"venus_stairs{suffix}", {"parent": f"minecraft:block/{parent}", "textures": planks})
    base_y = {"east": 0, "south": 90, "west": 180, "north": 270}
    variants = {}
    for facing, by in base_y.items():
        for half in ("bottom", "top"):
            for shape in ("straight", "inner_left", "inner_right", "outer_left", "outer_right"):
                m = P("block/venus_stairs" + ("_inner" if shape.startswith("inner") else
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
    blockstate("venus_stairs", {"variants": variants})
    item("venus_stairs", P("block/venus_stairs"))
    model("venus_slab", {"parent": "minecraft:block/slab", "textures": planks})
    model("venus_slab_top", {"parent": "minecraft:block/slab_top", "textures": planks})
    blockstate("venus_slab", {"variants": {"type=bottom": {"model": P("block/venus_slab")},
                                           "type=double": {"model": P("block/venus_planks")},
                                           "type=top": {"model": P("block/venus_slab_top")}}})
    item("venus_slab", P("block/venus_slab"))


def mushroom_models():
    for name, outside in (("venus_glowcap_block", "venus_glowcap_block"), ("venus_glowcap_stem", "venus_glowcap_stem")):
        model(name, {"parent": "minecraft:block/template_single_face", "textures": {"texture": tex(outside)}})
        model(f"{name}_inventory", {"parent": "minecraft:block/cube_all", "textures": {"all": tex(outside)}})
        item(name, P(f"block/{name}_inventory"))
    model("venus_glowcap_block_inside", {"parent": "minecraft:block/template_single_face",
                                         "textures": {"texture": tex("venus_glowcap_block_inside")}})
    rot = {"north": {}, "east": {"y": 90}, "south": {"y": 180}, "west": {"y": 270}, "up": {"x": 270}, "down": {"x": 90}}
    for name in ("venus_glowcap_block", "venus_glowcap_stem"):
        parts = []
        for side, r in rot.items():
            parts.append({"apply": {"model": P(f"block/{name}"), **({"uvlock": True} if r else {}), **r},
                          "when": {side: "true"}})
        for side, r in rot.items():
            parts.append({"apply": {"model": P("block/venus_glowcap_block_inside"), **r}, "when": {side: "false"}})
        blockstate(name, {"multipart": parts})


def block_models():
    for name in ("venus_stone", "venus_cobblestone", "venus_stone_bricks", "venus_mud", "venus_soil", "venus_tar"):
        simple(name, random_y=name in ("venus_stone", "venus_mud", "venus_soil"))
    simple("venus_black_rock", parent="minecraft:block/cube_column",
           textures={"end": tex("venus_black_rock_top"), "side": tex("venus_black_rock")})
    simple("venus_fumarole", parent="minecraft:block/cube_bottom_top",
           textures={"top": tex("venus_fumarole_top"), "side": tex("venus_fumarole"), "bottom": tex("venus_black_rock_top")})
    simple("venus_moss", parent="minecraft:block/cube_bottom_top", random_y=True,
           textures={"top": tex("venus_moss_top"), "side": tex("venus_moss_side"), "bottom": tex("venus_soil")})
    wood_models()
    plant_models()
    mushroom_models()


# =====================================================================================================================
# Loot, tags, recipes
# =====================================================================================================================

SILK = {"condition": "minecraft:match_tool", "predicate": {"predicates": {
    "minecraft:enchantments": [{"enchantments": "minecraft:silk_touch", "levels": {"min": 1}}]}}}
SHEARS = {"condition": "minecraft:match_tool", "predicate": {"items": "minecraft:shears"}}
SHEARS_OR_SILK = {"condition": "minecraft:any_of", "terms": [SHEARS, SILK]}


def loot(name, pools):
    write_json(os.path.join(DATA, "loot_table", "blocks", name + ".json"),
               {"type": "minecraft:block", "pools": pools, "random_sequence": f"{MOD}:blocks/{name}"})


def entry(name, conditions=None, functions=None):
    e = {"type": "minecraft:item", "name": name if ":" in name else P(name)}
    if conditions:
        e["conditions"] = conditions
    if functions:
        e["functions"] = functions
    return e


def pool(entries, conditions=None):
    p = {"rolls": 1, "bonus_rolls": 0, "entries": entries}
    if conditions:
        p["conditions"] = conditions
    return p


def loot_silk_else(name, other, functions=None):
    loot(name, [pool([{"type": "minecraft:alternatives", "children": [
        entry(name, [SILK]), entry(other, [{"condition": "minecraft:survives_explosion"}], functions)]}])])


def loot_tables():
    for b in ("venus_cobblestone", "venus_stone_bricks", "venus_black_rock", "venus_fumarole", "venus_mud", "venus_soil",
              "venus_tar", "venus_log", "venus_wood", "venus_planks", "venus_stairs", "venus_horsetail", "venus_cycad",
              "venus_fire_lily", "venus_glowcap", "venus_hanging_vines"):
        loot_self(b)
    loot_silk_else("venus_stone", "venus_cobblestone")
    loot_silk_else("venus_moss", "venus_soil")
    loot("venus_slab", [pool([entry("venus_slab", functions=[
        {"function": "minecraft:set_count", "add": False, "count": 2.0,
         "conditions": [{"condition": "minecraft:block_state_property", "block": P("venus_slab"),
                         "properties": {"type": "double"}}]},
        {"function": "minecraft:explosion_decay"}])])])
    for leaves in ("venus_leaves", "venus_amber_leaves"):
        loot(leaves, [
            pool([entry(leaves, [SHEARS_OR_SILK])]),
            pool([entry("minecraft:stick", [{"condition": "minecraft:table_bonus", "enchantment": "minecraft:fortune",
                                             "chances": [0.02, 0.022222223, 0.025, 0.033333335, 0.1]}],
                        [{"function": "minecraft:set_count", "add": False,
                          "count": {"type": "minecraft:uniform", "min": 1.0, "max": 2.0}},
                         {"function": "minecraft:explosion_decay"}])],
                 [{"condition": "minecraft:inverted", "term": SHEARS_OR_SILK}])])
    loot("venus_sedge", [pool([entry("venus_sedge", [SHEARS])])])
    for b in ("venus_tree_fern", "venus_giant_fern", "venus_glowstalk"):
        loot(b, [pool([entry(b, [{"condition": "minecraft:block_state_property", "block": P(b),
                                  "properties": {"half": "lower"}}])],
                      [{"condition": "minecraft:survives_explosion"}])])
    loot_silk_else("venus_glowcap_block", "venus_glowcap", [
        {"function": "minecraft:set_count", "add": False, "count": {"type": "minecraft:uniform", "min": -4.0, "max": 2.0}},
        {"function": "minecraft:limit_count", "limit": {"min": 0}}])
    loot("venus_glowcap_stem", [pool([entry("venus_glowcap_stem", [SILK])])])


def tags():
    m = lambda *names: [P(n) for n in names]
    add_to_tag("block/mineable/pickaxe", m("venus_stone", "venus_cobblestone", "venus_stone_bricks", "venus_black_rock",
                                           "venus_fumarole"))
    add_to_tag("block/mineable/shovel", m("venus_mud", "venus_soil", "venus_moss", "venus_tar"))
    add_to_tag("block/mineable/axe", m("venus_log", "venus_wood", "venus_planks", "venus_stairs", "venus_slab",
                                       "venus_glowcap_block", "venus_glowcap_stem", "venus_hanging_vines"))
    add_to_tag("block/mineable/hoe", m("venus_leaves", "venus_amber_leaves", "venus_moss"))
    logs = m("venus_log", "venus_wood")
    tag("block/venus_logs", logs, namespace=MOD)
    tag("item/venus_logs", logs, namespace=MOD)
    for kind in ("block", "item"):
        add_to_tag(f"{kind}/logs", [f"#{MOD}:venus_logs"])
        add_to_tag(f"{kind}/logs_that_burn", [f"#{MOD}:venus_logs"])
        add_to_tag(f"{kind}/planks", m("venus_planks"))
        add_to_tag(f"{kind}/wooden_stairs", m("venus_stairs"))
        add_to_tag(f"{kind}/wooden_slabs", m("venus_slab"))
        add_to_tag(f"{kind}/leaves", m("venus_leaves", "venus_amber_leaves"))
    add_to_tag("item/stone_crafting_materials", m("venus_cobblestone"))
    add_to_tag("item/stone_tool_materials", m("venus_cobblestone"))
    add_to_tag("block/dirt", m("venus_soil", "venus_moss", "venus_mud"))
    add_to_tag("block/climbable", m("venus_hanging_vines"))
    add_to_tag("block/animals_spawnable_on", m("venus_moss", "venus_soil"))
    add_to_tag("block/parrots_spawnable_on", m("venus_moss"))
    add_to_tag("block/frogs_spawnable_on", m("venus_moss", "venus_mud"))
    plants = m("venus_sedge", "venus_horsetail", "venus_fire_lily", "venus_giant_fern", "venus_glowcap",
               "venus_hanging_vines")
    add_to_tag("block/replaceable_by_trees", plants)
    add_to_tag("block/replaceable_by_mushrooms", plants)
    add_to_tag("block/enchantment_power_transmitter", m("venus_sedge"))
    # world-gen helper tags
    tag("block/venus_carver_replaceables", m("venus_stone", "venus_black_rock", "venus_soil", "venus_moss", "venus_mud",
                                             "venus_tar") + ["minecraft:water"], namespace=MOD)
    tag("block/venus_stone_replaceables", m("venus_stone"), namespace=MOD)


def recipes():
    shapeless("venus_planks", [f"#{MOD}:venus_logs"], "venus_planks", count=4, category="building")
    shaped("venus_wood", ["LL", "LL"], {"L": "venus_log"}, "venus_wood", count=3, category="building")
    shaped("venus_stairs", ["P  ", "PP ", "PPP"], {"P": "venus_planks"}, "venus_stairs", count=4, category="building")
    shaped("venus_slab", ["PPP"], {"P": "venus_planks"}, "venus_slab", count=6, category="building")
    shaped("venus_stone_bricks", ["SS", "SS"], {"S": "venus_stone"}, "venus_stone_bricks", count=4, category="building")
    cooking("venus_stone_from_smelting", "smelting", "venus_cobblestone", "venus_stone", 0.1, 200)
    shapeless("torch_from_venus_glowcap", ["venus_glowcap", "minecraft:stick"], "minecraft:torch", count=2)


# =====================================================================================================================
# World generation
# =====================================================================================================================
BIOMES = ("venus_jungle", "venus_fern_swamp", "venus_cycad_plains", "venus_volcanic_highlands", "venus_glowcap_hollows",
          "venus_steaming_sea")


def configured(name, ftype, config):
    write_json(os.path.join(DATA, "worldgen", "configured_feature", name + ".json"), {"type": ftype, "config": config})


def placed(name, feature, placement):
    write_json(os.path.join(DATA, "worldgen", "placed_feature", name + ".json"),
               {"feature": feature if ":" in feature else P(feature), "placement": placement})


def provider(state):
    return {"type": "minecraft:simple_state_provider", "state": state}


AIR = {"type": "minecraft:matching_blocks", "blocks": "minecraft:air"}
LEAF_STATE = B("venus_leaves", distance=7, persistent=False, waterlogged=False)
LOG_STATE = B("venus_log", axis="y")


def biome_filter():
    return {"type": "minecraft:biome"}


def count(n):
    return {"type": "minecraft:count", "count": n}


def rarity(n):
    return {"type": "minecraft:rarity_filter", "chance": n}


def heightmap(kind):
    return {"type": "minecraft:heightmap", "heightmap": kind}


SQUARE = {"type": "minecraft:in_square"}


def would_survive(state):
    return {"type": "minecraft:block_predicate_filter", "predicate": {"type": "minecraft:would_survive", "state": state}}


def on_dirt():
    return {"type": "minecraft:block_predicate_filter",
            "predicate": {"type": "minecraft:matching_block_tag", "tag": "minecraft:dirt", "offset": [0, -1, 0]}}


def tree(trunk_placer, foliage_placer, minimum_size, decorators=(), trunk=LOG_STATE, leaves=LEAF_STATE, root_placer=None):
    cfg = {"decorators": list(decorators),
           "dirt_provider": provider(B("venus_soil")),
           "foliage_placer": foliage_placer,
           "foliage_provider": provider(leaves),
           "force_dirt": False, "ignore_vines": True,
           "minimum_size": minimum_size,
           "trunk_placer": trunk_placer,
           "trunk_provider": provider(trunk)}
    if root_placer:
        cfg["root_placer"] = root_placer
    return cfg


def patch(name, state_provider, tries, xz=7, y=3, predicate=None, block_feature=None):
    pred = predicate or AIR
    feature = block_feature or {"type": "minecraft:simple_block", "config": {"to_place": state_provider}}
    configured(name, "minecraft:random_patch", {
        "feature": {"feature": feature,
                    "placement": [{"type": "minecraft:block_predicate_filter", "predicate": pred}]},
        "tries": tries, "xz_spread": xz, "y_spread": y})


def features():
    # ---------------- trees ----------------
    vine_drape = {"type": "minecraft:attached_to_leaves", "probability": 0.18, "exclusion_radius_xz": 1,
                  "exclusion_radius_y": 0, "required_empty_blocks": 2, "directions": ["down"],
                  "block_provider": provider(B("venus_hanging_vines", tip=True))}
    configured("venus_giant_tree", "minecraft:tree", tree(
        {"type": "minecraft:mega_jungle_trunk_placer", "base_height": 18, "height_rand_a": 4, "height_rand_b": 12},
        {"type": "minecraft:jungle_foliage_placer", "height": 3, "offset": 0, "radius": 3},
        {"type": "minecraft:two_layers_feature_size", "limit": 1, "lower_size": 1, "upper_size": 2},
        [vine_drape]))
    for name, leaves in (("venus_canopy_tree", LEAF_STATE),
                         ("venus_amber_tree", B("venus_amber_leaves", distance=7, persistent=False, waterlogged=False))):
        configured(name, "minecraft:tree", tree(
            {"type": "minecraft:fancy_trunk_placer", "base_height": 9, "height_rand_a": 5, "height_rand_b": 0},
            {"type": "minecraft:fancy_foliage_placer", "height": 4, "offset": 4, "radius": 2},
            {"type": "minecraft:two_layers_feature_size", "limit": 0, "lower_size": 0, "upper_size": 0,
             "min_clipped_height": 4},
            [vine_drape], leaves=leaves))
    # swamp cypress-like tree on buttress roots (mangrove root placer, giant-tree wood)
    configured("venus_buttress_tree", "minecraft:tree", tree(
        {"type": "minecraft:upwards_branching_trunk_placer", "base_height": 4, "height_rand_a": 2, "height_rand_b": 3,
         "can_grow_through": "#minecraft:mangrove_logs_can_grow_through",
         "extra_branch_length": {"type": "minecraft:uniform", "min_inclusive": 0, "max_inclusive": 1},
         "extra_branch_steps": {"type": "minecraft:uniform", "min_inclusive": 1, "max_inclusive": 3},
         "place_branch_per_log_probability": 0.4},
        {"type": "minecraft:random_spread_foliage_placer", "foliage_height": 2, "leaf_placement_attempts": 70,
         "offset": 0, "radius": 3},
        {"type": "minecraft:two_layers_feature_size", "limit": 2, "lower_size": 0, "upper_size": 2},
        [vine_drape],
        root_placer={"type": "minecraft:mangrove_root_placer",
                     "mangrove_root_placement": {"can_grow_through": "#minecraft:mangrove_roots_can_grow_through",
                                                 "max_root_length": 12, "max_root_width": 6,
                                                 "muddy_roots_in": [P("venus_mud")],
                                                 "muddy_roots_provider": provider(LOG_STATE),
                                                 "random_skew_chance": 0.2},
                     "root_provider": provider(B("venus_wood", axis="y")),
                     "trunk_offset_y": {"type": "minecraft:uniform", "min_inclusive": 1, "max_inclusive": 3}}))
    configured("venus_jungle_bush", "minecraft:tree", tree(
        {"type": "minecraft:straight_trunk_placer", "base_height": 1, "height_rand_a": 0, "height_rand_b": 0},
        {"type": "minecraft:bush_foliage_placer", "height": 2, "offset": 1, "radius": 2},
        {"type": "minecraft:two_layers_feature_size", "limit": 0, "lower_size": 0, "upper_size": 0}))
    sapling_check = would_survive(B("minecraft:jungle_sapling", stage=0))
    for t in ("venus_giant_tree", "venus_canopy_tree", "venus_amber_tree", "venus_buttress_tree", "venus_jungle_bush"):
        placed(f"{t}_checked", t, [sapling_check])

    configured("trees_venus_jungle", "minecraft:random_selector", {
        "default": P("venus_canopy_tree_checked"),
        "features": [{"chance": 0.45, "feature": P("venus_giant_tree_checked")},
                     {"chance": 0.12, "feature": P("venus_amber_tree_checked")},
                     {"chance": 0.3, "feature": P("venus_jungle_bush_checked")}]})
    placed("trees_venus_jungle", "trees_venus_jungle", [
        count({"type": "minecraft:weighted_list", "distribution": [{"data": 22, "weight": 9}, {"data": 26, "weight": 1}]}),
        SQUARE, {"type": "minecraft:surface_water_depth_filter", "max_water_depth": 0}, heightmap("OCEAN_FLOOR"),
        biome_filter()])
    configured("trees_venus_swamp", "minecraft:random_selector", {
        "default": P("venus_buttress_tree_checked"),
        "features": [{"chance": 0.2, "feature": P("venus_jungle_bush_checked")}]})
    placed("trees_venus_swamp", "trees_venus_swamp", [
        count({"type": "minecraft:weighted_list", "distribution": [{"data": 3, "weight": 3}, {"data": 5, "weight": 1}]}),
        SQUARE, {"type": "minecraft:surface_water_depth_filter", "max_water_depth": 2}, heightmap("OCEAN_FLOOR"),
        biome_filter()])
    configured("trees_venus_sparse", "minecraft:random_selector", {
        "default": P("venus_jungle_bush_checked"),
        "features": [{"chance": 0.2, "feature": P("venus_canopy_tree_checked")},
                     {"chance": 0.12, "feature": P("venus_amber_tree_checked")}]})
    placed("trees_venus_plains", "trees_venus_sparse", [
        rarity(2), SQUARE, {"type": "minecraft:surface_water_depth_filter", "max_water_depth": 0},
        heightmap("OCEAN_FLOOR"), biome_filter()])
    placed("trees_venus_highlands", "trees_venus_sparse", [
        rarity(6), SQUARE, {"type": "minecraft:surface_water_depth_filter", "max_water_depth": 0},
        heightmap("OCEAN_FLOOR"), biome_filter()])

    # ---------------- giant glowcaps ----------------
    all_sides = {"down": "false", "east": "true", "north": "true", "south": "true", "up": "true", "west": "true"}
    configured("huge_venus_glowcap", "minecraft:huge_red_mushroom", {
        "cap_provider": provider({"Name": P("venus_glowcap_block"), "Properties": dict(all_sides)}),
        "stem_provider": provider({"Name": P("venus_glowcap_stem"),
                                   "Properties": {**all_sides, "up": "false"}}),
        "foliage_radius": 2})
    configured("huge_venus_glowcap_flat", "minecraft:huge_brown_mushroom", {
        "cap_provider": provider({"Name": P("venus_glowcap_block"), "Properties": dict(all_sides)}),
        "stem_provider": provider({"Name": P("venus_glowcap_stem"),
                                   "Properties": {**all_sides, "up": "false"}}),
        "foliage_radius": 3})
    configured("venus_glowcaps_huge", "minecraft:random_selector", {
        "default": P("huge_venus_glowcap_flat_checked"),
        "features": [{"chance": 0.5, "feature": P("huge_venus_glowcap_checked")}]})
    placed("huge_venus_glowcap_checked", "huge_venus_glowcap", [on_dirt()])
    placed("huge_venus_glowcap_flat_checked", "huge_venus_glowcap_flat", [on_dirt()])
    placed("venus_glowcaps_huge", "venus_glowcaps_huge", [
        count(4), SQUARE, {"type": "minecraft:surface_water_depth_filter", "max_water_depth": 0},
        heightmap("OCEAN_FLOOR"), biome_filter()])

    # ---------------- ground cover & plants ----------------
    not_water = {"type": "minecraft:all_of", "predicates": [AIR, {"type": "minecraft:matching_block_tag",
                                                                  "tag": "minecraft:dirt", "offset": [0, -1, 0]}]}
    patch("patch_venus_sedge", provider(B("venus_sedge")), 48, predicate=not_water)
    patch("patch_venus_horsetail", provider(B("venus_horsetail")), 40, xz=5, y=2, predicate=not_water)
    patch("patch_venus_cycad", provider(B("venus_cycad")), 18, xz=6, y=2, predicate=not_water)
    patch("patch_venus_fire_lily", provider(B("venus_fire_lily")), 24, xz=5, y=2, predicate=not_water)
    patch("patch_venus_glowcap", provider(B("venus_glowcap")), 32, xz=6, y=3)
    for tall in ("venus_tree_fern", "venus_giant_fern", "venus_glowstalk"):
        patch(f"patch_{tall}", None, 40 if tall != "venus_tree_fern" else 24, xz=7, y=3, predicate=AIR,
              block_feature={"type": "minecraft:simple_block",
                             "config": {"to_place": provider(B(tall, half="lower"))}})
    surface = lambda n: [count(n), SQUARE, heightmap("WORLD_SURFACE_WG"), biome_filter()]
    surface_rare = lambda n: [rarity(n), SQUARE, heightmap("MOTION_BLOCKING"), biome_filter()]
    placed("patch_venus_sedge_dense", "patch_venus_sedge", surface(22))
    placed("patch_venus_sedge", "patch_venus_sedge", surface(8))
    placed("patch_venus_horsetail", "patch_venus_horsetail", surface(3))
    placed("patch_venus_horsetail_swamp", "patch_venus_horsetail", surface(8))
    placed("patch_venus_cycad", "patch_venus_cycad", surface(4))
    placed("patch_venus_cycad_sparse", "patch_venus_cycad", surface_rare(2))
    placed("patch_venus_fire_lily", "patch_venus_fire_lily", surface_rare(3))
    placed("patch_venus_fire_lily_plains", "patch_venus_fire_lily", surface(2))
    placed("patch_venus_glowcap", "patch_venus_glowcap", surface(3))
    placed("patch_venus_glowcap_sparse", "patch_venus_glowcap", surface_rare(4))
    placed("patch_venus_tree_fern", "patch_venus_tree_fern", surface(2))
    placed("patch_venus_tree_fern_swamp", "patch_venus_tree_fern", surface(5))
    placed("patch_venus_giant_fern", "patch_venus_giant_fern", surface(4))
    placed("patch_venus_giant_fern_sparse", "patch_venus_giant_fern", surface_rare(2))
    placed("patch_venus_glowstalk", "patch_venus_glowstalk", surface(3))

    # hanging lianas under the canopy: scan up from the ground for the underside of leaves
    configured("venus_lianas", "minecraft:block_column", {
        "allowed_placement": AIR, "direction": "down", "prioritize_tip": True,
        "layers": [{"height": {"type": "minecraft:uniform", "min_inclusive": 1, "max_inclusive": 7},
                    "provider": provider(B("venus_hanging_vines", tip=False))},
                   {"height": 1, "provider": provider(B("venus_hanging_vines", tip=True))}]})
    placed("venus_lianas", "venus_lianas", [
        count(90), SQUARE, heightmap("MOTION_BLOCKING_NO_LEAVES"),
        {"type": "minecraft:environment_scan", "direction_of_search": "up", "max_steps": 28,
         "allowed_search_condition": AIR,
         "target_condition": {"type": "minecraft:matching_block_tag", "tag": "minecraft:leaves"}},
        {"type": "minecraft:random_offset", "xz_spread": 0, "y_spread": -1}, biome_filter()])

    # cave fungi: glowcaps and glowstalks on cave floors everywhere on Venus
    placed("venus_cave_glowcaps", "patch_venus_glowcap", [
        count(40), SQUARE,
        {"type": "minecraft:height_range", "height": {"type": "minecraft:uniform",
                                                      "min_inclusive": {"above_bottom": 8}, "max_inclusive": {"absolute": 56}}},
        {"type": "minecraft:environment_scan", "direction_of_search": "down", "max_steps": 12,
         "allowed_search_condition": AIR, "target_condition": {"type": "minecraft:solid"}},
        {"type": "minecraft:random_offset", "xz_spread": 0, "y_spread": 1}, biome_filter()])
    placed("venus_cave_glowstalks", "patch_venus_glowstalk", [
        count(12), SQUARE,
        {"type": "minecraft:height_range", "height": {"type": "minecraft:uniform",
                                                      "min_inclusive": {"above_bottom": 8}, "max_inclusive": {"absolute": 48}}},
        {"type": "minecraft:environment_scan", "direction_of_search": "down", "max_steps": 12,
         "allowed_search_condition": AIR, "target_condition": {"type": "minecraft:solid"}},
        {"type": "minecraft:random_offset", "xz_spread": 0, "y_spread": 1}, biome_filter()])

    # ---------------- lakes, pits, springs ----------------
    configured("venus_tar_pit", "minecraft:lake", {"fluid": provider(B("venus_tar")), "barrier": provider(B("venus_mud"))})
    placed("venus_tar_pit", "venus_tar_pit", [rarity(9), SQUARE, heightmap("WORLD_SURFACE_WG"), biome_filter()])
    placed("venus_tar_pit_rare", "venus_tar_pit", [rarity(40), SQUARE, heightmap("WORLD_SURFACE_WG"), biome_filter()])
    # hot springs: our own small feature (venus/HotSpringFeature.java). minecraft:lake must not be used for water:
    # it looks up the biome of its whole 16x16 surface to freeze cold lakes, and the biome sampler's fuzzy zoom
    # can then read two chunks away from the origin chunk, outside the region a feature may touch ("Requested
    # chunk unavailable during world generation"). Tar and lava are no water, so their lakes never do that.
    configured("venus_hot_spring", P("hot_spring"), {})
    placed("venus_hot_spring", "venus_hot_spring", [rarity(5), SQUARE, heightmap("WORLD_SURFACE_WG"), biome_filter()])
    placed("venus_hot_spring_rare", "venus_hot_spring", [rarity(30), SQUARE, heightmap("WORLD_SURFACE_WG"),
                                                         biome_filter()])
    # vents at the bottom of hot springs: look down through the water for the black rock basin
    configured("venus_spring_vent", "minecraft:simple_block", {"to_place": provider(B("venus_fumarole"))})
    placed("venus_spring_vents", "venus_spring_vent", [
        count(6), SQUARE, heightmap("WORLD_SURFACE_WG"),
        {"type": "minecraft:environment_scan", "direction_of_search": "down", "max_steps": 10,
         "allowed_search_condition": {"type": "minecraft:matching_fluids", "fluids": "minecraft:water"},
         "target_condition": {"type": "minecraft:matching_blocks", "blocks": P("venus_black_rock")}},
        biome_filter()])
    configured("venus_lava_lake", "minecraft:lake", {"fluid": provider(B("minecraft:lava", level=0)),
                                                     "barrier": provider(B("venus_black_rock", axis="y"))})
    placed("venus_lava_lake_underground", "venus_lava_lake", [
        rarity(9), SQUARE,
        {"type": "minecraft:height_range", "height": {"type": "minecraft:uniform", "min_inclusive": {"absolute": 0},
                                                      "max_inclusive": {"below_top": 0}}},
        {"type": "minecraft:environment_scan", "direction_of_search": "down", "max_steps": 32,
         "target_condition": {"type": "minecraft:all_of", "predicates": [
             {"type": "minecraft:not", "predicate": {"type": "minecraft:matching_blocks", "blocks": "minecraft:air"}},
             {"type": "minecraft:inside_world_bounds", "offset": [0, -5, 0]}]}},
        {"type": "minecraft:surface_relative_threshold_filter", "heightmap": "OCEAN_FLOOR_WG", "max_inclusive": -5},
        biome_filter()])
    configured("venus_cinder_cone", P("cinder_cone"), {})
    placed("venus_cinder_cone", "venus_cinder_cone", [rarity(7), SQUARE, heightmap("WORLD_SURFACE_WG"), biome_filter()])
    configured("venus_fumarole_field", "minecraft:random_patch", {
        "feature": {"feature": {"type": "minecraft:simple_block", "config": {"to_place": provider(B("venus_fumarole"))}},
                    "placement": [{"type": "minecraft:block_predicate_filter", "predicate": {
                        "type": "minecraft:all_of", "predicates": [
                            {"type": "minecraft:matching_blocks", "blocks": P("venus_black_rock")},
                            {"type": "minecraft:matching_blocks", "blocks": "minecraft:air", "offset": [0, 1, 0]}]}}]},
        "tries": 6, "xz_spread": 4, "y_spread": 1})
    placed("venus_fumarole_field", "venus_fumarole_field", [
        rarity(3), SQUARE, heightmap("WORLD_SURFACE_WG"), {"type": "minecraft:random_offset", "xz_spread": 0, "y_spread": -1},
        biome_filter()])
    stone_valid = [P("venus_stone"), P("venus_black_rock"), P("venus_soil")]
    configured("venus_spring_water", "minecraft:spring_feature", {
        "hole_count": 1, "requires_block_below": True, "rock_count": 4,
        "state": {"Name": "minecraft:water", "Properties": {"falling": "true"}}, "valid_blocks": stone_valid})
    placed("venus_spring_water", "venus_spring_water", [
        count(25), SQUARE, {"type": "minecraft:height_range", "height": {
            "type": "minecraft:uniform", "min_inclusive": {"above_bottom": 0}, "max_inclusive": {"absolute": 192}}},
        biome_filter()])
    configured("venus_spring_lava", "minecraft:spring_feature", {
        "hole_count": 1, "requires_block_below": True, "rock_count": 4,
        "state": {"Name": "minecraft:lava", "Properties": {"falling": "true"}}, "valid_blocks": stone_valid})
    placed("venus_spring_lava", "venus_spring_lava", [
        count(20), SQUARE, {"type": "minecraft:height_range", "height": {
            "type": "minecraft:very_biased_to_bottom", "min_inclusive": {"above_bottom": 0},
            "max_inclusive": {"below_top": 8}, "inner": 8}}, biome_filter()])

    # ---------------- underground blobs ----------------
    def ore(name, state, size, n, lo, hi, discard=0.0):
        configured(name, "minecraft:ore", {"discard_chance_on_air_exposure": discard, "size": size, "targets": [
            {"state": state, "target": {"predicate_type": "minecraft:tag_match", "tag": f"{MOD}:venus_stone_replaceables"}}]})
        placed(name, name, [count(n), SQUARE, {"type": "minecraft:height_range", "height": {
            "type": "minecraft:uniform", "min_inclusive": {"absolute": lo}, "max_inclusive": {"absolute": hi}}},
            biome_filter()])
    ore("ore_venus_soil", B("venus_soil"), 33, 7, 0, 160)
    ore("ore_venus_black_rock", B("venus_black_rock", axis="y"), 64, 3, -16, 128)
    ore("ore_venus_tar", B("venus_tar"), 24, 3, -40, 40)
    ore("ore_venus_mud", B("venus_mud"), 33, 2, 0, 70)
    configured("disk_venus_mud", "minecraft:disk", {
        "half_height": 1, "radius": {"type": "minecraft:uniform", "min_inclusive": 2, "max_inclusive": 5},
        "state_provider": {"fallback": provider(B("venus_mud")), "rules": []},
        "target": {"type": "minecraft:matching_blocks", "blocks": [P("venus_soil"), P("venus_stone"), P("venus_moss")]}})
    placed("disk_venus_mud", "disk_venus_mud", [
        count(2), SQUARE, heightmap("OCEAN_FLOOR_WG"),
        {"type": "minecraft:block_predicate_filter", "predicate": {"type": "minecraft:matching_fluids",
                                                                   "fluids": "minecraft:water"}}, biome_filter()])


# =====================================================================================================================
# Ores & local propellant: everything a stranded crew needs to refuel the Liberty I and fly home
# =====================================================================================================================
# name: (dark, mid, light, seed)
ORE_COLORS = {
    "venus_coal_ore": ((24, 22, 26), (44, 40, 46), (66, 62, 70), 301),
    "venus_iron_ore": ((150, 106, 80), (204, 160, 124), (232, 204, 172), 302),
    "venus_copper_ore": ((118, 62, 40), (190, 108, 70), (96, 180, 150), 303),
    "venus_gold_ore": ((184, 124, 18), (246, 206, 52), (255, 246, 160), 304),
    "venus_redstone_ore": ((128, 8, 8), (220, 24, 24), (255, 108, 96), 305),
    "venus_diamond_ore": ((22, 132, 128), (92, 226, 214), (214, 255, 250), 306),
    "venus_bauxite_ore": ((120, 56, 34), (176, 88, 52), (214, 132, 84), 307),
    "venus_titanium_ore": ((96, 108, 140), (150, 164, 196), (206, 216, 240), 308),
}
CRYO = [(92, 150, 186), (150, 206, 232), (204, 238, 252), (246, 254, 255)]
ORE_BLOCKS = list(ORE_COLORS) + ["venus_oil_shale", "venus_cryolite_ore"]
SAND = [(58, 48, 46), (74, 62, 58), (92, 78, 70), (112, 96, 84)]


def tex_venus_ore(dark, mid, light, seed):
    """Same cluster layout as the Earth ores (gen_resources.ore), set in Venusian stone."""
    img = tex_stone()
    rnd = random.Random(seed)
    for cx, cy in ((3, 3), (10, 2), (5, 9), (12, 10), (8, 13)):
        pts = [(cx, cy), (cx + 1, cy), (cx, cy + 1), (cx + 1, cy + 1)]
        if rnd.random() < 0.6:
            pts.append((cx + 2, cy + 1))
        if rnd.random() < 0.6:
            pts.append((cx - 1, cy))
        for x, y in pts:
            put(img, x, y, mid)
        put(img, cx + 1, cy + 1, dark)
        put(img, cx, cy, light)
    return img


def tex_venus_oil_shale():
    """Sedimentary strata of dark kerogen shale with an oily violet-green sheen, in mauve stone."""
    img = tex_stone()
    rnd = random.Random(311)
    shale = [(40, 34, 40), (54, 46, 52), (70, 60, 66)]
    for y in range(16):
        band = (y // 3) % 2 == 0
        for x in range(16):
            if band and rnd.random() < 0.85:
                put(img, x, y, shale[0] if y % 3 == 1 else shale[1 if rnd.random() < 0.7 else 2])
    for x, y in ((3, 1), (4, 1), (10, 7), (11, 7), (12, 7), (6, 13), (7, 13), (13, 1), (1, 7)):
        put(img, x, y, (84, 104, 96) if (x + y) % 2 else (104, 82, 122))
    return img


def crystal(img, x0, y0, h, cols):
    """A small hexagonal prism pointing up: 2px wide body, a 1px tip."""
    for i in range(h):
        put(img, x0, y0 - i, cols[2] if i < h - 1 else cols[3])
        put(img, x0 + 1, y0 - i, cols[1])
    put(img, x0, y0 - h, cols[3])
    put(img, x0 - 1, y0, cols[0])
    put(img, x0 + 2, y0, cols[0])


def tex_venus_cryolite_ore():
    img = tex_stone()
    for x0, y0, h in ((3, 6, 3), (10, 4, 3), (6, 13, 4), (12, 12, 2), (1, 12, 2)):
        crystal(img, x0, y0, h, CRYO)
    return img


def tex_cryolite_crystal():
    """Item: a cluster of frosty pale-blue prisms with a cold glint."""
    img = new()
    outline_c = (54, 92, 124)
    body = [((7, 14), 10, 2), ((4, 14), 6, 2), ((10, 14), 7, 2), ((2, 15), 3, 1), ((12, 15), 4, 1)]
    for (x0, y0), h, w in body:
        for i in range(h):
            for dx in range(w):
                c = CRYO[2] if dx == 0 else CRYO[1]
                if i >= h - 2:
                    c = CRYO[3] if dx == 0 else CRYO[2]
                put(img, x0 + dx, y0 - i, c)
        put(img, x0, y0 - h, CRYO[3])
    # dark outline like vanilla item sprites
    src = img.copy()
    for y in range(16):
        for x in range(16):
            if src.getpixel((x, y))[3] == 0 and any(
                    0 <= x + dx < 16 and 0 <= y + dy < 16 and src.getpixel((x + dx, y + dy))[3]
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                put(img, x, y, outline_c)
    for x, y in ((7, 6), (8, 7), (4, 10), (10, 9)):
        put(img, x, y, (255, 255, 255))
    for x in range(1, 15):
        if img.getpixel((x, 15))[3]:
            put(img, x, 15, CRYO[0])
    return img


def tex_venus_sand():
    img = tonal(321, SAND, [14, 34, 36, 16], octaves=((8, 0.4),), jitter=0.6)
    rnd = random.Random(322)
    for _ in range(9):   # ochre and glassy grains in the black volcanic sand
        put(img, rnd.randrange(16), rnd.randrange(16), OCHRE if rnd.random() < 0.6 else (150, 170, 176))
    return img


def ore_textures():
    for name, (d, m, l, seed) in ORE_COLORS.items():
        save(tex_venus_ore(d, m, l, seed), "block", name)
    save(tex_venus_oil_shale(), "block", "venus_oil_shale")
    save(tex_venus_cryolite_ore(), "block", "venus_cryolite_ore")
    save(tex_venus_sand(), "block", "venus_sand")
    save(tex_cryolite_crystal(), "item", "cryolite_crystal")


def ore_models():
    for name in ORE_BLOCKS + ["venus_sand"]:
        simple(name)
    blockstate("venus_redstone_ore", {"variants": {"lit=false": {"model": P("block/venus_redstone_ore")},
                                                   "lit=true": {"model": P("block/venus_redstone_ore")}}})
    write_json(os.path.join(ASSETS, "models", "item", "cryolite_crystal.json"),
               {"parent": "minecraft:item/generated", "textures": {"layer0": f"{MOD}:item/cryolite_crystal"}})
    item("cryolite_crystal", P("item/cryolite_crystal"))


def ore_loot():
    fortune = {"function": "minecraft:apply_bonus", "enchantment": "minecraft:fortune", "formula": "minecraft:ore_drops"}
    decay = {"function": "minecraft:explosion_decay"}

    def count_fn(lo, hi):
        return {"function": "minecraft:set_count", "add": False,
                "count": {"type": "minecraft:uniform", "min": float(lo), "max": float(hi)}}

    def ore_loot_table(name, drop, functions):
        loot(name, [pool([{"type": "minecraft:alternatives", "children": [
            entry(name, [SILK]), entry(drop, functions=functions)]}])])

    ore_loot_table("venus_coal_ore", "minecraft:coal", [fortune, decay])
    ore_loot_table("venus_iron_ore", "minecraft:raw_iron", [fortune, decay])
    ore_loot_table("venus_copper_ore", "minecraft:raw_copper", [count_fn(2, 5), fortune, decay])
    ore_loot_table("venus_gold_ore", "minecraft:raw_gold", [fortune, decay])
    ore_loot_table("venus_redstone_ore", "minecraft:redstone", [
        count_fn(4, 5), {"function": "minecraft:apply_bonus", "enchantment": "minecraft:fortune",
                         "formula": "minecraft:uniform_bonus_count", "parameters": {"bonusMultiplier": 1}}, decay])
    ore_loot_table("venus_diamond_ore", "minecraft:diamond", [fortune, decay])
    ore_loot_table("venus_bauxite_ore", "raw_aluminum", [fortune, decay])
    ore_loot_table("venus_titanium_ore", "raw_titanium", [fortune, decay])
    ore_loot_table("venus_cryolite_ore", "cryolite_crystal", [count_fn(1, 2), fortune, decay])
    loot_self("venus_oil_shale")    # the shale itself feeds the Fuel Refinery, like Earth's
    loot_self("venus_sand")


VANILLA_ORE_TAGS = {"venus_coal_ore": "coal", "venus_iron_ore": "iron", "venus_copper_ore": "copper",
                    "venus_gold_ore": "gold", "venus_redstone_ore": "redstone", "venus_diamond_ore": "diamond"}


def ore_tags():
    m = lambda *names: [P(n) for n in names]
    add_to_tag("block/mineable/pickaxe", m(*ORE_BLOCKS))
    add_to_tag("block/mineable/shovel", m("venus_sand"))
    add_to_tag("block/needs_stone_tool", m("venus_iron_ore", "venus_copper_ore", "venus_bauxite_ore", "venus_oil_shale",
                                           "venus_cryolite_ore"))
    add_to_tag("block/needs_iron_tool", m("venus_gold_ore", "venus_redstone_ore", "venus_diamond_ore",
                                          "venus_titanium_ore"))
    for kind in ("block", "item"):
        for name, metal in VANILLA_ORE_TAGS.items():
            add_to_tag(f"{kind}/{metal}_ores", m(name))
            add_to_tag(f"{kind}/ores/{metal}", m(name), namespace="c")
        add_to_tag(f"{kind}/ores/aluminum", m("venus_bauxite_ore"), namespace="c")
        add_to_tag(f"{kind}/ores/titanium", m("venus_titanium_ore"), namespace="c")
        add_to_tag(f"{kind}/ores/cryolite", m("venus_cryolite_ore"), namespace="c")
        add_to_tag(f"{kind}/ores/oil_shale", m("venus_oil_shale"), namespace="c")
        add_to_tag(f"{kind}/ores", [f"#c:ores/{x}" for x in list(VANILLA_ORE_TAGS.values())
                                    + ["aluminum", "titanium", "cryolite", "oil_shale"]], namespace="c")
        add_to_tag(f"{kind}/sands", m("venus_sand"), namespace="c")
    add_to_tag("block/sand", m("venus_sand"))
    add_to_tag("item/smelts_to_glass", m("venus_sand"))
    add_to_tag("item/gems/cryolite", m("cryolite_crystal"), namespace="c")
    # local propellant: Venusian oil shale and tar for RP-1, cryolite as the liquefier's coolant
    add_to_tag("item/refinery_input", m("venus_oil_shale", "venus_tar"), namespace=MOD)
    add_to_tag("item/liquefier_input", m("cryolite_crystal"), namespace=MOD)
    # ores sit in stone and in the deep black rock; caves may cut through them
    tag("block/venus_ore_replaceables", m("venus_stone", "venus_black_rock"), namespace=MOD)
    add_to_tag("block/venus_carver_replaceables", m(*ORE_BLOCKS, "venus_sand"), namespace=MOD)


def ore_recipes():
    """Smelting / blasting for silk-touched ore blocks (the raw drops already smelt with the vanilla recipes)."""
    results = {"venus_coal_ore": ("minecraft:coal", 0.1), "venus_iron_ore": ("minecraft:iron_ingot", 0.7),
               "venus_copper_ore": ("minecraft:copper_ingot", 0.7), "venus_gold_ore": ("minecraft:gold_ingot", 1.0),
               "venus_redstone_ore": ("minecraft:redstone", 0.7), "venus_diamond_ore": ("minecraft:diamond", 1.0),
               "venus_bauxite_ore": ("aluminum_ingot", 0.7), "venus_titanium_ore": ("titanium_ingot", 1.0)}
    for ore_name, (result, xp) in results.items():
        out = result.split(":")[-1]
        cooking(f"{out}_from_smelting_{ore_name}", "smelting", ore_name, result, xp, 200)
        cooking(f"{out}_from_blasting_{ore_name}", "blasting", ore_name, result, xp, 100)
    cooking("glass_from_smelting_venus_sand", "smelting", "venus_sand", "minecraft:glass", 0.1, 200)


# Overworld-like distributions (vanilla sizes / counts / height ranges), a little richer in iron and copper.
def height(kind, lo, hi):
    def anchor(v):
        if isinstance(v, dict):
            return v
        return {"absolute": v}
    return {"type": "minecraft:height_range", "height": {"type": f"minecraft:{kind}", "min_inclusive": anchor(lo),
                                                         "max_inclusive": anchor(hi)}}


ORE_PLACEMENTS = [
    # name, block, size, discard, frequency (int count or ("rarity", n) or ("uniform", a, b)), height
    ("ore_venus_coal_upper", "venus_coal_ore", 17, 0.0, 30, ("uniform", 136, {"below_top": 0})),
    ("ore_venus_coal_lower", "venus_coal_ore", 17, 0.5, 16, ("trapezoid", 0, 192)),
    ("ore_venus_iron_upper", "venus_iron_ore", 9, 0.0, 90, ("trapezoid", 80, 384)),
    ("ore_venus_iron_middle", "venus_iron_ore", 9, 0.0, 13, ("trapezoid", -24, 56)),
    ("ore_venus_iron_small", "venus_iron_ore", 4, 0.0, 13, ("uniform", {"above_bottom": 0}, 72)),
    ("ore_venus_copper", "venus_copper_ore", 10, 0.0, 17, ("trapezoid", -16, 112)),
    ("ore_venus_gold", "venus_gold_ore", 9, 0.5, 4, ("trapezoid", -64, 32)),
    ("ore_venus_gold_lower", "venus_gold_ore", 9, 0.5, ("uniform", 0, 1), ("uniform", -64, -48)),
    ("ore_venus_redstone", "venus_redstone_ore", 8, 0.0, 4, ("uniform", {"above_bottom": 0}, 15)),
    ("ore_venus_redstone_lower", "venus_redstone_ore", 8, 0.0, 8,
     ("trapezoid", {"above_bottom": -32}, {"above_bottom": 32})),
    ("ore_venus_diamond", "venus_diamond_ore", 4, 0.5, 7, ("trapezoid", {"above_bottom": -80}, {"above_bottom": 80})),
    ("ore_venus_diamond_medium", "venus_diamond_ore", 8, 0.5, 2, ("uniform", -64, -4)),
    ("ore_venus_diamond_large", "venus_diamond_ore", 12, 0.7, ("rarity", 9),
     ("trapezoid", {"above_bottom": -80}, {"above_bottom": 80})),
    ("ore_venus_diamond_buried", "venus_diamond_ore", 8, 1.0, 4,
     ("trapezoid", {"above_bottom": -80}, {"above_bottom": 80})),
    ("ore_venus_bauxite", "venus_bauxite_ore", 9, 0.0, 12, ("trapezoid", -16, 112)),
    ("ore_venus_titanium", "venus_titanium_ore", 6, 0.4, 6, ("trapezoid", -64, 24)),
    ("ore_venus_oil_shale", "venus_oil_shale", 14, 0.0, 8, ("uniform", 8, 72)),
    ("ore_venus_cryolite", "venus_cryolite_ore", 7, 0.0, 5, ("trapezoid", -64, 24)),
    # volcanic highlands: hydrothermal gold and redstone, cryolite crusts around the deep vents
    ("ore_venus_gold_volcanic", "venus_gold_ore", 9, 0.0, 7, ("uniform", 32, 160)),
    ("ore_venus_redstone_volcanic", "venus_redstone_ore", 8, 0.0, 6, ("uniform", 0, 96)),
    ("ore_venus_cryolite_volcanic", "venus_cryolite_ore", 7, 0.0, 6, ("uniform", -40, 64)),
]
VOLCANIC_ORES = ["ore_venus_gold_volcanic", "ore_venus_redstone_volcanic", "ore_venus_cryolite_volcanic"]
COMMON_ORES = [p[0] for p in ORE_PLACEMENTS if p[0] not in VOLCANIC_ORES]


def ore_features():
    for name, block, size, discard, freq, (kind, lo, hi) in ORE_PLACEMENTS:
        state = B(block, lit=False) if block == "venus_redstone_ore" else B(block)
        configured(name, "minecraft:ore", {"discard_chance_on_air_exposure": discard, "size": size, "targets": [
            {"state": state, "target": {"predicate_type": "minecraft:tag_match",
                                        "tag": f"{MOD}:venus_ore_replaceables"}}]})
        if isinstance(freq, int):
            first = count(freq)
        elif freq[0] == "rarity":
            first = rarity(freq[1])
        else:
            first = count({"type": "minecraft:uniform", "min_inclusive": freq[1], "max_inclusive": freq[2]})
        placed(name, name, [first, SQUARE, height(kind, lo, hi), biome_filter()])
    # beaches and shallows of volcanic sand (glass for vacuum tubes and machine windows)
    configured("disk_venus_sand", "minecraft:disk", {
        "half_height": 2, "radius": {"type": "minecraft:uniform", "min_inclusive": 2, "max_inclusive": 6},
        "state_provider": {"fallback": provider(B("venus_sand")), "rules": []},
        "target": {"type": "minecraft:matching_blocks", "blocks": [P("venus_mud"), P("venus_soil"), P("venus_sand")]}})
    placed("disk_venus_sand", "disk_venus_sand", [
        count(3), SQUARE, heightmap("OCEAN_FLOOR_WG"),
        {"type": "minecraft:block_predicate_filter", "predicate": {"type": "minecraft:matching_fluids",
                                                                   "fluids": "minecraft:water"}}, biome_filter()])


def carvers():
    for name, base in (("venus_cave", "cave"), ("venus_cave_extra", "cave_extra_underground"), ("venus_canyon", "canyon")):
        src = CARVERS[base]
        cfg = json.loads(json.dumps(src))
        cfg["config"]["replaceable"] = f"#{MOD}:venus_carver_replaceables"
        write_json(os.path.join(DATA, "worldgen", "configured_carver", name + ".json"), cfg)


_DEBUG = {"air_state": {"Name": "minecraft:crimson_button",
                        "Properties": {"face": "wall", "facing": "north", "powered": "false"}},
          "barrier_state": {"Name": "minecraft:glass"},
          "lava_state": {"Name": "minecraft:orange_stained_glass"},
          "water_state": {"Name": "minecraft:candle", "Properties": {"candles": "1", "lit": "false",
                                                                    "waterlogged": "false"}}}
CARVERS = {
    "cave": {"type": "minecraft:cave", "config": {
        "debug_settings": _DEBUG,
        "floor_level": {"type": "minecraft:uniform", "max_exclusive": -0.4, "min_inclusive": -1.0},
        "horizontal_radius_multiplier": {"type": "minecraft:uniform", "max_exclusive": 1.4, "min_inclusive": 0.7},
        "lava_level": {"above_bottom": 8}, "probability": 0.15, "replaceable": "",
        "vertical_radius_multiplier": {"type": "minecraft:uniform", "max_exclusive": 1.3, "min_inclusive": 0.8},
        "y": {"type": "minecraft:uniform", "max_inclusive": {"absolute": 180}, "min_inclusive": {"above_bottom": 8}},
        "yScale": {"type": "minecraft:uniform", "max_exclusive": 0.9, "min_inclusive": 0.1}}},
    "cave_extra_underground": {"type": "minecraft:cave", "config": {
        "debug_settings": {**_DEBUG, "air_state": {"Name": "minecraft:oak_button",
                                                   "Properties": {"face": "wall", "facing": "north", "powered": "false"}}},
        "floor_level": {"type": "minecraft:uniform", "max_exclusive": -0.4, "min_inclusive": -1.0},
        "horizontal_radius_multiplier": {"type": "minecraft:uniform", "max_exclusive": 1.4, "min_inclusive": 0.7},
        "lava_level": {"above_bottom": 8}, "probability": 0.07, "replaceable": "",
        "vertical_radius_multiplier": {"type": "minecraft:uniform", "max_exclusive": 1.3, "min_inclusive": 0.8},
        "y": {"type": "minecraft:uniform", "max_inclusive": {"absolute": 47}, "min_inclusive": {"above_bottom": 8}},
        "yScale": {"type": "minecraft:uniform", "max_exclusive": 0.9, "min_inclusive": 0.1}}},
    "canyon": {"type": "minecraft:canyon", "config": {
        "debug_settings": {"air_state": {"Name": "minecraft:warped_button",
                                         "Properties": {"face": "wall", "facing": "north", "powered": "false"}},
                           "barrier_state": {"Name": "minecraft:glass"},
                           "lava_state": {"Name": "minecraft:orange_stained_glass"},
                           "water_state": {"Name": "minecraft:candle", "Properties": {"candles": "1", "lit": "false",
                                                                                     "waterlogged": "false"}}},
        "lava_level": {"above_bottom": 8}, "probability": 0.01, "replaceable": "",
        "shape": {"distance_factor": {"type": "minecraft:uniform", "max_exclusive": 1.0, "min_inclusive": 0.75},
                  "horizontal_radius_factor": {"type": "minecraft:uniform", "max_exclusive": 1.0, "min_inclusive": 0.75},
                  "thickness": {"type": "minecraft:trapezoid", "max": 6.0, "min": 0.0, "plateau": 2.0},
                  "vertical_radius_center_factor": 0.0, "vertical_radius_default_factor": 1.0,
                  "width_smoothness": 3},
        "vertical_rotation": {"type": "minecraft:uniform", "max_exclusive": 0.125, "min_inclusive": -0.125},
        "y": {"type": "minecraft:uniform", "max_inclusive": {"absolute": 67}, "min_inclusive": {"absolute": 10}},
        "yScale": 3.0}},
}


# ---------------------------------------------------------------------------------------------------------------------
# Biomes
# ---------------------------------------------------------------------------------------------------------------------

def dino_spawns_enabled():
    flag = os.environ.get("VENUS_DINO_SPAWNS")
    if flag is not None:
        return flag.strip().lower() in ("1", "true", "yes", "on")
    try:
        with open(JAVA_DINOS, encoding="utf-8") as f:
            src = f.read()
    except OSError:
        return False
    return all(f'"{d}"' in src for d in DINOS)


def spawner(entity, weight, lo, hi):
    return {"type": entity, "maxCount": hi, "minCount": lo, "weight": weight}


def music(sound="minecraft:music.overworld.jungle"):
    return {"default": {"max_delay": 24000, "min_delay": 12000, "sound": sound}}


def biome(name, *, fog, water, water_fog, grass, foliage, steps, spawners, particles=None, extra_attrs=None,
          temperature=0.95, downfall=0.9, sound="minecraft:music.overworld.jungle"):
    attrs = {"minecraft:audio/background_music": music(sound),
             "minecraft:visual/fog_color": fog,
             "minecraft:visual/sky_color": fog,
             "minecraft:visual/water_fog_color": water_fog,
             "minecraft:gameplay/increased_fire_burnout": True,
             "minecraft:gameplay/snow_golem_melts": True}
    if particles:
        attrs["minecraft:visual/ambient_particles"] = particles
    attrs.update(extra_attrs or {})
    feats = [[] for _ in range(11)]
    for step, names in steps.items():
        # one global order for all biomes, so the feature sorter never finds an ordering cycle
        feats[step] = [n if ":" in n else P(n) for n in sorted(names, key=FEATURE_ORDER.index)]
    cats = ("ambient", "axolotls", "creature", "misc", "monster", "underground_water_creature", "water_ambient",
            "water_creature")
    write_json(os.path.join(DATA, "worldgen", "biome", name + ".json"), {
        "attributes": attrs,
        "carvers": [P("venus_cave"), P("venus_cave_extra"), P("venus_canyon")],
        "downfall": downfall,
        "effects": {"water_color": water, "grass_color": grass, "foliage_color": foliage,
                    "dry_foliage_color": "#8a6a3c"},
        "features": feats,
        "has_precipitation": True,
        "spawn_costs": {},
        "spawners": {c: spawners.get(c, []) for c in cats},
        "temperature": temperature})


LAKES, LOCAL, UNDERGROUND_DECOR, ORES, SPRINGS, VEGETAL = 1, 2, 7, 6, 8, 9
FEATURE_ORDER = [
    # lakes
    "venus_tar_pit", "venus_tar_pit_rare", "venus_hot_spring", "venus_hot_spring_rare", "venus_lava_lake_underground",
    # local modifications
    "venus_cinder_cone", "venus_spring_vents",
    # ores
    "ore_venus_soil", "ore_venus_black_rock", "ore_venus_tar", "ore_venus_mud", "disk_venus_mud", "disk_venus_sand",
    *COMMON_ORES, *VOLCANIC_ORES,
    # springs
    "venus_spring_water", "venus_spring_lava",
    # vegetation: big things first, then the undergrowth
    "venus_fumarole_field", "venus_glowcaps_huge", "trees_venus_jungle", "trees_venus_swamp", "trees_venus_plains",
    "trees_venus_highlands", "venus_lianas",
    "patch_venus_giant_fern", "patch_venus_tree_fern", "patch_venus_tree_fern_swamp", "patch_venus_glowstalk",
    "patch_venus_cycad", "patch_venus_sedge_dense", "patch_venus_sedge", "patch_venus_horsetail",
    "patch_venus_horsetail_swamp", "patch_venus_fire_lily", "patch_venus_fire_lily_plains", "patch_venus_cycad_sparse",
    "patch_venus_giant_fern_sparse", "patch_venus_glowcap", "patch_venus_glowcap_sparse",
    "minecraft:seagrass_swamp", "minecraft:patch_waterlily", "minecraft:seagrass_warm", "minecraft:kelp_warm",
    "venus_cave_glowcaps", "venus_cave_glowstalks",
]


def biomes():
    dinos = dino_spawns_enabled()
    raptor = [spawner(P("raptor"), 60, 2, 4)] if dinos else []
    bronto = lambda w: [spawner(P("brontosaurus"), w, 2, 4)] if dinos else []
    trike = lambda w: [spawner(P("triceratops"), w, 2, 5)] if dinos else []
    # second wave: spore-creepers in the dark jungle, pteranodons roosting on the canopy and - very rarely,
    # further throttled in ModDinosaurs - the tyrannosaurus
    creeper = lambda w: [spawner(P("venus_creeper"), w, 1, 1)] if dinos else []
    ptero = lambda w: [spawner(P("pteranodon"), w, 1, 3)] if dinos else []
    rex = lambda w: [spawner(P("tyrannosaurus"), w, 1, 1)] if dinos else []
    # third wave: the sea monster, the swamp crocodile, the armoured tank and the small background life
    plesio = lambda w: [spawner(P("plesiosaur"), w, 1, 2)] if dinos else []
    croc = lambda w: [spawner(P("deinosuchus"), w, 1, 1)] if dinos else []
    anky = lambda w: [spawner(P("ankylosaurus"), w, 1, 3)] if dinos else []
    compy = lambda w: [spawner(P("compsognathus"), w, 3, 6)] if dinos else []
    dragonfly = lambda w: [spawner(P("meganeura"), w, 2, 4)] if dinos else []
    moth = lambda w: [spawner(P("spore_moth"), w, 3, 5)] if dinos else []
    ambient = [spawner("minecraft:bat", 10, 8, 8)]
    caves_water = [spawner("minecraft:glow_squid", 10, 4, 6)]
    common_ores = ["ore_venus_soil", "ore_venus_black_rock", "ore_venus_tar", "ore_venus_mud", "disk_venus_mud"] \
        + COMMON_ORES
    shore_ores = common_ores + ["disk_venus_sand"]
    cave_life = ["venus_cave_glowcaps", "venus_cave_glowstalks"]
    springs = ["venus_spring_water", "venus_spring_lava"]
    spores = [{"particle": {"type": "minecraft:spore_blossom_air"}, "probability": 0.004}]

    biome("venus_jungle", fog="#d9a64e", water="#3f9a7c", water_fog="#1e4a3c", grass="#5f9a4a", foliage="#3f8a5c",
          particles=spores,
          steps={LAKES: ["venus_tar_pit_rare", "venus_lava_lake_underground"], ORES: common_ores,
                 SPRINGS: springs,
                 VEGETAL: ["trees_venus_jungle", "venus_lianas", "patch_venus_giant_fern", "patch_venus_tree_fern",
                           "patch_venus_sedge_dense", "patch_venus_horsetail", "patch_venus_fire_lily",
                           "patch_venus_cycad_sparse", "patch_venus_glowcap_sparse"] + cave_life},
          spawners={"monster": raptor + creeper(15) + rex(2), "ambient": ambient + dragonfly(8),
                    "underground_water_creature": caves_water,
                    "creature": [spawner("minecraft:parrot", 30, 1, 2)] + ptero(12) + compy(8)})
    biome("venus_fern_swamp", fog="#c9a456", water="#4e8c64", water_fog="#26402c", grass="#6a9244", foliage="#52864a",
          extra_attrs={"minecraft:visual/water_fog_end_distance": {"argument": 0.85, "modifier": "multiply"}},
          particles=[{"particle": {"type": "minecraft:white_ash"}, "probability": 0.01}],
          sound="minecraft:music.overworld.swamp",
          steps={LAKES: ["venus_tar_pit", "venus_hot_spring_rare", "venus_lava_lake_underground"],
                 LOCAL: ["venus_spring_vents"], ORES: shore_ores, SPRINGS: springs,
                 VEGETAL: ["trees_venus_swamp", "venus_lianas", "patch_venus_tree_fern_swamp", "patch_venus_giant_fern",
                           "patch_venus_horsetail_swamp", "patch_venus_sedge_dense", "patch_venus_glowcap_sparse",
                           "minecraft:seagrass_swamp", "minecraft:patch_waterlily"] + cave_life},
          spawners={"creature": bronto(8) + [spawner("minecraft:frog", 10, 2, 5)] + ptero(4) + compy(6),
                    "monster": creeper(10) + croc(10), "ambient": ambient + dragonfly(14),
                    "underground_water_creature": caves_water,
                    "water_ambient": [spawner("minecraft:tropical_fish", 25, 8, 8)]})
    biome("venus_cycad_plains", fog="#e0ae58", water="#3f9a7c", water_fog="#1e4a3c", grass="#7d9a48", foliage="#5c8a4a",
          temperature=0.9, downfall=0.6,
          steps={LAKES: ["venus_tar_pit_rare", "venus_lava_lake_underground"], ORES: common_ores, SPRINGS: springs,
                 VEGETAL: ["trees_venus_plains", "patch_venus_cycad", "patch_venus_sedge_dense",
                           "patch_venus_fire_lily_plains", "patch_venus_horsetail", "patch_venus_giant_fern_sparse"]
                 + cave_life},
          spawners={"creature": bronto(10) + trike(14) + compy(10) + anky(4), "monster": rex(3), "ambient": ambient,
                    "underground_water_creature": caves_water})
    biome("venus_volcanic_highlands", fog="#b98a5a", water="#3a8a80", water_fog="#20403c", grass="#7a8a4a",
          foliage="#5a7a4a", temperature=1.2, downfall=0.3, sound="minecraft:music.nether.basalt_deltas",
          particles=[{"particle": {"type": "minecraft:white_ash"}, "probability": 0.05}],
          steps={LAKES: ["venus_hot_spring", "venus_lava_lake_underground"], LOCAL: ["venus_cinder_cone", "venus_spring_vents"],
                 ORES: common_ores + VOLCANIC_ORES, SPRINGS: springs,
                 VEGETAL: ["venus_fumarole_field", "trees_venus_highlands", "patch_venus_sedge",
                           "patch_venus_cycad_sparse", "patch_venus_fire_lily"] + cave_life},
          spawners={"creature": trike(10) + anky(10), "monster": rex(3), "ambient": ambient,
                    "underground_water_creature": caves_water})
    biome("venus_glowcap_hollows", fog="#a78a7a", water="#3a8a8a", water_fog="#1c3a44", grass="#4a8a6a",
          foliage="#3a7a6a", temperature=0.8,
          particles=[{"particle": {"type": "minecraft:spore_blossom_air"}, "probability": 0.02}],
          extra_attrs={"minecraft:visual/sky_light_color": "#c8b0ff"},
          sound="minecraft:music.overworld.lush_caves",
          steps={LAKES: ["venus_tar_pit_rare", "venus_lava_lake_underground"], ORES: common_ores, SPRINGS: springs,
                 VEGETAL: ["venus_glowcaps_huge", "trees_venus_plains", "venus_lianas", "patch_venus_glowstalk",
                           "patch_venus_glowcap", "patch_venus_sedge", "patch_venus_giant_fern_sparse"] + cave_life},
          spawners={"monster": raptor + creeper(25), "ambient": ambient + moth(25),
                    "underground_water_creature": caves_water})
    biome("venus_steaming_sea", fog="#d2a85e", water="#3a9c8c", water_fog="#1a4a44", grass="#5f9a4a",
          foliage="#3f8a5c", sound="minecraft:music.overworld.jungle",
          steps={LAKES: ["venus_lava_lake_underground"], ORES: shore_ores, SPRINGS: springs,
                 VEGETAL: ["minecraft:seagrass_warm", "minecraft:kelp_warm"] + cave_life},
          spawners={"water_ambient": [spawner("minecraft:tropical_fish", 25, 8, 8),
                                      spawner("minecraft:pufferfish", 15, 1, 3)],
                    "water_creature": [spawner("minecraft:dolphin", 2, 1, 2)] + plesio(6),
                    "ambient": ambient, "underground_water_creature": caves_water})
    return dinos


def climate():
    """Multi-noise parameter list (inline in the dimension). Uses the vanilla overworld noise router."""
    full = [-1.0, 1.0]
    entries = []

    def add(b, t=full, h=full, c=full, e=full, w=full):
        entries.append({"biome": P(b), "parameters": {"temperature": t, "humidity": h, "continentalness": c,
                                                      "erosion": e, "weirdness": w, "depth": 0.0, "offset": 0.0}})

    near, far = [-0.11, 0.03], [0.3, 1.0]
    land = [-0.11, 1.0]
    add("venus_steaming_sea", c=[-1.2, -0.19])
    add("venus_fern_swamp", c=[-0.19, -0.11])                       # the steaming shoreline
    add("venus_fern_swamp", c=land, e=[0.45, 1.0], h=[-0.1, 1.0])     # flat wet lowlands
    add("venus_cycad_plains", c=land, e=[0.45, 1.0], h=[-1.0, -0.1])  # flat dry lowlands
    add("venus_volcanic_highlands", c=[0.03, 1.0], e=[-1.0, -0.45])  # mountains
    add("venus_volcanic_highlands", c=far, e=[-0.45, -0.2])
    add("venus_jungle", c=near, e=[-1.0, -0.45], h=[-0.15, 1.0])
    add("venus_cycad_plains", c=near, e=[-1.0, -0.45], h=[-1.0, -0.15])
    for c, e in (([-0.11, 0.3], [-0.45, 0.45]), (far, [-0.2, 0.45])):
        add("venus_cycad_plains", c=c, e=e, h=[-1.0, -0.15])
        add("venus_jungle", c=c, e=e, h=[-0.15, 0.0])
        add("venus_jungle", c=c, e=e, h=[0.0, 1.0], t=[-0.25, 1.0])
        add("venus_glowcap_hollows", c=c, e=e, h=[0.0, 1.0], t=[-1.0, -0.25])
    return entries


# ---------------------------------------------------------------------------------------------------------------------
# Surface rules
# ---------------------------------------------------------------------------------------------------------------------

def block_rule(state):
    return {"type": "minecraft:block", "result_state": state}


def cond(if_true, then_run):
    return {"type": "minecraft:condition", "if_true": if_true, "then_run": then_run}


def seq(*rules):
    return {"type": "minecraft:sequence", "sequence": list(rules)}


def stone_depth(add_surface_depth=False, offset=0, surface_type="floor", secondary=0):
    return {"type": "minecraft:stone_depth", "add_surface_depth": add_surface_depth, "offset": offset,
            "secondary_depth_range": secondary, "surface_type": surface_type}


def is_biome(*names):
    return {"type": "minecraft:biome", "biome_is": [P(n) for n in names]}


def water_above(offset=-1, mult=0, add=False):
    return {"type": "minecraft:water", "add_stone_depth": add, "offset": offset, "surface_depth_multiplier": mult}


def noise(lo, hi, name="minecraft:surface"):
    return {"type": "minecraft:noise_threshold", "noise": name, "min_threshold": lo, "max_threshold": hi}


def y_above(y, mult=0, add=False):
    return {"type": "minecraft:y_above", "anchor": {"absolute": y}, "surface_depth_multiplier": mult,
            "add_stone_depth": add}


def surface_rule():
    moss, soil, mud = B("venus_moss"), B("venus_soil"), B("venus_mud")
    black, stone = B("venus_black_rock", axis="y"), B("venus_stone")
    tar = B("venus_tar")
    steep = {"type": "minecraft:steep"}
    big = 1.7976931348623157e+308
    floor = seq(
        # volcanic highlands: black rock with mossy pockets in sheltered hollows
        cond(is_biome("venus_volcanic_highlands"), seq(
            cond(steep, block_rule(black)),
            cond(noise(-0.06, 0.1), block_rule(stone)),
            cond(noise(0.3, 0.55), cond(water_above(), block_rule(moss))),
            cond(noise(-0.5, -0.38), block_rule(soil)),
            block_rule(black))),
        # the swamp: puddles of mud and dark tar between moss hummocks
        cond(is_biome("venus_fern_swamp"), seq(
            cond(y_above(62), cond({"type": "minecraft:not", "invert": y_above(63)},
                                   cond(noise(0.0, big, "minecraft:surface_swamp"),
                                        block_rule(B("minecraft:water", level=0))))),
            cond(noise(0.42, 0.5, "minecraft:surface_swamp"), block_rule(tar)),
            cond(noise(-0.12, 0.08), block_rule(mud)),
            cond(water_above(), block_rule(moss)),
            block_rule(mud))),
        cond(is_biome("venus_steaming_sea"), seq(
            cond(y_above(58), block_rule(B("venus_sand"))),
            block_rule(mud))),
        cond(steep, block_rule(stone)),
        cond(is_biome("venus_cycad_plains"), cond(noise(0.55, big), block_rule(soil))),
        cond(water_above(), block_rule(moss)),
        block_rule(mud))
    under = seq(
        cond(is_biome("venus_volcanic_highlands"), block_rule(black)),
        cond(is_biome("venus_fern_swamp", "venus_steaming_sea"), block_rule(mud)),
        cond(steep, block_rule(stone)),
        block_rule(soil))
    return seq(
        cond({"type": "minecraft:vertical_gradient", "random_name": "minecraft:bedrock_floor",
              "true_at_and_below": {"above_bottom": 0}, "false_at_and_above": {"above_bottom": 5}},
             block_rule(B("minecraft:bedrock"))),
        cond({"type": "minecraft:above_preliminary_surface"}, seq(
            cond(stone_depth(), floor),
            cond(stone_depth(add_surface_depth=True), under))),
        cond({"type": "minecraft:vertical_gradient", "random_name": f"{MOD}:black_rock",
              "true_at_and_below": {"absolute": 0}, "false_at_and_above": {"absolute": 8}}, block_rule(black)))


# ---------------------------------------------------------------------------------------------------------------------
# Dimension
# ---------------------------------------------------------------------------------------------------------------------

VANILLA_OVERWORLD_ROUTER = (
    '{"barrier":{"type":"minecraft:noise","noise":"minecraft:aquifer_barrier","xz_scale":1.0,"y_scale":0.5},"contin'
    'ents":"minecraft:overworld/continents","depth":"minecraft:overworld/depth","erosion":"minecraft:overworld/eros'
    'ion","final_density":{"type":"minecraft:min","argument1":{"type":"minecraft:squeeze","argument":{"type":"minec'
    'raft:mul","argument1":0.64,"argument2":{"type":"minecraft:interpolated","argument":{"type":"minecraft:blend_de'
    'nsity","argument":{"type":"minecraft:add","argument1":0.1171875,"argument2":{"type":"minecraft:mul","argument1'
    '":{"type":"minecraft:y_clamped_gradient","from_value":0.0,"from_y":-64,"to_value":1.0,"to_y":-40},"argument2":'
    '{"type":"minecraft:add","argument1":-0.1171875,"argument2":{"type":"minecraft:add","argument1":-0.078125,"argu'
    'ment2":{"type":"minecraft:mul","argument1":{"type":"minecraft:y_clamped_gradient","from_value":1.0,"from_y":24'
    '0,"to_value":0.0,"to_y":256},"argument2":{"type":"minecraft:add","argument1":0.078125,"argument2":{"type":"min'
    'ecraft:range_choice","input":"minecraft:overworld/sloped_cheese","max_exclusive":1.5625,"min_inclusive":-10000'
    '00.0,"when_in_range":{"type":"minecraft:min","argument1":"minecraft:overworld/sloped_cheese","argument2":{"typ'
    'e":"minecraft:mul","argument1":5.0,"argument2":"minecraft:overworld/caves/entrances"}},"when_out_of_range":{"t'
    'ype":"minecraft:max","argument1":{"type":"minecraft:min","argument1":{"type":"minecraft:min","argument1":{"typ'
    'e":"minecraft:add","argument1":{"type":"minecraft:mul","argument1":4.0,"argument2":{"type":"minecraft:square",'
    '"argument":{"type":"minecraft:noise","noise":"minecraft:cave_layer","xz_scale":1.0,"y_scale":8.0}}},"argument2'
    '":{"type":"minecraft:add","argument1":{"type":"minecraft:clamp","input":{"type":"minecraft:add","argument1":0.'
    '27,"argument2":{"type":"minecraft:noise","noise":"minecraft:cave_cheese","xz_scale":1.0,"y_scale":0.6666666666'
    '666666}},"max":1.0,"min":-1.0},"argument2":{"type":"minecraft:clamp","input":{"type":"minecraft:add","argument'
    '1":1.5,"argument2":{"type":"minecraft:mul","argument1":-0.64,"argument2":"minecraft:overworld/sloped_cheese"}}'
    ',"max":0.5,"min":0.0}}},"argument2":"minecraft:overworld/caves/entrances"},"argument2":{"type":"minecraft:add"'
    ',"argument1":"minecraft:overworld/caves/spaghetti_2d","argument2":"minecraft:overworld/caves/spaghetti_roughne'
    'ss_function"}},"argument2":{"type":"minecraft:range_choice","input":"minecraft:overworld/caves/pillars","max_e'
    'xclusive":0.03,"min_inclusive":-1000000.0,"when_in_range":-1000000.0,"when_out_of_range":"minecraft:overworld/'
    'caves/pillars"}}}}}}}}}}}}},"argument2":"minecraft:overworld/caves/noodle"},"fluid_level_floodedness":{"type":'
    '"minecraft:noise","noise":"minecraft:aquifer_fluid_level_floodedness","xz_scale":1.0,"y_scale":0.67},"fluid_le'
    'vel_spread":{"type":"minecraft:noise","noise":"minecraft:aquifer_fluid_level_spread","xz_scale":1.0,"y_scale":'
    '0.7142857142857143},"lava":{"type":"minecraft:noise","noise":"minecraft:aquifer_lava","xz_scale":1.0,"y_scale"'
    ':1.0},"preliminary_surface_level":{"type":"minecraft:find_top_surface","cell_height":8,"density":{"type":"mine'
    'craft:add","argument1":-0.390625,"argument2":{"type":"minecraft:add","argument1":0.1171875,"argument2":{"type"'
    ':"minecraft:mul","argument1":{"type":"minecraft:y_clamped_gradient","from_value":0.0,"from_y":-64,"to_value":1'
    '.0,"to_y":-40},"argument2":{"type":"minecraft:add","argument1":-0.1171875,"argument2":{"type":"minecraft:add",'
    '"argument1":-0.078125,"argument2":{"type":"minecraft:mul","argument1":{"type":"minecraft:y_clamped_gradient","'
    'from_value":1.0,"from_y":240,"to_value":0.0,"to_y":256},"argument2":{"type":"minecraft:add","argument1":0.0781'
    '25,"argument2":{"type":"minecraft:clamp","input":{"type":"minecraft:add","argument1":-0.703125,"argument2":{"t'
    'ype":"minecraft:mul","argument1":4.0,"argument2":{"type":"minecraft:quarter_negative","argument":{"type":"mine'
    'craft:mul","argument1":{"type":"minecraft:add","argument1":{"type":"minecraft:y_clamped_gradient","from_value"'
    ':1.5,"from_y":-64,"to_value":-1.5,"to_y":320},"argument2":{"type":"minecraft:cache_2d","argument":"minecraft:o'
    'verworld/offset"}},"argument2":{"type":"minecraft:cache_2d","argument":"minecraft:overworld/factor"}}}}},"max"'
    ':64.0,"min":-64.0}}}}}}}},"lower_bound":-64,"upper_bound":{"type":"minecraft:clamp","input":{"type":"minecraft'
    ':add","argument1":128.0,"argument2":{"type":"minecraft:mul","argument1":-128.0,"argument2":{"type":"minecraft:'
    'add","argument1":{"type":"minecraft:mul","argument1":0.2734375,"argument2":{"type":"minecraft:invert","argumen'
    't":{"type":"minecraft:cache_2d","argument":"minecraft:overworld/factor"}}},"argument2":{"type":"minecraft:mul"'
    ',"argument1":-1.0,"argument2":{"type":"minecraft:cache_2d","argument":"minecraft:overworld/offset"}}}}},"max":'
    '320.0,"min":-40.0}},"ridges":"minecraft:overworld/ridges","temperature":{"type":"minecraft:shifted_noise","noi'
    'se":"minecraft:temperature","shift_x":"minecraft:shift_x","shift_y":0.0,"shift_z":"minecraft:shift_z","xz_scal'
    'e":0.25,"y_scale":0.0},"vegetation":{"type":"minecraft:shifted_noise","noise":"minecraft:vegetation","shift_x"'
    ':"minecraft:shift_x","shift_y":0.0,"shift_z":"minecraft:shift_z","xz_scale":0.25,"y_scale":0.0},"vein_gap":{"t'
    'ype":"minecraft:noise","noise":"minecraft:ore_gap","xz_scale":1.0,"y_scale":1.0},"vein_ridged":{"type":"minecr'
    'aft:add","argument1":-0.07999999821186066,"argument2":{"type":"minecraft:max","argument1":{"type":"minecraft:a'
    'bs","argument":{"type":"minecraft:interpolated","argument":{"type":"minecraft:range_choice","input":"minecraft'
    ':y","max_exclusive":51.0,"min_inclusive":-60.0,"when_in_range":{"type":"minecraft:noise","noise":"minecraft:or'
    'e_vein_a","xz_scale":4.0,"y_scale":4.0},"when_out_of_range":0.0}}},"argument2":{"type":"minecraft:abs","argume'
    'nt":{"type":"minecraft:interpolated","argument":{"type":"minecraft:range_choice","input":"minecraft:y","max_ex'
    'clusive":51.0,"min_inclusive":-60.0,"when_in_range":{"type":"minecraft:noise","noise":"minecraft:ore_vein_b","'
    'xz_scale":4.0,"y_scale":4.0},"when_out_of_range":0.0}}}}},"vein_toggle":{"type":"minecraft:interpolated","argu'
    'ment":{"type":"minecraft:range_choice","input":"minecraft:y","max_exclusive":51.0,"min_inclusive":-60.0,"when_'
    'in_range":{"type":"minecraft:noise","noise":"minecraft:ore_veininess","xz_scale":1.5,"y_scale":1.5},"when_out_'
    'of_range":0.0}}}')


def noise_router():
    """The vanilla overworld noise router (terrain shape, caves, aquifers); it references the vanilla
    minecraft:overworld/* density functions, so Venus gets Earth-like continents, mountains and caves."""
    return json.loads(VANILLA_OVERWORLD_ROUTER)


def dimension():
    write_json(os.path.join(DATA, "dimension_type", "venus.json"), {
        "ambient_light": 0.0,
        "attributes": {
            "minecraft:audio/ambient_sounds": {"mood": {"block_search_extent": 8, "offset": 2.0,
                                                        "sound": "minecraft:ambient.cave", "tick_delay": 6000}},
            "minecraft:audio/background_music": music(),
            "minecraft:gameplay/bed_rule": {"can_set_spawn": "always", "can_sleep": "when_dark",
                                            "error_message": {"translate": "block.minecraft.bed.no_sleep"}},
            "minecraft:gameplay/respawn_anchor_works": False,
            "minecraft:gameplay/snow_golem_melts": True,
            "minecraft:visual/cloud_color": "#ccf0c080",
            "minecraft:visual/cloud_height": 170.0,
            "minecraft:visual/fog_color": "#d9a64e",
            "minecraft:visual/sky_color": "#d9a64e",
            "minecraft:visual/fog_start_distance": 12.0,
            "minecraft:visual/fog_end_distance": 168.0,
            "minecraft:visual/water_fog_color": "#1e4a3c",
            "minecraft:visual/sky_light_color": "#ffd8a0",
            "minecraft:visual/sky_light_factor": 1.0,
            "minecraft:visual/star_brightness": 0.0,
            "minecraft:visual/sunrise_sunset_color": "#00000000"},
        "coordinate_scale": 1.0,
        "has_ceiling": False,
        "has_fixed_time": False,
        "has_skylight": True,
        "height": 384,
        "infiniburn": "#minecraft:infiniburn_overworld",
        "logical_height": 384,
        "min_y": -64,
        "monster_spawn_block_light_limit": 0,
        "monster_spawn_light_level": {"type": "minecraft:uniform", "max_inclusive": 7, "min_inclusive": 0},
        "skybox": "none",
        "timelines": [P("venus_day")]})

    # The Venusian day: no sun through the cloud deck, just a slow fade from amber noon to violet dusk.
    def track(day, night, modifier="multiply"):
        return {"keyframes": [{"ticks": 133, "value": day}, {"ticks": 11867, "value": day},
                              {"ticks": 13670, "value": night}, {"ticks": 22330, "value": night}],
                "modifier": modifier}
    write_json(os.path.join(DATA, "timeline", "venus_day.json"), {
        "period_ticks": 24000,
        "tracks": {
            "minecraft:gameplay/sky_light_level": track(1.0, 0.4),
            "minecraft:visual/sky_light_factor": track(1.0, 0.45),
            "minecraft:visual/sky_light_color": track("#ffffff", "#b49cff"),
            "minecraft:visual/fog_color": track("#ffffff", "#4a3a5e"),
            "minecraft:visual/sky_color": track("#ffffff", "#4a3a5e"),
            "minecraft:visual/cloud_color": track(-1, -11849150)}})

    write_json(os.path.join(DATA, "worldgen", "noise_settings", "venus.json"), {
        "aquifers_enabled": True,
        "default_block": B("venus_stone"),
        "default_fluid": {"Name": "minecraft:water", "Properties": {"level": "0"}},
        "disable_mob_generation": False,
        "legacy_random_source": False,
        "noise": {"height": 384, "min_y": -64, "size_horizontal": 1, "size_vertical": 2},
        "noise_router": noise_router(),
        "ore_veins_enabled": False,
        "sea_level": 63,
        "spawn_target": [
            {"continentalness": [-0.11, 1.0], "depth": 0.0, "erosion": [-1.0, 1.0], "humidity": [-1.0, 1.0],
             "offset": 0.0, "temperature": [-1.0, 1.0], "weirdness": [-1.0, -0.16]},
            {"continentalness": [-0.11, 1.0], "depth": 0.0, "erosion": [-1.0, 1.0], "humidity": [-1.0, 1.0],
             "offset": 0.0, "temperature": [-1.0, 1.0], "weirdness": [0.16, 1.0]}],
        "surface_rule": surface_rule()})

    write_json(os.path.join(DATA, "dimension", "venus.json"), {
        "type": P("venus"),
        "generator": {"type": "minecraft:noise", "settings": P("venus"),
                      "biome_source": {"type": "minecraft:multi_noise", "biomes": climate()}}})


# =====================================================================================================================
# Entry point
# =====================================================================================================================

def textures():
    for name, fn in TEXTURES.items():
        save(fn(), "block", name)
    for name, fn in ITEM_TEXTURES.items():
        save(fn(), "item", name)


def generate():
    textures()
    ore_textures()
    block_models()
    ore_models()
    loot_tables()
    ore_loot()
    tags()
    ore_tags()
    recipes()
    ore_recipes()
    features()
    ore_features()
    carvers()
    dinos = biomes()
    dimension()
    print(f"venus: generated (dinosaur spawns {'ON' if dinos else 'off'})")


NAMES = {
    "venus_stone": ("Venusian Stone", "Венерианский камень"),
    "venus_cobblestone": ("Venusian Cobblestone", "Венерианский булыжник"),
    "venus_stone_bricks": ("Venusian Stone Bricks", "Венерианские каменные кирпичи"),
    "venus_black_rock": ("Black Volcanic Rock", "Чёрная вулканическая порода"),
    "venus_fumarole": ("Fumarole", "Фумарола"),
    "venus_mud": ("Venusian Mud", "Венерианская грязь"),
    "venus_soil": ("Jungle Loam", "Лесной суглинок"),
    "venus_moss": ("Venusian Moss", "Венерианский мох"),
    "venus_tar": ("Tar", "Смола"),
    "venus_log": ("Giant Tree Log", "Бревно исполинского дерева"),
    "venus_wood": ("Giant Tree Wood", "Древесина исполинского дерева"),
    "venus_planks": ("Giant Tree Planks", "Доски исполинского дерева"),
    "venus_stairs": ("Giant Tree Stairs", "Ступени из исполинского дерева"),
    "venus_slab": ("Giant Tree Slab", "Плита из исполинского дерева"),
    "venus_leaves": ("Giant Tree Leaves", "Листва исполинского дерева"),
    "venus_amber_leaves": ("Amber Leaves", "Янтарная листва"),
    "venus_sedge": ("Venusian Sedge", "Венерианская осока"),
    "venus_horsetail": ("Horsetail", "Хвощ"),
    "venus_cycad": ("Cycad", "Саговник"),
    "venus_fire_lily": ("Fire Lily", "Огненная лилия"),
    "venus_tree_fern": ("Tree Fern", "Древовидный папоротник"),
    "venus_giant_fern": ("Giant Fern", "Гигантский папоротник"),
    "venus_hanging_vines": ("Hanging Lianas", "Свисающие лианы"),
    "venus_glowcap": ("Glowcap", "Светогриб"),
    "venus_glowstalk": ("Glowstalk", "Светостебель"),
    "venus_glowcap_block": ("Glowcap Cap", "Шляпка светогриба"),
    "venus_glowcap_stem": ("Glowcap Stem", "Ножка светогриба"),
}
NAMES.update({
    "venus_sand": ("Volcanic Sand", "Вулканический песок"),
    "venus_coal_ore": ("Venusian Coal Ore", "Венерианская угольная руда"),
    "venus_iron_ore": ("Venusian Iron Ore", "Венерианская железная руда"),
    "venus_copper_ore": ("Venusian Copper Ore", "Венерианская медная руда"),
    "venus_gold_ore": ("Venusian Gold Ore", "Венерианская золотая руда"),
    "venus_redstone_ore": ("Venusian Redstone Ore", "Венерианская редстоуновая руда"),
    "venus_diamond_ore": ("Venusian Diamond Ore", "Венерианская алмазная руда"),
    "venus_bauxite_ore": ("Venusian Bauxite Ore", "Венерианская бокситовая руда"),
    "venus_titanium_ore": ("Venusian Titanium Ore", "Венерианская титановая руда"),
    "venus_oil_shale": ("Venusian Oil Shale", "Венерианский горючий сланец"),
    "venus_cryolite_ore": ("Cryolite Ore", "Криолитовая руда"),
})
BIOME_NAMES = {
    "venus_jungle": ("Venusian Jungle", "Венерианские джунгли"),
    "venus_fern_swamp": ("Fern Swamp", "Папоротниковое болото"),
    "venus_cycad_plains": ("Cycad Plains", "Саговниковые равнины"),
    "venus_volcanic_highlands": ("Volcanic Highlands", "Вулканическое нагорье"),
    "venus_glowcap_hollows": ("Glowcap Hollows", "Светогрибные лощины"),
    "venus_steaming_sea": ("Steaming Sea", "Парящее море"),
}

EN = {f"block.{MOD}.{k}": v[0] for k, v in NAMES.items()}
RU = {f"block.{MOD}.{k}": v[1] for k, v in NAMES.items()}
EN[f"item.{MOD}.cryolite_crystal"] = "Cryolite Crystal"
RU[f"item.{MOD}.cryolite_crystal"] = "Кристалл криолита"
EN.update({f"biome.{MOD}.{k}": v[0] for k, v in BIOME_NAMES.items()})
RU.update({f"biome.{MOD}.{k}": v[1] for k, v in BIOME_NAMES.items()})
