"""The dinosaurs of Venus: model geometry, entity textures, spawn eggs, loot tables and lang.

The box models are defined once, here, in SPECS. From that single definition the generator
  * packs every box onto the texture sheet (box-UV layout, exactly as ModelPart.Cube lays it out),
  * paints each texel by where it sits on the 3D model (countershading, stripes, eyes, teeth...),
  * writes the Java geometry (dinosaur/client/DinoGeometry.java) with the same boxes, pivots and UVs,
so the textures always line up with the in-game models.

Coordinates are Minecraft entity-model pixels: y points down, the ground is at y = 24, the head is at -z.
"""
import math
import os

from PIL import Image

from gen_resources import ASSETS, DATA, MOD, generated_item, loot_self, save, shaped, shapeless, write_json
from furniture import add_to_tag

JAVA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "main", "java",
                        "com", "replecant", "retrocosmos", "dinosaur", "client")


# ----------------------------------------------------------------------------
# Spec helpers
# ----------------------------------------------------------------------------

def B(x, y, z, w, h, d, mat, **feat):
    """A box: origin (x, y, z) relative to its part's pivot, integer size (w, h, d), a paint material."""
    return {"pos": (x, y, z), "size": (w, h, d), "mat": mat, "feat": feat}


def P(name, parent, pivot, rot, boxes):
    return {"name": name, "parent": parent, "pivot": pivot, "rot": rot, "boxes": boxes}


def mirrored(part, name, parent=None):
    """The same part on the other side of the body (x mirrored)."""
    px, py, pz = part["pivot"]
    rx, ry, rz = part["rot"]
    boxes = []
    for b in part["boxes"]:
        x, y, z = b["pos"]
        w, h, d = b["size"]
        boxes.append({"pos": (-(x + w), y, z), "size": (w, h, d), "mat": b["mat"], "feat": dict(b["feat"])})
    return P(name, parent if parent is not None else part["parent"], (-px, py, pz), (rx, -ry, -rz), boxes)


def legs(prefix, parts):
    """parts: list of left-side parts whose names end with _l; returns left + mirrored right parts."""
    out = list(parts)
    for p in parts:
        parent = p["parent"]
        if parent and parent.endswith("_l"):
            parent = parent[:-2] + "_r"
        out.append(mirrored(p, p["name"][:-2] + "_r", parent))
    return out


# ----------------------------------------------------------------------------
# The three species
# ----------------------------------------------------------------------------

def raptor_spec():
    parts = [
        P("body", None, (0, 13.5, 1), (-0.12, 0, 0), [
            B(-3.5, -4, -7, 7, 8, 12, "skin"),
        ]),
        P("neck", "body", (0, -1.5, -6), (-0.7, 0, 0), [
            B(-2, -2.5, -6, 4, 5, 7, "skin"),
        ]),
        P("head", "neck", (0, -0.5, -5.5), (0.78, 0, 0), [
            B(-2.5, -3, -5, 5, 5, 6, "skin", eye=(-1.5, -3.5)),
            B(-2, -2, -10, 4, 3, 5, "snout", teeth="bottom", nostril=True),
            B(-0.5, -6, -8, 1, 3, 8, "crest"),
        ]),
        P("jaw", "head", (0, 1, -4.5), (0, 0, 0), [
            B(-1.5, 0, -5.5, 3, 2, 7, "jaw", teeth="top"),
        ]),
        P("tail1", "body", (0, -2.5, 4.5), (0.14, 0, 0), [
            B(-2.5, -1.5, 0, 5, 5, 7, "skin"),
        ]),
        P("tail2", "tail1", (0, 1, 6.5), (0.06, 0, 0), [
            B(-1.5, -1.5, 0, 3, 3, 8, "skin"),
        ]),
    ]
    parts += legs("", [
        P("arm_l", "body", (3, 1.5, -5.5), (0.55, 0, -0.12), [
            B(-0.5, -0.5, -1, 2, 5, 2, "skin"),
        ]),
        P("hand_l", "arm_l", (0.5, 4, 0), (-0.75, 0, 0), [
            B(-1, 0, -2, 2, 3, 1, "claws"),
        ]),
        P("thigh_l", None, (2.5, 14, 2), (-0.4, 0, 0), [
            B(-1, -1.5, -2.5, 3, 7, 5, "skin"),
        ]),
        P("shin_l", "thigh_l", (0.5, 5, 0.5), (0.95, 0, 0), [
            B(-1, -0.5, -1, 2, 6, 2, "skin"),
        ]),
        P("foot_l", "shin_l", (0, 5.5, 0), (-0.55, 0, 0), [
            B(-1.5, -0.5, -4, 3, 1, 5, "foot"),
            B(-0.5, -2.5, -3.5, 1, 2, 1, "claw"),
        ]),
    ])
    return {"name": "raptor", "tex_w": 64, "parts": parts,
            "palette": {"dorsal": (52, 104, 46), "base": (84, 148, 60), "belly": (204, 206, 120),
                        "stripe": (214, 150, 42), "crest": (206, 38, 34), "crest_dark": (128, 18, 22),
                        "claw": (238, 226, 186), "claw_tip": (96, 80, 60), "eye": (255, 214, 40),
                        "foot": (70, 92, 54)}}


def bronto_spec():
    parts = [
        P("body", None, (0, -14, 0), (0, 0, 0), [
            B(-12, -13, -18, 24, 24, 36, "skin"),
            B(-10, -17, -12, 20, 4, 26, "skin"),
            B(-10, 11, -13, 20, 3, 26, "skin"),
        ]),
        P("neck1", "body", (0, -6, -17), (-0.8, 0, 0), [
            B(-6, -6, -15, 12, 12, 16, "neck"),
        ]),
        P("neck2", "neck1", (0, 0, -14), (-0.2, 0, 0), [
            B(-4.5, -4.5, -14, 9, 9, 15, "neck"),
        ]),
        P("neck3", "neck2", (0, 0, -13), (-0.05, 0, 0), [
            B(-3.5, -3.5, -12, 7, 7, 13, "neck"),
        ]),
        P("head", "neck3", (0, 0, -11), (1.0, 0, 0), [
            B(-3.5, -4, -8, 7, 7, 9, "skin", eye=(-2.5, -5.5)),
            B(-2.5, -2, -12, 5, 4, 4, "snout", mouth=True, nostril=True),
        ]),
        P("tail1", "body", (0, -7, 17), (-0.4, 0, 0), [
            B(-8, -7, 0, 16, 14, 15, "skin"),
        ]),
        P("tail2", "tail1", (0, 0, 14), (0.15, 0, 0), [
            B(-5.5, -5, 0, 11, 10, 14, "skin"),
        ]),
        P("tail3", "tail2", (0, 0, 13), (0.15, 0, 0), [
            B(-3.5, -3.5, 0, 7, 7, 13, "skin"),
        ]),
        P("tail4", "tail3", (0, 0, 12), (0.12, 0, 0), [
            B(-2, -2, 0, 4, 4, 11, "skin"),
        ]),
    ]
    parts += legs("", [
        P("leg_front_l", None, (8, -6, -12), (0, 0, 0), [
            B(-4.5, 0, -4.5, 9, 30, 9, "leg", nails=True),
        ]),
        P("leg_back_l", None, (8, -6, 12), (0, 0, 0), [
            B(-5, 0, -5, 10, 30, 10, "leg", nails=True),
        ]),
    ])
    return {"name": "brontosaurus", "tex_w": 256, "parts": parts,
            "palette": {"dorsal": (86, 94, 62), "base": (124, 132, 92), "belly": (196, 192, 150),
                        "blotch": (96, 104, 66), "noise": 6, "nail": (226, 214, 176), "eye": (24, 20, 18)}}


def trike_spec():
    parts = [
        P("body", None, (0, 4, 1), (0, 0, 0), [
            B(-8, -8, -13, 16, 15, 27, "skin"),
            B(-6, -10, -10, 12, 2, 18, "skin"),
        ]),
        P("head", "body", (0, -0.5, -13), (0.12, 0, 0), [
            B(-5, -5, -10, 10, 10, 11, "skin", eye=(-2.5, -6.5)),
            B(-3, -2.5, -14, 6, 4, 4, "beak", hook=True),
            B(-2, 1.5, -13, 4, 2, 3, "beak"),
            B(-1, -5.5, -13, 2, 3, 2, "horn", tip="up"),
        ]),
        P("frill", "head", (0, -3.5, 0.5), (-0.5, 0, 0), []),
        P("tail1", "body", (0, -3, 13), (-0.3, 0, 0), [
            B(-4, -4, 0, 8, 8, 12, "skin"),
        ]),
        P("tail2", "tail1", (0, 0, 11), (0.12, 0, 0), [
            B(-2.5, -2.5, 0, 5, 5, 11, "skin"),
        ]),
    ]
    parts += legs("", [
        # the frill is two halves swept back into a shallow V, so it reads from the side as well
        P("frill_l", "frill", (0, 0, 0), (0, -0.45, 0), [
            B(0, -17, 0, 11, 19, 2, "frill", half_w=11),
        ]),
        P("horn_l", "head", (3, -4.5, -7.5), (-0.45, -0.12, 0), [
            B(-1, -1, -11, 2, 2, 11, "horn", tip="front"),
        ]),
        P("leg_front_l", None, (5.5, 8, -8), (0, 0, 0), [
            B(-3, 0, -3, 6, 16, 6, "leg", nails=True),
        ]),
        P("leg_back_l", None, (5.5, 7, 9), (0, 0, 0), [
            B(-3.5, 0, -3.5, 7, 17, 7, "leg", nails=True),
        ]),
    ])
    return {"name": "triceratops", "tex_w": 128, "parts": parts,
            "palette": {"dorsal": (62, 82, 84), "base": (94, 120, 114), "belly": (206, 198, 160),
                        "blotch": (74, 96, 96), "noise": 7, "horn": (240, 230, 196), "horn_base": (150, 124, 84),
                        "beak": (84, 70, 56), "frill": (214, 84, 38), "frill_edge": (246, 206, 66),
                        "frill_spot": (52, 160, 196), "frill_dark": (110, 34, 24), "nail": (226, 214, 176),
                        "eye": (240, 150, 30)}}


def creeper_spec():
    """Venus Creeper: exactly the vanilla creeper's boxes (head 8x8x8, body 8x12x4, legs 4x6x4 at the vanilla
    pivots), dressed as Venus flora: leafy teal-olive skin with ochre veins, root toes, a fringe of leaf frills at
    the neck (2 px) and a little glowing spore bulb sprouting from the crown."""
    parts = [
        P("head", None, (0, 6, 0), (0, 0, 0), [
            B(-4, -8, -4, 8, 8, 8, "cskin", face=True),
        ]),
        P("body", None, (0, 6, 0), (0, 0, 0), [
            B(-4, 0, -2, 8, 12, 4, "cskin"),
        ]),
        P("bulb", "head", (1.5, -8, 1.5), (0.15, 0, 0.1), [
            B(-0.5, -1, -0.5, 1, 1, 1, "bulbstem"),
            B(-1.5, -3.5, -1.5, 3, 3, 3, "bulb"),
        ]),
        P("leaf_front", "head", (0, 0, -4), (0.7, 0, 0), [
            B(-4, 0, -2, 8, 1, 2, "fringe", axis="-z"),
        ]),
        P("leaf_back", "head", (0, 0, 4), (-0.7, 0, 0), [
            B(-4, 0, 0, 8, 1, 2, "fringe", axis="+z"),
        ]),
    ]
    parts += legs("", [
        P("leaf_l", "head", (4, 0, 0), (0, 0, 0.7), [
            B(0, 0, -4, 2, 1, 8, "fringe", axis="+x"),
        ]),
        P("leg_front_l", None, (2, 18, -4), (0, 0, 0), [
            B(-2, 0, -2, 4, 6, 4, "cskin", toes=True),
        ]),
        P("leg_back_l", None, (2, 18, 4), (0, 0, 0), [
            B(-2, 0, -2, 4, 6, 4, "cskin", toes=True),
        ]),
    ])
    return {"name": "venus_creeper", "tex_w": 64, "parts": parts, "glow": True,
            "palette": {"noise": 6, "skin": (92, 132, 96), "skin_light": (124, 160, 108), "skin_dark": (58, 92, 70),
                        "vein": (204, 152, 62), "face": (18, 30, 20), "root": (104, 78, 50), "root_dark": (62, 44, 30),
                        "stalk": (74, 128, 50), "vein_dark": (52, 96, 40),
                        "leaf": (70, 140, 80), "leaf_dark": (40, 96, 58), "leaf_edge": (214, 170, 60),
                        "bulb": (226, 250, 120), "bulb_core": (255, 255, 210), "bulb_dark": (150, 200, 60)}}


def ptero_spec():
    """Pteranodon: rust-red leather wings, a long beak and the classic swept-back crest. Rest pose = gliding."""
    parts = [
        P("body", None, (0, 15, 0), (0, 0, 0), [
            B(-2.5, -2, -5, 5, 5, 11, "skin"),
        ]),
        P("neck", "body", (0, -0.5, -5), (-0.35, 0, 0), [
            B(-1.5, -1.5, -5, 3, 3, 6, "skin"),
        ]),
        P("head", "neck", (0, -0.5, -4.5), (0.35, 0, 0), [
            B(-2, -2.5, -4, 4, 4, 5, "skin", eye=(-1.5, -2.5)),
            B(-1, -1, -14, 2, 2, 10, "beak"),
        ]),
        P("crest", "head", (0, -2.5, 0), (-0.4, 0, 0), [
            B(-0.5, -2, -1, 1, 3, 9, "pcrest"),
        ]),
        P("jaw", "head", (0, 1, -3.5), (0, 0, 0), [
            B(-1, 0, -9.5, 2, 1, 9, "beak", lower=True),
        ]),
        P("tail", "body", (0, -0.5, 6), (0.1, 0, 0), [
            B(-0.5, -0.5, 0, 1, 1, 4, "skin"),
        ]),
    ]
    parts += legs("", [
        P("wing_l", "body", (2.5, -1, -2.5), (0, 0, 0), [
            B(0, -1, -1, 13, 2, 2, "bone"),
            B(0, -0.5, 1, 13, 1, 8, "membrane", part="inner"),
        ]),
        P("wingtip_l", "wing_l", (13, 0, 0), (0, 0, 0), [
            B(0, -1, -1, 14, 1, 2, "bone"),
            B(0, -0.5, 1, 14, 1, 6, "membrane", part="tip"),
        ]),
        P("leg_l", "body", (1.5, 2, 4), (1.3, 0, 0), [
            B(-0.5, 0, -0.5, 1, 5, 1, "skin"),
            B(-1, 4.5, -2, 2, 1, 3, "pfoot"),
        ]),
    ])
    return {"name": "pteranodon", "tex_w": 64, "parts": parts,
            "palette": {"dorsal": (124, 58, 36), "base": (178, 92, 50), "belly": (226, 196, 146),
                        "blotch": (146, 70, 40), "noise": 6, "eye": (255, 210, 40),
                        "membrane": (206, 116, 62), "membrane_dark": (150, 70, 40), "vein": (120, 54, 34),
                        "bone": (190, 104, 58), "beak": (226, 196, 120), "beak_tip": (110, 80, 50),
                        "crest": (220, 60, 36), "crest_stripe": (250, 200, 70), "foot": (90, 60, 40)}}


def trex_spec():
    """Tyrannosaurus: the 1933 picture-show monster - upright, tail on the ground, a head full of teeth."""
    parts = [
        P("body", None, (0, -18, 4), (-0.7, 0, 0), [
            B(-11, -12, -30, 22, 23, 34, "skin"),
        ]),
        P("neck", "body", (0, -5, -29), (0.35, 0, 0), [
            B(-7, -8, -13, 14, 15, 15, "skin"),
        ]),
        P("head", "neck", (0, -3, -11), (0.3, 0, 0), [
            B(-8, -9, -18, 16, 14, 20, "skin", eye=(-5.5, -13.5), brow=True),
            B(-6, -7, -30, 12, 9, 12, "snout", teeth="bottom", nostril=True, big_teeth=True),
        ]),
        P("jaw", "head", (0, 4, -7), (0.06, 0, 0), [
            B(-5.5, 0, -23, 11, 5, 24, "jaw", teeth="top", big_teeth=True),
        ]),
        P("tail1", "body", (0, -3, 3), (0.38, 0, 0), [
            B(-9, -9, 0, 18, 17, 24, "skin"),
        ]),
        P("tail2", "tail1", (0, 0.5, 23), (0.14, 0, 0), [
            B(-6, -6, 0, 12, 11, 24, "skin"),
        ]),
        P("tail3", "tail2", (0, 0.5, 23), (0.12, 0, 0), [
            B(-4, -4, 0, 8, 7, 22, "skin"),
        ]),
        P("tail4", "tail3", (0, 0, 21), (0.08, 0, 0), [
            B(-2, -2, 0, 4, 4, 18, "skin"),
        ]),
    ]
    parts += legs("", [
        P("arm_l", "body", (10, 6, -24), (0.9, 0, -0.2), [
            B(-1, -1, -1.5, 3, 9, 3, "skin"),
        ]),
        P("hand_l", "arm_l", (0.5, 8, 0), (-0.8, 0, 0), [
            B(-1, 0, -2, 2, 3, 1, "claws"),
        ]),
        P("thigh_l", None, (10, -18, 4), (-0.3, 0, 0), [
            B(-4.5, -6, -7, 10, 29, 14, "skin"),
        ]),
        P("shin_l", "thigh_l", (0.5, 21.5, -0.5), (0.75, 0, 0), [
            B(-3.5, -1, -3.5, 7, 23, 7, "skin"),
        ]),
        P("foot_l", "shin_l", (0, 21.2, 0), (-0.45, 0, 0), [
            B(-4.5, -1, -11, 9, 3, 14, "foot"),
            B(-4, -0.5, -13, 2, 2, 2, "claw"),
            B(-1, -0.5, -13.5, 2, 2, 2, "claw"),
            B(2, -0.5, -13, 2, 2, 2, "claw"),
        ]),
    ])
    return {"name": "tyrannosaurus", "tex_w": 256, "parts": parts,
            "palette": {"dorsal": (58, 72, 40), "base": (98, 114, 60), "belly": (218, 190, 122),
                        "stripe": (46, 56, 32), "noise": 4, "eye": (255, 120, 30),
                        "claw": (232, 220, 186), "claw_tip": (70, 56, 40), "foot": (66, 60, 40)}}


def plesio_spec():
    """Plesiosaur (elasmosaurus): Loch Ness of Venus - broad body, four paddles, a neck four blocks long."""
    parts = [
        P("body", None, (0, 16, 0), (0, 0, 0), [
            B(-8, -5, -11, 16, 10, 22, "skin"),
        ]),
        P("neck1", "body", (0, -2, -10), (-0.4, 0, 0), [
            B(-3.5, -3.5, -16, 7, 7, 17, "neck"),
        ]),
        P("neck2", "neck1", (0, 0, -15), (0.1, 0, 0), [
            B(-2.5, -2.5, -16, 5, 5, 17, "neck"),
        ]),
        P("neck3", "neck2", (0, 0, -15), (0.12, 0, 0), [
            B(-2, -2, -15, 4, 4, 16, "neck"),
        ]),
        P("neck4", "neck3", (0, 0, -14), (0.0, 0, 0), [
            B(-1.5, -1.5, -13, 3, 3, 14, "neck"),
        ]),
        P("head", "neck4", (0, 0, -12), (0.3, 0, 0), [
            B(-2.5, -2.5, -6, 5, 4, 6, "skin", eye=(-1.5, -3.5)),
            B(-1.5, -1.5, -10, 3, 2, 4, "snout", teeth="bottom"),
        ]),
        P("jaw", "head", (0, 0.5, -5), (0.05, 0, 0), [
            B(-1.5, 0, -5, 3, 1, 5, "jaw", teeth="top"),
        ]),
        P("tail1", "body", (0, -0.5, 10), (0.05, 0, 0), [
            B(-4, -3, 0, 8, 6, 9, "skin"),
        ]),
        P("tail2", "tail1", (0, 0, 8.5), (0.05, 0, 0), [
            B(-2, -2, 0, 4, 4, 10, "skin"),
        ]),
    ]
    parts += legs("", [
        P("flipper_front_l", "body", (7.5, 2.5, -6), (0, -0.45, 0.25), [
            B(0, -0.5, -3, 13, 1, 7, "flipper"),
        ]),
        P("flipper_back_l", "body", (7, 2.5, 7), (0, -0.55, 0.2), [
            B(0, -0.5, -2.5, 10, 1, 6, "flipper"),
        ]),
    ])
    return {"name": "plesiosaur", "tex_w": 128, "parts": parts,
            "palette": {"dorsal": (46, 80, 88), "base": (74, 118, 118), "belly": (200, 204, 174),
                        "blotch": (104, 150, 140), "noise": 5, "eye": (250, 210, 60),
                        "flipper": (56, 92, 98), "flipper_edge": (32, 58, 66)}}


def meganeura_spec():
    """Meganeura: a crow-sized dragonfly - huge jewel eyes, a striped tail and four glassy wings."""
    parts = [
        P("thorax", None, (0, 19, 0), (0, 0, 0), [
            B(-1, -1, -1.5, 2, 2, 3, "dbody"),
        ]),
        P("head", "thorax", (0, 0, -1.5), (0, 0, 0), [
            B(-1.5, -1, -2, 3, 2, 2, "deye"),
        ]),
        P("abdomen", "thorax", (0, 0, 1.5), (0.05, 0, 0), [
            B(-0.5, -0.5, 0, 1, 1, 9, "dtail"),
        ]),
    ]
    parts += legs("", [
        P("wing_front_l", "thorax", (1, -1, -0.5), (0, 0.15, 0), [
            B(0, -0.5, -1, 6, 1, 3, "dwing"),
        ]),
        P("wing_back_l", "thorax", (1, -1, 1.5), (0, -0.2, 0), [
            B(0, -0.5, -1, 5, 1, 3, "dwing"),
        ]),
    ])
    return {"name": "meganeura", "tex_w": 64, "parts": parts, "translucent": True,
            "palette": {"body": (34, 120, 110), "body_dark": (18, 52, 50), "eye": (90, 220, 170),
                        "eye_dark": (20, 90, 90), "wing_a": (120, 230, 210), "wing_b": (170, 120, 240),
                        "vein": (30, 70, 70)}}


def compy_spec():
    """Compsognathus: a chicken-sized dinosaur, all legs, tail and curiosity."""
    parts = [
        P("body", None, (0, 17.5, 0), (-0.15, 0, 0), [
            B(-1.5, -1.5, -3, 3, 3, 5, "skin"),
        ]),
        P("neck", "body", (0, -1, -2.5), (-0.75, 0, 0), [
            B(-1, -1, -3, 2, 2, 3, "skin"),
        ]),
        P("head", "neck", (0, -0.5, -2.5), (0.8, 0, 0), [
            B(-1.5, -1.5, -3, 3, 2, 3, "skin", eye=(-1.0, -1.5), small_eye=True),
            B(-1, -1, -5, 2, 1, 2, "snout"),
        ]),
        P("tail1", "body", (0, -0.5, 2), (0.1, 0, 0), [
            B(-1, -1, 0, 2, 2, 4, "skin"),
        ]),
        P("tail2", "tail1", (0, 0, 3.5), (0.05, 0, 0), [
            B(-0.5, -0.5, 0, 1, 1, 5, "skin"),
        ]),
    ]
    parts += legs("", [
        P("leg_l", None, (1.2, 18.5, 0.5), (0, 0, 0), [
            B(-0.5, 0, -0.5, 1, 5, 1, "skin"),
            B(-0.5, 4.5, -2, 1, 1, 2, "foot"),
        ]),
    ])
    return {"name": "compsognathus", "tex_w": 64, "parts": parts,
            "palette": {"dorsal": (140, 98, 46), "base": (196, 164, 74), "belly": (234, 222, 172),
                        "stripe": (104, 64, 34), "stripe_k": 1.3, "noise": 5, "eye": (255, 120, 40),
                        "claw": (232, 220, 186), "foot": (120, 90, 50)}}


def moth_spec():
    """Spore moth: a fluffy lilac moth of the glowcap hollows with softly glowing eyespots."""
    parts = [
        P("body", None, (0, 20, 0), (0, 0, 0), [
            B(-1.5, -1.5, -2.5, 3, 3, 5, "fur"),
        ]),
        P("head", "body", (0, 0, -2.5), (0, 0, 0), [
            B(-1, -1, -2, 2, 2, 2, "fur", mothface=True),
        ]),
    ]
    parts += legs("", [
        P("antenna_l", "head", (0.5, -1, -1.5), (-1.0, 0, 0.45), [
            B(0, -2, -0.5, 1, 2, 1, "antenna"),
        ]),
        P("wing_l", "body", (1.5, -1.5, -1), (0, -0.1, 0), [
            B(0, -0.5, -2, 5, 1, 5, "mwing"),
        ]),
        P("hindwing_l", "body", (1.5, -1, 1.5), (0, -0.25, 0), [
            B(0, -0.5, -1, 4, 1, 4, "mwing", hind=True),
        ]),
    ])
    return {"name": "spore_moth", "tex_w": 64, "parts": parts, "glow": True,
            "palette": {"fur": (214, 202, 222), "fur_dark": (156, 138, 170), "wing": (190, 172, 210),
                        "wing_edge": (110, 90, 136), "ring": (56, 44, 76), "spot": (120, 255, 220),
                        "antenna": (110, 90, 120), "eye": (30, 20, 40)}}


def ankylo_spec():
    """Ankylosaurus: a walking boulder - basalt hide, ochre armour plates, spikes, and that tail club."""
    parts = [
        P("body", None, (0, 13, 0), (0, 0, 0), [
            B(-8, -6, -9, 16, 10, 18, "skin", armored=True),
            B(-9, -8, -9.5, 18, 2, 19, "plates"),
        ]),
        P("head", "body", (0, -1, -9), (0.2, 0, 0), [
            B(-4, -3, -7, 8, 6, 7, "skin", eye=(-1.5, -4.5)),
            B(-3, -1, -9, 6, 4, 2, "beak"),
            B(4, -3, -4, 2, 2, 2, "spike"), B(-6, -3, -4, 2, 2, 2, "spike"),
        ]),
        P("tail1", "body", (0, -2, 9), (0.1, 0, 0), [
            B(-4, -3, 0, 8, 6, 7, "skin", armored=True),
            B(-4.5, -4, 0, 9, 1, 6, "plates"),
        ]),
        P("tail2", "tail1", (0, 0, 6.5), (0.05, 0, 0), [
            B(-2, -2, 0, 4, 4, 6, "skin"),
        ]),
        P("club", "tail2", (0, 0, 5.5), (0, 0, 0), [
            B(-3.5, -2.5, 0, 7, 5, 5, "club"),
        ]),
    ]
    parts += legs("", [
        # a row of spikes jutting out and up along each flank
        P("spikes_l", "body", (8, -4, 0), (0, 0, -0.45), [
            B(0, -1, -7, 4, 2, 2, "spike"), B(0, -1, -1, 4, 2, 2, "spike"), B(0, -1, 5, 4, 2, 2, "spike"),
        ]),
        P("leg_front_l", None, (5.5, 17, -6), (0, 0, 0), [
            B(-2.5, 0, -2.5, 5, 7, 5, "leg", nails=True),
        ]),
        P("leg_back_l", None, (5.5, 17, 6), (0, 0, 0), [
            B(-3, 0, -3, 6, 7, 6, "leg", nails=True),
        ]),
    ])
    return {"name": "ankylosaurus", "tex_w": 128, "parts": parts,
            "palette": {"dorsal": (66, 64, 62), "base": (96, 92, 86), "belly": (156, 144, 120),
                        "blotch": (80, 78, 74), "noise": 5, "eye": (230, 160, 40), "nail": (222, 206, 160),
                        "plate": (192, 142, 62), "plate_light": (222, 176, 92), "plate_dark": (110, 74, 34),
                        "spike": (236, 220, 170), "spike_base": (150, 110, 56), "beak": (60, 54, 48)}}


def croc_spec():
    """Deinosuchus: a four-block swamp crocodile - armoured back, eyes and nostrils on top for lurking."""
    parts = [
        P("body", None, (0, 19, 0), (0, 0, 0), [
            B(-6, -3, -10, 12, 6, 20, "skin"),
            B(-4, -4, -9, 8, 1, 18, "scutes"),
        ]),
        P("head", "body", (0, -0.5, -10), (0, 0, 0), [
            B(-4, -2.5, -6, 8, 5, 6, "skin"),
            B(-3.5, -3.5, -5, 2, 1, 2, "croceye"), B(1.5, -3.5, -5, 2, 1, 2, "croceye"),
            B(-2.5, -1.5, -20, 5, 3, 14, "snout", teeth="bottom"),
            B(-1, -2.5, -20, 2, 1, 2, "skin", nostril_bump=True),
        ]),
        P("jaw", "head", (0, 1.5, -5), (0, 0, 0), [
            B(-2.5, 0, -15, 5, 2, 15, "jaw", teeth="top"),
        ]),
        P("tail1", "body", (0, -0.5, 10), (0.03, 0, 0), [
            B(-4.5, -2.5, 0, 9, 5, 12, "skin"),
            B(-1.5, -3.5, 0, 3, 1, 12, "scutes"),
        ]),
        P("tail2", "tail1", (0, 0, 11.5), (0.0, 0, 0), [
            B(-3, -2, 0, 6, 4, 11, "skin"),
            B(-1, -3, 0, 2, 1, 11, "scutes"),
        ]),
        P("tail3", "tail2", (0, 0, 10.5), (0.0, 0, 0), [
            B(-1.5, -1.5, 0, 3, 3, 10, "skin"),
        ]),
    ]
    parts += legs("", [
        P("leg_front_l", "body", (5, 1.5, -7), (0, 0, -0.65), [
            B(-1, 0, -1.5, 3, 4, 3, "leg"),
        ]),
        P("leg_back_l", "body", (5, 1.5, 7), (0, 0, -0.65), [
            B(-1, 0, -2, 3, 4, 4, "leg"),
        ]),
    ])
    return {"name": "deinosuchus", "tex_w": 128, "parts": parts,
            "palette": {"dorsal": (44, 56, 34), "base": (70, 86, 50), "belly": (176, 170, 120),
                        "blotch": (54, 68, 40), "noise": 5, "eye": (220, 210, 60), "nail": (200, 190, 150),
                        "scute": (52, 62, 38), "scute_light": (86, 100, 60)}}


SPECS = [raptor_spec(), bronto_spec(), trike_spec(), creeper_spec(), ptero_spec(), trex_spec(),
         plesio_spec(), meganeura_spec(), compy_spec(), moth_spec(), ankylo_spec(), croc_spec()]

# Pose offsets (radians, added to the rest rotation). Used by the Java models and the preview renderer.
POSES = {
    "raptor": {
        # mid-air pounce: legs tucked, arms and claws thrown forward, jaws wide, tail straight back
        "leap": {"body": (0.25, 0, 0), "neck": (0.35, 0, 0), "head": (-0.25, 0, 0), "jaw": (0.6, 0, 0),
                 "arm_l": (-1.2, 0, 0), "arm_r": (-1.2, 0, 0), "hand_l": (-0.4, 0, 0), "hand_r": (-0.4, 0, 0),
                 "thigh_l": (-0.9, 0, 0), "thigh_r": (-0.9, 0, 0), "shin_l": (0.9, 0, 0), "shin_r": (0.9, 0, 0),
                 "tail1": (-0.2, 0, 0), "tail2": (-0.06, 0, 0)},
    },
    "brontosaurus": {
        # grazing: the long neck swings down to the ground
        "graze": {"neck1": (1.4, 0, 0), "neck2": (0.5, 0, 0), "neck3": (0.3, 0, 0), "head": (-0.25, 0, 0)},
    },
    "triceratops": {
        # charge: head low, horns levelled at the enemy, frill raised like a shield
        "charge": {"head": (0.45, 0, 0), "frill": (-0.35, 0, 0), "tail1": (0.25, 0, 0)},
    },
    "pteranodon": {
        # sitting on the canopy: nose up, wings folded along the flanks, standing on its feet
        "perch": {"body": (-0.45, 0, 0, 0, 0.2, 0), "neck": (0.15, 0, 0), "head": (0.25, 0, 0),
                  "wing_l": (0.3, -0.5, 1.3), "wing_r": (0.3, 0.5, -1.3),
                  "wingtip_l": (0, -3.0, 0), "wingtip_r": (0, 3.0, 0),
                  "leg_l": (-0.85, 0, 0), "leg_r": (-0.85, 0, 0), "tail": (0.4, 0, 0)},
        # stooping on prey: wings swept back, beak first
        "dive": {"body": (0.55, 0, 0), "neck": (0.15, 0, 0), "head": (0.1, 0, 0),
                 "wing_l": (0, -0.7, 0.25), "wing_r": (0, 0.7, -0.25),
                 "wingtip_l": (0, -0.6, 0), "wingtip_r": (0, 0.6, 0), "jaw": (0.5, 0, 0)},
    },
    "plesiosaur": {
        # the Loch Ness pose: neck up out of the water in a swan's S, head looking about
        "peek": {"neck1": (-1.05, 0, 0), "neck2": (-0.3, 0, 0), "neck3": (0.35, 0, 0), "neck4": (0.5, 0, 0),
                 "head": (0.55, 0, 0)},
    },
    "ankylosaurus": {
        "graze": {"head": (0.55, 0, 0, 0, 1.5, 0)},
    },
    "deinosuchus": {
        # the strike: head thrown up, jaws gaping
        "lunge": {"head": (-0.3, 0, 0), "jaw": (0.95, 0, 0), "body": (-0.08, 0, 0)},
    },
    "tyrannosaurus": {
        # the roar: head thrown up, jaws wide, puny arms flailing
        "roar": {"body": (-0.1, 0, 0), "neck": (-0.45, 0, 0), "head": (-0.3, 0, 0), "jaw": (0.85, 0, 0),
                 "arm_l": (-0.7, 0, -0.3), "arm_r": (-0.7, 0, 0.3), "tail1": (-0.1, 0, 0)},
    },
}


# ----------------------------------------------------------------------------
# Tiny 3D math (pure python so the generator needs nothing but Pillow)
# ----------------------------------------------------------------------------

def mat_mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def translate(x, y, z):
    return [[1, 0, 0, x], [0, 1, 0, y], [0, 0, 1, z], [0, 0, 0, 1]]


def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return [[1, 0, 0, 0], [0, c, -s, 0], [0, s, c, 0], [0, 0, 0, 1]]


def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return [[c, 0, s, 0], [0, 1, 0, 0], [-s, 0, c, 0], [0, 0, 0, 1]]


def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return [[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]


def apply(m, p, w=1.0):
    return tuple(m[i][0] * p[0] + m[i][1] * p[1] + m[i][2] * p[2] + m[i][3] * w for i in range(3))


def part_matrices(spec, pose=None):
    """Model-space matrix of every part, like ModelPart.translateAndRotate (translate, then Z*Y*X rotation)."""
    pose = pose or {}
    by_name = {p["name"]: p for p in spec["parts"]}
    out = {}

    def get(name):
        if name in out:
            return out[name]
        p = by_name[name]
        parent = get(p["parent"]) if p["parent"] else [[1 if i == j else 0 for j in range(4)] for i in range(4)]
        off = tuple(pose.get(name, (0, 0, 0))) + (0, 0, 0)
        rx, ry, rz = p["rot"][0] + off[0], p["rot"][1] + off[1], p["rot"][2] + off[2]
        px, py, pz = p["pivot"]
        m = mat_mul(parent, translate(px + off[3], py + off[4], pz + off[5]))
        m = mat_mul(m, mat_mul(rot_z(rz), mat_mul(rot_y(ry), rot_x(rx))))
        out[name] = m
        return m

    for p in spec["parts"]:
        get(p["name"])
    return out


# ----------------------------------------------------------------------------
# Box UV layout (identical to ModelPart.Cube)
# ----------------------------------------------------------------------------

def pack(spec):
    """Shelf-packs every box's UV block; stores box['uv'] and the sheet size in the spec."""
    boxes = [b for p in spec["parts"] for b in p["boxes"]]
    width = spec["tex_w"]
    order = sorted(boxes, key=lambda b: (-(b["size"][1] + b["size"][2]), -(2 * (b["size"][0] + b["size"][2]))))
    x = y = shelf = 0
    for b in order:
        w, h, d = b["size"]
        bw, bh = 2 * (w + d), h + d
        if x + bw > width:
            x, y, shelf = 0, y + shelf, 0
        b["uv"] = (x, y)
        x += bw
        shelf = max(shelf, bh)
    used = y + shelf
    height = 16
    while height < used:
        height *= 2
    spec["tex_h"] = height


def faces(b):
    """Yields (face, (u0, v0), (cols, rows), texel_to_local) for the six faces of a box.

    texel_to_local(i, j, fi, fj) gives the local point at fractional texel position (i + fi, j + fj),
    following the vertex/UV assignment of ModelPart.Cube's polygons.
    """
    u, v = b["uv"]
    x0, y0, z0 = b["pos"]
    w, h, d = b["size"]
    x1, y1, z1 = x0 + w, y0 + h, z0 + d
    yield "top", (u + d, v), (w, d), lambda i, j, fi=0.5, fj=0.5: (x0 + i + fi, y0, z1 - (j + fj))
    yield "bottom", (u + d + w, v), (w, d), lambda i, j, fi=0.5, fj=0.5: (x0 + i + fi, y1, z1 - (j + fj))
    yield "west", (u, v + d), (d, h), lambda i, j, fi=0.5, fj=0.5: (x0, y0 + j + fj, z1 - (i + fi))
    yield "north", (u + d, v + d), (w, h), lambda i, j, fi=0.5, fj=0.5: (x0 + i + fi, y0 + j + fj, z0)
    yield "east", (u + d + w, v + d), (d, h), lambda i, j, fi=0.5, fj=0.5: (x1, y0 + j + fj, z0 + i + fi)
    yield "south", (u + 2 * d + w, v + d), (w, h), lambda i, j, fi=0.5, fj=0.5: (x1 - (i + fi), y0 + j + fj, z1)


FACE_NORMALS = {"top": (0, -1, 0), "bottom": (0, 1, 0), "west": (-1, 0, 0), "east": (1, 0, 0),
                "north": (0, 0, -1), "south": (0, 0, 1)}


# ----------------------------------------------------------------------------
# Painting
# ----------------------------------------------------------------------------

def hash3(*k):
    h = 2166136261
    for n in k:
        h = ((h ^ (int(n) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    h ^= h >> 13
    h = (h * 1274126177) & 0xFFFFFFFF
    return (h & 0xFFFF) / 65535.0


def value_noise(x, y, z, scale, seed):
    x, y, z = x / scale, y / scale, z / scale
    ix, iy, iz = math.floor(x), math.floor(y), math.floor(z)
    fx, fy, fz = x - ix, y - iy, z - iz
    fx, fy, fz = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy), fz * fz * (3 - 2 * fz)
    total = 0.0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                wgt = (fx if dx else 1 - fx) * (fy if dy else 1 - fy) * (fz if dz else 1 - fz)
                total += wgt * hash3(ix + dx, iy + dy, iz + dz, seed)
    return total


def lerp(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def mul(c, f):
    return tuple(c[i] * f for i in range(3))


class Texel:
    """Everything the painter knows about one texel."""

    def __init__(self, **kw):
        self.__dict__.update(kw)


def countershade(pal, t):
    """Dorsal colour on top, body colour on the flanks, pale belly underneath (t = model normal / height)."""
    if t.ny < -0.6:
        return pal["dorsal"]
    if t.ny > 0.6:
        return pal["belly"]
    f = t.fy  # 0 at top of the box side, 1 at the bottom
    if f < 0.35:
        return lerp(pal["dorsal"], pal["base"], f / 0.35)
    if f > 0.72:
        return lerp(pal["base"], pal["belly"], (f - 0.72) / 0.28 * 1.4)
    return pal["base"]


def eye_texel(t, eye, pal, big=False):
    """Returns a colour if this texel is part of the eye (side faces only), else None."""
    if t.face not in ("east", "west") or eye is None:
        return None
    ey, ez = eye
    dy, dz = t.ly - ey, t.lz - ez
    if -1 <= dy < 0 and -1.5 <= dz < 1.5:  # heavy brow ridge
        return "brow"
    if 0 <= dy < (2 if big else 1) and -1 <= dz < 1:
        if dz < 0:  # front half of the eye: the pupil
            return (14, 10, 8)
        return pal["eye"]
    return None


def paint(spec, t):
    """Colour (r, g, b, a) of one texel."""
    pal = spec["palette"]
    sp = spec["name"]
    mat = t.mat
    feat = t.feat
    a = 255
    noise = (hash3(t.box_id, t.i, t.j, sum(map(ord, t.face))) - 0.5) * 2 * pal.get("noise", 7)
    speck = hash3(t.box_id, t.i * 7, t.j * 13, 99)

    if mat in ("skin", "neck", "leg", "snout", "jaw"):
        c = countershade(pal, t)
        if mat == "leg" and t.face != "bottom":
            # legs darken towards the feet instead of fading to the belly colour
            c = lerp(pal["base"], mul(pal["dorsal"], 0.95), t.fy * 1.1) if t.face != "top" else pal["dorsal"]
        if "stripe" in pal:
            # tiger stripes over the back, flanks, neck and tail (ochre on the raptor, dark on the T-rex)
            k = pal.get("stripe_k", 0.9 if sp == "raptor" else 0.32)
            band = (t.mz * k + abs(t.mx) * 0.55 * k / 0.9 + t.my * 0.25 * k / 0.9)
            if t.fy < 0.62 or t.ny < -0.6:
                if (math.floor(band) % 4) == 0 and t.ny < 0.5:
                    c = lerp(c, pal["stripe"], 0.9)
            if speck > 0.9:
                c = mul(c, 0.82)
        else:
            blot = value_noise(t.mx, t.my, t.mz, 7.0 if sp == "brontosaurus" else 4.5, 7)
            if (t.fy < 0.65 or t.ny < -0.6) and blot > 0.6:
                c = lerp(c, pal["blotch"], 0.7)
            if speck > 0.92:
                c = mul(c, 0.86)
            if sp == "brontosaurus" and mat != "leg" and (t.ny < -0.6 or t.fy < 0.2) and abs(t.mx) < 3.5:
                c = mul(c, 0.84)  # darker band along the spine
        if mat == "neck" and t.face in ("east", "west", "bottom"):
            if int(math.floor(t.lz)) % 3 == 0:  # wrinkled neck folds
                c = mul(c, 0.9)
        if mat == "leg":
            if t.face != "top" and int(math.floor(t.ly)) % 4 == 3:
                c = mul(c, 0.9)
            if feat.get("nails") and t.face in ("north", "east", "west") and t.fy > 1 - 2.2 / t.h:
                # chunky toenails along the front of the foot
                along = t.lx if t.face == "north" else (t.lz - t.z0)
                front = t.face == "north" or (t.lz - t.z0) < 2
                if front and (int(math.floor(along)) % 3 != 2):
                    c = pal["nail"] if t.fy > 1 - 1.2 / t.h else mul(pal["nail"], 0.85)
            if t.face == "bottom":
                c = mul(pal["dorsal"], 0.7)
        if mat == "snout":
            if feat.get("nostril") and t.face == "top" and (t.lz - t.z0) < 1.2 and abs(t.lx) > 0.4 and abs(t.lx) < 1.6:
                c = (30, 22, 18)
            if feat.get("teeth") == "bottom" and t.face in ("east", "west", "north") and t.ly > t.y1 - 1:
                c = (244, 240, 222) if (t.i % 2 == 0) else (120, 24, 24)
                if feat.get("big_teeth"):
                    c = (244, 240, 222) if (t.i % 3 != 2) else (120, 24, 24)
            if feat.get("big_teeth") and t.face in ("east", "west", "north") and t.y1 - 2 < t.ly < t.y1 - 1:
                c = (236, 230, 206) if t.i % 3 == 0 else (150, 30, 30)
            if feat.get("mouth") and t.face in ("east", "west") and abs(t.ly - (t.y0 + t.h * 0.62)) < 0.5:
                c = mul(c, 0.55)
        if mat == "jaw":
            if feat.get("teeth") == "top" and t.face in ("east", "west", "north") and t.ly < t.y0 + 1:
                c = (244, 240, 222) if (t.i % 2 == 1) else (120, 24, 24)
                if feat.get("big_teeth"):
                    c = (244, 240, 222) if (t.i % 3 != 0) else (120, 24, 24)
            if feat.get("big_teeth") and t.face in ("east", "west", "north") and t.y0 + 1 < t.ly < t.y0 + 2:
                c = (236, 230, 206) if t.i % 3 == 1 else (150, 30, 30)
            if t.face == "top":
                c = (150, 40, 40)  # inside of the mouth
        e = eye_texel(t, feat.get("eye"), pal, big=(sp != "brontosaurus" and not feat.get("small_eye")))
        if e == "brow" and feat.get("small_eye"):
            e = None
        if feat.get("nostril_bump") and t.face == "top":
            c = (24, 24, 16)
        if e == "brow":
            c = mul(c, 0.62)
        elif e is not None:
            c = e
        if feat.get("armored") and t.face in ("east", "west", "north", "south") and t.fy < 0.5:
            # armour scutes running down the upper flanks
            along = (t.lz - t.z0) if t.face in ("east", "west") else (t.lx - t.x0)
            u = (along + (int(t.fy * 3) % 2) * 1.5) % 3 / 3
            c = pal["plate"] if u > 0.3 else pal["plate_dark"]
            if t.fy > 0.38:
                c = pal["plate_dark"]
        # edges of every face a touch darker: reads like a chunky sculpted model at a distance
        if t.edge and t.face != "top":
            c = mul(c, 0.9)
        c = tuple(v + noise for v in c)

    elif mat == "foot":
        c = pal["foot"]
        if t.face in ("north",) or (t.face in ("east", "west") and t.lz - t.z0 < 1):
            c = pal["claw"]
        c = tuple(v + noise for v in c)

    elif mat == "claw":
        c = lerp(pal["claw"], pal["claw_tip"], (t.ly - t.y0) / max(1, t.h) * 0.4)
        if t.ly < t.y0 + 1:
            c = pal["claw_tip"]

    elif mat == "claws":
        # three hooked claws hanging from the hand; gaps are cut out
        c = pal["claw"]
        if t.face in ("north", "south", "top", "bottom"):
            if t.face in ("north", "south") and t.j >= 1 and t.i % 2 == 1:
                a = 0
            if t.ly > t.y1 - 1:
                c = pal["claw_tip"]
        if t.face in ("east", "west"):
            c = pal["claw"] if t.j < t.h - 1 else pal["claw_tip"]
        if t.j == 0:
            c = countershade(pal, t)

    elif mat == "crest":
        # sawtooth fin: bright red with a dark rim, cut-out notches along the top
        c = pal["crest"]
        if t.face == "top":
            a = 0
        elif t.face in ("east", "west", "north", "south"):
            along = (t.lz - t.z0)
            depth = t.ly - t.y0
            k = (along - t.d / 2) / (t.d / 2)
            tooth = int(round(1.6 * k * k)) + (1 if int(math.floor(along)) % 2 == 1 else 0)
            if t.face in ("east", "west") and depth < tooth:
                a = 0
            if t.face in ("north", "south"):
                a = 0 if depth < 1 else 255
            if depth >= t.h - 1:
                c = pal["crest_dark"]
            elif depth < tooth + 1:
                c = (236, 92, 60)
        if t.face == "bottom":
            c = pal["crest_dark"]
        c = tuple(v + noise for v in c)

    elif mat == "horn":
        tip_axis = feat.get("tip", "front")
        if tip_axis == "front":
            f = 1 - (t.lz - t.z0) / t.d  # 1 at the tip
        else:
            f = 1 - (t.ly - t.y0) / t.h
        c = lerp(pal["horn_base"], pal["horn"], f * 1.6)
        if f > 0.85:
            c = mul(pal["horn"], 0.86)
        if t.face == "top" or t.face == "east":
            c = mul(c, 1.04)
        c = tuple(v + noise * 0.6 for v in c)

    elif mat == "beak" and sp == "pteranodon":
        f = 1 - (t.lz - t.z0) / t.d
        c = lerp(pal["beak"], pal["beak_tip"], max(0.0, f - 0.7) / 0.3)
        if t.face == "bottom" or (feat.get("lower") and t.face == "top"):
            c = mul(c, 0.8)
        c = tuple(v + noise for v in c)

    elif mat == "beak":
        # dark horny beak, glossier on top, the upper bill hooking down over the lower one
        f = 1 - (t.lz - t.z0) / t.d  # 1 at the front
        c = lerp(pal["beak"], mul(pal["beak"], 0.6), f)
        if t.face == "top":
            c = mul(c, 1.3)
        if feat.get("hook") and t.face in ("east", "west", "north") and t.ly > t.y1 - 1 and f < 0.6:
            c = (40, 32, 30)
        c = tuple(v + noise for v in c)

    elif mat in EXTRA_PAINTERS:
        c, a = EXTRA_PAINTERS[mat](spec, t, noise)
        if c is None:
            return (0, 0, 0, 0)

    elif mat == "frill":
        c = paint_frill(spec, t)
        if c is None:
            return (0, 0, 0, 0)
        c = tuple(v + noise * 0.7 for v in c)

    else:
        raise ValueError(mat)

    return tuple(max(0, min(255, int(round(v)))) for v in c) + (a,)


def paint_frill(spec, t):
    pal = spec["palette"]
    x0, y0, z0 = t.x0, t.y0, t.z0
    w, h = t.w, t.h
    # position on the whole plate: u across (-1..1, from the centre line), v up (0 bottom .. 1 top)
    hw = t.feat["half_w"]
    u = t.lx / hw
    vv = 1 - (t.ly - y0) / h
    # shield outline: full width low down, rounded over the top (a superellipse), with knobbly
    # epoccipital bumps along the rim. The same outline cuts every face so the plate stays solid.
    v_knee = 0.42
    top = max(0.0, vv - v_knee) / (1 - v_knee)
    r = (abs(u) ** 2.6 + top ** 2.6) ** (1 / 2.6)
    edge_r = 1.02
    knob = int(math.floor(abs(t.lx) + (t.ly - y0))) % 3
    if t.face in ("north", "south"):
        if r > edge_r + (0.0 if knob else 0.08) or (r > edge_r - 0.06 and vv > v_knee and knob == 0):
            return None
    else:
        # rim faces: solid exactly where the neighbouring front texel is
        ua = min(abs(u), 1 - 0.5 / hw)
        va = min(vv, 1 - 0.5 / h)
        ra = (ua ** 2.6 + (max(0.0, va - v_knee) / (1 - v_knee)) ** 2.6) ** (1 / 2.6)
        if ra > edge_r:
            return None
    if t.face == "south":  # back of the frill: plain hide
        c = lerp(spec["palette"]["base"], spec["palette"]["dorsal"], vv)
        return mul(c, 0.95)
    if t.face != "north":
        return pal["frill_dark"] if t.face == "bottom" else (178, 62, 30)
    if r > edge_r - 0.17:
        c = pal["frill_edge"]
        if r > edge_r - 0.05:
            c = pal["frill_dark"]
        return c
    # bold eyespots either side, pulp-poster style
    for sx in (-0.48, 0.48):
        dr = math.hypot((u - sx) * 1.1, (vv - 0.62) * 1.3)
        if dr < 0.12:
            return (24, 30, 40)
        if dr < 0.24:
            return pal["frill_spot"]
        if dr < 0.31:
            return pal["frill_edge"]
    # sunburst rays from the neck
    ang = math.atan2(vv + 0.05, u)
    if int(math.floor(ang * 9 / math.pi)) % 2 == 0 and r > 0.3:
        return mul(pal["frill"], 0.82)
    return pal["frill"]


# ---- materials of the second wave (creeper, pteranodon, T-rex) -------------------------------------------------

CREEPER_FACE = ["........",
                "........",
                ".XX..XX.",
                ".XX..XX.",
                "...XX...",
                "..XXXX..",
                "..XXXX..",
                "..X..X.."]


def _creeper_face(t):
    """True on the dark texels of the classic creeper face (front of the pod)."""
    if t.face != "north" or t.w != 8 or t.h != 8:
        return False
    return CREEPER_FACE[t.j][t.i] == "X"


def p_pod(spec, t, noise):
    pal = spec["palette"]
    mott = value_noise(t.mx, t.my, t.mz, 2.2, 31)
    c = lerp(pal["pod"], pal["pod_dark"], (t.ly - t.y0) / t.h * 0.6 + (0.5 if mott > 0.66 else 0.0))
    if t.face == "top":
        c = lerp(pal["pod"], (176, 220, 110), 0.4)
    if t.face == "bottom":
        c = pal["pod_dark"]
    if hash3(t.box_id, t.i, t.j, 7) > 0.88:
        c = mul(c, 0.8)
    if t.feat.get("face") and _creeper_face(t):
        c = pal["face"]
    return tuple(v + noise for v in c), 255


def p_stalk(spec, t, noise):
    pal = spec["palette"]
    c = pal["stalk"]
    along = t.i if t.face in ("north", "south", "east", "west") else t.j
    if along % 3 == 1:
        c = pal["vein"]
    if t.face == "top":
        c = mul(pal["stalk"], 1.15)
    return tuple(v + noise for v in c), 255


def p_root(spec, t, noise):
    pal = spec["palette"]
    c = pal["root"] if t.face != "top" else lerp(pal["root"], pal["stalk"], 0.5)
    if (t.i + t.j) % 3 == 0:
        c = mul(c, 0.8)
    return tuple(v + noise for v in c), 255


def p_leaf(spec, t, noise):
    """A pointed leaf blade on the flat faces of a 1-texel-thin box; everything outside the outline is cut out."""
    pal = spec["palette"]
    if t.face not in ("top", "bottom"):
        return None, 0
    axis = t.feat["axis"]
    if axis.endswith("z"):
        sa, length, cross, half = abs(t.lz), t.d, t.lx - (t.x0 + t.w / 2), t.w / 2
    else:
        sa, length, cross, half = abs(t.lx), t.w, t.lz - (t.z0 + t.d / 2), t.d / 2
    sa /= length
    width = math.sin(math.pi * min(1.0, sa * 0.92 + 0.08)) ** 0.7 * (1.0 - 0.25 * sa)
    cr = abs(cross) / half
    if cr > width + 0.08:
        return None, 0
    c = pal["leaf"] if t.face == "top" else lerp(pal["leaf"], pal["belly"], 0.35)
    if cr < 0.18:
        c = pal["leaf_dark"]  # midrib
    elif cr > width - 0.2:
        c = pal["leaf_edge"]
    return tuple(v + noise for v in c), 255


def p_bulb(spec, t, noise):
    pal = spec["palette"]
    cx = (t.i + 0.5) / (t.w if t.face in ("north", "south", "top", "bottom") else t.d) - 0.5
    cy = (t.j + 0.5) / (t.h if t.face not in ("top", "bottom") else t.d) - 0.5
    r = math.hypot(cx, cy)
    c = pal["bulb_core"] if r < 0.2 else pal["bulb"] if r < 0.42 else pal["bulb_dark"]
    if t.face == "bottom":
        c = pal["bulb_dark"]
    return c, 255


def p_membrane(spec, t, noise):
    """Leathery wing membrane: flat faces only, trailing edge scalloped between the wing fingers, pointed tip."""
    pal = spec["palette"]
    if t.face not in ("top", "bottom"):
        return None, 0
    span = abs(t.lx) / t.w
    chord = (t.lz - t.z0) / t.d
    if t.feat["part"] == "tip":
        limit = (1.0 - span) ** 0.85
    else:
        limit = 1.0 - 0.12 * span - 0.1 * abs(math.sin(span * math.pi * 2.0))
    if chord > limit + 0.04:
        return None, 0
    c = pal["membrane"] if t.face == "bottom" else pal["membrane_dark"]
    if abs(chord - (0.42 + 0.12 * span)) < 0.5 / t.d or abs(chord - 0.15) < 0.5 / t.d:
        c = pal["vein"]
    if chord > limit - 1.2 / t.d:
        c = mul(c, 0.78)
    return tuple(v + noise for v in c), 255


def p_bone(spec, t, noise):
    pal = spec["palette"]
    c = pal["bone"] if t.face != "top" else mul(pal["bone"], 0.85)
    if abs(t.lx) > t.w - 1.5:
        c = mul(c, 0.75)  # knuckle
    return tuple(v + noise for v in c), 255


def p_pcrest(spec, t, noise):
    pal = spec["palette"]
    c = pal["crest"]
    if t.face in ("east", "west") and int(math.floor((t.lz - t.z0) + (t.ly - t.y0))) % 4 == 0:
        c = pal["crest_stripe"]
    if t.face in ("east", "west") and t.ly < t.y0 + 1 and (t.lz - t.z0) > t.d - 3:
        return None, 0  # tapering top edge at the tip
    return tuple(v + noise for v in c), 255


def p_pfoot(spec, t, noise):
    c = spec["palette"]["foot"]
    if t.face == "north":
        c = (40, 30, 24)
    return tuple(v + noise for v in c), 255


def p_cskin(spec, t, noise):
    """Creeper hide as Venus flora: vanilla-style green mottling in teal-olive, branching ochre veins."""
    pal = spec["palette"]
    m = hash3(t.box_id, t.i, t.j, sum(map(ord, t.face)))
    c = pal["skin_light"] if m > 0.78 else pal["skin_dark"] if m < 0.22 else pal["skin"]
    if pal.get("veins", True):
        ridge = abs(value_noise(t.mx, t.my, t.mz, 3.2, 41) - 0.5)
        if ridge < 0.022:
            c = pal["vein"]
    if t.face == "bottom":
        c = mul(c, 0.8)
    if t.feat.get("toes") and t.face in ("north", "south", "east", "west"):
        if t.ly > t.y1 - 2:  # root toes at the bottom of each leg
            c = pal["root"] if t.i % 2 == 0 else pal["root_dark"]
            if t.ly < t.y1 - 1 and t.i % 2 == 1:
                c = mul(pal["skin_dark"], 0.9)
    if t.feat.get("toes") and t.face == "bottom":
        c = pal["root_dark"]
    if t.feat.get("face") and _creeper_face(t):
        c = pal["face"]
    return tuple(v + noise * 0.5 for v in c), 255


def p_fringe(spec, t, noise):
    """A 2 px leaf fringe: flat faces only, the outer row cut into points."""
    pal = spec["palette"]
    if t.face not in ("top", "bottom"):
        return None, 0
    axis = t.feat["axis"]
    out = abs(t.lz) if axis.endswith("z") else abs(t.lx)
    along = t.i if axis.endswith("z") else t.j
    if out > 1.0 and along % 2 == 1:
        return None, 0
    c = pal["leaf"] if out <= 1.0 else pal["leaf_edge"]
    if t.face == "bottom":
        c = mul(c, 0.8)
    return tuple(v + noise for v in c), 255


EXTRA_PAINTERS = {"cskin": p_cskin, "fringe": p_fringe, "pod": p_pod, "stalk": p_stalk, "bulbstem": p_stalk, "root": p_root, "leaf": p_leaf,
                  "bulb": p_bulb, "membrane": p_membrane, "bone": p_bone, "pcrest": p_pcrest, "pfoot": p_pfoot}


# ---- materials of the third wave (sea, swamp, highlands and the small life) --------------------------------------

def _flat_cut(t, along, across, shape):
    """Flat faces of a 1-thick plate keep texels inside shape(along 0..1, across 0..1); rim faces are cut away."""
    if t.face not in ("top", "bottom"):
        return False
    return shape(along, across)


def p_flipper(spec, t, noise):
    pal = spec["palette"]
    span = abs(t.lx) / t.w
    chord = (t.lz - t.z0) / t.d
    if t.face not in ("top", "bottom"):
        return None, 0
    if abs(chord - 0.5) > 0.5 * (1.0 - span ** 2.2) + 0.05:  # rounded, tapering paddle
        return None, 0
    c = pal["flipper"] if t.face == "top" else lerp(pal["flipper"], pal["belly"], 0.5)
    if chord > 0.75:
        c = pal["flipper_edge"]
    return tuple(v + noise for v in c), 255


def p_dbody(spec, t, noise):
    pal = spec["palette"]
    c = pal["body"] if t.face != "bottom" else pal["body_dark"]
    return tuple(v + noise * 0.5 for v in c), 255


def p_deye(spec, t, noise):
    pal = spec["palette"]
    side = t.face in ("east", "west") or (t.face in ("north", "top") and abs(t.lx) > 0.6)
    c = pal["eye"] if side else pal["eye_dark"]
    if t.face == "bottom":
        c = pal["body_dark"]
    return c, 255


def p_dtail(spec, t, noise):
    pal = spec["palette"]
    c = pal["body"] if int(math.floor(t.lz)) % 2 == 0 else pal["body_dark"]
    if t.lz > t.z1 - 1:
        c = pal["eye"]
    return c, 255


def p_dwing(spec, t, noise):
    """Glassy dragonfly wing (drawn translucent): teal-to-violet sheen, dark veins, a dark spot near the tip."""
    pal = spec["palette"]
    if t.face not in ("top", "bottom"):
        return None, 0
    span = abs(t.lx) / t.w
    c = lerp(pal["wing_a"], pal["wing_b"], span)
    a = 140
    if span > 0.8 and (t.lz - t.z0) < 1.0:
        c, a = pal["vein"], 220  # pterostigma
    elif (t.lz - t.z0) < 1.0:
        c, a = lerp(pal["vein"], c, 0.35), 210  # leading-edge vein
    elif (t.lz - t.z0) > t.d - 1.0 and span > 0.15:
        a = 110
    return c, a


def p_fur(spec, t, noise):
    pal = spec["palette"]
    c = pal["fur"] if hash3(t.box_id, t.i, t.j, 11) > 0.35 else pal["fur_dark"]
    if t.feat.get("mothface") and t.face == "north":
        c = pal["eye"] if t.j == 0 else pal["fur_dark"]
    return tuple(v + noise for v in c), 255


def p_antenna(spec, t, noise):
    return spec["palette"]["antenna"], 255


def _moth_spot(t):
    """Eyespot centre of a moth wing in wing-local units (span 0..1, chord 0..1)."""
    span = abs(t.lx) / t.w
    chord = (t.lz - t.z0) / t.d
    return math.hypot((span - 0.55) * t.w, (chord - 0.5) * t.d)


def p_mwing(spec, t, noise):
    pal = spec["palette"]
    if t.face not in ("top", "bottom"):
        return None, 0
    span = abs(t.lx) / t.w
    chord = (t.lz - t.z0) / t.d
    if t.feat.get("hind"):
        inside = math.hypot(span * 0.9, (chord - 0.45) * 1.3) < 1.0
    else:
        inside = chord < 0.25 + 0.9 * span + 0.2 and math.hypot(span - 0.1, chord - 0.5) < 1.05
    if not inside:
        return None, 0
    c = pal["wing"] if t.face == "top" else lerp(pal["wing"], pal["fur"], 0.5)
    r = _moth_spot(t)
    if t.face == "top" and r < 1.6:
        c = pal["spot"] if r < 0.8 else pal["ring"]
    elif span > 0.82:
        c = pal["wing_edge"]
    return tuple(v + noise * 0.6 for v in c), 255


def p_plates(spec, t, noise):
    """Osteoderm armour: staggered rows of big ochre scutes, each with a raised boss, soft dark grout."""
    pal = spec["palette"]
    if t.face == "top":
        size = 4.0
        row = int(math.floor((t.lz - t.z0) / size))
        off = (row % 2) * size / 2
        u = ((t.lx - t.x0 + off) % size) / size
        v = ((t.lz - t.z0) % size) / size
        boss = math.hypot(u - 0.55, v - 0.55)
        c = pal["plate_light"] if boss < 0.2 else pal["plate"]
        if u < 0.2 or v < 0.2:
            c = lerp(pal["plate"], pal["plate_dark"], 0.7)
    else:
        c = pal["plate"] if t.j == 0 else pal["plate_dark"]
    return tuple(v + noise for v in c), 255


def p_spike(spec, t, noise):
    pal = spec["palette"]
    out = abs(t.lx) - min(abs(t.x0), abs(t.x1)) if abs(t.x0) > 1 or abs(t.x1) > 1 else 0
    f = out / max(1.0, t.w)
    c = lerp(pal["spike_base"], pal["spike"], f * 1.4)
    return tuple(v + noise * 0.5 for v in c), 255


def p_club(spec, t, noise):
    pal = spec["palette"]
    lump = value_noise(t.lx * 1.7, t.ly * 1.7, t.lz * 1.7, 1.5, 21)
    c = pal["plate_light"] if lump > 0.62 else pal["plate"] if lump > 0.38 else pal["plate_dark"]
    return tuple(v + noise for v in c), 255


def p_scutes(spec, t, noise):
    pal = spec["palette"]
    ridge = (int(math.floor(t.lx - t.x0)) % 2 == 0)
    c = pal["scute_light"] if ridge and int(math.floor(t.lz)) % 3 != 0 else pal["scute"]
    return tuple(v + noise for v in c), 255


def p_croceye(spec, t, noise):
    pal = spec["palette"]
    if t.face in ("top", "north", "east", "west"):
        c = (20, 20, 10) if (t.face == "top" and t.i == 0) else pal["eye"]
    else:
        c = pal["dorsal"]
    return c, 255


EXTRA_PAINTERS.update({"flipper": p_flipper, "dbody": p_dbody, "deye": p_deye, "dtail": p_dtail, "dwing": p_dwing,
                       "fur": p_fur, "antenna": p_antenna, "mwing": p_mwing, "plates": p_plates, "spike": p_spike,
                       "club": p_club, "scutes": p_scutes, "croceye": p_croceye})


# ---- Dr. Oinstein's atomic robots ---------------------------------------------------------------------------------

ROBOT_PAL = {"chrome": (196, 206, 214), "chrome_dark": (110, 122, 134), "chrome_light": (244, 248, 252),
             "steel": (128, 136, 140), "steel_dark": (78, 84, 90), "rivet": (60, 64, 70), "rivet_light": (210, 214, 218),
             "gun": (58, 62, 70), "gun_light": (96, 102, 112), "hazard_y": (236, 186, 40), "hazard_k": (34, 32, 30),
             "glass": (190, 236, 240), "core": (120, 255, 190), "core_hot": (230, 255, 240), "lens": (255, 40, 30),
             "lens_hot": (255, 200, 170), "orbit": (90, 220, 255), "electron": (220, 250, 255), "beacon": (255, 70, 50),
             "visor": (255, 90, 40), "noise": 3}


def sentry_spec():
    """Atomic Sentry: a chrome flying saucer on watch - one red eye, a blaster below, a glass reactor dome on top and
    two glowing atom orbits spinning round it."""
    parts = [
        P("body", None, (0, 15, 0), (0, 0, 0), [
            B(-7, -1.5, -7, 14, 3, 14, "band"),
            B(-5, -4.5, -5, 10, 3, 10, "chrome", rivets=True),
            B(-5, 1.5, -5, 10, 2, 10, "chrome"),
            B(-3, -6.5, -3, 6, 2, 6, "glass"),
            B(-2, 3.5, -2, 4, 1, 4, "steel"),
        ]),
        P("core", "body", (0, -5.5, 0), (0, 0, 0), [
            B(-1.5, -1.5, -1.5, 3, 3, 3, "core"),
        ]),
        P("eye", "body", (0, -2.5, -5), (0, 0, 0), [
            B(-2, -1.5, -1.5, 4, 3, 2, "lens"),
        ]),
        P("eye_flare", "eye", (0, 0, 0), (0, 0, 0), [
            B(-3, -2.5, -2.5, 6, 5, 1, "flare"),
        ]),
        P("barrel", "body", (0, 3, -2), (0.3, 0, 0), [
            B(-1, -1, -6, 2, 2, 6, "gun"),
            B(-1.5, -1.5, -7, 3, 3, 1, "muzzle"),
        ]),
        P("antenna", "body", (3, -4.5, 3), (0, 0, 0.3), [
            B(-0.5, -5, -0.5, 1, 5, 1, "steel"),
            B(-1, -6, -1, 2, 1, 2, "beacon"),
        ]),
        P("orbit_a", None, (0, 15, 0), (0.5, 0, 0.3), []),
        P("ring_a", "orbit_a", (0, 0, 0), (0, 0, 0), [
            B(-9, -0.5, -9, 18, 1, 1, "orbit"), B(-9, -0.5, 8, 18, 1, 1, "orbit"),
            B(-9, -0.5, -8, 1, 1, 16, "orbit"), B(8, -0.5, -8, 1, 1, 16, "orbit"),
            B(-10, -1, -1, 2, 2, 2, "electron"),
        ]),
        P("orbit_b", None, (0, 15, 0), (-0.5, 0, -0.3), []),
        P("ring_b", "orbit_b", (0, 0, 0), (0, 0.78, 0), [
            B(-9, -0.5, -9, 18, 1, 1, "orbit"), B(-9, -0.5, 8, 18, 1, 1, "orbit"),
            B(-9, -0.5, -8, 1, 1, 16, "orbit"), B(8, -0.5, -8, 1, 1, 16, "orbit"),
            B(8, -1, -1, 2, 2, 2, "electron"),
        ]),
    ]
    return {"name": "atomic_sentry", "tex_w": 128, "parts": parts, "glow": True, "palette": dict(ROBOT_PAL)}


def automaton_spec():
    """Atomic Automaton: a 1950s picture-show robot - barrel chest with an atom-core window, bucket head, visor slit."""
    parts = [
        P("body", None, (0, 10, 0), (0, 0, 0), [
            B(-7, -14, -4.5, 14, 13, 9, "steel", rivets=True, core_window=True),
            B(-5, -1, -3.5, 10, 3, 7, "hazard"),
        ]),
        P("head", "body", (0, -14, 0), (0, 0, 0), [
            B(-4.5, -8, -4.5, 9, 8, 9, "chrome", visor=True, rivets=True),
            B(-3.5, -9, -3.5, 7, 1, 7, "chrome"),
            B(-5.5, -6, -1, 1, 3, 2, "gun"), B(4.5, -6, -1, 1, 3, 2, "gun"),
        ]),
        P("antenna", "head", (0, -9, 0), (0, 0, 0), [
            B(-0.5, -3, -0.5, 1, 3, 1, "steel"),
            B(-1, -4, -1, 2, 1, 2, "beacon"),
        ]),
    ]
    parts += legs("", [
        P("arm_l", "body", (7, -12, 0), (0, 0, -0.08), [
            B(0, -2, -2.5, 3, 4, 5, "chrome"),
            B(0.5, 2, -1.5, 2, 6, 3, "accordion"),
        ]),
        P("forearm_l", "arm_l", (1.5, 8, 0), (-0.15, 0, 0), [
            B(-1.5, 0, -2, 3, 6, 4, "steel", rivets=True),
        ]),
        P("claw_l", "forearm_l", (0, 6, 0), (0, 0, 0), [
            B(-1.5, 0, -2.5, 3, 3, 1, "rclaw"), B(-1.5, 0, 1.5, 3, 3, 1, "rclaw"),
        ]),
        P("leg_l", None, (3.5, 12, 0), (0, 0, 0), [
            B(-2.5, 0, -2.5, 5, 6, 5, "gun"),
        ]),
        P("shin_l", "leg_l", (0, 6, 0), (0, 0, 0), [
            B(-2, 0, -2, 4, 5, 4, "chrome", rivets=True),
            B(-3, 5, -4, 6, 1, 7, "gun"),
        ]),
    ])
    return {"name": "atomic_automaton", "tex_w": 128, "parts": parts, "glow": True, "palette": dict(ROBOT_PAL)}


def _rivet(t):
    """Rivet heads along the edges of a face, every 3 texels."""
    cols = t.w if t.face in ("north", "south", "top", "bottom") else t.d
    rows = t.h if t.face not in ("top", "bottom") else t.d
    on_edge = t.i in (0, cols - 1) or t.j in (0, rows - 1)
    return on_edge and (t.i + t.j) % 3 == 0 and cols > 3 and rows > 3


def p_metal(spec, t, noise):
    pal = spec["palette"]
    mat = t.mat
    rows = t.h if t.face not in ("top", "bottom") else t.d
    cols = t.w if t.face in ("north", "south", "top", "bottom") else t.d
    fy = t.j / max(1, rows - 1)
    if mat == "chrome":
        c = lerp(pal["chrome_light"], pal["chrome_dark"], fy * 0.9)
        if abs(t.i - cols * 0.3) < 1.0 and t.face not in ("top", "bottom"):
            c = pal["chrome_light"]  # the specular streak
        if t.face == "top":
            c = pal["chrome_light"]
    elif mat == "steel":
        c = lerp(pal["steel"], pal["steel_dark"], fy * 0.5)
        if t.j % 5 == 4 and t.face not in ("top", "bottom"):
            c = pal["steel_dark"]  # plate seams
    elif mat == "gun":
        c = pal["gun_light"] if hash3(t.box_id, t.i, t.j, 4) > 0.85 else pal["gun"]
        if t.j == 0:
            c = pal["gun_light"]
    elif mat == "accordion":
        c = pal["gun"] if t.j % 2 == 0 else pal["chrome_dark"]
    elif mat == "rclaw":
        c = pal["chrome_dark"] if t.j < rows - 1 else pal["gun"]
    elif mat in ("band", "hazard"):
        c = pal["hazard_y"] if int(math.floor((t.i + t.j) / 2)) % 2 == 0 else pal["hazard_k"]
        if t.face in ("top", "bottom"):
            c = pal["steel_dark"]
        if mat == "band" and t.j in (0, rows - 1):
            c = pal["chrome_dark"]
    else:
        c = pal["steel"]
    if t.feat.get("rivets") and _rivet(t):
        c = pal["rivet"] if (t.i + t.j) % 2 else pal["rivet_light"]
    if t.feat.get("core_window") and t.face == "north":
        r = math.hypot(t.i + 0.5 - cols / 2, t.j + 0.5 - rows * 0.42)
        if r < 3.6:
            c = _core_glow(pal, t, cols, rows) if r < 2.8 else pal["chrome_light"]
    if t.feat.get("visor") and t.face in ("north", "east", "west") and t.j in (3, 4):
        if t.face == "north" and 0 < t.i < cols - 1 or t.face != "north" and t.i < 3:
            c = pal["visor"] if t.j == 3 else mul(pal["visor"], 0.7)
    return tuple(v + noise for v in c), 255


def _core_glow(pal, t, cols, rows):
    """Atom emblem in the chest window: a bright nucleus with an orbit ring."""
    dx = t.i + 0.5 - cols / 2
    dy = t.j + 0.5 - rows * 0.42
    r = math.hypot(dx, dy)
    if r < 1.0:
        return pal["core_hot"]
    if abs(r - 2.1) < 0.6 or abs(dx) < 0.6 or abs(dy) < 0.6:
        return pal["core"]
    return mul(pal["core"], 0.45)


def p_glow_parts(spec, t, noise):
    """Self-lit bits (also drawn in the base texture, so they read even without the glow layer)."""
    pal = spec["palette"]
    m = t.mat
    if m == "core":
        return (pal["core_hot"] if t.j == 1 and t.i == 1 else pal["core"]), 255
    if m == "lens":
        if t.face == "north":
            r = math.hypot(t.i - 1.5, t.j - 1.5)
            return (pal["lens_hot"] if r < 0.8 else pal["lens"] if r < 1.8 else (120, 10, 10)), 255
        return pal["gun"], 255
    if m == "flare":
        return None, 0  # only in the glow layer, and only while alarmed
    if m == "orbit":
        return pal["orbit"], 255
    if m == "electron":
        return pal["electron"], 255
    if m == "beacon":
        return pal["beacon"], 255
    if m == "muzzle":
        return ((255, 120, 60) if t.face == "north" and t.i == 1 and t.j == 1 else pal["gun"]), 255
    if m == "glass":
        cols = t.w if t.face in ("north", "south", "top", "bottom") else t.d
        rows = t.h if t.face not in ("top", "bottom") else t.d
        edge = t.i in (0, cols - 1) or t.j in (0, rows - 1)
        if edge:
            return pal["chrome_dark"], 255
        if t.i == t.j:
            return pal["glass"], 255  # glint
        return None, 0  # clear: the glowing core shows through
    raise ValueError(m)


def robot_glow(spec, t):
    pal = spec["palette"]
    if t.mat in ("core", "orbit", "electron", "beacon"):
        c, _ = p_glow_parts(spec, t, 0)
        return c + (255,)
    if t.mat == "lens" and t.face == "north":
        c, _ = p_glow_parts(spec, t, 0)
        return c + (255,)
    if t.mat == "flare" and t.face in ("north", "south"):
        r = math.hypot(t.i - 2.5, t.j - 2.5)
        if r < 3.2:
            return (255, 80, 60, 255) if r > 1.5 else (255, 230, 210, 255)
    if t.mat == "muzzle" and t.face == "north" and t.i == 1 and t.j == 1:
        return (255, 140, 70, 255)
    if t.feat.get("core_window") and t.face == "north":
        r = math.hypot(t.i + 0.5 - t.w / 2, t.j + 0.5 - t.h * 0.42)
        if r < 2.8:
            return _core_glow(pal, t, t.w, t.h) + (255,)
    if t.feat.get("visor") and t.face in ("north", "east", "west") and t.j == 3:
        cols = t.w if t.face == "north" else t.d
        if t.face == "north" and 0 < t.i < cols - 1 or t.face != "north" and t.i < 3:
            return pal["visor"] + (255,)
    return None


EXTRA_PAINTERS.update({m: p_metal for m in ("chrome", "steel", "gun", "accordion", "rclaw", "band", "hazard")})
EXTRA_PAINTERS.update({m: p_glow_parts for m in ("core", "lens", "flare", "orbit", "electron", "beacon", "muzzle", "glass")})

SPECS += [sentry_spec(), automaton_spec()]


def glow_texel(spec, t):
    """Emissive overlay (drawn full-bright in game): spore bulbs, eyes, wing spots, robot cores and lenses."""
    if spec["name"] in ("atomic_sentry", "atomic_automaton"):
        return robot_glow(spec, t)
    if t.mat == "bulb":
        c, _ = p_bulb(spec, t, 0)
        return c + (255,)
    if t.mat == "mwing" and t.face == "top" and _moth_spot(t) < 0.8:
        return (150, 255, 225, 255)
    if t.mat in ("pod", "cskin") and t.feat.get("face") and _creeper_face(t) and t.j in (2, 3):
        return (150, 255, 110, 255)
    return None


def build_texture(spec, glow=False):
    pack(spec)
    img = Image.new("RGBA", (spec["tex_w"], spec["tex_h"]), (0, 0, 0, 0))
    mats = part_matrices(spec)
    box_id = 0
    for part in spec["parts"]:
        m = mats[part["name"]]
        for b in part["boxes"]:
            box_id += 1
            x0, y0, z0 = b["pos"]
            w, h, d = b["size"]
            for face, (u0, v0), (cols, rows), to_local in faces(b):
                n = apply(m, FACE_NORMALS[face], 0.0)
                for j in range(rows):
                    for i in range(cols):
                        lx, ly, lz = to_local(i, j)
                        mx, my, mz = apply(m, (lx, ly, lz))
                        fy = (ly - y0) / h if h else 0.0
                        edge = i == 0 or j == 0 or i == cols - 1 or j == rows - 1
                        t = Texel(mat=b["mat"], feat=b["feat"], face=face, i=i, j=j, lx=lx, ly=ly, lz=lz,
                                  mx=mx, my=my, mz=mz, nx=n[0], ny=n[1], nz=n[2], fy=fy, edge=edge,
                                  x0=x0, y0=y0, z0=z0, x1=x0 + w, y1=y0 + h, z1=z0 + d, w=w, h=h, d=d,
                                  box_id=box_id)
                        if glow:
                            px = glow_texel(spec, t)
                            if px:
                                img.putpixel((u0 + i, v0 + j), tuple(max(0, min(255, int(round(v)))) for v in px))
                        else:
                            img.putpixel((u0 + i, v0 + j), paint(spec, t))
    return img


# ----------------------------------------------------------------------------
# Java geometry
# ----------------------------------------------------------------------------

def jf(v):
    s = repr(round(float(v), 4))
    return s + "F"


def java_layer(spec):
    name = spec["name"]
    lines = [f"    /** {name}: {len(spec['parts'])} parts, texture {spec['tex_w']}x{spec['tex_h']}. */",
             f"    public static LayerDefinition {java_name(name)}() {{",
             "        MeshDefinition mesh = new MeshDefinition();",
             "        PartDefinition root = mesh.getRoot();"]
    for p in spec["parts"]:
        cubes = "CubeListBuilder.create()"
        for b in p["boxes"]:
            (x, y, z), (w, h, d), (u, v) = b["pos"], b["size"], b["uv"]
            cubes += f"\n                .texOffs({u}, {v}).addBox({jf(x)}, {jf(y)}, {jf(z)}, {jf(w)}, {jf(h)}, {jf(d)})"
        parent = p["parent"] or "root"
        pose = (f"PartPose.offsetAndRotation({jf(p['pivot'][0])}, {jf(p['pivot'][1])}, {jf(p['pivot'][2])}, "
                f"{jf(p['rot'][0])}, {jf(p['rot'][1])}, {jf(p['rot'][2])})")
        lines.append(f"        PartDefinition {p['name']} = {parent}.addOrReplaceChild(\"{p['name']}\", {cubes},")
        lines.append(f"                {pose});")
    lines.append(f"        return LayerDefinition.create(mesh, {spec['tex_w']}, {spec['tex_h']});")
    lines.append("    }")
    return "\n".join(lines)


def java_name(name):
    return name


def java_poses():
    out = []
    for species, poses in POSES.items():
        for pose, parts in poses.items():
            const = f"{species.upper()}_{pose.upper()}"
            entries = ",\n            ".join(
                f"Map.entry(\"{k}\", new float[]{{{', '.join(jf(x) for x in v)}}})" for k, v in parts.items())
            out.append(f"    public static final Map<String, float[]> {const} = Map.ofEntries(\n            {entries});")
    return "\n\n".join(out)


def write_java():
    body = "\n\n".join(java_layer(s) for s in SPECS)
    src = f"""package com.replecant.retrocosmos.dinosaur.client;

import java.util.Map;
import java.util.function.Function;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;

/**
 * Box geometry of the Venus dinosaurs. GENERATED by tools/dinosaurs.py from the same box list that paints
 * their textures - edit the spec there and re-run tools/gen_resources.py instead of editing this file.
 */
@SuppressWarnings("unused")
public final class DinoGeometry {{
    private DinoGeometry() {{}}

{body}

    // ---- key poses, as rotation offsets added on top of the rest pose ----

{java_poses()}

    /** Blends a key pose in: every listed part is rotated (and optionally moved) by amount * its offset. */
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
                if (r.length > 3) {{
                    part.x += r[3] * amount;
                    part.y += r[4] * amount;
                    part.z += r[5] * amount;
                }}
            }}
        }}
    }}
}}
"""
    path = os.path.join(JAVA_DIR, "DinoGeometry.java")
    os.makedirs(JAVA_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(src)


# ----------------------------------------------------------------------------
# Spawn eggs
# ----------------------------------------------------------------------------

EGG_ROWS = [
    "......####......",
    ".....######.....",
    "....########....",
    "....########....",
    "...##########...",
    "...##########...",
    "..############..",
    "..############..",
    "..############..",
    "..############..",
    "..############..",
    "..############..",
    "...##########...",
    "...##########...",
    "....########....",
    "......####......",
]

EGGS = {
    # name: (shell, spots) - chunky vanilla-style two-colour eggs
    "raptor": ((86, 150, 60), (222, 156, 44)),
    "brontosaurus": ((124, 130, 90), (204, 200, 156)),
    "triceratops": ((96, 124, 118), (238, 102, 40)),
    "venus_creeper": ((110, 180, 70), (232, 250, 130)),
    "pteranodon": ((180, 94, 52), (226, 60, 36)),
    "tyrannosaurus": ((88, 102, 54), (40, 46, 28)),
    "plesiosaur": ((74, 118, 118), (200, 204, 174)),
    "meganeura": ((34, 120, 110), (150, 120, 240)),
    "compsognathus": ((196, 164, 74), (104, 64, 34)),
    "spore_moth": ((196, 180, 214), (120, 255, 220)),
    "ankylosaurus": ((96, 92, 86), (192, 142, 62)),
    "deinosuchus": ((70, 86, 50), (176, 170, 120)),
    "atomic_sentry": ((196, 206, 214), (230, 40, 30)),
    "atomic_automaton": ((110, 118, 124), (236, 186, 40)),
}

EGG_SPOTS = [(5, 3), (9, 4), (4, 7), (8, 8), (11, 7), (6, 11), (10, 11), (7, 5), (12, 10), (4, 10)]


def egg(shell, spots):
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    inside = {(x, y) for y, row in enumerate(EGG_ROWS) for x, ch in enumerate(row) if ch == "#"}
    for (x, y) in inside:
        c = shell
        # shading: light upper-left, dark lower-right
        shade = 1.0 + 0.12 * ((7.5 - x) + (7.5 - y)) / 8
        c = mul(c, shade)
        edge = any((x + dx, y + dy) not in inside for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if edge:
            c = mul(shell, 0.55)
        img.putpixel((x, y), tuple(max(0, min(255, int(v))) for v in c) + (255,))
    for (sx, sy) in EGG_SPOTS:
        for dx, dy in ((0, 0), (1, 0), (0, 1)):
            p = (sx + dx, sy + dy)
            if p in inside and not any((p[0] + a, p[1] + b) not in inside for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                img.putpixel(p, spots + (255,))
    for p in ((5, 2), (4, 3), (4, 4)):  # glossy highlight
        img.putpixel(p, (255, 255, 255, 255) if p != (4, 4) else mul_px(shell, 1.5))
    return img


def mul_px(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c) + (255,)


# ----------------------------------------------------------------------------
# Tyrannosaurus trophies: skull block (block-model elements), fang, fang dagger
# ----------------------------------------------------------------------------

# block-model space (y up), facing north = the snout points to -z
SKULL = [
    ((2, 0, 2), (14, 2, 14), "plinth"),
    ((5, 2, 1), (11, 4, 12), "jaw"),
    ((4, 4, 1), (12, 9, 6), "snout"),
    ((6, 9, 1), (10, 10, 6), "ridge"),
    ((3, 4, 6), (13, 12, 15), "cranium"),
    ((3, 12, 6), (5, 13, 9), "horn"),
    ((11, 12, 6), (13, 13, 9), "horn"),
]
SKULL_TEX = 64


def skull_faces(frm, to):
    """(face, cols, rows, texel -> (x, y, z)) following the block-model default UV orientation (FaceBakery)."""
    (x1, y1, z1), (x2, y2, z2) = frm, to
    w, h, d = x2 - x1, y2 - y1, z2 - z1
    yield "north", w, h, lambda i, j: (x2 - i - 0.5, y2 - j - 0.5, z1)
    yield "south", w, h, lambda i, j: (x1 + i + 0.5, y2 - j - 0.5, z2)
    yield "east", d, h, lambda i, j: (x2, y2 - j - 0.5, z2 - i - 0.5)
    yield "west", d, h, lambda i, j: (x1, y2 - j - 0.5, z1 + i + 0.5)
    yield "up", w, d, lambda i, j: (x1 + i + 0.5, y2, z1 + j + 0.5)
    yield "down", w, d, lambda i, j: (x1 + i + 0.5, y1, z2 - j - 0.5)


def paint_skull(mat, face, x, y, z, i, j):
    bone = (230, 218, 186)
    stain = value_noise(x * 2.1, y * 2.1, z * 2.1, 3.0, 77)
    c = lerp(bone, (176, 152, 110), max(0.0, stain - 0.45) * 1.6)
    if face == "up":
        c = mul(c, 1.05)
    elif face == "down":
        c = mul(c, 0.75)
    if hash3(int(x * 4), int(y * 4), int(z * 4), 5) > 0.93:
        c = mul(c, 0.82)  # pits and cracks
    if mat == "plinth":
        c = (96, 60, 38) if int(x + z * 0.3) % 3 else (78, 48, 30)
        if face == "up":
            c = (110, 70, 44) if (2.5 < x < 13.5 and 2.5 < z < 13.5) else (70, 42, 26)
        if face == "north" and 5 < x < 11:
            c = (226, 182, 76) if y > 1 else (170, 128, 50)  # the brass plate
        return c
    if mat == "cranium" and face in ("east", "west"):
        if 6.0 <= z < 9.5 and 8.0 <= y < 11.0:
            return (36, 26, 22) if (6.8 < z < 8.8 and 8.6 < y < 10.6) else (120, 100, 76)  # eye socket
        if 10.5 <= z < 13.5 and 6.5 <= y < 9.0:
            return (52, 40, 32)  # the great window behind the eye
    if mat == "snout" and face in ("north", "east", "west") and y < 5.0:
        return (250, 246, 228) if i % 2 == 0 else (60, 44, 34)  # upper teeth
    if mat == "jaw" and face in ("north", "east", "west") and y > 3.0:
        return (244, 238, 216) if i % 2 == 1 else (60, 44, 34)  # lower teeth
    if mat == "ridge" and face == "up" and z < 2.6 and (6.4 < x < 7.6 or 8.4 < x < 9.6):
        return (40, 30, 24)  # nostrils
    if mat == "horn":
        c = mul(c, 0.92)
    return c


def build_skull():
    img = Image.new("RGBA", (SKULL_TEX, SKULL_TEX), (0, 0, 0, 0))
    elements = []
    x = y = shelf = 0
    for frm, to, mat in SKULL:
        faces_json = {}
        for face, cols, rows, pos in skull_faces(frm, to):
            if face == "down" and frm[1] == 0:
                pass
            if x + cols > SKULL_TEX:
                x, y, shelf = 0, y + shelf, 0
            for j in range(rows):
                for i in range(cols):
                    px, py, pz = pos(i, j)
                    c = paint_skull(mat, face, px, py, pz, i, j)
                    img.putpixel((x + i, y + j), tuple(max(0, min(255, int(v))) for v in c) + (255,))
            k = 16.0 / SKULL_TEX
            faces_json[face] = {"uv": [x * k, y * k, (x + cols) * k, (y + rows) * k], "texture": "#skull"}
            if face == "down" and frm[1] == 0:
                faces_json[face]["cullface"] = "down"
            x += cols
            shelf = max(shelf, rows)
        elements.append({"from": list(frm), "to": list(to), "faces": faces_json})
    assert y + shelf <= SKULL_TEX, "skull texture overflow"
    return img, elements


def write_skull():
    img, elements = build_skull()
    save(img, "block", "tyrannosaurus_skull")
    tex = f"{MOD}:block/tyrannosaurus_skull"
    write_json(os.path.join(ASSETS, "models", "block", "tyrannosaurus_skull.json"),
               {"parent": "minecraft:block/block", "textures": {"skull": tex, "particle": tex}, "elements": elements})
    write_json(os.path.join(ASSETS, "blockstates", "tyrannosaurus_skull.json"), {"variants": {
        f"facing={f}": ({"model": f"{MOD}:block/tyrannosaurus_skull", "y": r} if r else
                        {"model": f"{MOD}:block/tyrannosaurus_skull"})
        for f, r in (("north", 0), ("east", 90), ("south", 180), ("west", 270))}})
    write_json(os.path.join(ASSETS, "items", "tyrannosaurus_skull.json"),
               {"model": {"type": "minecraft:model", "model": f"{MOD}:block/tyrannosaurus_skull"}})
    loot_self("tyrannosaurus_skull")
    add_to_tag("block/mineable/pickaxe", [f"{MOD}:tyrannosaurus_skull"])


def fang_icon():
    """A great curved fang: brown root top-left, ivory enamel curving down to a sharp tip bottom-right."""
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    pts = {}
    for k in range(60):
        t = k / 59
        cx = 4.0 + t * 8.0 + math.sin(t * math.pi) * 1.8
        cy = 3.0 + t * 10.5 - math.sin(t * math.pi) * 1.6
        r = 3.4 * (1 - t) ** 0.75 + 0.35
        for px in range(16):
            for py in range(16):
                if (px + 0.5 - cx) ** 2 + (py + 0.5 - cy) ** 2 <= r * r:
                    pts[(px, py)] = max(pts.get((px, py), -1.0), t)
    for (px, py), t in pts.items():
        edge = any((px + a, py + b) not in pts for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if t < 0.22:
            c = (130, 84, 52)
        else:
            c = lerp((232, 220, 186), (255, 252, 236), (t - 0.22) * 1.3)
        if edge:
            c = (70, 46, 30) if t < 0.22 else (140, 116, 84)
        img.putpixel((px, py), tuple(int(v) for v in c) + (255,))
    for p in ((6, 5), (7, 6), (8, 7)):
        if p in pts:
            img.putpixel(p, (255, 255, 255, 255))
    return img


def tooth_icon(enamel, root, curve, length):
    """A tooth: straight-ish and conical (plesiosaur) or a stout crocodile peg."""
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    pts = {}
    for k in range(50):
        t = k / 49
        cx = 8.0 + math.sin(t * math.pi * 0.5) * curve
        cy = 2.0 + t * length
        r = 3.6 * (1 - t) ** 0.7 + 0.4
        for px in range(16):
            for py in range(16):
                if (px + 0.5 - cx) ** 2 + (py + 0.5 - cy) ** 2 <= r * r:
                    pts[(px, py)] = max(pts.get((px, py), -1.0), t)
    for (px, py), t in pts.items():
        edge = any((px + a, py + b) not in pts for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        c = root if t < 0.2 else lerp(enamel, (255, 252, 240), (t - 0.2) * 1.2)
        if edge:
            c = mul(c, 0.6)
        img.putpixel((px, py), tuple(int(v) for v in c) + (255,))
    return img


def plate_icon():
    """An ankylosaurus osteoderm: a domed ochre plate with a raised keel and a short spike."""
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for x in range(16):
        for y in range(16):
            r = math.hypot((x - 7.5) / 6.5, (y - 8.5) / 5.5)
            if r <= 1.0:
                c = lerp((222, 176, 92), (110, 74, 34), r ** 2)
                if abs(x - 7.5) < 1.0 and 4 <= y < 12 or abs(y - 8.5) < 0.6 and 3 < x < 12:
                    c = (240, 210, 140)
                if r > 0.86:
                    c = (80, 52, 24)
                img.putpixel((x, y), tuple(int(v) for v in c) + (255,))
    for (x, y) in ((6, 5), (7, 4), (8, 4), (9, 5)):  # the keel's raised point
        img.putpixel((x, y), (250, 232, 170, 255))
    return img


def bolt_texture():
    """The blaster bolt glow: a white-hot centre fading through orange to red at the rim (drawn additive)."""
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for x in range(16):
        for y in range(16):
            r = math.hypot(x - 7.5, y - 7.5) / 7.5
            if r < 1.0:
                c = lerp((255, 250, 230), (255, 110, 40), r * 1.6) if r < 0.6 else lerp((255, 110, 40), (200, 20, 10), (r - 0.6) / 0.4)
                img.putpixel((x, y), tuple(int(v) for v in c) + (int(255 * (1 - r ** 3)),))
    return img


def scrap_icon():
    """A twisted bit of riveted chrome plating with a stripped wire."""
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    plate = [(x, y) for y in range(4, 13) for x in range(2, 14) if abs((x - 8) * 0.6 + (y - 8)) < 4.2 and (x + y) % 11 != 0]
    for (x, y) in plate:
        c = lerp((236, 240, 246), (96, 106, 118), (y - 4) / 9)
        edge = any((x + a, y + b) not in plate for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        img.putpixel((x, y), tuple(int(v * (0.6 if edge else 1.0)) for v in c) + (255,))
    for (x, y) in ((5, 7), (9, 6), (7, 10)):
        img.putpixel((x, y), (50, 54, 60, 255))
    for k, (x, y) in enumerate(((11, 3), (12, 2), (13, 2), (14, 1))):
        img.putpixel((x, y), (214, 120, 60, 255) if k % 2 == 0 else (240, 170, 90, 255))
    return img


def core_icon():
    """An atomic core: a glass bulb with a glowing green nucleus and an orbit ring, on a brass cap."""
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for x in range(16):
        for y in range(16):
            r = math.hypot(x - 7.5, y - 7.0)
            if r < 5.6:
                c = (150, 220, 210) if r > 4.6 else lerp((230, 255, 240), (60, 200, 140), r / 4.6)
                img.putpixel((x, y), tuple(int(v) for v in c) + (255,))
    for k in range(40):
        a = k / 40 * math.pi * 2
        x, y = 7.5 + math.cos(a) * 6.8, 7.0 + math.sin(a) * 2.6
        if 0 <= int(x) < 16 and 0 <= int(y) < 16:
            img.putpixel((int(x), int(y)), (120, 230, 255, 255))
    for x in range(5, 11):
        for y in (13, 14):
            img.putpixel((x, y), (214, 170, 70, 255) if y == 13 else (150, 110, 40, 255))
    img.putpixel((6, 4), (255, 255, 255, 255))
    return img


def dagger_icon():
    """The fang lashed to a leather-wrapped grip with a brass pommel, held like a vanilla sword (tip top-right)."""
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    blade = [(5 + k, 10 - k) for k in range(9)]  # diagonal up to the tip
    for k, (x, y) in enumerate(blade):
        w = 2 if k < 6 else 1
        for dx in range(w):
            img.putpixel((x + dx, y), (240, 232, 204, 255))
        img.putpixel((x - 1, y), (150, 128, 96, 255))
        if k < 6:
            img.putpixel((x + 2, y), (150, 128, 96, 255) if y < 15 else (0, 0, 0, 0))
    img.putpixel((14, 1), (255, 252, 240, 255))
    for (x, y) in ((4, 10), (5, 11), (3, 11), (4, 12), (6, 10), (4, 11)):  # leather binding / guard
        img.putpixel((x, y), (122, 76, 44, 255))
    for (x, y) in ((3, 12), (2, 13), (1, 14)):  # grip
        img.putpixel((x, y), (92, 56, 32, 255))
        img.putpixel((x + 1, y), (70, 42, 24, 255))
    img.putpixel((0, 15), (214, 170, 70, 255))  # brass pommel
    img.putpixel((1, 15), (170, 128, 50, 255))
    img.putpixel((0, 14), (170, 128, 50, 255))
    return img


# ----------------------------------------------------------------------------
# Loot
# ----------------------------------------------------------------------------

def drop(item, lo, hi, smelt=None, looting=(0, 1)):
    functions = [{"function": "minecraft:set_count", "count": {"type": "minecraft:uniform", "min": lo, "max": hi}}]
    if smelt:
        functions.append({"function": "minecraft:furnace_smelt", "conditions": [{
            "condition": "minecraft:entity_properties", "entity": "this",
            "predicate": {"flags": {"is_on_fire": True}}}]})
    functions.append({"function": "minecraft:enchanted_count_increase", "enchantment": "minecraft:looting",
                      "count": {"type": "minecraft:uniform", "min": looting[0], "max": looting[1]}})
    return {"rolls": 1, "bonus_rolls": 0, "entries": [{"type": "minecraft:item", "name": item, "functions": functions}]}


def always(item, lo=1, hi=1):
    """A drop that never fails (no looting bonus)."""
    entry = {"type": "minecraft:item", "name": item}
    if (lo, hi) != (1, 1):
        entry["functions"] = [{"function": "minecraft:set_count", "count": {"type": "minecraft:uniform", "min": lo, "max": hi}}]
    return {"rolls": 1, "bonus_rolls": 0, "entries": [entry]}


def rare(item, chance, per_looting=0.03):
    """A rare drop: a flat chance, a little better with Looting."""
    return {"rolls": 1, "bonus_rolls": 0, "entries": [{"type": "minecraft:item", "name": item}],
            "conditions": [{"condition": "minecraft:killed_by_player"},
                           {"condition": "minecraft:random_chance_with_enchanted_bonus", "enchantment": "minecraft:looting",
                            "unenchanted_chance": chance,
                            "enchanted_chance": {"type": "minecraft:linear", "base": chance + per_looting,
                                                 "per_level_above_first": per_looting}}]}


def loot(name, pools):
    write_json(os.path.join(DATA, "loot_table", "entities", name + ".json"),
               {"type": "minecraft:entity", "pools": pools, "random_sequence": f"{MOD}:entities/{name}"})


# ----------------------------------------------------------------------------
# Entry points used by gen_resources.py
# ----------------------------------------------------------------------------

EN = {
    "entity.retrocosmos.raptor": "Venus Raptor",
    "entity.retrocosmos.brontosaurus": "Brontosaurus",
    "entity.retrocosmos.triceratops": "Triceratops",
    "item.retrocosmos.raptor_spawn_egg": "Venus Raptor Spawn Egg",
    "item.retrocosmos.brontosaurus_spawn_egg": "Brontosaurus Spawn Egg",
    "item.retrocosmos.triceratops_spawn_egg": "Triceratops Spawn Egg",
    "entity.retrocosmos.venus_creeper": "Venus Creeper",
    "entity.retrocosmos.pteranodon": "Pteranodon",
    "entity.retrocosmos.tyrannosaurus": "Tyrannosaurus",
    "item.retrocosmos.venus_creeper_spawn_egg": "Venus Creeper Spawn Egg",
    "item.retrocosmos.pteranodon_spawn_egg": "Pteranodon Spawn Egg",
    "item.retrocosmos.tyrannosaurus_spawn_egg": "Tyrannosaurus Spawn Egg",
    "item.retrocosmos.tyrannosaurus_fang": "Tyrannosaurus Fang",
    "item.retrocosmos.fang_dagger": "Fang Dagger",
    "block.retrocosmos.tyrannosaurus_skull": "Tyrannosaurus Skull",
    "entity.retrocosmos.plesiosaur": "Plesiosaur",
    "item.retrocosmos.plesiosaur_spawn_egg": "Plesiosaur Spawn Egg",
    "entity.retrocosmos.meganeura": "Meganeura",
    "item.retrocosmos.meganeura_spawn_egg": "Meganeura Spawn Egg",
    "entity.retrocosmos.compsognathus": "Compsognathus",
    "item.retrocosmos.compsognathus_spawn_egg": "Compsognathus Spawn Egg",
    "entity.retrocosmos.spore_moth": "Spore Moth",
    "item.retrocosmos.spore_moth_spawn_egg": "Spore Moth Spawn Egg",
    "entity.retrocosmos.ankylosaurus": "Ankylosaurus",
    "item.retrocosmos.ankylosaurus_spawn_egg": "Ankylosaurus Spawn Egg",
    "entity.retrocosmos.deinosuchus": "Deinosuchus",
    "item.retrocosmos.deinosuchus_spawn_egg": "Deinosuchus Spawn Egg",
    "item.retrocosmos.plesiosaur_tooth": "Plesiosaur Tooth",
    "item.retrocosmos.deinosuchus_tooth": "Deinosuchus Tooth",
    "item.retrocosmos.ankylosaurus_plate": "Ankylosaurus Plate",
    "entity.retrocosmos.atomic_sentry": "Atomic Sentry",
    "entity.retrocosmos.atomic_automaton": "Atomic Automaton",
    "entity.retrocosmos.sentry_bolt": "Blaster Bolt",
    "item.retrocosmos.atomic_sentry_spawn_egg": "Atomic Sentry Spawn Egg",
    "item.retrocosmos.atomic_automaton_spawn_egg": "Atomic Automaton Spawn Egg",
    "item.retrocosmos.atomic_scrap": "Atomic Scrap",
    "item.retrocosmos.atomic_core": "Atomic Core",
}

RU = {
    "entity.retrocosmos.raptor": "Венерианский раптор",
    "entity.retrocosmos.brontosaurus": "Бронтозавр",
    "entity.retrocosmos.triceratops": "Трицератопс",
    "item.retrocosmos.raptor_spawn_egg": "Яйцо призыва венерианского раптора",
    "item.retrocosmos.brontosaurus_spawn_egg": "Яйцо призыва бронтозавра",
    "item.retrocosmos.triceratops_spawn_egg": "Яйцо призыва трицератопса",
    "entity.retrocosmos.venus_creeper": "Венерианский крипер",
    "entity.retrocosmos.pteranodon": "Птеранодон",
    "entity.retrocosmos.tyrannosaurus": "Тиранозавр",
    "item.retrocosmos.venus_creeper_spawn_egg": "Яйцо призыва венерианского крипера",
    "item.retrocosmos.pteranodon_spawn_egg": "Яйцо призыва птеранодона",
    "item.retrocosmos.tyrannosaurus_spawn_egg": "Яйцо призыва тиранозавра",
    "item.retrocosmos.tyrannosaurus_fang": "Клык тиранозавра",
    "item.retrocosmos.fang_dagger": "Кинжал из клыка",
    "block.retrocosmos.tyrannosaurus_skull": "Череп тиранозавра",
    "entity.retrocosmos.plesiosaur": "Плезиозавр",
    "item.retrocosmos.plesiosaur_spawn_egg": "Яйцо призыва плезиозавра",
    "entity.retrocosmos.meganeura": "Меганевра",
    "item.retrocosmos.meganeura_spawn_egg": "Яйцо призыва меганевры",
    "entity.retrocosmos.compsognathus": "Компсогнат",
    "item.retrocosmos.compsognathus_spawn_egg": "Яйцо призыва компсогната",
    "entity.retrocosmos.spore_moth": "Споровый мотылёк",
    "item.retrocosmos.spore_moth_spawn_egg": "Яйцо призыва спорового мотылька",
    "entity.retrocosmos.ankylosaurus": "Анкилозавр",
    "item.retrocosmos.ankylosaurus_spawn_egg": "Яйцо призыва анкилозавра",
    "entity.retrocosmos.deinosuchus": "Дейнозух",
    "item.retrocosmos.deinosuchus_spawn_egg": "Яйцо призыва дейнозуха",
    "item.retrocosmos.plesiosaur_tooth": "Зуб плезиозавра",
    "item.retrocosmos.deinosuchus_tooth": "Зуб дейнозуха",
    "item.retrocosmos.ankylosaurus_plate": "Пластина анкилозавра",
    "entity.retrocosmos.atomic_sentry": "Атомный часовой",
    "entity.retrocosmos.atomic_automaton": "Атомный автоматон",
    "entity.retrocosmos.sentry_bolt": "Бластерный заряд",
    "item.retrocosmos.atomic_sentry_spawn_egg": "Яйцо призыва атомного часового",
    "item.retrocosmos.atomic_automaton_spawn_egg": "Яйцо призыва атомного автоматона",
    "item.retrocosmos.atomic_scrap": "Атомный лом",
    "item.retrocosmos.atomic_core": "Атомное ядро",
}


def generate():
    for spec in SPECS:
        save(build_texture(spec), "entity", "dinosaur", spec["name"])
        if spec.get("glow"):
            save(build_texture(spec, glow=True), "entity", "dinosaur", spec["name"] + "_glow")
    write_java()
    write_skull()
    save(fang_icon(), "item", "tyrannosaurus_fang")
    generated_item("tyrannosaurus_fang")
    save(dagger_icon(), "item", "fang_dagger")
    generated_item("fang_dagger", parent="minecraft:item/handheld")
    save(tooth_icon((230, 226, 206), (120, 110, 90), 1.2, 12.0), "item", "plesiosaur_tooth")
    generated_item("plesiosaur_tooth")
    save(tooth_icon((214, 204, 160), (96, 84, 56), 0.4, 9.5), "item", "deinosuchus_tooth")
    generated_item("deinosuchus_tooth")
    save(plate_icon(), "item", "ankylosaurus_plate")
    generated_item("ankylosaurus_plate")
    # Dr. Oinstein's robots
    save(bolt_texture(), "entity", "dinosaur", "sentry_bolt")
    save(scrap_icon(), "item", "atomic_scrap")
    generated_item("atomic_scrap")
    save(core_icon(), "item", "atomic_core")
    generated_item("atomic_core")
    shapeless("iron_ingot_from_atomic_scrap", ["atomic_scrap"] * 4, "minecraft:iron_ingot")
    add_to_tag("entity_type/oinstein_forces", [f"{MOD}:atomic_sentry", f"{MOD}:atomic_automaton"], namespace=MOD)
    shaped("fang_dagger", ["F", "L", "S"], {"F": "tyrannosaurus_fang", "L": "minecraft:leather", "S": "minecraft:stick"},
           "fang_dagger", category="equipment")

    for name, (shell, spots) in EGGS.items():
        save(egg(shell, spots), "item", f"{name}_spawn_egg")
        generated_item(f"{name}_spawn_egg")

    loot("raptor", [drop("minecraft:leather", 0, 2), drop("minecraft:bone", 0, 2)])
    loot("brontosaurus", [drop("minecraft:beef", 6, 10, smelt=True, looting=(0, 3)),
                          drop("minecraft:bone", 2, 5, looting=(0, 2)),
                          drop("minecraft:leather", 2, 4, looting=(0, 2))])
    loot("triceratops", [drop("minecraft:leather", 1, 3), drop("minecraft:bone", 0, 2),
                         drop("minecraft:beef", 1, 3, smelt=True)])
    loot("venus_creeper", [drop("minecraft:gunpowder", 0, 2), drop("minecraft:glow_berries", 0, 1)])
    loot("pteranodon", [drop("minecraft:leather", 0, 2), drop("minecraft:bone", 0, 2)])
    # the great reward: the skull and a fang always, plus a mountain of meat
    loot("tyrannosaurus", [always(f"{MOD}:tyrannosaurus_skull"), always(f"{MOD}:tyrannosaurus_fang"),
                           drop(f"{MOD}:tyrannosaurus_fang", 0, 1, looting=(0, 1)),
                           drop("minecraft:beef", 10, 16, smelt=True, looting=(0, 4)),
                           drop("minecraft:bone", 6, 10, looting=(0, 3)),
                           drop("minecraft:leather", 3, 6, looting=(0, 2))])
    loot("plesiosaur", [drop("minecraft:beef", 2, 5, smelt=True, looting=(0, 2)), drop("minecraft:bone", 1, 3),
                        rare(f"{MOD}:plesiosaur_tooth", 0.12)])
    loot("meganeura", [])
    loot("compsognathus", [drop("minecraft:chicken", 0, 1, smelt=True)])
    loot("spore_moth", [drop("minecraft:glowstone_dust", 0, 1)])
    loot("ankylosaurus", [drop("minecraft:beef", 2, 4, smelt=True), drop("minecraft:leather", 1, 3),
                          rare(f"{MOD}:ankylosaurus_plate", 0.15)])
    loot("deinosuchus", [drop("minecraft:leather", 1, 3), drop("minecraft:bone", 0, 2),
                         rare(f"{MOD}:deinosuchus_tooth", 0.12)])
    loot("atomic_sentry", [drop(f"{MOD}:atomic_scrap", 1, 2), drop("minecraft:copper_ingot", 0, 1),
                           drop("minecraft:redstone", 0, 2), rare(f"{MOD}:atomic_core", 0.06)])
    loot("atomic_automaton", [drop(f"{MOD}:atomic_scrap", 2, 4), drop("minecraft:copper_ingot", 0, 2),
                              drop("minecraft:redstone", 1, 3), rare(f"{MOD}:atomic_core", 0.12)])


if __name__ == "__main__":
    generate()
