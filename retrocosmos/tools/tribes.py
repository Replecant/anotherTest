"""The primitive tribes of Venus: tribesfolk model + textures, Venus trade goods, loot, recipes and the camp.

The tribesman box model is defined once, here, in SPEC (same machinery as tools/dinosaurs.py): the generator packs
the boxes onto a box-UV sheet, paints every texel from where it sits on the model, and writes the matching Java
geometry (tribe/client/TribeGeometry.java). Every role/fur variant shares the one layout; only the paint differs.
Role props (spear, club, staff, basket, mask, feather crowns, cape) are model parts the renderer shows per role.

The camp (data/retrocosmos/structure/tribal_camp/*.nbt) is built block by block in build_camp(): stilt huts of
Venus logs with fern thatch, a central fire pit with log benches, a totem pole, hide tents, drying racks, bone
piles and a raptor rib-cage gateway; the tribe itself is stored in the template's entity list.

Coordinates of the model are Minecraft entity-model pixels: y points down, the ground is at y = 24, the face is -z.
"""
import gzip
import math
import os
import random

from PIL import Image

import dinosaurs as D
import tribe_mutants as MU
import tribe_boss as TB
import ranger_items as RI
from gen_resources import ASSETS, DATA, MOD, ROOT, item_def, save, shaped, shapeless, write_json

JAVA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "main", "java",
                        "com", "replecant", "retrocosmos", "tribe", "client")

B, P, mirrored = D.B, D.P, D.mirrored

ROLES = ("hunter", "gatherer", "shaman", "chief")
VARIANTS = 3

# parts shown only for some roles (everything else is always visible)
ROLE_PARTS = {
    "spear": ("hunter",),
    "club": ("chief",),
    "staff": ("shaman",),
    "basket": ("gatherer",),
    "mask": ("shaman",),
    "feathers": ("shaman",),
    "crown": ("chief",),
    "cape": ("chief",),
}


# ----------------------------------------------------------------------------
# The model
# ----------------------------------------------------------------------------

def tribesman_spec():
    lean = 0.42  # the stoop: torso pitched forward, head and arms counter-rotated
    parts = [
        P("hips", None, (0, 14, 0.5), (0, 0, 0), [
            B(-5, -1, -3.5, 10, 2, 7, "belt"),
        ]),
        P("flap_front", "hips", (0, 1, -3.5), (0, 0, 0), [
            B(-3, 0, -0.5, 6, 6, 1, "hide", flap="front"),
        ]),
        P("flap_back", "hips", (0, 1, 3.5), (0, 0, 0), [
            B(-3, 0, -0.5, 6, 5, 1, "hide", flap="back"),
        ]),
        P("body", None, (0, 14, 0.5), (lean, 0, 0), [
            B(-4.5, -11, -3, 9, 11, 6, "torso"),
            B(-4, -12, -1.5, 8, 2, 4, "fur", hump=True),
        ]),
        P("necklace", "body", (0, 0, 0), (0, 0, 0), [
            B(-3.5, -11, -3.5, 7, 3, 1, "necklace"),
        ]),
        P("head", "body", (0, -11.5, -1.5), (-lean + 0.06, 0, 0), [
            B(-3.5, -7, -4, 7, 7, 7, "head"),
            B(-4, -8, -4.5, 8, 2, 8, "hair"),
            B(-4, -5, -5, 8, 1, 1, "brow"),
            B(-2.5, -3, -5.5, 5, 3, 2, "muzzle"),
        ]),
        P("mask", "head", (0, 0, 0), (0, 0, 0), [
            B(-4, -8, -6.5, 8, 9, 1, "mask"),
        ]),
        P("feathers", "head", (0, -6.5, 1.5), (-0.3, 0, 0), [
            B(-5, -8, 0, 10, 8, 1, "feathers"),
        ]),
        P("crown", "head", (0, -7, -3.5), (-0.12, 0, 0), [
            B(-4.5, -6, 0, 9, 6, 1, "crown"),
        ]),
        P("cape", "body", (0, -11.5, 3), (0.08, 0, 0), [
            B(-5, 0, 0, 10, 14, 1, "cape"),
        ]),
        P("basket", "body", (0, -10.5, 3), (0, 0, 0), [
            B(-3.5, 0, 0, 7, 7, 4, "basket"),
            B(-3, -3, 1, 6, 3, 1, "fronds"),
        ]),
    ]
    arm_l = P("arm_l", "body", (5.5, -9.5, -0.5), (-lean - 0.12, 0, -0.1), [
        B(-1.5, -1.5, -1.5, 3, 11, 3, "arm"),
        B(-2, 9.5, -2, 4, 3, 4, "hand"),
    ])
    leg_l = P("leg_l", None, (2.4, 14.5, 1), (0, 0, -0.04), [
        B(-2, -0.5, -2, 4, 9, 4, "leg"),
        B(-2, 8.5, -3.5, 4, 1, 5, "foot"),
    ])
    parts += [arm_l, mirrored(arm_l, "arm_r"), leg_l, mirrored(leg_l, "leg_r")]
    # props in the right hand (rest pose: arm hangs, the prop is held upright / pointing ahead)
    parts += [
        P("spear", "arm_r", (0, 11, 0), (0.08, 0, 0), [
            B(-0.5, -19, -0.5, 1, 26, 1, "shaft"),
            B(-1.5, -24, -0.5, 3, 5, 1, "spearhead"),
        ]),
        P("staff", "arm_r", (0, 11, 0), (0.05, 0, 0), [
            B(-0.5, -18, -0.5, 1, 25, 1, "staff"),
            B(-1.5, -21, -1.5, 3, 3, 3, "orb"),
        ]),
        P("club", "arm_r", (0, 11, 0), (-1.2, 0, 0), [
            B(-0.5, -1, -0.5, 1, 6, 1, "shaft", grip=True),
            B(-1.5, 5, -1.5, 3, 5, 3, "clubhead"),
        ]),
    ]
    return {"name": "tribesman", "tex_w": 128, "parts": parts, "palette": {}}


SPEC = tribesman_spec()

# Pose offsets (radians, added to the rest rotation), blended in by the Java model.
POSES = {
    # squatting by the fire: knees up, forearms on the knees, a deeper stoop
    "sit": {"leg_l": (-1.45, -0.2, 0), "leg_r": (-1.45, 0.2, 0), "body": (0.18, 0, 0), "head": (-0.25, 0, 0),
            "arm_l": (-0.75, 0, 0.12), "arm_r": (-0.75, 0, -0.12), "flap_front": (-1.1, 0, 0)},
    # caged: hunched over the knees, arms wrapped around the shins, head hanging
    "huddle": {"head": (0.55, 0, 0), "body": (0.15, 0, 0), "arm_l": (-0.35, 0.3, -0.25), "arm_r": (-0.35, -0.3, 0.25)},
    # the dance: arms thrown up, head back, hopping
    "dance": {"arm_l": (-2.5, 0, -0.35), "arm_r": (-2.5, 0, 0.35), "body": (-0.25, 0, 0), "head": (-0.3, 0, 0)},
    # spear / staff thrust: right arm forward and up
    "thrust": {"arm_r": (-1.35, 0.1, 0), "body": (0.12, 0, 0)},
    # club smash: right arm high overhead
    "smash": {"arm_r": (-2.7, 0, 0.2), "body": (-0.1, 0, 0)},
}


# ----------------------------------------------------------------------------
# Palettes
# ----------------------------------------------------------------------------

FUR = [
    # rusty red-brown
    {"fur": (146, 80, 46), "fur_d": (100, 52, 32), "fur_l": (178, 108, 64), "skin": (208, 158, 114),
     "skin_d": (162, 112, 78), "hair": (88, 42, 26), "eye": (214, 150, 40)},
    # dark brown
    {"fur": (96, 66, 46), "fur_d": (64, 42, 30), "fur_l": (124, 88, 60), "skin": (184, 132, 92),
     "skin_d": (140, 96, 66), "hair": (46, 30, 24), "eye": (200, 120, 40)},
    # grey-ochre
    {"fur": (138, 120, 88), "fur_d": (98, 84, 62), "fur_l": (168, 150, 112), "skin": (214, 174, 130),
     "skin_d": (168, 128, 92), "hair": (82, 68, 50), "eye": (120, 170, 60)},
]

ROLE_PAL = {
    "hunter": {"paint": (198, 46, 34), "paint2": (240, 226, 196), "hide": (150, 102, 58), "hide_d": (104, 68, 40),
               "hide_spot": None},
    "gatherer": {"paint": (238, 234, 216), "paint2": (232, 118, 46), "hide": (92, 132, 62), "hide_d": (58, 92, 44),
                 "hide_spot": None},
    "shaman": {"paint": (236, 234, 222), "paint2": (60, 156, 210), "hide": (198, 160, 92), "hide_d": (140, 104, 56),
               "hide_spot": (70, 48, 30)},
    "chief": {"paint": (240, 196, 52), "paint2": (204, 44, 34), "hide": (84, 146, 60), "hide_d": (52, 104, 46),
              "hide_spot": (214, 150, 42)},
}

BONE = (232, 222, 196)
BONE_D = (184, 170, 138)
WOOD = (112, 72, 42)
WOOD_D = (78, 48, 30)
WOOD_L = (146, 98, 58)
FIBER = (196, 170, 104)
FIBER_D = (146, 120, 68)
FLINT = (70, 66, 74)
FLINT_L = (120, 116, 128)
GLOW = (110, 230, 214)
GLOW_L = (214, 255, 244)


def clamp_px(c, a=255):
    return tuple(max(0, min(255, int(round(v)))) for v in c) + (a,)


def mul(c, f):
    return tuple(v * f for v in c)


def lerp(a, b, t):
    return D.lerp(a, b, t)


# ----------------------------------------------------------------------------
# Painting
# ----------------------------------------------------------------------------

def fur_texel(pal, t, base=None, strands=True):
    """Shaggy fur: vertical strands (darker grooves), lighter tips, darker at the box edges."""
    c = base or pal["fur"]
    h = D.hash3(t.box_id, t.i, int(t.j / 2), 5)
    if strands:
        if h < 0.28:
            c = lerp(c, pal["fur_d"], 0.7)
        elif h > 0.82:
            c = lerp(c, pal["fur_l"], 0.6)
    n = (D.hash3(t.box_id, t.i, t.j, 17) - 0.5) * 14
    return tuple(v + n for v in c)


def paint(role, var, t):
    pal = dict(FUR[var])
    pal.update(ROLE_PAL[role])
    mat, f = t.mat, t.face
    a = 255
    noise = (D.hash3(t.box_id, t.i, t.j, sum(map(ord, f))) - 0.5) * 12
    lx, ly, lz = t.lx, t.ly, t.lz

    if mat == "torso":
        c = fur_texel(pal, t)
        if f == "north":  # the chest: a bare skin patch framed by fur
            cx = abs(lx)
            yy = ly - t.y0  # 0 at the collar .. 11 at the belt
            if cx < 3.0 and 1.5 < yy < 10.5 and not (cx > 2.0 and (yy < 2.5 or yy > 9.5)):
                c = pal["skin"]
                if 4.0 < yy < 5.0 and cx > 0.6:  # pecs
                    c = pal["skin_d"]
                if yy > 6 and int(yy) % 2 == 0 and cx < 1.6:  # belly
                    c = lerp(pal["skin"], pal["skin_d"], 0.45)
                c = chest_paint(role, pal, cx, lx, yy, c)
            c = tuple(v + noise * 0.5 for v in c)
        elif f == "south":
            if abs(lx) < 1.0:
                c = lerp(c, pal["fur_d"], 0.5)  # spine
        elif f == "top":
            c = lerp(c, pal["fur_d"], 0.25)

    elif mat == "fur":
        c = fur_texel(pal, t)
        if f == "top":
            c = lerp(c, pal["fur_d"], 0.3)

    elif mat == "head":
        c = paint_head(role, pal, t)
        if c is None:
            return (0, 0, 0, 0)

    elif mat == "hair":
        c = pal["hair"]
        h = D.hash3(t.box_id, t.i, 3)
        if h < 0.3:
            c = mul(c, 0.78)
        elif h > 0.85:
            c = lerp(c, pal["fur_l"], 0.35)
        if f in ("north", "east", "west", "south"):
            # ragged lower edge: alternate strands hang down a pixel further
            if t.j == t.h - 1 and (t.i + (t.box_id % 2)) % 2 == 0:
                a = 0
            if f == "north" and t.j == t.h - 1:
                a = 0 if abs(lx) < 3.2 else 255  # a straight fringe, the forehead stays clear
        if f == "bottom":
            a = 0 if abs(lx) < 3.4 and lz < 3.0 else 255  # the head is inside; the fringe is open
        c = tuple(v + noise * 0.6 for v in c)

    elif mat == "brow":
        c = lerp(pal["fur_d"], pal["skin_d"], 0.35)
        if f == "bottom":
            c = mul(pal["skin_d"], 0.7)
        if role == "chief" and f == "north":
            c = pal["paint2"]
        c = tuple(v + noise * 0.5 for v in c)

    elif mat == "muzzle":
        c = pal["skin"]
        if f == "north":
            if t.j == 0:
                c = lerp(pal["skin"], pal["skin_d"], 0.15)
                if t.i in (1, 3):
                    c = mul(pal["skin_d"], 0.72)  # flat broad nose: nostrils
                if t.i == 2:
                    c = lerp(pal["skin"], pal["skin_d"], 0.5)
            elif t.j == 1:
                c = lerp(pal["skin"], pal["skin_d"], 0.3)
                if 0 < t.i < 4:
                    c = mul(pal["skin_d"], 0.62)  # thin, wide lips
                if role == "hunter" and t.i in (0, 4):
                    c = pal["paint"]
            else:
                c = lerp(pal["skin"], pal["skin_d"], 0.25)
        elif f == "top":
            c = lerp(pal["skin"], pal["skin_d"], 0.2) if t.i == 2 else pal["skin"]
        elif f in ("east", "west"):
            c = lerp(pal["skin"], pal["skin_d"], 0.35)
            if role == "hunter" and t.j == 0:
                c = pal["paint"]
        else:
            c = pal["skin_d"]
        c = tuple(v + noise * 0.5 for v in c)

    elif mat == "arm":
        c = fur_texel(pal, t)
        if role == "hunter" and 2.5 < ly < 4.5 and f in ("north", "east", "west", "south"):
            c = pal["paint"]  # arm bands
        if role == "gatherer" and 1.5 < ly < 2.5 and f != "top":
            c = FIBER  # woven bracelet
        if role == "chief" and 6.5 < ly < 8 and f != "top":
            c = BONE if (t.i % 2 == 0) else BONE_D  # bone arm ring

    elif mat == "hand":
        c = pal["skin_d"]
        if f == "north" and t.j >= 1 and t.i % 2 == 1:
            c = mul(pal["skin_d"], 0.82)  # fingers
        if f == "bottom":
            c = mul(pal["skin_d"], 0.9)
        if f == "top":
            c = fur_texel(pal, t)
        c = tuple(v + noise * 0.5 for v in c)

    elif mat == "leg":
        c = fur_texel(pal, t)
        if t.ly > t.y1 - 1.5:  # ankles: shaggy fur cuffs
            c = lerp(c, pal["fur_d"], 0.4)

    elif mat == "foot":
        c = pal["skin_d"]
        if f == "north" and t.i % 2 == 0:
            c = mul(pal["skin_d"], 0.8)  # toes
        if f == "top" and lz < -1.5 and t.i % 2 == 0:
            c = mul(pal["skin_d"], 0.88)
        c = tuple(v + noise * 0.5 for v in c)

    elif mat == "belt":
        # braided fern-fiber cord
        c = FIBER if (t.i + t.j) % 2 == 0 else FIBER_D
        if f in ("top", "bottom"):
            c = FIBER_D
            if abs(lx) < 4 and abs(lz) < 2.6:
                a = 0
        c = tuple(v + noise * 0.4 for v in c)

    elif mat == "hide":
        c = paint_hide(pal, t)
        if c is None:
            return (0, 0, 0, 0)

    elif mat == "necklace":
        c = paint_necklace(role, pal, t)
        if c is None:
            return (0, 0, 0, 0)

    elif mat == "shaft":
        c = WOOD if t.i % 2 == 0 else WOOD_D
        if t.feat.get("grip") or True:
            yy = ly - t.y0
            if t.feat.get("grip") and yy < 4:
                c = FIBER if int(yy) % 2 == 0 else FIBER_D
            elif not t.feat.get("grip") and 2 <= yy < 5:
                c = FIBER if int(yy) % 2 == 0 else FIBER_D  # binding under the head
            elif not t.feat.get("grip") and 18 <= yy < 22:
                c = (196, 52, 40) if int(yy) % 2 == 0 else (120, 30, 24)  # red grip wrap
        if not t.feat.get("grip") and 6 <= ly - t.y0 < 8 and f in ("east", "west"):
            c = (226, 190, 60)  # feather tuft

    elif mat == "spearhead":
        # knapped flint leaf blade, cut to a point
        yy = ly - t.y0
        c = FLINT_L if (t.i + t.j) % 3 == 0 else FLINT
        if f in ("north", "south"):
            half = (yy + 0.5) / t.h  # 0 at the tip .. 1 at the base
            width = 1.6 * min(1.0, half * 1.6) if yy < t.h - 1 else 0.6
            if abs(lx) > width:
                a = 0
            if abs(lx) > width - 0.9:
                c = lerp(c, (200, 196, 210), 0.5)  # knapped, glinting edges
        if f == "top":
            a = 0
        c = tuple(v + noise for v in c)

    elif mat == "staff":
        c = WOOD_D if (t.j + t.i) % 3 else WOOD
        yy = ly - t.y0
        if int(yy) % 7 == 3:
            c = WOOD_L  # knots
        if 3 <= yy < 6:
            c = (60, 150, 200) if int(yy) % 2 else BONE  # beads
        if 4 <= yy < 6 and f in ("east", "west"):
            c = (214, 64, 44)

    elif mat == "orb":
        # a glowcap cap tied to the staff: glowing cyan with pale spots
        c = GLOW if (t.i + t.j) % 2 else lerp(GLOW, GLOW_L, 0.5)
        if f == "bottom":
            c = mul(GLOW, 0.6)
        if f == "top" and t.i == 1 and t.j == 1:
            c = GLOW_L

    elif mat == "clubhead":
        c = WOOD if (t.i * 3 + t.j) % 4 else WOOD_L
        if (t.i + t.j * 2) % 3 == 0 and f not in ("top",):
            c = BONE  # embedded raptor teeth
        if f == "top":
            c = WOOD_D

    elif mat == "basket":
        weave = ((t.i // 1) + (t.j // 1)) % 2
        c = FIBER if weave else FIBER_D
        if t.j == 0 and f != "top":
            c = WOOD  # rim
        if f == "top":
            c = (60, 104, 54)  # gathered greens inside
            if (t.i + t.j) % 3 == 0:
                c = (224, 92, 44)  # fire-lily fruit
        c = tuple(v + noise * 0.5 for v in c)

    elif mat == "fronds":
        c = paint_fronds(t)
        if c is None:
            return (0, 0, 0, 0)

    elif mat == "mask":
        c = paint_mask(pal, t)
        if c is None:
            return (0, 0, 0, 0)

    elif mat == "feathers":
        c = paint_feathers(t, ((214, 52, 40), (240, 196, 52), (52, 140, 196), (236, 232, 216)), fan=True)
        if c is None:
            return (0, 0, 0, 0)

    elif mat == "crown":
        c = paint_feathers(t, ((240, 196, 52), (214, 52, 40), (240, 196, 52), (52, 150, 90)), fan=False)
        if c is None:
            return (0, 0, 0, 0)

    elif mat == "cape":
        c = paint_cape(pal, t)
        if c is None:
            return (0, 0, 0, 0)

    else:
        raise ValueError(mat)

    return clamp_px(c, a)


def chest_paint(role, pal, cx, lx, yy, c):
    if role == "hunter":
        if 2.5 < yy < 3.5 or 6.5 < yy < 7.5:  # two red ochre stripes
            return pal["paint"]
        if 4.5 < yy < 5.5 and cx < 0.6:
            return pal["paint"]
    elif role == "gatherer":
        if (int(lx + 3) + int(yy)) % 3 == 0 and 2.5 < yy < 8.5 and cx < 2.6:
            return pal["paint"]  # clay dots
    elif role == "shaman":
        if yy > 2.5 and yy < 8.5 and int(yy) % 2 == 1 and cx > 0.5:
            return pal["paint"]  # painted ribs
        if cx < 0.5 and 2.5 < yy < 9.5:
            return pal["paint"]  # spine/sternum
        if 8.5 < yy < 9.5:
            return pal["paint2"]
    elif role == "chief":
        v = yy - 3 - cx * 0.9  # a yellow chevron
        if -0.6 < v < 0.6 or (5.5 < yy < 6.5 and cx < 2.5):
            return pal["paint"] if v > -0.6 and v < 0.6 else pal["paint2"]
    return c


def paint_head(role, pal, t):
    f, lx, ly, lz = t.face, t.lx, t.ly, t.lz
    skin, skin_d = pal["skin"], pal["skin_d"]
    noise = (D.hash3(t.box_id, t.i, t.j, 3) - 0.5) * 10
    if f == "north":
        j, i = t.j, t.i
        c = skin
        if j <= 1:
            c = lerp(skin, skin_d, 0.15)  # low sloping forehead
            if role == "chief" and j == 1:
                c = pal["paint2"]  # red forehead band
            if role == "shaman" and j == 1 and i % 2 == 0:
                c = pal["paint2"]
        elif j == 2:
            c = mul(skin_d, 0.8)  # shadow under the brow ridge
        elif j == 3:
            c = mul(skin_d, 0.9)
            if i in (1, 5):
                c = (236, 226, 204)
            if i in (2, 4):
                c = pal["eye"] if role != "shaman" else (30, 20, 16)
            if i == 3:
                c = skin_d
            if role == "shaman" and i in (0, 6):
                c = pal["paint"]  # skull paint around the eyes
        else:
            c = lerp(skin, skin_d, 0.2)
            if i in (0, 6):
                c = fur_texel(pal, t, pal["fur"])  # cheek whiskers / sideburns
            if role == "hunter" and j == 4 and i in (0, 1, 5, 6):
                c = pal["paint"]
            if role == "gatherer" and j == 4 and i in (1, 5):
                c = pal["paint"]
        return tuple(v + noise * 0.5 for v in c)
    if f in ("east", "west"):
        # sides: skin in front (cheek, ear), fur behind
        front = lz - t.z0  # 0 at the face
        if front < 2.5 and ly > t.y0 + 2:
            c = lerp(skin, skin_d, 0.3)
            if 1.5 < front < 2.5 and t.y0 + 3 < ly < t.y0 + 5:
                c = mul(skin_d, 0.85)  # ear
            if role == "hunter" and t.y0 + 4 < ly < t.y0 + 5:
                c = pal["paint"]
            return tuple(v + noise * 0.4 for v in c)
        return fur_texel(pal, t, pal["hair"])
    if f == "bottom":
        return mul(skin_d, 0.85)
    if f == "top":
        return pal["hair"]
    return fur_texel(pal, t, pal["hair"])  # back of the head


def paint_hide(pal, t):
    f = t.face
    c = pal["hide"]
    if pal.get("hide_spot") and D.value_noise(t.lx * 1.6, t.ly * 1.6, t.box_id * 3.0, 1.0, 9) > 0.66:
        c = pal["hide_spot"]
    if t.i == 0 or t.i == t.w - 1:
        c = pal["hide_d"]
    if f in ("north", "south", "east", "west"):
        yy = t.ly - t.y0
        # ragged bottom edge
        if yy > t.h - 1 and (t.i + (1 if t.feat.get("flap") == "back" else 0)) % 2 == 0:
            return None
        if yy < 1:
            c = pal["hide_d"]
    n = (D.hash3(t.box_id, t.i, t.j, 11) - 0.5) * 16
    return tuple(v + n for v in c)


def paint_necklace(role, pal, t):
    f = t.face
    if f not in ("north",):
        if f in ("east", "west") and t.j == 0:
            return FIBER_D
        if f == "top":
            return None
        return None if f != "south" else None
    i, j = t.i, t.j
    # cord across the top row, sagging to the middle; teeth/beads hang from it
    sag = 1 if 1 <= i <= 5 else 0
    if j == sag - 0 and j == 0 and sag == 0:
        return FIBER_D
    if j == sag:
        if role == "gatherer":
            return (232, 112, 48) if i % 2 else (246, 206, 90)  # fire-lily petals
        return FIBER_D if i % 2 == 0 else BONE_D
    if j == sag + 1:
        if role in ("hunter", "chief") and i % 2 == 1:
            return BONE  # raptor teeth
        if role == "shaman" and i % 2 == 0:
            return (60, 156, 210) if i % 4 == 0 else BONE
        if role == "gatherer" and i % 2 == 1:
            return (246, 206, 90)
        return None
    if j == 2 and role == "chief" and i == 3:
        return BONE  # the big centre fang
    return None


def paint_fronds(t):
    if t.face not in ("north", "south"):
        return None if t.face in ("top",) else (52, 104, 54)
    # three fern tips poking out of the basket
    for cx in (-2, 0, 2):
        dx = t.lx - cx
        top = t.y0 + abs(dx) * 2.2
        if abs(dx) < 1.0 and t.ly > top:
            return (70, 128, 62) if (t.j + t.i) % 2 else (100, 150, 70)
    return None


def paint_mask(pal, t):
    """Carved wooden spirit mask: pale ochre wood, huge round eye holes ringed in blue, a grinning mouth."""
    f = t.face
    base = (214, 176, 112)
    if f != "north":
        if f == "south":
            return mul(base, 0.7)
        return lerp(base, WOOD, 0.4)
    i, j = t.i, t.j  # 8 x 9
    u = t.lx  # -4 .. 4
    v = t.ly - t.y0  # 0 .. 9
    # outline: an oval, cut-out corners
    ov = (u / 4.0) ** 2 + ((v - 4.6) / 4.7) ** 2
    if ov > 1.05:
        return None
    c = base
    if ov > 0.72:
        c = (196, 66, 40)  # red rim
    for ex in (-1.9, 1.9):
        d = math.hypot(u - ex, (v - 3.6) * 1.1)
        if d < 0.75:
            return (24, 18, 14)  # eye hole
        if d < 1.45:
            return pal["paint2"]
    if 1.0 < v < 2.0 and abs(u) < 3:
        c = (24, 18, 14) if abs(u) < 0.5 else c
    if 4.5 < v < 6.0 and abs(u) < 0.8:
        c = (140, 92, 50)  # nose
    if 6.4 < v < 7.6 and abs(u) < 2.5:
        c = BONE if int(u + 4) % 2 == 0 else (24, 18, 14)  # teeth
    if 0 < v < 1.0 and abs(u) < 2.5:
        c = (240, 196, 52)
    n = (D.hash3(t.box_id, i, j, 21) - 0.5) * 10
    return tuple(x + n for x in c)


def paint_feathers(t, colours, fan=True):
    if t.face not in ("north", "south"):
        return None
    u = t.lx  # -w/2 .. w/2
    v = t.ly - t.y0  # 0 top .. h bottom
    n_feathers = int(t.w)
    k = int(math.floor(u + t.w / 2.0))  # feather index across
    k = max(0, min(n_feathers - 1, k))
    centre = (k - (n_feathers - 1) / 2.0) / ((n_feathers - 1) / 2.0)  # -1 .. 1
    length = t.h * (1.0 - (0.45 * abs(centre) ** 1.5 if fan else 0.25 * abs(centre)))
    if not fan and k % 2 == 1:
        length *= 0.75
    if v < t.h - length:
        return None
    c = colours[k % len(colours)]
    if v < t.h - length + 1:
        c = mul(c, 0.7)  # dark tip
    if t.face == "south":
        c = mul(c, 0.8)
    return c


def paint_cape(pal, t):
    """The chief's cape: a whole raptor hide, green with ochre tiger stripes, ragged at the hem."""
    f = t.face
    yy = t.ly - t.y0
    if f in ("north", "south", "east", "west") and yy > t.h - 1.5:
        if (t.i + int(yy)) % 2 == 0:
            return None
    if f == "north":
        return mul(pal["hide"], 0.75)
    c = pal["hide"]
    band = (yy * 0.9 + abs(t.lx) * 0.5)
    if math.floor(band) % 4 == 0:
        c = pal["hide_spot"] or pal["hide_d"]
    if abs(t.lx) < 0.6:
        c = mul(pal["hide_d"], 0.9)  # spine ridge
    n = (D.hash3(t.box_id, t.i, t.j, 13) - 0.5) * 14
    return tuple(v + n for v in c)


def build_texture(role, var):
    spec = SPEC
    if "tex_h" not in spec:
        D.pack(spec)
    img = Image.new("RGBA", (spec["tex_w"], spec["tex_h"]), (0, 0, 0, 0))
    mats = D.part_matrices(spec)
    box_id = 0
    for part in spec["parts"]:
        m = mats[part["name"]]
        for b in part["boxes"]:
            box_id += 1
            x0, y0, z0 = b["pos"]
            w, h, d = b["size"]
            for face, (u0, v0), (cols, rows), to_local in D.faces(b):
                n = D.apply(m, D.FACE_NORMALS[face], 0.0)
                for j in range(rows):
                    for i in range(cols):
                        lx, ly, lz = to_local(i, j)
                        mx, my, mz = D.apply(m, (lx, ly, lz))
                        fy = (ly - y0) / h if h else 0.0
                        edge = i == 0 or j == 0 or i == cols - 1 or j == rows - 1
                        t = D.Texel(mat=b["mat"], feat=b["feat"], face=face, i=i, j=j, lx=lx, ly=ly, lz=lz,
                                    mx=mx, my=my, mz=mz, nx=n[0], ny=n[1], nz=n[2], fy=fy, edge=edge,
                                    x0=x0, y0=y0, z0=z0, x1=x0 + w, y1=y0 + h, z1=z0 + d, w=w, h=h, d=d,
                                    box_id=box_id)
                        img.putpixel((u0 + i, v0 + j), paint(role, var, t))
    return img


# ----------------------------------------------------------------------------
# Java geometry
# ----------------------------------------------------------------------------

def write_java():
    for spec in TB.SPECS:
        D.pack(spec)
    layer = "\n\n".join(D.java_layer(spec) for spec in [SPEC] + MU.SPECS + TB.SPECS)
    scales = ",\n            ".join(f"Map.entry(\"{k}\", {D.jf(v)})" for k, v in TB.java_scales().items())
    poses = []
    for pose, parts in list(POSES.items()) + list(MU.POSES.items()) + list(TB.POSES.items()):
        entries = ",\n            ".join(
            f"Map.entry(\"{k}\", new float[]{{{D.jf(v[0])}, {D.jf(v[1])}, {D.jf(v[2])}}})" for k, v in parts.items())
        poses.append(f"    public static final Map<String, float[]> {pose.upper()} = Map.ofEntries(\n            {entries});")
    role_parts = ",\n            ".join(
        f"Map.entry(\"{k}\", new int[]{{{', '.join(str(ROLES.index(r)) for r in v)}}})" for k, v in ROLE_PARTS.items())
    src = f"""package com.replecant.retrocosmos.tribe.client;

import java.util.Map;
import java.util.function.Function;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;

/**
 * Box geometry of the Venus tribesfolk, of Dr. Oinstein's mutant hominids and of the doctor himself (boss). GENERATED by tools/tribes.py from the same box list that paints their
 * textures - edit the spec there and re-run tools/gen_resources.py instead of editing this file.
 */
@SuppressWarnings("unused")
public final class TribeGeometry {{
    private TribeGeometry() {{}}

{layer}

    // ---- key poses, as rotation offsets added on top of the rest pose ----

{chr(10).join(poses)}

    /** Role props: part name to the roles (Tribesman.Role ordinals) that show it. */
    public static final Map<String, int[]> ROLE_PARTS = Map.ofEntries(
            {role_parts});

    /** Parts drawn at a uniform scale (the strider's pilot is a 0.75-scale doctor). */
    public static final Map<String, Float> SCALES = Map.ofEntries(
            {scales});

    /** Sets the {{@link #SCALES}} on a freshly reset model (call after super.setupAnim). */
    public static void applyScales(Function<String, ModelPart> parts) {{
        for (Map.Entry<String, Float> e : SCALES.entrySet()) {{
            ModelPart part = parts.apply(e.getKey());
            if (part != null) {{
                float s = e.getValue();
                part.xScale = s;
                part.yScale = s;
                part.zScale = s;
            }}
        }}
    }}

    /** Blends a key pose in: every listed part is rotated by amount * its offset. */
    public static void applyPose(Function<String, ModelPart> parts, Map<String, float[]> pose, float amount) {{
        if (amount <= 0.0F) {{
            return;
        }}
        for (Map.Entry<String, float[]> e : pose.entrySet()) {{
            ModelPart part = parts.apply(e.getKey());
            if (part != null) {{
                float[] r = e.getValue();
                part.xRot += r[0] * amount;
                part.yRot += r[1] * amount;
                part.zRot += r[2] * amount;
            }}
        }}
    }}
}}
"""
    os.makedirs(JAVA_DIR, exist_ok=True)
    with open(os.path.join(JAVA_DIR, "TribeGeometry.java"), "w", encoding="utf-8") as f:
        f.write(src)


# ----------------------------------------------------------------------------
# Item sprites (16x16)
# ----------------------------------------------------------------------------

def sprite(rows, colours):
    """rows: 16 strings; each char is a key into colours (space / '.' = transparent)."""
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in " .":
                continue
            img.putpixel((x, y), clamp_px(colours[ch]))
    return img


def outline(img, colour):
    """Dark outline around the opaque pixels (vanilla item style)."""
    src = img.copy()
    for y in range(16):
        for x in range(16):
            if src.getpixel((x, y))[3]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < 16 and 0 <= ny < 16 and src.getpixel((nx, ny))[3]:
                    img.putpixel((x, y), clamp_px(colour))
                    break
    return img


def item_amber():
    rows = ["................",
            "................",
            "......aaa.......",
            ".....abbba......",
            "....abhhbba.....",
            "...abhbbbbba....",
            "...abbbbbbbba...",
            "..abbbbikbbbba..",
            "..abbbikkibbba..",
            "..abbbbbbbbbba..",
            "...abbbbbbbbba..",
            "...acbbbbbbca...",
            "....accbbcca....",
            ".....acccca.....",
            "......aaaa......",
            "................"]
    return sprite(rows, {"a": (124, 58, 14), "b": (232, 138, 30), "c": (184, 92, 20), "h": (255, 226, 140),
                         "i": (60, 34, 20), "k": (110, 66, 26)})


def item_tooth():
    rows = ["................",
            "................",
            "...........aa...",
            "..........abba..",
            ".........abhba..",
            "........abhbba..",
            ".......abhbbba..",
            "......abhbbba...",
            ".....abhbbbca...",
            "....abhbbbca....",
            "...abhbbcca.....",
            "..abbbcca.......",
            ".abbcca.........",
            ".abca...........",
            "..a.............",
            "................"]
    rows = [r[::-1] for r in rows]
    return sprite(rows, {"a": (110, 96, 72), "b": (236, 228, 204), "c": (190, 176, 140), "h": (255, 252, 240)})


def item_fiber():
    rows = ["................",
            "..........a.....",
            ".........aba....",
            "....a...abca....",
            "...aba.abca.....",
            "...abcaabca.....",
            "....abcbcaa.....",
            ".....acbca......",
            "....addddda.....",
            "....aeeeeea.....",
            ".....acbca......",
            "....abca.bca....",
            "...abca...bca...",
            "...aba.....aa...",
            "....a...........",
            "................"]
    return sprite(rows, {"a": (60, 70, 34), "b": (150, 172, 84), "c": (110, 132, 60), "d": (196, 170, 104),
                         "e": (146, 120, 68)})


def item_hide():
    rows = ["................",
            "................",
            "..aa........aa..",
            ".abba......abba.",
            ".abbbaaaaaabbba.",
            "..abbsbbbbsbba..",
            "..absbbbbbbsba..",
            "..abbbssssbbba..",
            "..abbbbbbbbbba..",
            "..absssbbsssba..",
            "..abbbbbbbbbba..",
            ".abbbbssssbbbba.",
            ".abba.abba.abba.",
            "..aa...aa...aa..",
            "................",
            "................"]
    return sprite(rows, {"a": (34, 60, 30), "b": (84, 146, 60), "s": (214, 150, 42)})


def item_tea():
    rows = ["................",
            "......g..g......",
            ".......g..g.....",
            "......g..g......",
            "................",
            "..aaaaaaaaaaaa..",
            ".abttttsttttttba",
            ".abtsttttttsttba",
            "..abttttttttba..",
            "..abbbbbbbbbba..",
            "...abbbbbbbba...",
            "....abbbbbba....",
            ".....aaaaaa.....",
            "................",
            "................",
            "................"]
    img = sprite(rows, {"a": (60, 36, 20), "b": (140, 92, 52), "t": (90, 220, 206), "s": (220, 255, 246),
                        "g": (170, 240, 230)})
    return img


def item_spear():
    rows = ["..............hh",
            ".............hfh",
            "............hffh",
            "...........hfgh.",
            "..........bhhh..",
            ".........bb.....",
            "........sb......",
            ".......ss.......",
            "......ws........",
            ".....ww.........",
            "....rw..........",
            "...rr...........",
            "..rw............",
            ".ww.............",
            "ww..............",
            "w..............."]
    img = sprite(rows, {"h": (54, 50, 60), "f": (128, 124, 138), "g": (200, 198, 214), "b": (196, 170, 104),
                        "s": (146, 98, 58), "w": (112, 72, 42), "r": (196, 52, 40)})
    return img


def item_mask():
    rows = ["................",
            "..r..y..b..r....",
            "..r.y.b..y.r....",
            "...aaaaaaaaa....",
            "..abbbbbbbbba...",
            "..aboobbbooba...",
            ".abolobbbolob a.",
            ".abboobnboobba..",
            ".abbbbbnbbbbba..",
            "..abbbnnnbbba...",
            "..abwkwkwkwba...",
            "...abkwkwkba....",
            "....abbbbba.....",
            ".....aaaaa......",
            "................",
            "................"]
    rows = [r[:16].ljust(16, ".") for r in rows]
    return sprite(rows, {"a": (110, 40, 26), "b": (214, 176, 112), "o": (60, 156, 210), "l": (24, 18, 14),
                         "n": (140, 92, 50), "w": (236, 228, 204), "k": (24, 18, 14), "r": (214, 52, 40),
                         "y": (240, 196, 52)})


def item_charm():
    rows = ["......cccc......",
            ".....c....c.....",
            "....c......c....",
            "....c......c....",
            ".....c....c.....",
            "......cbbc......",
            ".....abhhba.....",
            ".....abmmba.....",
            "......abba......",
            ".....r.aa.y.....",
            "....rr.ga.yy....",
            "....r..gg..y....",
            "...rr..g...yy...",
            "...r........y...",
            "................",
            "................"]
    return sprite(rows, {"c": (146, 120, 68), "a": (150, 136, 108), "b": (236, 228, 204), "h": (255, 252, 240),
                         "m": (232, 138, 30), "r": (214, 52, 40), "y": (60, 156, 210), "g": (236, 228, 204)})


ITEMS = {
    "venus_amber": item_amber, "raptor_tooth": item_tooth, "fern_fiber": item_fiber, "dino_hide": item_hide,
    "glowcap_tea": item_tea, "bone_spear": item_spear, "tribal_mask": item_mask, "shaman_charm": item_charm,
}


def mask_equipment_texture():
    """64x32 humanoid armor layout: the helmet cube (8x8x8 at uv 0,0) carries the painted mask on its front."""
    img = Image.new("RGBA", (64, 32), (0, 0, 0, 0))
    base = (214, 176, 112)
    front = {}
    for j in range(8):
        for i in range(8):
            u = i - 3.5
            v = j
            ov = (u / 4.0) ** 2 + ((v - 3.8) / 4.3) ** 2
            if ov > 1.08:
                continue
            c = base
            if ov > 0.7:
                c = (196, 66, 40)
            for ex in (-1.8, 1.8):
                d = math.hypot(u - ex, (v - 3.0) * 1.1)
                if d < 0.75:
                    c = (24, 18, 14)
                elif d < 1.4 and c == base:
                    c = (60, 156, 210)
            if j == 0 and abs(u) < 2.6:
                c = (240, 196, 52)
            if j == 6 and abs(u) < 2.6:
                c = (236, 228, 204) if i % 2 == 0 else (24, 18, 14)
            front[(i, j)] = c
    for (i, j), c in front.items():
        img.putpixel((8 + i, 8 + j), clamp_px(c))
    # straps of fern cord around the sides and back, feathers standing up from the top edge at the back
    for i in range(8):
        img.putpixel((i, 8 + 4), clamp_px(FIBER_D))  # right side
        img.putpixel((16 + i, 8 + 4), clamp_px(FIBER_D))  # left side
        img.putpixel((24 + i, 8 + 4), clamp_px(FIBER))  # back
    for i, c in enumerate(((214, 52, 40), (240, 196, 52), (60, 156, 210), (214, 52, 40))):
        for j in range(3):
            img.putpixel((26 + i, 8 + j), clamp_px(c))
    return img


# ----------------------------------------------------------------------------
# The camp template
# ----------------------------------------------------------------------------

import station as ST  # noqa: E402  (NBT writer)

TAG_DOUBLE = 6


class Double(float):
    tag = TAG_DOUBLE


def V(name):
    return name if ":" in name else f"{MOD}:{name}"


LEAVES = {"distance": "1", "persistent": "true", "waterlogged": "false"}


class Camp:
    SIZE = 27
    HEIGHT = 12

    def __init__(self, seed):
        self.rnd = random.Random(seed)
        self.blocks = {}
        self.entities = []
        self.c = self.SIZE // 2

    def put(self, x, y, z, name, props=None, nbt=None):
        if 0 <= x < self.SIZE and 0 <= z < self.SIZE and 0 <= y < self.HEIGHT:
            self.blocks[(x, y, z)] = (V(name), dict(props or {}), nbt)

    def get(self, x, y, z):
        b = self.blocks.get((x, y, z))
        return b[0] if b else None

    def solid(self, x, y, z):
        n = self.get(x, y, z)
        return n is not None and n != "minecraft:air"

    # ---- ground ----
    def plaza(self):
        """The trodden camp ground. Nothing in the footprint is dirt-tagged, so the jungle's trees and ferns
        (placed after structures) cannot take root inside the camp; the mossy corners blend into the forest."""
        c = self.c
        for x in range(self.SIZE):
            for z in range(self.SIZE):
                d = math.hypot(x - c, z - c)
                edge = 11.2 + 1.3 * D.value_noise(x, 0, z, 3.0, 41)
                r = self.rnd.random()
                if d < 2.2:
                    name = "venus_cobblestone"
                elif 3.0 < d < 4.4 and r < 0.75:
                    name = "minecraft:dirt_path"  # the trodden ring around the fire
                elif d <= edge:
                    name = "minecraft:packed_mud" if r < 0.72 else "minecraft:dirt_path"
                else:
                    name = "minecraft:packed_mud"
                self.put(x, 0, z, name)
                for y in range(1, 6):
                    self.put(x, y, z, "minecraft:air")
                if d > edge - 0.8:
                    # overgrown rim: moss carpet and leafy bushes
                    rr = self.rnd.random()
                    if rr < 0.55 + 0.1 * (d - edge):
                        self.put(x, 1, z, "minecraft:moss_carpet")
                    elif rr < 0.7 and d > edge + 1:
                        self.put(x, 1, z, "venus_leaves", LEAVES)

    def greenery(self):
        """A few ferns, sedges and lilies on mossy soil patches in the corners (planted by the tribe)."""
        c = self.c
        corners = [(x, z) for x in range(self.SIZE) for z in range(self.SIZE)
                   if math.hypot(x - c, z - c) > 13.0 and self.get(x, 1, z) == V("minecraft:moss_carpet")]
        self.rnd.shuffle(corners)
        for (x, z) in corners[:14]:
            if self.solid(x, 2, z):
                continue
            self.put(x, 0, z, "venus_moss")
            if self.rnd.random() < 0.35:
                self.put(x, 1, z, "venus_giant_fern", {"half": "lower"})
                self.put(x, 2, z, "venus_giant_fern", {"half": "upper"})
            else:
                self.put(x, 1, z, self.rnd.choice(("venus_sedge", "venus_horsetail", "venus_fire_lily")))

    def path_to(self, x1, z1):
        """A trodden path from the fire ring out to a hut door."""
        c = self.c
        steps = int(max(abs(x1 - c), abs(z1 - c)) * 2)
        for k in range(steps + 1):
            t = k / max(1, steps)
            x = round(c + (x1 - c) * t)
            z = round(c + (z1 - c) * t)
            if math.hypot(x - c, z - c) > 2.5 and self.get(x, 0, z) == V("minecraft:packed_mud"):
                self.put(x, 0, z, "minecraft:dirt_path")
                if self.get(x, 1, z) in (V("minecraft:moss_carpet"), V("venus_leaves")):
                    self.put(x, 1, z, "minecraft:air")

    # ---- the fire pit and benches ----
    def fire_pit(self):
        c = self.c
        self.put(c, 0, c, "minecraft:campfire", {"facing": "north", "lit": "true", "signal_fire": "false",
                                                  "waterlogged": "false"})
        for dx, dz in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            self.put(c + dx, 1, c + dz, "venus_cobblestone" if self.rnd.random() < 0.5 else "minecraft:air")
        # a roasting spit: two posts and a cross-bar over the flames
        for dx in (-2, 2):
            self.put(c + dx, 1, c, "venus_log", {"axis": "y"})
            self.put(c + dx, 2, c, "venus_log", {"axis": "y"})
        for dx in (-2, -1, 0, 1, 2):
            self.put(c + dx, 3, c, "venus_log", {"axis": "x"})
        # log benches on three sides; the fourth side faces the totem
        for side in ("s", "w", "e"):
            for k in (-1, 0, 1):
                if side == "s":
                    self.put(c + k, 1, c + 4, "venus_log", {"axis": "x"})
                elif side == "w":
                    self.put(c - 4, 1, c + k, "venus_log", {"axis": "z"})
                else:
                    self.put(c + 4, 1, c + k, "venus_log", {"axis": "z"})

    def totem(self, x, z):
        """A totem pole of stacked logs, bone arms, skulls and painted streamers, facing the fire (south)."""
        self.put(x, 0, z, "venus_log", {"axis": "y"})
        self.put(x, 1, z, "minecraft:bone_block", {"axis": "y"})
        for y in range(2, 6):
            self.put(x, y, z, "venus_log", {"axis": "y"})
        self.put(x, 6, z, "minecraft:skeleton_skull", {"rotation": "0", "powered": "false"})
        self.put(x - 1, 4, z, "minecraft:bone_block", {"axis": "x"})
        self.put(x + 1, 4, z, "minecraft:bone_block", {"axis": "x"})
        self.put(x, 3, z + 1, "minecraft:skeleton_wall_skull", {"facing": "south", "powered": "false"})
        self.put(x, 5, z + 1, "minecraft:red_wall_banner", {"facing": "south"})
        self.put(x, 5, z - 1, "minecraft:yellow_wall_banner", {"facing": "north"})
        self.put(x + 1, 1, z + 1, "venus_glowcap")
        self.put(x - 1, 1, z + 1, "venus_glowcap")

    # ---- stilt huts ----
    THATCH = (("venus_leaves", 0.5), ("venus_amber_leaves", 0.8), ("minecraft:hay_block", 1.0))

    def thatch(self, x, y, z):
        r = self.rnd.random()
        for name, p in self.THATCH:
            if r < p:
                props = LEAVES if "leaves" in name else {"axis": "y"}
                self.put(x, y, z, name, props)
                return

    def hut(self, x0, z0, door):
        """A 5x5 stilt hut: log corner stilts, plank floor three blocks up, log-and-plank walls, a fern-thatch
        cone roof with a skull on top, and stairs up to the door. door: 'n', 's', 'e' or 'w'."""
        X = range(x0, x0 + 5)
        Z = range(z0, z0 + 5)
        corners = {(x0, z0), (x0 + 4, z0), (x0, z0 + 4), (x0 + 4, z0 + 4)}
        for (x, z) in corners:
            for y in range(0, 6):
                self.put(x, y, z, "venus_log", {"axis": "y"})
        # clear under the hut (but keep the ground)
        for x in X:
            for z in Z:
                if (x, z) not in corners:
                    if not self.solid(x, 0, z):
                        self.put(x, 0, z, "minecraft:packed_mud")
                    for y in (1, 2):
                        self.put(x, y, z, "minecraft:air")
                    self.put(x, 3, z, "venus_planks")
        # walls
        dx, dz = {"n": (2, 0), "s": (2, 4), "w": (0, 2), "e": (4, 2)}[door]
        door_xz = (x0 + dx, z0 + dz)
        for x in X:
            for z in Z:
                if (x, z) in corners:
                    continue
                on_edge = x in (x0, x0 + 4) or z in (z0, z0 + 4)
                if not on_edge:
                    for y in (4, 5):
                        self.put(x, y, z, "minecraft:air")
                    continue
                axis = "x" if z in (z0, z0 + 4) else "z"
                if (x, z) == door_xz:
                    self.put(x, 4, z, "minecraft:air")
                    self.put(x, 5, z, "minecraft:air")
                    continue
                self.put(x, 4, z, "venus_log", {"axis": axis})
                middle = (x == x0 + 2) or (z == z0 + 2)
                self.put(x, 5, z, "minecraft:air" if middle else "venus_planks")  # window holes
        # thatched cone roof
        for y, r in ((6, 3), (7, 2), (8, 1)):
            for x in range(x0 + 2 - r, x0 + 3 + r):
                for z in range(z0 + 2 - r, z0 + 3 + r):
                    if y == 6 or abs(x - x0 - 2) == r or abs(z - z0 - 2) == r or y == 8:
                        self.thatch(x, y, z)
                    else:
                        self.put(x, y, z, "minecraft:air")
        self.put(x0 + 2, 9, z0 + 2, "venus_log", {"axis": "y"})
        self.put(x0 + 2, 10, z0 + 2, "minecraft:skeleton_skull", {"rotation": str(self.rnd.randrange(16)),
                                                                   "powered": "false"})
        # roof underside rests on the walls: interior ceiling at y=6 is thatch, fine; inside: bedding, a pot, a light
        inside = [(x, z) for x in range(x0 + 1, x0 + 4) for z in range(z0 + 1, z0 + 4)]
        self.rnd.shuffle(inside)
        door_in = (x0 + {"n": 2, "s": 2, "w": 1, "e": 3}[door], z0 + {"n": 1, "s": 3, "w": 2, "e": 2}[door])
        inside = [p for p in inside if p != door_in]
        for (x, z) in inside[:3]:
            self.put(x, 4, z, self.rnd.choice(("minecraft:brown_carpet", "minecraft:orange_carpet")))
        x, z = inside[3]
        self.pot(x, 4, z)
        x, z = inside[4]
        self.put(x, 4, z, "venus_glowcap")
        # storage pots between the stilts, lianas hanging from the eaves
        under = [(x, z) for x in range(x0 + 1, x0 + 4) for z in range(z0 + 1, z0 + 4)]
        for (x, z) in self.rnd.sample(under, 2):
            self.pot(x, 1, z)
        for (x, z) in self.rnd.sample([(x0 - 1, z0 - 1), (x0 + 5, z0 - 1), (x0 - 1, z0 + 5), (x0 + 5, z0 + 5),
                                       (x0 - 1, z0 + 2), (x0 + 5, z0 + 2)], 3):
            if self.solid(x, 6, z) and not self.solid(x, 5, z):
                self.put(x, 5, z, "venus_hanging_vines", {"tip": "false"})
                if not self.solid(x, 4, z):
                    self.put(x, 4, z, "venus_hanging_vines", {"tip": "true"})
                else:
                    self.put(x, 5, z, "venus_hanging_vines", {"tip": "true"})
        # stairs down from the door
        ox, oz = {"n": (0, -1), "s": (0, 1), "w": (-1, 0), "e": (1, 0)}[door]
        facing = {"n": "south", "s": "north", "w": "east", "e": "west"}[door]
        sx, sz = door_xz
        for k, y in enumerate((3, 2, 1)):
            px, pz = sx + ox * (k + 1), sz + oz * (k + 1)
            self.put(px, y, pz, "venus_stairs", {"facing": facing, "half": "bottom", "shape": "straight"})
            for yy in range(y + 1, 6):
                self.put(px, yy, pz, "minecraft:air")
            if k == 0:
                for yy in range(1, y):
                    self.put(px, yy, pz, "venus_log", {"axis": "y"})  # a post under the top step
            if not self.solid(px, 0, pz):
                self.put(px, 0, pz, "minecraft:dirt_path")
        # a lamp at the foot of the stairs
        lx, lz = sx + ox * 4 + oz, sz + oz * 4 + ox
        if not self.solid(lx, 1, lz):
            self.put(lx, 1, lz, "venus_glowcap")
        return (sx + ox * 4, sz + oz * 4)

    def pot(self, x, y, z):
        self.put(x, y, z, "minecraft:decorated_pot", {"facing": self.rnd.choice(("north", "south", "east", "west")),
                                                      "cracked": "false", "waterlogged": "false"},
                 nbt=ST.Compound({"LootTable": ST.Str(f"{MOD}:chests/tribal_hut")}))

    # ---- tents, racks, bones, the gateway ----
    def tent(self, x0, z0, along):
        """An A-frame tent of patched hides over a log ridge pole, open at one end."""
        hides = ("minecraft:brown_wool", "minecraft:orange_wool", "minecraft:brown_wool", "minecraft:light_gray_wool")
        for k in range(4):
            for (w, y) in ((0, 1), (4, 1), (1, 2), (3, 2)):
                x, z = (x0 + k, z0 + w) if along == "x" else (x0 + w, z0 + k)
                self.put(x, y, z, self.rnd.choice(hides))
            x, z = (x0 + k, z0 + 2) if along == "x" else (x0 + 2, z0 + k)
            self.put(x, 3, z, "venus_log", {"axis": along})
            for (w, y) in ((1, 1), (2, 1), (3, 1), (2, 2)):
                xx, zz = (x0 + k, z0 + w) if along == "x" else (x0 + w, z0 + k)
                self.put(xx, y, zz, "minecraft:air")
        # closed back end
        for (w, y) in ((1, 1), (2, 1), (3, 1), (2, 2)):
            x, z = (x0 + 3, z0 + w) if along == "x" else (x0 + w, z0 + 3)
            self.put(x, y, z, self.rnd.choice(hides))
        # a bed of hides and a pot inside
        self.put(x0 + 2, 1, z0 + 2, "minecraft:brown_carpet")
        self.pot(x0 + 1, 1, z0 + 1) if along == "z" else self.pot(x0 + 2, 1, z0 + 1)

    def rack(self, x0, z0, along):
        """A drying rack: two log posts, a cross-bar, hides hanging from it."""
        for k in (0, 3):
            x, z = (x0 + k, z0) if along == "x" else (x0, z0 + k)
            for y in (1, 2, 3):
                self.put(x, y, z, "venus_log", {"axis": "y"})
        colours = ("brown", "orange", "yellow", "brown")
        for k in (1, 2):
            x, z = (x0 + k, z0) if along == "x" else (x0, z0 + k)
            self.put(x, 3, z, "venus_log", {"axis": along})
            face = ("south", (0, 1)) if along == "x" else ("east", (1, 0))
            self.put(x + face[1][0], 3, z + face[1][1], f"minecraft:{self.rnd.choice(colours)}_wall_banner",
                     {"facing": face[0]})
            back = ("north", (0, -1)) if along == "x" else ("west", (-1, 0))
            self.put(x + back[1][0], 3, z + back[1][1], f"minecraft:{self.rnd.choice(colours)}_wall_banner",
                     {"facing": back[0]})

    def bones(self, x, z):
        """A heap of dinosaur bones and a skull or two."""
        for (dx, dz, y) in ((0, 0, 1), (1, 0, 1), (0, 1, 1), (0, 0, 2)):
            if self.rnd.random() < 0.85:
                self.put(x + dx, y, z + dz, "minecraft:bone_block", {"axis": self.rnd.choice("xyz")})
        self.put(x + 1, 1, z + 1, "minecraft:skeleton_skull", {"rotation": str(self.rnd.randrange(16)), "powered": "false"})
        if self.rnd.random() < 0.6:
            self.put(x - 1, 1, z, "minecraft:skeleton_skull", {"rotation": str(self.rnd.randrange(16)), "powered": "false"})

    def gateway(self, z):
        """The camp gate: two ribs of a giant dinosaur, arching over the path, its skull on top."""
        c = self.c
        for zz in (z, z + 2):
            for y in (1, 2, 3):
                self.put(c - 3, y, zz, "minecraft:bone_block", {"axis": "y"})
                self.put(c + 3, y, zz, "minecraft:bone_block", {"axis": "y"})
            self.put(c - 2, 4, zz, "minecraft:bone_block", {"axis": "x"})
            self.put(c + 2, 4, zz, "minecraft:bone_block", {"axis": "x"})
            for x in (c - 1, c, c + 1):
                self.put(x, 5, zz, "minecraft:bone_block", {"axis": "x"})
        for zz in (z, z + 1, z + 2):
            self.put(c, 6, zz, "minecraft:bone_block", {"axis": "z"})  # the spine
        self.put(c, 7, z + 2, "minecraft:skeleton_skull", {"rotation": "0", "powered": "false"})
        for x in range(c - 2, c + 3):
            for zz in range(z - 1, z + 4):
                if self.get(x, 0, zz) in (V("minecraft:packed_mud"), None):
                    self.put(x, 0, zz, "minecraft:dirt_path")
                if self.get(x, 1, zz) in (V("minecraft:moss_carpet"), V("venus_leaves")):
                    self.put(x, 1, zz, "minecraft:air")

    def free(self, x, z):
        return (0 <= x < self.SIZE and 0 <= z < self.SIZE and self.solid(x, 0, z)
                and not self.solid(x, 1, z) and not self.solid(x, 2, z)
                and all((x, z) != (int(e["blockPos"][0]), int(e["blockPos"][2])) for e in self.entities))

    def tribesman(self, x, z, role, baby=False, y=1):
        if not self.free(x, z):
            spots = sorted(((dx, dz) for dx in range(-4, 5) for dz in range(-4, 5)), key=lambda d: d[0] ** 2 + d[1] ** 2)
            x, z = next((x + dx, z + dz) for dx, dz in spots if self.free(x + dx, z + dz))
        nbt = ST.Compound({"id": ST.Str(f"{MOD}:tribesman"), "Role": ST.Str(role), "PersistenceRequired": ST.Byte(1),
                           "Assigned": ST.Byte(1)})
        if baby:
            nbt["Age"] = ST.Int(-24000)
        pos = (x + 0.5, float(y), z + 0.5)
        self.entities.append(ST.Compound({
            "blockPos": ST.List([ST.Int(x), ST.Int(y), ST.Int(z)], ST.TAG_INT),
            "pos": ST.List([Double(v) for v in pos], TAG_DOUBLE),
            "nbt": nbt}))

    def to_nbt(self):
        palette_index = {}
        palette = ST.List([], ST.TAG_COMPOUND)
        blocks = ST.List([], ST.TAG_COMPOUND)
        for (x, y, z) in sorted(self.blocks, key=lambda p: (p[1], p[2], p[0])):
            name, props, nbt = self.blocks[(x, y, z)]
            key = (name, tuple(sorted(props.items())))
            if key not in palette_index:
                palette_index[key] = len(palette)
                entry = ST.Compound({"Name": ST.Str(name)})
                if props:
                    entry["Properties"] = ST.Compound({ST.Str(k): ST.Str(v) for k, v in sorted(props.items())})
                palette.append(entry)
            entry = ST.Compound({"pos": ST.List([ST.Int(x), ST.Int(y), ST.Int(z)], ST.TAG_INT),
                                 "state": ST.Int(palette_index[key])})
            if nbt is not None:
                entry["nbt"] = nbt
            blocks.append(entry)
        return ST.Compound({
            "DataVersion": ST.Int(ST.DATA_VERSION),
            "size": ST.List([ST.Int(self.SIZE), ST.Int(self.HEIGHT), ST.Int(self.SIZE)], ST.TAG_INT),
            "palette": palette,
            "blocks": blocks,
            "entities": ST.List(list(self.entities), ST.TAG_COMPOUND),
        })


def build_camp(variant):
    """Three layouts around the same heart (fire pit, totem, benches); the jigsaw rotates them at random."""
    camp = Camp(1000 + variant)
    c = camp.c
    camp.plaza()
    camp.fire_pit()
    camp.totem(c, c - 6)
    huts = {
        0: [(1, 3, "e"), (21, 3, "w"), (3, 19, "e")],
        1: [(2, 2, "s"), (20, 2, "s"), (20, 18, "w")],
        2: [(1, 11, "e"), (21, 4, "w"), (21, 17, "w")],
    }[variant]
    for (x0, z0, door) in huts:
        foot = camp.hut(x0, z0, door)
        camp.path_to(*foot)
    if variant == 0:
        camp.tent(17, 17, "x")
        camp.rack(8, 21, "x")
        camp.bones(18, 11)
        camp.gateway(24)
    elif variant == 1:
        camp.tent(3, 17, "z")
        camp.rack(9, 21, "x")
        camp.bones(16, 10)
        camp.bones(5, 12)
        camp.gateway(24)
    else:
        camp.tent(4, 2, "x")
        camp.tent(5, 18, "z")
        camp.rack(15, 21, "x")
        camp.bones(9, 20)
        camp.gateway(24)
    camp.greenery()
    # the tribe: a chief by the totem, a shaman at the fire, hunters, gatherers and the little ones
    camp.tribesman(c + 1, c - 4, "chief")
    camp.tribesman(c - 2, c - 2, "shaman")
    camp.tribesman(c + 3, c + 6, "hunter")
    camp.tribesman(c - 6, c + 5, "hunter")
    camp.tribesman(c + 6, c - 1, "gatherer")
    camp.tribesman(c - 5, c - 5, "gatherer")
    camp.tribesman(c + 2, c + 2, "gatherer", baby=True)
    if variant != 1:
        camp.tribesman(c - 2, c + 2, "hunter", baby=True)
    if variant == 2:
        camp.tribesman(c + 7, c + 4, "hunter")
    return camp


def write_camps():
    out = os.path.join(DATA, "structure", "tribal_camp")
    os.makedirs(out, exist_ok=True)
    names = []
    for v in range(3):
        camp = build_camp(v)
        validate_camp(camp)
        root = camp.to_nbt()
        path = os.path.join(out, f"camp_{v + 1}.nbt")
        with gzip.GzipFile(path, "wb", mtime=0) as f:
            f.write(ST.nbt_bytes(root))
        names.append(f"{MOD}:tribal_camp/camp_{v + 1}")
    write_json(os.path.join(DATA, "worldgen", "template_pool", "tribal_camp", "start.json"), {
        "fallback": "minecraft:empty",
        "elements": [{"weight": 1, "element": {"element_type": "minecraft:single_pool_element", "location": n,
                                                "processors": "minecraft:empty", "projection": "rigid"}}
                     for n in names]})
    write_json(os.path.join(DATA, "worldgen", "structure", "tribal_camp.json"), {
        "type": f"{MOD}:dry_jigsaw",     # never on water (see oinstein/DryJigsawStructure.java)
        "biomes": f"#{MOD}:has_structure/tribal_camp",
        "max_distance_from_center": 80,
        "project_start_to_heightmap": "WORLD_SURFACE_WG",
        "size": 1,
        "spawn_overrides": {},
        "start_height": {"absolute": 0},
        "start_pool": f"{MOD}:tribal_camp/start",
        "step": "surface_structures",
        "terrain_adaptation": "beard_thin",
        "use_expansion_hack": False})
    write_json(os.path.join(DATA, "worldgen", "structure_set", "tribal_camps.json"), {
        # Clear of ruined villages and of Dr. Oinstein's Institute. Only sets that never exclude tribal camps
        # themselves may be listed here (the outposts already keep away from us), or the checks would recurse.
        "placement": {"type": f"{MOD}:exclusive_spread", "salt": 581273921, "separation": 22, "spacing": 52,
                      "exclusion_zones": [{"other_set": f"{MOD}:venusian_ruined_villages", "chunk_count": 6},
                                          {"other_set": f"{MOD}:oinstein_institute", "chunk_count": 8}]},
        "structures": [{"structure": f"{MOD}:tribal_camp", "weight": 1}]})
    write_json(os.path.join(DATA, "tags", "worldgen", "biome", "has_structure", "tribal_camp.json"), {
        "replace": False, "values": [f"{MOD}:venus_jungle", f"{MOD}:venus_cycad_plains", f"{MOD}:venus_fern_swamp"]})


def validate_camp(camp):
    """Every mod block must exist with exactly the properties of its blockstate file."""
    states = os.path.join(ROOT, "assets", MOD, "blockstates")
    for (name, props, _nbt) in camp.blocks.values():
        if not name.startswith(MOD + ":"):
            continue
        path = os.path.join(states, name.split(":")[1] + ".json")
        if not os.path.exists(path):
            raise SystemExit(f"tribes.py: camp uses unknown block {name}")
        import json
        with open(path, encoding="utf-8") as f:
            bs = json.load(f)
        if "variants" in bs:
            key = ",".join(f"{k}={v}" for k, v in sorted(props.items()))
            keys = {",".join(sorted(k.split(","))) if k else "" for k in bs["variants"]}
            if key not in keys and not (name.endswith("_leaves")):
                raise SystemExit(f"tribes.py: {name}[{key}] has no blockstate variant")


# ----------------------------------------------------------------------------
# Loot, recipes, tags
# ----------------------------------------------------------------------------

def entry(name, lo=1, hi=1, weight=1):
    e = {"type": "minecraft:item", "name": name if ":" in name else f"{MOD}:{name}", "weight": weight}
    if (lo, hi) != (1, 1):
        e["functions"] = [{"function": "minecraft:set_count", "count": {"type": "minecraft:uniform", "min": lo, "max": hi}}]
    return e


def loot_tables():
    write_json(os.path.join(DATA, "loot_table", "entities", "tribesman.json"), {
        "type": "minecraft:entity", "random_sequence": f"{MOD}:entities/tribesman",
        "pools": [
            {"rolls": 1, "bonus_rolls": 0, "entries": [entry("fern_fiber", 0, 2)]},
            {"rolls": 1, "bonus_rolls": 0, "entries": [entry("minecraft:bone", 0, 1)]},
            {"rolls": 1, "bonus_rolls": 0, "conditions": [{"condition": "minecraft:random_chance", "chance": 0.1}],
             "entries": [entry("venus_amber")]},
        ]})
    write_json(os.path.join(DATA, "loot_table", "chests", "tribal_hut.json"), {
        "type": "minecraft:chest", "random_sequence": f"{MOD}:chests/tribal_hut",
        "pools": [
            {"rolls": {"type": "minecraft:uniform", "min": 1, "max": 3}, "bonus_rolls": 0, "entries": [
                entry("fern_fiber", 2, 6, 10), entry("minecraft:bone", 1, 3, 8), entry("raptor_tooth", 1, 3, 6),
                entry("venus_amber", 1, 2, 4), entry("dino_hide", 1, 1, 4), entry("glowcap_tea", 1, 1, 3),
                entry("minecraft:flint", 1, 4, 5), entry("minecraft:stick", 2, 5, 5)]},
            {"rolls": 1, "bonus_rolls": 0, "conditions": [{"condition": "minecraft:random_chance", "chance": 0.08}],
             "entries": [entry("shaman_charm")]},
        ]})


def recipes():
    shapeless("fern_fiber_from_giant_fern", [f"{MOD}:venus_giant_fern"], "fern_fiber", 3)
    shapeless("string_from_fern_fiber", ["fern_fiber", "fern_fiber", "fern_fiber"], "minecraft:string")
    shapeless("leather_from_dino_hide", ["dino_hide"], "minecraft:leather", 2)
    shapeless("glowcap_tea", [f"{MOD}:venus_glowcap", f"{MOD}:venus_glowcap", "minecraft:bowl"], "glowcap_tea",
              category="misc")
    shaped("bone_spear", ["  T", " F ", "S  "], {"T": "raptor_tooth", "F": "fern_fiber", "S": "minecraft:stick"},
           "bone_spear", category="equipment")


def tags():
    import furniture
    furniture.add_to_tag("item/repairs_bone_spear", [f"{MOD}:raptor_tooth"], namespace=MOD)
    furniture.add_to_tag("item/spears", [f"{MOD}:bone_spear"])


# ----------------------------------------------------------------------------
# Lang
# ----------------------------------------------------------------------------

NAMES = [("Ugg", "Угг"), ("Grok", "Грок"), ("Mog", "Мог"), ("Thak", "Тхак"), ("Zug", "Зуг"), ("Oona", "Уна"),
         ("Krag", "Краг"), ("Boru", "Бору"), ("Narr", "Нарр"), ("Tok", "Ток"), ("Ayra", "Айра"), ("Gub", "Губ"),
         ("Vrrn", "Вррн"), ("Ekka", "Экка"), ("Dar", "Дар"), ("Hoom", "Хуум")]

LINES = {
    "say": ("<%s> %s", "<%s> %s"),
    "greet.0": ("Ugh! Sky-man bring shiny?", "Угх! Небесный человек принёс блестяшку?"),
    "greet.1": ("Hm. Sky-man smell funny. Trade?", "Хм. Небесный человек пахнет странно. Меняться?"),
    "greet.2": ("Tribe give good thing. Sky-man give good thing.", "Племя даёт хорошее. Небесный человек даёт хорошее."),
    "greet.3": ("Sky-man come in fire-bird! Tribe see!", "Небесный человек прилетел на огненной птице! Племя видело!"),
    "greet.4": ("No touch fire. Fire bite. Trade instead.", "Огонь не трогай. Огонь кусается. Лучше меняйся."),
    "greet.5": ("Clear ice-stone! Sky-man have clear ice-stone?", "Прозрачный лёд-камень! У небесного человека есть лёд-камень?"),
    "hunter.0": ("Hunter kill big lizard. You want tooth?", "Охотник убил большую ящерицу. Хочешь зуб?"),
    "hunter.1": ("Raptor fast. Spear faster. Ha!", "Раптор быстрый. Копьё быстрее. Ха!"),
    "gatherer.0": ("Gatherer pick fern. Fern soft. Good for rope.", "Собиратель рвёт папоротник. Мягкий. Хорош для верёвки."),
    "gatherer.1": ("Glow-mushroom tea make eyes see in dark.", "Чай из светогриба: глаза видят в темноте."),
    "shaman.0": ("Spirits say... sky-man come from star.", "Духи говорят... небесный человек пришёл со звезды."),
    "shaman.1": ("Mask hold spirit. Charm hold spirit. Amber hold sun.", "Маска хранит духа. Оберег хранит духа. Янтарь хранит солнце."),
    "chief.0": ("Chief speak! Sky-man trade fair, or tribe angry.", "Вождь говорит! Небесный человек меняется честно, или племя злится."),
    "chief.1": ("Chief want shiny metal. Chief give much amber.", "Вождь хочет блестящий металл. Вождь даст много янтаря."),
    "angry": ("Sky-man hurt tribe! Tribe hurt sky-man!", "Небесный человек обидел племя! Племя побьёт небесного человека!"),
    "refuse": ("Grr! Go away, bad sky-man!", "Ррр! Уходи, плохой небесный человек!"),
    "child": ("*giggles and hides behind a fern*", "*хихикает и прячется за папоротник*"),
    "thanks": ("Ugh! Good trade! Good!", "Угх! Хороший обмен! Хороший!"),
    "mask": ("Sky-man wear tribe face! Sky-man friend! Good price!", "Небесный человек носит лицо племени! Друг! Хорошая цена!"),
    "friend": ("Sky-man free tribe-brother from glass-head den! Friend price!",
               "Небесный человек спас брата из логова стеклоголовых! Цена для друга!"),
    "captive.0": ("Sky-man! Help! Bad white-coat man lock tribe in box!",
                  "Небесный человек! Помоги! Злой человек в белом халате запер племя в ящике!"),
    "captive.1": ("Ugh... no fire... no sky... want go home...", "Угх... нет огня... нет неба... хочу домой..."),
    "captive.2": ("White-coat man make tribe-brother big and angry. Next is me!",
                  "Человек в халате сделал брата огромным и злым. Следующий - я!"),
    "captive.3": ("Psst! Sky-man! Bars too strong for tribe hands...",
                  "Псст! Небесный человек! Прутья слишком крепкие для рук племени..."),
    "captive.4": ("Glass-head come with needle every night. Ugh. Hurts.",
                  "Стеклоголовый каждую ночь приходит с иглой. Угх. Больно."),
    "captive.5": ("Tribe hear iron-man walking. Clank, clank. Sky-man careful!",
                  "Племя слышит железного человека. Бряк, бряк. Небесный человек, осторожно!"),
    "captive.6": ("Sky-man open box? Tribe give amber! Much amber!",
                  "Небесный человек откроет ящик? Племя даст янтарь! Много янтаря!"),
    "captive.locked": ("Box shut tight! Sky-man find way to open!", "Ящик заперт! Небесный человек, найди, как открыть!"),
    "freed.0": ("Free! Sky-man good! Tribe remember!", "Свобода! Небесный человек хороший! Племя запомнит!"),
    "freed.1": ("Ugh! Sky-man strong friend! Take, take! Gift!", "Угх! Небесный человек - сильный друг! Бери, бери! Подарок!"),
}

ITEM_NAMES = {
    "venus_amber": ("Venusian Amber", "Венерианский янтарь"),
    "raptor_tooth": ("Raptor Tooth", "Зуб раптора"),
    "fern_fiber": ("Fern Fiber", "Волокно папоротника"),
    "dino_hide": ("Dinosaur Hide", "Шкура динозавра"),
    "glowcap_tea": ("Glowcap Tea", "Чай из светогриба"),
    "bone_spear": ("Bone Spear", "Костяное копьё"),
    "tribal_mask": ("Tribal Mask", "Племенная маска"),
    "shaman_charm": ("Shaman's Charm", "Оберег шамана"),
    "tribesman_spawn_egg": ("Tribesman Spawn Egg", "Яйцо призыва соплеменника"),
}

ENTITY_NAMES = {
    "": ("Venusian Tribesman", "Венерианский соплеменник"),
    ".hunter": ("Tribe Hunter", "Охотник племени"),
    ".gatherer": ("Tribe Gatherer", "Собиратель племени"),
    ".shaman": ("Tribe Shaman", "Шаман племени"),
    ".chief": ("Tribe Chief", "Вождь племени"),
    ".child": ("Tribe Child", "Детёныш племени"),
    ".title": ("%s, %s", "%s, %s"),
}

EN, RU = {}, {}
for _k, (_en, _ru) in ITEM_NAMES.items():
    EN[f"item.{MOD}.{_k}"], RU[f"item.{MOD}.{_k}"] = _en, _ru
for _k, (_en, _ru) in ENTITY_NAMES.items():
    EN[f"entity.{MOD}.tribesman{_k}"], RU[f"entity.{MOD}.tribesman{_k}"] = _en, _ru
for _k, (_en, _ru) in {
    "hominid_novus": ("Hominid Novus", "Гоминид Новус"),
    "hominus_sapiens": ("Hominus Sapiens", "Гоминус Сапиенс"),
    "blaster_bolt": ("Blaster Bolt", "Заряд бластера"),
}.items():
    EN[f"entity.{MOD}.{_k}"], RU[f"entity.{MOD}.{_k}"] = _en, _ru
for _k, (_en, _ru) in {
    "ray_blaster": ("Ray Blaster", "Лучевой бластер"),
    "control_collar": ("Control Collar", "Ошейник управления"),
    "brain_flask": ("Brain Flask", "Колба с мозгом"),
    "hominid_novus_spawn_egg": ("Hominid Novus Spawn Egg", "Яйцо призыва гоминида Новуса"),
    "hominus_sapiens_spawn_egg": ("Hominus Sapiens Spawn Egg", "Яйцо призыва гоминуса Сапиенса"),
}.items():
    EN[f"item.{MOD}.{_k}"], RU[f"item.{MOD}.{_k}"] = _en, _ru
EN[f"death.attack.{MOD}.blaster"] = "%1$s was zapped by %2$s"
RU[f"death.attack.{MOD}.blaster"] = "%1$s испепелён лучом: %2$s"
EN[f"death.attack.{MOD}.blaster.item"] = "%1$s was zapped by %2$s using %3$s"
RU[f"death.attack.{MOD}.blaster.item"] = "%1$s испепелён лучом: %2$s, оружие: %3$s"
EN[f"item.{MOD}.ray_blaster.desc"] = "Dr. Oinstein's ray pistol. Recharges between shots; repair with redstone."
RU[f"item.{MOD}.ray_blaster.desc"] = "Лучевой пистолет доктора Ойнштайна. Перезаряжается между выстрелами; чинится редстоуном."
EN[f"subtitles.{MOD}.blaster_shot"] = "Blaster fires"
RU[f"subtitles.{MOD}.blaster_shot"] = "Выстрел бластера"
EN[f"entity.{MOD}.thrown_spear"], RU[f"entity.{MOD}.thrown_spear"] = "Thrown Spear", "Брошенное копьё"
EN.update(TB.EN)
RU.update(TB.RU)
EN.update(RI.EN)
RU.update(RI.RU)
for _i, (_en, _ru) in enumerate(NAMES):
    EN[f"tribe.{MOD}.name.{_i}"], RU[f"tribe.{MOD}.name.{_i}"] = _en, _ru
for _k, (_en, _ru) in LINES.items():
    EN[f"chat.{MOD}.tribe.{_k}"], RU[f"chat.{MOD}.tribe.{_k}"] = _en, _ru


# ----------------------------------------------------------------------------
# Entry point used by gen_resources.py
# ----------------------------------------------------------------------------

def mutant_assets():
    """Dr. Oinstein's mutants: entity textures (+ glow / lamp / glass layers), items, eggs, loot, damage type, tags."""
    for spec in MU.SPECS:
        D.pack(spec)
        _paint, layers = MU.PAINTERS[spec["name"]]
        for layer in layers:
            save(MU.build_texture(spec, layer), "entity", "tribe", spec["name"] + ("" if layer == "main" else "_" + layer))
    save(MU.bolt_texture(), "entity", "tribe", "blaster_bolt")
    write_json(os.path.join(ASSETS, "models", "item", "blaster_template.json"), MU.BLASTER_TEMPLATE)
    for name, fn in (("ray_blaster", MU.item_ray_blaster), ("control_collar", MU.item_control_collar),
                     ("brain_flask", MU.item_brain_flask)):
        save(fn(), "item", name)
        parent = f"{MOD}:item/blaster_template" if name == "ray_blaster" else "minecraft:item/generated"
        write_json(os.path.join(ASSETS, "models", "item", name + ".json"),
                   {"parent": parent, "textures": {"layer0": f"{MOD}:item/{name}"}})
        item_def(name, f"{MOD}:item/{name}")
    for name, shell, spots in (("hominid_novus", (86, 84, 64), (186, 192, 200)),
                               ("hominus_sapiens", (120, 126, 132), (232, 136, 160))):
        egg = name + "_spawn_egg"
        save(D.egg(shell, spots), "item", egg)
        write_json(os.path.join(ASSETS, "models", "item", egg + ".json"),
                   {"parent": "minecraft:item/generated", "textures": {"layer0": f"{MOD}:item/{egg}"}})
        item_def(egg, f"{MOD}:item/{egg}")

    def rare(item, unenchanted, base, per_level):
        return {"rolls": 1, "bonus_rolls": 0,
                "conditions": [{"condition": "minecraft:killed_by_player"},
                               {"condition": "minecraft:random_chance_with_enchanted_bonus",
                                "enchantment": "minecraft:looting", "unenchanted_chance": unenchanted,
                                "enchanted_chance": {"type": "minecraft:linear", "base": base,
                                                     "per_level_above_first": per_level}}],
                "entries": [entry(item)]}

    def common(item, lo, hi, smelt=False):
        functions = [{"function": "minecraft:set_count", "count": {"type": "minecraft:uniform", "min": lo, "max": hi}}]
        if smelt:
            functions.append({"function": "minecraft:furnace_smelt", "conditions": [{
                "condition": "minecraft:entity_properties", "entity": "this",
                "predicate": {"flags": {"is_on_fire": True}}}]})
        functions.append({"function": "minecraft:enchanted_count_increase", "enchantment": "minecraft:looting",
                          "count": {"type": "minecraft:uniform", "min": 0, "max": 1}})
        return {"rolls": 1, "bonus_rolls": 0,
                "entries": [{"type": "minecraft:item", "name": item, "functions": functions}]}

    # now and then a Sapiens carries a few spare energy cartridges for its blaster
    cartridges = rare("energy_cartridge", 0.18, 0.22, 0.04)
    cartridges["entries"][0]["functions"] = [
        {"function": "minecraft:set_count", "count": {"type": "minecraft:uniform", "min": 1, "max": 3}},
        {"function": "minecraft:enchanted_count_increase", "enchantment": "minecraft:looting",
         "count": {"type": "minecraft:uniform", "min": 0, "max": 1}}]
    write_json(os.path.join(DATA, "loot_table", "entities", "hominid_novus.json"), {
        "type": "minecraft:entity", "random_sequence": f"{MOD}:entities/hominid_novus",
        "pools": [common("minecraft:beef", 1, 3, smelt=True), common("minecraft:leather", 1, 2),
                  rare("control_collar", 0.07, 0.09, 0.03)]})
    write_json(os.path.join(DATA, "loot_table", "entities", "hominus_sapiens.json"), {
        "type": "minecraft:entity", "random_sequence": f"{MOD}:entities/hominus_sapiens",
        "pools": [common("minecraft:redstone", 0, 2), rare("ray_blaster", 0.08, 0.1, 0.03),
                  rare("brain_flask", 0.05, 0.07, 0.02), cartridges]})
    write_json(os.path.join(DATA, "damage_type", "blaster.json"),
               {"message_id": f"{MOD}.blaster", "exhaustion": 0.1, "scaling": "when_caused_by_living_non_player"})
    import furniture
    furniture.add_to_tag("damage_type/is_projectile", [f"{MOD}:blaster"])
    furniture.add_to_tag("entity_type/oinstein_forces", [f"{MOD}:hominid_novus", f"{MOD}:hominus_sapiens"],
                         namespace=MOD)


def generate():
    D.pack(SPEC)
    for role in ROLES:
        for v in range(VARIANTS):
            save(build_texture(role, v), "entity", "tribe", f"tribesman_{role}_{v}")
    mutant_assets()
    TB.boss_assets()
    RI.generate()
    write_java()

    for name, fn in ITEMS.items():
        img = fn()
        save(img, "item", name)
        parent = "minecraft:item/handheld" if name == "bone_spear" else "minecraft:item/generated"
        write_json(os.path.join(ASSETS, "models", "item", name + ".json"),
                   {"parent": parent, "textures": {"layer0": f"{MOD}:item/{name}"}})
        item_def(name, f"{MOD}:item/{name}")
    save(D.egg((134, 84, 50), (214, 168, 118)), "item", "tribesman_spawn_egg")
    write_json(os.path.join(ASSETS, "models", "item", "tribesman_spawn_egg.json"),
               {"parent": "minecraft:item/generated", "textures": {"layer0": f"{MOD}:item/tribesman_spawn_egg"}})
    item_def("tribesman_spawn_egg", f"{MOD}:item/tribesman_spawn_egg")

    save(mask_equipment_texture(), "entity", "equipment", "humanoid", "tribal_mask")
    write_json(os.path.join(ASSETS, "equipment", "tribal_mask.json"),
               {"layers": {"humanoid": [{"texture": f"{MOD}:tribal_mask"}]}})

    loot_tables()
    recipes()
    tags()
    write_camps()


if __name__ == "__main__":
    generate()
