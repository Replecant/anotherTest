"""Freedom Station ("Свобода") - the orbital station the "Liberty I" rocket docks at.

Builds the station procedurally and writes it as a vanilla structure template
(data/retrocosmos/structure/freedom_station.nbt) plus an anchors file
(data/retrocosmos/station/freedom_station.json) with the docking pad, a safe arrival spot and the
pressurized interior boxes.

Layout (structure-local X east, Z south, Y up; the hub centre is the origin before normalisation):

    * Central hub: 21-block cylinder with a glass-ribbed dome (lounge, galley bar, reading nook).
    * North: observation deck - round, glass-walled, low dome, telescope.
    * East: crew quarters - four cabins off a central hallway.
    * West: laboratory / machine room - fuel refinery, air liquefier, cryo tanks, workbench.
    * South: docking module - airlock passage, supply room and stairwell on the ground floor,
      the bridge (mission control console) upstairs overlooking the open docking bay with the
      3x3 launch pad and the service tower.
    * Solar wings on the crew and lab modules, antennas, a Googie starburst sign on the bridge roof.

Only a small self-contained NBT writer/reader is used (no external libraries).
"""
import gzip
import io
import json
import math
import os
import struct

from gen_resources import DATA, ROOT, write_json

STRUCTURE_FILE = os.path.join(DATA, "structure", "freedom_station.nbt")
ANCHORS_FILE = os.path.join(DATA, "station", "freedom_station.json")
DATA_VERSION = 4671

# ----------------------------------------------------------------------------
# Minimal NBT
# ----------------------------------------------------------------------------
TAG_END, TAG_BYTE, TAG_SHORT, TAG_INT, TAG_LONG, TAG_FLOAT, TAG_DOUBLE = 0, 1, 2, 3, 4, 5, 6
TAG_BYTE_ARRAY, TAG_STRING, TAG_LIST, TAG_COMPOUND, TAG_INT_ARRAY, TAG_LONG_ARRAY = 7, 8, 9, 10, 11, 12


class Byte(int):
    tag = TAG_BYTE


class Short(int):
    tag = TAG_SHORT


class Int(int):
    tag = TAG_INT


class Long(int):
    tag = TAG_LONG


class Str(str):
    tag = TAG_STRING


class List(list):
    """Homogeneous NBT list; `elem` is the element tag type (needed for empty lists)."""
    tag = TAG_LIST

    def __init__(self, items=(), elem=None):
        super().__init__(items)
        self.elem = elem if elem is not None else (_tag_of(self[0]) if len(self) else TAG_END)


class Compound(dict):
    tag = TAG_COMPOUND


def _tag_of(v):
    if isinstance(v, bool):
        return TAG_BYTE
    if hasattr(v, "tag"):
        return v.tag
    if isinstance(v, int):
        return TAG_INT
    if isinstance(v, str):
        return TAG_STRING
    if isinstance(v, dict):
        return TAG_COMPOUND
    if isinstance(v, list):
        return TAG_LIST
    raise TypeError(f"unsupported NBT value {v!r}")


def _write_payload(out, tag, v):
    if tag == TAG_BYTE:
        out.write(struct.pack(">b", int(v)))
    elif tag == TAG_SHORT:
        out.write(struct.pack(">h", int(v)))
    elif tag == TAG_INT:
        out.write(struct.pack(">i", int(v)))
    elif tag == TAG_LONG:
        out.write(struct.pack(">q", int(v)))
    elif tag == TAG_FLOAT:
        out.write(struct.pack(">f", float(v)))
    elif tag == TAG_DOUBLE:
        out.write(struct.pack(">d", float(v)))
    elif tag == TAG_STRING:
        data = str(v).encode("utf-8")
        out.write(struct.pack(">H", len(data)))
        out.write(data)
    elif tag == TAG_LIST:
        elem = v.elem if isinstance(v, List) else (_tag_of(v[0]) if len(v) else TAG_END)
        out.write(struct.pack(">bi", elem, len(v)))
        for item in v:
            _write_payload(out, elem, item)
    elif tag == TAG_COMPOUND:
        for key, item in v.items():
            t = _tag_of(item)
            out.write(struct.pack(">b", t))
            _write_payload(out, TAG_STRING, key)
            _write_payload(out, t, item)
        out.write(b"\x00")
    else:
        raise TypeError(f"unsupported tag {tag}")


def nbt_bytes(root, name=""):
    out = io.BytesIO()
    out.write(struct.pack(">b", TAG_COMPOUND))
    _write_payload(out, TAG_STRING, name)
    _write_payload(out, TAG_COMPOUND, root)
    return out.getvalue()


def _read_payload(inp, tag):
    if tag == TAG_BYTE:
        return Byte(struct.unpack(">b", inp.read(1))[0])
    if tag == TAG_SHORT:
        return Short(struct.unpack(">h", inp.read(2))[0])
    if tag == TAG_INT:
        return Int(struct.unpack(">i", inp.read(4))[0])
    if tag == TAG_LONG:
        return Long(struct.unpack(">q", inp.read(8))[0])
    if tag == TAG_FLOAT:
        return struct.unpack(">f", inp.read(4))[0]
    if tag == TAG_DOUBLE:
        return struct.unpack(">d", inp.read(8))[0]
    if tag == TAG_STRING:
        n = struct.unpack(">H", inp.read(2))[0]
        return Str(inp.read(n).decode("utf-8"))
    if tag == TAG_LIST:
        elem, n = struct.unpack(">bi", inp.read(5))
        return List([_read_payload(inp, elem) for _ in range(n)], elem)
    if tag == TAG_COMPOUND:
        out = Compound()
        while True:
            t = struct.unpack(">b", inp.read(1))[0]
            if t == TAG_END:
                return out
            key = _read_payload(inp, TAG_STRING)
            out[key] = _read_payload(inp, t)
    if tag == TAG_BYTE_ARRAY:
        n = struct.unpack(">i", inp.read(4))[0]
        return list(struct.unpack(f">{n}b", inp.read(n)))
    if tag == TAG_INT_ARRAY:
        n = struct.unpack(">i", inp.read(4))[0]
        return list(struct.unpack(f">{n}i", inp.read(4 * n)))
    if tag == TAG_LONG_ARRAY:
        n = struct.unpack(">i", inp.read(4))[0]
        return list(struct.unpack(f">{n}q", inp.read(8 * n)))
    raise TypeError(f"unsupported tag {tag}")


def nbt_parse(data):
    inp = io.BytesIO(data)
    tag = struct.unpack(">b", inp.read(1))[0]
    assert tag == TAG_COMPOUND
    name = _read_payload(inp, TAG_STRING)
    return name, _read_payload(inp, TAG_COMPOUND)


# ----------------------------------------------------------------------------
# Block ids
# ----------------------------------------------------------------------------
def rc(name):
    return "retrocosmos:" + name


AIR = "minecraft:air"
WHITE = "minecraft:white_concrete"
LGRAY = "minecraft:light_gray_concrete"
RED = "minecraft:red_concrete"
QUARTZ = "minecraft:quartz_block"
SMOOTH_QUARTZ = "minecraft:smooth_quartz"
QUARTZ_STAIRS = "minecraft:quartz_stairs"
QUARTZ_SLAB = "minecraft:quartz_slab"
GLASS = "minecraft:glass"
BLUE_GLASS = "minecraft:blue_stained_glass"
LBLUE_GLASS = "minecraft:light_blue_stained_glass"
SEA_LANTERN = "minecraft:sea_lantern"
GOLD = "minecraft:gold_block"
IRON_BARS = "minecraft:iron_bars"
END_ROD = "minecraft:end_rod"
LIGHTNING_ROD = "minecraft:lightning_rod"
DAYLIGHT = "minecraft:daylight_detector"
CHEST = "minecraft:chest"
BARREL = "minecraft:barrel"
IRON_DOOR = "minecraft:iron_door"
BUTTON = "minecraft:stone_button"
HOPPER = "minecraft:hopper"
BOOKSHELF = "minecraft:bookshelf"
WHITE_CARPET = "minecraft:white_carpet"
RED_CARPET = "minecraft:red_carpet"
CYAN_CARPET = "minecraft:cyan_carpet"

ALU = rc("aluminum_block")
TI = rc("titanium_block")
LAUNCH_PAD = rc("launch_pad")
TOWER = rc("service_tower")
REFINERY = rc("fuel_refinery")
LIQUEFIER = rc("air_liquefier")
CONSOLE = rc("mission_control_console")
PORTHOLE = rc("porthole_window")
CHECKER = rc("checkered_tile")
TURQ = rc("turquoise_panel")
CREAM = rc("cream_panel")
CHROME = rc("chrome_trim")
FLOOR_LAMP = rc("atomic_floor_lamp")
TABLE_LAMP = rc("rocket_table_lamp")
CHANDELIER = rc("sputnik_chandelier")
STOOL = rc("diner_stool")
EGG_CHAIR = rc("egg_chair")
SOFA = rc("googie_sofa")
TABLE = rc("boomerang_table")
TV = rc("atomic_tv")
RADIO = rc("tube_radio")
CLOCK = rc("starburst_clock")
NEON = rc("neon_rocket_sign")

# Full cubes that iron bars connect to.
FULL_CUBES = {WHITE, LGRAY, RED, QUARTZ, SMOOTH_QUARTZ, GLASS, BLUE_GLASS, LBLUE_GLASS, SEA_LANTERN, GOLD, ALU, TI,
              PORTHOLE, CHECKER, TURQ, CREAM, CHROME, BOOKSHELF, TOWER, "minecraft:black_concrete"}

DIRS = {"north": (0, -1), "south": (0, 1), "west": (-1, 0), "east": (1, 0)}


# ----------------------------------------------------------------------------
# Builder
# ----------------------------------------------------------------------------
class Station:
    def __init__(self):
        self.blocks = {}     # (x, y, z) -> (name, props dict, nbt Compound|None)
        self.inner = set()   # pressurised interior cells (air or furniture), structure void elsewhere

    # -- primitives -------------------------------------------------------
    def put(self, x, y, z, name, props=None, nbt=None):
        """Places a structural block; a cell placed this way is never part of the pressurised volume."""
        self.blocks[(x, y, z)] = (name, dict(props or {}), nbt)
        self.inner.discard((x, y, z))

    def get(self, x, y, z):
        b = self.blocks.get((x, y, z))
        return b[0] if b else None

    def interior(self, x, y, z, name=AIR, props=None, nbt=None):
        """Marks a cell as pressurised interior (and places air or a piece of furniture there)."""
        self.put(x, y, z, name, props, nbt)
        self.inner.add((x, y, z))

    def fill(self, x0, y0, z0, x1, y1, z1, name, props=None):
        for x in range(min(x0, x1), max(x0, x1) + 1):
            for y in range(min(y0, y1), max(y0, y1) + 1):
                for z in range(min(z0, z1), max(z0, z1) + 1):
                    self.put(x, y, z, name, props)

    def fill_interior(self, x0, y0, z0, x1, y1, z1):
        for x in range(min(x0, x1), max(x0, x1) + 1):
            for y in range(min(y0, y1), max(y0, y1) + 1):
                for z in range(min(z0, z1), max(z0, z1) + 1):
                    self.interior(x, y, z)

    def facing(self, x, y, z, name, facing, lit=None, extra=None):
        props = {"facing": facing}
        if lit is not None:
            props["lit"] = "true" if lit else "false"
        if extra:
            props.update(extra)
        self.interior(x, y, z, name, props)

    def lamp(self, x, y, z):
        self.interior(x, y, z, FLOOR_LAMP, {"lit": "true"})

    def chandelier(self, x, y, z):
        self.interior(x, y, z, CHANDELIER, {"lit": "true"})

    def bed(self, x, y, z, facing, color="red"):
        dx, dz = DIRS[facing]
        self.interior(x, y, z, f"minecraft:{color}_bed", {"facing": facing, "part": "foot", "occupied": "false"})
        self.interior(x + dx, y, z + dz, f"minecraft:{color}_bed", {"facing": facing, "part": "head", "occupied": "false"})

    def chest(self, x, y, z, facing, items):
        stacks = List([Compound({"Slot": Byte(i), "id": Str(item), "count": Int(n)}) for i, (item, n) in enumerate(items)],
                      TAG_COMPOUND)
        nbt = Compound({"id": Str(CHEST), "Items": stacks})
        self.interior(x, y, z, CHEST, {"facing": facing, "type": "single", "waterlogged": "false"}, nbt)

    def iron_door(self, x, y, z, facing):
        base = {"facing": facing, "hinge": "left", "open": "false", "powered": "false"}
        self.interior(x, y, z, IRON_DOOR, dict(base, half="lower"))
        self.interior(x, y + 1, z, IRON_DOOR, dict(base, half="upper"))

    def button(self, x, y, z, facing):
        self.put(x, y, z, BUTTON, {"face": "wall", "facing": facing, "powered": "false"})

    def stairs(self, x, y, z, facing):
        self.interior(x, y, z, QUARTZ_STAIRS, {"facing": facing, "half": "bottom", "shape": "straight", "waterlogged": "false"})

    # -- geometry helpers ------------------------------------------------
    @staticmethod
    def dist(x, z, cx=0, cz=0):
        return math.hypot(x - cx, z - cz)

    # ---------------------------------------------------------------------
    # Hub
    # ---------------------------------------------------------------------
    HUB_R = 10.5         # outer radius of the cylinder (cells with d <= HUB_R)
    HUB_DOME_B = 8.5     # vertical semi-axis of the dome
    HUB_WALL_TOP = 10    # last y of the vertical wall; dome starts above

    def hub_inside(self, x, y, z):
        d = self.dist(x, z)
        if y <= self.HUB_WALL_TOP:
            return d <= self.HUB_R
        return (d / self.HUB_R) ** 2 + ((y - self.HUB_WALL_TOP) / self.HUB_DOME_B) ** 2 <= 1.0

    def hub(self):
        R = self.HUB_R
        porthole_angles = [math.radians(a) for a in range(30, 360, 30) if a % 90 != 0]

        def ring_cells(r_lo, r_hi):
            return [(x, z) for x in range(-12, 13) for z in range(-12, 13) if r_lo < self.dist(x, z) <= r_hi]

        hull_ring = ring_cells(R - 1, R)
        liner_ring = ring_cells(R - 2, R - 1)
        inner_cells = [(x, z) for x in range(-12, 13) for z in range(-12, 13) if self.dist(x, z) <= R - 2]

        def pick(ring, ang):
            return min(ring, key=lambda c: abs(math.remainder(math.atan2(c[1], c[0]) - ang, 2 * math.pi)))

        portholes = set()
        for a in porthole_angles:
            portholes.add(pick(hull_ring, a))
            portholes.add(pick(liner_ring, a))

        # bottom plate and keel
        for (x, z) in hull_ring + liner_ring + inner_cells:
            self.put(x, 2, z, LGRAY)
        for (x, z) in inner_cells:
            if self.dist(x, z) <= 5.5:
                self.put(x, 1, z, TI)
        for sx in (-3, 3):
            for sz in (-3, 3):
                self.put(sx, 0, sz, HOPPER, {"facing": "down", "enabled": "true"})
        self.put(0, 0, 0, END_ROD, {"facing": "down"})

        # vertical wall: hull ring and liner ring
        for (x, z) in hull_ring:
            self.put(x, 3, z, ALU)
            self.put(x, 4, z, LGRAY)
            for y in (5, 6, 7, 8):
                self.put(x, y, z, PORTHOLE if (y == 6 and (x, z) in portholes) else WHITE)
            self.put(x, 9, z, RED)
            self.put(x, 10, z, TI)
        for (x, z) in liner_ring:
            self.put(x, 3, z, CHECKER)
            self.put(x, 4, z, TURQ)
            for y in (5, 6, 7, 8):
                self.put(x, y, z, PORTHOLE if (y == 6 and (x, z) in portholes) else CREAM)
            self.put(x, 9, z, TURQ)
            # glowing cornice
            self.put(x, 10, z, SEA_LANTERN if (round(math.degrees(math.atan2(z, x))) % 30) < 10 else CREAM)

        # floor with a starburst motif
        for (x, z) in inner_cells:
            d = self.dist(x, z)
            name = CHECKER
            if d <= 2.5:
                name = CREAM
            if (x == 0 or z == 0) and 3 <= max(abs(x), abs(z)) <= 7:
                name = TURQ
            if abs(x) == abs(z) and 2 <= abs(x) <= 5:
                name = TURQ
            if (x, z) in ((0, 0), (7, 0), (-7, 0), (0, 7), (0, -7), (5, 5), (-5, 5), (5, -5), (-5, -5)):
                name = SEA_LANTERN
            self.put(x, 3, z, name)
            for y in range(4, self.HUB_WALL_TOP + 1):
                self.interior(x, y, z)

        # dome: watertight 1-thick shell with glass meridians and light dots
        for y in range(self.HUB_WALL_TOP + 1, self.HUB_WALL_TOP + 12):
            for x in range(-12, 13):
                for z in range(-12, 13):
                    if not self.hub_inside(x, y, z):
                        continue
                    shell = not all(self.hub_inside(x + dx, y + dy, z + dz)
                                    for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)))
                    if not shell:
                        self.interior(x, y, z)
                        continue
                    name = WHITE
                    if x == 0 or z == 0 or abs(x) == abs(z):
                        name = GLASS
                    ang = math.degrees(math.atan2(z, x)) % 360
                    if y in (12, 15) and abs((ang - 22.5) % 45) < 4 and self.dist(x, z) > 2:
                        name = SEA_LANTERN
                    if x == 0 and z == 0:
                        name = GOLD
                    self.put(x, y, z, name)
        # apex mast
        top = max(y for (x, y, z) in self.blocks if x == 0 and z == 0)
        for y in range(top + 1, top + 5):
            self.put(0, y, 0, CHROME, {"axis": "y"})
        self.put(0, top + 5, 0, LIGHTNING_ROD, {"facing": "up", "powered": "false", "waterlogged": "false"})
        for (x, z), f in (((1, 0), "east"), ((-1, 0), "west"), ((0, 1), "south"), ((0, -1), "north")):
            self.put(x, top + 3, z, END_ROD, {"facing": f})
        # central chain + chandelier under the apex
        for y in range(top - 1, top - 5, -1):
            self.interior(0, y, 0, CHROME, {"axis": "y"})
        self.chandelier(0, top - 5, 0)

        # pillars
        for px_ in (-5, 5):
            for pz in (-5, 5):
                for y in range(4, self.HUB_WALL_TOP + 1):
                    self.interior(px_, y, pz, CHROME, {"axis": "y"})

        # conversation pit in the centre
        self.facing(0, 4, 0, TABLE, "north")
        self.interior(0, 5, 0, TABLE_LAMP, {"facing": "north", "lit": "true"})
        self.facing(-2, 4, 0, SOFA, "east")
        self.facing(2, 4, 0, SOFA, "west")
        self.facing(2, 4, 2, EGG_CHAIR, "west")
        self.facing(-2, 4, -2, EGG_CHAIR, "east")
        self.facing(2, 4, -2, EGG_CHAIR, "south")
        self.facing(-2, 4, 2, EGG_CHAIR, "north")

        # NE: TV lounge
        self.facing(4, 4, -7, TV, "south", lit=True)
        self.facing(4, 4, -5, SOFA, "north")
        self.facing(3, 4, -5, SOFA, "north")
        self.facing(5, 4, -5, SOFA, "north")
        self.lamp(7, 4, -4)
        self.facing(6, 4, -6, TABLE, "north")
        self.interior(6, 5, -6, "minecraft:potted_fern")

        # NW: galley bar
        for x in range(-6, -2):
            self.interior(x, 4, -5, SMOOTH_QUARTZ)
            self.interior(x, 4, -4, STOOL)
        self.interior(-3, 5, -5, RADIO, {"facing": "south", "lit": "true"})
        self.interior(-5, 5, -5, "minecraft:cake", {"bites": "0"})
        self.interior(-6, 4, -6, "minecraft:smoker", {"facing": "south", "lit": "false"})
        self.interior(-5, 4, -6, BARREL, {"facing": "up", "open": "false"})
        self.interior(-4, 4, -6, "minecraft:water_cauldron", {"level": "3"})
        self.interior(-3, 4, -6, BARREL, {"facing": "up", "open": "false"})
        self.lamp(-7, 4, -3)

        # SE: reading nook
        for (x, z) in ((4, 7), (5, 6), (6, 5)):
            self.interior(x, 4, z, BOOKSHELF)
            self.interior(x, 5, z, BOOKSHELF)
        self.facing(4, 4, 5, EGG_CHAIR, "west")
        self.facing(6, 4, 3, EGG_CHAIR, "north")
        self.facing(5, 4, 4, TABLE, "north")
        self.interior(5, 5, 4, TABLE_LAMP, {"facing": "north", "lit": "true"})
        self.lamp(7, 4, 3)

        # SW: music corner
        self.interior(-6, 4, 5, "minecraft:jukebox", {"has_record": "false"})
        self.facing(-4, 4, 6, SOFA, "north")
        self.facing(-3, 4, 6, SOFA, "north")
        self.facing(-6, 4, 3, SOFA, "east")
        self.facing(-4, 4, 4, TABLE, "north")
        self.interior(-4, 5, 4, "minecraft:potted_cactus")
        self.lamp(-7, 4, 4)
        self.lamp(-3, 4, 7)

        # wall decor above the four doorways (y 4..6 doorway, decor at y 7)
        self.facing(0, 7, -8, CLOCK, "south")
        self.interior(0, 7, 8, NEON, {"facing": "north", "lit": "true"})
        self.facing(8, 7, 0, CLOCK, "west")
        self.facing(-8, 7, 0, CLOCK, "east")

    def hub_openings(self):
        """Cuts the four doorways through the hub rings (corridor cross-section 3 wide, 3 tall)."""
        R = self.HUB_R
        for axis in ("x", "z"):
            for sign in (-1, 1):
                for t in range(8, 12):
                    for u in (-1, 0, 1):
                        x, z = (t * sign, u) if axis == "x" else (u, t * sign)
                        d = self.dist(x, z)
                        if not (R - 2 < d <= R):
                            continue
                        self.put(x, 3, z, CHECKER)
                        for y in (4, 5, 6):
                            self.interior(x, y, z)
                        self.put(x, 7, z, CREAM)

    # ---------------------------------------------------------------------
    # Corridors
    # ---------------------------------------------------------------------
    def corridor(self, axis, t0, t1, portholes=()):
        """Tube along `axis` (x or z) for t in t0..t1; cross-section u -3..3, y 2..8; interior 3x3."""
        for t in range(t0, t1 + 1):
            end = t in (t0, t1)
            rib = (t - t0) % 4 == 2 and not end
            for u in range(-3, 4):
                for y in range(2, 9):
                    x, z = (t, u) if axis == "x" else (u, t)
                    au = abs(u)
                    if au <= 1 and 4 <= y <= 6:
                        self.interior(x, y, z)
                    elif au <= 1 and y == 3:
                        self.put(x, y, z, CHECKER)
                    elif au <= 1 and y == 7:
                        self.put(x, y, z, SEA_LANTERN if (u == 0 and (t - t0) % 3 == 1) else WHITE)
                    elif au == 2 and 3 <= y <= 7:
                        if y == 3 or y == 7:
                            self.put(x, y, z, WHITE)
                        elif y == 4:
                            self.put(x, y, z, TURQ)
                        else:
                            self.put(x, y, z, PORTHOLE if (y == 5 and t in portholes) else CREAM)
                    else:
                        # hull layer, chamfered corners
                        if au == 3 and y in (2, 8):
                            continue
                        if end:
                            self.put(x, y, z, RED)
                        elif rib:
                            self.put(x, y, z, CHROME, {"axis": ("y" if au == 3 else ("z" if axis == "x" else "x"))})
                        elif au == 3 and y == 5 and t in portholes:
                            self.put(x, y, z, PORTHOLE)
                        elif y == 2:
                            self.put(x, y, z, LGRAY)
                        else:
                            self.put(x, y, z, WHITE)

    # ---------------------------------------------------------------------
    # Rectangular module shell (crew quarters, laboratory)
    # ---------------------------------------------------------------------
    def module_box(self, x0, x1, z0, z1, portholes, floor=CHECKER, door_side="west"):
        """Exterior bounds x0..x1, z0..z1 (inclusive); hull y 2..10, interior inset by 2, y 4..8."""
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                layer = min(x - x0, x1 - x, z - z0, z1 - z)  # 0 hull, 1 liner, >=2 interior
                corner = (x in (x0, x1)) and (z in (z0, z1))
                self.put(x, 2, z, LGRAY)
                if layer == 0:
                    self.put(x, 3, z, ALU)
                    self.put(x, 4, z, LGRAY)
                    for y in (5, 6, 7, 8):
                        self.put(x, y, z, PORTHOLE if (y == 6 and (x, z) in portholes) else WHITE)
                    self.put(x, 9, z, RED)
                    self.put(x, 10, z, TI)
                    if corner:
                        for y in range(3, 11):
                            self.put(x, y, z, CHROME, {"axis": "y"})
                elif layer == 1:
                    self.put(x, 3, z, floor)
                    self.put(x, 4, z, TURQ)
                    for y in (5, 6, 7, 8):
                        self.put(x, y, z, PORTHOLE if (y == 6 and (x, z) in portholes) else CREAM)
                    self.put(x, 9, z, WHITE)
                    self.put(x, 10, z, WHITE)
                else:
                    self.put(x, 3, z, floor)
                    for y in range(4, 9):
                        self.interior(x, y, z)
                    self.put(x, 9, z, WHITE)
                    self.put(x, 10, z, WHITE)
        # roof stripe along the module axis
        zc = (z0 + z1) // 2
        for x in range(x0 + 1, x1):
            self.put(x, 10, zc, RED)
        # doorway towards the hub (3 wide, 3 tall) through hull + liner
        dx = x0 if door_side == "west" else x1
        for x in (dx, dx + (1 if door_side == "west" else -1)):
            for z in (zc - 1, zc, zc + 1):
                self.put(x, 3, z, CHECKER)
                for y in (4, 5, 6):
                    self.interior(x, y, z)
                self.put(x, 7, z, CREAM)

    def ceiling_lights(self, cells, y=9):
        for (x, z) in cells:
            self.put(x, y, z, SEA_LANTERN)

    # ---------------------------------------------------------------------
    # Crew quarters (east)
    # ---------------------------------------------------------------------
    def crew_quarters(self):
        x0, x1, z0, z1 = 16, 28, -8, 8
        portholes = ({(x, z) for x in (19, 25) for z in (z0, z0 + 1, z1 - 1, z1)}
                     | {(x, z) for x in (x1 - 1, x1) for z in (-3, 0, 3)})
        self.module_box(x0, x1, z0, z1, portholes, floor=CHECKER, door_side="west")
        # partitions z=+-2 and x=22 within the cabin rows
        for x in range(18, 27):
            for z in (-2, 2):
                for y in range(4, 9):
                    self.put(x, y, z, CREAM if y != 4 else TURQ)
        for z in list(range(3, 7)) + list(range(-6, -2)):
            for y in range(4, 9):
                self.put(22, y, z, CREAM if y != 4 else TURQ)
        # cabin doorways
        for x in (19, 24):
            for z in (-2, 2):
                for y in (4, 5):
                    self.interior(x, y, z)
                self.put(x, 6, z, CHROME, {"axis": "x"})
        # cabins
        for (cx0, cx1) in ((18, 21), (23, 26)):
            for side in (1, -1):
                zout = 6 * side           # cell next to the outer liner
                zin = 3 * side            # cell next to the partition
                bed_x = cx1
                self.bed(bed_x, 4, zout - side, "south" if side > 0 else "north",
                         color="cyan" if cx0 == 18 else "red")
                # nightstand chest faces into the room: for the north cabin the room is to the south
                self.chest(bed_x - 1, 4, zout, "south" if side > 0 else "north",
                           [("minecraft:book", 1), ("minecraft:paper", 4)])
                self.interior(bed_x - 1, 5, zout, TABLE_LAMP, {"facing": "south" if side > 0 else "north", "lit": "true"})
                self.facing(cx0, 4, zout, TABLE, "east")
                self.interior(cx0, 4, zin, STOOL)
                self.facing(cx0, 6, zin + side, CLOCK, "east")
                carpet = CYAN_CARPET if cx0 == 18 else RED_CARPET
                self.interior(cx0 + 1, 4, zin, carpet)
                self.interior(cx0 + 1, 4, zin + side, carpet)
                self.interior(cx0 + 2, 4, zin, WHITE_CARPET)
                self.put(cx0 + 1, 9, zin + side, SEA_LANTERN)
        # hallway
        self.ceiling_lights([(19, 0), (22, 0), (25, 0)])
        self.facing(26, 4, 0, EGG_CHAIR, "west")
        self.lamp(26, 4, 1)
        self.lamp(26, 4, -1)
        self.interior(24, 6, -1, NEON, {"facing": "south", "lit": "true"})  # on the partition at z=-2
        self.facing(20, 6, 1, CLOCK, "north")  # on the partition at z=2
        for x in range(18, 26):
            self.interior(x, 4, 0, RED_CARPET)

    # ---------------------------------------------------------------------
    # Laboratory / machine room (west)
    # ---------------------------------------------------------------------
    def laboratory(self):
        x0, x1, z0, z1 = -28, -16, -8, 8
        portholes = ({(x, z) for x in (-25, -19) for z in (z0, z0 + 1, z1 - 1, z1)}
                     | {(x, z) for x in (x0, x0 + 1) for z in (-3, 0, 3)})
        self.module_box(x0, x1, z0, z1, portholes, floor=LGRAY, door_side="east")
        # machines along the north wall with exhaust pipes
        self.facing(-24, 4, 6, REFINERY, "south", lit=False)
        self.facing(-20, 4, 6, LIQUEFIER, "south", lit=False)
        for x in (-24, -20):
            for y in (5, 6, 7, 8):
                self.interior(x, y, 6, CHROME, {"axis": "y"})
        self.chest(-22, 4, 6, "south", [(rc("empty_fuel_canister"), 6), (rc("titanium_plate"), 8),
                                        ("minecraft:bucket", 2), ("minecraft:coal", 16)])
        self.interior(-23, 4, 6, HOPPER, {"facing": "down", "enabled": "true"})
        self.interior(-21, 4, 6, HOPPER, {"facing": "down", "enabled": "true"})
        # cryogenic tanks along the west wall
        for z in (-5, -2, 2, 5):
            self.interior(-26, 4, z, CHROME, {"axis": "y"})
            for y in (5, 6, 7):
                self.interior(-26, y, z, LBLUE_GLASS)
            self.interior(-26, 8, z, CHROME, {"axis": "y"})
        self.facing(-26, 6, 0, CLOCK, "east")
        # central workbench
        for x in (-23, -22, -21):
            self.interior(x, 4, 0, QUARTZ)
        self.interior(-23, 5, 0, "minecraft:lever", {"face": "floor", "facing": "north", "powered": "false"})
        self.interior(-22, 5, 0, "minecraft:brewing_stand", {"has_bottle_0": "false", "has_bottle_1": "false",
                                                             "has_bottle_2": "false"})
        self.interior(-21, 5, 0, "minecraft:potted_fern")
        self.interior(-24, 4, 0, STOOL)
        self.interior(-20, 4, 0, STOOL)
        self.chandelier(-22, 8, 0)
        self.put(-22, 9, 0, WHITE)
        # south wall: library and workshop
        for x in (-25, -24):
            self.interior(x, 4, -6, BOOKSHELF)
            self.interior(x, 5, -6, BOOKSHELF)
        self.interior(-23, 4, -6, "minecraft:lectern", {"facing": "north", "has_book": "false", "powered": "false"})
        self.interior(-22, 4, -6, "minecraft:crafting_table")
        self.interior(-21, 4, -6, "minecraft:anvil", {"facing": "east"})
        self.interior(-20, 4, -6, "minecraft:blast_furnace", {"facing": "north", "lit": "false"})
        self.interior(-19, 4, -6, "minecraft:cauldron")
        self.interior(-18, 4, -6, BARREL, {"facing": "up", "open": "false"})
        self.interior(-18, 5, -6, RADIO, {"facing": "north", "lit": "true"})
        self.lamp(-18, 4, 5)
        self.interior(-18, 6, 4, NEON, {"facing": "west", "lit": "true"})  # hangs on the east liner (x=-17)
        self.ceiling_lights([(-25, -4), (-25, 4), (-19, -4), (-19, 4), (-22, -4), (-22, 4)])

    # ---------------------------------------------------------------------
    # Observation deck (north)
    # ---------------------------------------------------------------------
    OBS_C = (0, -21)
    OBS_R = 7.5

    def obs_inside(self, x, y, z):
        d = self.dist(x, z, *self.OBS_C)
        if y <= 8:
            return d <= self.OBS_R
        return (d / self.OBS_R) ** 2 + ((y - 8.5) / 4.5) ** 2 <= 1.0

    def observation_deck(self):
        cx, cz = self.OBS_C
        R = self.OBS_R
        mullions = set()
        ring = [(x, z) for x in range(cx - 8, cx + 9) for z in range(cz - 8, cz + 9) if R - 1 < self.dist(x, z, cx, cz) <= R]
        for a in range(0, 360, 45):
            ang = math.radians(a + 22.5)
            mullions.add(min(ring, key=lambda c: abs(math.remainder(math.atan2(c[1] - cz, c[0] - cx) - ang, 2 * math.pi))))
        for x in range(cx - 8, cx + 9):
            for z in range(cz - 8, cz + 9):
                d = self.dist(x, z, cx, cz)
                if d > R:
                    continue
                self.put(x, 2, z, LGRAY)
                if d > R - 1:
                    self.put(x, 3, z, ALU)
                    self.put(x, 4, z, WHITE)
                    for y in (5, 6, 7, 8):
                        self.put(x, y, z, CHROME if (x, z) in mullions else GLASS, {"axis": "y"} if (x, z) in mullions else None)
                else:
                    self.put(x, 3, z, CHECKER if (x + z) % 2 == 0 or d > 4.5 else "minecraft:black_concrete")
                    for y in range(4, 9):
                        self.interior(x, y, z)
        # floor compass star
        for (x, z) in ((cx, cz), (cx + 3, cz), (cx - 3, cz), (cx, cz + 3), (cx, cz - 3)):
            self.put(x, 3, z, SEA_LANTERN if (x, z) == (cx, cz) else CREAM)
        # low dome
        for y in range(9, 14):
            for x in range(cx - 8, cx + 9):
                for z in range(cz - 8, cz + 9):
                    if not self.obs_inside(x, y, z):
                        continue
                    shell = not all(self.obs_inside(x + dx, y + dy, z + dz)
                                    for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)))
                    if not shell:
                        self.interior(x, y, z)
                        continue
                    name = WHITE
                    ang = math.degrees(math.atan2(z - cz, x - cx)) % 360
                    if y == 9:
                        name = RED if self.dist(x, z, cx, cz) > R - 1 else WHITE
                    elif x == cx or z == cz:
                        name = GLASS
                    elif y in (10, 11) and abs((ang - 22.5) % 45) < 7:
                        name = SEA_LANTERN
                    self.put(x, y, z, name)
        top = max(y for (x, y, z) in self.blocks if (x, z) == (cx, cz))
        self.put(cx, top, cz, TI)
        self.put(cx, top + 1, cz, LIGHTNING_ROD, {"facing": "up", "powered": "false", "waterlogged": "false"})
        self.chandelier(cx, top - 1, cz)
        # doorway from the corridor (south side of the ring)
        for x in (-1, 0, 1):
            for z in range(cz + 5, cz + 9):
                if R - 1 < self.dist(x, z, cx, cz) <= R:
                    self.put(x, 3, z, CHECKER)
                    for y in (4, 5, 6):
                        self.interior(x, y, z)
                    self.put(x, 7, z, CREAM)
                    self.put(x, 8, z, WHITE)
        # furniture: telescope, chairs facing the stars, tables with lamps
        self.interior(cx, 4, cz - 5, CHROME, {"axis": "y"})
        self.interior(cx, 5, cz - 5, END_ROD, {"facing": "north"})
        self.facing(cx + 2, 4, cz - 4, EGG_CHAIR, "north")
        self.facing(cx - 2, 4, cz - 4, EGG_CHAIR, "north")
        self.facing(cx + 5, 4, cz, EGG_CHAIR, "east")
        self.facing(cx - 5, 4, cz, EGG_CHAIR, "west")
        self.facing(cx + 4, 4, cz + 3, EGG_CHAIR, "east")
        self.facing(cx - 4, 4, cz + 3, EGG_CHAIR, "west")
        for sx in (-4, 4):
            self.facing(cx + sx, 4, cz - 2, TABLE, "north")
            self.interior(cx + sx, 5, cz - 2, TABLE_LAMP, {"facing": "north", "lit": "true"})
        self.facing(cx + 2, 4, cz + 2, TABLE, "north")
        self.interior(cx + 2, 5, cz + 2, RADIO, {"facing": "west", "lit": "true"})
        self.facing(cx - 2, 4, cz + 2, SOFA, "east")
        self.lamp(cx + 5, 4, cz - 2)
        self.lamp(cx - 5, 4, cz - 2)

    # ---------------------------------------------------------------------
    # Docking module: airlock, supply room, stairwell, bridge
    # ---------------------------------------------------------------------
    def docking_module(self):
        x0, x1, z0, z1 = -8, 8, 15, 25
        # shell
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                layer = min(x - x0, x1 - x, z - z0, z1 - z)
                corner = (x in (x0, x1)) and (z in (z0, z1))
                self.put(x, 2, z, LGRAY)
                if layer == 0:
                    self.put(x, 3, z, ALU)
                    self.put(x, 4, z, LGRAY)
                    for y in range(5, 15):
                        self.put(x, y, z, WHITE)
                    self.put(x, 9, z, RED)
                    self.put(x, 15, z, TI)
                    if corner:
                        for y in range(3, 16):
                            self.put(x, y, z, CHROME, {"axis": "y"})
                elif layer == 1:
                    self.put(x, 3, z, CHECKER)
                    self.put(x, 4, z, TURQ)
                    for y in range(5, 15):
                        self.put(x, y, z, CREAM)
                    self.put(x, 8, z, WHITE)
                    self.put(x, 9, z, CHECKER)
                    self.put(x, 10, z, TURQ)
                    self.put(x, 14, z, WHITE)
                    self.put(x, 15, z, WHITE)
                else:
                    self.put(x, 3, z, CHECKER)
                    for y in range(4, 8):
                        self.interior(x, y, z)
                    self.put(x, 8, z, WHITE)
                    self.put(x, 9, z, CHECKER)
                    for y in range(10, 14):
                        self.interior(x, y, z)
                    self.put(x, 14, z, WHITE)
                    self.put(x, 15, z, WHITE)
        # ground floor side portholes (rooms look at the bay/space)
        for x in (-5, 5):
            for z in (24, 25):
                self.put(x, 6, z, PORTHOLE)
        for z in (18, 21):
            for x in (-7, -8, 7, 8):
                self.put(x, 6, z, PORTHOLE)
                self.put(x, 11, z, PORTHOLE)
        for x in (-4, 4):
            for z in (15, 16):
                self.put(x, 11, z, PORTHOLE)
        # bridge: bay window along the south (z=24 becomes interior, z=25 one-thick glass)
        for x in range(-6, 7):
            for y in range(10, 14):
                self.interior(x, y, 24)
            for y in (10, 11, 12):
                self.put(x, y, 25, PORTHOLE if abs(x) % 3 == 0 else GLASS)
            self.put(x, 13, 25, WHITE)
        for y in range(10, 14):
            self.put(-7, y, 24, CREAM)
            self.put(7, y, 24, CREAM)
        # north wall doorway + airlock door (corridor arrives at z=14)
        for x in (-1, 0, 1):
            self.put(x, 3, 15, CHECKER)
            for y in (4, 5, 6):
                self.put(x, y, 15, CREAM)
        self.put(-1, 5, 15, PORTHOLE)
        self.put(0, 6, 15, CHROME, {"axis": "x"})
        self.iron_door(0, 4, 15, "south")
        self.button(1, 5, 14, "north")
        self.button(1, 5, 16, "south")
        # airlock passage x -1..1, z 16..24; partitions at x=+-2
        for z in range(16, 24):
            for x in (-2, 2):
                for y in range(4, 8):
                    self.put(x, y, z, CREAM if y != 4 else TURQ)
        for z in (19, 20):
            for x in (-2, 2):
                for y in (4, 5):
                    self.interior(x, y, z)
                self.put(x, 6, z, CHROME, {"axis": "z"})
        for x in (-1, 0, 1):
            for y in range(4, 8):
                self.interior(x, y, 24)
        self.put(-1, 5, 25, PORTHOLE)
        self.put(0, 6, 25, CHROME, {"axis": "x"})
        self.put(1, 5, 25, WHITE)
        self.iron_door(0, 4, 25, "south")
        self.button(1, 5, 24, "north")
        self.button(1, 5, 26, "south")
        for z in (17, 20, 23):
            self.put(0, 8, z, SEA_LANTERN)
        self.interior(0, 7, 16, NEON, {"facing": "south", "lit": "true"})
        self.interior(0, 7, 24, CLOCK, {"facing": "north"})  # above the outer airlock door
        for z in range(16, 24):
            self.interior(0, 4, z, RED_CARPET)
        # supply room (west): chests with propellant for the trip home
        fuel = [(rc("rocket_fuel_canister"), 8), (rc("rocket_fuel_canister"), 8), (rc("rocket_fuel_canister"), 8)]
        lox = [(rc("liquid_oxygen_canister"), 8), (rc("liquid_oxygen_canister"), 8), (rc("liquid_oxygen_canister"), 8)]
        spares = [(rc("empty_fuel_canister"), 8), (rc("titanium_plate"), 12), ("minecraft:iron_ingot", 16),
                  ("minecraft:redstone", 16)]
        food = [("minecraft:bread", 16), ("minecraft:apple", 12), ("minecraft:golden_carrot", 8),
                ("minecraft:cookie", 16), ("minecraft:cake", 1)]
        self.chest(-6, 4, 17, "east", fuel)
        self.chest(-6, 4, 18, "east", lox)
        self.interior(-6, 4, 19, BARREL, {"facing": "up", "open": "false"})
        self.chest(-6, 4, 20, "east", spares)
        self.chest(-6, 4, 21, "east", food)
        self.chest(-6, 4, 22, "east", [(rc("rocket_fuel_canister"), 4), (rc("liquid_oxygen_canister"), 4),
                                       ("minecraft:torch", 16)])
        for x in (-5, -4, -3):
            self.interior(x, 4, 16, BARREL, {"facing": "up", "open": "false"})
        self.interior(-4, 4, 23, "minecraft:crafting_table")
        self.interior(-3, 4, 23, STOOL)
        self.interior(-3, 6, 18, CLOCK, {"facing": "west"})
        self.interior(-3, 6, 21, NEON, {"facing": "west", "lit": "true"})
        self.lamp(-6, 4, 23)
        for z in (18, 21):
            self.put(-4, 8, z, SEA_LANTERN)
        # stairwell room (east): quartz stairs x 4..5 climbing north from z=22 (y4) to z=17 (y9)
        for i, z in enumerate(range(22, 16, -1)):
            y = 4 + i
            for x in (4, 5):
                self.stairs(x, y, z, "north")
                for yy in range(4, y):
                    self.put(x, yy, z, CREAM)
                # head room above
                for yy in range(y + 1, y + 3):
                    self.interior(x, yy, z)
        for x in (4, 5):
            for z in range(17, 21):
                for y in (8, 9):
                    if self.get(x, y, z) in (WHITE, CHECKER):
                        self.interior(x, y, z)
        for z in range(17, 21):
            self.put(3, 10, z, IRON_BARS)
            self.put(6, 10, z, IRON_BARS)
        for x in (4, 5):
            self.put(x, 10, 21, IRON_BARS)
        self.chest(6, 4, 17, "west", [(rc("titanium_plate"), 6), ("minecraft:leather", 4), ("minecraft:string", 8)])
        self.interior(6, 4, 23, BARREL, {"facing": "up", "open": "false"})
        self.interior(3, 4, 23, BARREL, {"facing": "up", "open": "false"})
        self.lamp(6, 4, 22)
        self.interior(3, 6, 16, CLOCK, {"facing": "south"})
        self.put(4, 8, 22, SEA_LANTERN)
        # bridge furnishing
        self.facing(0, 10, 24, CONSOLE, "north")
        for x in (-2, 2):
            self.interior(x, 10, 24, "minecraft:lectern", {"facing": "north", "has_book": "false", "powered": "false"})
        for x in (-3, -1, 1, 3):
            self.interior(x, 10, 24, DAYLIGHT, {"inverted": "false", "power": "0"})
        for x in (-4, 4):
            self.interior(x, 10, 24, QUARTZ)
            self.interior(x, 11, 24, "minecraft:lever", {"face": "floor", "facing": "south", "powered": "false"})
        self.interior(-6, 10, 24, TV, {"facing": "north", "lit": "true"})
        self.interior(6, 10, 24, RADIO, {"facing": "north", "lit": "true"})
        for x in (-2, 0, 2):
            self.interior(x, 10, 23, STOOL)
        self.facing(0, 10, 20, EGG_CHAIR, "south")
        self.facing(-3, 10, 20, SOFA, "south")
        self.facing(-2, 10, 20, SOFA, "south")
        self.facing(-2, 10, 18, TABLE, "north")
        self.interior(-2, 11, 18, TABLE_LAMP, {"facing": "north", "lit": "true"})
        self.lamp(-6, 10, 16)
        self.lamp(-6, 10, 23)
        self.lamp(6, 10, 23)
        self.chandelier(0, 13, 20)
        self.interior(0, 12, 16, CLOCK, {"facing": "south"})
        self.interior(-4, 12, 16, NEON, {"facing": "south", "lit": "true"})
        for x in (-4, 4):
            for z in (18, 22):
                self.put(x, 14, z, SEA_LANTERN)
        self.put(0, 14, 23, SEA_LANTERN)
        # bridge floor: checkered already; starburst inlay under the chandelier
        for (x, z) in ((0, 20), (1, 20), (-1, 20), (0, 19), (0, 21)):
            if self.get(x, 9, z) == CHECKER:
                self.put(x, 9, z, TURQ)
        # roof: Googie starburst sign on a post + mast
        self.starburst_sign(0, 16, 24)
        for y in (16, 17, 18):
            self.put(-6, y, 17, CHROME, {"axis": "y"})
        self.put(-6, 19, 17, LIGHTNING_ROD, {"facing": "up", "powered": "false", "waterlogged": "false"})
        self.put(6, 16, 17, CHROME, {"axis": "y"})
        self.put(6, 17, 17, END_ROD, {"facing": "up"})

    def starburst_sign(self, x, y0, z):
        """Vertical starburst in the X-Y plane standing on a post; centre at (x, y0 + 3, z)."""
        cy = y0 + 3
        self.put(x, y0, z, CHROME, {"axis": "y"})
        self.put(x, y0 + 1, z, CHROME, {"axis": "y"})
        self.put(x, cy, z, SEA_LANTERN)
        for k in (1, 2):
            self.put(x + k, cy, z, GOLD)
            self.put(x - k, cy, z, GOLD)
            self.put(x, cy + k, z, GOLD)
            self.put(x + k, cy + k, z, GOLD)
            self.put(x - k, cy + k, z, GOLD)
            self.put(x + k, cy - k, z, GOLD)
            self.put(x - k, cy - k, z, GOLD)
        self.put(x, cy - 1, z, GOLD)
        self.put(x + 3, cy, z, END_ROD, {"facing": "east"})
        self.put(x - 3, cy, z, END_ROD, {"facing": "west"})
        self.put(x, cy + 3, z, END_ROD, {"facing": "up"})
        for sx in (-3, 3):
            self.put(x + sx, cy + 3, z, SEA_LANTERN)
            self.put(x + sx, cy - 3, z, SEA_LANTERN)

    # ---------------------------------------------------------------------
    # Open docking bay
    # ---------------------------------------------------------------------
    PAD = (0, 33)   # pad centre (x, z); pad blocks sit at y=3

    def docking_bay(self):
        cx, cz = self.PAD
        R = 7.5
        cells = [(x, z) for x in range(cx - 8, cx + 9) for z in range(cz - 8, cz + 9) if self.dist(x, z, cx, cz) <= R]
        cells += [(x, z) for x in range(-4, 5) for z in range(26, 29)]
        cells = sorted(set(cells))
        for (x, z) in cells:
            d = self.dist(x, z, cx, cz)
            ang = math.degrees(math.atan2(z - cz, x - cx)) % 360
            name = LGRAY
            if d > R - 1:
                name = RED if int(ang // 15) % 2 == 0 else WHITE
            elif 3.5 < d <= 4.5:
                name = WHITE
            if abs(x - cx) <= 1 and abs(z - cz) <= 1:
                name = LAUNCH_PAD
            if (x, z) in ((cx + 3, cz - 2), (cx - 3, cz - 2), (cx + 3, cz + 2), (cx - 3, cz + 2)):
                name = SEA_LANTERN
            self.put(x, 3, z, name)
            self.put(x, 2, z, LGRAY)
            if d > R - 1 and z > 28:
                self.put(x, 4, z, IRON_BARS)
        # service tower east of the pad (dx = +2), base on the pad level
        for y in range(3, 11):
            self.put(cx + 2, y, cz, TOWER)
        # floodlight posts
        for (x, z) in ((cx - 5, cz - 4), (cx + 5, cz - 4), (cx - 5, cz + 4), (cx + 5, cz + 4)):
            for y in (4, 5, 6):
                self.put(x, y, z, CHROME, {"axis": "y"})
            self.put(x, 7, z, SEA_LANTERN)
        # keel under the deck
        for (x, z) in ((cx - 4, cz), (cx + 4, cz), (cx, cz + 4), (cx, cz - 4)):
            self.put(x, 1, z, TI)
        for z in range(26, 30):
            self.put(0, 1, z, TI)

    # ---------------------------------------------------------------------
    # Exterior: solar wings, antennas
    # ---------------------------------------------------------------------
    def solar_wings(self):
        for mx in (22, -22):
            for side in (1, -1):
                for k in range(1, 13):
                    z = (8 + k) * side
                    for x in range(mx - 3, mx + 4):
                        if x == mx:
                            self.put(x, 6, z, CHROME, {"axis": "z"})
                        elif k in (4, 8, 12):
                            self.put(x, 6, z, CHROME, {"axis": "x"})
                        else:
                            self.put(x, 6, z, DAYLIGHT, {"inverted": "false", "power": "0"})
                self.put(mx, 6, (8 + 13) * side, TI)

    def antennas(self):
        # radar dish on the laboratory roof
        cx, cz = -22, 0
        for y in (11, 12):
            self.put(cx, y, cz, CHROME, {"axis": "y"})
        for x in range(cx - 2, cx + 3):
            for z in range(cz - 2, cz + 3):
                if 0 < self.dist(x, z, cx, cz) <= 2.5:
                    self.put(x, 13, z, QUARTZ_SLAB, {"type": "bottom", "waterlogged": "false"})
        self.put(cx, 13, cz, TI)
        self.put(cx, 14, cz, END_ROD, {"facing": "up"})
        # antenna farm on the crew roof
        for (x, z, h) in ((19, -4, 3), (25, 4, 2), (25, -4, 4)):
            for y in range(11, 11 + h):
                self.put(x, y, z, CHROME, {"axis": "y"})
            self.put(x, 11 + h, z, LIGHTNING_ROD, {"facing": "up", "powered": "false", "waterlogged": "false"})
        for x in (19, 25):
            self.put(x, 11, 0, END_ROD, {"facing": "up"})
        # red beacon lights on the module ends
        for (x, z) in ((-28, -8), (-28, 8), (28, -8), (28, 8)):
            self.put(x, 11, z, SEA_LANTERN)
            self.put(x, 12, z, "minecraft:red_stained_glass")

    # ---------------------------------------------------------------------
    # Post-processing
    # ---------------------------------------------------------------------
    def finish(self):
        # launch pad part/facing like LaunchPadBlock.shapeFor
        pads = [p for p, b in self.blocks.items() if b[0] == LAUNCH_PAD]
        for (x, y, z) in pads:
            n = self.get(x, y, z - 1) == LAUNCH_PAD
            s = self.get(x, y, z + 1) == LAUNCH_PAD
            e = self.get(x + 1, y, z) == LAUNCH_PAD
            w = self.get(x - 1, y, z) == LAUNCH_PAD
            missing = (not n) + (not s) + (not e) + (not w)
            if missing == 0:
                part, facing = "center", "north"
            elif missing == 1:
                part = "edge"
                facing = "north" if not n else "south" if not s else "east" if not e else "west"
            elif missing == 2 and n != s:
                part = "corner"
                facing = ("north" if not w else "east") if not n else ("south" if not e else "west")
            else:
                part, facing = "single", "north"
            self.blocks[(x, y, z)] = (LAUNCH_PAD, {"part": part, "facing": facing}, None)
        # iron bars connections
        for (x, y, z), (name, props, nbt) in list(self.blocks.items()):
            if name != IRON_BARS:
                continue
            p = {"waterlogged": "false"}
            for d, (dx, dz) in DIRS.items():
                nb = self.get(x + dx, y, z + dz)
                p[d] = "true" if (nb == IRON_BARS or nb in FULL_CUBES) else "false"
            self.blocks[(x, y, z)] = (name, p, nbt)
        # make sure every interior cell has a block entry (air unless furnished)
        for c in self.inner:
            if c not in self.blocks:
                self.blocks[c] = (AIR, {}, None)

    def build(self):
        self.corridor("x", 11, 15, portholes=(13,))
        self.corridor("x", -15, -11, portholes=(-13,))
        self.corridor("z", -13, -11)
        self.corridor("z", 11, 14, portholes=(12,))
        self.crew_quarters()
        self.laboratory()
        self.observation_deck()
        self.docking_module()
        self.docking_bay()
        self.solar_wings()
        self.antennas()
        self.hub()
        self.hub_openings()
        self.finish()
        return self

    # ---------------------------------------------------------------------
    # Export
    # ---------------------------------------------------------------------
    def bounds(self):
        xs = [p[0] for p in self.blocks]
        ys = [p[1] for p in self.blocks]
        zs = [p[2] for p in self.blocks]
        return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))

    def pressurized_boxes(self):
        """Greedy decomposition of the interior cell set into inclusive boxes (structure coords)."""
        (ox, oy, oz), _ = self.bounds()
        cells = {(x - ox, y - oy, z - oz) for (x, y, z) in self.inner}
        remaining = set(cells)
        boxes = []
        for start in sorted(cells, key=lambda c: (c[1], c[2], c[0])):
            if start not in remaining:
                continue
            x0, y0, z0 = start
            x1 = x0
            while (x1 + 1, y0, z0) in remaining:
                x1 += 1
            z1 = z0
            while all((x, y0, z1 + 1) in remaining for x in range(x0, x1 + 1)):
                z1 += 1
            y1 = y0
            while all((x, y1 + 1, z) in remaining for x in range(x0, x1 + 1) for z in range(z0, z1 + 1)):
                y1 += 1
            for x in range(x0, x1 + 1):
                for y in range(y0, y1 + 1):
                    for z in range(z0, z1 + 1):
                        remaining.discard((x, y, z))
            boxes.append([x0, y0, z0, x1, y1, z1])
        return boxes

    def to_nbt(self):
        (ox, oy, oz), (mx, my, mz) = self.bounds()
        palette_index = {}
        palette = List([], TAG_COMPOUND)
        blocks = List([], TAG_COMPOUND)
        for (x, y, z) in sorted(self.blocks, key=lambda c: (c[1], c[2], c[0])):
            name, props, nbt = self.blocks[(x, y, z)]
            key = (name, tuple(sorted(props.items())))
            if key not in palette_index:
                palette_index[key] = len(palette)
                entry = Compound({"Name": Str(name)})
                if props:
                    entry["Properties"] = Compound({Str(k): Str(v) for k, v in sorted(props.items())})
                palette.append(entry)
            entry = Compound({"pos": List([Int(x - ox), Int(y - oy), Int(z - oz)], TAG_INT),
                              "state": Int(palette_index[key])})
            if nbt is not None:
                entry["nbt"] = nbt
            blocks.append(entry)
        root = Compound({
            "DataVersion": Int(DATA_VERSION),
            "size": List([Int(mx - ox + 1), Int(my - oy + 1), Int(mz - oz + 1)], TAG_INT),
            "palette": palette,
            "blocks": blocks,
            "entities": List([], TAG_COMPOUND),
        })
        return root

    def anchors(self):
        (ox, oy, oz), (mx, my, mz) = self.bounds()
        px_, pz = self.PAD
        return {
            "size": [mx - ox + 1, my - oy + 1, mz - oz + 1],
            "pad_center": [px_ - ox, 3 - oy, pz - oz],
            "arrival": [0 - ox, 4 - oy, 20 - oz],
            "pressurized": self.pressurized_boxes(),
        }


# ----------------------------------------------------------------------------
# Validation against the mod's registered blockstates
# ----------------------------------------------------------------------------
def validate(station):
    states_dir = os.path.join(ROOT, "assets", "retrocosmos", "blockstates")
    problems = []
    for (name, props, _nbt) in station.blocks.values():
        if not name.startswith("retrocosmos:"):
            continue
        short = name.split(":", 1)[1]
        path = os.path.join(states_dir, short + ".json")
        if not os.path.exists(path):
            problems.append(f"unknown mod block {name}")
            continue
        with open(path, encoding="utf-8") as f:
            variants = json.load(f).get("variants")
        if variants is None:
            continue
        key = ",".join(f"{k}={v}" for k, v in sorted(props.items()))
        if key not in variants:
            problems.append(f"{name}[{key}] has no blockstate variant")
    problems = sorted(set(problems))
    if problems:
        raise SystemExit("station.py: invalid block states:\n  " + "\n  ".join(problems))


def generate():
    station = Station().build()
    validate(station)
    root = station.to_nbt()
    data = nbt_bytes(root)
    os.makedirs(os.path.dirname(STRUCTURE_FILE), exist_ok=True)
    with gzip.open(STRUCTURE_FILE, "wb") as f:
        f.write(data)
    # read back and verify
    with gzip.open(STRUCTURE_FILE, "rb") as f:
        name, back = nbt_parse(f.read())
    assert name == "" and back["DataVersion"] == DATA_VERSION
    assert list(back["size"]) == list(root["size"]) and len(back["blocks"]) == len(root["blocks"])
    assert len(back["palette"]) == len(root["palette"])
    anchors = station.anchors()
    write_json(ANCHORS_FILE, anchors)
    print(f"freedom_station: size {anchors['size']}, {len(root['blocks'])} blocks, {len(root['palette'])} states, "
          f"{len(anchors['pressurized'])} pressurized boxes")
    return station


if __name__ == "__main__":
    generate()
