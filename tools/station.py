"""Freedom Station ("Свобода") - a 1950s "von Braun wheel" orbital station (Collier's magazine style).

Writes a vanilla structure template (data/retrocosmos/structure/freedom_station.nbt) plus an anchors file
(data/retrocosmos/station/freedom_station.json) holding the docking pad, a safe arrival spot and the
pressurised interior boxes.  Only a small self-contained NBT writer/reader is used.

Geometry (structure-local X east, Z south, Y up; the wheel centre is the origin before normalisation):

    * Habitat ring: torus of major radius RING_R with a rounded cross-section, a 7-wide / 4-tall
      corridor inside.  Eight modules sit along it, separated by bulkheads with door frames:
      N Command Center, E Laboratory, S Hydroponics, W Crew Quarters (50 degrees each, centred on
      the spokes) and NE Galley, SE Medical Bay, SW Reactor Room, NW Radar & Observation (40 degrees).
    * Four tube spokes (N/E/S/W) join the ring to the central hub.
    * Hub: two-level cylinder - lower level = supply room (RP-1/LOX chests) where the spokes arrive,
      upper level = docking lobby.  The roof is the docking deck: 3x3 launch pad, service tower,
      an airlock hut with a ladder shaft down into the lobby.  Nothing is built above the pad.
    * Solar mirror band on top of the ring, radar dish, antenna mast, dish under the hub,
      red/white striped markings, porthole bands.
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
LGRAY = "minecraft:light_gray_concrete"
RED = "minecraft:red_concrete"
QUARTZ = "minecraft:quartz_block"
QUARTZ_STAIRS = "minecraft:quartz_stairs"
QUARTZ_SLAB = "minecraft:quartz_slab"
LBLUE_GLASS = "minecraft:light_blue_stained_glass"
SEA_LANTERN = "minecraft:sea_lantern"
END_ROD = "minecraft:end_rod"
LIGHTNING_ROD = "minecraft:lightning_rod"
DAYLIGHT = "minecraft:daylight_detector"
CHEST = "minecraft:chest"
BARREL = "minecraft:barrel"
IRON_DOOR = "minecraft:iron_door"
BUTTON = "minecraft:stone_button"
LADDER = "minecraft:ladder"
BOOKSHELF = "minecraft:bookshelf"
WHITE_CARPET = "minecraft:white_carpet"
RED_CARPET = "minecraft:red_carpet"

ALU = rc("aluminum_block")
TI = rc("titanium_block")
LAUNCH_PAD = rc("launch_pad")
TOWER = rc("service_tower")
REFINERY = rc("fuel_refinery")
LIQUEFIER = rc("air_liquefier")
CONSOLE = rc("mission_control_console")
CREAM = rc("cream_panel")
TURQ = rc("turquoise_panel")
CHROME = rc("chrome_trim")
TABLE = rc("boomerang_table")
STOOL = rc("diner_stool")
EGG_CHAIR = rc("egg_chair")
CLOCK = rc("starburst_clock")
# station pack (ids and properties fixed by the design brief)
CONTROL_PANEL = rc("control_panel")       # facing, lit; wall
RADAR_SCOPE = rc("radar_scope")           # facing, lit
COMPUTER_BANK = rc("computer_bank")       # facing, lit
CAPTAIN_CHAIR = rc("captain_chair")       # facing
CREW_BUNK = rc("crew_bunk")               # facing
PLANTER = rc("hydroponic_planter")        # lit
O2_RACK = rc("oxygen_tank_rack")          # facing
VENDING = rc("vending_machine")           # facing, lit
STAR_CHART = rc("star_chart")             # facing, lit; wall
CEILING_LIGHT = rc("ceiling_light")       # lit; attaches to ceiling
SCONCE = rc("wall_sconce")                # facing, lit; wall
TELESCOPE = rc("telescope")               # facing
GLOBE = rc("space_globe")                 # facing
GRATE = rc("floor_grate")
HULL = rc("hull_panel")
HULL_STRIPED = rc("hull_panel_striped")
WINDOW = rc("hull_window")
REACTOR = rc("reactor_core")              # lit

# Full sturdy cubes (support for attachables, iron-bar connections).
FULL_CUBES = {LGRAY, RED, QUARTZ, LBLUE_GLASS, SEA_LANTERN, ALU, TI, CREAM, TURQ, CHROME, BOOKSHELF, TOWER,
              GRATE, HULL, HULL_STRIPED, WINDOW, "minecraft:white_concrete", "minecraft:smooth_quartz"}
# Blocks that need a support block on some side: name -> how to find the support cell.
ATTACH_BACK = {BUTTON, LADDER, SCONCE, CONTROL_PANEL, STAR_CHART, CLOCK}
ATTACH_BELOW = {WHITE_CARPET, RED_CARPET, "minecraft:cyan_carpet", IRON_DOOR, QUARTZ_STAIRS}
ATTACH_ABOVE = {CEILING_LIGHT}

DIRS = {"north": (0, -1), "south": (0, 1), "west": (-1, 0), "east": (1, 0)}
OPPOSITE = {"north": "south", "south": "north", "west": "east", "east": "west"}

RING_R = 35.0          # major radius of the habitat ring
RING_A, RING_B = 5.5, 4.3   # hull cross-section semi-axes (radial, vertical)
RING_CY = 5.5          # vertical centre of the cross-section
HUB_R = 9.5            # hub outer radius
HUB_ROOF = 13          # y of the docking deck (pad blocks)
SPOKE_ANGLES = (0, 90, 180, 270)
# Modules: (name, centre angle, half width in degrees).  Angle 0 = east, 90 = south (atan2(z, x)).
MODULES = [
    ("command", 270, 25), ("laboratory", 0, 25), ("hydroponics", 90, 25), ("crew", 180, 25),
    ("galley", 315, 20), ("medical", 45, 20), ("reactor", 135, 20), ("radar", 225, 20),
]
BULKHEADS = sorted({(c - w) % 360 for _, c, w in MODULES})


def ang_of(x, z):
    return math.degrees(math.atan2(z, x)) % 360


def ang_diff(a, b):
    return abs(math.remainder(a - b, 360.0))


def inward_dir(angle):
    """Cardinal direction pointing from a ring cell at `angle` towards the wheel centre."""
    a = angle % 360
    if 315 <= a or a < 45:
        return "west"
    if a < 135:
        return "north"
    if a < 225:
        return "east"
    return "south"


# ----------------------------------------------------------------------------
# Builder
# ----------------------------------------------------------------------------
class Station:
    def __init__(self):
        self.blocks = {}     # (x, y, z) -> (name, props dict, nbt Compound|None)
        self.inner = set()   # pressurised interior cells (air or furniture)
        self.warnings = []

    # -- primitives -------------------------------------------------------
    def put(self, x, y, z, name, props=None, nbt=None):
        """Structural block; a cell placed this way is never part of the pressurised volume."""
        self.blocks[(x, y, z)] = (name, dict(props or {}), nbt)
        self.inner.discard((x, y, z))

    def get(self, x, y, z):
        b = self.blocks.get((x, y, z))
        return b[0] if b else None

    def solid(self, x, y, z):
        return self.get(x, y, z) in FULL_CUBES

    def interior(self, x, y, z, name=AIR, props=None, nbt=None):
        """Pressurised cell: air or a piece of furniture standing in the room."""
        self.put(x, y, z, name, props, nbt)
        self.inner.add((x, y, z))

    def furnish(self, x, y, z, name, props=None, nbt=None):
        """Furniture inside a room; refuses to overwrite walls (keeps the hull watertight)."""
        if (x, y, z) not in self.inner:
            self.warnings.append(f"skip {name} at {(x, y, z)}: not interior")
            return False
        self.interior(x, y, z, name, props, nbt)
        return True

    def facing(self, x, y, z, name, facing, lit=None, extra=None):
        props = {"facing": facing}
        if lit is not None:
            props["lit"] = "true" if lit else "false"
        if extra:
            props.update(extra)
        return self.furnish(x, y, z, name, props)

    def wall_mount(self, x, y, z, name, facing, lit=None, prefer=None):
        """Wall decor: facing points away from the supporting wall.  Tries the preferred facing first,
        then any facing with a sturdy block behind.  Returns the facing used or None."""
        order = [f for f in ([facing] + (prefer or []) + list(DIRS)) if f]
        seen = []
        for f in order:
            if f in seen:
                continue
            seen.append(f)
            dx, dz = DIRS[f]
            if self.solid(x - dx, y, z - dz) and (x, y, z) in self.inner and self.get(x, y, z) == AIR:
                props = {"facing": f}
                if lit is not None:
                    props["lit"] = "true" if lit else "false"
                self.interior(x, y, z, name, props)
                return f
        self.warnings.append(f"no wall for {name} at {(x, y, z)}")
        return None

    def ceiling_light(self, x, y, z):
        if self.solid(x, y + 1, z) and (x, y, z) in self.inner and self.get(x, y, z) == AIR:
            self.interior(x, y, z, CEILING_LIGHT, {"lit": "true"})
            return True
        return False

    def chest(self, x, y, z, facing, items):
        stacks = List([Compound({"Slot": Byte(i), "id": Str(item), "count": Int(n)}) for i, (item, n) in enumerate(items)],
                      TAG_COMPOUND)
        nbt = Compound({"id": Str(CHEST), "Items": stacks})
        return self.furnish(x, y, z, CHEST, {"facing": facing, "type": "single", "waterlogged": "false"}, nbt)

    def bed(self, x, y, z, facing, color="white"):
        dx, dz = DIRS[facing]
        head = (x + dx, y, z + dz)
        if (x, y, z) not in self.inner or head not in self.inner or not self.solid(x, y - 1, z) or not self.solid(*head[:1], y - 1, head[2]):
            self.warnings.append(f"skip bed at {(x, y, z)}")
            return False
        self.interior(x, y, z, f"minecraft:{color}_bed", {"facing": facing, "part": "foot", "occupied": "false"})
        self.interior(*head, f"minecraft:{color}_bed", {"facing": facing, "part": "head", "occupied": "false"})
        return True

    def iron_door(self, x, y, z, facing):
        assert self.solid(x, y - 1, z), f"door at {(x, y, z)} has no floor"
        base = {"facing": facing, "hinge": "left", "open": "false", "powered": "false"}
        self.interior(x, y, z, IRON_DOOR, dict(base, half="lower"))
        self.interior(x, y + 1, z, IRON_DOOR, dict(base, half="upper"))

    def button(self, x, y, z, facing):
        dx, dz = DIRS[facing]
        assert self.solid(x - dx, y, z - dz), f"button at {(x, y, z)} has no wall"
        self.put(x, y, z, BUTTON, {"face": "wall", "facing": facing, "powered": "false"})

    def stairs(self, x, y, z, facing):
        self.interior(x, y, z, QUARTZ_STAIRS, {"facing": facing, "half": "bottom", "shape": "straight", "waterlogged": "false"})

    # -- polar helpers ------------------------------------------------------
    @staticmethod
    def cell(angle, radius):
        a = math.radians(angle)
        return int(round(math.cos(a) * radius)), int(round(math.sin(a) * radius))

    def touches_wall(self, x, y, z, side):
        """True when a horizontal neighbour of the cell is a solid wall further out (side > 0) or further in."""
        r = math.hypot(x, z)
        for dx, dz in DIRS.values():
            nr = math.hypot(x + dx, z + dz)
            if self.solid(x + dx, y, z + dz) and (x + dx, y, z + dz) not in self.inner and (nr > r if side > 0 else nr < r):
                return True
        return False

    def ring_band(self, a0, a1, dr0, dr1, y=4, touch=0):
        """Interior ring cells (air) with angle in [a0, a1] (degrees, clockwise span) and radial offset
        dr in [dr0, dr1] at height y, sorted by angle.  touch=+1/-1 keeps only cells touching the
        outer/inner wall, so wall-mounted blocks always have a support."""
        out = []
        for (x, yy, z) in self.inner:
            if yy != y:
                continue
            r = math.hypot(x, z)
            dr = r - RING_R
            if not (dr0 - 0.01 <= dr <= dr1 + 0.01) or r < RING_R - 4:
                continue
            if touch and not self.touches_wall(x, yy, z, touch):
                continue
            a = ang_of(x, z)
            span = (a1 - a0) % 360
            if (a - a0) % 360 <= span and self.get(x, yy, z) == AIR:
                out.append(((a - a0) % 360, x, z))
        out.sort()
        return [(x, z) for _, x, z in out]

    def hub_edge(self, a, y, r_max=7.5):
        """Interior hub cell at angle `a` that touches the hub wall (or None)."""
        r = r_max
        while r > 5:
            x, z = self.cell(a, r)
            if (x, y, z) in self.inner and self.get(x, y, z) == AIR and any(
                    self.solid(x + dx, y, z + dz) for dx, dz in DIRS.values()):
                return x, z
            r -= 0.25
        return None

    # ---------------------------------------------------------------------
    # Habitat ring
    # ---------------------------------------------------------------------
    @staticmethod
    def ring_inside(r, y):
        return ((r - RING_R) / RING_A) ** 2 + ((y - RING_CY) / RING_B) ** 2 <= 1.0

    @staticmethod
    def ring_interior(r, y):
        return abs(r - RING_R) <= 3.5 and 4 <= y <= 7

    def module_at(self, angle):
        for name, c, w in MODULES:
            if ang_diff(angle, c) <= w:
                return name, c, w
        return None, None, None

    def ring(self):
        big_window_rooms = {"command", "radar", "laboratory", "crew", "medical", "galley"}
        lim = int(RING_R + RING_A) + 1
        for x in range(-lim, lim + 1):
            for z in range(-lim, lim + 1):
                r = math.hypot(x, z)
                if abs(r - RING_R) > RING_A + 0.5:
                    continue
                dr = r - RING_R
                ang = ang_of(x, z)
                room, rc_, rw = self.module_at(ang)
                for y in range(1, 11):
                    if self.ring_interior(r, y):
                        self.interior(x, y, z)
                        continue
                    if not self.ring_inside(r, y):
                        continue
                    liner = any(self.ring_interior(math.hypot(x + dx, z + dz), y + dy)
                                for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)))
                    if liner:
                        if y == 3:      # floor
                            name = GRATE if abs(dr) <= 0.5 else LGRAY
                        elif y == 8:    # ceiling
                            name = HULL
                        elif y == 4:
                            name = TURQ
                        else:
                            name = CREAM
                            if y in (5, 6) and self.is_window(ang, dr, y, room, rc_, rw, big_window_rooms):
                                name = WINDOW
                        self.put(x, y, z, name)
                    else:
                        name = HULL
                        if y == 2 and abs(dr) <= 0.5:
                            name = SEA_LANTERN           # glows up through the floor grate
                        elif y == 9 and abs(dr) <= 1.5:
                            name = DAYLIGHT              # solar mirror band
                        elif y == 9 and abs(dr) <= 2.5:
                            name = ALU
                        elif y in (5, 6) and dr > 0 and self.is_window(ang, dr, y, room, rc_, rw, big_window_rooms):
                            name = WINDOW
                        elif y == 5 and dr < 0 and self.is_window(ang, dr, y, room, rc_, rw, big_window_rooms):
                            name = WINDOW
                        elif any(ang_diff(ang, b) < 1.2 for b in BULKHEADS):
                            name = HULL_STRIPED          # external rib marking each bulkhead
                        if name == DAYLIGHT:
                            self.put(x, y, z, name, {"inverted": "false", "power": "0"})
                        else:
                            self.put(x, y, z, name)
                # keel under the lantern strip
                if abs(dr) <= 1.0:
                    self.put(x, 1, z, HULL)
        self.bulkheads()

    def is_window(self, ang, dr, y, room, rc_, rw, big_rooms):
        if dr > 0:   # outer wall
            if room in big_rooms and ang_diff(ang, rc_) <= rw - 7 and y in (5, 6):
                return True
            return y == 5 and int(ang * 1.6) % 3 == 0
        return y == 5 and int(ang * 1.6) % 3 == 0

    def bulkheads(self):
        """Radial walls between modules with a 3-wide, 3-tall doorway and a striped lintel."""
        for b in BULKHEADS:
            rad = math.radians(b)
            ux, uz = math.cos(rad), math.sin(rad)
            for (x, y, z) in list(self.inner):
                if y < 4 or y > 7 or math.hypot(x, z) < RING_R - 4:
                    continue
                along = x * ux + z * uz
                perp = -x * uz + z * ux
                if along <= 0 or abs(perp) > 0.5:
                    continue
                dr = math.hypot(x, z) - RING_R
                if abs(dr) <= 1.5 and y <= 6:
                    continue                     # doorway
                if abs(dr) <= 2.5 and y <= 6:
                    self.put(x, y, z, CHROME, {"axis": "y"})
                elif y == 7 and abs(dr) <= 1.5:
                    self.put(x, y, z, HULL_STRIPED)
                else:
                    self.put(x, y, z, HULL)

    # ---------------------------------------------------------------------
    # Spokes and hub
    # ---------------------------------------------------------------------
    def spokes(self):
        for a in SPOKE_ANGLES:
            ux, uz = round(math.cos(math.radians(a))), round(math.sin(math.radians(a)))
            t0, t1 = int(HUB_R) + 1, int(RING_R - RING_A) + 1     # 10 .. 30
            for t in range(t0, t1 + 1):
                for u in range(-3, 4):
                    x, z = t * ux - u * uz, t * uz + u * ux
                    for y in range(2, 9):
                        if abs(u) <= 1 and 4 <= y <= 6:
                            self.interior(x, y, z)
                        elif abs(u) <= 1 and y == 3:
                            self.put(x, y, z, GRATE if u == 0 else LGRAY)
                        elif abs(u) <= 1 and y == 7:
                            self.put(x, y, z, HULL)
                        elif abs(u) == 2 and 3 <= y <= 7:
                            if y == 4:
                                self.put(x, y, z, TURQ)
                            elif y == 5 and t % 4 == 0:
                                self.put(x, y, z, WINDOW)
                            else:
                                self.put(x, y, z, CREAM if 4 <= y <= 6 else HULL)
                        else:
                            if abs(u) == 3 and y in (2, 8):
                                continue
                            if t in (t0, t0 + 1, t1 - 1, t1):
                                self.put(x, y, z, HULL_STRIPED)
                            elif abs(u) == 3 and y == 5 and t % 4 == 0:
                                self.put(x, y, z, WINDOW)
                            elif u == 0 and y == 2:
                                self.put(x, y, z, SEA_LANTERN)
                            else:
                                self.put(x, y, z, HULL)
            # carve the junction through the hub wall and the ring inner wall
            for t in list(range(int(HUB_R) - 2, int(HUB_R) + 1)) + list(range(t1, t1 + 3)):
                for u in (-1, 0, 1):
                    x, z = t * ux - u * uz, t * uz + u * ux
                    r = math.hypot(x, z)
                    if (7.5 < r <= HUB_R) or (RING_R - 5.6 < r <= RING_R - 3.5):
                        self.put(x, 3, z, LGRAY if u else GRATE)
                        for y in (4, 5, 6):
                            self.interior(x, y, z)
                        self.put(x, 7, z, HULL)
            # ceiling lights along the spoke
            for t in range(t0 + 3, t1, 4):
                x, z = t * ux, t * uz
                self.ceiling_light(x, 6, z)

    def hub(self):
        R = HUB_R
        lim = int(R) + 1
        cells = [(x, z) for x in range(-lim, lim + 1) for z in range(-lim, lim + 1) if math.hypot(x, z) <= R]
        for (x, z) in cells:
            r = math.hypot(x, z)
            ang = ang_of(x, z)
            window = ang_diff(ang % 90, 45) < 9 and 2 < r   # between the spokes
            self.put(x, 1, z, HULL)
            if r > 7.5:
                # two-layer wall, y 2..12
                hull = r > 8.5
                for y in range(2, HUB_ROOF):
                    if hull:
                        name = HULL
                        if y in (5, 10) and window:
                            name = WINDOW
                        elif y == 11:
                            name = HULL_STRIPED
                        elif y == 2:
                            name = ALU
                    else:
                        name = CREAM
                        if y in (5, 10) and window:
                            name = WINDOW
                        elif y in (4, 9):
                            name = TURQ
                        elif y in (3, 8):
                            name = LGRAY
                    self.put(x, y, z, name)
            else:
                self.put(x, 2, z, SEA_LANTERN if 5.5 < r <= 6.5 else HULL)
                self.put(x, 3, z, GRATE if 5.5 < r <= 6.5 else LGRAY)
                for y in range(4, 8):
                    self.interior(x, y, z)
                self.put(x, 8, z, LGRAY)
                for y in range(9, HUB_ROOF):
                    self.interior(x, y, z)
            # docking deck
            name = HULL
            if r > 8.5:
                name = HULL_STRIPED
            elif 3.5 < r <= 4.5:
                name = RED
            if abs(x) <= 1 and abs(z) <= 1:
                name = LAUNCH_PAD
            self.put(x, HUB_ROOF, z, name)
        # deck lights at the corners of the ring around the pad
        for (x, z) in ((3, 3), (-3, 3), (3, -3), (-3, -3)):
            self.put(x, HUB_ROOF, z, SEA_LANTERN)
        # service tower east of the pad (dx = +2), base on the deck
        for y in range(HUB_ROOF, HUB_ROOF + 8):
            self.put(2, y, 0, TOWER)
        # dish under the hub
        for x in range(-4, 5):
            for z in range(-4, 5):
                d = math.hypot(x, z)
                if 0 < d <= 4.5:
                    self.put(x, 0, z, QUARTZ_SLAB, {"type": "top", "waterlogged": "false"})
        self.put(0, 0, 0, END_ROD, {"facing": "down"})
        # antenna mast on the deck edge (outside the 5x5 clearance column)
        for y in range(HUB_ROOF + 1, HUB_ROOF + 6):
            self.put(6, y, -6, CHROME, {"axis": "y"})
        self.put(6, HUB_ROOF + 6, -6, LIGHTNING_ROD, {"facing": "up", "powered": "false", "waterlogged": "false"})
        self.put(7, HUB_ROOF + 4, -6, END_ROD, {"facing": "east"})
        self.put(5, HUB_ROOF + 4, -6, END_ROD, {"facing": "west"})
        self.put(6, HUB_ROOF + 4, -5, END_ROD, {"facing": "south"})
        self.put(6, HUB_ROOF + 4, -7, END_ROD, {"facing": "north"})
        self.put(6, HUB_ROOF + 2, -6, SEA_LANTERN)
        self.airlock_hut()
        self.hub_interior()

    def airlock_hut(self):
        """Airlock on the deck (west side) with a ladder shaft down into the docking lobby."""
        y0 = HUB_ROOF + 1
        for x in range(-9, -4):
            for z in range(-2, 3):
                for y in range(y0, y0 + 4):
                    edge = x in (-9, -5) or z in (-2, 2) or y == y0 + 3
                    if edge:
                        self.put(x, y, z, HULL_STRIPED if y == y0 + 3 and (x in (-9, -5) or z in (-2, 2)) else HULL)
                    else:
                        self.interior(x, y, z)
        self.put(-5, y0 + 1, -1, WINDOW)
        self.put(-7, y0 + 1, 2, WINDOW)
        self.put(-7, y0 + 1, -2, WINDOW)
        # shaft through the roof and the lobby liner, ladder on the west wall (x = -9 is solid all the way)
        for y in range(9, y0):
            self.interior(-8, y, 0)
        for y in range(9, y0 + 2):
            assert self.solid(-9, y, 0), (y, self.get(-9, y, 0))
            self.interior(-8, y, 0, LADDER, {"facing": "east", "waterlogged": "false"})
        # door facing the pad, buttons on both sides
        self.iron_door(-5, y0, 0, "east")
        self.button(-4, y0 + 1, 1, "east")
        self.button(-6, y0 + 1, 1, "west")
        self.ceiling_light(-7, y0 + 2, 0)
        self.wall_mount(-6, y0 + 1, -1, SCONCE, "west", lit=True)

    def hub_interior(self):
        # --- lower level: supply room ---
        fuel = [(rc("rocket_fuel_canister"), 8)] * 3
        lox = [(rc("liquid_oxygen_canister"), 8)] * 3
        spares = [(rc("empty_fuel_canister"), 8), (rc("titanium_plate"), 12), ("minecraft:iron_ingot", 16),
                  ("minecraft:redstone", 16), (rc("rocket_fuel_canister"), 4), (rc("liquid_oxygen_canister"), 4)]
        food = [("minecraft:bread", 16), ("minecraft:apple", 12), ("minecraft:golden_carrot", 8), ("minecraft:cookie", 16)]
        groups = {45: (fuel, lox, spares), 135: (food, fuel, lox), 225: (lox, spares, food), 315: (fuel, food, lox)}
        for a, items in groups.items():
            for k, offset in enumerate((-12, 0, 12)):
                x, z = self.cell(a + offset, 7.0)
                self.chest(x, 4, z, inward_dir(a + offset), items[k])
            e = self.hub_edge(a - 6, 6)
            if e:
                self.wall_mount(e[0], 6, e[1], SCONCE, inward_dir(a - 6), lit=True)
            x, z = self.cell(a + 6, 7.0)
            self.furnish(x, 4, z, BARREL, {"facing": "up", "open": "false"})
            self.furnish(x, 5, z, BARREL, {"facing": "up", "open": "false"})
        for a in (20, 70, 110, 160, 200, 250, 290, 340):
            x, z = self.cell(a, 6.5)
            self.furnish(x, 4, z, O2_RACK, {"facing": inward_dir(a)})
        for (x, z) in ((3, 3), (-3, 3), (3, -3), (-3, -3)):
            self.ceiling_light(x, 7, z)
        self.furnish(0, 4, 0, CHROME, {"axis": "y"})
        self.furnish(0, 5, 0, CHROME, {"axis": "y"})
        self.furnish(0, 6, 0, CHROME, {"axis": "y"})
        self.furnish(0, 7, 0, CHROME, {"axis": "y"})
        # stairs lower <-> upper: x 4..5, climbing north from z=2 (y4) to z=-1 (y7)
        for i, z in enumerate((2, 1, 0, -1)):
            y = 4 + i
            for x in (4, 5):
                self.stairs(x, y, z, "north")
                for yy in range(4, y):
                    self.put(x, yy, z, LGRAY)
        for x in (4, 5):
            for z in (-1, 0):
                self.interior(x, 8, z)          # opening in the upper floor
            self.put(x, 8, 1, LGRAY)
            self.put(x, 8, 2, LGRAY)
        for z in (-1, 0):
            self.furnish(3, 9, z, CHROME, {"axis": "y"})   # railing
            self.furnish(6, 9, z, CHROME, {"axis": "y"})
        self.furnish(4, 9, -2, CHROME, {"axis": "x"})
        self.furnish(5, 9, -2, CHROME, {"axis": "x"})
        # --- upper level: docking lobby ---
        for (x, z) in ((3, 3), (-3, 3), (3, -3), (-3, -3), (0, 5), (0, -5), (-5, 0), (5, 0)):
            self.ceiling_light(x, HUB_ROOF - 1, z)
        self.furnish(0, 9, 0, CHROME, {"axis": "y"})
        self.furnish(0, 10, 0, CHROME, {"axis": "y"})
        self.furnish(0, 11, 0, CHROME, {"axis": "y"})
        self.furnish(0, 12, 0, CHROME, {"axis": "y"})
        for a in (45, 135, 225, 315):
            e = self.hub_edge(a, 10)
            if e:
                self.wall_mount(e[0], 10, e[1], CONTROL_PANEL, inward_dir(a), lit=True)
        e = self.hub_edge(90, 10)
        self.wall_mount(e[0], 10, e[1], STAR_CHART, "north", lit=True)
        for a in (60, 120):
            x, z = self.cell(a, 7.0)
            self.furnish(x, 9, z, O2_RACK, {"facing": "north"})
        for a in (240, 300):
            x, z = self.cell(a, 7.0)
            self.furnish(x, 9, z, BARREL, {"facing": "south", "open": "false"})
        x, z = self.cell(270, 7.0)
        self.facing(x, 9, z, COMPUTER_BANK, "south", lit=True)
        self.chest(-6, 9, 3, "east", [(rc("rocket_fuel_canister"), 8), (rc("liquid_oxygen_canister"), 8)])
        self.chest(-6, 9, -3, "east", [("minecraft:torch", 16), ("minecraft:bread", 8), (rc("empty_fuel_canister"), 4)])
        self.facing(5, 9, 4, EGG_CHAIR, "west")
        self.facing(5, 9, -4, EGG_CHAIR, "west")
        for a in (20, 160, 200, 340):
            e = self.hub_edge(a, 10)
            if e:
                self.wall_mount(e[0], 10, e[1], SCONCE, inward_dir(a), lit=True)

    # ---------------------------------------------------------------------
    # Ring modules
    # ---------------------------------------------------------------------
    def outer_row(self, c, w, margin=2):
        """Interior cells touching the outer wall of a module (dr 2.5..3.5), away from the bulkheads."""
        return self.ring_band(c - w + margin, c + w - margin, 1.5, 3.5, touch=1)

    def inner_row(self, c, w, margin=2):
        return self.ring_band(c - w + margin, c + w - margin, -3.5, -1.5, touch=-1)

    def second_outer_row(self, c, w, margin=2):
        return self.ring_band(c - w + margin, c + w - margin, 1.5, 2.5)

    def lights(self, c, w, step=5):
        """Ceiling lights along the module centre line; sconces on both walls."""
        for (x, z) in self.ring_band(c - w + 2, c + w - 2, -0.5, 0.5, y=7)[::step]:
            self.ceiling_light(x, 7, z)
        for (x, z) in self.ring_band(c - w + 3, c + w - 3, 1.5, 3.5, y=6, touch=1)[3::9]:
            self.wall_mount(x, 6, z, SCONCE, inward_dir(ang_of(x, z)), lit=True)
        for (x, z) in self.ring_band(c - w + 3, c + w - 3, -3.5, -1.5, y=6, touch=-1)[6::9]:
            self.wall_mount(x, 6, z, SCONCE, OPPOSITE[inward_dir(ang_of(x, z))], lit=True)

    def every(self, cells, step, start=0):
        return cells[start::step]

    def facing_in(self, x, z):
        return inward_dir(ang_of(x, z))

    def facing_out(self, x, z):
        return OPPOSITE[inward_dir(ang_of(x, z))]

    def command_center(self):
        c, w = 270, 25
        outer = self.outer_row(c, w)
        n = len(outer)
        mid = n // 2
        # console in the middle of the outer row, computer banks either side
        cx, cz = outer[mid]
        self.facing(cx, 4, cz, CONSOLE, "south")
        for (x, z) in outer[mid - 6:mid - 1] + outer[mid + 2:mid + 7]:
            self.facing(x, 4, z, COMPUTER_BANK, "south", lit=True)
        for (x, z) in outer[mid - 8:mid - 6] + outer[mid + 7:mid + 9]:
            self.facing(x, 4, z, RADAR_SCOPE, "south", lit=True)
        for (x, z) in outer[2:mid - 9] + outer[mid + 10:n - 2]:
            self.facing(x, 4, z, COMPUTER_BANK, self.facing_in(x, z), lit=True)
            self.wall_mount(x, 5, z, CONTROL_PANEL, self.facing_in(x, z), lit=True)
        # operators' chairs and the captain
        second = self.second_outer_row(c, w)
        m2 = len(second) // 2
        for (x, z) in (second[m2 - 3], second[m2], second[m2 + 3]):
            self.furnish(x, 4, z, STOOL)
        centre = self.ring_band(c - 1.5, c + 1.5, -1.5, -0.5)
        if centre:
            x, z = centre[len(centre) // 2]
            self.facing(x, 4, z, CAPTAIN_CHAIR, "north")
        # inner wall: star charts, radar scopes, lockers (spoke doorway stays clear)
        inner = self.inner_row(c, w)
        for (x, z) in inner:
            a = ang_of(x, z)
            if ang_diff(a, c) < 4:
                continue
            k = int(ang_diff(a, c))
            if k in (6, 7):
                self.wall_mount(x, 5, z, STAR_CHART, "north", lit=True)
            elif k in (9, 14, 19):
                self.facing(x, 4, z, RADAR_SCOPE, "north", lit=True)
            elif k in (11, 16):
                self.furnish(x, 4, z, BOOKSHELF)
                self.furnish(x, 5, z, BOOKSHELF)
            elif k in (12, 21):
                self.furnish(x, 4, z, BARREL, {"facing": "north", "open": "false"})
        self.lights(c, w)
        for (x, z) in self.ring_band(c - 20, c + 20, -0.5, 0.5)[::7]:
            self.furnish(x, 4, z, RED_CARPET) if self.get(x, 3, z) in FULL_CUBES else None

    def laboratory(self):
        c, w = 0, 25
        outer = self.outer_row(c, w)
        n = len(outer)
        mid = n // 2
        x, z = outer[mid - 2]
        self.facing(x, 4, z, REFINERY, "west", lit=False)
        x, z = outer[mid + 2]
        self.facing(x, 4, z, LIQUEFIER, "west", lit=False)
        for (x, z) in (outer[mid - 2], outer[mid + 2]):
            for y in (5, 6, 7):
                self.furnish(x, y, z, CHROME, {"axis": "y"})     # exhaust stacks to the ceiling
        x, z = outer[mid]
        self.chest(x, 4, z, "west", [(rc("empty_fuel_canister"), 6), ("minecraft:bucket", 2), ("minecraft:coal", 16)])
        self.wall_mount(x, 5, z, CONTROL_PANEL, "west", lit=True)
        for (x, z) in outer[mid - 5:mid - 2] + outer[mid + 3:mid + 6]:
            self.facing(x, 4, z, COMPUTER_BANK, self.facing_in(x, z), lit=True)
        for (x, z) in outer[2:mid - 6] + outer[mid + 7:n - 2]:
            k = int(ang_diff(ang_of(x, z), c))
            if k % 3 == 0:
                self.furnish(x, 4, z, O2_RACK, {"facing": self.facing_in(x, z)})
            elif k % 3 == 1:
                self.furnish(x, 4, z, CHROME, {"axis": "y"})
                for y in (5, 6):
                    self.furnish(x, y, z, LBLUE_GLASS)
                self.furnish(x, 7, z, CHROME, {"axis": "y"})
        # bench in the second row
        second = self.second_outer_row(c, w)
        m2 = len(second) // 2
        for (x, z) in second[m2 - 8:m2 - 5]:
            self.furnish(x, 4, z, QUARTZ)
        bx, bz = second[m2 - 7]
        self.furnish(bx, 5, bz, "minecraft:brewing_stand", {"has_bottle_0": "false", "has_bottle_1": "false",
                                                           "has_bottle_2": "false"})
        bx, bz = second[m2 - 6]
        self.furnish(bx, 5, bz, "minecraft:lever", {"face": "floor", "facing": "north", "powered": "false"})
        for (x, z) in second[m2 + 5:m2 + 8]:
            self.furnish(x, 4, z, QUARTZ)
        bx, bz = second[m2 + 6]
        self.furnish(bx, 5, bz, "minecraft:cauldron")
        # inner wall: library, workshop, star chart
        inner = self.inner_row(c, w)
        for (x, z) in inner:
            k = int(ang_diff(ang_of(x, z), c))
            if k < 4:
                continue
            if k in (6, 7, 8):
                self.furnish(x, 4, z, BOOKSHELF)
                self.furnish(x, 5, z, BOOKSHELF)
            elif k == 10:
                self.furnish(x, 4, z, "minecraft:crafting_table")
            elif k == 12:
                self.furnish(x, 4, z, "minecraft:anvil", {"facing": "north"})
            elif k == 14:
                self.furnish(x, 4, z, "minecraft:blast_furnace", {"facing": self.facing_out(x, z), "lit": "false"})
            elif k in (16, 17):
                self.facing(x, 4, z, COMPUTER_BANK, self.facing_out(x, z), lit=True)
            elif k == 19:
                self.wall_mount(x, 5, z, STAR_CHART, self.facing_out(x, z), lit=True)
        self.lights(c, w)

    def hydroponics(self):
        c, w = 90, 25
        outer = self.outer_row(c, w)
        second = self.second_outer_row(c, w)
        inner = self.inner_row(c, w)
        inner2 = self.ring_band(c - w + 2, c + w - 2, -2.5, -1.5)
        for (x, z) in outer:
            self.furnish(x, 4, z, PLANTER, {"lit": "true"})
        for (x, z) in inner:
            if ang_diff(ang_of(x, z), c) > 4:
                self.furnish(x, 4, z, PLANTER, {"lit": "true"})
        for (x, z) in second[::2] + inner2[1::2]:
            if ang_diff(ang_of(x, z), c) > 4:
                self.furnish(x, 4, z, PLANTER, {"lit": "true"})
        # grow lights over every planter row, water tanks at the ends
        for (x, z) in self.ring_band(c - w + 2, c + w - 2, 2.5, 3.5, y=7)[::3] + \
                self.ring_band(c - w + 2, c + w - 2, -3.5, -2.5, y=7)[::3]:
            self.ceiling_light(x, 7, z)
        for (x, z) in (outer[0], outer[-1]):
            for y in (4, 5, 6):
                self.furnish(x, y, z, LBLUE_GLASS)
            self.furnish(x, 7, z, CHROME, {"axis": "y"})
        for (x, z) in self.ring_band(c - 22, c + 22, -0.5, 0.5):
            if self.get(x, 3, z) == LGRAY:
                self.put(x, 3, z, GRATE)
        self.lights(c, w, step=4)

    def crew_quarters(self):
        c, w = 180, 25
        outer = self.outer_row(c, w)
        for i, (x, z) in enumerate(outer):
            if i % 2 == 0:
                self.facing(x, 4, z, CREW_BUNK, self.facing_in(x, z))
                self.facing(x, 5, z, CREW_BUNK, self.facing_in(x, z))
            else:
                self.furnish(x, 4, z, BARREL, {"facing": self.facing_in(x, z), "open": "false"})
                self.wall_mount(x, 5, z, SCONCE, self.facing_in(x, z), lit=True)
        inner = self.inner_row(c, w)
        for (x, z) in inner:
            k = int(ang_diff(ang_of(x, z), c))
            if k < 4:
                continue
            if k % 4 == 0:
                self.furnish(x, 4, z, BARREL, {"facing": self.facing_out(x, z), "open": "false"})
                self.furnish(x, 5, z, BARREL, {"facing": self.facing_out(x, z), "open": "false"})
            elif k % 4 == 2:
                self.facing(x, 4, z, TABLE, "north")
                self.furnish(x, 5, z, rc("rocket_table_lamp"), {"facing": "north", "lit": "true"})
            elif k == 9:
                self.wall_mount(x, 5, z, CLOCK, self.facing_out(x, z))
            elif k == 17:
                self.wall_mount(x, 5, z, STAR_CHART, self.facing_out(x, z), lit=True)
        second = self.second_outer_row(c, w)
        for (x, z) in second[::6]:
            self.furnish(x, 4, z, RED_CARPET)
        self.lights(c, w)

    def galley(self):
        c, w = 315, 20
        outer = self.outer_row(c, w)
        n = len(outer)
        mid = n // 2
        for (x, z) in (outer[mid - 1], outer[mid + 1]):
            self.facing(x, 4, z, VENDING, self.facing_in(x, z), lit=True)
        x, z = outer[mid]
        self.furnish(x, 4, z, "minecraft:smoker", {"facing": self.facing_in(x, z), "lit": "false"})
        x, z = outer[mid - 3]
        self.furnish(x, 4, z, "minecraft:cauldron")
        x, z = outer[mid + 3]
        self.chest(x, 4, z, self.facing_in(x, z), [("minecraft:bread", 12), ("minecraft:cookie", 16), ("minecraft:apple", 8)])
        for (x, z) in (outer[mid - 5], outer[mid + 5]):
            self.furnish(x, 4, z, BARREL, {"facing": "up", "open": "false"})
        # tables with seats in the inner band
        inner = self.inner_row(c, w)
        m = len(inner) // 2
        for (x, z) in (inner[m - 3], inner[m + 3]):
            self.facing(x, 4, z, TABLE, "north")
        inner2 = self.ring_band(c - w + 2, c + w - 2, -2.5, -1.5)
        m2 = len(inner2) // 2
        for (x, z) in (inner2[m2 - 4], inner2[m2 - 2], inner2[m2 + 2], inner2[m2 + 4]):
            self.furnish(x, 4, z, STOOL)
        x, z = inner[m]
        self.wall_mount(x, 5, z, CLOCK, self.facing_out(x, z))
        self.lights(c, w)

    def medical(self):
        c, w = 45, 20
        outer = self.outer_row(c, w)
        n = len(outer)
        mid = n // 2
        placed = 0
        for (x, z) in (outer[mid - 4], outer[mid + 4]):
            f = self.facing_out(x, z)
            dx, dz = DIRS[f]
            # bed foot in the second row, head against the outer wall
            if self.bed(x - dx, 4, z - dz, f, "white"):
                placed += 1
        x, z = outer[mid]
        self.furnish(x, 4, z, QUARTZ)
        self.furnish(x, 5, z, "minecraft:brewing_stand", {"has_bottle_0": "false", "has_bottle_1": "false",
                                                        "has_bottle_2": "false"})
        for (x, z) in (outer[mid - 1], outer[mid + 1]):
            self.chest(x, 4, z, self.facing_in(x, z), [("minecraft:golden_apple", 2), ("minecraft:bread", 8),
                                                        ("minecraft:paper", 8), ("minecraft:glass_bottle", 6)])
        for (x, z) in (outer[mid - 2], outer[mid + 2]):
            self.wall_mount(x, 5, z, CONTROL_PANEL, self.facing_in(x, z), lit=True)
        x, z = outer[mid - 7]
        self.furnish(x, 4, z, "minecraft:cauldron")
        x, z = outer[mid + 7]
        self.facing(x, 4, z, COMPUTER_BANK, self.facing_in(x, z), lit=True)
        inner = self.inner_row(c, w)
        m = len(inner) // 2
        for (x, z) in (inner[m - 5], inner[m + 5]):
            self.furnish(x, 4, z, O2_RACK, {"facing": self.facing_out(x, z)})
        x, z = inner[m]
        self.wall_mount(x, 5, z, STAR_CHART, self.facing_out(x, z), lit=True)
        for (x, z) in (inner[m - 2], inner[m + 2]):
            self.furnish(x, 4, z, BOOKSHELF)
        for (x, z) in self.ring_band(c - 8, c + 8, -0.5, 0.5):
            self.furnish(x, 4, z, WHITE_CARPET)
        self.lights(c, w)

    def reactor_room(self):
        c, w = 135, 20
        # striped warning floor + grate with lanterns around two reactor columns
        for (x, z) in self.ring_band(c - 10, c + 10, -3.5, 3.5):
            dr = math.hypot(x, z) - RING_R
            if abs(dr) > 2.5:
                self.put(x, 3, z, HULL_STRIPED)
            else:
                self.put(x, 3, z, GRATE)
                self.put(x, 2, z, SEA_LANTERN)
        cores = []
        for a in (c - 6, c + 6):
            for dr in (-2.0, 2.0):
                x, z = self.cell(a, RING_R + dr)
                if (x, 4, z) in self.inner:
                    for y in (4, 5, 6):
                        self.furnish(x, y, z, REACTOR, {"lit": "true"})
                    cores.append((x, z))
        # chrome rails around the cores
        for (x, z) in cores:
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    if (dx or dz) and (x + dx, 4, z + dz) in self.inner and self.get(x + dx, 4, z + dz) == AIR:
                        if abs(math.hypot(x + dx, z + dz) - RING_R) <= 3.0:
                            self.furnish(x + dx, 4, z + dz, CHROME, {"axis": "x" if dz else "z"})
        outer = self.outer_row(c, w)
        n = len(outer)
        for (x, z) in outer[2:n - 2]:
            k = int(ang_diff(ang_of(x, z), c))
            if k <= 9:
                continue
            if k % 2 == 0:
                self.facing(x, 4, z, COMPUTER_BANK, self.facing_in(x, z), lit=True)
                self.wall_mount(x, 5, z, CONTROL_PANEL, self.facing_in(x, z), lit=True)
            else:
                self.furnish(x, 4, z, CHROME, {"axis": "y"})
                for y in (5, 6):
                    self.furnish(x, y, z, LBLUE_GLASS)
                self.furnish(x, 7, z, CHROME, {"axis": "y"})
        inner = self.inner_row(c, w)
        for (x, z) in inner:
            k = int(ang_diff(ang_of(x, z), c))
            if k < 4:
                continue
            if k in (11, 13, 15):
                f = self.facing_out(x, z)
                dx, dz = DIRS[f]
                if self.solid(x - dx, 5, z - dz):
                    self.furnish(x, 5, z, "minecraft:lever", {"face": "wall", "facing": f, "powered": "false"})
            elif k == 9:
                self.wall_mount(x, 5, z, CONTROL_PANEL, self.facing_out(x, z), lit=True)
            elif k == 17:
                self.facing(x, 4, z, RADAR_SCOPE, self.facing_out(x, z), lit=True)
        self.lights(c, w, step=4)

    def radar_room(self):
        c, w = 225, 20
        outer = self.outer_row(c, w)
        n = len(outer)
        mid = n // 2
        x, z = outer[mid]
        self.facing(x, 4, z, TELESCOPE, self.facing_out(x, z))
        for (x, z) in (outer[mid - 4], outer[mid + 4]):
            self.facing(x, 4, z, RADAR_SCOPE, self.facing_in(x, z), lit=True)
        for (x, z) in (outer[mid - 6], outer[mid + 6]):
            self.facing(x, 4, z, COMPUTER_BANK, self.facing_in(x, z), lit=True)
        for (x, z) in (outer[mid - 2], outer[mid + 2]):
            self.facing(x, 4, z, EGG_CHAIR, self.facing_out(x, z))
        second = self.second_outer_row(c, w)
        m2 = len(second) // 2
        x, z = second[m2]
        self.facing(x, 4, z, GLOBE, self.facing_in(x, z))
        inner = self.inner_row(c, w)
        m = len(inner) // 2
        x, z = inner[m]
        self.wall_mount(x, 5, z, STAR_CHART, self.facing_out(x, z), lit=True)
        for (x, z) in (inner[m - 3], inner[m + 3]):
            self.facing(x, 4, z, COMPUTER_BANK, self.facing_out(x, z), lit=True)
        for (x, z) in (inner[m - 5], inner[m + 5]):
            self.furnish(x, 4, z, BOOKSHELF)
            self.furnish(x, 5, z, BOOKSHELF)
        x, z = inner[m - 1]
        self.facing(x, 4, z, TABLE, "north")
        self.furnish(x, 5, z, rc("tube_radio"), {"facing": self.facing_out(x, z), "lit": "true"})
        self.lights(c, w)
        # radar dish on the roof above the room
        rx, rz = self.cell(c, RING_R)
        for y in (10, 11):
            self.put(rx, y, rz, CHROME, {"axis": "y"})
        for dx in range(-2, 3):
            self.put(rx + dx, 12, rz, QUARTZ_SLAB if dx else TI, {"type": "bottom", "waterlogged": "false"} if dx else None)
        self.put(rx, 13, rz, END_ROD, {"facing": "up"})

    def exterior_details(self):
        # beacon lights on the ring top at the spokes and mast tips
        for a in SPOKE_ANGLES:
            x, z = self.cell(a, RING_R + 4)
            if self.get(x, 9, z) is None and self.get(x, 8, z) in FULL_CUBES:
                self.put(x, 9, z, SEA_LANTERN)
        # short antenna masts on the ring above the command centre
        for a in (262, 278):
            x, z = self.cell(a, RING_R)
            if self.get(x, 9, z):
                self.put(x, 10, z, CHROME, {"axis": "y"})
                self.put(x, 11, z, CHROME, {"axis": "y"})
                self.put(x, 12, z, LIGHTNING_ROD, {"facing": "up", "powered": "false", "waterlogged": "false"})

    # ---------------------------------------------------------------------
    # Post-processing and checks
    # ---------------------------------------------------------------------
    def finish(self):
        for (x, y, z) in [p for p, b in self.blocks.items() if b[0] == LAUNCH_PAD]:
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
        for c in self.inner:
            if c not in self.blocks:
                self.blocks[c] = (AIR, {}, None)
        self.check()

    def check(self):
        problems = []
        for (x, y, z), (name, props, _) in self.blocks.items():
            if name in ATTACH_BACK:
                dx, dz = DIRS[props["facing"]]
                if not self.solid(x - dx, y, z - dz):
                    problems.append(f"{name} at {(x, y, z)} has no wall behind")
            if name == "minecraft:lever":
                if props.get("face") == "wall":
                    dx, dz = DIRS[props["facing"]]
                    if not self.solid(x - dx, y, z - dz):
                        problems.append(f"lever at {(x, y, z)} has no wall behind")
                elif not self.solid(x, y - 1, z):
                    problems.append(f"lever at {(x, y, z)} has nothing below")
            if name in ATTACH_BELOW and not self.solid(x, y - 1, z) and props.get("half") != "upper":
                problems.append(f"{name} at {(x, y, z)} has nothing below")
            if name in ATTACH_ABOVE and not self.solid(x, y + 1, z):
                problems.append(f"{name} at {(x, y, z)} has nothing above")
            if name == IRON_DOOR:
                other = (x, y + (1 if props["half"] == "lower" else -1), z)
                if self.get(*other) != IRON_DOOR:
                    problems.append(f"unpaired door at {(x, y, z)}")
            if name.endswith("_bed") and props["part"] == "foot":
                dx, dz = DIRS[props["facing"]]
                h = (x + dx, y, z + dz)
                if self.get(*h) != name or self.blocks[h][1]["part"] != "head":
                    problems.append(f"unpaired bed at {(x, y, z)}")
        # clearance above the pad
        for (x, y, z), (name, _, _) in self.blocks.items():
            if abs(x) <= 2 and abs(z) <= 2 and y > HUB_ROOF and name != TOWER:
                problems.append(f"{name} at {(x, y, z)} blocks the docking column")
        if problems:
            raise SystemExit("station.py: " + "\n  ".join(["structural problems:"] + problems))

    def build(self):
        self.ring()
        self.spokes()
        self.hub()
        self.command_center()
        self.laboratory()
        self.hydroponics()
        self.crew_quarters()
        self.galley()
        self.medical()
        self.reactor_room()
        self.radar_room()
        self.exterior_details()
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
            y1 = y0
            while (x0, y1 + 1, z0) in remaining:
                y1 += 1
            x1 = x0
            while all((x1 + 1, y, z0) in remaining for y in range(y0, y1 + 1)):
                x1 += 1
            z1 = z0
            while all((x, y, z1 + 1) in remaining for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)):
                z1 += 1
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
        return Compound({
            "DataVersion": Int(DATA_VERSION),
            "size": List([Int(mx - ox + 1), Int(my - oy + 1), Int(mz - oz + 1)], TAG_INT),
            "palette": palette,
            "blocks": blocks,
            "entities": List([], TAG_COMPOUND),
        })

    def anchors(self):
        (ox, oy, oz), (mx, my, mz) = self.bounds()
        arrival = (-3, 9, 0)
        assert arrival in self.inner and self.get(*arrival) == AIR and self.solid(arrival[0], 8, arrival[2])
        return {
            "size": [mx - ox + 1, my - oy + 1, mz - oz + 1],
            "pad_center": [0 - ox, HUB_ROOF - oy, 0 - oz],
            "arrival": [arrival[0] - ox, arrival[1] - oy, arrival[2] - oz],
            "pressurized": self.pressurized_boxes(),
        }


# ----------------------------------------------------------------------------
# Validation against the mod's registered blockstates
# ----------------------------------------------------------------------------
def validate(station):
    states_dir = os.path.join(ROOT, "assets", "retrocosmos", "blockstates")
    problems, missing = set(), set()
    for (name, props, _nbt) in station.blocks.values():
        if not name.startswith("retrocosmos:"):
            continue
        short = name.split(":", 1)[1]
        path = os.path.join(states_dir, short + ".json")
        if not os.path.exists(path):
            missing.add(name)
            continue
        with open(path, encoding="utf-8") as f:
            variants = json.load(f).get("variants")
        if variants is None:
            continue
        key = ",".join(f"{k}={v}" for k, v in sorted(props.items()))
        if key not in variants:
            problems.add(f"{name}[{key}] has no blockstate variant")
    if missing:
        print("station.py: blockstates not generated yet (ids/properties taken from the design brief): "
              + ", ".join(sorted(missing)))
    if problems:
        raise SystemExit("station.py: invalid block states:\n  " + "\n  ".join(sorted(problems)))


def generate():
    station = Station().build()
    validate(station)
    for w in station.warnings:
        print("station.py: warning:", w)
    root = station.to_nbt()
    data = nbt_bytes(root)
    os.makedirs(os.path.dirname(STRUCTURE_FILE), exist_ok=True)
    with gzip.open(STRUCTURE_FILE, "wb") as f:
        f.write(data)
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
