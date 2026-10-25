"""Dr. Oinstein's mutant hominids: Hominid Novus (the brute) and Hominus Sapiens (the big-brained gunman).

Same pipeline as the tribesman (tools/tribes.py, tools/dinosaurs.py): one box spec per mob packs the box-UV sheet,
paints every texel from where it sits on the model and becomes Java geometry in tribe/client/TribeGeometry.java.
Each mob gets extra texture layers drawn over the same boxes:
  * *_glow.png  - full-bright overlay (eyes, the novus' collar lamp, the sapiens' brain and blaster coil),
  * *_glass.png - the sapiens' translucent brain dome (drawn after the body, so the brain shows through).
Also here: the blaster bolt texture, the item sprites (ray blaster, control collar, brain flask) and spawn eggs.
"""
import math

from PIL import Image

import dinosaurs as D

B, P, mirrored = D.B, D.P, D.mirrored


# ----------------------------------------------------------------------------
# Hominid Novus: a 2.6-block gorilla-built brute in a steel collar
# ----------------------------------------------------------------------------

def novus_spec():
    lean = 0.62
    parts = [
        P("hips", None, (0, 8, 4), (0.15, 0, 0), [
            B(-7, -2, -4, 14, 7, 9, "fur", belly=True),
        ]),
        P("body", None, (0, 8, 3.5), (lean, 0, 0), [
            B(-9, -22, -6, 18, 22, 12, "torso"),
            B(-7.5, -26, -3, 15, 5, 9, "fur", hump=True),
            B(-3, -15, 6, 2, 2, 1, "port"),
            B(1, -10, 6, 2, 2, 1, "port"),
        ]),
        P("collar", "body", (0, -21.5, -5), (-lean + 0.2, 0, 0), [
            B(-6, -2, -6, 12, 4, 12, "collar"),
            B(-1, -1.5, -7, 2, 2, 1, "lamp"),
        ]),
        P("head", "body", (0, -22.5, -4.5), (-lean + 0.25, 0, 0), [
            B(-4.5, -8, -7, 9, 8, 8, "nhead"),
            B(-5, -6.5, -8, 10, 2, 2, "nbrow"),
            B(-3.5, -4, -9, 7, 4, 3, "nmuzzle"),
        ]),
        P("jaw", "head", (0, 0, -3), (0, 0, 0), [
            B(-3.5, -0.5, -6, 7, 2, 4, "njaw"),
        ]),
    ]
    arm_l = P("arm_l", "body", (9.5, -19, -1), (-lean - 0.18, 0, -0.14), [
        B(-3, -2.5, -3.5, 7, 14, 7, "arm"),
        B(1, -3.5, -1, 2, 2, 2, "port"),
    ])
    fore_l = P("forearm_l", "arm_l", (0.5, 11, 0), (-0.22, 0, 0.1), [
        B(-4, 0, -4, 8, 12, 8, "forearm"),
        B(-4.5, 2, -4.5, 9, 4, 9, "brace"),
        B(-4.5, 12, -4.5, 9, 4, 9, "fist"),
    ])
    leg_l = P("leg_l", None, (4.5, 10, 5), (-0.05, 0, -0.06), [
        B(-3, -1, -3, 6, 13, 6, "leg"),
        B(-3.5, 12, -5, 7, 2, 8, "nfoot"),
    ])
    parts += [arm_l, fore_l, leg_l,
              mirrored(arm_l, "arm_r"), mirrored(fore_l, "forearm_r", "arm_r"), mirrored(leg_l, "leg_r")]
    return {"name": "hominid_novus", "tex_w": 256, "parts": parts, "palette": {}}


NOVUS = {
    "fur": (86, 84, 64), "fur_d": (60, 58, 46), "fur_l": (112, 110, 84),
    "skin": (176, 152, 144), "skin_d": (134, 110, 106), "scar": (128, 44, 50), "stitch": (226, 220, 206),
    "steel": (126, 132, 140), "steel_d": (78, 82, 90), "steel_l": (186, 192, 200), "rivet": (214, 218, 222),
    "eye": (255, 70, 40), "lamp": (255, 40, 30), "hazard": (232, 186, 40),
}


def bald(t, density=0.7):
    """A few large patches where the fur has fallen out (lab tampering)."""
    return D.value_noise(t.mx, t.my, t.mz, 6.5, 77) > density


def fur(pal, t, base=None):
    """Matted fur in coarse vertical strands, darker on the underside."""
    c = base or pal["fur"]
    h = D.hash3(t.box_id, t.i, int(t.j / 3), 5)
    if h < 0.22:
        c = D.lerp(c, pal["fur_d"], 0.55)
    elif h > 0.88:
        c = D.lerp(c, pal["fur_l"], 0.45)
    if t.ny > 0.5:
        c = D.mul(c, 0.85)
    n = (D.hash3(t.box_id, t.i, t.j, 17) - 0.5) * 6
    return tuple(v + n for v in c)


def skin(pal, t):
    c = pal["skin"]
    if D.hash3(t.box_id, t.i, t.j, 9) > 0.8:
        c = D.mul(c, 0.92)
    # stitched scar lines across the bald patches
    s = (t.mx * 0.7 + t.my * 0.45 + t.mz * 0.3)
    if abs(s - round(s / 11.0) * 11.0) < 0.45:
        c = pal["scar"] if (t.i + t.j) % 2 else pal["stitch"]
    return c


def steel(pal, t, rivets=True):
    c = pal["steel"]
    if t.edge:
        c = pal["steel_d"]
    if rivets and (t.i % 3 == 1) and (t.j % 3 == 1) and not t.edge:
        c = pal["rivet"]
    if t.face == "top":
        c = D.lerp(c, pal["steel_l"], 0.3)
    n = (D.hash3(t.box_id, t.i, t.j, 3) - 0.5) * 8
    return tuple(v + n for v in c)


def paint_novus(t, layer="main"):
    pal = NOVUS
    mat, f = t.mat, t.face
    glow = layer == "glow"
    lamp_layer = layer == "lamp"
    if glow or lamp_layer:
        if lamp_layer and mat == "lamp" and f != "south":
            return (255, 60, 40, 255) if (t.i + t.j) % 3 else (255, 200, 170, 255)
        if glow and mat == "nhead" and f == "north" and t.j == 3 and t.i in (2, 6):
            return (255, 60, 30, 255)
        return (0, 0, 0, 0)
    a = 255
    if mat in ("fur", "torso", "arm", "leg"):
        c = fur(pal, t)
        if bald(t) or (mat == "torso" and f == "north" and abs(t.lx) < 5 and t.ly > t.y0 + 4):
            c = skin(pal, t)
        if mat == "torso" and f == "north" and abs(t.lx) < 5 and t.y0 + 4 < t.ly < t.y0 + 6:
            c = pal["skin_d"]  # pectoral shadow
        if t.feat.get("belly") and f == "north":
            c = skin(pal, t)
    elif mat == "forearm":
        c = fur(pal, t)
        if bald(t, 0.55):
            c = skin(pal, t)
    elif mat == "brace":
        c = steel(pal, t)
        if f in ("north", "east", "west", "south") and t.j == 1 and t.i % 4 < 2:
            c = pal["hazard"]  # hazard stripes on the band
    elif mat == "fist":
        c = pal["skin_d"]
        if f == "bottom" or (f == "north" and t.j >= 2 and t.i % 2 == 0):
            c = D.mul(pal["skin_d"], 0.78)  # knuckle pads
        if f == "top":
            c = fur(pal, t)
    elif mat == "nfoot":
        c = pal["skin_d"]
        if f == "north" and t.i % 2 == 0:
            c = D.mul(pal["skin_d"], 0.8)
    elif mat == "port":
        c = pal["steel_l"] if f != "south" and f != "north" else (40, 44, 50)
        if f in ("south", "north") and t.edge:
            c = pal["steel"]
    elif mat == "collar":
        c = steel(pal, t)
        if f in ("north", "south", "east", "west") and t.j == 1 and t.i % 5 == 2:
            c = pal["rivet"]
        if f == "north" and t.j == 0:
            c = pal["hazard"] if t.i % 2 else (40, 40, 40)
    elif mat == "lamp":
        c = (180, 30, 24) if f != "south" else pal["steel_d"]
    elif mat == "nhead":
        if f == "north":
            c = pal["skin_d"]
            if t.j == 3:
                c = D.mul(pal["skin_d"], 0.6)
                if t.i in (2, 6):
                    c = (200, 40, 30)  # bloodshot eyes
            if t.j >= 4 and t.i in (0, 8):
                c = fur(pal, t)
        elif f == "top":
            c = fur(pal, t) if not bald(t, 0.5) else skin(pal, t)
            if t.i in (3, 5) and t.j % 2 == 0:
                c = pal["stitch"]  # surgery stitches over the skull
        else:
            c = fur(pal, t)
            if f in ("east", "west") and t.lz - t.z0 < 2.5 and t.ly > t.y0 + 3:
                c = pal["skin_d"]
    elif mat == "nbrow":
        c = D.lerp(pal["fur_d"], pal["skin_d"], 0.3)
        if f == "bottom":
            c = D.mul(pal["skin_d"], 0.6)
    elif mat == "nmuzzle":
        c = pal["skin"]
        if f == "north":
            c = pal["skin_d"]
            if t.j == 0 and t.i in (2, 4):
                c = (50, 32, 30)  # nostrils
            if t.j == 3:
                c = (70, 30, 30)  # lips
        if f in ("east", "west"):
            c = D.mul(pal["skin"], 0.9)
    elif mat == "njaw":
        c = pal["skin_d"]
        if f in ("north", "east", "west") and t.j == 0:
            c = (236, 226, 196) if t.i % 2 == 0 else (90, 30, 30)  # fangs
        if f == "top":
            c = (110, 40, 40)
    else:
        raise ValueError(mat)
    return tuple(max(0, min(255, int(round(v)))) for v in c) + (a,)


# ----------------------------------------------------------------------------
# Hominus Sapiens: upright, lean, a giant brain under a glass dome, a ray pistol
# ----------------------------------------------------------------------------

def sapiens_spec():
    parts = [
        P("body", None, (0, 14, 0), (0.08, 0, 0), [
            B(-4, -8, -2, 8, 8, 4, "suit"),
            B(-4.5, -8.5, -2.5, 9, 3, 5, "harness"),
            B(-2, -7, 2, 4, 5, 2, "pack"),
        ]),
        P("head", "body", (0, -8, -0.5), (-0.08, 0, 0), [
            B(-3.5, -6, -3.5, 7, 6, 7, "sface"),
            B(-5, -13, -5, 10, 8, 10, "glass"),
            B(-5.5, -6, -5.5, 11, 1, 11, "ring"),
            B(-1.5, -12, 5, 3, 3, 2, "valve"),
        ]),
        P("brain", "head", (0, -6, 0), (0, 0, 0), [
            B(-4, -6, -4, 8, 6, 8, "brain"),
        ]),
        P("tube_l", "head", (2, -8, 5), (0.35, 0, 0), [
            B(-0.5, 0, 0, 1, 8, 1, "tube"),
        ]),
    ]
    parts.append(mirrored(parts[-1], "tube_r"))
    arm_l = P("arm_l", "body", (5, -7, 0), (0, 0, -0.06), [
        B(-1, -1, -1.5, 3, 10, 3, "sleeve"),
    ])
    leg_l = P("leg_l", None, (2, 14, 0), (0, 0, 0), [
        B(-2, 0, -2, 4, 10, 4, "pants"),
    ])
    parts += [arm_l, mirrored(arm_l, "arm_r"), leg_l, mirrored(leg_l, "leg_r")]
    # the ray pistol in the right hand: the barrel runs down the arm axis, so it points ahead when the arm is raised
    parts.append(P("blaster", "arm_r", (-0.5, 9, 0), (0, 0, 0), [
        B(-0.5, -1, -0.5, 1, 3, 2, "grip"),
        B(-1, 1, -2.5, 2, 5, 3, "gun"),
        B(-0.5, 6, -1.5, 1, 2, 1, "barrel"),
        B(-2, 2, -3, 4, 1, 4, "fin"),
        B(-2, 4, -3, 4, 1, 4, "fin"),
        B(-1, 8, -2, 2, 2, 2, "emitter"),
    ]))
    return {"name": "hominus_sapiens", "tex_w": 128, "parts": parts, "palette": {}}


SAPIENS = {
    "skin": (174, 162, 172), "skin_d": (132, 120, 134), "fur": (96, 90, 104), "fur_l": (124, 116, 132),
    "suit": (120, 126, 132), "suit_d": (84, 88, 96), "suit_l": (158, 164, 170), "strap": (66, 56, 50),
    "brass": (196, 156, 72), "brain": (232, 136, 160), "brain_d": (184, 88, 116), "brain_l": (250, 186, 200),
    "eye": (250, 230, 90), "chrome": (204, 212, 220), "chrome_d": (132, 142, 154), "red": (208, 44, 48),
    "glow": (110, 255, 200),
}


BRAIN_TILE = ["PPLdPPPd",
              "PLPdPLPd",
              "ddPPdPPP",
              "PPddPdLP",
              "LPPPPdPP",
              "PdddPPdd",
              "PPLdPLPP",
              "dPPdPPPL"]


def brain_texel(pal, t):
    """Pink lobes split by wandering dark sulci (a hand-drawn 8x8 tile, offset per face), and on top the fissure
    between the two hemispheres."""
    off = {"north": 0, "east": 3, "south": 5, "west": 2, "top": 1, "bottom": 4}[t.face]
    ch = BRAIN_TILE[(t.j + off) % 8][(t.i + off * 3) % 8]
    c = {"P": pal["brain"], "L": pal["brain_l"], "d": pal["brain_d"]}[ch]
    if t.face == "top" and abs(t.lx) < 0.6:
        c = D.mul(pal["brain_d"], 0.8)
    return c


def insignia(u, v):
    """Dr. Oinstein's insignia, 7x7: an ape skull under the orbits of an atom. u, v in 0..6."""
    rows = ["..r.r..",
            ".r.c.r.",
            "r.www.r",
            ".wkwkw.",
            "r.www.r",
            ".r.w.r.",
            "..r.r.."]
    ch = rows[v][u]
    return {"r": (214, 52, 48), "c": (90, 240, 220), "w": (238, 234, 222), "k": (30, 26, 30)}.get(ch)


def paint_sapiens(t, layer="main"):
    pal = SAPIENS
    mat, f = t.mat, t.face
    if layer == "glass":
        if mat != "glass":
            return (0, 0, 0, 0)
        if f == "bottom":
            return (0, 0, 0, 0)
        c, a = (176, 228, 236), 70
        if t.edge:
            a = 120
        if f in ("north", "east") and t.i in (1, 2) and 1 <= t.j <= 5:
            c, a = (255, 255, 255), 170  # specular glint
        if f == "top" and t.i == 2 and t.j in (2, 3):
            c, a = (255, 255, 255), 170
        return c + (a,)
    if layer == "glow":
        if mat == "brain" and f != "bottom":
            c = brain_texel(pal, t)
            return tuple(int(v * 0.35) for v in c) + (255,)
        if mat == "sface" and f == "north" and t.j == 2 and t.i in (1, 2, 4, 5):
            return pal["eye"] + (255,)
        if mat == "emitter" or (mat == "fin" and f in ("north", "south", "east", "west") and t.i == 1):
            return pal["glow"] + (255,)
        if mat == "gun" and f == "bottom":
            return pal["glow"] + (255,)
        return (0, 0, 0, 0)

    a = 255
    n = (D.hash3(t.box_id, t.i, t.j, 7) - 0.5) * 8
    if mat == "glass":
        return (0, 0, 0, 0)  # drawn by the translucent glass layer
    if mat == "suit":
        c = pal["suit"]
        if f == "north":
            u, v = t.i - 1, t.j - 1
            if 0 <= u < 7 and 0 <= v < 7 and insignia(u, v):
                c = insignia(u, v)
            elif t.i in (0, 7):
                c = pal["suit_d"]
        if t.ly > t.y1 - 1.5:
            c = pal["strap"]  # belt
            if f == "north" and abs(t.lx) < 1:
                c = pal["brass"]
        if f in ("east", "west") and t.j % 4 == 1:
            c = pal["suit_d"]  # seams
    elif mat == "harness":
        c = pal["strap"]
        if f == "north" and abs(t.lx) > 1.5 and abs(t.lx) < 3.5:
            c = pal["strap"]
        elif f == "north":
            return (0, 0, 0, 0)  # open chest (the insignia shows)
        if f == "top" and abs(t.lx) < 3.5 and -2 < t.lz < 2:
            return (0, 0, 0, 0)
        if f == "bottom":
            return (0, 0, 0, 0)
        if (t.i + t.j) % 5 == 0:
            c = pal["brass"]  # buckles
    elif mat == "pack":
        c = pal["chrome_d"]
        if t.j % 2 == 0 and f == "south":
            c = pal["chrome"]
        if f == "south" and t.j == 1 and t.i in (1, 2):
            c = pal["red"]
    elif mat == "sleeve":
        c = pal["suit"]
        if t.ly > t.y1 - 2.5:
            c = pal["skin_d"] if f != "bottom" else D.mul(pal["skin_d"], 0.8)  # bare hands
            if f == "north" and t.i == 1:
                c = D.mul(pal["skin_d"], 0.8)
        elif t.ly > t.y1 - 3.5:
            c = pal["suit_l"]  # cuff
        if t.ly < t.y0 + 2 and f in ("east", "west"):
            c = pal["red"] if t.j == 1 else c  # shoulder flash
    elif mat == "pants":
        c = pal["suit_d"]
        if t.ly > t.y1 - 3:
            c = (46, 42, 44) if t.ly > t.y1 - 1 or f != "north" else (60, 56, 58)  # boots
            if t.ly < t.y1 - 2 and t.ly > t.y1 - 3:
                c = pal["chrome_d"]
        elif f in ("east", "west") and t.i == 1:
            c = pal["suit"]
    elif mat == "sface":
        if f == "north":
            c = pal["skin"]
            if t.j == 0:
                c = pal["skin_d"]
            if t.j == 1:
                c = D.mul(pal["skin_d"], 0.85)  # slight brow
            if t.j == 2:
                c = D.mul(pal["skin_d"], 0.9)
                if t.i in (1, 5):
                    c = (30, 24, 26)
                if t.i in (2, 4):
                    c = pal["eye"]
            if t.j == 3 and t.i == 3:
                c = pal["skin_d"]
            if t.j == 4 and 1 < t.i < 5:
                c = D.mul(pal["skin_d"], 0.75)  # thin mouth
            if t.j == 5:
                c = D.mul(pal["skin"], 0.94)
        elif f in ("east", "west"):
            c = pal["skin"] if t.lz - t.z0 < 3 else pal["fur"]
            if 2 <= t.lz - t.z0 < 3 and t.j in (2, 3):
                c = pal["skin_d"]  # ear
        elif f == "top":
            c = pal["brain_d"]
        else:
            c = pal["fur"]
    elif mat == "brain":
        c = brain_texel(pal, t)
        if f == "top" and abs(t.lx) < 0.6:
            c = D.mul(pal["brain_d"], 0.8)
    elif mat == "ring":
        c = pal["brass"] if (t.i % 3) else pal["chrome"]
        if f in ("top",) and abs(t.lx) < 4.5 and abs(t.lz) < 4.5:
            return (0, 0, 0, 0)
        if f == "bottom" and abs(t.lx) < 3.6 and abs(t.lz) < 3.6:
            return (0, 0, 0, 0)
    elif mat == "valve":
        c = pal["chrome"] if f != "south" else pal["red"]
    elif mat == "tube":
        c = (140, 180, 190) if t.j % 2 else (110, 150, 160)
    elif mat == "grip":
        c = (92, 54, 36) if t.j % 2 else (120, 72, 44)
    elif mat == "gun":
        c = pal["chrome"] if (t.i + t.j) % 3 else pal["chrome_d"]
        if f == "top" or f == "bottom":
            c = pal["chrome_d"]
    elif mat == "barrel":
        c = pal["chrome_d"] if t.j % 2 else pal["chrome"]
    elif mat == "fin":
        c = pal["red"]
        if t.edge and f in ("top", "bottom"):
            c = D.mul(pal["red"], 0.75)
    elif mat == "emitter":
        c = pal["glow"]
    else:
        raise ValueError(mat)
    return tuple(max(0, min(255, int(round(v + n * 0.5)))) for v in c) + (a,)


SPECS = [novus_spec(), sapiens_spec()]
PAINTERS = {"hominid_novus": (paint_novus, ("main", "glow", "lamp")),
            "hominus_sapiens": (paint_sapiens, ("main", "glow", "glass"))}

POSES = {
    # novus: rearing up on the hind legs, both fists raised over the head (before the slam)
    "novus_rear": {"body": (-0.55, 0, 0), "head": (0.35, 0, 0), "collar": (0.35, 0, 0), "hips": (-0.2, 0, 0),
                   "arm_l": (-2.0, 0, -0.25), "arm_r": (-2.0, 0, 0.25), "forearm_l": (-0.4, 0, 0),
                   "forearm_r": (-0.4, 0, 0), "leg_l": (0.2, 0, 0), "leg_r": (0.2, 0, 0)},
    # novus: the slam itself, fists driven into the ground in front
    "novus_slam": {"body": (0.25, 0, 0), "arm_l": (-0.7, 0, 0.1), "arm_r": (-0.7, 0, -0.1),
                   "forearm_l": (-0.2, 0, 0), "forearm_r": (-0.2, 0, 0), "head": (-0.2, 0, 0)},
    # sapiens: blaster levelled at the target
    "sapiens_aim": {"arm_r": (-1.57, -0.1, 0), "arm_l": (-0.4, 0.3, 0)},
}


def build_texture(spec, layer):
    paint, _layers = PAINTERS[spec["name"]]
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


# ----------------------------------------------------------------------------
# Bolt texture and item sprites
# ----------------------------------------------------------------------------

def bolt_texture():
    """16x16: a white-hot core fading through mint green to clear, used on crossed quads along the flight path."""
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for y in range(16):
        for x in range(16):
            dy = abs(y - 7.5) / 7.5  # across the bolt
            dx = abs(x - 7.5) / 7.5  # along it
            r = math.hypot(dy, dx ** 2.2)
            if r > 1:
                continue
            core = max(0.0, 1 - r * 2.2)
            a = int(255 * (1 - r) ** 0.7)
            c = D.lerp((70, 255, 190), (255, 255, 255), core)
            img.putpixel((x, y), tuple(int(v) for v in c) + (a,))
    return img


def sprite(rows, colours):
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row[:16]):
            if ch in " .":
                continue
            img.putpixel((x, y), tuple(int(v) for v in colours[ch]) + (255,))
    return img


def item_ray_blaster():
    rows = ["................",
            "................",
            "................",
            ".......rr.......",
            "......rrrr......",
            "..kcccccccccchg.",
            ".kclllllllllchgG",
            ".kcddddddddddhg.",
            "..kkcccrrccckk..",
            "....kbbk.rr.....",
            "....kbbk........",
            "...kbbbk........",
            "...kbbk.........",
            "...kbbk.........",
            "...kkkk.........",
            "................"]
    return sprite(rows, {"k": (44, 44, 52), "c": (170, 180, 192), "l": (236, 242, 248), "d": (110, 118, 130),
                         "r": (208, 44, 48), "h": (92, 220, 180), "g": (150, 255, 210), "G": (230, 255, 245),
                         "b": (124, 74, 44)})


def item_control_collar():
    rows = ["................",
            "................",
            "....kkkkkkkk....",
            "...kccllllcck...",
            "..kcdkkkkkkdck..",
            "..kck......kck..",
            ".kck........kck.",
            ".kck........kck.",
            ".kck........kck.",
            ".kcdk......kdck.",
            "..kcdkkrrkkdck..",
            "..kccyyRRyycck..",
            "...kkcckkcckk...",
            ".....kkkkkk.....",
            "................",
            "................"]
    return sprite(rows, {"k": (40, 42, 48), "c": (126, 132, 140), "l": (196, 202, 210), "d": (86, 90, 98),
                         "r": (190, 30, 24), "R": (255, 120, 100), "y": (232, 186, 40)})


def item_brain_flask():
    rows = ["......kkkk......",
            "......kmmk......",
            ".......kk.......",
            "......kggk......",
            ".....kgggwk.....",
            "....kgpppgwk....",
            "...kgpPpppgwk...",
            "...kgppPppPgk...",
            "..kgpPppPpppgk..",
            "..kgppppPpPpgk..",
            "..kgpPpppppPgk..",
            "..kggpppPpppgk..",
            "...kgggpppggk...",
            "....kkggggkk....",
            "......kkkk......",
            "................"]
    return sprite(rows, {"k": (60, 76, 84), "m": (196, 156, 72), "g": (170, 222, 230), "w": (240, 252, 255),
                         "p": (232, 136, 160), "P": (184, 88, 116)})
