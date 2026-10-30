"""Giant wild beehives: honey blocks, honey as a fluid, honey cookies and the honey cake, and the hive structures.

Writes (vanilla conventions throughout):
  * textures (16x, vanilla honey palette), block / item models, blockstates for: wild_comb, dripping_comb,
    honeycomb_bricks (+ stairs, slab, wall), comb_window, royal_jelly, hive_heart, the honey fluid (still / flowing),
    honey_bucket, honey_cookie, honey_cake (a 7-slice cake block);
  * loot tables (blocks, hive chests), recipes (crafting + stonecutting), tool tags;
  * the structure: two templates (giant_hive/tree - a hive swallowing an old oak, giant_hive/dome - a lumpy mound),
    template pool, structure (naturequirks:dry_jigsaw: never on water or broken ground) and structure set.
"""
import gzip
import io
import json
import math
import os
import random
import struct

from PIL import Image

from gen_resources import ASSETS, DATA, MOD, write_json

EN, RU = {}, {}


def N(name):
    return f"{MOD}:{name}"


def T(name, kind="block"):
    return f"{MOD}:{kind}/{name}"


# =====================================================================================================================
# Palette (the vanilla honey colours) and pixel helpers
# =====================================================================================================================
HONEY = [(176, 86, 6), (200, 106, 8), (216, 120, 3), (232, 140, 8), (250, 171, 28), (255, 206, 93), (255, 228, 127)]
WAX = [(120, 70, 18), (156, 92, 24), (190, 120, 36)]
CREAM = [(214, 196, 150), (236, 224, 184), (248, 241, 212), (255, 252, 236)]
CAKE = [(141, 67, 36), (167, 75, 36), (199, 97, 36)]


def img(w=16, h=16):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def put(im, x, y, c, a=255):
    if 0 <= x < im.width and 0 <= y < im.height:
        im.putpixel((x, y), (int(c[0]), int(c[1]), int(c[2]), a if len(c) < 4 else c[3]))


def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c[:3])


def save_tex(im, name, kind="block", frametime=None, interpolate=False):
    path = os.path.join(ASSETS, "textures", kind, name + ".png")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path)
    meta = path + ".mcmeta"
    if frametime:
        anim = {"frametime": frametime}
        if interpolate:
            anim["interpolate"] = True
        with open(meta, "w") as f:
            json.dump({"animation": anim}, f)
    elif os.path.exists(meta):
        os.remove(meta)
    TEXTURES[name] = im


TEXTURES = {}


def hex_cells(w=16, h=16, size=4):
    """A tileable honeycomb lattice: (cell id, rim?) for every pixel - rows every `size` px, odd rows shifted."""
    out = {}
    for y in range(h):
        row = y // size
        off = (size // 2) if row % 2 else 0
        for x in range(w):
            col = ((x + off) % w) // size
            ly, lx = y % size, (x + off) % size
            rim = ly == 0 or lx == 0
            out[(x, y)] = ((row, col), rim)
    return out


def comb(seed, filled=0.35, glossy=False, dark_rate=0.18):
    """Wild comb: amber cells in a darker wax lattice; some cells capped with honey, some empty and dark."""
    rnd = random.Random(seed)
    cells = hex_cells()
    kinds = {}
    for (_x, _y), (cid, _r) in cells.items():
        if cid not in kinds:
            r = rnd.random()
            kinds[cid] = "honey" if r < filled else "empty" if r < filled + dark_rate else "wax"
    im = img()
    for (x, y), (cid, rim) in cells.items():
        k = kinds[cid]
        if rim:
            c = WAX[2] if (x + y) % 3 else WAX[1]
        elif k == "honey":
            c = HONEY[5] if (x + y) % 4 == 0 else HONEY[4] if glossy or (x * 7 + y) % 3 else HONEY[3]
        elif k == "empty":
            c = HONEY[1] if (x + y) % 2 else HONEY[0]
        else:
            c = HONEY[3] if (x * 3 + y) % 4 else HONEY[2]
        c = shade(c, 1.0 + (rnd.random() - 0.5) * 0.08)
        put(im, x, y, c)
    return im


def drips(im, seed, bottom=False):
    """Honey runs down the face (side) or hangs in drops (bottom)."""
    rnd = random.Random(seed)
    for _ in range(4 if not bottom else 6):
        x = rnd.randrange(16)
        if bottom:
            y = rnd.randrange(16)
            put(im, x, y, HONEY[5])
            put(im, (x + 1) % 16, y, HONEY[4])
            continue
        top = rnd.randrange(0, 6)
        length = rnd.randrange(4, 11)
        for y in range(top, min(16, top + length)):
            put(im, x, y, HONEY[5] if y < top + length - 1 else HONEY[6])
        put(im, x, min(15, top + length), HONEY[4])
    return im


def bricks():
    im = img()
    rnd = random.Random(31)
    for y in range(16):
        course = y // 4
        for x in range(16):
            mortar = y % 4 == 3 or (x + (4 if course % 2 else 0)) % 8 == 7
            if mortar:
                c = WAX[1]
            else:
                bx = ((x + (4 if course % 2 else 0)) // 8, course)
                base = HONEY[3] if (bx[0] + bx[1]) % 3 else HONEY[4]
                c = HONEY[5] if y % 4 == 0 else base
                if (x + (4 if course % 2 else 0)) % 8 == 6 or y % 4 == 2:
                    c = shade(c, 0.85)
                c = shade(c, 1.0 + (rnd.random() - 0.5) * 0.06)
            put(im, x, y, c)
    return im


def window():
    """Waxed comb window: a wax frame and amber cells you can see through."""
    cells = hex_cells()
    im = img()
    for (x, y), (_cid, rim) in cells.items():
        if x in (0, 15) or y in (0, 15):
            put(im, x, y, WAX[2])
        elif rim:
            put(im, x, y, HONEY[2])
        else:
            put(im, x, y, HONEY[4] if (x + y) % 5 else HONEY[6], 110)
    return im


def royal_jelly(side=True):
    im = img()
    rnd = random.Random(41 if side else 42)
    for y in range(16):
        for x in range(16):
            v = 0.5 + 0.25 * math.sin(x * 0.7 + y * 0.3) + 0.25 * math.sin(y * 0.9 - x * 0.2) + (rnd.random() - 0.5) * 0.2
            c = CREAM[3] if v > 0.85 else CREAM[2] if v > 0.45 else CREAM[1]
            put(im, x, y, c)
    for (x, y) in ((3, 3), (4, 3), (11, 9), (12, 9), (7, 12)):
        put(im, x, y, (255, 255, 250))
    if side:
        for x in range(16):
            put(im, x, 0, CREAM[0])
            put(im, x, 15, CREAM[0])
    return im


def heart_frames(n=8):
    """The Hive Heart: an amber core with dark veins that pulses (bright - dim - bright)."""
    frames = []
    for f in range(n):
        p = 0.5 + 0.5 * math.cos(2 * math.pi * f / n)
        im = img()
        for y in range(16):
            for x in range(16):
                d = math.hypot(x - 7.5, y - 7.5)
                vein = abs(math.sin(math.atan2(y - 7.5, x - 7.5) * 3 + d * 0.6)) < 0.18 and d > 2
                if x in (0, 15) or y in (0, 15):
                    c = WAX[0]
                elif vein:
                    c = shade(HONEY[0], 0.8 + 0.2 * p)
                elif d < 2.5 + p:
                    c = HONEY[6]
                elif d < 4.5 + p:
                    c = HONEY[5]
                elif d < 6.5:
                    c = shade(HONEY[4], 0.85 + 0.15 * p)
                else:
                    c = HONEY[2]
                put(im, x, y, c)
        frames.append(im)
    return frames


def strip(frames):
    w, h = frames[0].size
    out = Image.new("RGBA", (w, h * len(frames)))
    for i, f in enumerate(frames):
        out.paste(f, (0, i * h))
    return out


def honey_frames(size, n, flowing):
    """Still: slow swirling amber; flowing: the same streaked downwards (vanilla layout: 16 / 32 px frames)."""
    frames = []
    for f in range(n):
        im = img(size, size)
        t = 2 * math.pi * f / n
        for y in range(size):
            for x in range(size):
                u, v = x / size * 2 * math.pi, y / size * 2 * math.pi
                if flowing:
                    v = v + t
                    s = math.sin(u * 2 + math.sin(v) * 0.8) * 0.5 + math.sin(v * 3 + u) * 0.5
                else:
                    s = math.sin(u + t) * 0.4 + math.sin(v * 2 - t) * 0.35 + math.sin(u + v + t) * 0.25
                c = HONEY[6] if s > 0.75 else HONEY[5] if s > 0.3 else HONEY[4] if s > -0.4 else HONEY[3]
                put(im, x, y, c, 215)
        frames.append(im)
    return frames


# ---------------------------------------------------------------------------------------------------- item sprites
def sprite(rows, pal):
    im = img()
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in pal:
                put(im, x, y, pal[ch])
    return im


def bucket_sprite():
    rows = ["................",
            "................",
            "....kkkkkkkk....",
            "...k........k...",
            "...kHHHHHHHHk...",
            "..kHhhhHHHhhHk..",
            "..kSHHHHhHHHSk..",
            "..kSsHHHHHHsSk..",
            "...kSsssssSSk...",
            "...kSSsssSSSk...",
            "....kSSSSSSk....",
            "....kSSSSSSk....",
            ".....kkkkkk.....",
            "................",
            "................",
            "................"]
    return sprite(rows, {"k": (58, 58, 58), "S": (198, 198, 198), "s": (150, 150, 150), "H": HONEY[4],
                         "h": HONEY[6]})


def cookie_sprite():
    rows = ["................",
            "................",
            "................",
            ".....kkkkkk.....",
            "....kCCCCCCk....",
            "...kCChCCCCCk...",
            "..kCCHHhCCcCCk..",
            "..kCCHHCCCCCCk..",
            "..kCcCCCCHhCCk..",
            "..kCCCCCCHHCCk..",
            "...kCCcCCCCCk...",
            "....kCCCCCCk....",
            ".....kkkkkk.....",
            "................",
            "................",
            "................"]
    return sprite(rows, {"k": (120, 70, 26), "C": (226, 168, 82), "c": (180, 118, 48), "H": HONEY[3], "h": HONEY[6]})


def cake_item_sprite():
    rows = ["................",
            "................",
            "................",
            "................",
            "......hhhh......",
            "...hhHHHHHHhh...",
            "..hHHhHHHHhHHh..",
            "..kHHHHHHHHHHk..",
            "..kccccccccccK..",
            "..kHHHHHHHHHHK..",
            "..kccccccccccK..",
            "..kHHHHHHHHHHK..",
            "..kccccccccccK..",
            "...kkkkkkkkkk...",
            "................",
            "................"]
    return sprite(rows, {"k": CAKE[0], "K": shade(CAKE[0], 0.8), "c": CREAM[2], "H": HONEY[4], "h": HONEY[6]})


def cake_side():
    im = img()
    for y in range(8, 16):
        for x in range(1, 15):
            layer = (y - 8) // 2
            c = HONEY[5] if y == 8 else (CAKE[2] if layer % 2 else HONEY[3]) if y < 15 else CAKE[0]
            if layer % 2 and y % 2 == 1:
                c = CREAM[2]
            put(im, x, y, shade(c, 0.95 if x in (1, 14) else 1.0))
    return im


def cake_top():
    im = img()
    cells = hex_cells(size=4)
    for (x, y), (_c, rim) in cells.items():
        if 1 <= x <= 14 and 1 <= y <= 14:
            put(im, x, y, HONEY[4] if rim else HONEY[5] if (x + y) % 3 else HONEY[6])
    return im


def cake_bottom():
    im = img()
    for y in range(1, 15):
        for x in range(1, 15):
            put(im, x, y, CAKE[1] if (x + y) % 3 else CAKE[0])
    return im


def cake_inner():
    im = img()
    for y in range(8, 16):
        for x in range(1, 15):
            c = CREAM[2] if (y - 8) % 2 else HONEY[3]
            if y == 15:
                c = CAKE[0]
            put(im, x, y, c)
    return im


# =====================================================================================================================
# Models, blockstates, items
# =====================================================================================================================
def model(name, obj):
    write_json(os.path.join(ASSETS, "models", "block", name + ".json"), obj)


def item_model(name, model_ref):
    write_json(os.path.join(ASSETS, "items", name + ".json"), {"model": {"type": "minecraft:model", "model": model_ref}})


def flat_item(name):
    write_json(os.path.join(ASSETS, "models", "item", name + ".json"),
               {"parent": "minecraft:item/generated", "textures": {"layer0": T(name, "item")}})
    item_model(name, T(name, "item"))


def states(name, variants):
    write_json(os.path.join(ASSETS, "blockstates", name + ".json"), {"variants": variants})


def cube(name, all_=None, side=None, top=None, bottom=None, render=None):
    if all_ is not None:
        m = {"parent": "minecraft:block/cube_all", "textures": {"all": T(all_)}}
    else:
        m = {"parent": "minecraft:block/cube_bottom_top", "textures": {"side": T(side), "top": T(top), "bottom": T(bottom)}}
    if render:
        m["render_type"] = render
    model(name, m)
    states(name, {"": {"model": T(name)}})
    item_model(name, T(name))


def stairs_slab_wall(base, tex):
    stairs = "honeycomb_brick_stairs"
    slab = "honeycomb_brick_slab"
    wall = "honeycomb_brick_wall"
    t = {"bottom": T(tex), "top": T(tex), "side": T(tex)}
    for suffix, parent in (("", "stairs"), ("_inner", "inner_stairs"), ("_outer", "outer_stairs")):
        model(stairs + suffix, {"parent": f"minecraft:block/{parent}", "textures": t})
    variants = {}
    for facing, rot in (("east", 0), ("south", 90), ("west", 180), ("north", 270)):
        for half in ("bottom", "top"):
            for shape in ("straight", "inner_left", "inner_right", "outer_left", "outer_right"):
                m = stairs + ("" if shape == "straight" else "_inner" if shape.startswith("inner") else "_outer")
                extra = 0
                if shape.endswith("left"):
                    extra = 270 if half == "bottom" else 0
                elif shape.endswith("right"):
                    extra = 0 if half == "bottom" else 90
                y = (rot + extra) % 360
                v = {"model": T(m)}
                if half == "top":
                    v["x"] = 180
                if y:
                    v["y"] = y
                if half == "top" or y:
                    v["uvlock"] = True
                variants[f"facing={facing},half={half},shape={shape}"] = v
    states(stairs, variants)
    item_model(stairs, T(stairs))
    model(slab, {"parent": "minecraft:block/slab", "textures": t})
    model(slab + "_top", {"parent": "minecraft:block/slab_top", "textures": t})
    states(slab, {"type=bottom": {"model": T(slab)}, "type=top": {"model": T(slab + "_top")},
                  "type=double": {"model": T("honeycomb_bricks")}})
    item_model(slab, T(slab))
    model(wall + "_post", {"parent": "minecraft:block/template_wall_post", "textures": {"wall": T(tex)}})
    model(wall + "_side", {"parent": "minecraft:block/template_wall_side", "textures": {"wall": T(tex)}})
    model(wall + "_side_tall", {"parent": "minecraft:block/template_wall_side_tall", "textures": {"wall": T(tex)}})
    model(wall + "_inventory", {"parent": "minecraft:block/wall_inventory", "textures": {"wall": T(tex)}})
    parts = [{"when": {"up": "true"}, "apply": {"model": T(wall + "_post")}}]
    for d, rot in (("north", 0), ("east", 90), ("south", 180), ("west", 270)):
        for h, m in (("low", "_side"), ("tall", "_side_tall")):
            a = {"model": T(wall + m), "uvlock": True}
            if rot:
                a["y"] = rot
            parts.append({"when": {d: h}, "apply": a})
    write_json(os.path.join(ASSETS, "blockstates", wall + ".json"), {"multipart": parts})
    item_model(wall, T(wall + "_inventory"))
    return stairs, slab, wall


def cake_models():
    tex = {"particle": T("honey_cake_side"), "bottom": T("honey_cake_bottom"), "top": T("honey_cake_top"),
           "side": T("honey_cake_side"), "inside": T("honey_cake_inner")}
    model("honey_cake", {"parent": "minecraft:block/cake", "textures": tex})
    variants = {"bites=0": {"model": T("honey_cake")}}
    for b in range(1, 7):
        model(f"honey_cake_slice{b}", {"parent": f"minecraft:block/cake_slice{b}", "textures": tex})
        variants[f"bites={b}"] = {"model": T(f"honey_cake_slice{b}")}
    states("honey_cake", variants)
    flat_item("honey_cake")


def write_assets():
    save_tex(comb(11), "wild_comb")
    save_tex(drips(comb(12, filled=0.55, glossy=True), 13), "dripping_comb_side")
    save_tex(drips(comb(14, filled=0.7, glossy=True), 15, bottom=True), "dripping_comb_bottom")
    save_tex(comb(16, filled=0.5, glossy=True, dark_rate=0.05), "dripping_comb_top")
    save_tex(bricks(), "honeycomb_bricks")
    save_tex(window(), "comb_window")
    save_tex(royal_jelly(), "royal_jelly")
    save_tex(strip(heart_frames()), "hive_heart", frametime=3, interpolate=True)
    save_tex(strip(honey_frames(16, 32, False)), "honey_still", frametime=4, interpolate=True)
    save_tex(strip(honey_frames(32, 16, True)), "honey_flow", frametime=4, interpolate=True)
    save_tex(cake_side(), "honey_cake_side")
    save_tex(cake_top(), "honey_cake_top")
    save_tex(cake_bottom(), "honey_cake_bottom")
    save_tex(cake_inner(), "honey_cake_inner")
    for name, fn in (("honey_bucket", bucket_sprite), ("honey_cookie", cookie_sprite), ("honey_cake", cake_item_sprite)):
        save_tex(fn(), name, "item")
    cube("wild_comb", all_="wild_comb")
    cube("dripping_comb", side="dripping_comb_side", top="dripping_comb_top", bottom="dripping_comb_bottom")
    cube("honeycomb_bricks", all_="honeycomb_bricks")
    cube("comb_window", all_="comb_window", render="minecraft:translucent")
    cube("royal_jelly", all_="royal_jelly")
    cube("hive_heart", all_="hive_heart")
    stairs_slab_wall("honeycomb_bricks", "honeycomb_bricks")
    cake_models()
    # the fluid block: no model of its own beyond a particle (like vanilla water)
    model("honey", {"textures": {"particle": T("honey_still")}})
    states("honey", {f"level={i}": {"model": T("honey")} for i in range(16)})
    flat_item("honey_bucket")
    flat_item("honey_cookie")


# =====================================================================================================================
# Data: loot, recipes, tags
# =====================================================================================================================
def loot_block(name, pools):
    write_json(os.path.join(DATA, "loot_table", "blocks", name + ".json"),
               {"type": "minecraft:block", "pools": pools, "random_sequence": f"{MOD}:blocks/{name}"})


def self_drop(name, explosion=True):
    pool = {"rolls": 1, "bonus_rolls": 0, "entries": [{"type": "minecraft:item", "name": N(name)}]}
    if explosion:
        pool["conditions"] = [{"condition": "minecraft:survives_explosion"}]
    loot_block(name, [pool])


def item(name, weight, lo=1, hi=None, extra=None):
    e = {"type": "minecraft:item", "name": name if ":" in name else N(name), "weight": weight}
    fns = []
    if hi is not None and hi != lo or lo != 1:
        fns.append({"function": "minecraft:set_count", "count": {"type": "minecraft:uniform", "min": lo, "max": hi or lo}})
    fns += extra or []
    if fns:
        e["functions"] = fns
    return e


def chest(name, pools):
    write_json(os.path.join(DATA, "loot_table", "chests", name + ".json"),
               {"type": "minecraft:chest", "random_sequence": f"{MOD}:chests/{name}",
                "pools": [{"rolls": r, "bonus_rolls": 0, "entries": e} for r, e in pools]})


def uniform(a, b):
    return {"type": "minecraft:uniform", "min": a, "max": b}


def shaped(name, pattern, key, result, count=1, category="misc"):
    write_json(os.path.join(DATA, "recipe", name + ".json"), {
        "type": "minecraft:crafting_shaped", "category": category, "pattern": pattern,
        "key": {k: v for k, v in key.items()}, "result": {"id": result, "count": count}})


def shapeless(name, ingredients, result, count=1, category="misc"):
    write_json(os.path.join(DATA, "recipe", name + ".json"), {
        "type": "minecraft:crafting_shapeless", "category": category, "ingredients": ingredients,
        "result": {"id": result, "count": count}})


def stonecut(name, ingredient, result, count=1):
    write_json(os.path.join(DATA, "recipe", name + ".json"), {
        "type": "minecraft:stonecutting", "ingredient": ingredient, "result": {"id": result, "count": count}})


def tag(path, values, namespace="minecraft"):
    base = os.path.join(ROOT_DATA, namespace, "tags", *path.split("/")) + ".json"
    old = []
    if os.path.exists(base):
        with open(base, encoding="utf-8") as f:
            old = json.load(f).get("values", [])
    write_json(base, {"replace": False, "values": sorted(set(old) | set(values), key=str)})


ROOT_DATA = os.path.dirname(DATA)


def write_data():
    for b in ("wild_comb", "dripping_comb", "honeycomb_bricks", "honeycomb_brick_stairs", "honeycomb_brick_wall",
              "comb_window", "royal_jelly"):
        self_drop(b)
    loot_block("honeycomb_brick_slab", [{"rolls": 1, "bonus_rolls": 0, "entries": [{
        "type": "minecraft:item", "name": N("honeycomb_brick_slab"), "functions": [{
            "function": "minecraft:set_count", "count": 2, "add": False, "conditions": [{
                "condition": "minecraft:block_state_property", "block": N("honeycomb_brick_slab"),
                "properties": {"type": "double"}}]}, {"function": "minecraft:explosion_decay"}]}]}])
    # the heart: royal jelly and comb, never itself
    loot_block("hive_heart", [
        {"rolls": 1, "bonus_rolls": 0, "entries": [item("royal_jelly", 1, 1, 2)]},
        {"rolls": 1, "bonus_rolls": 0, "entries": [item("minecraft:honeycomb", 1, 2, 5)]}])
    loot_block("honey_cake", [])
    # hive chests
    common = [item("minecraft:honeycomb", 14, 2, 6), item("minecraft:honey_bottle", 12, 1, 3),
              item("honey_cookie", 10, 3, 8), item("minecraft:sunflower", 4, 1, 3), item("minecraft:oxeye_daisy", 4, 1, 3),
              item("minecraft:cornflower", 4, 1, 3), item("minecraft:dandelion", 4, 1, 4), item("minecraft:bread", 5, 1, 3),
              item("minecraft:candle", 5, 1, 3), item("minecraft:gold_nugget", 6, 2, 8), item("minecraft:glass_bottle", 6, 1, 3)]
    chest("giant_hive", [(uniform(3, 6), common),
                         (uniform(0, 1), [item("honey_bucket", 3), item("minecraft:honey_block", 3),
                                          item("minecraft:gold_ingot", 2, 1, 3), {"type": "minecraft:empty", "weight": 6}])])
    chest("giant_hive_heart", [(uniform(3, 5), common + [item("royal_jelly", 4, 1, 2), item("honey_bucket", 4)]),
                               (1, [item("minecraft:golden_apple", 4), item("minecraft:book", 4, extra=[
                                   {"function": "minecraft:enchant_randomly"}]),
                                   item("minecraft:honey_block", 3, 1, 2), item("minecraft:golden_carrot", 3, 2, 5),
                                   item("minecraft:enchanted_golden_apple", 1)]),
                               (uniform(0, 1), [item("minecraft:name_tag", 1), item("minecraft:emerald", 3, 1, 4),
                                                {"type": "minecraft:empty", "weight": 4}])])
    # recipes
    hb, hc = "minecraft:honey_bottle", "minecraft:honeycomb"
    shaped("honeycomb_bricks", ["CC", "CC"], {"C": "minecraft:honeycomb_block"}, N("honeycomb_bricks"), 4, "building")
    shaped("honeycomb_brick_stairs", ["B  ", "BB ", "BBB"], {"B": N("honeycomb_bricks")}, N("honeycomb_brick_stairs"), 4,
           "building")
    shaped("honeycomb_brick_slab", ["BBB"], {"B": N("honeycomb_bricks")}, N("honeycomb_brick_slab"), 6, "building")
    shaped("honeycomb_brick_wall", ["BBB", "BBB"], {"B": N("honeycomb_bricks")}, N("honeycomb_brick_wall"), 6, "building")
    for src in ("minecraft:honeycomb_block", N("honeycomb_bricks")):
        tagname = src.split(":")[1]
        if src != N("honeycomb_bricks"):
            stonecut(f"honeycomb_bricks_from_{tagname}_stonecutting", src, N("honeycomb_bricks"))
        stonecut(f"honeycomb_brick_stairs_from_{tagname}_stonecutting", src, N("honeycomb_brick_stairs"))
        stonecut(f"honeycomb_brick_slab_from_{tagname}_stonecutting", src, N("honeycomb_brick_slab"), 2)
        stonecut(f"honeycomb_brick_wall_from_{tagname}_stonecutting", src, N("honeycomb_brick_wall"))
    shaped("wild_comb", ["CC", "CC"], {"C": hc}, N("wild_comb"), 1, "building")
    shapeless("dripping_comb", [N("wild_comb"), hb], N("dripping_comb"), 1, "building")
    shaped("comb_window", [" C ", "CGC", " C "], {"C": hc, "G": "minecraft:glass"}, N("comb_window"), 2, "building")
    shapeless("honey_bucket", ["minecraft:bucket", hb, hb, hb, hb], N("honey_bucket"))
    shapeless("honey_bottles_from_honey_bucket", [N("honey_bucket"), "minecraft:glass_bottle", "minecraft:glass_bottle",
                                                  "minecraft:glass_bottle", "minecraft:glass_bottle"], hb, 4)
    shaped("honey_cookie", ["WHW"], {"W": "minecraft:wheat", "H": hb}, N("honey_cookie"), 8, "misc")
    shaped("honey_cake", ["HHH", "SEM", "WWW"], {"H": hb, "S": "minecraft:sugar", "E": "#minecraft:eggs",
                                                  "M": "minecraft:milk_bucket", "W": "minecraft:wheat"}, N("honey_cake"), 1)
    # tags
    tag("block/mineable/axe", [N(b) for b in ("wild_comb", "dripping_comb", "honeycomb_bricks", "honeycomb_brick_stairs",
                                              "honeycomb_brick_slab", "honeycomb_brick_wall", "comb_window", "hive_heart")])
    tag("block/walls", [N("honeycomb_brick_wall")])
    tag("block/stairs", [N("honeycomb_brick_stairs")])
    tag("block/slabs", [N("honeycomb_brick_slab")])
    tag("item/walls", [N("honeycomb_brick_wall")])
    tag("item/stairs", [N("honeycomb_brick_stairs")])
    tag("item/slabs", [N("honeycomb_brick_slab")])
    tag("fluid/honey", [N("honey"), N("flowing_honey")], MOD)
    # breaking these near a Hive Heart raises the alarm (HiveEvents.HIVE_MATERIAL)
    tag("block/hive_material", [N("wild_comb"), N("dripping_comb"), N("royal_jelly"), "minecraft:honeycomb_block",
                                "minecraft:honey_block", "minecraft:bee_nest", "minecraft:beehive"], MOD)


# =====================================================================================================================
# NBT (structure templates)
# =====================================================================================================================
class Tag:
    def __init__(self, kind, value):
        self.kind, self.value = kind, value


def Byte(v):
    return Tag(1, v)


def Int(v):
    return Tag(3, v)


def Double(v):
    return Tag(6, v)


def Str(v):
    return Tag(8, v)


def ListT(kind, items):
    return Tag(9, (kind, items))


def Comp(d):
    return Tag(10, d)


def _w(out, t):
    k, v = t.kind, t.value
    if k == 1:
        out.write(struct.pack(">b", v))
    elif k == 3:
        out.write(struct.pack(">i", v))
    elif k == 6:
        out.write(struct.pack(">d", v))
    elif k == 8:
        b = v.encode("utf-8")
        out.write(struct.pack(">H", len(b)) + b)
    elif k == 9:
        kind, items = v
        out.write(struct.pack(">bi", kind if items else (kind or 0), len(items)))
        for it in items:
            _w(out, it)
    elif k == 10:
        for name, val in v.items():
            out.write(struct.pack(">b", val.kind))
            nb = name.encode("utf-8")
            out.write(struct.pack(">H", len(nb)) + nb)
            _w(out, val)
        out.write(b"\x00")


def nbt_file(path, root):
    buf = io.BytesIO()
    buf.write(b"\x0a\x00\x00")
    _w(buf, root)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with gzip.GzipFile(path, "wb", mtime=0) as f:
        f.write(buf.getvalue())


DATA_VERSION = 4671


def js_to_nbt(v):
    """Plain python values -> tags (dict -> compound, str -> string, int -> int, bool -> byte, float -> double)."""
    if isinstance(v, Tag):
        return v
    if isinstance(v, bool):
        return Byte(1 if v else 0)
    if isinstance(v, int):
        return Int(v)
    if isinstance(v, float):
        return Double(v)
    if isinstance(v, str):
        return Str(v)
    if isinstance(v, dict):
        return Comp({k: js_to_nbt(x) for k, x in v.items()})
    if isinstance(v, list):
        items = [js_to_nbt(x) for x in v]
        return ListT(items[0].kind if items else 0, items)
    raise TypeError(v)


# =====================================================================================================================
# The hive templates
# =====================================================================================================================
AIR = "minecraft:air"
P_BOOL = ("true", "false")
HORIZ = ("north", "east", "south", "west")
VANILLA = {   # the vanilla states the templates use, with their full property sets
    "minecraft:air": {}, "minecraft:dirt": {}, "minecraft:coarse_dirt": {}, "minecraft:rooted_dirt": {},
    "minecraft:moss_block": {}, "minecraft:honeycomb_block": {}, "minecraft:honey_block": {},
    "minecraft:grass_block": {"snowy": P_BOOL}, "minecraft:oak_log": {"axis": ("x", "y", "z")},
    "minecraft:oak_wood": {"axis": ("x", "y", "z")},
    "minecraft:oak_leaves": {"distance": tuple(str(i) for i in range(1, 8)), "persistent": P_BOOL, "waterlogged": P_BOOL},
    "minecraft:bee_nest": {"facing": HORIZ, "honey_level": tuple(str(i) for i in range(6))},
    "minecraft:beehive": {"facing": HORIZ, "honey_level": tuple(str(i) for i in range(6))},
    "minecraft:chest": {"facing": HORIZ, "type": ("single", "left", "right"), "waterlogged": P_BOOL},
    "minecraft:barrel": {"facing": HORIZ + ("up", "down"), "open": P_BOOL},
    "minecraft:poppy": {}, "minecraft:dandelion": {}, "minecraft:oxeye_daisy": {}, "minecraft:cornflower": {},
    "minecraft:allium": {}, "minecraft:azure_bluet": {}, "minecraft:lily_of_the_valley": {},
    "minecraft:short_grass": {}, "minecraft:candle": {"candles": ("1", "2", "3", "4"), "lit": P_BOOL, "waterlogged": P_BOOL},
    "minecraft:vine": {d: P_BOOL for d in ("north", "east", "south", "west", "up")},
}
MODB = {N("wild_comb"): {}, N("dripping_comb"): {}, N("honeycomb_bricks"): {}, N("royal_jelly"): {}, N("hive_heart"): {},
        N("comb_window"): {}, N("honey"): {"level": tuple(str(i) for i in range(16))}}
SOLID = {"minecraft:dirt", "minecraft:coarse_dirt", "minecraft:rooted_dirt", "minecraft:moss_block",
         "minecraft:honeycomb_block", "minecraft:honey_block", "minecraft:grass_block", "minecraft:oak_log",
         "minecraft:oak_wood", "minecraft:bee_nest", "minecraft:beehive", "minecraft:barrel",
         N("wild_comb"), N("dripping_comb"), N("honeycomb_bricks"), N("royal_jelly"), N("hive_heart"), N("comb_window")}
FLOWERS = ["minecraft:poppy", "minecraft:dandelion", "minecraft:oxeye_daisy", "minecraft:cornflower",
           "minecraft:allium", "minecraft:azure_bluet", "minecraft:lily_of_the_valley"]


def S(name, **props):
    return (name if ":" in name else N(name), {k: str(v).lower() for k, v in props.items()}, None)


S_AIR = S(AIR)
COMB = S("wild_comb")
DRIP = S("dripping_comb")
HCB = S("minecraft:honeycomb_block")
HONEYB = S("minecraft:honey_block")
JELLY = S("royal_jelly")
HONEY_SRC = S("honey", level=0)


class Hive:
    def __init__(self, name, size, seed, ground):
        self.name = name
        self.W, self.H, self.D = size
        self.b = {}
        self.ents = []
        self.rnd = random.Random(seed)
        self.G = ground
        self.info = {"honey": 0, "nests": 0, "bees_in_nests": 0, "bees": 0, "chests": 0}

    def inside(self, x, y, z):
        return 0 <= x < self.W and 0 <= y < self.H and 0 <= z < self.D

    def set(self, x, y, z, st):
        if self.inside(x, y, z):
            self.b[(x, y, z)] = st

    def get(self, x, y, z):
        s = self.b.get((x, y, z))
        return s[0] if s else None

    def solid(self, x, y, z):
        return self.get(x, y, z) in SOLID

    def bee(self, x, y, z):
        self.ents.append(((x, y, z), {"id": "minecraft:bee", "PersistenceRequired": True}))
        self.info["bees"] += 1

    def nest(self, x, y, z, facing, bees, honey):
        occupants = [{"entity_data": {"id": "minecraft:bee"}, "min_ticks_in_hive": 600, "ticks_in_hive": 0}
                     for _ in range(bees)]
        self.b[(x, y, z)] = ("minecraft:bee_nest", {"facing": facing, "honey_level": str(honey)},
                             js_to_nbt({"id": "minecraft:beehive", "bees": occupants}))
        self.info["nests"] += 1
        self.info["bees_in_nests"] += bees

    def chest(self, x, y, z, facing, table):
        if not self.solid(x, y - 1, z):
            self.set(x, y - 1, z, HCB)
        self.b[(x, y, z)] = ("minecraft:chest", {"facing": facing, "type": "single", "waterlogged": "false"},
                             js_to_nbt({"id": "minecraft:chest", "LootTable": f"{MOD}:chests/{table}"}))
        self.info["chests"] += 1

    def nbt(self):
        palette, index, blocks = [], {}, []
        for (x, y, z) in sorted(self.b, key=lambda p: (p[1], p[2], p[0])):
            name, props, be = self.b[(x, y, z)]
            key = (name, tuple(sorted(props.items())))
            if key not in index:
                index[key] = len(palette)
                e = {"Name": Str(name)}
                if props:
                    e["Properties"] = Comp({k: Str(v) for k, v in sorted(props.items())})
                palette.append(Comp(e))
            e = {"pos": ListT(3, [Int(x), Int(y), Int(z)]), "state": Int(index[key])}
            if be is not None:
                e["nbt"] = be
            blocks.append(Comp(e))
        ents = []
        for (x, y, z), data in self.ents:
            ents.append(Comp({"pos": ListT(6, [Double(x + 0.5), Double(y + 0.2), Double(z + 0.5)]),
                              "blockPos": ListT(3, [Int(x), Int(y), Int(z)]), "nbt": js_to_nbt(data)}))
        return Comp({"DataVersion": Int(DATA_VERSION), "size": ListT(3, [Int(self.W), Int(self.H), Int(self.D)]),
                     "palette": ListT(10, palette), "blocks": ListT(10, blocks), "entities": ListT(10, ents)})


def blob(centers):
    """A lumpy mass: the union of spheres [(cx, cy, cz, r)] (r may be a (rx, ry, rz) tuple)."""
    cells = set()
    for (cx, cy, cz, r) in centers:
        rx, ry, rz = r if isinstance(r, tuple) else (r, r, r)
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
                for z in range(int(cz - rz) - 1, int(cz + rz) + 2):
                    if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 + ((z - cz) / rz) ** 2 <= 1.0:
                        cells.add((x, y, z))
    return cells


def tube(points, r):
    """A winding tunnel through the points (spheres every half block along the polyline)."""
    centers = []
    for (a, b) in zip(points, points[1:]):
        n = max(1, int(math.dist(a, b) * 2))
        for i in range(n + 1):
            t = i / n
            centers.append(tuple(a[k] + (b[k] - a[k]) * t for k in range(3)) + (r,))
    return blob(centers)


NEIGH6 = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))


def build_mass(h, mass, rooms, tunnels, reservoir, heart_room, brood_rooms, cache_room):
    """Fills the comb mass, carves the rooms and tunnels, dresses walls, puts the honey pool, the heart, the nests."""
    rnd = h.rnd
    hollow = set().union(*rooms, *tunnels) & set(p for p in mass) | set().union(*tunnels)
    hollow = {p for p in hollow if h.inside(*p) and p[1] > h.G}
    for p in mass:
        if h.inside(*p) and h.get(*p) not in ("minecraft:oak_log", "minecraft:oak_wood"):
            r = rnd.random()
            h.set(*p, HCB if r < 0.22 else HONEYB if r < 0.26 else COMB)
    for p in hollow:
        if h.get(*p) not in ("minecraft:oak_log", "minecraft:oak_wood"):
            h.set(*p, S_AIR)
    # walls: comb with drips under every ceiling cell
    for (x, y, z) in hollow:
        if h.get(x, y, z) != AIR:
            continue
        up = (x, y + 1, z)
        if h.get(*up) in (N("wild_comb"), "minecraft:honeycomb_block") and rnd.random() < 0.45:
            h.set(*up, DRIP)
    # the honey reservoir: a basin under the reservoir room's floor, every source on solid comb
    pool = 0
    for (x, y, z) in sorted(reservoir):
        if not h.inside(x, y, z):
            continue
        ok = all(h.solid(x + dx, y + dy, z + dz) or (x + dx, y + dy, z + dz) in reservoir
                 for (dx, dy, dz) in NEIGH6 if dy <= 0)
        if ok:
            h.set(x, y, z, HONEY_SRC)
            pool += 1
    h.info["honey"] = pool
    # basin rim: anything next to honey that is not honey or air above must be solid
    for (x, y, z), st in list(h.b.items()):
        if st[0] == N("honey"):
            for dx, dy, dz in NEIGH6:
                q = (x + dx, y + dy, z + dz)
                if dy == 1:
                    continue
                if h.get(*q) not in SOLID and h.get(*q) != N("honey"):
                    h.set(*q, HCB)
    # the heart: on a royal jelly plinth, jelly in the walls of its chamber
    hx, hy, hz = heart_room
    h.set(hx, hy - 1, hz, JELLY)
    h.set(hx, hy, hz, S("hive_heart"))
    for (x, y, z) in blob([(hx, hy + 1, hz, 4.6)]):
        if h.get(x, y, z) in (N("wild_comb"), "minecraft:honeycomb_block", N("dripping_comb")) and rnd.random() < 0.3:
            h.set(x, y, z, JELLY)
    # brood chambers: bee nests set into the walls, facing into the room
    for (cx, cy, cz) in brood_rooms:
        placed = 0
        for (dx, dz, facing) in ((3, 0, "west"), (-3, 0, "east"), (0, 3, "north"), (0, -3, "south")):
            x, y, z = cx + dx, cy, cz + dz
            ox, oz = {"west": (-1, 0), "east": (1, 0), "north": (0, -1), "south": (0, 1)}[facing]
            for k in range(3):
                px, pz = x - ox * k, z - oz * k
                if h.solid(px, y, pz) and h.get(px + ox, y, pz + oz) == AIR:
                    h.nest(px, y, pz, facing, bees=1 + (placed % 2), honey=5 if placed % 2 == 0 else 3)
                    placed += 1
                    break
    # loot: the heart chest beside the heart, a cache chest in the hidden pocket
    return pool


def floor_of(h, x, z, y0):
    for y in range(y0, h.G - 1, -1):
        if h.get(x, y, z) != AIR and h.get(x, y, z) is not None:
            return y
    return None


def ground(h, R, rnd, cx, cz):
    """The site: a grass disc with dirt below, flowers round the hive, explicit air above (clears the meadow)."""
    G = h.G
    for x in range(h.W):
        for z in range(h.D):
            d = math.hypot(x - cx, z - cz)
            if d > R:
                continue
            h.set(x, G - 1, z, S("minecraft:dirt"))
            h.set(x, G, z, S("minecraft:grass_block", snowy=False) if rnd.random() < 0.85 else S("minecraft:coarse_dirt"))


def flowers(h, R, rnd, cx, cz, n=40):
    G = h.G
    for _ in range(n):
        a = rnd.random() * 2 * math.pi
        r = R * (0.55 + 0.45 * rnd.random())
        x, z = int(cx + math.cos(a) * r), int(cz + math.sin(a) * r)
        if h.get(x, G, z) == "minecraft:grass_block" and h.get(x, G + 1, z) in (None, AIR):
            h.set(x, G + 1, z, S(rnd.choice(FLOWERS)))


def clear_air(h, height):
    """Explicit air over the whole footprint (the meadow's grass and saplings must not stand in the hive)."""
    cols = {(x, z) for (x, y, z) in h.b}
    for (x, z) in cols:
        for y in range(h.G + 1, min(h.H, h.G + 1 + height)):
            if (x, y, z) not in h.b:
                h.b[(x, y, z)] = S_AIR


def oak(h, x0, z0, top, rnd):
    """A giant old oak: a 2 x 2 trunk with buttress roots, three heavy boughs and a broad crown."""
    G = h.G
    for x in (x0, x0 + 1):
        for z in (z0, z0 + 1):
            for y in range(G - 1, top + 1):
                h.set(x, y, z, S("minecraft:oak_log", axis="y"))
    for (dx, dz) in ((-1, 0), (2, 1), (0, 2), (1, -1), (-1, 1), (2, 0)):
        for y in range(G, G + 2 + rnd.randrange(2)):
            h.set(x0 + dx, y, z0 + dz, S("minecraft:oak_wood", axis="y"))
    boughs = []
    for (ax, az, y) in ((1, 0, top - 5), (-1, 1, top - 3), (0, -1, top - 1), (1, 1, top)):
        x, z = x0 + 0.5, z0 + 0.5
        for k in range(1, 7):
            x += ax * 0.9
            z += az * 0.9
            yy = y + k // 3
            axis = "x" if abs(ax) >= abs(az) else "z"
            h.set(int(round(x)), yy, int(round(z)), S("minecraft:oak_log", axis=axis))
        boughs.append((int(round(x)), y + 2, int(round(z))))
    crown = [(x0 + 0.5, top + 2, z0 + 0.5, (6.5, 3.5, 6.5))] + [(bx, by, bz, (3.8, 2.6, 3.8)) for (bx, by, bz) in boughs]
    for p in blob(crown):
        if h.inside(*p) and h.get(*p) in (None, AIR):
            if rnd.random() < 0.93:
                h.set(*p, S("minecraft:oak_leaves", distance=1, persistent=True, waterlogged=False))


def build_tree_hive():
    """A giant hive that has swallowed the lower half of an old oak: a lumpy comb mass 21 x 16 x 20 round the trunk,
    a ramp of slumped comb up to the entrance, the honey reservoir in its belly, brood chambers, the heart."""
    W, H, D, G = 32, 38, 32, 1
    h = Hive("giant_hive/tree", (W, H, D), seed=7101, ground=G)
    rnd = h.rnd
    cx, cz = 15, 15
    ground(h, 15.5, rnd, cx + 0.5, cz + 0.5)
    oak(h, cx - 7, cz + 4, 29, rnd)            # the old oak stands at the hive's west flank, its trunk in the comb
    mass = blob([(cx + 0.5, 10, cz + 0.5, (10, 8, 9.5)), (cx + 5, 7, cz - 3, 5.5), (cx - 4, 12, cz + 4, 6),
                 (cx + 2, 15, cz + 5, 5), (cx - 5, 6, cz - 2, 5), (cx + 6, 12, cz + 4, 4.5), (cx, 4, cz + 6, 4.5),
                 (cx + 1, 17, cz - 3, 4)])
    mass = {p for p in mass if p[1] >= G}
    heart = (cx - 3, 9, cz + 3)
    rooms = [blob([(heart[0], heart[1] + 1.5, heart[2], (3.5, 2.6, 3.5))]),     # the heart chamber
             blob([(cx + 4, 6, cz - 3, (3.4, 2.4, 3.2))]),                         # brood A
             blob([(cx + 3, 13, cz + 3, (3.2, 2.2, 3.2))]),                        # brood B
             blob([(cx - 4, 4, cz - 3, (3.5, 2.0, 3.0))]),                         # the reservoir chamber
             blob([(cx + 1, 16, cz - 3, (2.2, 1.6, 2.2))])]                        # the hidden cache
    tunnels = [tube([(cx + 12, 2, cz - 2), (cx + 8, 3, cz - 3), (cx + 5, 5, cz - 3)], 1.4),   # the entrance
               tube([(cx + 4, 6, cz - 3), (cx + 3, 8, cz + 1), (cx - 1, 9, cz + 4), heart], 1.3),
               tube([(cx + 3, 6, cz - 3), (cx - 1, 5, cz - 4), (cx - 4, 4, cz - 3)], 1.3),
               tube([heart, (cx, 11, cz + 5), (cx + 3, 13, cz + 3)], 1.2),
               tube([(cx + 3, 13, cz + 3), (cx + 4, 15, cz - 1), (cx + 1, 16, cz - 3)], 1.0)]
    reservoir = {(x, y, z) for (x, y, z) in blob([(cx - 4, 3, cz - 3, (2.6, 1.2, 2.2))]) if y in (2, 3)}
    # the slumped comb ramp from the meadow to the entrance (so a player can walk in)
    ramp = blob([(cx + 12, 0.5, cz - 2, (3.5, 2.0, 3.0)), (cx + 9, 1.5, cz - 2.5, (3.2, 2.4, 3.2))])
    mass |= {p for p in ramp if p[1] >= G}
    pool = build_mass(h, mass, rooms, tunnels, reservoir, heart, [(cx + 4, 6, cz - 3), (cx + 3, 13, cz + 3)],
                      (cx + 1, 16, cz - 3))
    # the entrance mouth must be open to the meadow
    for p in tube([(cx + 15, 2, cz - 2), (cx + 11, 2, cz - 2)], 1.4):
        if h.inside(*p) and p[1] > G:
            h.set(*p, S_AIR)
    h.chest(heart[0] + 2, heart[1], heart[2], "west", "giant_hive_heart")
    h.chest(cx + 1, 15, cz - 3, "south", "giant_hive")
    h.set(cx + 4, 5, cz - 1, S("minecraft:barrel", facing="up", open=False))
    h.b[(cx + 4, 5, cz - 1)] = ("minecraft:barrel", {"facing": "up", "open": "false"},
                                js_to_nbt({"id": "minecraft:barrel", "LootTable": f"{MOD}:chests/giant_hive"}))
    # nests on the outside of the hive and on the oak's boughs; vanilla bees round the flowers
    for (x, y, z, f) in ((cx - 4, 25, cz + 3, "east"), (cx - 9, 24, cz + 6, "west")):
        if h.get(x, y, z) in (None, AIR, "minecraft:oak_leaves"):
            h.nest(x, y, z, f, bees=3, honey=5)
    for (x, y, z) in ((cx + 13, 3, cz - 6), (cx + 11, 4, cz + 3), (cx - 9, 3, cz + 9), (cx + 6, 6, cz + 11)):
        if h.get(x, y, z) in (None, AIR):
            h.bee(x, y, z)
    flowers(h, 14.5, rnd, cx + 0.5, cz + 0.5, 60)
    clear_air(h, 34)
    return h


def build_dome_hive():
    """A free-standing wild hive on the ground: a lumpy honeycomb dome 24 x 14 x 22 half sunk into the meadow, its
    entrance at ground level, the reservoir and the heart deep inside."""
    W, H, D, G = 30, 20, 30, 1
    h = Hive("giant_hive/dome", (W, H, D), seed=7202, ground=G)
    rnd = h.rnd
    cx, cz = 14.5, 14.5
    ground(h, 14.5, rnd, cx, cz)
    for x in range(W):
        for z in range(D):
            if math.hypot(x - cx, z - cz) <= 14.5:
                for y in range(0, G - 1):
                    h.set(x, y, z, S("minecraft:dirt"))
    mass = blob([(cx, G + 2, cz, (11.5, 8, 10.5)), (cx + 6, G + 4, cz - 4, 5.5), (cx - 6, G + 5, cz + 3, 5.5),
                 (cx + 2, G + 8, cz + 3, 5), (cx - 3, G + 1, cz - 6, 5.5), (cx + 7, G + 1, cz + 6, 4.5),
                 (cx - 1, G + 10, cz - 1, 4)])
    mass = {p for p in mass if p[1] >= 0}
    heart = (int(cx), G + 3, int(cz))
    rooms = [blob([(heart[0], heart[1] + 1.5, heart[2], (3.8, 2.6, 3.6))]),
             blob([(cx + 6, G + 2, cz - 4, (3.2, 2.2, 3.0))]),
             blob([(cx - 6, G + 4, cz + 3, (3.2, 2.2, 3.0))]),
             blob([(cx - 3, G + 1.2, cz - 6, (3.4, 2.0, 3.0))]),
             blob([(cx + 1, G + 8, cz + 2, (2.0, 1.4, 2.0))])]
    tunnels = [tube([(cx + 14, G + 1, cz + 1), (cx + 9, G + 1, cz), (cx + 6, G + 2, cz - 3)], 1.4),
               tube([(cx + 6, G + 2, cz - 4), (cx + 3, G + 3, cz - 1), heart], 1.3),
               tube([heart, (cx - 3, G + 4, cz + 2), (cx - 6, G + 4, cz + 3)], 1.3),
               tube([(cx - 6, G + 4, cz + 3), (cx - 5, G + 2, cz - 2), (cx - 3, G, cz - 6)], 1.2),
               tube([(cx - 6, G + 4, cz + 3), (cx - 3, G + 6, cz + 3), (cx + 1, G + 8, cz + 2)], 1.0)]
    reservoir = {(x, y, z) for (x, y, z) in blob([(cx - 3, G + 0.5, cz - 6, (2.6, 1.2, 2.2))]) if y in (G, G + 1)}
    build_mass(h, mass, rooms, tunnels, reservoir, heart, [(int(cx + 6), G + 2, int(cz - 4)), (int(cx - 6), G + 4, int(cz + 3))],
               (int(cx + 1), G + 8, int(cz + 2)))
    for p in tube([(cx + 17, G + 1, cz + 1), (cx + 12, G + 1, cz + 1)], 1.4):
        if h.inside(*p) and p[1] > G:
            h.set(*p, S_AIR)
    h.chest(heart[0] - 2, heart[1], heart[2], "east", "giant_hive_heart")
    h.chest(int(cx + 1), G + 8, int(cz + 3), "north", "giant_hive")
    for (x, y, z) in ((int(cx + 14), G + 3, int(cz - 5)), (int(cx - 12), G + 2, int(cz + 8)), (int(cx + 4), G + 13, int(cz)),
                      (int(cx + 10), G + 5, int(cz + 9))):
        if h.get(x, y, z) in (None, AIR):
            h.bee(x, y, z)
    flowers(h, 14, rnd, cx, cz, 55)
    clear_air(h, H - G - 1)
    return h


def fix_honey_floor(h):
    """Reservoir sources sit at the room floor: the template reservoir y range must be inside carved space; make sure
    no honey source has air beside or below it (it would flow out)."""
    bad = []
    for (x, y, z), st in h.b.items():
        if st[0] != N("honey"):
            continue
        for dx, dy, dz in NEIGH6:
            if dy == 1:
                continue
            n = h.get(x + dx, y + dy, z + dz)
            if n not in SOLID and n != N("honey"):
                bad.append((x, y, z))
    return bad


def audit(h):
    problems = []
    for (x, y, z), (name, props, _nbt) in h.b.items():
        schema = VANILLA.get(name) if name.startswith("minecraft:") else MODB.get(name)
        if schema is None:
            problems.append(f"unknown block {name}")
        elif set(props) != set(schema) or any(v not in schema[k] for k, v in props.items()):
            problems.append(f"bad state {name}{props}")
        if name in FLOWERS and h.get(x, y - 1, z) != "minecraft:grass_block":
            problems.append(f"flower {name} at {(x, y, z)} not on grass")
        if name in ("minecraft:chest", "minecraft:barrel") and not h.solid(x, y - 1, z):
            problems.append(f"{name} at {(x, y, z)} floats")
    problems += [f"honey leaks at {p}" for p in fix_honey_floor(h)]
    heart = [p for p, s in h.b.items() if s[0] == N("hive_heart")]
    if len(heart) != 1:
        problems.append(f"{len(heart)} hearts")
    for (x, y, z), _d in h.ents:
        if h.get(x, y, z) not in (None, AIR):
            problems.append(f"bee at {(x, y, z)} inside {h.get(x, y, z)}")
    if h.info["honey"] < 6:
        problems.append(f"only {h.info['honey']} honey sources")
    # the heart must be reachable from the entrance through open air (2 high)
    if problems:
        raise SystemExit(f"giant_hive.py: {h.name}:\n  " + "\n  ".join(problems[:40]))


def reach(h, start, goal):
    seen, todo = {start}, [start]
    while todo:
        x, y, z = todo.pop()
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            for dy in (1, 0, -1, -2):
                p = (x + dx, y + dy, z + dz)
                if p in seen or not h.inside(*p):
                    continue
                free = lambda q: h.get(*q) in (None, AIR) and q[1] > h.G - 1   # noqa: E731
                if free(p) and free((p[0], p[1] + 1, p[2])) and (h.solid(p[0], p[1] - 1, p[2])
                                                                 or h.get(p[0], p[1] - 1, p[2]) == N("honey")):
                    if dy > 0 and not free((x, y + 2, z)):
                        continue
                    seen.add(p)
                    todo.append(p)
    return any(math.dist(p, goal) <= 2.5 for p in seen)


TEMPLATES = {"giant_hive/tree": build_tree_hive, "giant_hive/dome": build_dome_hive}
INFO = {}


def write_templates():
    for path, fn in TEMPLATES.items():
        h = fn()
        audit(h)
        heart = next(p for p, s in h.b.items() if s[0] == N("hive_heart"))
        entrance = {"giant_hive/tree": (30, 2, 13), "giant_hive/dome": (29, 2, 15)}[path]
        if not reach(h, entrance, heart):
            raise SystemExit(f"giant_hive.py: {path}: the heart cannot be reached from the entrance")
        nbt_file(os.path.join(DATA, "structure", *path.split("/")) + ".nbt", h.nbt())
        INFO[path] = dict(h.info, blocks=len(h.b), size=(h.W, h.H, h.D), heart=heart)


# =====================================================================================================================
# Worldgen
# =====================================================================================================================
BIOMES = ["minecraft:flower_forest", "minecraft:meadow", "minecraft:plains", "minecraft:sunflower_plains",
          "minecraft:birch_forest", "minecraft:old_growth_birch_forest", "minecraft:cherry_grove", "minecraft:forest"]


def write_worldgen():
    wg = os.path.join(DATA, "worldgen")
    write_json(os.path.join(ROOT_DATA, MOD, "tags", "worldgen", "biome", "has_structure", "giant_hive.json"),
               {"values": BIOMES})
    write_json(os.path.join(wg, "template_pool", "giant_hive", "start.json"), {"fallback": "minecraft:empty", "elements": [
        {"weight": w, "element": {"element_type": "minecraft:single_pool_element", "location": N(path),
                                  "processors": "minecraft:empty", "projection": "rigid"}}
        for path, w in (("giant_hive/tree", 3), ("giant_hive/dome", 2))]})
    write_json(os.path.join(wg, "structure", "giant_hive.json"), {
        "type": N("dry_jigsaw"), "max_relief": 6,
        "biomes": f"#{MOD}:has_structure/giant_hive", "step": "surface_structures",
        "spawn_overrides": {}, "terrain_adaptation": "beard_thin", "start_pool": N("giant_hive/start"), "size": 1,
        "start_height": {"absolute": -1}, "project_start_to_heightmap": "WORLD_SURFACE_WG",
        "max_distance_from_center": 80, "use_expansion_hack": False})
    write_json(os.path.join(wg, "structure_set", "giant_hives.json"), {
        "structures": [{"structure": N("giant_hive"), "weight": 1}],
        "placement": {"type": "minecraft:random_spread", "spacing": 44, "separation": 18, "salt": 581233907,
                      "exclusion_zone": {"other_set": "minecraft:villages", "chunk_count": 6}}})


# =====================================================================================================================
# Lang
# =====================================================================================================================
NAMES = {
    "wild_comb": ("Wild Comb", "Дикие соты"),
    "dripping_comb": ("Dripping Comb", "Сочащиеся соты"),
    "honeycomb_bricks": ("Honeycomb Bricks", "Сотовые кирпичи"),
    "honeycomb_brick_stairs": ("Honeycomb Brick Stairs", "Ступени из сотовых кирпичей"),
    "honeycomb_brick_slab": ("Honeycomb Brick Slab", "Плита из сотовых кирпичей"),
    "honeycomb_brick_wall": ("Honeycomb Brick Wall", "Ограда из сотовых кирпичей"),
    "comb_window": ("Waxed Comb Window", "Вощёное сотовое окно"),
    "royal_jelly": ("Royal Jelly Block", "Блок маточного молочка"),
    "hive_heart": ("Hive Heart", "Сердце улья"),
    "honey_cake": ("Honey Cake", "Медовик"),
    "honey": ("Honey", "Мёд"),
}
for k, (en, ru) in NAMES.items():
    EN[f"block.{MOD}.{k}"], RU[f"block.{MOD}.{k}"] = en, ru
EN.update({f"item.{MOD}.honey_bucket": "Honey Bucket", f"item.{MOD}.honey_cookie": "Honey Cookie",
           f"fluid_type.{MOD}.honey": "Honey", f"structure.{MOD}.giant_hive": "Giant Beehive",
           f"block.{MOD}.hive_heart.desc": "The hive defends its heart"})
RU.update({f"item.{MOD}.honey_bucket": "Ведро мёда", f"item.{MOD}.honey_cookie": "Медовое печенье",
           f"fluid_type.{MOD}.honey": "Мёд", f"structure.{MOD}.giant_hive": "Огромный улей",
           f"block.{MOD}.hive_heart.desc": "Улей защищает своё сердце"})


def generate():
    write_assets()
    write_data()
    write_templates()
    write_worldgen()
    print("giant_hive: " + ", ".join(f"{p}: {i['size']} {i['blocks']} blocks, honey {i['honey']}, nests {i['nests']} "
                                     f"({i['bees_in_nests']} bees), {i['bees']} bees out, {i['chests']} chests"
                                     for p, i in INFO.items()))
