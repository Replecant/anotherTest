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

from gen_resources import ASSETS, DATA, MOD, generated_item, save, write_json

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


SPECS = [raptor_spec(), bronto_spec(), trike_spec()]

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
        dx, dy, dz = pose.get(name, (0, 0, 0))
        rx, ry, rz = p["rot"][0] + dx, p["rot"][1] + dy, p["rot"][2] + dz
        m = mat_mul(parent, translate(*p["pivot"]))
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
        if sp == "raptor":
            # ochre tiger stripes over the back, flanks, neck and tail
            band = (t.mz * 0.9 + abs(t.mx) * 0.55 + t.my * 0.25)
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
            if feat.get("mouth") and t.face in ("east", "west") and abs(t.ly - (t.y0 + t.h * 0.62)) < 0.5:
                c = mul(c, 0.55)
        if mat == "jaw":
            if feat.get("teeth") == "top" and t.face in ("east", "west", "north") and t.ly < t.y0 + 1:
                c = (244, 240, 222) if (t.i % 2 == 1) else (120, 24, 24)
            if t.face == "top":
                c = (150, 40, 40)  # inside of the mouth
        e = eye_texel(t, feat.get("eye"), pal, big=(sp != "brontosaurus"))
        if e == "brow":
            c = mul(c, 0.62)
        elif e is not None:
            c = e
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

    elif mat == "beak":
        # dark horny beak, glossier on top, the upper bill hooking down over the lower one
        f = 1 - (t.lz - t.z0) / t.d  # 1 at the front
        c = lerp(pal["beak"], mul(pal["beak"], 0.6), f)
        if t.face == "top":
            c = mul(c, 1.3)
        if feat.get("hook") and t.face in ("east", "west", "north") and t.ly > t.y1 - 1 and f < 0.6:
            c = (40, 32, 30)
        c = tuple(v + noise for v in c)

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


def build_texture(spec):
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
                f"Map.entry(\"{k}\", new float[]{{{jf(v[0])}, {jf(v[1])}, {jf(v[2])}}})" for k, v in parts.items())
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
}

RU = {
    "entity.retrocosmos.raptor": "Венерианский раптор",
    "entity.retrocosmos.brontosaurus": "Бронтозавр",
    "entity.retrocosmos.triceratops": "Трицератопс",
    "item.retrocosmos.raptor_spawn_egg": "Яйцо призыва венерианского раптора",
    "item.retrocosmos.brontosaurus_spawn_egg": "Яйцо призыва бронтозавра",
    "item.retrocosmos.triceratops_spawn_egg": "Яйцо призыва трицератопса",
}


def generate():
    for spec in SPECS:
        save(build_texture(spec), "entity", "dinosaur", spec["name"])
    write_java()

    for name, (shell, spots) in EGGS.items():
        save(egg(shell, spots), "item", f"{name}_spawn_egg")
        generated_item(f"{name}_spawn_egg")

    loot("raptor", [drop("minecraft:leather", 0, 2), drop("minecraft:bone", 0, 2)])
    loot("brontosaurus", [drop("minecraft:beef", 6, 10, smelt=True, looting=(0, 3)),
                          drop("minecraft:bone", 2, 5, looting=(0, 2)),
                          drop("minecraft:leather", 2, 4, looting=(0, 2))])
    loot("triceratops", [drop("minecraft:leather", 1, 3), drop("minecraft:bone", 0, 2),
                         drop("minecraft:beef", 1, 3, smelt=True)])


if __name__ == "__main__":
    generate()
