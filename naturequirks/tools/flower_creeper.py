"""Flower Creeper: the vanilla creeper body with a mossy, leafy skin and real little flowers growing on its head and
back. It bursts into flowers and pollen instead of blowing holes in the ground.

generate() writes: the entity texture, the generated model geometry (with the flower anchors), the spawn egg, the
hay-fever effect icon, the loot table, the flowery-biome tag and spawn modifier.
"""
import math
import os

import quirk_models as Q
from quirk_models import B, P

NAME = "flower_creeper"
ID = f"{Q.MOD}:{NAME}"

# ----------------------------------------------------------------------------
# Geometry: exactly the vanilla creeper (CreeperModel.createBodyLayer)
# ----------------------------------------------------------------------------


def spec():
    parts = [
        P("head", None, (0, 6, 0), (0, 0, 0), [B(-4, -8, -4, 8, 8, 8, "head")]),
        P("body", None, (0, 6, 0), (0, 0, 0), [B(-4, 0, -2, 8, 12, 4, "body")]),
    ]
    for name, x, z in (("right_hind_leg", -2, 4), ("left_hind_leg", 2, 4), ("right_front_leg", -2, -4), ("left_front_leg", 2, -4)):
        parts.append(P(name, None, (x, 18, z), (0, 0, 0), [B(-2, 0, -2, 4, 6, 4, "leg", side=name)]))
    return {"name": NAME, "tex_w": 64, "parts": parts}


# Flowers growing out of it: (part, x, y, z [px, part space], x tilt, y turn [rad], scale [blocks]). Rendered in game
# as real flower block models (FlowerCreeperFlowerLayer), so they are the flowers you know.
FLOWER_SLOTS = [
    ("head", -2.0, -8.0, -1.5, 0.12, 0.35, 0.5),
    ("head", 2.2, -8.0, 1.2, -0.15, 1.1, 0.46),
    ("head", -0.6, -8.0, 2.6, -0.3, 2.3, 0.4),
    ("body", 1.6, 3.0, 2.0, -0.95, 0.4, 0.42),
    ("body", -2.0, 7.5, 2.0, -1.1, -0.5, 0.38),
]

# ----------------------------------------------------------------------------
# Texture
# ----------------------------------------------------------------------------

LEAF = [(54, 94, 38), (72, 120, 46), (92, 146, 56), (114, 168, 66), (142, 192, 86)]
SPECK = (176, 214, 112)
FACE_DARK = (18, 30, 16)
FACE_MID = (36, 54, 30)
SOIL = (82, 62, 40)

# the creeper face, 8x8, '#' = dark, '+' = the lighter inner shade vanilla uses for depth
FACE = [
    "........",
    ".##..##.",
    ".#+..+#.",
    "...##...",
    "..#++#..",
    "..#++#..",
    "..#..#..",
    "........",
]
# tiny painted blossoms on the skin: (part, face, i, j, petal colour)
BLOSSOMS = [
    ("body", "east", 1, 3, (236, 236, 244)), ("body", "west", 2, 8, (240, 160, 196)),
    ("body", "south", 5, 9, (122, 150, 238)),
]


def blossom(t):
    for part, face, ci, cj, petal in BLOSSOMS:
        if t.part == part and t.face == face:
            di, dj = t.i - ci, t.j - cj
            if di == 0 and dj == 0:
                return (250, 206, 60)
            if abs(di) + abs(dj) == 1:
                return petal
    return None


def paint(spec, t):
    seed = 7
    # leafy clumps: smooth noise for the patches, per-texel hash for the crunchy vanilla grain
    n = Q.value_noise(t.mx * 1.0, t.my * 1.0, t.mz * 1.0, 2.6, seed)
    g = Q.hash3(t.u, t.v, seed)
    k = n * 0.62 + g * 0.38
    if t.face == "top":
        k += 0.12
    elif t.face == "bottom":
        k -= 0.25
    idx = max(0, min(4, int(k * 5.2 - 0.3)))
    c = LEAF[idx]
    if g > 0.955:
        c = SPECK
    if t.mat == "head" and t.face == "north":
        ch = FACE[t.j][t.i]
        if ch == "#":
            return FACE_DARK + (255,)
        if ch == "+":
            return FACE_MID + (255,)
    if t.mat == "leg":
        # muddy toes
        if t.face != "top" and t.j >= t.rows - 1:
            c = Q.mix(c, SOIL, 0.55)
        elif t.face != "top" and t.j == t.rows - 2 and g > 0.5:
            c = Q.mix(c, SOIL, 0.3)
    b = blossom(t)
    if b:
        c = b
    return c + (255,)


# ----------------------------------------------------------------------------
# Preview flowers (in game the real block models are drawn; here a small painted stand-in of each)
# ----------------------------------------------------------------------------

FLOWER_SPRITES = {
    # 16x16 cross-model sprites, bottom row = 15; only the drawn texels matter
    "poppy": {"stem": (50, 110, 30), "petal": (200, 30, 30), "dark": (130, 14, 14), "eye": (30, 20, 10), "shape": "cup"},
    "dandelion": {"stem": (70, 130, 30), "petal": (250, 220, 40), "dark": (210, 160, 20), "eye": (250, 220, 40), "shape": "puff"},
    "cornflower": {"stem": (60, 120, 40), "petal": (70, 100, 230), "dark": (40, 60, 170), "eye": (30, 40, 120), "shape": "star"},
    "allium": {"stem": (70, 130, 50), "petal": (190, 110, 230), "dark": (140, 70, 190), "eye": (220, 160, 240), "shape": "ball"},
}


def flower_sprite(kind):
    from PIL import Image
    s = FLOWER_SPRITES[kind]
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for y in range(9, 16):
        img.putpixel((8, y), Q.rgba(s["stem"]))
    img.putpixel((7, 12), Q.rgba(s["stem"]))
    img.putpixel((9, 11), Q.rgba(s["stem"]))
    cy = 6
    pts = {"cup": [(-2, -1), (-1, -2), (0, -2), (1, -2), (2, -1), (-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0), (-1, 1), (0, 1), (1, 1),
                   (-1, -1), (0, -1), (1, -1)],
           "puff": [(-1, -1), (0, -1), (1, -1), (-1, 0), (0, 0), (1, 0), (-1, 1), (0, 1), (1, 1), (0, -2), (0, 2), (-2, 0), (2, 0)],
           "star": [(0, -2), (-2, 0), (2, 0), (0, 0), (-1, -1), (1, -1), (-1, 1), (1, 1), (0, 1), (0, -1), (-1, 0), (1, 0), (-2, -2),
                    (2, -2)],
           "ball": [(x, y) for x in range(-2, 3) for y in range(-2, 3) if x * x + y * y <= 5]}[s["shape"]]
    for dx, dy in pts:
        c = s["petal"] if (dx + dy) % 2 == 0 else s["dark"]
        img.putpixel((8 + dx, cy + dy), Q.rgba(c))
    img.putpixel((8, cy), Q.rgba(s["eye"]))
    return img


def flower_quads(spec, yaw, pitch, kinds, offset=(0, 0, 0)):
    """Two crossed sprite planes per flower slot, transformed exactly like the Java flower layer does."""
    mats = Q.part_matrices(spec)
    out = []
    for (part, x, y, z, rx, ry, sc), kind in zip(FLOWER_SLOTS, kinds):
        img = flower_sprite(kind)
        m = Q.mat_mul(mats[part], Q.translate(x, y, z))
        m = Q.mat_mul(m, Q.rot_y(ry))
        m = Q.mat_mul(m, Q.rot_x(rx))
        s16 = sc * 16
        m = Q.mat_mul(m, [[-s16, 0, 0, 0], [0, -s16, 0, 0], [0, 0, s16, 0], [0, 0, 0, 1]])
        m = Q.mat_mul(m, Q.translate(-0.5, 0, -0.5))
        # vanilla cross model: two planes through the block's diagonals, sprite bottom at y = 0
        for (ax, az, bx, bz) in ((0.15, 0.15, 0.85, 0.85), (0.15, 0.85, 0.85, 0.15)):
            for py in range(16):
                for pxl in range(16):
                    c = img.getpixel((pxl, py))
                    if c[3] < 128:
                        continue
                    corners = []
                    for (fi, fj) in ((0, 0), (1, 0), (1, 1), (0, 1)):
                        f = (pxl + fi) / 16
                        h = 1 - (py + fj) / 16
                        q = Q.apply(m, (ax + (bx - ax) * f, h, az + (bz - az) * f))
                        q = (q[0] + offset[0], q[1] + offset[1], q[2] + offset[2])
                        corners.append(Q.cam(q, yaw, pitch))
                    depth = sum(p[2] for p in corners) / 4
                    out.append((depth, [(p[0], p[1]) for p in corners], c[:3]))
    return out


# ----------------------------------------------------------------------------
# Java constants for the flower layer
# ----------------------------------------------------------------------------

def write_java():
    sp = spec()
    Q.pack(sp)
    Q.write_geometry("com.replecant.naturequirks.flowercreeper.client", "FlowerCreeperGeometry",
                     [(sp, "create")], "Flower creeper model: the vanilla creeper body.")
    rows = ",\n            ".join(
        "{" + ", ".join(Q.jf(v) for v in (0 if part == "head" else 1, x, y, z, rx, ry, sc)) + "}"
        for part, x, y, z, rx, ry, sc in FLOWER_SLOTS)
    path = os.path.join(Q.JAVA, "flowercreeper", "client", "FlowerSlots.java")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"""package com.replecant.naturequirks.flowercreeper.client;

/** Where the flowers grow on a flower creeper. GENERATED by tools/flower_creeper.py (FLOWER_SLOTS). */
final class FlowerSlots {{
    /** {{part (0 = head, 1 = body), x, y, z (pixels, part space), x tilt, y turn (radians), scale (blocks)}} */
    static final float[][] SLOTS = {{
            {rows}}};

    private FlowerSlots() {{}}
}}
""")


# ----------------------------------------------------------------------------
# Icons, data
# ----------------------------------------------------------------------------

def hay_fever_icon():
    """18x18 mob effect icon: a yellow pollen puff with a sneeze burst."""
    from PIL import Image
    img = Image.new("RGBA", (18, 18), (0, 0, 0, 0))
    for y in range(18):
        for x in range(18):
            d = math.hypot(x - 7.5, y - 9.5)
            if d < 5.6:
                g = Q.hash3(x, y, 11)
                c = (250, 216, 72) if g > 0.35 else (226, 178, 40)
                if d > 4.6:
                    c = (170, 126, 30)
                if g > 0.9:
                    c = (255, 246, 170)
                img.putpixel((x, y), Q.rgba(c))
    for (x, y) in ((14, 4), (15, 3), (16, 6), (13, 2), (16, 9), (14, 12)):
        img.putpixel((x, y), Q.rgba((255, 240, 150)))
    return img


EGG_FACE = {(5, 5), (6, 5), (9, 5), (10, 5), (5, 6), (6, 6), (9, 6), (10, 6), (7, 7), (8, 7), (6, 8), (7, 8), (8, 8), (9, 8),
            (6, 9), (7, 9), (8, 9), (9, 9), (6, 10), (9, 10)}


def egg():
    """The creeper's mossy egg with its face, and a poppy growing out of the top."""
    def paint(x, y):
        if (x, y) in EGG_FACE:
            return FACE_DARK
        g = Q.hash3(x, y, 17)
        return LEAF[min(4, int(g * 4.2) + (1 if y < 6 else 0))] if g < 0.94 else SPECK
    extras = {(7, 0): (196, 30, 30, 255), (8, 0): (222, 52, 40, 255), (6, 1): (200, 30, 30, 255), (9, 1): (180, 24, 24, 255),
              (7, 1): (120, 14, 14, 255), (8, 1): (232, 72, 52, 255), (12, 3): (90, 120, 230, 255), (12, 2): (70, 100, 210, 255),
              (3, 4): (250, 220, 60, 255)}
    return Q.spawn_egg(paint, extras)


FLOWERS = ["minecraft:poppy", "minecraft:dandelion", "minecraft:cornflower", "minecraft:allium", "minecraft:oxeye_daisy",
           "minecraft:azure_bluet", "minecraft:red_tulip", "minecraft:orange_tulip", "minecraft:pink_tulip",
           "minecraft:white_tulip", "minecraft:lily_of_the_valley"]


def generate():
    import gen_resources
    if "guardian_bee" not in gen_resources.FEATURES:
        import guardian_bee
        guardian_bee.generate()
        EN.update(guardian_bee.EN)
        RU.update(guardian_bee.RU)
    sp = spec()
    tex = Q.build_texture(sp, paint)
    Q.save_png(tex, "entity", NAME, NAME + ".png")
    write_java()
    Q.save_png(egg(), "item", NAME + "_spawn_egg.png")
    Q.item_model(NAME + "_spawn_egg")
    icon = hay_fever_icon()
    Q.save_png(icon, "mob_effect", "hay_fever.png")
    Q.loot_table(f"entities/{NAME}", [
        Q.pool([Q.entry("minecraft:gunpowder", 0, 1, functions=[Q.looting(0, 1)])]),
        Q.pool([Q.entry(f, 1, 2, weight=3 if f.endswith(("poppy", "dandelion", "cornflower", "allium")) else 1) for f in FLOWERS],
               rolls={"type": "minecraft:uniform", "min": 1, "max": 2}),
    ])
    Q.tag("worldgen/biome", "has_flower_creeper", ["minecraft:flower_forest", "minecraft:meadow",
                                                     "minecraft:sunflower_plains", "minecraft:cherry_grove"])
    Q.spawn_modifier("flower_creeper_spawns", f"{Q.MOD}:has_flower_creeper", ID, 40, 1, 2)


EN = {
    f"entity.{Q.MOD}.{NAME}": "Flower Creeper",
    f"item.{Q.MOD}.{NAME}_spawn_egg": "Flower Creeper Spawn Egg",
    f"effect.{Q.MOD}.hay_fever": "Hay Fever",
}
RU = {
    f"entity.{Q.MOD}.{NAME}": "Цветочный крипер",
    f"item.{Q.MOD}.{NAME}_spawn_egg": "Яйцо призыва цветочного крипера",
    f"effect.{Q.MOD}.hay_fever": "Сенная лихорадка",
}


if __name__ == "__main__":
    generate()
