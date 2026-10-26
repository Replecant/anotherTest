"""Dr. Oinstein, the Venus boss: his Atomic Strider walker (with him in the cockpit), the doctor himself, and what
the serum makes of him - Homo Novus. Same box-spec pipeline as the tribesfolk and mutants (tools/tribes.py): each
spec packs a box-UV sheet, is painted texel by texel and becomes Java geometry in tribe/client/TribeGeometry.java.

Parts may carry a "scale" (the cockpit pilot is a 0.75-scale doctor); Java applies it in the model, the painter
and the preview use part_matrices() below, which honours it.
Texture layers per mob: main, _glow (full-bright: reactor, muzzles, serum, veins, brain) and, for the glass of the
cockpit dome and of Homo Novus' brain flask, _glass (translucent, drawn last).
"""
import math

from PIL import Image

import dinosaurs as D
import tribe_mutants as MU

B, mirrored = D.B, D.mirrored


def P(name, parent, pivot, rot, boxes, scale=1.0):
    p = D.P(name, parent, pivot, rot, boxes)
    p["scale"] = scale
    return p


def part_matrices(spec, pose=None):
    """Like dinosaurs.part_matrices, plus per-part uniform scale (applied after the part's rotation, as ModelPart)."""
    pose = pose or {}
    by_name = {p["name"]: p for p in spec["parts"]}
    out = {}

    def get(name):
        if name in out:
            return out[name]
        p = by_name[name]
        parent = get(p["parent"]) if p["parent"] else [[1 if i == j else 0 for j in range(4)] for i in range(4)]
        dx, dy, dz = pose.get(name, (0, 0, 0))
        rx, ry, rz = p["rot"][0] + dx, p["rot"][1] + dy, p["rot"][2] + dz
        m = D.mat_mul(parent, D.translate(*p["pivot"]))
        m = D.mat_mul(m, D.mat_mul(D.rot_z(rz), D.mat_mul(D.rot_y(ry), D.rot_x(rx))))
        s = p.get("scale", 1.0)
        if s != 1.0:
            m = D.mat_mul(m, [[s, 0, 0, 0], [0, s, 0, 0], [0, 0, s, 0], [0, 0, 0, 1]])
        out[name] = m
        return m

    for p in spec["parts"]:
        get(p["name"])
    return out


def clamp(c, a=255):
    return tuple(max(0, min(255, int(round(v)))) for v in c) + (a,)


def noise(t, k, amp):
    return (D.hash3(t.box_id, t.i, t.j, k) - 0.5) * amp


CLEAR = (0, 0, 0, 0)

# ----------------------------------------------------------------------------
# Dr. Oinstein
# ----------------------------------------------------------------------------

DOC = {
    "skin": (230, 200, 182), "skin_d": (192, 158, 144), "hair": (240, 240, 236), "hair_d": (196, 198, 204),
    "coat": (236, 236, 230), "coat_d": (196, 200, 200), "coat_l": (250, 250, 248), "shirt": (70, 74, 86),
    "tie": (196, 40, 44), "trousers": (62, 64, 74), "shoe": (34, 30, 30),
    "brass": (198, 156, 70), "brass_d": (140, 104, 44), "lens": (110, 200, 150), "lens_l": (210, 255, 230),
    "serum": (90, 255, 110), "glass": (190, 230, 236),
}


def doctor_parts(prefix="", parent=None, pivot=(0, 0, 0), scale=1.0, seated=False, syringe=True):
    """The doctor's box model: a 1950s mad scientist, wild white hair, brass goggles, lab coat."""
    n = lambda s: prefix + s
    parts = [
        P(n("body"), parent, pivot, (0, 0, 0), [B(-4, 0 if not seated else -12, -2, 8, 12, 4, "coat")], scale=scale),
    ]
    head_y = 0 if not seated else -12
    parts.append(P(n("head"), n("body"), (0, head_y, 0), (0, 0, 0), [
        B(-4, -8, -4, 8, 8, 8, "dface"),
        B(-5, -9, -4.5, 10, 6, 10, "dhair"),
        B(-6, -7.5, -1.5, 12, 5, 7, "dtuft"),
        B(-4.5, -5.5, -4.6, 9, 2, 1, "goggles"),
    ]))
    arm_y = 2 if not seated else -10
    arm_l = P(n("arm_l"), n("body"), (5, arm_y, 0), ((-1.1 if seated else 0), 0, (-0.1 if seated else -0.05)), [
        B(-1, -2, -2, 4, 12, 4, "sleeve"),
    ])
    parts += [arm_l, mirrored(arm_l, n("arm_r"))]
    if not seated:
        tail = P(n("coattail"), n("body"), (0, 12, 0), (0, 0, 0), [B(-4.5, 0, -2.5, 9, 5, 5, "coattail")])
        leg_l = P(n("leg_l"), parent, (pivot[0] + 1.9, pivot[1] + 12, pivot[2]), (0, 0, 0),
                  [B(-2, 0, -2, 4, 12, 4, "trousers")], scale=scale)
        parts += [tail, leg_l, mirrored(leg_l, n("leg_r"))]
        if syringe:
            parts.append(P(n("syringe"), n("arm_r"), (-0.5, 10, 0), (0, 0, 0), [
                B(-1, -1, 0, 2, 2, 1, "plunger"),
                B(-0.5, -0.5, -4, 1, 1, 4, "syringe"),
                B(-0.5, -0.5, -6, 1, 1, 2, "needle"),
            ]))
    return parts


def paint_doctor(t, layer):
    """Shared materials of the doctor (standalone, in the cockpit) - main, glow and glass layers."""
    pal = DOC
    mat, f = t.mat, t.face
    if mat not in DOCTOR_MATS:
        return None
    if layer == "glow":
        return clamp(pal["serum"]) if mat == "syringe" and f != "south" else CLEAR
    if layer == "glass":
        return CLEAR
    a = 255
    if mat == "dface":
        if f == "north":
            rows = ["........",
                    "ssssssss",
                    "ssssssss",
                    "ssssssss",  # goggles cover rows 2.5-4.5
                    "ssssssss",
                    "sssddsss",
                    "smmmmmms",
                    "ssMllMss"]
            ch = rows[t.j][t.i]
            c = {"s": pal["skin"], "d": pal["skin_d"], "m": pal["hair"], "M": pal["hair_d"], "l": (150, 90, 90),
                 ".": pal["hair"]}[ch]
        elif f == "top":
            c = pal["hair"]
        elif f == "south":
            c = pal["hair_d"] if (t.i + t.j) % 3 == 0 else pal["hair"]
        elif f == "bottom":
            c = pal["skin_d"]
        else:
            c = pal["skin"] if t.lz - t.z0 < 4 and t.j > 1 else pal["hair"]
            if t.lz - t.z0 < 4 and 3 <= t.lz - t.z0 and t.j in (3, 4):
                c = pal["skin_d"]  # ear
        c = tuple(v + noise(t, 3, 6) for v in c)
    elif mat in ("dhair", "dtuft"):
        # wild white hair, wispy at every edge; the face stays clear
        c = pal["hair"] if D.hash3(t.box_id, t.i, t.j, 5) > 0.25 else pal["hair_d"]
        if f == "north" and mat == "dhair" and t.j >= 1:
            return CLEAR
        if f == "north" and mat == "dtuft" and abs(t.lx) < 4.2:
            return CLEAR
        if f == "bottom" and (abs(t.lx) < 4.1 and t.lz < 4.1) and mat == "dhair":
            return CLEAR
        if f == "bottom" and mat == "dtuft" and abs(t.lx) < 4.1:
            return CLEAR
        if f == "top" and mat == "dtuft" and abs(t.lx) < 5:
            return CLEAR
        edge_row = t.j == 0 if f == "top" else (t.j == t.h - 1 if f in ("east", "west", "south") else False)
        if t.edge and D.hash3(t.box_id, t.i, t.j, 8) < 0.45 and f != "top":
            return CLEAR  # wisps
        if edge_row and D.hash3(t.box_id, t.i, 1, 9) < 0.5:
            return CLEAR
    elif mat == "goggles":
        c = pal["brass"]
        if f == "north":
            if t.i in (1, 2, 6, 7):
                c = pal["lens"] if not (t.j == 0 and t.i in (1, 6)) else pal["lens_l"]
            elif t.i in (0, 8):
                c = pal["brass_d"]
        if f in ("east", "west"):
            c = (44, 40, 40)  # strap
    elif mat == "coat":
        c = pal["coat"]
        if f == "north":
            if abs(t.lx) < 1.0:
                c = pal["shirt"] if t.ly > t.y0 + 1 else pal["coat_d"]
                if abs(t.lx) < 0.6 and t.y0 + 1 < t.ly < t.y0 + 6:
                    c = pal["tie"]
            elif abs(t.lx) < 2.0 and t.ly < t.y0 + 4:
                c = pal["coat_d"]  # lapels
            # Oinstein's insignia on the left breast (3 px wide, a sketch of the 7x7 one)
            if 1.0 < t.lx < 4.0 and t.y0 + 2 < t.ly < t.y0 + 5:
                c = (214, 52, 48) if (t.i + t.j) % 2 else (238, 234, 222)
            # pocket with pens
            if -3.5 < t.lx < -1.5 and t.y0 + 7 < t.ly < t.y0 + 8:
                c = pal["coat_d"]
        if f in ("east", "west") and t.j % 4 == 3:
            c = pal["coat_d"]
        c = tuple(v + noise(t, 4, 5) for v in c)
    elif mat == "coattail":
        c = pal["coat"] if t.i % 3 else pal["coat_d"]
        if f in ("top", "bottom"):
            return CLEAR if (abs(t.lx) < 4 and abs(t.lz) < 2) else clamp(pal["coat_d"])
        if f == "north" and abs(t.lx) < 0.6:
            c = pal["coat_d"]  # the coat's opening
    elif mat == "sleeve":
        c = pal["coat"]
        if t.ly > t.y1 - 3:
            c = pal["skin"] if f != "bottom" else pal["skin_d"]
        elif t.ly > t.y1 - 4:
            c = pal["coat_d"]
        c = tuple(v + noise(t, 6, 5) for v in c)
    elif mat == "trousers":
        c = pal["trousers"]
        if t.ly > t.y1 - 2:
            c = pal["shoe"]
    elif mat == "plunger":
        c = (180, 186, 194)
    elif mat == "syringe":
        c, a = pal["serum"], 255
        if f in ("top", "bottom") and t.edge:
            c = (200, 210, 214)
    elif mat == "needle":
        c = (210, 214, 220)
    else:
        raise ValueError(mat)
    return clamp(c, a)


DOCTOR_MATS = {"dface", "dhair", "dtuft", "goggles", "coat", "coattail", "sleeve", "trousers", "plunger", "syringe",
               "needle"}


def doctor_spec():
    return {"name": "dr_oinstein", "tex_w": 128, "parts": doctor_parts(pivot=(0, 0, 0)), "palette": {}}


# ----------------------------------------------------------------------------
# The Atomic Strider
# ----------------------------------------------------------------------------

STEEL = {"steel": (150, 156, 164), "steel_d": (96, 100, 110), "steel_l": (206, 212, 220), "chrome": (214, 222, 230),
         "rivet": (232, 236, 240), "hazard": (236, 186, 38), "black": (36, 36, 40), "red": (200, 40, 40),
         "core": (110, 255, 170), "core_l": (230, 255, 240), "glow": (110, 255, 200)}


def strider_spec():
    th, sh = 20, 22
    hips_y = -9.6
    parts = [
        P("hips", None, (0, hips_y, 2), (0, 0, 0), [B(-7, -3, -5, 14, 6, 10, "steel")]),
        P("body", "hips", (0, -3, 0), (0, 0, 0), [
            B(-11, -16, -10, 22, 16, 20, "hull"),
            B(-5, -13, 10, 10, 10, 5, "reactor"),
            B(-6.5, -10, 9.5, 13, 2, 6, "ring"),
            B(-7.5, -17, -8.5, 15, 1, 14, "frame"),
            B(-7, -31, -8, 14, 14, 13, "sglass"),
            B(4, -20, 6, 1, 8, 1, "antenna"),
            B(3.5, -21, 5.5, 2, 1, 2, "light"),
        ]),
        P("cannon_l", "body", (12, -9, -1), (0, 0, 0), [
            B(-2, -4, -3, 4, 8, 6, "steel"),
            B(-1, -3.5, -15, 7, 7, 19, "cannon"),
            B(0.5, -2, -20, 4, 4, 5, "muzzle"),
        ]),
    ]
    parts.append(mirrored(parts[-1], "cannon_r"))
    leg = [
        P("thigh_l", "hips", (8, 0, 0), (-0.6, 0, 0), [B(-2.5, -2, -3, 5, th, 6, "armor")]),
        P("shin_l", "thigh_l", (0, th - 2, 0), (1.25, 0, 0), [
            B(-2, -1, -2, 4, sh, 4, "strut"),
            B(-1, 1, 2, 2, sh - 6, 2, "piston"),
        ]),
        P("foot_l", "shin_l", (0, sh - 1, 0), (-0.65, 0, 0), [
            B(-4, -1, -8, 8, 3, 12, "foot"),
            B(-5, 0, -11, 3, 2, 4, "toe"),
            B(2, 0, -11, 3, 2, 4, "toe"),
        ]),
    ]
    parts += leg
    parts += [mirrored(leg[0], "thigh_r", "hips"), mirrored(leg[1], "shin_r", "thigh_r"), mirrored(leg[2], "foot_r", "shin_r")]
    # Dr. Oinstein at the controls, under the glass (a 0.75-scale doctor; legs hidden in the hull)
    parts += doctor_parts(prefix="pilot_", parent="body", pivot=(0, -14, -1.5), scale=0.75, seated=True)
    return {"name": "oinstein_strider", "tex_w": 256, "parts": parts, "palette": {}}


def paint_strider(t, layer):
    d = paint_doctor(t, layer)
    if d is not None:
        return d
    pal = STEEL
    mat, f = t.mat, t.face
    if layer == "glass":
        if mat != "sglass" or f == "bottom":
            return CLEAR
        a = 70 if not t.edge else 130
        c = (186, 232, 240)
        if f in ("north", "east") and t.i in (1, 2) and 1 <= t.j <= t.h - 3:
            c, a = (255, 255, 255), 170
        return c + (a,)
    if layer == "glow":
        if mat == "reactor" and f == "south" and 1 <= t.i <= 8 and 1 <= t.j <= 8:
            r = math.hypot(t.i - 4.5, t.j - 4.5)
            if r < 1.6:
                return clamp(pal["core_l"])
            orbit = abs(math.hypot((t.i - 4.5) * 0.7, t.j - 4.5) - 3.2) < 0.6 or abs(math.hypot(t.i - 4.5, (t.j - 4.5) * 0.7) - 3.2) < 0.6
            return clamp(pal["core"]) if orbit else CLEAR
        if mat == "muzzle" and f == "north":
            return clamp(pal["glow"]) if 0 < t.i < 3 and 0 < t.j < 3 else CLEAR
        if mat == "light":
            return clamp(pal["red"])
        return CLEAR
    if mat == "sglass":
        return CLEAR
    c = pal["steel"]
    rivets = (t.i % 4 == 1 and t.j % 4 == 1) and not t.edge
    if mat in ("steel", "armor", "hull"):
        c = pal["steel"] if not t.edge else pal["steel_d"]
        if rivets:
            c = pal["rivet"]
        if f == "top":
            c = D.lerp(c, pal["steel_l"], 0.35)
        if mat == "hull":
            if f == "north" and t.j >= t.h - 3:
                c = pal["hazard"] if ((t.i + t.j) // 2) % 2 == 0 else pal["black"]  # hazard band
            if f in ("east", "west") and 3 <= t.j < 10:
                u, v = t.i - 6, t.j - 4
                if 0 <= u < 7 and 0 <= v < 7 and MU.insignia(u, v):
                    c = MU.insignia(u, v)
            if f == "north" and 2 <= t.j < 6 and t.i in (3, 4, 17, 18):
                c = (60, 64, 72)  # vents
        if mat == "armor" and f == "north" and t.j % 5 == 2:
            c = pal["steel_d"]
    elif mat == "strut":
        c = pal["steel_d"] if t.i % 2 else pal["steel"]
    elif mat == "piston":
        c = pal["chrome"] if t.j % 6 else pal["steel_d"]
    elif mat in ("foot", "toe"):
        c = pal["steel_d"]
        if f == "top" and rivets:
            c = pal["rivet"]
        if mat == "toe" and f == "north":
            c = pal["hazard"] if t.i % 2 == 0 else pal["black"]
    elif mat == "reactor":
        c = pal["steel_d"]
        if f == "south" and 1 <= t.i <= 8 and 1 <= t.j <= 8:
            c = (40, 70, 60)
    elif mat == "ring":
        c = pal["chrome"] if t.i % 3 else pal["steel_d"]
    elif mat == "frame":
        c = pal["chrome"] if t.i % 3 else pal["red"]
        if f in ("top", "bottom") and abs(t.lx) < 7 and -8 < t.lz < 5:
            return CLEAR
    elif mat == "cannon":
        c = pal["chrome"] if (t.j % 6) else pal["steel_d"]
        if f == "top" and t.i in (2, 3) and t.j % 4 == 0:
            c = pal["red"]
        if f in ("east", "west") and t.j == 2:
            c = pal["red"]
    elif mat == "muzzle":
        c = pal["steel_d"]
        if f == "north":
            c = pal["black"] if 0 < t.i < 3 and 0 < t.j < 3 else pal["chrome"]
    elif mat == "antenna":
        c = pal["steel_l"]
    elif mat == "light":
        c = (140, 30, 30)
    else:
        raise ValueError(mat)
    return clamp(tuple(v + noise(t, 2, 6) for v in c))


# ----------------------------------------------------------------------------
# Homo Novus
# ----------------------------------------------------------------------------

HN = {"skin": (178, 196, 162), "skin_d": (132, 150, 120), "vein": (110, 255, 120), "vein_d": (60, 130, 70),
      "coat": (222, 224, 214), "coat_d": (176, 180, 170), "trousers": (56, 58, 66), "brain": (232, 136, 160),
      "brain_d": (184, 88, 116), "brain_l": (250, 186, 200)}


def homo_spec():
    parts = [
        P("body", None, (0, 6, 0), (0.25, 0, 0), [
            B(-7, -17, -4, 14, 17, 8, "hcoat"),
        ]),
        P("coattail", "body", (0, 0, 0), (-0.25, 0, 0), [B(-7.5, -2, -4.5, 15, 6, 9, "hcoattail")]),
        P("head", "body", (0, -17, -1.5), (-0.2, 0, 0), [
            B(-4, -8, -4, 8, 8, 8, "hface"),
            B(-6, -7.5, -1.5, 12, 5, 7, "dtuft"),
            B(-4.5, -5.5, -4.6, 9, 2, 1, "hgoggles"),
            B(-5.5, -15, -5, 11, 8, 10, "hglass"),
        ]),
        P("brain", "head", (0, -10.5, 0), (0, 0, 0), [B(-4.5, -3.5, -4, 9, 6, 8, "hbrain")]),
    ]
    arm = P("arm_l", "body", (8.5, -15, 0), (-0.35, 0, -0.15), [B(-2.5, -2, -3, 6, 13, 6, "harm")])
    fore = P("forearm_l", "arm_l", (0.5, 11, 0), (-0.2, 0, 0.05), [
        B(-3, 0, -3.5, 7, 11, 7, "hforearm"),
        B(-3.5, 10, -4, 8, 5, 8, "hfist"),
    ])
    leg = P("leg_l", None, (3.5, 6, 0), (0, 0, 0), [B(-2.5, 0, -2.5, 5, 18, 5, "htrousers")])
    parts += [arm, fore, leg, mirrored(arm, "arm_r"), mirrored(fore, "forearm_r", "arm_r"), mirrored(leg, "leg_r")]
    return {"name": "homo_novus", "tex_w": 128, "parts": parts, "palette": {}}


def vein(t):
    """Branching glowing veins: thin lines of a noise field's contours."""
    v = D.value_noise(t.mx, t.my, t.mz, 3.0, 19) * 6.0
    return abs(v - round(v)) < 0.09


def paint_homo(t, layer):
    pal = HN
    mat, f = t.mat, t.face
    if layer == "glass":
        if mat != "hglass" or f == "bottom":
            return CLEAR
        a = 80 if not t.edge else 140
        c = (190, 230, 220)
        crack = (t.i * 3 + t.j * 5) % 11 == 0 or (abs(t.i - t.j) == 1 and t.i < 5)
        if crack:
            c, a = (250, 255, 255), 200  # cracks in the overstretched glass
        return c + (a,)
    if layer == "glow":
        if mat == "hbrain" and f != "bottom":
            c = MU.brain_texel(pal, t)
            return clamp(tuple(v * 0.45 for v in c))
        if mat in ("harm", "hforearm", "hface") and vein(t) and f != "top":
            return clamp(pal["vein"])
        if mat == "hcoat" and f == "north" and abs(t.lx) < 3 and vein(t):
            return clamp(pal["vein"])
        if mat == "hgoggles" and f == "north" and t.i in (1, 2, 6, 7):
            return clamp((150, 255, 160))
        return CLEAR
    if mat == "hglass":
        return CLEAR
    if mat == "dtuft":
        c = paint_doctor(t, "main")
        return c
    if mat == "hface":
        if f == "north":
            rows = ["sSsSSsSs",
                    "ssssssss",
                    "dddddddd",
                    "ssssssss",
                    "ssssssss",
                    "sdsddsds",
                    "smwmwmws",
                    "ssMMMMss"]
            ch = rows[t.j][t.i]
            c = {"s": pal["skin"], "S": pal["skin_d"], "d": pal["skin_d"], "m": (60, 30, 30), "w": (236, 228, 200),
                 "M": DOC["hair"]}[ch]
        elif f == "top":
            c = pal["skin_d"]
        else:
            c = pal["skin"] if t.lz - t.z0 < 4 else DOC["hair"]
        if vein(t) and f != "top":
            c = pal["vein_d"]
    elif mat == "hgoggles":
        c = DOC["brass"]
        if f == "north":
            if t.i in (1, 2, 6, 7):
                c = (90, 160, 110)
                if (t.i, t.j) in ((2, 0), (6, 1)):
                    c = (240, 255, 240)  # cracked lens
            elif t.i in (0, 8):
                c = DOC["brass_d"]
        if f in ("east", "west"):
            c = (44, 40, 40)
    elif mat == "hbrain":
        c = MU.brain_texel(pal, t)
    elif mat in ("hcoat", "hcoattail"):
        c = pal["coat"] if (t.i + t.j) % 5 else pal["coat_d"]
        torn = D.value_noise(t.mx, t.my, t.mz, 2.4, 7) > 0.62
        if torn:
            c = pal["skin"] if not vein(t) else pal["vein_d"]  # the coat split open over the swollen body
        if mat == "hcoat" and f == "north":
            if abs(t.lx) < 1:
                c = pal["skin_d"]
            if 1.5 < t.lx < 4.5 and t.y0 + 2 < t.ly < t.y0 + 5:
                c = (214, 52, 48) if (t.i + t.j) % 2 else (238, 234, 222)  # the insignia, stretched
        if mat == "hcoattail":
            if f in ("top", "bottom") and abs(t.lx) < 7 and abs(t.lz) < 3.5:
                return CLEAR
            if f != "top" and t.ly > t.y1 - 1.5 and (t.i % 3 == 0):
                return CLEAR  # ragged hem
    elif mat in ("harm", "hforearm"):
        c = pal["skin"] if D.hash3(t.box_id, t.i, t.j, 3) > 0.15 else pal["skin_d"]
        if mat == "harm" and t.ly < t.y0 + 3:
            c = DOC["coat"] if (t.i + t.j) % 3 else DOC["coat_d"]  # what is left of the sleeves
        if vein(t):
            c = pal["vein_d"]
    elif mat == "hfist":
        c = pal["skin_d"]
        if f == "north" and t.j >= 2 and t.i % 2 == 0:
            c = D.mul(pal["skin_d"], 0.8)
    elif mat == "htrousers":
        c = pal["trousers"]
        if t.ly > t.y1 - 2.5:
            c = pal["skin_d"]  # burst shoes, bare feet
        if D.value_noise(t.mx, t.my, t.mz, 2.0, 5) > 0.7:
            c = pal["skin"]
    else:
        raise ValueError(mat)
    return clamp(tuple(v + noise(t, 4, 6) for v in c))


SPECS = [doctor_spec(), strider_spec(), homo_spec()]
PAINTERS = {"dr_oinstein": (lambda t, l: paint_doctor(t, l), ("main", "glow")),
            "oinstein_strider": (paint_strider, ("main", "glow", "glass")),
            "homo_novus": (paint_homo, ("main", "glow", "glass"))}

POSES = {
    # the doctor: syringe to the neck
    "doctor_inject": {"arm_r": (-2.3, 0.6, 0.4), "head": (0.15, -0.35, 0.25), "arm_l": (-0.5, 0, -0.4)},
    # the doctor: arms thrown out, head back - "I AM HOMO NOVUS!"
    "doctor_shout": {"arm_l": (-2.6, 0, 0.75), "arm_r": (-2.6, 0, -0.75), "head": (-0.5, 0, 0)},
    # strider: one foot raised high for the stomp
    "strider_stomp": {"thigh_l": (-0.9, 0, 0), "shin_l": (0.4, 0, 0), "foot_l": (0.3, 0, 0), "body": (0.08, 0, 0.05)},
    # strider: wrecked, sagging on its knees
    "strider_wreck": {"thigh_l": (-0.45, 0, 0.15), "thigh_r": (-0.5, 0, -0.2), "shin_l": (0.55, 0, 0), "shin_r": (0.6, 0, 0),
                      "body": (0.3, 0, 0.12), "cannon_l": (0.6, 0, 0), "cannon_r": (0.4, 0, 0)},
    # homo novus: crouched to leap
    "homo_crouch": {"body": (0.45, 0, 0), "head": (-0.35, 0, 0), "leg_l": (-0.9, 0, 0), "leg_r": (-0.9, 0, 0),
                    "arm_l": (-0.4, 0, -0.3), "arm_r": (-0.4, 0, 0.3)},
    # homo novus: both arms reaching forward (the grab)
    "homo_grab": {"arm_l": (-1.5, 0.3, 0), "arm_r": (-1.5, -0.3, 0), "forearm_l": (-0.2, 0, 0), "forearm_r": (-0.2, 0, 0),
                  "body": (0.15, 0, 0)},
    # homo novus: the psychic scream, arms flung wide, head back
    "homo_scream": {"arm_l": (-0.6, 0, -1.2), "arm_r": (-0.6, 0, 1.2), "head": (-0.6, 0, 0), "body": (-0.35, 0, 0)},
}


def build_texture(spec, layer):
    paint, _layers = PAINTERS[spec["name"]]
    if "tex_h" not in spec:
        D.pack(spec)
    img = Image.new("RGBA", (spec["tex_w"], spec["tex_h"]), (0, 0, 0, 0))
    mats = part_matrices(spec)
    box_id = 0
    for part in spec["parts"]:
        m = mats[part["name"]]
        for b in part["boxes"]:
            box_id += 1
            x0, y0, z0 = b["pos"]
            w, h, d = b["size"]
            for face, (u0, v0), (cols, rows), to_local in D.faces(b):
                nrm = D.apply(m, D.FACE_NORMALS[face], 0.0)
                for j in range(rows):
                    for i in range(cols):
                        lx, ly, lz = to_local(i, j)
                        mx, my, mz = D.apply(m, (lx, ly, lz))
                        edge = i == 0 or j == 0 or i == cols - 1 or j == rows - 1
                        t = D.Texel(mat=b["mat"], feat=b["feat"], face=face, i=i, j=j, lx=lx, ly=ly, lz=lz,
                                    mx=mx, my=my, mz=mz, nx=nrm[0], ny=nrm[1], nz=nrm[2], fy=(ly - y0) / h,
                                    edge=edge, x0=x0, y0=y0, z0=z0, x1=x0 + w, y1=y0 + h, z1=z0 + d,
                                    w=w, h=h, d=d, box_id=box_id)
                        img.putpixel((u0 + i, v0 + j), paint(t, layer))
    return img


def java_scales():
    """Part name -> scale, for parts that are not 1:1 (applied by the Java models)."""
    out = {}
    for spec in SPECS:
        for p in spec["parts"]:
            if p.get("scale", 1.0) != 1.0:
                out[p["name"]] = p["scale"]
    return out


# ----------------------------------------------------------------------------
# Assets, data and lang (called from tribes.generate)
# ----------------------------------------------------------------------------

def anchor_sprite():
    """The anchor's item icon: the insignia on a dark steel plate with hazard corners."""
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for y in range(1, 15):
        for x in range(1, 15):
            edge = x in (1, 14) or y in (1, 14)
            c = (60, 64, 72) if not edge else (30, 30, 34)
            if edge and (x + y) % 4 < 2 and (x < 4 or x > 11) and (y < 4 or y > 11):
                c = STEEL["hazard"]
            img.putpixel((x, y), c + (255,))
    for v in range(7):
        for u in range(7):
            c = MU.insignia(u, v)
            if c:
                for dx in range(2):
                    for dy in range(2):
                        if 0 <= 1 + u * 2 + dx < 16:
                            img.putpixel((1 + u * 2 + dx, 1 + v * 2 + dy), c + (255,))
    return img


def boss_assets():
    import os
    from gen_resources import ASSETS, DATA, MOD, item_def, save, write_json
    for spec in SPECS:
        D.pack(spec)
        _paint, layers = PAINTERS[spec["name"]]
        for layer in layers:
            save(build_texture(spec, layer), "entity", "tribe", spec["name"] + ("" if layer == "main" else "_" + layer))
    for name, shell, spots in (("oinstein_strider", (150, 156, 164), (236, 186, 38)),
                               ("homo_novus", (178, 196, 162), (110, 255, 120))):
        egg = name + "_spawn_egg"
        save(D.egg(shell, spots), "item", egg)
        write_json(os.path.join(ASSETS, "models", "item", egg + ".json"),
                   {"parent": "minecraft:item/generated", "textures": {"layer0": f"{MOD}:item/{egg}"}})
        item_def(egg, f"{MOD}:item/{egg}")
    # the anchor: invisible in the world, a plate with the insignia in the hand
    save(anchor_sprite(), "item", "oinstein_boss_anchor")
    write_json(os.path.join(ASSETS, "models", "item", "oinstein_boss_anchor.json"),
               {"parent": "minecraft:item/generated", "textures": {"layer0": f"{MOD}:item/oinstein_boss_anchor"}})
    item_def("oinstein_boss_anchor", f"{MOD}:item/oinstein_boss_anchor")
    write_json(os.path.join(ASSETS, "models", "block", "oinstein_boss_anchor.json"),
               {"textures": {"particle": f"{MOD}:item/oinstein_boss_anchor"}})
    write_json(os.path.join(ASSETS, "blockstates", "oinstein_boss_anchor.json"),
               {"variants": {"": {"model": f"{MOD}:block/oinstein_boss_anchor"}}})
    # Homo Novus' loot (placeholder: his notes drop from code, as a written book)
    write_json(os.path.join(DATA, "loot_table", "entities", "homo_novus.json"), {
        "type": "minecraft:entity", "random_sequence": f"{MOD}:entities/homo_novus",
        "pools": [
            {"rolls": 1, "bonus_rolls": 0, "entries": [{"type": "minecraft:item", "name": f"{MOD}:ray_blaster"}]},
            {"rolls": 1, "bonus_rolls": 0, "entries": [{"type": "minecraft:item", "name": f"{MOD}:brain_flask"}]},
            {"rolls": 1, "bonus_rolls": 0, "entries": [{"type": "minecraft:item", "name": f"{MOD}:venus_amber", "functions": [
                {"function": "minecraft:set_count", "count": {"type": "minecraft:uniform", "min": 4, "max": 8}}]}]},
        ]})
    write_json(os.path.join(DATA, "advancement", "stage2", "a_better_ape.json"), {
        "display": {"icon": {"id": f"{MOD}:brain_flask"},
                    "title": {"translate": f"advancements.{MOD}.stage2.a_better_ape.title"},
                    "description": {"translate": f"advancements.{MOD}.stage2.a_better_ape.description"},
                    "frame": "challenge", "show_toast": True, "announce_to_chat": True, "hidden": False},
        "criteria": {"defeated": {"trigger": "minecraft:impossible"}},
        "rewards": {"experience": 100},
        "parent": f"{MOD}:stage2/venus"})


LINES = {
    "say": ("<%s> %s", "<%s> %s"),
    "strider.intro.0": ("Ah, a visitor! Do wipe your feet - this is a laboratory.",
                        "А, посетитель! Вытирайте ноги - здесь лаборатория."),
    "strider.intro.1": ("You came all this way to be disintegrated? How thoughtful.",
                        "Вы проделали такой путь, чтобы вас дезинтегрировали? Как любезно."),
    "strider.intro.2": ("Behold the Atomic Strider! Forty tons of pure progress!",
                        "Узрите Атомный шагоход! Сорок тонн чистого прогресса!"),
    "strider.taunt.0": ("Hold still! Science requires a steady target.", "Не дёргайтесь! Науке нужна неподвижная мишень."),
    "strider.taunt.1": ("Every great mind was mocked. Then it built a death ray.",
                        "Над каждым великим умом смеялись. Потом он строил луч смерти."),
    "strider.taunt.2": ("Your skull has such a modest capacity. I could fix that.",
                        "У вас такой скромный объём черепа. Я мог бы это исправить."),
    "strider.taunt.3": ("The tribes worship the sun. Soon they will worship ME.",
                        "Племена поклоняются солнцу. Скоро они будут поклоняться МНЕ."),
    "strider.taunt.4": ("Atomic power, my friend! Clean, safe and very, very loud!",
                        "Атомная энергия, друг мой! Чистая, безопасная и очень, очень громкая!"),
    "strider.taunt.5": ("Is that iron? How charmingly medieval.", "Это железо? Как мило, прямо Средневековье."),
    "strider.sentries": ("Sentries! Protect the genius!", "Часовые! Защитить гения!"),
    "strider.wreck": ("No, no, NO! The gyro-stabilisers!", "Нет, нет, НЕТ! Гиростабилизаторы!"),
    "doctor.broke": ("You broke my beautiful machine!", "Вы сломали мою прекрасную машину!"),
    "doctor.serum": ("Very well. I was saving the last dose for a special occasion...",
                     "Что ж. Последнюю дозу я берёг для особого случая..."),
    "doctor.inject": ("For science!", "Во имя науки!"),
    "doctor.shout": ("I AM HOMO NOVUS!", "Я — ЧЕЛОВЕК НОВЫЙ!"),
    "homo.awake": ("Magnificent... I can hear your thoughts. They are very small.",
                   "Великолепно... Я слышу ваши мысли. Они очень маленькие."),
    "homo.taunt.0": ("BIGGER BRAIN! BIGGER FISTS!", "БОЛЬШЕ МОЗГ! БОЛЬШЕ КУЛАКИ!"),
    "homo.taunt.1": ("Evolution is not a theory. It is ME!", "Эволюция - не теория. Эволюция - это Я!"),
    "homo.taunt.2": ("Your ancestors were apes. Your descendants will be MINE.",
                     "Ваши предки были обезьянами. Ваши потомки будут МОИМИ."),
    "homo.taunt.3": ("So many thoughts! I can taste them!", "Сколько мыслей! Я чувствую их вкус!"),
    "homo.taunt.4": ("Come here, specimen!", "Иди сюда, образец!"),
    "homo.taunt.5": ("The flask is holding. Mostly.", "Колба держится. В основном."),
    "homo.rage": ("Children! Out of your tanks - Father needs you!", "Дети! Вон из банок - папа зовёт!"),
    "homo.death": ("Too... big... for one... skull...", "Слишком... велик... для одного... черепа..."),
    "kill.0": ("Another one for the specimen jars!", "Ещё один для банок с образцами!"),
    "kill.1": ("Fascinating. You stopped.", "Любопытно. Вы перестали."),
    "kill.2": ("Note: the subject did not survive. Next!", "Запись: испытуемый не выжил. Следующий!"),
}

NOTES = [
    ("LAB JOURNAL, VENUS.\n\nDay 1. The natives are hominids: stone tools, fire, painfully slow. Their skulls hold "
     "900 cc. Mine holds 1600. The conclusion writes itself.",
     "ЛАБОРАТОРНЫЙ ЖУРНАЛ, ВЕНЕРА.\n\nДень 1. Туземцы - гоминиды: каменные орудия, огонь, мучительная медлительность. "
     "Объём черепа - 900 см³. Мой - 1600. Вывод очевиден."),
    ("Day 40. Serum batch 7 doubles muscle mass in a week. The subjects lose speech but gain obedience. The collars "
     "work. I call them Novus - the new.",
     "День 40. Сыворотка, партия 7, удваивает мышечную массу за неделю. Подопытные теряют речь, зато обретают "
     "послушание. Ошейники работают. Я назвал их Новус - новые."),
    ("Day 112. Batch 9 swells the brain instead. Too big for the skull - a glass flask will do. Hominus Sapiens can "
     "aim a ray pistol. It can also hate. Noted.",
     "День 112. Партия 9 раздувает мозг. В черепе не помещается - сойдёт стеклянная колба. Гоминус Сапиенс умеет "
     "целиться из лучевого пистолета. А ещё ненавидеть. Принято к сведению."),
    ("Day 200. Someone from Earth keeps freeing my specimens. One dose remains, the purest yet. In an emergency, "
     "inject into the neck. Do NOT exceed one dose.",
     "День 200. Кто-то с Земли освобождает мои образцы. Осталась одна доза, самая чистая. В крайнем случае - "
     "колоть в шею. НЕ превышать одну дозу."),
    ("If you are reading this, I exceeded one dose.\n\nLet the tribesfolk go home. Tell Earth the ape was never the "
     "problem. The man with the syringe was.\n\n- O.",
     "Если вы это читаете, я превысил дозу.\n\nОтпустите соплеменников домой. Скажите Земле: дело было не в "
     "обезьяне. Дело было в человеке со шприцем.\n\n- О."),
]

EN, RU = {}, {}
_MOD = "retrocosmos"
for _k, (_en, _ru) in LINES.items():
    EN[f"chat.{_MOD}.oinstein.{_k}"], RU[f"chat.{_MOD}.oinstein.{_k}"] = _en, _ru
for _i, (_en, _ru) in enumerate(NOTES):
    EN[f"book.{_MOD}.oinstein_notes.page{_i}"], RU[f"book.{_MOD}.oinstein_notes.page{_i}"] = _en, _ru
for _k, (_en, _ru) in {
    f"entity.{_MOD}.oinstein_strider": ("Atomic Strider", "Атомный шагоход"),
    f"entity.{_MOD}.dr_oinstein": ("Dr. Oinstein", "Доктор Ойнштайн"),
    f"entity.{_MOD}.homo_novus": ("Homo Novus", "Человек Новый"),
    f"bossbar.{_MOD}.oinstein_strider": ("Dr. Oinstein — Atomic Strider", "Доктор Ойнштайн — Атомный шагоход"),
    f"bossbar.{_MOD}.oinstein_strider.critical": ("Atomic Strider — CRITICAL DAMAGE", "Атомный шагоход — КРИТИЧЕСКИЕ ПОВРЕЖДЕНИЯ"),
    f"bossbar.{_MOD}.dr_oinstein": ("Dr. Oinstein", "Доктор Ойнштайн"),
    f"bossbar.{_MOD}.homo_novus": ("Homo Novus", "Человек Новый"),
    f"title.{_MOD}.homo_novus": ("I AM HOMO NOVUS!", "Я — ЧЕЛОВЕК НОВЫЙ!"),
    f"title.{_MOD}.homo_novus.subtitle": ("Dr. Oinstein has injected the serum", "Доктор Ойнштайн вколол себе сыворотку"),
    f"item.{_MOD}.oinstein_strider_spawn_egg": ("Atomic Strider Spawn Egg", "Яйцо призыва атомного шагохода"),
    f"item.{_MOD}.homo_novus_spawn_egg": ("Homo Novus Spawn Egg", "Яйцо призыва Человека Нового"),
    f"item.{_MOD}.oinstein_notes": ("Dr. Oinstein's Final Notes", "Последние записи доктора Ойнштайна"),
    f"block.{_MOD}.oinstein_boss_anchor": ("Oinstein Boss Anchor", "Якорь босса Ойнштайна"),
    f"advancements.{_MOD}.stage2.a_better_ape.title": ("A Better Ape", "Человек Новый"),
    f"advancements.{_MOD}.stage2.a_better_ape.description": ("Defeat Dr. Oinstein - in his walker and after the serum",
                                                             "Победите доктора Ойнштайна - и в шагоходе, и после сыворотки"),
}.items():
    EN[_k], RU[_k] = _en, _ru
