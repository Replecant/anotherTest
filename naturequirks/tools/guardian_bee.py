"""Guardian Bee: the soldier of the giant hives. The vanilla bee's body and proportions (drawn 1.4x bigger), darker
amber and brown, with an armoured head cap and thorax plate, mandibles and a big stinger; red eyes when angry.

generate() writes both textures (calm / angry), the model geometry, the spawn egg and the loot table.
Called from flower_creeper.generate() unless gen_resources lists "guardian_bee" in FEATURES itself.
"""
import quirk_models as Q
from quirk_models import B, P

NAME = "guardian_bee"
ID = f"{Q.MOD}:{NAME}"


def spec():
    parts = [
        P("bone", None, (0, 19, 0), (0, 0, 0), []),
        # vanilla bee body: 7 x 7 x 10, the face is its front
        P("body", "bone", (0, 0, 0), (0, 0, 0), [
            B(-3.5, -4, -5, 7, 7, 10, "body"),
            # armour: a chitin cap over the head and a plate over the thorax, ridged down the middle
            B(-4, -4.6, -5.6, 8, 2, 4, "helmet"),
            B(-0.5, -5.6, -5.2, 1, 1, 3, "crest"),
            B(-3, -4.5, -1.0, 6, 1, 3, "plate"),
            # mandibles under the face
            B(-2.5, 1.6, -6.1, 2, 1, 1, "mandible"),
            B(0.5, 1.6, -6.1, 2, 1, 1, "mandible"),
        ]),
        # a big stinger (the vanilla one is a 0 x 1 x 2 sliver)
        P("stinger", "body", (0, 0, 0), (0, 0, 0), [
            B(-1, -1.5, 5, 2, 2, 1, "stinger_base"),
            B(-0.5, -1, 6, 1, 1, 2, "stinger"),
        ]),
        P("left_antenna", "body", (0, -2, -5), (0, 0, 0), [B(1.5, -2, -3, 1, 2, 3, "antenna")]),
        P("right_antenna", "body", (0, -2, -5), (0, 0, 0), [B(-2.5, -2, -3, 1, 2, 3, "antenna")]),
        P("right_wing", "bone", (-1.5, -4, -3), (0, -0.2618, 0), [B(-9, 0, 0, 9, 0, 6, "wing", inflate=0.001)]),
        P("left_wing", "bone", (1.5, -4, -3), (0, 0.2618, 0), [B(0, 0, 0, 9, 0, 6, "wing", inflate=0.001)]),
        P("front_legs", "bone", (1.5, 3, -2), (0, 0, 0), [B(-5, 0, 0, 7, 2, 0, "legs")]),
        P("middle_legs", "bone", (1.5, 3, 0), (0, 0, 0), [B(-5, 0, 0, 7, 2, 0, "legs")]),
        P("back_legs", "bone", (1.5, 3, 2), (0, 0, 0), [B(-5, 0, 0, 7, 2, 0, "legs")]),
    ]
    return {"name": NAME, "tex_w": 64, "parts": parts}


# flying pose of the vanilla model (legs tucked at 45 degrees)
FLYING = {"right_wing": (0, 0.2618, 0.3), "left_wing": (0, -0.2618, -0.3), "front_legs": (0.785, 0, 0), "middle_legs": (0.785, 0, 0), "back_legs": (0.785, 0, 0)}

# darker than a worker bee: deep amber and near-black brown, armour of dark reddish chitin
AMBER = [(166, 96, 28), (194, 122, 38), (218, 148, 50), (236, 172, 66)]
BROWN = [(26, 16, 12), (40, 22, 16), (58, 32, 22), (76, 44, 28)]
CHITIN = [(40, 22, 18), (66, 36, 26), (98, 56, 36), (140, 86, 52)]
EYE = [(26, 22, 30), (44, 38, 46)]
EYE_GLINT = (232, 186, 96)
EYE_ANGRY = [(150, 18, 16), (196, 30, 24)]
EYE_GLINT_ANGRY = (255, 132, 96)
WING = (232, 228, 216)
WING_BASE = (92, 52, 36)


def amber(fy, g):
    """Vanilla bees are lit from above: light at the top of each face, darker toward the belly."""
    k = 3 - int(fy * 3.2 + (0.6 if g > 0.75 else 0))
    return AMBER[max(0, min(3, k))]


def stripe(z):
    """Along the body (z -5 front .. +5 rear): amber front, then thin dark rings, a dark rear end - as vanilla."""
    if z > 4:
        return "rear"
    if z > -1 and int(z + 1) % 2 == 0:
        return "ring"
    return "amber"


def eye_px(i, j, cols, angry):
    """Compound eyes wrapping round the corners of the face, rows 3-5 (as on the vanilla bee)."""
    pal, glint = (EYE_ANGRY, EYE_GLINT_ANGRY) if angry else (EYE, EYE_GLINT)
    if 3 <= j <= 5 and (i <= 1 or i >= cols - 2):
        inner = i == 1 or i == cols - 2
        if j == 3 and inner:
            return glint
        return pal[1] if (i + j) % 2 else pal[0]
    return None


def paint_for(angry):
    def paint(spec, t):
        g = Q.hash3(t.u, t.v, 31)
        if t.mat == "body":
            if t.face == "north":
                e = eye_px(t.i, t.j, t.cols, angry)
                if e:
                    return e + (255,)
                if t.j >= 5 and 2 <= t.i <= 4:
                    return (BROWN[1] if t.j == 6 else BROWN[2]) + (255,)  # the mouth under the mandibles
                return amber(t.fy, g) + (255,)
            if t.face in ("east", "west"):
                # the eyes wrap round onto the sides at the front edge
                front = t.lz < -4
                if front and 3 <= t.j <= 5:
                    pal = EYE_ANGRY if angry else EYE
                    return pal[t.j % 2] + (255,)
                kind = stripe(t.lz)
                if kind == "rear":
                    return BROWN[min(3, 1 + int(g * 2.5)) - (1 if t.fy > 0.6 else 0)] + (255,)
                if kind == "ring":
                    return BROWN[1 if t.fy > 0.5 else 2] + (255,)
                return amber(t.fy, g) + (255,)
            if t.face == "top":
                kind = stripe(t.lz)
                if kind == "rear":
                    return BROWN[2 + (1 if g > 0.6 else 0)] + (255,)
                if kind == "ring":
                    return BROWN[2] + (255,)
                return AMBER[3 if g > 0.3 else 2] + (255,)
            if t.face == "bottom":
                kind = stripe(t.lz)
                return (BROWN[1] if kind != "amber" else AMBER[0]) + (255,)
            if t.face == "south":
                ring = t.i in (0, t.cols - 1) or t.j in (0, t.rows - 1)
                return (BROWN[2] if ring else BROWN[1] if g > 0.4 else BROWN[0]) + (255,)
        if t.mat in ("helmet", "plate", "crest"):
            k = 2 if g > 0.45 else 1
            if t.face == "top":
                k += 1
            elif t.face == "bottom":
                k = 0
            elif t.face in ("east", "west", "north", "south") and t.fy > 0.6:
                k -= 1
            if t.mat == "helmet" and t.face == "north" and t.j == t.rows - 1:
                k = 0  # the rim over the eyes
            if t.mat == "plate" and t.face == "top" and t.j == t.rows - 1:
                k = 0  # the seam between cap and plate
            if t.mat == "crest" and t.face == "top":
                k = 3
            return CHITIN[max(0, min(3, k))] + (255,)
        if t.mat == "mandible":
            return (CHITIN[2] if t.face in ("top", "north") else CHITIN[0]) + (255,)
        if t.mat == "stinger_base":
            return BROWN[2] + (255,)
        if t.mat == "stinger":
            return ((150, 140, 128) if t.lz > 7 else (96, 82, 68)) + (255,)
        if t.mat == "antenna":
            return (BROWN[0] if t.ly < -1.5 else BROWN[2]) + (255,)
        if t.mat == "wing":
            # vanilla bee wings: a pale outline loop, clear inside, with a dark root where it joins the body
            if t.face not in ("top", "bottom"):
                return None
            fx = (t.i + 0.5) / t.cols
            fz = (t.j + 0.5) / t.rows
            # the loop is wider toward the tip (away from the body)
            tip = fx if t.part == "left_wing" else 1 - fx
            if t.face == "bottom":
                tip = 1 - tip
            dx = (tip - 0.58) / 0.42
            dz = (fz - 0.5) / 0.5
            r = dx * dx + dz * dz
            if tip < 0.12 and abs(fz - 0.4) < 0.2:
                return WING_BASE + (255,)
            if 0.62 <= r <= 1.05:
                return WING + (255,)
            if 0.2 < r < 0.32 and g > 0.5:
                return Q.shade(WING, 0.9) + (255,)  # a vein
            return None
        if t.mat == "legs":
            return (BROWN[0] if t.j == 1 else BROWN[2]) + (255,)
        return (255, 0, 255, 255)
    return paint


def egg():
    """Amber egg with dark rings, a chitin cap, smoky wings out to the sides."""
    def paint(x, y):
        if y <= 4:
            return CHITIN[2] if (x + y) % 3 else CHITIN[3]
        if y in (9, 12):
            return BROWN[2]
        if y >= 13:
            return BROWN[1]
        return AMBER[3] if y < 8 else AMBER[2]
    extras = {}
    for (x, y) in ((0, 6), (0, 7), (1, 5), (1, 8), (2, 5), (15, 6), (15, 7), (14, 5), (14, 8), (13, 5)):
        extras[(x, y)] = WING + (255,)
    for (x, y) in ((4, 7), (11, 7)):
        extras[(x, y)] = EYE[0] + (255,)
    for (x, y) in ((5, 7), (10, 7)):
        extras[(x, y)] = EYE_GLINT + (255,)
    return Q.spawn_egg(paint, extras)


def generate():
    sp = spec()
    calm = Q.build_texture(sp, paint_for(False))
    angry = Q.build_texture(sp, paint_for(True))
    Q.save_png(calm, "entity", NAME, NAME + ".png")
    Q.save_png(angry, "entity", NAME, NAME + "_angry.png")
    Q.write_geometry("com.replecant.naturequirks.guardianbee.client", "GuardianBeeGeometry", [(sp, "create")],
                     "Guardian bee model: the vanilla bee's parts (same names and pivots) plus armour and a big stinger.")
    Q.save_png(egg(), "item", NAME + "_spawn_egg.png")
    Q.item_model(NAME + "_spawn_egg")
    Q.loot_table(f"entities/{NAME}", [
        Q.pool([Q.entry("minecraft:honeycomb", 0, 1, functions=[Q.looting(0, 1)])]),
    ])


EN = {
    f"entity.{Q.MOD}.{NAME}": "Guardian Bee",
    f"item.{Q.MOD}.{NAME}_spawn_egg": "Guardian Bee Spawn Egg",
}
RU = {
    f"entity.{Q.MOD}.{NAME}": "Пчела-защитник",
    f"item.{Q.MOD}.{NAME}_spawn_egg": "Яйцо призыва пчелы-защитника",
}


if __name__ == "__main__":
    generate()
