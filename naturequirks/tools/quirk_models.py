"""Box-model toolkit for the Nature's Quirks mobs (stone head, flower creeper, guardian bee).

A creature is a spec: parts (name, parent, pivot, rotation) holding boxes (origin, integer size, material). From one
spec this module produces
  * the texture: every texel is painted by a painter function that knows the texel's box, face and 3D position,
  * the Java LayerDefinition (box UVs are shelf-packed exactly like ModelPart.Cube lays them out),
  * software previews (orthographic, painter's algorithm) for checking the look without starting the game.
Model space is Minecraft's: y points down, the feet stand on y = 24, -z is the front.
"""
import json
import math
import os

from PIL import Image, ImageDraw

MOD = "naturequirks"
TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(TOOLS, "..", "src", "main", "resources")
ASSETS = os.path.join(ROOT, "assets", MOD)
DATA = os.path.join(ROOT, "data", MOD)
JAVA = os.path.join(TOOLS, "..", "src", "main", "java", "com", "replecant", MOD)


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")


def save_png(img, *rel):
    path = os.path.join(ASSETS, "textures", *rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)


# ----------------------------------------------------------------------------
# Specs
# ----------------------------------------------------------------------------

def B(x, y, z, w, h, d, mat, **feat):
    """A box: origin (x, y, z) relative to its part's pivot, integer size (w, h, d), a paint material."""
    return {"pos": (x, y, z), "size": (w, h, d), "mat": mat, "feat": feat}


def P(name, parent, pivot, rot, boxes):
    return {"name": name, "parent": parent, "pivot": pivot, "rot": rot, "boxes": boxes}


# ----------------------------------------------------------------------------
# Math
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


IDENTITY = [[1 if i == j else 0 for j in range(4)] for i in range(4)]


def part_matrices(spec, pose=None):
    """Model-space matrix of every part, like ModelPart.translateAndRotate (translate, then Z*Y*X rotation).
    pose: {part: (drx, dry, drz[, dx, dy, dz])} added to the rest pose."""
    pose = pose or {}
    by_name = {p["name"]: p for p in spec["parts"]}
    out = {}

    def get(name):
        if name in out:
            return out[name]
        p = by_name[name]
        parent = get(p["parent"]) if p["parent"] else IDENTITY
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
# UV layout (identical to ModelPart.Cube)
# ----------------------------------------------------------------------------

def pack(spec):
    """Shelf-packs every box's UV block; stores box['uv'] and the sheet height in the spec."""
    boxes = []
    for p in spec["parts"]:
        for b in p["boxes"]:
            if "uv" in b["feat"]:
                b["uv"] = b["feat"]["uv"]  # a fixed layout (used to preview vanilla models with vanilla textures)
            else:
                boxes.append(b)
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
    spec["tex_h"] = max(height, spec.get("tex_h_min", 16))


def faces(b):
    """Yields (face, (u0, v0), (cols, rows), texel_to_local) for the six faces of a box, following the vertex/UV
    assignment of ModelPart.Cube's polygons. texel_to_local(i, j, fi, fj) -> local point of texel (i+fi, j+fj)."""
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
    h = (h * 0x5BD1E995) & 0xFFFFFFFF
    h ^= h >> 15
    return h / 0xFFFFFFFF


def value_noise(x, y, z, scale, seed):
    """Smooth 3D value noise in 0..1 (trilinear over a lattice of the given scale)."""
    x, y, z = x / scale, y / scale, z / scale
    xi, yi, zi = math.floor(x), math.floor(y), math.floor(z)
    fx, fy, fz = x - xi, y - yi, z - zi
    fx, fy, fz = (f * f * (3 - 2 * f) for f in (fx, fy, fz))
    acc = 0.0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                wgt = (fx if dx else 1 - fx) * (fy if dy else 1 - fy) * (fz if dz else 1 - fz)
                acc += wgt * hash3(xi + dx, yi + dy, zi + dz, seed)
    return acc


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(a[k] + (b[k] - a[k]) * t for k in range(3))


def shade(c, f):
    return tuple(max(0, min(255, v * f)) for v in c[:3])


def rgba(c, a=255):
    return tuple(max(0, min(255, int(round(v)))) for v in c[:3]) + (a,)


class Texel:
    """Everything a painter may want to know about one texel."""
    __slots__ = ("mat", "feat", "face", "i", "j", "cols", "rows", "lx", "ly", "lz", "mx", "my", "mz", "nx", "ny",
                 "nz", "x0", "y0", "z0", "x1", "y1", "z1", "w", "h", "d", "fx", "fy", "fz", "box", "part", "u", "v")

    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)

    def edge(self, n=1):
        return self.i < n or self.j < n or self.i >= self.cols - n or self.j >= self.rows - n


def build_texture(spec, painter):
    """painter(spec, texel) -> RGBA tuple (or None for transparent)."""
    pack(spec)
    img = Image.new("RGBA", (spec["tex_w"], spec["tex_h"]), (0, 0, 0, 0))
    mats = part_matrices(spec)
    for part in spec["parts"]:
        m = mats[part["name"]]
        for bi, b in enumerate(part["boxes"]):
            x0, y0, z0 = b["pos"]
            w, h, d = b["size"]
            for face, (u0, v0), (cols, rows), to_local in faces(b):
                n = apply(m, FACE_NORMALS[face], 0.0)
                for j in range(rows):
                    for i in range(cols):
                        lx, ly, lz = to_local(i, j)
                        mx, my, mz = apply(m, (lx, ly, lz))
                        t = Texel(mat=b["mat"], feat=b["feat"], face=face, i=i, j=j, cols=cols, rows=rows,
                                  lx=lx, ly=ly, lz=lz, mx=mx, my=my, mz=mz, nx=n[0], ny=n[1], nz=n[2],
                                  x0=x0, y0=y0, z0=z0, x1=x0 + w, y1=y0 + h, z1=z0 + d, w=w, h=h, d=d,
                                  fx=(lx - x0) / w if w else 0.5, fy=(ly - y0) / h if h else 0.5,
                                  fz=(lz - z0) / d if d else 0.5, box=b, part=part["name"], u=u0 + i, v=v0 + j)
                        px = painter(spec, t)
                        if px is not None:
                            img.putpixel((u0 + i, v0 + j), rgba(px, px[3] if len(px) > 3 else 255))
    return img


# ----------------------------------------------------------------------------
# Java
# ----------------------------------------------------------------------------

def jf(v):
    return repr(round(float(v), 4)) + "F"


def java_layer(spec, method):
    lines = [f"    /** {spec['name']}: {len(spec['parts'])} parts, texture {spec['tex_w']}x{spec['tex_h']}. */",
             f"    public static LayerDefinition {method}() {{",
             "        MeshDefinition mesh = new MeshDefinition();",
             "        PartDefinition root = mesh.getRoot();"]
    for p in spec["parts"]:
        cubes = "CubeListBuilder.create()"
        for b in p["boxes"]:
            (x, y, z), (w, h, d), (u, v) = b["pos"], b["size"], b["uv"]
            infl = b["feat"].get("inflate")
            extra = f", new CubeDeformation({jf(infl)})" if infl else ""
            cubes += f"\n                .texOffs({u}, {v}).addBox({jf(x)}, {jf(y)}, {jf(z)}, {jf(w)}, {jf(h)}, {jf(d)}{extra})"
        parent = p["parent"] or "root"
        pose = (f"PartPose.offsetAndRotation({jf(p['pivot'][0])}, {jf(p['pivot'][1])}, {jf(p['pivot'][2])}, "
                f"{jf(p['rot'][0])}, {jf(p['rot'][1])}, {jf(p['rot'][2])})")
        var = p["name"] if any(q["parent"] == p["name"] for q in spec["parts"]) else None
        decl = f"PartDefinition {var} = " if var else ""
        lines.append(f"        {decl}{parent}.addOrReplaceChild(\"{p['name']}\", {cubes},")
        lines.append(f"                {pose});")
    lines.append(f"        return LayerDefinition.create(mesh, {spec['tex_w']}, {spec['tex_h']});")
    lines.append("    }")
    return "\n".join(lines)


def write_geometry(package, cls, layers, doc):
    """layers: [(spec, method name)]. Writes src/main/java/<package path>/<cls>.java."""
    body = "\n\n".join(java_layer(s, m) for s, m in layers)
    src = f"""package {package};

import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeDeformation;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;

/** {doc} GENERATED by tools/{cls_tool(package)}.py - edit the spec there, not this file. */
public final class {cls} {{
    private {cls}() {{}}

{body}
}}
"""
    rel = package.split(".")[3:]
    path = os.path.join(JAVA, *rel, cls + ".java")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(src)


def cls_tool(package):
    return {"stonehead": "stone_head", "flowercreeper": "flower_creeper", "guardianbee": "guardian_bee"}[package.split(".")[3]]


# ----------------------------------------------------------------------------
# Previews
# ----------------------------------------------------------------------------

def cam(p, yaw, pitch):
    x, y, z = p
    c, s = math.cos(yaw), math.sin(yaw)
    X, Z = x * c + z * s, -x * s + z * c
    cp, sp = math.cos(pitch), math.sin(pitch)
    return X, y * cp - Z * sp, Z * cp + y * sp


def quads(spec, tex, yaw, pitch, pose=None, scale_model=1.0, offset=(0, 0, 0), light=1.0):
    """Projected, shaded texel quads of one model: [(depth, [(x, y)...], rgb)] in model units."""
    mats = part_matrices(spec, pose)
    out = []
    for part in spec["parts"]:
        if part["name"] in spec.get("hidden", ()):
            continue
        m = mats[part["name"]]
        for b in part["boxes"]:
            for face, (u0, v0), (cols, rows), to_local in faces(b):
                n = apply(m, FACE_NORMALS[face], 0.0)
                cn = cam(n, yaw, pitch)
                if cn[2] > 0.01 and min(b["size"]) > 0:
                    continue
                sh = 0.8 - 0.2 * n[1] + 0.06 * abs(n[2]) - 0.04 * abs(n[0])
                sh = max(0.45, min(1.0, sh)) * light
                for j in range(rows):
                    for i in range(cols):
                        px = tex.getpixel((u0 + i, v0 + j))
                        if px[3] < 128:
                            continue
                        corners = [to_local(i, j, 0, 0), to_local(i, j, 1, 0), to_local(i, j, 1, 1), to_local(i, j, 0, 1)]
                        pts = []
                        for c in corners:
                            q = apply(m, c)
                            q = ((q[0] * scale_model + offset[0]), (24 + (q[1] - 24) * scale_model + offset[1]),
                                 (q[2] * scale_model + offset[2]))
                            pts.append(cam(q, yaw, pitch))
                        depth = sum(p[2] for p in pts) / 4
                        out.append((depth, [(p[0], p[1]) for p in pts], tuple(int(px[k] * sh) for k in range(3))))
    return out


def sky(W, H, top=(150, 190, 245), bottom=(205, 225, 250)):
    img = Image.new("RGB", (W, H))
    dr = ImageDraw.Draw(img)
    for yy in range(H):
        dr.line([(0, yy), (W, yy)], fill=tuple(int(v) for v in mix(top, bottom, yy / max(1, H - 1))))
    return img


def draw_scene(groups, yaw, pitch, scale, size=None, ground=None, label=None, extra=None):
    """groups: list of quad lists (already offset in model units). Renders them into one image.
    ground: rgb of a ground strip drawn under y = 24 (side views)."""
    allq = [q for g in groups for q in g]
    xs = [p[0] for q in allq for p in q[1]]
    ys = [p[1] for q in allq for p in q[1]]
    if extra:
        xs += [p[0] for p in extra]
        ys += [p[1] for p in extra]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    pad = 14
    W = size[0] if size else int((maxx - minx) * scale) + 2 * pad
    H = size[1] if size else int((maxy - miny) * scale) + 2 * pad + (10 if ground else 0)
    img = sky(W, H)
    dr = ImageDraw.Draw(img)
    ox = (W - (maxx - minx) * scale) / 2 - minx * scale
    oy = pad - miny * scale
    if ground:
        gy = oy + 24 * math.cos(pitch) * scale
        dr.rectangle([0, gy, W, H], fill=ground)
    allq.sort(key=lambda q: -q[0])
    for depth, pts, col in allq:
        dr.polygon([(ox + x * scale, oy + y * scale) for x, y in pts], fill=col)
    if label:
        dr.text((6, 4), label, fill=(30, 30, 40))
    return img, (ox, oy)


def sheet(spec, tex, scale, poses=(), views=None):
    """Side / front / 3-4 / rear views + named poses + the texture, in one image."""
    views = views or [("side", math.pi / 2, 0.0), ("front", 0.0, 0.0), ("3/4", math.pi / 4 + 0.35, 0.42),
                      ("rear 3/4", math.pi + 0.8, 0.42)]
    imgs = []
    for label, yaw, pitch in views:
        im, _ = draw_scene([quads(spec, tex, yaw, pitch)], yaw, pitch, scale, label=label)
        imgs.append(im)
    for label, pose in poses:
        yaw, pitch = math.pi / 4 + 0.35, 0.3
        im, _ = draw_scene([quads(spec, tex, yaw, pitch, pose)], yaw, pitch, scale, label=label)
        imgs.append(im)
    texs = max(1, 512 // spec["tex_w"])
    tex_big = tex.resize((tex.size[0] * texs, tex.size[1] * texs), Image.NEAREST)
    checker = Image.new("RGBA", tex_big.size, (60, 60, 70, 255))
    checker.alpha_composite(tex_big)
    rows = [imgs[i:i + 4] for i in range(0, len(imgs), 4)]
    W = max(max(sum(i.size[0] for i in r) for r in rows), checker.size[0])
    H = sum(max(i.size[1] for i in r) for r in rows) + checker.size[1]
    out = Image.new("RGB", (W, H), (30, 30, 36))
    y = 0
    for r in rows:
        x = 0
        for im in r:
            out.paste(im, (x, y))
            x += im.size[0]
        y += max(i.size[1] for i in r)
    out.paste(checker.convert("RGB"), (0, y))
    return out


def extents(spec, pose=None):
    mats = part_matrices(spec, pose)
    pts = []
    for part in spec["parts"]:
        m = mats[part["name"]]
        for b in part["boxes"]:
            x0, y0, z0 = b["pos"]
            w, h, d = b["size"]
            for cx in (x0, x0 + w):
                for cy in (y0, y0 + h):
                    for cz in (z0, z0 + d):
                        pts.append(apply(m, (cx, cy, cz)))
    return [(min(p[k] for p in pts), max(p[k] for p in pts)) for k in range(3)]


# ----------------------------------------------------------------------------
# Items
# ----------------------------------------------------------------------------

def item_model(name, parent="minecraft:item/generated"):
    write_json(os.path.join(ASSETS, "items", name + ".json"),
               {"model": {"type": "minecraft:model", "model": f"{MOD}:item/{name}"}})
    write_json(os.path.join(ASSETS, "models", "item", name + ".json"),
               {"parent": parent, "textures": {"layer0": f"{MOD}:item/{name}"}})


EGG_ROWS = [
    "................",
    "......####......",
    ".....######.....",
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
    "....########....",
    ".....######.....",
    "................",
]
EGG_INSIDE = {(x, y) for y, row in enumerate(EGG_ROWS) for x, ch in enumerate(row) if ch == "#"}


def egg_edge(x, y):
    return any((x + a, y + b) not in EGG_INSIDE for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))


def spawn_egg(paint, extras=None):
    """A 1.21.5+-style spawn egg: the egg silhouette dressed as its mob. paint(x, y) -> rgb for each egg texel (the
    rim is darkened automatically, light falls from the upper left); extras: {(x, y): rgba} drawn on top, also
    outside the egg (wings, petals...)."""
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for (x, y) in EGG_INSIDE:
        c = paint(x, y)
        if c is None:
            continue
        f = 1.0 + 0.08 * ((7.5 - x) + (7.5 - y)) / 8
        c = shade(c, f)
        if egg_edge(x, y):
            c = shade(c, 0.58)
        img.putpixel((x, y), rgba(c))
    for p, c in (extras or {}).items():
        img.putpixel(p, rgba(c, c[3] if len(c) > 3 else 255))
    return img


# ----------------------------------------------------------------------------
# Data helpers
# ----------------------------------------------------------------------------

def count_fn(lo, hi):
    return {"function": "minecraft:set_count", "count": lo if lo == hi else {"type": "minecraft:uniform", "min": lo, "max": hi}}


def looting(lo, hi):
    return {"function": "minecraft:enchanted_count_increase", "enchantment": "minecraft:looting",
            "count": {"type": "minecraft:uniform", "min": lo, "max": hi}}


def entry(item, lo=1, hi=1, weight=None, quality=None, functions=()):
    e = {"type": "minecraft:item", "name": item}
    fns = ([count_fn(lo, hi)] if (lo, hi) != (1, 1) else []) + list(functions)
    if fns:
        e["functions"] = fns
    if weight is not None:
        e["weight"] = weight
    if quality is not None:
        e["quality"] = quality
    return e


def pool(entries, rolls=1, bonus=0, conditions=None):
    p = {"rolls": rolls, "bonus_rolls": bonus, "entries": entries}
    if conditions:
        p["conditions"] = conditions
    return p


def loot_table(path, pools, kind="minecraft:entity"):
    write_json(os.path.join(DATA, "loot_table", path + ".json"), {"type": kind, "pools": pools})


def spawn_modifier(name, biome_tag, entity, weight, lo, hi):
    write_json(os.path.join(DATA, "neoforge", "biome_modifier", name + ".json"),
               {"type": "neoforge:add_spawns", "biomes": "#" + biome_tag,
                "spawners": [{"type": entity, "weight": weight, "minCount": lo, "maxCount": hi}]})


def tag(kind, name, values):
    write_json(os.path.join(DATA, "tags", kind, name + ".json"), {"replace": False, "values": values})
