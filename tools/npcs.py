"""The human crew of the Earth expedition: Dr. Cooper, the camp guards and the scientists.

Generates
  * the crew skins (textures/entity/npc/<role>_<variant>.png): 64x64, vanilla player-skin layout including the
    outer layer (hat, jacket, sleeves, pants), painted texel by texel from small per-face pixel grids and
    procedural fabric so they read well at Minecraft scale;
  * the shared gear sheet (textures/entity/npc/gear.png) for the 3D accessories that a skin cannot hold
    (Cooper's fedora brim and satchel, the guards' helmet visor, crest, ear pieces, radio pack, thigh holster,
    ray pistol and stun baton), plus the matching Java geometry npc/client/CrewGeometry.java;
  * the Space Credit, the crew spawn eggs, and all the crew's lines in English and Russian.

Model coordinates are Minecraft entity-model pixels: y points down, the feet are at y = 24, the face looks to -z,
the entity's right side is -x.
"""
import math
import os

from PIL import Image

import dinosaurs as D
from gen_resources import ASSETS, MOD, item_def, save, write_json

JAVA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "main", "java",
                        "com", "replecant", "retrocosmos", "npc", "client")

ROLES = ("cooper", "guard", "scientist", "decorator")
VARIANTS = {"cooper": 1, "guard": 4, "scientist": 4, "decorator": 1}


# ----------------------------------------------------------------------------
# Vanilla player skin layout (PlayerModel.createMesh, wide arms)
# ----------------------------------------------------------------------------

# name: (u, v, (w, h, d), bone, inflate, box origin)
SKIN_BOXES = {
    "head": (0, 0, (8, 8, 8), "head", 0.0, (-4, -8, -4)),
    "hat": (32, 0, (8, 8, 8), "head", 0.5, (-4, -8, -4)),
    "body": (16, 16, (8, 12, 4), "body", 0.0, (-4, 0, -2)),
    "jacket": (16, 32, (8, 12, 4), "body", 0.25, (-4, 0, -2)),
    "right_arm": (40, 16, (4, 12, 4), "right_arm", 0.0, (-3, -2, -2)),
    "right_sleeve": (40, 32, (4, 12, 4), "right_arm", 0.25, (-3, -2, -2)),
    "left_arm": (32, 48, (4, 12, 4), "left_arm", 0.0, (-1, -2, -2)),
    "left_sleeve": (48, 48, (4, 12, 4), "left_arm", 0.25, (-1, -2, -2)),
    "right_leg": (0, 16, (4, 12, 4), "right_leg", 0.0, (-2, 0, -2)),
    "right_pants": (0, 32, (4, 12, 4), "right_leg", 0.25, (-2, 0, -2)),
    "left_leg": (16, 48, (4, 12, 4), "left_leg", 0.0, (-2, 0, -2)),
    "left_pants": (0, 48, (4, 12, 4), "left_leg", 0.25, (-2, 0, -2)),
}
BONES = {  # bone: pivot
    "head": (0, 0, 0), "body": (0, 0, 0), "right_arm": (-5, 2, 0), "left_arm": (5, 2, 0),
    "right_leg": (-1.9, 12, 0), "left_leg": (1.9, 12, 0),
}
OVERLAY = {"head": "hat", "body": "jacket", "right_arm": "right_sleeve", "left_arm": "left_sleeve",
           "right_leg": "right_pants", "left_leg": "left_pants"}

# face names: front (-z), back (+z), right (-x, the entity's right), left (+x), top, bottom
FACE_OF = {"north": "front", "south": "back", "west": "right", "east": "left", "top": "top", "bottom": "bottom"}


def face_rect(part, face):
    """(x0, y0, w, h) of a face of a skin box, in texture pixels."""
    u, v, (w, h, d) = SKIN_BOXES[part][:3]
    return {
        "top": (u + d, v, w, d),
        "bottom": (u + d + w, v, w, d),
        "right": (u, v + d, d, h),
        "front": (u + d, v + d, w, h),
        "left": (u + d + w, v + d, d, h),
        "back": (u + 2 * d + w, v + d, w, h),
    }[face]


# Orientation of the side faces (from D.faces / ModelPart.Cube):
#   right face: column 0 is at the back, the last column at the front
#   left face:  column 0 is at the front
#   back face:  column 0 is at the entity's left (+x)
#   top face:   row 0 is at the back, the last row at the front


# ----------------------------------------------------------------------------
# Colour helpers
# ----------------------------------------------------------------------------

def clamp(c, a=255):
    return tuple(max(0, min(255, int(round(v)))) for v in c[:3]) + (a,)


def mul(c, f):
    return tuple(v * f for v in c[:3])


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def noise(*k):
    return D.hash3(*k) - 0.5


FACE_LIGHT = {"front": 1.0, "back": 0.9, "right": 0.94, "left": 0.94, "top": 1.08, "bottom": 0.72}


class Skin:
    """A 64x64 skin being painted. Colours are RGB tuples; None leaves a texel transparent."""

    def __init__(self, seed):
        self.img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        self.seed = seed

    def px(self, part, face, x, y, c, shade=True, grain=0.0):
        if c is None:
            return
        x0, y0, w, h = face_rect(part, face)
        if not (0 <= x < w and 0 <= y < h):
            return
        if len(c) == 4 and c[3] == 0:
            self.img.putpixel((x0 + x, y0 + y), (0, 0, 0, 0))
            return
        col = c[:3]
        if shade:
            col = mul(col, FACE_LIGHT[face])
        if grain:
            col = mul(col, 1.0 + grain * noise(x0 + x, y0 + y, self.seed))
        self.img.putpixel((x0 + x, y0 + y), clamp(col))

    def clear(self, part, face, x, y):
        x0, y0, w, h = face_rect(part, face)
        if 0 <= x < w and 0 <= y < h:
            self.img.putpixel((x0 + x, y0 + y), (0, 0, 0, 0))

    def fill(self, part, face, fn, shade=True, grain=0.0):
        """fn(x, y, w, h) -> colour or None."""
        x0, y0, w, h = face_rect(part, face)
        for y in range(h):
            for x in range(w):
                self.px(part, face, x, y, fn(x, y, w, h), shade, grain)

    def fill_all(self, part, fn, shade=True, grain=0.0, faces=("front", "back", "right", "left", "top", "bottom")):
        """fn(face, x, y, w, h) -> colour or None, for several faces."""
        for face in faces:
            self.fill(part, face, lambda x, y, w, h, f=face: fn(f, x, y, w, h), shade, grain)

    def grid(self, part, face, rows, pal, shade=True, grain=0.0):
        """Paints a pixel grid onto a face: each char a key of pal; '.' leaves the texel untouched, '_' clears it."""
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                if ch == ".":
                    continue
                if ch == "_":
                    self.clear(part, face, x, y)
                    continue
                self.px(part, face, x, y, pal[ch], shade, grain)


def mirror(rows):
    return [r[::-1] for r in rows]


# ----------------------------------------------------------------------------
# Palette
# ----------------------------------------------------------------------------

TONES = {  # base, shade, dark, lip
    "light": ((240, 202, 174), (220, 176, 148), (188, 140, 114), (204, 128, 116)),
    "rosy": ((236, 190, 164), (216, 166, 140), (182, 128, 104), (196, 114, 104)),
    "tan": ((224, 172, 130), (200, 148, 108), (164, 114, 80), (178, 104, 80)),
    "medium": ((190, 136, 96), (166, 114, 78), (132, 86, 56), (150, 84, 64)),
    "dark": ((128, 86, 60), (106, 68, 46), (80, 50, 34), (96, 54, 44)),
    "warm": ((238, 204, 164), (218, 180, 138), (186, 146, 106), (198, 122, 104)),
}
EYE_WHITE = (238, 238, 232)
IRIS = {"brown": (82, 52, 32), "blue": (58, 100, 160), "green": (70, 112, 74), "dark": (38, 28, 24),
        "gray": (96, 108, 120)}

KHAKI = ((192, 166, 118), (168, 142, 98), (130, 106, 70))
TROUSER = ((138, 118, 82), (114, 96, 64), (88, 72, 48))
LEATHER = ((122, 78, 44), (92, 56, 30), (66, 40, 22))
BOOT = ((104, 66, 38), (80, 50, 28), (54, 34, 20))
FEDORA = ((204, 172, 122), (176, 144, 98), (146, 116, 76))
BAND = ((80, 50, 32), (60, 36, 22))
CREAM = ((238, 230, 206), (212, 202, 176))
CHERRY = ((204, 40, 46), (154, 28, 34), (110, 18, 24))
TEAL = ((36, 156, 156), (24, 116, 120), (16, 82, 88))
ENAMEL = ((246, 246, 240), (218, 220, 216), (184, 188, 190))
CHROME = ((232, 238, 244), (176, 184, 194), (116, 124, 136))
TURQ = ((72, 204, 196), (46, 162, 158), (30, 118, 120))
LABCOAT = ((248, 248, 244), (224, 226, 224), (192, 196, 198))
SHOE = ((50, 44, 44), (32, 28, 28))
GOLD = ((236, 194, 84), (184, 138, 42))
GLASS_FRAME = {"wire": (196, 160, 82), "silver": (196, 200, 208), "horn": (70, 34, 30), "black": (26, 24, 26)}


def fabric(cols, face, x, y, w, h, seed=0):
    """Plain cloth: base colour with a faint weave and darker edges at the bottom of a face."""
    base, shade, dark = cols[0], cols[1], cols[2] if len(cols) > 2 else mul(cols[1], 0.8)
    c = base
    if face in ("right", "left", "back") and (x == 0 or x == w - 1) and face != "back":
        c = mix(base, shade, 0.35)
    return c


# ----------------------------------------------------------------------------
# Heads
# ----------------------------------------------------------------------------

def head_base(sk, tone, hair, hair_rows_front=2, hairline_sides=4, neck=True):
    """Skin-coloured head with hair on top/back; faces are painted afterwards."""
    s, sh, dk, _ = TONES[tone]
    hb, hs = hair[0], hair[1]

    def fn(face, x, y, w, h):
        if face == "top":
            return hb if noise(x, y, 7) < 0.35 else hs
        if face == "bottom":
            return sh
        if face == "back":
            if y < 7 or not neck:
                return hb if noise(x, y, 8) < 0.3 else hs
            return sh
        if face == "front":
            return hb if y < hair_rows_front else s
        # sides: hair at the back and on top, skin toward the face
        front_col = 7 if face == "right" else 0
        dist = abs(x - front_col)  # 0 at the front edge
        if y < 2:
            return hb
        if y < hairline_sides + 2 and dist >= 2:
            return hb if noise(x, y, 9) < 0.3 else hs
        if y >= 6 and dist >= 5:
            return hb if y == 6 else sh
        return s
    sk.fill_all("head", fn, grain=0.03)


def face_grid(sk, rows, pal):
    sk.grid("head", "front", rows, pal)


def ear(sk, tone):
    s, sh, dk, _ = TONES[tone]
    for face, cols in (("right", (3, 4)), ("left", (3, 4))):
        for y in (4, 5):
            for x in cols:
                sk.px("head", face, x, y, sh if (x, y) != (cols[0] if face == "left" else cols[1], 4) else dk)


def glasses(sk, style, row=4, color=None):
    """Spectacles painted on the face (frames on the base layer read cleaner than floating ones at 8x8).

    wire:  thin round frames - rims beside and under the eyes, the brows stay visible above
    horn / black: 1950s browline frames - a heavy bar over the eyes, outer rims and the bridge
    """
    f = color or GLASS_FRAME[style]
    if style == "wire":
        for x in (0, 3, 4, 7):
            sk.px("head", "front", x, row, f)
        for x in (1, 2, 5, 6):
            sk.px("head", "front", x, row + 1, mix(f, (0, 0, 0), 0.15))
    else:
        for x in (0, 1, 2, 5, 6, 7):
            sk.px("head", "front", x, row - 1, f)
        for x in (0, 3, 4, 7):
            sk.px("head", "front", x, row, f)
    arm = row if style == "wire" else row - 1
    for x in range(5, 8):
        sk.px("head", "right", x, arm, mul(f, 0.9))
    for x in range(0, 3):
        sk.px("head", "left", x, arm, mul(f, 0.9))
    # a glint on the lenses
    sk.px("head", "front", 1, row, mix(EYE_WHITE, (190, 225, 255), 0.6))
    sk.px("head", "front", 6, row, mix(EYE_WHITE, (190, 225, 255), 0.6))


# ----------------------------------------------------------------------------
# Bodies and limbs (procedural cloth + details)
# ----------------------------------------------------------------------------

def limb(sk, part, bands, outer_detail=None, grain=0.04):
    """bands: list of (rows_end_exclusive, colours) top to bottom; colours = (base, shade[, dark])."""
    def colour_at(y):
        for end, cols in bands:
            if y < end:
                return cols
        return bands[-1][1]

    def fn(face, x, y, w, h):
        if face == "top":
            return colour_at(0)[0]
        if face == "bottom":
            return colour_at(11)[1]
        cols = colour_at(y)
        c = cols[0]
        # the band edges get a seam
        for end, _ in bands:
            if y == end - 1 and end < 12:
                c = mix(cols[0], cols[1], 0.55)
        return c
    sk.fill_all(part, fn, grain=grain)


def outer_face(part):
    return "right" if part.startswith("right") else "left"


def inner_face(part):
    return "left" if part.startswith("right") else "right"


def hands(sk, part, tone, rows=(10, 11), overlay=False):
    s, sh, dk, _ = TONES[tone]
    for face in ("front", "back", "right", "left"):
        for y in rows:
            for x in range(4):
                c = s if y == rows[0] else sh
                if face == "back":
                    c = sh
                sk.px(part, face, x, y, c, grain=0.03)
    for x in range(4):
        for y in range(4):
            sk.px(part, "bottom", x, y, sh)


# ----------------------------------------------------------------------------
# Dr. Harold Cooper - 1950s field archaeologist
# ----------------------------------------------------------------------------

def cooper():
    sk = Skin(11)
    tone = "tan"
    s, sh, dk, lip = TONES[tone]
    hair = ((104, 74, 50), (86, 60, 40))
    gray = (156, 146, 136)
    stache = (92, 62, 40)
    stache_d = (70, 46, 30)
    head_base(sk, tone, hair, hair_rows_front=2)
    pal = {"h": hair[0], "H": gray, "S": s, "s": sh, "d": dk, "w": EYE_WHITE, "e": IRIS["blue"],
           "b": (120, 88, 62), "m": stache, "M": stache_d, "l": lip, "c": mix(s, sh, 0.5)}
    face_grid(sk, [
        "hhhhhhhh",
        "hhhhhhhh",
        "HSSSSSSH",
        "SbbSSbbS",
        "SwesSewS",
        "SSSddSSS",
        "SSmMMmSS",
        "sSSllSSs",
    ], pal)
    side = [
        "hhhhhhhh",
        "hhhhhhhh",
        "hhhhhhHS",
        "hhhhhHHS",
        "hhhsdHSS",
        "hhhssSSS",
        "hhSSSSSS",
        "sssSSSSs",
    ]
    sk.grid("head", "right", side, pal)
    sk.grid("head", "left", mirror(side), pal)
    # fedora crown on the hat layer: crown rows 0-1, band row 2, the brim is a gear part
    F, Fs, Fd = FEDORA
    for face in ("front", "back", "right", "left"):
        for x in range(8):
            sk.px("hat", face, x, 0, F if face != "back" else Fs, grain=0.04)
            sk.px("hat", face, x, 1, Fs if (face == "front" and x in (3, 4)) else F, grain=0.04)
            sk.px("hat", face, x, 2, BAND[0] if x % 7 else BAND[1])
    # pinch at the front of the crown
    sk.px("hat", "front", 2, 0, Fd)
    sk.px("hat", "front", 5, 0, Fd)

    def crown_top(x, y, w, h):
        c = F
        if x in (3, 4) and 1 <= y <= 6:
            c = Fd if y > 1 else Fs  # the centre crease, front to back
        if (x in (2, 5)) and y >= 5:
            c = Fs  # the two front pinches
        if x in (0, 7) or y in (0, 7):
            c = mix(c, Fs, 0.5)
        return c
    sk.fill("hat", "top", crown_top, grain=0.04)
    glasses(sk, "wire")

    # --- khaki safari jacket over a cream shirt, red neckerchief, satchel strap ---
    K, Ks, Kd = KHAKI

    def jacket(face, x, y, w, h):
        c = K
        if face == "front":
            if y >= 8 and y <= 8:
                c = Ks  # belt of the jacket
            if x == 4 and 2 <= y <= 11 and y != 8:
                c = Ks  # button placket
            if (x in (1, 2) or x in (5, 6)) and y in (3,):
                c = Kd  # chest pocket flaps
            if (x in (1, 2) or x in (5, 6)) and y in (4, 5):
                c = mix(K, Ks, 0.25)
            if (x in (0, 1) or x in (6, 7)) and y in (9,):
                c = Kd  # lower pocket flaps
            if y == 11:
                c = Ks
        elif face == "back":
            if y == 8:
                c = Ks
            if x in (3, 4) and y > 8:
                c = mix(K, Ks, 0.5)  # back vent
            if y == 11:
                c = Ks
        elif face in ("right", "left"):
            if y == 8:
                c = Ks
            if y == 11:
                c = Ks
        elif face == "top":
            c = K
        elif face == "bottom":
            c = TROUSER[1]
        return c
    sk.fill_all("body", jacket, grain=0.05)
    # collar: open shirt and the knotted neckerchief
    for x, y, c in ((3, 0, CHERRY[0]), (4, 0, CHERRY[0]), (3, 1, CHERRY[1]), (4, 1, CHERRY[0]), (4, 2, CHERRY[1]),
                    (2, 0, CREAM[0]), (5, 0, CREAM[0]), (2, 1, Ks), (5, 1, Ks), (3, 2, CREAM[1])):
        sk.px("body", "front", x, y, c)
    for x in range(8):
        sk.px("body", "top", x, 0, CHERRY[1] if 2 < x < 5 else K)
    # brass buttons
    for y in (3, 6, 10):
        sk.px("body", "front", 4, y, GOLD[1])
    # satchel strap: right shoulder across the chest to the left hip, and back up across the back
    L, Ls, Ld = LEATHER
    for y in range(0, 9):
        x = min(7, y)
        sk.px("body", "front", x, y, L if y % 3 else Ls)
    for y in range(0, 9):  # back face column 0 is the entity's left side: the strap climbs back to the right shoulder
        sk.px("body", "back", min(7, y), y, Ls)
    sk.px("body", "top", 0, 1, L)
    sk.px("body", "top", 0, 2, L)
    sk.px("body", "top", 0, 3, L)
    sk.px("body", "top", 0, 0, L)
    # jacket layer: collar points, pocket flaps and the cuffed hem stand out
    for x, y in ((1, 0), (6, 0), (2, 1), (5, 1)):
        sk.px("jacket", "front", x, y, Ks if y else K)
    for x in (1, 2, 5, 6):
        sk.px("jacket", "front", x, 3, Ks)
    for x in (0, 1, 6, 7):
        sk.px("jacket", "front", x, 9, Ks)
    for face in ("front", "back", "right", "left"):
        w = 8 if face in ("front", "back") else 4
        for x in range(w):
            sk.px("jacket", face, x, 8, Kd if face == "front" and x in (3, 4) else Ks)
    sk.px("jacket", "front", 3, 8, GOLD[1])  # belt buckle
    for y in range(0, 8):
        sk.px("jacket", "front", y, y, L if y % 3 else Ls)

    # arms: rolled-up sleeves, forearms, a wristwatch on the left wrist
    for part in ("right_arm", "left_arm"):
        limb(sk, part, [(7, KHAKI), (8, (mix(K, CREAM[0], 0.35), K)), (12, (s, sh))])
        hands(sk, part, tone, rows=(10, 11))
        for face in ("front", "back", "right", "left"):
            for x in range(4):
                sk.px(part, face, x, 8, s)
                sk.px(part, face, x, 9, s if face != "back" else sh)
        # forearm hair hint
        sk.px(part, "front", 1, 8, sh)
    for face in ("front", "left", "back", "right"):
        for x in range(4):
            sk.px("left_arm", face, x, 9, CHROME[1] if face != "left" else CHROME[0])
    sk.px("left_arm", "left", 1, 9, GOLD[0])
    for part in ("right_sleeve", "left_sleeve"):
        for face in ("front", "back", "right", "left"):
            for x in range(4):
                sk.px(part, face, x, 7, mix(K, CREAM[0], 0.35))
                sk.px(part, face, x, 6, Ks if x % 2 else K)
    # shoulder epaulettes
    for part in ("right_arm", "left_arm"):
        for x in range(4):
            sk.px(part, "top", x, 1, Ks)
            sk.px(part, "top", x, 2, Ks)

    # legs: field trousers and tall laced boots
    T, Ts, Td = TROUSER
    B, Bs, Bd = BOOT
    for part in ("right_leg", "left_leg"):
        limb(sk, part, [(7, TROUSER), (12, BOOT)])
        for face in ("front", "back", "right", "left"):
            for x in range(4):
                sk.px(part, face, x, 11, Bd)
                sk.px(part, face, x, 7, Bs)
        sk.px(part, "front", 1, 8, Bd)
        sk.px(part, "front", 2, 9, Bd)
        sk.px(part, "front", 1, 10, Bd)
        for x in range(4):
            for y in range(4):
                sk.px(part, "bottom", x, y, Bd)
        sk.px(part, outer_face(part), 1, 2, Ts)  # cargo pocket
        sk.px(part, outer_face(part), 2, 2, Ts)
        sk.px(part, outer_face(part), 1, 3, Ts)
        sk.px(part, outer_face(part), 2, 3, Ts)
    for part in ("right_pants", "left_pants"):
        for face in ("front", "back", "right", "left"):
            for x in range(4):
                sk.px(part, face, x, 7, Bs)  # boot tops
        sk.px(part, outer_face(part.replace("pants", "leg")), 1, 2, Td)
        sk.px(part, outer_face(part.replace("pants", "leg")), 2, 2, Td)
    return sk.img


# ----------------------------------------------------------------------------
# Expedition guards - jumpsuits, chrome belt, white space helmet with a star
# ----------------------------------------------------------------------------

GUARD_LOOKS = [  # suit, tone, iris, extras
    (CHERRY, "light", "blue", ()),
    (TEAL, "dark", "dark", ()),
    (CHERRY, "medium", "brown", ("mustache",)),
    (TEAL, "rosy", "green", ("freckles",)),
]

STAR5 = [
    "..x..",
    ".xxx.",
    "xxxxx",
    ".xxx.",
    ".x.x.",
]


def guard(v):
    suit, tone, iris, extras = GUARD_LOOKS[v]
    sk = Skin(20 + v)
    s, sh, dk, lip = TONES[tone]
    hair = ((70, 52, 40), (54, 40, 30)) if tone != "dark" else ((30, 24, 22), (20, 16, 16))
    if "freckles" in extras:
        hair = ((176, 92, 48), (140, 70, 36))
    head_base(sk, tone, hair, hair_rows_front=2)
    pal = {"h": hair[0], "S": s, "s": sh, "d": dk, "w": EYE_WHITE, "e": IRIS[iris], "b": mul(hair[1], 0.9),
           "l": mix(lip, sh, 0.4), "m": mul(hair[1], 0.9), "f": mix(s, (170, 96, 60), 0.35)}
    face = [
        "hhhhhhhh",
        "hhhhhhhh",
        "SSSSSSSS",
        "SbbSSbbS",
        "SwesSewS",
        "SSSddSSS",
        "SSsllsSS",
        "sSSSSSSs",
    ]
    if "mustache" in extras:
        face[6] = "SmmmmmmS"
    if "freckles" in extras:
        face[5] = "SfSddSfS"
    face_grid(sk, face, pal)
    ear(sk, tone)
    # the helmet (hat layer): white enamel shell, red/teal stripe, a star on both sides, cheek guards
    E, Es, Ed = ENAMEL
    S0, S1, S2 = suit

    def helmet(face, x, y, w, h):
        if face == "top":
            c = E
            if x in (3, 4):
                c = S0  # stripe over the crown
            if x in (0, 7) or y in (0, 7):
                c = Es
            return c
        if face == "bottom":
            return None
        if face == "front":
            if y <= 1:
                return S0 if x in (3, 4) else E
            if y == 2:
                return Es
            if x in (0, 7) and y <= 4:
                return Es  # cheek guards
            if (x in (1, 6)) and y == 6 and False:
                return Ed
            return (0, 0, 0, 0)
        if face == "back":
            if y == 7:
                return Ed
            if x in (3, 4) and y <= 5:
                return S0
            return E if y < 6 else Es
        # sides
        if y == 7:
            return None
        if y == 6:
            return Es
        front_col = 7 if face == "right" else 0
        if x == front_col and y >= 3:
            return Es
        return E
    sk.fill_all("hat", helmet, grain=0.02)
    for face in ("right", "left"):
        for yy, row in enumerate(STAR5):
            for xx, ch in enumerate(row):
                if ch == "x":
                    sk.px("hat", face, 1 + xx if face == "right" else 2 + xx, 1 + yy, S0)

    # body: jumpsuit, high white collar, zip, star badge, chrome belt
    def suit_fn(face, x, y, w, h):
        c = S0
        if face == "front":
            if x == 3 and 1 <= y <= 6:
                c = CHROME[1]  # zip
            if y in (7, 8):
                c = CHROME[0] if y == 7 else CHROME[1]
        elif face in ("back", "right", "left"):
            if y in (7, 8):
                c = CHROME[0] if y == 7 else CHROME[2]
            if face == "back" and x in (3, 4) and y < 7:
                c = mix(S0, S1, 0.4)
        elif face == "top":
            c = S0
        elif face == "bottom":
            c = S1
        if face != "top" and y == 11:
            c = S1
        return c
    sk.fill_all("body", suit_fn, grain=0.035)
    for x in range(1, 7):
        sk.px("body", "front", x, 0, E if x not in (3, 4) else Es)
    for x in range(8):
        sk.px("body", "top", x, 0, E if 0 < x < 7 else S0)
        sk.px("body", "top", x, 3, E if 0 < x < 7 else S0)
    for (x, y) in ((5, 2), (4, 3), (5, 3), (6, 3), (4, 4), (6, 4)):
        sk.px("body", "front", x, y, GOLD[0] if (x, y) != (5, 3) else GOLD[1])
    for x in (3, 4):  # buckle
        sk.px("body", "front", x, 7, (255, 255, 255))
        sk.px("body", "front", x, 8, CHROME[0])
    sk.px("body", "front", 4, 8, CHERRY[0] if suit is TEAL else (255, 214, 90))
    # belt stands out on the jacket layer
    for face in ("front", "back", "right", "left"):
        w = 8 if face in ("front", "back") else 4
        for x in range(w):
            sk.px("jacket", face, x, 7, CHROME[0] if face != "back" else CHROME[1])
            sk.px("jacket", face, x, 8, CHROME[1] if face != "back" else CHROME[2])
    sk.px("jacket", "front", 3, 7, (255, 255, 255))
    sk.px("jacket", "front", 4, 7, (255, 255, 255))
    sk.px("jacket", "front", 3, 8, CHROME[0])
    sk.px("jacket", "front", 4, 8, CHERRY[0] if suit is TEAL else (255, 214, 90))
    for x in range(1, 7):
        sk.px("jacket", "front", x, 0, E)  # collar

    # arms: suit sleeves, white piping at the shoulder, mission patch, white gauntlets
    for part in ("right_arm", "left_arm"):
        limb(sk, part, [(9, suit), (10, ENAMEL), (12, ((52, 50, 56), (36, 34, 40)))])
        for face in ("front", "back", "right", "left"):
            for x in range(4):
                sk.px(part, face, x, 0, E)
        o = outer_face(part)
        for (x, y, c) in ((1, 2, TEAL[0] if suit is CHERRY else CHERRY[0]), (2, 2, TEAL[0] if suit is CHERRY else CHERRY[0]),
                          (1, 3, E), (2, 3, TEAL[0] if suit is CHERRY else CHERRY[0]),
                          (0, 3, TEAL[1] if suit is CHERRY else CHERRY[1]), (3, 3, TEAL[1] if suit is CHERRY else CHERRY[1]),
                          (1, 4, TEAL[1] if suit is CHERRY else CHERRY[1]), (2, 4, TEAL[1] if suit is CHERRY else CHERRY[1])):
            sk.px(part, o, x, y, c)
        sk.px(part, o, 1, 3, (255, 255, 255))
        for x in range(4):
            for y in range(4):
                sk.px(part, "bottom", x, y, (36, 34, 40))
    for part in ("right_sleeve", "left_sleeve"):
        for face in ("front", "back", "right", "left"):
            for x in range(4):
                sk.px(part, face, x, 9, E)  # gauntlet cuffs
                sk.px(part, face, x, 0, E)
    # legs: suit with white side piping, white moon boots with a coloured band
    for part in ("right_leg", "left_leg"):
        limb(sk, part, [(8, suit), (12, ENAMEL)])
        o = outer_face(part)
        for y in range(0, 8):
            sk.px(part, o, 1, y, mix(E, S0, 0.15))
        for face in ("front", "back", "right", "left"):
            for x in range(4):
                sk.px(part, face, x, 9, S0)
                sk.px(part, face, x, 11, Ed)
        for x in range(4):
            for y in range(4):
                sk.px(part, "bottom", x, y, (60, 60, 64))
    for part in ("right_pants", "left_pants"):
        for face in ("front", "back", "right", "left"):
            for x in range(4):
                sk.px(part, face, x, 8, E)  # boot tops
    return sk.img


# ----------------------------------------------------------------------------
# Scientists - white lab coat over the turquoise expedition jumpsuit
# ----------------------------------------------------------------------------

def scientist(v):
    sk = Skin(40 + v)
    look = [
        # Dr. Ellen Hayes: auburn 1950s curls, cat-eye glasses, red lipstick
        dict(tone="light", hair=((170, 74, 38), (132, 52, 26), (204, 112, 64)), iris="green", glasses="horn",
             style="curls", lips=True),
        # Prof. Milo Vance: bald crown, white fringe, round spectacles, white mustache
        dict(tone="rosy", hair=((228, 226, 220), (192, 190, 186), (250, 250, 248)), iris="gray", glasses="wire", frame=GLASS_FRAME["silver"],
             style="bald", stache=True),
        # Dr. Ada Okafor: dark skin, black hair in a neat bun, lab goggles pushed up on her forehead
        dict(tone="dark", hair=((36, 30, 30), (22, 18, 18), (66, 56, 56)), iris="dark", glasses=None,
             style="bun", goggles=True, lips=True),
        # Dr. Hiro Tanaka: neat black side part, thick black frames
        dict(tone="warm", hair=((32, 28, 30), (18, 16, 18), (64, 60, 66)), iris="dark", glasses="wire", frame=GLASS_FRAME["black"],
             style="part"),
    ][v]
    tone = look["tone"]
    s, sh, dk, lip = TONES[tone]
    hb, hs, hl = look["hair"]
    style = look["style"]
    if style == "bald":
        head_base(sk, tone, (hb, hs), hair_rows_front=0, hairline_sides=3)
        sk.fill("head", "top", lambda x, y, w, h: s if not (x, y) in ((5, 2), (6, 3)) else mix(s, (255, 255, 255), 0.35))
        for face in ("right", "left", "back"):
            for x in range(8):
                sk.px("head", face, x, 0, s if face == "back" else s)
                sk.px("head", face, x, 1, s if face == "back" else (s if (x > 2 if face == "left" else x < 5) else s))
    else:
        head_base(sk, tone, (hb, hs), hair_rows_front=2)
    pal = {"h": hb, "H": hl, "x": hs, "S": s, "s": sh, "d": dk, "w": EYE_WHITE, "e": IRIS[look["iris"]],
           "b": hs if style != "bald" else hl, "l": (196, 36, 52) if look.get("lips") and tone != "dark" else mix(lip, dk, 0.2),
           "m": hl, "k": (60, 40, 34)}
    face = {
        "curls": ["hhhhhhhh", "hHhhhhHh", "hSSSSSSh", "SbbSSbbS", "SwesSewS", "SSSddSSS", "SSSllSSS", "sSSSSSSs"],
        "bald": ["SSSSSSSS", "SSSSSSSS", "hSSSSSSh", "SbbSSbbS", "SwesSewS", "SSSddSSS", "SSmmmmSS", "sSSSSSSs"],
        "bun": ["hhhhhhhh", "hhhhhhhh", "hSSSSSSh", "SbbSSbbS", "SwesSewS", "SSSddSSS", "SSSllSSS", "sSSSSSSs"],
        "part": ["hhhhhhhh", "hhhhhhxS", "hhSSSSSS", "SbbSSbbS", "SwesSewS", "SSSddSSS", "SSSllSSS", "sSSSSSSs"],
    }[style]
    if look.get("lips") and tone == "light":
        pal["l"] = (196, 36, 52)
    face_grid(sk, face, pal)
    ear(sk, tone)
    # hair volume on the hat layer
    if style == "curls":
        def curls(face, x, y, w, h):
            if face == "top":
                return hb if noise(x, y, 31) < 0.3 else hl
            if face == "bottom":
                return None
            if face == "front":
                if y == 0:
                    return hl if x % 3 == 0 else hb
                if y == 1 and x in (0, 1, 6, 7):
                    return hb
                if x in (0, 7) and y in (2, 5, 6):
                    return hb if y % 2 else hl
                return None
            if face == "back":
                if y <= 5:
                    return hb if (x + y) % 3 else hl
                if y == 6:
                    return hs if x % 2 else hb
                return None
            front_col = 7 if face == "right" else 0
            if x == front_col and y >= 1:
                return None
            if y <= 5:
                return hb if (x + y) % 3 else hl
            if y == 6:
                return hs if x % 2 else None
            return None
        sk.fill_all("hat", curls, grain=0.05)
    elif style == "bald":
        for face in ("right", "left"):
            front_col = 7 if face == "right" else 0
            for y in (2, 3, 4, 5):
                for x in range(8):
                    if abs(x - front_col) >= 2 and not (y == 2 and abs(x - front_col) < 4):
                        sk.px("hat", face, x, y, hl if (x + y) % 3 else hb)
        for x in range(8):
            for y in (3, 4, 5):
                sk.px("hat", "back", x, y, hl if (x + y) % 3 else hb)
    elif style == "bun":
        # hair swept up into a bun at the back of the crown
        sk.fill("hat", "top", lambda x, y, w, h: hb if (x * 3 + y) % 5 else hl, grain=0.05)
        for face in ("right", "left", "back", "front"):
            for x in range(8):
                sk.px("hat", face, x, 0, hb if x % 3 else hl)
        for x in range(2, 6):
            for y in range(1, 4):
                sk.px("hat", "back", x, y, hb if (x + y) % 3 else hl)
    elif style == "part":
        for x in range(1, 8):
            sk.px("hat", "front", x, 0, hb if x != 5 else hl)
        for x in range(0, 6):
            sk.px("hat", "front", x, 1, hb)
        for x in range(8):
            for y in range(0, 8):
                if y < 6 or x != 3:
                    sk.px("hat", "top", x, y, hb if x != 5 else hs)
    if look["glasses"]:
        glasses(sk, look["glasses"], color=look.get("frame"))
    if look.get("goggles"):
        # brass-rimmed goggles pushed up on the forehead, strap around the head
        strap = (70, 54, 40)
        for face in ("right", "left", "back"):
            for x in range(8):
                sk.px("hat", face, x, 2, strap)
        for x, c in ((0, strap), (1, GOLD[1]), (2, TURQ[0]), (3, GOLD[1]), (4, GOLD[1]), (5, TURQ[0]), (6, GOLD[1]), (7, strap)):
            sk.px("hat", "front", x, 2, c)
        sk.px("hat", "front", 2, 1, GOLD[1])
        sk.px("hat", "front", 5, 1, GOLD[1])
    if style == "bun" or style == "curls":
        sk.px("head", "right", 4, 6, GOLD[0])  # earrings
        sk.px("head", "left", 3, 6, GOLD[0])

    # --- the body: turquoise jumpsuit underneath, the coat over it ---
    C, Cs, Cd = LABCOAT
    T0, T1, T2 = TURQ

    def body_fn(face, x, y, w, h):
        if face == "front":
            if x in (3, 4):
                if y == 0:
                    return C
                return T0 if x == 4 or y > 1 else T1
            return C
        if face == "back":
            if x in (3, 4) and y >= 8:
                return Cs  # back vent
            if y == 7:
                return Cs  # half belt
            return C
        if face == "bottom":
            return T1
        return C
    sk.fill_all("body", body_fn, grain=0.03)
    sk.px("body", "front", 3, 1, Cs)
    sk.px("body", "front", 4, 1, Cs)

    def coat(face, x, y, w, h):
        if face == "front":
            if x in (3, 4):
                return (0, 0, 0, 0)
            c = C
            if x in (2, 5) and y <= 3:
                c = Cs  # lapels
            if y == 11:
                c = Cs
            return c
        if face == "back":
            if x in (3, 4) and y >= 8:
                return Cs
            if y == 7:
                return Cs
            return C if y < 11 else Cs
        if face in ("right", "left"):
            return C if y < 11 else Cs
        if face == "top":
            return None
        return None
    sk.fill_all("jacket", coat, grain=0.03)
    # breast pocket with a pen, lower pockets, an ID badge
    for x in (5, 6):
        sk.px("jacket", "front", x, 4, Cs)
        sk.px("jacket", "front", x, 6, Cd)
    sk.px("jacket", "front", 6, 3, CHERRY[0])  # pen cap
    sk.px("jacket", "front", 6, 4, CHROME[0])  # pen clip
    sk.px("jacket", "front", 5, 3, (40, 60, 120) if v % 2 else C)  # a second pen, for some
    for x in (0, 1, 6, 7):
        sk.px("jacket", "front", x, 8, Cs)
        sk.px("jacket", "front", x, 10, Cd)
    sk.px("jacket", "front", 1, 4, TURQ[1])
    sk.px("jacket", "front", 1, 5, (255, 255, 255))

    # arms: coat sleeves, jumpsuit cuff, hands
    for part in ("right_arm", "left_arm"):
        limb(sk, part, [(9, LABCOAT), (10, TURQ), (12, (s, sh))])
        hands(sk, part, tone, rows=(10, 11))
    for part in ("right_sleeve", "left_sleeve"):
        def sleeve(face, x, y, w, h):
            if face in ("top", "bottom"):
                return C if face == "top" else None
            if y < 9:
                return C if y < 8 else Cs
            return None
        sk.fill_all(part, sleeve, grain=0.03)
    # legs: jumpsuit trousers and black shoes; the coat skirt hangs over the thighs on the pants layer
    for part in ("right_leg", "left_leg"):
        limb(sk, part, [(10, TURQ), (12, SHOE)])
        for x in range(4):
            for y in range(4):
                sk.px(part, "bottom", x, y, SHOE[1])
            sk.px(part, "front", x, 10, SHOE[0] if x else mix(SHOE[0], (255, 255, 255), 0.25))
        sk.px(part, "front", 1, 4, T1)  # knee crease
        sk.px(part, "front", 2, 4, T1)
    for part in ("right_pants", "left_pants"):
        inner_col = 3 if part == "right_pants" else 0  # the coat opens down the middle

        def skirt(face, x, y, w, h, inner_col=inner_col, part=part):
            if face in ("top", "bottom"):
                return None
            if y > 4:
                return None
            if face == "front" and x == inner_col:
                return None
            if face == inner_face(part) and face != "back":
                return None
            return C if y < 4 else Cs
        sk.fill_all(part, skirt, grain=0.03)
    return sk.img


# ----------------------------------------------------------------------------
# Betty Palmer - the Atomic Home Showroom's saleswoman
# ----------------------------------------------------------------------------

DRESS = ((246, 178, 198), (222, 148, 172), (186, 112, 138))
DOT = (253, 247, 249)
APRON = ((252, 252, 248), (228, 228, 224), (200, 202, 204))
BLONDE = ((238, 212, 146), (210, 180, 112), (252, 238, 190))
PEARL = ((250, 246, 236), (214, 206, 196))
CATEYE = (190, 40, 78)


def dotted(x, y, seed=0):
    """Polka dots: a white dot every few texels in a staggered grid."""
    return (x + 2 * (y // 2) + seed) % 4 == 0 and y % 2 == 0


def decorator():
    sk = Skin(60)
    tone = "light"
    s, sh, dk, lip = TONES[tone]
    hb, hs, hl = BLONDE
    head_base(sk, tone, (hb, hs), hair_rows_front=2)
    pal = {"h": hb, "H": hl, "S": s, "s": sh, "d": dk, "w": EYE_WHITE, "e": IRIS["blue"], "b": hs,
           "l": (204, 30, 58), "k": mix(s, (240, 120, 130), 0.35)}
    face_grid(sk, [
        "hhhhhhhh",
        "hHhhhhHh",
        "hSSSSSSh",
        "SbbSSbbS",
        "SwesSewS",
        "SkSddSkS",
        "SSSllSSS",
        "sSSSSSSs",
    ], pal)
    ear(sk, tone)
    # cat-eye glasses: outer rims swept up into little wings, a fine bridge
    for x, y in ((0, 4), (7, 4), (0, 3), (1, 3), (6, 3), (7, 3), (3, 4), (4, 4)):
        sk.px("head", "front", x, y, CATEYE if y == 3 or x in (0, 7) else mix(CATEYE, s, 0.45))
    for x in (1, 2, 5, 6):
        sk.px("head", "front", x, 5, mix(CATEYE, s, 0.6))
    for x in range(5, 8):
        sk.px("head", "right", x, 3, mul(CATEYE, 0.9))
    for x in range(0, 3):
        sk.px("head", "left", x, 3, mul(CATEYE, 0.9))
    sk.px("head", "right", 6, 6, GOLD[0])  # pearl-drop earrings
    sk.px("head", "left", 1, 6, PEARL[0])
    sk.px("head", "right", 6, 6, PEARL[0])

    # the bouffant on the hat layer (the gear part piles it higher), flipped up at the ends
    def bouffant(face, x, y, w, h):
        n = noise(x, y, 61 + len(face))
        if face == "top":
            return hl if n > 0.25 else hb
        if face == "bottom":
            return None
        if face == "front":
            if y == 0:
                return hl if x % 3 == 0 else hb
            if y == 1 and x in (0, 1, 6, 7):
                return hb
            if x in (0, 7) and y in (5, 6):
                return hl if y == 6 else hb  # the flip
            return None
        if face == "back":
            if y <= 5:
                return hl if n > 0.25 else (hs if n < -0.35 else hb)
            if y == 6:
                return hl
            return None
        front_col = 7 if face == "right" else 0
        if x == front_col and 1 <= y <= 4:
            return None
        if y <= 5:
            return hl if n > 0.25 else (hs if n < -0.35 else hb)
        if y == 6:
            return hl if x % 2 else hb
        return None
    sk.fill_all("hat", bouffant, grain=0.04)

    # the dress: pastel pink with white polka dots, red belt, a crisp half apron
    D0, D1, D2 = DRESS
    A0, A1, A2 = APRON

    def dress(face, x, y, w, h):
        if face == "top":
            return D0
        if face == "bottom":
            return D1
        c = DOT if dotted(x, y, 1 if face in ("right", "left") else 0) else D0
        if y == 7:
            return CHERRY[0] if face != "back" else CHERRY[1]
        if face == "front" and y >= 8 and 1 <= x <= 6:
            return A1 if y == 11 and x % 2 else A0
        if face == "back" and y == 8 and x in (2, 3, 4, 5):
            return A0  # apron bow
        if face in ("right", "left") and y == 8:
            return A1  # apron strings
        return c
    sk.fill_all("body", dress, grain=0.03)
    # rounded neckline and the pearl necklace
    for x in (2, 3, 4, 5):
        sk.px("body", "front", x, 0, s)
    for x, y in ((3, 1), (4, 1)):
        sk.px("body", "front", x, y, sh)
    for x, y, c in ((2, 1, PEARL[0]), (5, 1, PEARL[0]), (3, 2, PEARL[1]), (4, 2, PEARL[0])):
        sk.px("body", "front", x, y, c)
    for x in range(8):
        sk.px("body", "top", x, 0, s if 2 <= x <= 5 else D0)
        sk.px("body", "top", x, 1, PEARL[0] if x in (2, 5) else (s if 2 < x < 5 else D0))
    sk.px("body", "front", 3, 7, GOLD[0])
    sk.px("body", "front", 4, 7, GOLD[0])
    # jacket layer: Peter Pan collar and the apron stand out
    for x in (1, 6):
        sk.px("jacket", "front", x, 0, A0)
    sk.px("jacket", "front", 2, 1, A1)
    sk.px("jacket", "front", 5, 1, A1)
    for y in range(8, 12):
        for x in range(1, 7):
            sk.px("jacket", "front", x, y, A1 if y == 11 and x % 2 else A0)
    for x in range(8):
        sk.px("jacket", "front", x, 7, CHERRY[0] if x not in (3, 4) else GOLD[0])
        sk.px("jacket", "back", x, 7, CHERRY[1])
    for face in ("right", "left"):
        for x in range(4):
            sk.px("jacket", face, x, 7, CHERRY[0])

    # arms: short puffed sleeves, bare arms, a gold bracelet, a pink manicure
    for part in ("right_arm", "left_arm"):
        limb(sk, part, [(3, DRESS), (4, APRON), (12, (s, sh))])
        hands(sk, part, tone, rows=(10, 11))
        for face in ("front", "back", "right", "left"):
            for x in range(4):
                if dotted(x, 1):
                    sk.px(part, face, x, 1, DOT)
    for x in range(4):
        for face in ("front", "back", "right", "left"):
            sk.px("left_arm", face, x, 9, GOLD[0] if (x + (face == "back")) % 2 else GOLD[1])
    sk.px("right_arm", "front", 1, 11, (226, 80, 110))
    sk.px("left_arm", "front", 2, 11, (226, 80, 110))
    for part in ("right_sleeve", "left_sleeve"):
        def puff(face, x, y, w, h):
            if face == "top":
                return D0
            if face == "bottom":
                return None
            if y < 3:
                return DOT if dotted(x, y, 2) else D0
            if y == 3:
                return A0
            return None
        sk.fill_all(part, puff, grain=0.03)

    # legs: the dress over the thighs, nylons, cherry-red pumps
    nylon = (mix(s, (210, 170, 140), 0.25), mix(sh, (190, 150, 120), 0.25))
    for part in ("right_leg", "left_leg"):
        limb(sk, part, [(5, DRESS), (11, nylon), (12, (CHERRY[0], CHERRY[1]))])
        for x in range(4):
            sk.px(part, "front", x, 10, CHERRY[0] if x in (1, 2) else nylon[0])
            for y in range(4):
                sk.px(part, "bottom", x, y, CHERRY[2])
        sk.px(part, "back", 1, 11, (40, 30, 30))  # heel
        sk.px(part, "back", 2, 11, (40, 30, 30))
        for y in range(6, 10):
            sk.px(part, "back", 1, y, nylon[1])  # stocking seam
    for part in ("right_pants", "left_pants"):
        def hem(face, x, y, w, h):
            if face in ("top", "bottom") or y > 5:
                return None
            if y == 5:
                return A1 if (x % 2 == 0) else None  # petticoat lace peeking out
            return DOT if dotted(x, y, 3) else D0
        sk.fill_all(part, hem, grain=0.03)
    return sk.img


# ----------------------------------------------------------------------------
# Gear: 3D accessories on a shared sheet
# ----------------------------------------------------------------------------

def G(name, bone, pos, size, mat, group, pivot=(0, 0, 0), rot=(0, 0, 0), grow=0.0):
    return {"name": name, "bone": bone, "pivot": pivot, "rot": rot,
            "box": {"pos": pos, "size": size, "mat": mat, "feat": {}, "grow": grow}, "group": group}


GEAR = [
    # Dr. Cooper
    G("fedora_brim", "head", (-6, -0.5, -6.5), (12, 1, 13), "brim", "cooper", pivot=(0, -5.0, 0), rot=(0.06, 0, 0),
      grow=(0, -0.3, 0)),
    G("satchel", "body", (4.1, 8, -2), (2, 4, 4), "satchel", "cooper"),
    # guards
    G("helmet_visor", "head", (-4.5, -7.6, -5.0), (9, 2, 1), "visor", "guard", grow=(0, 0, -0.2)),
    G("helmet_crest", "head", (-1, -9.2, -4.4), (2, 1, 9), "crest", "guard", grow=(-0.15, 0, 0)),
    G("radio_pack", "body", (-3, 1.5, 2.3), (6, 6, 2), "radio", "guard"),
    G("antenna", "body", (1.5, -6.5, 3.0), (1, 8, 1), "antenna", "guard", grow=(-0.3, 0, -0.3)),
    G("antenna_tip", "body", (1.5, -7.5, 3.0), (1, 1, 1), "tip", "guard", grow=-0.1),
    G("holster", "right_leg", (-3.4, 0.6, -1.5), (1, 4, 3), "holster", "guard"),
    G("holster_grip", "right_leg", (-3.4, -1.2, 0.2), (1, 2, 1), "grip", "holstered"),
    G("pistol_barrel", "right_arm", (-1.5, 8.5, -1.2), (1, 7, 1), "barrel", "pistol"),
    G("pistol_fins", "right_arm", (-2, 11.5, -1.7), (2, 1, 2), "fins", "pistol"),
    G("pistol_fins2", "right_arm", (-2, 13.0, -1.7), (2, 1, 2), "fins", "pistol", grow=-0.2),
    G("pistol_tip", "right_arm", (-1.5, 15.5, -1.2), (1, 1, 1), "emitter", "pistol", grow=0.1),
    G("baton", "right_arm", (-1.5, 9.0, -8.5), (1, 1, 7), "baton", "baton"),
    G("baton_tip", "right_arm", (-2, 8.5, -9.5), (2, 2, 1), "spark", "baton", grow=-0.2),
    # Betty Palmer
    G("bouffant", "head", (-4, -10.2, -4.3), (8, 2, 8), "bouffant", "decorator", grow=0.4),
    G("skirt", "body", (-5, 11, -3), (10, 6, 6), "skirt", "decorator", grow=(-0.2, 0, -0.2)),
]
GEAR_SPEC = {"name": "gear", "tex_w": 64, "parts": [{"name": g["name"], "boxes": [g["box"]]} for g in GEAR]}


def gear_texel(mat, face, i, j, w, h):
    """Colour of one texel of a gear box face."""
    side = face in ("west", "east", "north", "south")
    if mat == "brim":
        F, Fs, Fd = FEDORA
        if face == "top":
            edge = i == 0 or i == w - 1 or j == 0 or j == h - 1
            inner = 3 <= i <= w - 4 and 3 <= j <= h - 4
            if inner:
                return BAND[1]  # hidden under the crown
            return Fs if edge else F
        if face == "bottom":
            return Fd
        return Fs
    if mat == "satchel":
        L, Ls, Ld = LEATHER
        if face == "top":
            return Ls
        if face == "east":  # the outer side: a flap with a brass buckle
            if j <= 1:
                return Ls
            if j == 2 and i in (1, 2):
                return GOLD[0]
            return L
        if face == "bottom":
            return Ld
        return mix(L, Ls, 0.4)
    if mat == "visor":
        if face == "north":
            if i in (0, w - 1):
                return CHROME[1]  # hinges
            if j == 0 and i in (2, 3):
                return (150, 226, 230)  # glint
            return (34, 96, 110) if j == 0 else (22, 66, 80)
        if face == "top":
            return CHROME[0]
        return (20, 56, 66)
    if mat == "crest":
        return CHROME[0] if face == "top" else CHROME[1]
    if mat == "ear":
        if face in ("west", "east"):
            if i == 1 and j == 1:
                return CHERRY[0]
            return CHROME[0] if (i + j) % 2 == 0 else CHROME[1]
        return CHROME[2]
    if mat == "radio":
        if face == "south":
            if j == 0 or j == h - 1 or i in (0, w - 1):
                return CHROME[1]  # chrome frame
            if j in (2, 3) and 1 <= i <= w - 2:
                return (52, 56, 62) if j == 2 else (74, 80, 88)  # louvres
            if j == 1 and i == w - 2:
                return CHERRY[0]  # power lamp
            if j == 4 and i in (1, 2):
                return ENAMEL[0]  # tuning dial
            return ENAMEL[1]
        if face == "top":
            return CHROME[0]
        return ENAMEL[2]
    if mat == "antenna":
        return CHROME[1]
    if mat == "tip":
        return CHERRY[0]
    if mat == "holster":
        if face == "west" and j == 0:
            return LEATHER[1]
        return (52, 40, 34) if face != "top" else (36, 28, 24)
    if mat == "grip":
        return (40, 40, 46) if face != "top" else CHROME[1]
    if mat == "barrel":
        return CHROME[0] if (j % 2 == 0) else CHROME[1]
    if mat == "fins":
        return CHERRY[0] if face != "bottom" else CHERRY[1]
    if mat == "emitter":
        return (140, 255, 240)
    if mat == "baton":
        if j == h - 1 or (face == "top" and j == 0):
            return CHROME[0]
        return (34, 34, 40) if (j % 3) else (60, 60, 70)
    if mat == "spark":
        return (190, 230, 255)
    if mat == "bouffant":
        hb, hs, hl = BLONDE
        if face == "east" and j == h - 1 and i in (5, 6):
            return CHERRY[0]  # a little bow
        n = noise(i, j, 70 + ord(face[0]) + len(face))
        return hl if n > 0.25 else (hs if n < -0.3 else hb)
    if mat == "skirt":
        if face == "bottom":
            return DRESS[2]
        if face == "north" and 2 <= i <= w - 3:
            if j == h - 1:
                return APRON[1] if i % 2 else APRON[0]  # ruffled apron hem
            return APRON[0]
        if j == h - 1:
            return DRESS[1]
        return DOT if dotted(i, j, 1) else DRESS[0]
    return (255, 0, 255)


def gear_texture():
    D.pack(GEAR_SPEC)
    img = Image.new("RGBA", (GEAR_SPEC["tex_w"], GEAR_SPEC["tex_h"]), (0, 0, 0, 0))
    for part in GEAR_SPEC["parts"]:
        b = part["boxes"][0]
        for face, (u0, v0), (cols, rows), _ in D.faces(b):
            light = {"top": 1.06, "bottom": 0.75, "north": 1.0, "south": 0.9, "west": 0.94, "east": 0.94}[face]
            for j in range(rows):
                for i in range(cols):
                    c = gear_texel(b["mat"], face, i, j, cols, rows)
                    img.putpixel((u0 + i, v0 + j), clamp(mul(c, light)))
    return img


# ----------------------------------------------------------------------------
# Java geometry
# ----------------------------------------------------------------------------

def jf(v):
    return D.jf(v)


def grow_args(grow):
    if isinstance(grow, tuple):
        return f"new CubeDeformation({jf(grow[0])}, {jf(grow[1])}, {jf(grow[2])})"
    return f"new CubeDeformation({jf(grow)})"


def write_java():
    lines = []
    for g in GEAR:
        b = g["box"]
        (x, y, z), (w, h, d), (u, v) = b["pos"], b["size"], b["uv"]
        px, py, pz = g["pivot"]
        rx, ry, rz = g["rot"]
        lines.append(f"        {g['bone']}.addOrReplaceChild(\"{g['name']}\", CubeListBuilder.create().texOffs({u}, {v})"
                     f".addBox({jf(x)}, {jf(y)}, {jf(z)}, {jf(w)}, {jf(h)}, {jf(d)}, {grow_args(b['grow'])}),\n"
                     f"                PartPose.offsetAndRotation({jf(px)}, {jf(py)}, {jf(pz)}, {jf(rx)}, {jf(ry)}, {jf(rz)}));")
    groups = ",\n            ".join(f"Map.entry(\"{g['name']}\", \"{g['group']}\")" for g in GEAR)
    src = f"""package com.replecant.retrocosmos.npc.client;

import java.util.Map;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeDeformation;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.client.model.player.PlayerModel;

/**
 * Geometry of the expedition crew. GENERATED by tools/npcs.py (which also paints the matching gear sheet) - edit the
 * GEAR list there and re-run tools/gen_resources.py instead of editing this file.
 */
public final class CrewGeometry {{
    /** Gear part -> who wears it: cooper, guard, holstered (pistol in the holster), pistol (drawn), baton (drawn). */
    public static final Map<String, String> GEAR_GROUPS = Map.ofEntries(
            {groups});

    private CrewGeometry() {{}}

    /** The crew body: exactly the vanilla player model (wide arms), so the skins use the vanilla layout. */
    public static LayerDefinition skin() {{
        return LayerDefinition.create(PlayerModel.createMesh(CubeDeformation.NONE, false), 64, 64);
    }}

    /** Hats, helmets, packs and weapons: the same bones as the body, carrying only the accessories. */
    public static LayerDefinition gear() {{
        MeshDefinition mesh = new MeshDefinition();
        PartDefinition root = mesh.getRoot();
        PartDefinition head = root.addOrReplaceChild("head", CubeListBuilder.create(), PartPose.ZERO);
        head.addOrReplaceChild("hat", CubeListBuilder.create(), PartPose.ZERO);
        PartDefinition body = root.addOrReplaceChild("body", CubeListBuilder.create(), PartPose.ZERO);
        PartDefinition right_arm = root.addOrReplaceChild("right_arm", CubeListBuilder.create(), PartPose.offset(-5.0F, 2.0F, 0.0F));
        PartDefinition left_arm = root.addOrReplaceChild("left_arm", CubeListBuilder.create(), PartPose.offset(5.0F, 2.0F, 0.0F));
        PartDefinition right_leg = root.addOrReplaceChild("right_leg", CubeListBuilder.create(), PartPose.offset(-1.9F, 12.0F, 0.0F));
        PartDefinition left_leg = root.addOrReplaceChild("left_leg", CubeListBuilder.create(), PartPose.offset(1.9F, 12.0F, 0.0F));
{chr(10).join(lines)}
        return LayerDefinition.create(mesh, {GEAR_SPEC['tex_w']}, {GEAR_SPEC['tex_h']});
    }}
}}
"""
    os.makedirs(JAVA_DIR, exist_ok=True)
    with open(os.path.join(JAVA_DIR, "CrewGeometry.java"), "w", encoding="utf-8") as f:
        f.write(src)


def write_lines_java():
    """npc/CrewLines.java: how many lines each chat group and how many names each look has (from LINES / NAMES)."""
    groups = {}
    for key in LINES:
        head, _, tail = key.rpartition(".")
        if tail.isdigit():
            groups[head] = max(groups.get(head, 0), int(tail) + 1)
    lines = ",\n            ".join(f"Map.entry(\"{k}\", {v})" for k, v in sorted(groups.items()))
    names = ",\n            ".join(f"Map.entry(\"{k}\", {len(v)})" for k, v in sorted(NAMES.items()))
    src = f"""package com.replecant.retrocosmos.npc;

import java.util.Map;

/**
 * How many chat lines (chat.retrocosmos.npc.&lt;group&gt;.N) and names (npc.retrocosmos.name.&lt;group&gt;.N) there are.
 * GENERATED by tools/npcs.py from its LINES and NAMES tables - add lines there and re-run tools/gen_resources.py.
 */
public final class CrewLines {{
    private static final Map<String, Integer> LINES = Map.ofEntries(
            {lines});

    private static final Map<String, Integer> NAMES = Map.ofEntries(
            {names});

    private CrewLines() {{}}

    public static int count(String group) {{
        return LINES.getOrDefault(group, 0);
    }}

    public static int names(String group) {{
        return NAMES.getOrDefault(group, 1);
    }}
}}
"""
    path = os.path.join(JAVA_DIR, "..", "CrewLines.java")
    with open(path, "w", encoding="utf-8") as f:
        f.write(src)


# ----------------------------------------------------------------------------
# Items: the Space Credit and the crew spawn eggs
# ----------------------------------------------------------------------------

def item_credit():
    """A chrome coin with a cherry-red enamel star and a turquoise rim gem - the expedition's scrip."""
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    cx, cy = 7.5, 7.5
    for y in range(16):
        for x in range(16):
            d = math.hypot(x - cx, y - cy)
            if d > 7.2:
                continue
            if d > 6.2:
                c = (84, 90, 102)  # outline
            elif d > 5.0:
                # milled chrome rim, lit from the upper left
                t = ((x - cx) + (y - cy)) / 10.0
                c = mix((246, 250, 255), (132, 140, 154), 0.5 + t)
                if (x + y) % 2 == 0:
                    c = mul(c, 0.92)
            else:
                t = ((x - cx) + (y - cy)) / 12.0
                c = mix((214, 222, 232), (150, 158, 172), 0.5 + t)
            img.putpixel((x, y), clamp(c))
    star = [
        "...r...",
        "...r...",
        "rrrRrrr",
        ".rRRRr.",
        "..rRr..",
        ".rr.rr.",
        ".r...r.",
    ]
    for j, row in enumerate(star):
        for i, ch in enumerate(row):
            if ch == "r":
                img.putpixel((4 + i, 4 + j), clamp(CHERRY[0]))
            elif ch == "R":
                img.putpixel((4 + i, 4 + j), clamp((240, 90, 90)))
    img.putpixel((7, 1), clamp(TURQ[0]))
    img.putpixel((8, 1), clamp(mix(TURQ[0], (255, 255, 255), 0.5)))
    for p in ((4, 3), (3, 4)):
        img.putpixel(p, (255, 255, 255, 255))
    return img


EGGS = {
    "cooper_spawn_egg": ((196, 164, 112), (120, 78, 44)),
    "guard_spawn_egg": ((206, 42, 48), (244, 244, 238)),
    "scientist_spawn_egg": ((246, 246, 242), (60, 196, 188)),
    "decorator_spawn_egg": ((246, 178, 198), (252, 246, 248)),
}


# ----------------------------------------------------------------------------
# Language
# ----------------------------------------------------------------------------

ITEM_NAMES = {
    "space_credit": ("Space Credit", "Космический кредит"),
    "cooper_spawn_egg": ("Dr. Cooper Spawn Egg", "Яйцо призыва доктора Купера"),
    "guard_spawn_egg": ("Expedition Guard Spawn Egg", "Яйцо призыва охранника экспедиции"),
    "scientist_spawn_egg": ("Expedition Scientist Spawn Egg", "Яйцо призыва учёного экспедиции"),
    "decorator_spawn_egg": ("Showroom Decorator Spawn Egg", "Яйцо призыва продавщицы мебели"),
}

ENTITY_NAMES = {
    "": ("Expedition Member", "Член экспедиции"),
    ".cooper": ("Archaeologist", "Археолог"),
    ".guard": ("Expedition Guard", "Охранник экспедиции"),
    ".scientist": ("Expedition Scientist", "Учёный экспедиции"),
    ".decorator": ("Interior Decorator", "Декоратор интерьеров"),
    ".trade_title": ("%s - Antiquities & Supplies", "%s - древности и снабжение"),
    ".trade_title.decorator": ("%s — Atomic Home Showroom", "%s — салон «Атомный дом»"),
}

NAMES = {
    "cooper": [("Dr. Harold Cooper", "Доктор Гарольд Купер")],
    "decorator": [("Betty Palmer", "Бетти Палмер")],
    "guard": [("Sgt. Rourke", "Сержант Рурк"), ("Pvt. Dawson", "Рядовой Доусон"), ("Cpl. Mendez", "Капрал Мендес"),
              ("Pvt. Kowalski", "Рядовой Ковальски"), ("Sgt. Brooks", "Сержант Брукс"), ("Pvt. O'Hara", "Рядовой О'Хара"),
              ("Cpl. Jefferson", "Капрал Джефферсон"), ("Pvt. Lindqvist", "Рядовой Линдквист")],
    # per skin variant: the people who look like that
    "scientist.0": [("Dr. Ellen Hayes", "Доктор Эллен Хейз"), ("Dr. Margaret Wilde", "Доктор Маргарет Уайлд")],
    "scientist.1": [("Prof. Milo Vance", "Профессор Майло Вэнс"), ("Prof. Walter Grimsby", "Профессор Уолтер Гримсби")],
    "scientist.2": [("Dr. Ada Okafor", "Доктор Ада Окафор"), ("Dr. Ruth Bellamy", "Доктор Рут Беллами")],
    "scientist.3": [("Dr. Hiro Tanaka", "Доктор Хиро Танака"), ("Dr. Kenji Mori", "Доктор Кэндзи Мори")],
}

# chat.retrocosmos.npc.<key>
LINES = {
    "say": ("<%s> %s", "<%s> %s"),
    # ---- Dr. Cooper ----
    "cooper.greet.0": ("Ah, a fellow explorer! Come in, come in - mind the crates.",
                       "А, коллега-исследователь! Входите, входите - осторожно, ящики."),
    "cooper.greet.1": ("Found anything old, odd or obviously cursed? I pay in good Space Credits.",
                       "Нашли что-нибудь древнее, странное или явно проклятое? Плачу добротными кредитами."),
    "cooper.greet.2": ("Every relic tells a story, my friend. Let's hear yours.",
                       "Каждая реликвия рассказывает историю, друг мой. Послушаем вашу."),
    "cooper.greet.3": ("The Smithsonian would weep to see what I keep in this office.",
                       "Смитсоновский институт расплакался бы, увидев, что хранится в этом кабинете."),
    "cooper.greet.4": ("Back from Venus in one piece? Splendid. Show me the loot!",
                       "Вернулись с Венеры целым? Великолепно. Показывайте добычу!"),
    "cooper.greet.5": ("Rocket fuel, oxygen, tea - and a fair price for antiquities. Cooper's, at your service.",
                       "Ракетное топливо, кислород, чай - и честная цена за древности. Купер к вашим услугам."),
    "cooper.idle.0": ("Fascinating... the glyphs repeat every nineteen marks. A calendar? A warning?",
                      "Поразительно... глифы повторяются каждые девятнадцать знаков. Календарь? Предупреждение?"),
    "cooper.idle.1": ("Some day there'll be a museum of the Solar System. I intend to fill it.",
                      "Когда-нибудь будет музей Солнечной системы. И я намерен его заполнить."),
    "cooper.idle.2": ("I once traded a pocket watch for a raptor tooth. Best deal of my career.",
                      "Однажды я выменял карманные часы на зуб раптора. Лучшая сделка в моей карьере."),
    "cooper.idle.3": ("Whoever built those Venusian pyramids knew their stars better than we do.",
                      "Кто бы ни строил венерианские пирамиды, звёзды они знали лучше нас."),
    "cooper.idle.4": ("Mind you don't touch the idol. It hums at night. I'm nearly sure it hums.",
                      "Только не трогайте идола. Он гудит по ночам. Я почти уверен, что гудит."),
    "cooper.idle.5": ("Hmm. Someone has been at my blueprints drawer... no, no, not ready yet.",
                      "Хм. Кто-то рылся в ящике с чертежами... нет-нет, они ещё не готовы."),
    "cooper.thanks.0": ("Splendid! Into the collection it goes.", "Великолепно! Отправляется в коллекцию."),
    "cooper.thanks.1": ("A fine piece. Fine indeed.", "Прекрасный экземпляр. Действительно прекрасный."),
    "cooper.thanks.2": ("Pleasure doing business, explorer.", "Приятно иметь с вами дело, исследователь."),
    "cooper.thanks.3": ("Handle that canister gently - it's not a souvenir.",
                        "С канистрой поаккуратнее - это не сувенир."),
    "cooper.protest.0": ("I say! I'm a scholar, not a punching bag!",
                         "Позвольте! Я учёный, а не боксёрская груша!"),
    "cooper.protest.1": ("Steady on! I survived three curses and a camel - you won't be the end of me.",
                         "Полегче! Я пережил три проклятия и одного верблюда - вам меня не одолеть."),
    "cooper.protest.2": ("Careful! You'll knock over the Ming vase. Well - the Venusian equivalent.",
                         "Осторожно! Опрокинете вазу эпохи Мин. Ну - её венерианский аналог."),
    "cooper.first.venusian_idol": (
        "Great Scott - a Venusian idol! Look at the workmanship! Those eyes... they followed me. Did you see that?",
        "Святые угодники - венерианский идол! Какая работа! Эти глаза... они следят за мной. Вы видели?"),
    "cooper.first.glyph_tablet": (
        "A glyph tablet! The first complete inscription I've ever held. Somebody fetch me a dictionary - from 10,000 B.C.!",
        "Табличка с глифами! Первая целая надпись в моих руках. Дайте мне словарь - за десятое тысячелетие до н.э.!"),
    "cooper.first.sun_disk_fragment": (
        "A piece of a sun disk! Bring me every shard you find - I mean to put the whole thing back together.",
        "Осколок солнечного диска! Несите мне все осколки - я намерен собрать его целиком."),
    "cooper.first.ancient_amulet": (
        "By Jove... an ancient amulet. It's warm. Why is it warm?! This changes everything we know about Venus!",
        "Батюшки... древний амулет. Он тёплый. Почему он тёплый?! Это переворачивает всё, что мы знали о Венере!"),
    "cooper.first.tribal_mask": (
        "A tribal mask! Living culture, right next to the ruins - the tribes may be the builders' descendants!",
        "Племенная маска! Живая культура прямо возле руин - возможно, племена и есть потомки строителей!"),
    "cooper.first.bone_spear": (
        "A bone spear, flint-tipped and balanced like a rifle. Remarkable craftsmen, our hairy neighbours.",
        "Костяное копьё с кремнёвым наконечником и балансом как у винтовки. Замечательные мастера наши мохнатые соседи."),
    "cooper.first.raptor_tooth": (
        "A raptor tooth! Serrated like a steak knife. I'll keep this one on my desk - as a reminder to stay on the path.",
        "Зуб раптора! Зазубрен, как нож для стейка. Оставлю его на столе - чтобы не забывать держаться тропы."),
    "cooper.first.dino_hide": (
        "Dinosaur hide! Tanned by hand, too. Wait until the boys at the University see this.",
        "Шкура динозавра! Да ещё и выделана вручную. Вот увидят это ребята в университете..."),
    "cooper.first.venus_amber": (
        "Venusian amber - and there's something inside! A bug? A seed? Ha! A whole lost world in a pebble.",
        "Венерианский янтарь - и внутри что-то есть! Жук? Семя? Ха! Целый затерянный мир в камешке."),
    "cooper.first.shaman_charm": (
        "A shaman's charm. I don't believe in magic, of course. ...Of course. Put it down gently.",
        "Оберег шамана. В магию я, конечно, не верю. ...Конечно. Положите его аккуратно."),
    "cooper.first.tyrannosaurus_fang": (
        "Good heavens - a tyrant lizard's fang! As long as my hand! You... you didn't fight it, did you? Sit down. Have a drink.",
        "Боже правый - клык ящера-тирана! Длиной с мою ладонь! Вы... вы ведь не дрались с ним? Присядьте. Выпейте чего-нибудь."),
    "cooper.first.plesiosaur_tooth": (
        "A sea-serpent's tooth! So the sailors' stories were true - out there in that boiling sea, something with a neck like a crane.",
        "Зуб морского змея! Значит, байки моряков не врали - там, в кипящем море, водится тварь с шеей, как у подъёмного крана."),
    "cooper.first.deinosuchus_tooth": (
        "Crocodile? No - something far worse. Look at the size of it! Stay away from the swamp banks, my friend.",
        "Крокодил? Нет - нечто куда хуже. Вы только посмотрите на размер! Держитесь подальше от болотных берегов, друг мой."),
    "cooper.first.ankylosaurus_plate": (
        "Armour plate from a living tank! Our engineers would give their slide rules for an alloy this tough.",
        "Броневая пластина живого танка! Наши инженеры отдали бы свои логарифмические линейки за такой сплав."),
    "cooper.first.control_collar": (
        "A control collar - riveted steel, a radio valve and a kill switch. Whoever built this wanted an army, not a pet. Oinstein...",
        "Ошейник управления - клёпаная сталь, радиолампа и выключатель. Кто бы это ни собрал, ему нужна армия, а не питомец. Ойнштайн..."),
    "cooper.first.brain_flask": (
        "Good Lord, it's still warm. A brain - an ape's brain, three times too big. I'll need a stiff drink and a bigger jar.",
        "Господи, он ещё тёплый. Мозг - обезьяний мозг, втрое больше положенного. Мне нужно выпить и банку побольше."),
    "cooper.first.atomic_core": (
        "Still warm! An atomic core from one of Oinstein's machines... Wrap it in lead, please, and never tell me where you got it.",
        "Ещё тёплое! Атомное ядро из машины Ойнштайна... Заверните в свинец, прошу вас, и никогда не говорите, где вы его взяли."),
    "cooper.first.generic": ("Now THAT is something I've never seen before. Into the collection!",
                             "Вот ЭТОГО я ещё никогда не видел. В коллекцию!"),
    # ---- guards ----
    "guard.talk.0": ("Stay inside the perimeter, civilian. Raptors hunt in packs out there.",
                     "Держитесь в пределах периметра, гражданский. Рапторы охотятся стаями."),
    "guard.talk.1": ("Sir! Camp's secure, sir. Mostly.", "Сэр! Лагерь в безопасности, сэр. В основном."),
    "guard.talk.2": ("Ray pistols, fresh charge, full safety. Don't worry, I'm a crack shot.",
                     "Лучевой пистолет заряжен, предохранитель снят. Не волнуйтесь, стреляю без промаха."),
    "guard.talk.3": ("The hairy fellows from the jungle? Friendly, long as you don't poke 'em.",
                     "Мохнатые ребята из джунглей? Дружелюбные, пока их не дразнишь."),
    "guard.talk.4": ("Saw a long-neck big as a gantry by the river this morning. Didn't even look at us.",
                     "Утром у реки видел длинношеего размером с пусковую башню. Даже не взглянул на нас."),
    "guard.talk.5": ("Nobody goes into those ruins without telling the sergeant. Doctor's orders - Cooper's, that is.",
                     "В руины никто не ходит, не доложив сержанту. Распоряжение доктора - Купера, то есть."),
    "guard.talk.6": ("If the triceratops lowers its head - run. Don't ask, just run.",
                     "Если трицератопс опустил голову - беги. Не спрашивай, просто беги."),
    "guard.talk.7": ("Ever seen a sunset through Venus clouds? Copper and green. Beats Nebraska.",
                     "Видели закат сквозь облака Венеры? Медь и зелень. Небраске и не снилось."),
    "guard.idle.0": ("Quiet out there. Too quiet.", "Тихо там. Слишком тихо."),
    "guard.idle.1": ("Perimeter check, all clear!", "Обход периметра - всё чисто!"),
    "guard.idle.2": ("Hope the cook didn't put dinosaur in the stew again.",
                     "Надеюсь, повар опять не положил динозавра в рагу."),
    "guard.idle.3": ("Keep your eyes peeled for movement in the ferns.",
                     "Следите за движением в папоротниках."),
    "guard.idle.4": ("Battery at ninety percent. Ready for anything.", "Батарея на девяноста процентах. Готов ко всему."),
    "guard.alert.0": ("Contact! Hostile at the perimeter!", "Контакт! Враг у периметра!"),
    "guard.alert.1": ("Raptor! Take cover, eggheads!", "Раптор! В укрытие, яйцеголовые!"),
    "guard.alert.2": ("Hold it right there, you overgrown lizard!", "Ни с места, переросшая ящерица!"),
    "guard.alert.3": ("Weapons free! Protect the scientists!", "Огонь на поражение! Защищать учёных!"),
    "guard.kill.0": ("Target down. Back to your posts.", "Цель поражена. Все по местам."),
    "guard.kill.1": ("That'll teach it.", "Будет знать."),
    "guard.kill.2": ("Scratch one lizard.", "Минус одна ящерица."),
    "guard.protest.0": ("Watch it, pal! I'm on your side!", "Полегче, приятель! Я на твоей стороне!"),
    "guard.protest.1": ("Assaulting an officer of the Expedition? Not on my watch.",
                        "Нападение на сотрудника экспедиции? Не в мою смену."),
    "guard.protest.2": ("Save it for the raptors, mister.", "Прибереги это для рапторов, мистер."),
    "guard.protest.3": ("One more of those and you're on latrine duty.", "Ещё раз - и пойдёшь драить уборные."),
    # ---- scientists ----
    "scientist.lore.0": ("The ruins predate the tribes by thousands of years - yet the tribes guard them like temples.",
                         "Руины старше племён на тысячи лет - и всё же племена охраняют их, как храмы."),
    "scientist.lore.1": ("Raptors are pack hunters. Wound one and the whole pack comes. Remember that.",
                         "Рапторы охотятся стаей. Раните одного - придёт вся стая. Запомните."),
    "scientist.lore.2": ("Glowcap mushrooms brewed in water make a tea with remarkable effects on night vision.",
                         "Светогрибы, заваренные в воде, дают чай с удивительным действием на ночное зрение."),
    "scientist.lore.3": ("The tribesfolk adore anything shiny. Wear one of their masks and they'll treat you like kin.",
                         "Соплеменники обожают всё блестящее. Наденьте их маску - и примут как родного."),
    "scientist.lore.4": ("Fumaroles in the highlands vent sulphur. Fascinating chemistry. Terrible smell.",
                         "Фумаролы в нагорье выбрасывают серу. Потрясающая химия. Ужасный запах."),
    "scientist.lore.5": ("The brontosaurus is a gentle giant - a plant eater. Just don't stand where it steps.",
                         "Бронтозавр - добродушный великан, травоядный. Только не стойте там, куда он ступает."),
    "scientist.lore.6": ("Venus amber traps insects from a hundred million years ago. Dr. Cooper pays well for it.",
                         "Венерианский янтарь хранит насекомых возрастом сто миллионов лет. Доктор Купер платит за него хорошо."),
    "scientist.lore.7": ("The glyphs on the pyramid steps match the star charts. They were watching the sky - watching Earth.",
                         "Глифы на ступенях пирамиды совпадают со звёздными картами. Они наблюдали небо - наблюдали Землю."),
    "scientist.lore.8": ("A triceratops will charge anything that threatens its young. Give the calves a wide berth.",
                         "Трицератопс бросается на всё, что угрожает детёнышам. Обходите телят стороной."),
    "scientist.lore.9": ("Tar pits in the swamp preserve bones perfectly. Also unwary geologists.",
                         "Смоляные ямы в болоте прекрасно сохраняют кости. А также неосторожных геологов."),
    "scientist.lore.10": ("Oxygen readings are fine at ground level - but keep your suit handy in orbit.",
                          "Кислорода у поверхности хватает - но на орбите держите скафандр под рукой."),
    "scientist.lore.11": ("Somewhere in the ruins there is a sealed chamber. The tablets call it 'the house of the sun'.",
                          "Где-то в руинах есть запечатанный зал. Таблички называют его «домом солнца»."),
    "scientist.idle.0": ("Sample forty-two: chlorophyll... but not as we know it.",
                         "Образец сорок два: хлорофилл... но не такой, как мы знаем."),
    "scientist.idle.1": ("Readings are off the charts! Literally - I need more chart paper.",
                         "Показания зашкаливают! Буквально - нужна ещё бумага для самописца."),
    "scientist.idle.2": ("Note to self: do NOT feed the raptors.", "Напоминание себе: НЕ кормить рапторов."),
    "scientist.idle.3": ("If only Professor Einstein could see this.", "Если бы только профессор Эйнштейн это видел."),
    "scientist.idle.4": ("Humidity ninety-eight percent. My slide rule is warping.",
                         "Влажность девяносто восемь процентов. Моя логарифмическая линейка коробится."),
    "scientist.idle.5": ("Fascinating. Absolutely fascinating.", "Поразительно. Просто поразительно."),
    "scientist.flee.0": ("Guards! GUARDS!", "Охрана! ОХРАНА!"),
    "scientist.flee.1": ("It's coming right at me!", "Оно бежит прямо на меня!"),
    "scientist.flee.2": ("Not the notes! Save the notes!", "Только не записи! Спасите записи!"),
    "scientist.flee.3": ("Sergeant! Do something!", "Сержант! Сделайте же что-нибудь!"),
    "scientist.protest.0": ("Ow! I'm a scientist, not a test subject!", "Ай! Я учёный, а не подопытный!"),
    "scientist.protest.1": ("Please! These instruments are delicate - and so am I.",
                            "Прошу вас! Приборы хрупкие - и я тоже."),
    "scientist.protest.2": ("I shall be noting this in my report.", "Я отмечу это в своём отчёте."),
    # ---- Betty Palmer, Atomic Home Showroom ----
    "decorator.greet.0": ("Every modern family deserves a home of TOMORROW! Have a look around, dear!",
                          "Каждая современная семья заслуживает дом ЗАВТРАШНЕГО дня! Осмотритесь, дорогуша!"),
    "decorator.greet.1": ("Welcome to the Atomic Home Showroom! Space-age living at down-to-Earth prices!",
                          "Добро пожаловать в салон «Атомный дом»! Жизнь космической эры по земным ценам!"),
    "decorator.greet.2": ("Is that a bare steel cabin I see in your eyes? Let's fix that, sweetie!",
                          "Неужели у вас голая стальная каюта? Сейчас мы это исправим, милочка!"),
    "decorator.greet.3": ("Chrome! Turquoise! Boomerangs! Everything a rocket-age home could want!",
                          "Хром! Бирюза! Бумеранги! Всё, о чём мечтает дом ракетной эры!"),
    "decorator.greet.4": ("Our egg chair is the talk of three planets - try it, go on!",
                          "О нашем кресле-яйце говорят на трёх планетах - присядьте, не стесняйтесь!"),
    "decorator.greet.5": ("Credits accepted, smiles guaranteed! What can Betty find for you today?",
                          "Принимаем кредиты, улыбки гарантируем! Что Бетти подберёт вам сегодня?"),
    "decorator.idle.0": ("Ooh, that sputnik chandelier just sparkles, doesn't it?",
                         "Ах, как сверкает эта люстра-спутник, правда?"),
    "decorator.idle.1": ("A vending machine in every galley - that's the American way, out here too!",
                         "Автомат с газировкой на каждом камбузе - вот наш образ жизни, и здесь тоже!"),
    "decorator.idle.2": ("Dust in zero-g gets EVERYWHERE. Thank goodness for my feather duster.",
                         "Пыль в невесомости проникает ПОВСЮДУ. Слава богу, у меня есть метёлочка."),
    "decorator.idle.3": ("Turquoise is THE colour of the season. Of every season, honestly.",
                         "Бирюзовый - цвет сезона. Да любого сезона, если честно."),
    "decorator.idle.4": ("Mr. Cooper keeps asking me for a display case for his idols. Brr!",
                         "Мистер Купер всё просит у меня витрину для своих идолов. Бр-р!"),
    "decorator.idle.5": ("Picture it: a googie sofa, a tube radio, and Earth rising in the porthole. Dreamy!",
                         "Представьте: диван в стиле гуги, ламповое радио и Земля, восходящая в иллюминаторе. Мечта!"),
    "decorator.thanks.0": ("Wonderful choice! It'll look simply atomic in your place!",
                           "Чудесный выбор! У вас это будет смотреться просто атомно!"),
    "decorator.thanks.1": ("Thank you kindly - come back soon, we restock every day!",
                           "Большое спасибо - заходите ещё, у нас новый завоз каждый день!"),
    "decorator.thanks.2": ("Sold! Mind the corners on the way through the airlock, dear.",
                           "Продано! Аккуратнее с углами в шлюзе, дорогуша."),
    "decorator.thanks.3": ("Another happy homemaker of tomorrow!", "Ещё одна счастливая хозяйка дома будущего!"),
    "decorator.protest.0": ("Well, I never! Hands off the merchandise - and off me!",
                            "Ну знаете! Руки прочь от товара - и от меня!"),
    "decorator.protest.1": ("Goodness! Is that any way to treat a lady in a showroom?",
                            "Боже мой! Разве так обращаются с дамой в салоне?"),
    "decorator.protest.2": ("I'll have you know these pearls are real - and so is my temper!",
                            "Да будет вам известно, жемчуг настоящий - и характер тоже!"),
}

EN, RU = {}, {}
for _k, (_en, _ru) in ITEM_NAMES.items():
    EN[f"item.{MOD}.{_k}"], RU[f"item.{MOD}.{_k}"] = _en, _ru
for _k, (_en, _ru) in ENTITY_NAMES.items():
    EN[f"entity.{MOD}.expedition_member{_k}"], RU[f"entity.{MOD}.expedition_member{_k}"] = _en, _ru
for _k, _names in NAMES.items():
    for _i, (_en, _ru) in enumerate(_names):
        EN[f"npc.{MOD}.name.{_k}.{_i}"], RU[f"npc.{MOD}.name.{_k}.{_i}"] = _en, _ru
for _k, (_en, _ru) in LINES.items():
    EN[f"chat.{MOD}.npc.{_k}"], RU[f"chat.{MOD}.npc.{_k}"] = _en, _ru


# ----------------------------------------------------------------------------
# Entry point used by gen_resources.py
# ----------------------------------------------------------------------------

def skins():
    out = {"cooper_0": cooper()}
    for v in range(VARIANTS["guard"]):
        out[f"guard_{v}"] = guard(v)
    for v in range(VARIANTS["scientist"]):
        out[f"scientist_{v}"] = scientist(v)
    out["decorator_0"] = decorator()
    return out


def generate():
    for name, img in skins().items():
        save(img, "entity", "npc", name)
    save(gear_texture(), "entity", "npc", "gear")
    write_java()
    write_lines_java()

    save(item_credit(), "item", "space_credit")
    write_json(os.path.join(ASSETS, "models", "item", "space_credit.json"),
               {"parent": "minecraft:item/generated", "textures": {"layer0": f"{MOD}:item/space_credit"}})
    item_def("space_credit", f"{MOD}:item/space_credit")
    for name, (shell, spots) in EGGS.items():
        save(D.egg(shell, spots), "item", name)
        write_json(os.path.join(ASSETS, "models", "item", name + ".json"),
                   {"parent": "minecraft:item/generated", "textures": {"layer0": f"{MOD}:item/{name}"}})
        item_def(name, f"{MOD}:item/{name}")


if __name__ == "__main__":
    generate()
