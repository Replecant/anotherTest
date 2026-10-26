"""Freedom Station ("Свобода") v3 - a crewed 1950s "wheel" station built from straight rectangular modules.

Writes a vanilla structure template (data/retrocosmos/structure/freedom_station.nbt) plus an anchors file
(data/retrocosmos/station/freedom_station.json) holding the docking pad, a safe arrival spot and the
pressurised interior boxes.  Only a small self-contained NBT writer/reader is used.

Plan (structure-local X east, Z south, Y up; the hub axis is the origin before normalisation):

    * Hub (octagonal drum, 17x17 inside).  Roof = docking deck: 3x3 launch pad, service tower, airlock hut.
      Upper level ("DECK H"): EVA prep / suit-up room under the airlock + supply stores (RP-1 / LOX).
      Lower level: the hub lobby, at ring level.  Four straight spokes run N/E/S/W to the ring.
    * Ring = a square loop of straight modules with chamfered corners (reads as a wheel from outside,
      every room inside is a rectangle).  A 3-wide ring corridor runs along the inside of the loop; all rooms
      sit on its outer side (pinwheel bands), each opening off the corridor through a doorway with a sign:
        DECK A (north) - observation lounge, commander's cabin, BRIDGE, radio room
        DECK B (east)  - machine shop, stores, LABORATORY, reactor room
        DECK C (south) - hydroponics, galley stores, MESS HALL, medical bay
        DECK D (west)  - recreation, washroom, six two-berth crew cabins
      The main room of each deck faces its spoke across the corridor.
    * Rooms are furnished through helpers working in room-local coordinates (u along the corridor, v from the
      corridor wall towards the hull, h above the floor) so every piece lines up against a straight wall, and
      a checker verifies supports, desks under electronics, seats facing something, free corridor lanes,
      reachability from the arrival spot, required equipment per room and an airtight pressurised volume.
"""
import gzip
import io
import json
import math
import os
import struct
from collections import deque

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


def mc(name):
    return "minecraft:" + name


AIR = mc("air")
STRUCT = "?structure"          # placeholder for hull mass that is painted later

# vanilla building blocks
WHITE = mc("white_concrete")
LGRAY = mc("light_gray_concrete")
GRAY = mc("gray_concrete")
RED = mc("red_concrete")
YELLOW = mc("yellow_concrete")
BLACK = mc("black_concrete")
CYAN_TERRA = mc("cyan_terracotta")
QUARTZ = mc("quartz_block")
SQUARTZ = mc("smooth_quartz")
SQUARTZ_SLAB = mc("smooth_quartz_slab")
QUARTZ_SLAB = mc("quartz_slab")
SQUARTZ_STAIRS = mc("smooth_quartz_stairs")
QUARTZ_STAIRS = mc("quartz_stairs")
BIRCH = mc("birch_planks")
SPRUCE = mc("spruce_planks")
DARK_OAK = mc("dark_oak_planks")
SPRUCE_SLAB = mc("spruce_slab")
DARK_OAK_SLAB = mc("dark_oak_slab")
IRON_BLOCK = mc("iron_block")
SEA_LANTERN = mc("sea_lantern")
GLASS = mc("glass")
TINTED_GLASS = mc("tinted_glass")
LBLUE_GLASS = mc("light_blue_stained_glass")
BOOKSHELF = mc("bookshelf")
CRAFTING = mc("crafting_table")
SMITHING = mc("smithing_table")
CARTOGRAPHY = mc("cartography_table")
FLETCHING = mc("fletching_table")
STONECUTTER = mc("stonecutter")
JUKEBOX = mc("jukebox")
LECTERN = mc("lectern")
COMPOSTER = mc("composter")
CHEST = mc("chest")
BARREL = mc("barrel")
BIRCH_DOOR = mc("birch_door")
IRON_DOOR = mc("iron_door")
BUTTON = mc("stone_button")
WALL_SIGN = mc("birch_wall_sign")
STANDING_SIGN = mc("birch_sign")
SMOKER = mc("smoker")
FURNACE = mc("furnace")
BLAST_FURNACE = mc("blast_furnace")
CAULDRON = mc("cauldron")
BREWING = mc("brewing_stand")
LANTERN = mc("lantern")
END_ROD = mc("end_rod")
LIGHTNING_ROD = mc("lightning_rod")
DAYLIGHT = mc("daylight_detector")
POTTED_FERN = mc("potted_fern")
IRON_TRAPDOOR = mc("iron_trapdoor")
COLORS = ("white", "light_gray", "gray", "red", "light_blue", "cyan", "blue", "orange", "yellow")


def bed_id(color):
    return mc(color + "_bed")


def carpet_id(color):
    return mc(color + "_carpet")


# station / mod blocks
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
CHECKER = rc("checkered_tile")
TABLE = rc("boomerang_table")
STOOL = rc("diner_stool")
EGG_CHAIR = rc("egg_chair")
SOFA = rc("googie_sofa")
CLOCK = rc("starburst_clock")
NEON = rc("neon_rocket_sign")
TV = rc("atomic_tv")
RADIO = rc("tube_radio")
LAMP = rc("rocket_table_lamp")
FLOOR_LAMP = rc("atomic_floor_lamp")
CHANDELIER = rc("sputnik_chandelier")
CONTROL_PANEL = rc("control_panel")
RADAR_SCOPE = rc("radar_scope")
COMPUTER = rc("computer_bank")
CAPTAIN_CHAIR = rc("captain_chair")
CREW_BUNK = rc("crew_bunk")
PLANTER = rc("hydroponic_planter")
O2_RACK = rc("oxygen_tank_rack")
VENDING = rc("vending_machine")
STAR_CHART = rc("star_chart")
CEILING_LIGHT = rc("ceiling_light")
SCONCE = rc("wall_sconce")
TELESCOPE = rc("telescope")
GLOBE = rc("space_globe")
GRATE = rc("floor_grate")
HULL = rc("hull_panel")
STRIPED = rc("hull_panel_striped")
WINDOW = rc("hull_window")
PORTHOLE = rc("porthole_window")
REACTOR = rc("reactor_core")
# v4 station furniture (ids and properties fixed by the design brief)
SUPPLY_CABINET = rc("supply_cabinet")     # facing; storage
CARGO_CRATE = rc("cargo_crate")           # no properties; storage
CREW_LOCKER = rc("crew_locker")           # facing, half; two blocks tall; storage on the lower half
WORKBENCH = rc("retro_workbench")         # facing
STOVE = rc("galley_stove")                # facing, lit
SINK = rc("lab_sink")                     # facing
TAPE = rc("tape_archive")                 # facing
STATION_DOOR = rc("station_door")         # vanilla door properties, opens by hand
AIRLOCK_DOOR = rc("airlock_door")         # vanilla door properties, opens by hand
P_LIFTOFF, P_VESPER, P_SPACE_POP, P_SUIT_CHECK, P_HOMESTEAD, P_FREEDOM = (
    rc("poster_" + n) for n in ("liftoff", "vesper", "space_pop", "suit_check", "homestead", "freedom"))
# Venusian artifacts (ruins blocks) shown in Dr. Cooper's office
V_URN = rc("venusian_urn")                # no properties
V_STELE = rc("venusian_stele")            # facing
V_GLYPH = rc("venusian_glyph_stone")      # glyph 0..3
V_SUN_DISC = rc("venusian_sun_disc")      # facing
V_ALTAR = rc("venusian_altar")            # no properties
V_PILLAR = rc("venusian_pillar")          # axis
ARTIFACTS = {V_URN, V_STELE, V_GLYPH, V_SUN_DISC, V_ALTAR, V_PILLAR}
ON_PEDESTAL = {V_URN, V_GLYPH, V_SUN_DISC}
POSTERS = (P_LIFTOFF, P_VESPER, P_SPACE_POP, P_SUIT_CHECK, P_HOMESTEAD, P_FREEDOM)

# Full opaque building cubes: what walls, floors and ceilings are made of (supports wall decor and lights).
WALL_BLOCKS = {WHITE, LGRAY, GRAY, RED, YELLOW, BLACK, CYAN_TERRA, QUARTZ, SQUARTZ, BIRCH, SPRUCE, DARK_OAK, IRON_BLOCK,
               SEA_LANTERN, ALU, TI, CREAM, TURQ, CHROME, CHECKER, HULL, STRIPED, TOWER, LAUNCH_PAD, BOOKSHELF}
# Other full cubes (sturdy faces): workstations, containers, glass.
FULL_CUBES = WALL_BLOCKS | {CARGO_CRATE, TAPE, WORKBENCH, BARREL, CRAFTING, SMITHING, CARTOGRAPHY, FLETCHING, JUKEBOX, SMOKER, FURNACE,
                            BLAST_FURNACE, GLASS, TINTED_GLASS, LBLUE_GLASS, GRATE, WINDOW, PORTHOLE,
                            REFINERY, LIQUEFIER}
WINDOWS = {WINDOW, PORTHOLE, GLASS, LBLUE_GLASS}
# Work surfaces electronics may stand on.
DESK_BLOCKS = {SQUARTZ, WHITE, IRON_BLOCK, SPRUCE, DARK_OAK, QUARTZ, ALU}
DESK_SLABS = {SQUARTZ_SLAB, SPRUCE_SLAB, DARK_OAK_SLAB, QUARTZ_SLAB}
# Items that belong on a desk/counter, never on the bare floor.
ON_DESK = {RADAR_SCOPE, RADIO, LAMP, GLOBE, BREWING, POTTED_FERN, LANTERN}
# Wall-mounted decor: facing points away from the wall, which must be a wall block.
WALL_DECOR = {CONTROL_PANEL, STAR_CHART, CLOCK, NEON, SCONCE, WALL_SIGN} | set(POSTERS)
# Hung from the ceiling: a wall block must be directly above.
CEILING_HUNG = {CEILING_LIGHT, CHANDELIER}
SEATS_FACING = {CAPTAIN_CHAIR, EGG_CHAIR, SOFA}
CONTAINERS = {CHEST, BARREL, SUPPLY_CABINET, CARGO_CRATE, CREW_LOCKER}
STORAGE_BLOCKS = {SUPPLY_CABINET, CARGO_CRATE, CREW_LOCKER}
NO_COLLISION_DECOR = {STAR_CHART, CLOCK, NEON, SCONCE, WALL_SIGN, CEILING_LIGHT} | set(POSTERS)
TALL = {CREW_LOCKER, VENDING} | set(POSTERS)
DOORS = {IRON_DOOR, BIRCH_DOOR, STATION_DOOR, AIRLOCK_DOOR}
BEDS = {bed_id(c) for c in COLORS} | {CREW_BUNK}

HORIZ = ("north", "east", "south", "west")
ALL6 = HORIZ + ("up", "down")
BOOL = ("true", "false")
DIRS = {"north": (0, -1), "south": (0, 1), "west": (-1, 0), "east": (1, 0)}
OPPOSITE = {"north": "south", "south": "north", "west": "east", "east": "west", "up": "down", "down": "up"}
RIGHT_OF = {"north": "east", "east": "south", "south": "west", "west": "north"}
CCW = {"north": "west", "west": "south", "south": "east", "east": "north"}

# Property schemas of the vanilla blocks this generator may use (1.21.11); every state is checked against them.
_V = {}
for _n in (AIR, WHITE, LGRAY, GRAY, RED, YELLOW, BLACK, CYAN_TERRA, QUARTZ, SQUARTZ, BIRCH, SPRUCE, DARK_OAK, IRON_BLOCK,
           SEA_LANTERN, GLASS, TINTED_GLASS, LBLUE_GLASS, BOOKSHELF, CRAFTING, SMITHING, CARTOGRAPHY, FLETCHING,
           CAULDRON, POTTED_FERN):
    _V[_n] = {}
for _c in COLORS:
    _V[carpet_id(_c)] = {}
    _V[bed_id(_c)] = {"facing": HORIZ, "occupied": BOOL, "part": ("head", "foot")}
for _n in (SQUARTZ_SLAB, QUARTZ_SLAB, SPRUCE_SLAB, DARK_OAK_SLAB):
    _V[_n] = {"type": ("top", "bottom", "double"), "waterlogged": BOOL}
for _n in (SQUARTZ_STAIRS, QUARTZ_STAIRS):
    _V[_n] = {"facing": HORIZ, "half": ("top", "bottom"), "waterlogged": BOOL,
              "shape": ("straight", "inner_left", "inner_right", "outer_left", "outer_right")}
for _n in (BIRCH_DOOR, IRON_DOOR):
    _V[_n] = {"facing": HORIZ, "half": ("lower", "upper"), "hinge": ("left", "right"), "open": BOOL, "powered": BOOL}
for _n in (SMOKER, FURNACE, BLAST_FURNACE):
    _V[_n] = {"facing": HORIZ, "lit": BOOL}
_V.update({
    CHEST: {"facing": HORIZ, "type": ("single", "left", "right"), "waterlogged": BOOL},
    BARREL: {"facing": ALL6, "open": BOOL},
    BUTTON: {"face": ("floor", "wall", "ceiling"), "facing": HORIZ, "powered": BOOL},
    WALL_SIGN: {"facing": HORIZ, "waterlogged": BOOL},
    STANDING_SIGN: {"rotation": tuple(str(i) for i in range(16)), "waterlogged": BOOL},
    BREWING: {"has_bottle_0": BOOL, "has_bottle_1": BOOL, "has_bottle_2": BOOL},
    LANTERN: {"hanging": BOOL, "waterlogged": BOOL},
    END_ROD: {"facing": ALL6},
    LIGHTNING_ROD: {"facing": ALL6, "powered": BOOL, "waterlogged": BOOL},
    DAYLIGHT: {"inverted": BOOL, "power": tuple(str(i) for i in range(16))},
    STONECUTTER: {"facing": HORIZ},
    JUKEBOX: {"has_record": BOOL},
    LECTERN: {"facing": HORIZ, "has_book": BOOL, "powered": BOOL},
    COMPOSTER: {"level": tuple(str(i) for i in range(9))},
    IRON_TRAPDOOR: {"facing": HORIZ, "half": ("top", "bottom"), "open": BOOL, "powered": BOOL, "waterlogged": BOOL},
})
VANILLA_PROPS = _V
# Schemas of mod blocks whose blockstate files may not be drawn yet (used when the file is missing/outdated).
_DOOR = {"facing": HORIZ, "half": ("lower", "upper"), "hinge": ("left", "right"), "open": BOOL, "powered": BOOL}
_HALF = ("lower", "upper")
MOD_SCHEMAS = {
    SUPPLY_CABINET: {"facing": HORIZ}, CARGO_CRATE: {}, CREW_LOCKER: {"facing": HORIZ, "half": _HALF},
    WORKBENCH: {"facing": HORIZ}, STOVE: {"facing": HORIZ, "lit": BOOL}, SINK: {"facing": HORIZ},
    TAPE: {"facing": HORIZ}, STATION_DOOR: _DOOR, AIRLOCK_DOOR: _DOOR,
    VENDING: {"facing": HORIZ, "lit": BOOL, "half": _HALF},
    CREW_BUNK: {"facing": HORIZ, "part": ("foot", "head")},
}
for _p in POSTERS:
    MOD_SCHEMAS[_p] = {"facing": HORIZ, "half": _HALF}

# ----------------------------------------------------------------------------
# Geometry
# ----------------------------------------------------------------------------
F = 4                # ring / lobby floor level (solid); rooms are air at F+1 .. F+4
CEIL = F + 5         # ring ceiling
ROOF = CEIL + 1      # ring roof (solar mirrors)
UF = CEIL            # hub upper floor (EVA deck) = lobby ceiling
DECK = UF + 5        # docking deck = hub roof (pad blocks)
HUB_IN = 8           # hub interior half size (17 x 17)
CORR_IN, CORR_OUT = 24, 26       # ring corridor (square loop, max-norm)
BAND_IN, BAND_OUT = 29, 36       # room band (max-norm), 8 deep
RING_IN_HULL, RING_OUT_HULL = 22, 38
CHAMFER = 64         # |x| + |z| beyond this is outside the ring (chamfered corners -> octagonal outline)
CHAMFER_IN = CHAMFER - 2
FAIRING = 2 * RING_IN_HULL - 8   # courtyard corners filled where |x| + |z| >= this (octagonal courtyard)
ARRIVAL = (-7, UF + 1, 6)        # feet cell at the foot of the airlock stairs, in the EVA prep room


def mnorm(x, z):
    return max(abs(x), abs(z))


# ----------------------------------------------------------------------------
# Zone styles: one consistent material set per kind of space
# ----------------------------------------------------------------------------
# walls = (dado h0, h1, h2, cornice h3); a cornice of chrome runs along the wall.
STYLES = {
    "corridor": dict(floor=LGRAY, walls=(TURQ, HULL, HULL, CHROME), ceil=HULL),
    "lobby":    dict(floor=SQUARTZ, walls=(TURQ, HULL, HULL, CHROME), ceil=HULL),
    "command":  dict(floor=CYAN_TERRA, walls=(TURQ, HULL, HULL, CHROME), ceil=HULL),
    "living":   dict(floor=BIRCH, walls=(DARK_OAK, CREAM, CREAM, CHROME), ceil=CREAM),
    "mess":     dict(floor=CHECKER, walls=(RED, CREAM, CREAM, CHROME), ceil=WHITE),
    "medical":  dict(floor=WHITE, walls=(TURQ, WHITE, WHITE, CHROME), ceil=WHITE),
    "wash":     dict(floor=CHECKER, walls=(TURQ, TURQ, WHITE, CHROME), ceil=WHITE),
    "tech":     dict(floor=GRATE, walls=(ALU, HULL, HULL, CHROME), ceil=ALU),
    "hydro":    dict(floor=GRATE, walls=(TURQ, HULL, HULL, CHROME), ceil=HULL),
    "reactor":  dict(floor=STRIPED, walls=(STRIPED, ALU, ALU, CHROME), ceil=ALU),
    "store":    dict(floor=ALU, walls=(ALU, HULL, HULL, ALU), ceil=ALU),
    "eva":      dict(floor=ALU, walls=(STRIPED, HULL, HULL, CHROME), ceil=HULL),
    "airlock":  dict(floor=STRIPED, walls=(HULL, HULL, HULL, HULL), ceil=HULL),
    "shop":     dict(floor=WHITE, walls=(TURQ, CREAM, CREAM, CHROME), ceil=WHITE),
}


class Region:
    """A pressurised space (room, corridor, spoke ...)."""

    def __init__(self, key, kind, zone, floor_y, label="", priority=1):
        self.key, self.kind, self.zone, self.floor_y, self.label, self.priority = key, kind, zone, floor_y, label, priority
        self.cells = set()


LOCAL_OFF = {"back": (0, 1), "front": (0, -1), "right": (1, 0), "left": (-1, 0)}
LOCAL_OPP = {"back": "front", "front": "back", "left": "right", "right": "left"}


class Room(Region):
    """A rectangular room with a local frame: u runs left->right along the door wall as seen from the doorway,
    v runs from the door wall (v = 0) towards the far wall (v = V - 1), h is the height above the floor."""

    def __init__(self, st, key, kind, zone, label, sign, rect, back, floor_y=F, height=4, doors=(), priority=2):
        super().__init__(key, kind, zone, floor_y, label, priority)
        self.st, self.sign_lines, self.height = st, sign, height
        x0, z0, x1, z1 = rect
        self.rect = rect
        self.back, self.right = back, RIGHT_OF[back]
        bx, bz = DIRS[back]
        rx, rz = DIRS[self.right]
        self.bx, self.bz, self.rx, self.rz = bx, bz, rx, rz
        self.ox = (x0 if bx > 0 else x1) if bx else (x0 if rx > 0 else x1)
        self.oz = (z0 if bz > 0 else z1) if bz else (z0 if rz > 0 else z1)
        self.U = (x1 - x0 + 1) if rx else (z1 - z0 + 1)
        self.V = (x1 - x0 + 1) if bx else (z1 - z0 + 1)
        self.doors = list(doors)
        self.items = []          # (u, v, h, name) placed by the furnishing code, for the report

    # -- frame ------------------------------------------------------------
    def at(self, u, v, h=0):
        return (self.ox + u * self.rx + v * self.bx, self.floor_y + 1 + h, self.oz + u * self.rz + v * self.bz)

    def wdir(self, d):
        return {"back": self.back, "front": OPPOSITE[self.back], "right": self.right, "left": OPPOSITE[self.right]}[d]

    def step(self, u, v, d, n=1):
        du, dv = LOCAL_OFF[d]
        return u + du * n, v + dv * n

    def inside(self, u, v):
        return 0 <= u < self.U and 0 <= v < self.V and self.at(u, v) in self.cells

    def free(self, u, v, h=0):
        c = self.at(u, v, h)
        return c in self.cells and self.st.get(c) == AIR

    # -- placing ------------------------------------------------------------
    def put(self, u, v, h, name, props=None, nbt=None):
        c = self.at(u, v, h)
        if not self.free(u, v, h):
            self.st.error(f"{self.key}: cannot place {name} at local {(u, v, h)} {c}: {self.st.get(c)}")
            return False
        self.st.put(c, name, props, nbt)
        self.items.append((u, v, h, name))
        return True

    def fput(self, u, v, h, name, facing, lit=None, **extra):
        props = {"facing": self.wdir(facing)}
        if lit is not None:
            props["lit"] = "true" if lit else "false"
        props.update(extra)
        return self.put(u, v, h, name, props)

    def block(self, u, v, h, name, props=None):
        return self.put(u, v, h, name, props)

    def desk(self, u, v, top=None, facing="front", mat=SQUARTZ, lit=True):
        """A work surface with an optional item standing on it."""
        props = {"type": "top", "waterlogged": "false"} if mat in DESK_SLABS else None
        self.put(u, v, 0, mat, props)
        if top is not None:
            self.item(u, v, 1, top, facing, lit)

    def item(self, u, v, h, name, facing="front", lit=True):
        if name in (BREWING,):
            return self.put(u, v, h, name, {"has_bottle_0": "true", "has_bottle_1": "false", "has_bottle_2": "true"})
        if name == POTTED_FERN:
            return self.put(u, v, h, name)
        if name == LANTERN:
            return self.put(u, v, h, name, {"hanging": "false", "waterlogged": "false"})
        if name in (GLOBE, TELESCOPE):
            return self.fput(u, v, h, name, facing)
        return self.fput(u, v, h, name, facing, lit=lit)

    def wall(self, u, v, h, name, wall, lit=True):
        """Wall decor hung on the wall in local direction `wall` from the cell (u, v, h)."""
        du, dv = LOCAL_OFF[wall]
        support = self.at(u + du, v + dv, h)
        if self.st.get(support) not in WALL_BLOCKS:
            self.st.error(f"{self.key}: {name} at local {(u, v, h)} has no wall {wall} ({self.st.get(support)})")
            return False
        if name in (CLOCK,):
            return self.fput(u, v, h, name, LOCAL_OPP[wall])
        return self.fput(u, v, h, name, LOCAL_OPP[wall], lit=lit)

    def seat(self, u, v, name, facing):
        return self.fput(u, v, 0, name, facing)

    def stool(self, u, v):
        return self.put(u, v, 0, STOOL)

    def bed(self, u, v, toward, color="white"):
        """Bed with its foot at (u, v) and its head one step `toward`."""
        hu, hv = self.step(u, v, toward)
        f = self.wdir(toward)
        ok = self.put(u, v, 0, bed_id(color), {"facing": f, "part": "foot", "occupied": "false"})
        ok &= self.put(hu, hv, 0, bed_id(color), {"facing": f, "part": "head", "occupied": "false"})
        return ok

    def bunk(self, u, v, toward_head):
        """Two-block crew bunk: foot at (u, v), head one step `toward_head` (against a wall).  The block's
        facing is the direction the foot end faces, i.e. away from the head."""
        hu, hv = self.step(u, v, toward_head)
        f = self.wdir(LOCAL_OPP[toward_head])
        ok = self.put(u, v, 0, CREW_BUNK, {"facing": f, "part": "foot"})
        ok &= self.put(hu, hv, 0, CREW_BUNK, {"facing": f, "part": "head"})
        return ok

    def tall(self, u, v, h, name, facing, lit=None, nbt=None):
        """Two-block-tall furniture: lower half at h, upper half at h + 1 (same facing / lit)."""
        props = {"facing": self.wdir(facing)}
        if lit is not None:
            props["lit"] = "true" if lit else "false"
        if not (self.free(u, v, h) and self.free(u, v, h + 1)):
            self.st.error(f"{self.key}: no room for two-tall {name} at local {(u, v, h)}")
            return False
        self.put(u, v, h, name, dict(props, half="lower"), nbt)
        self.put(u, v, h + 1, name, dict(props, half="upper"))
        return True

    def locker(self, u, v, facing="front", items=()):
        """Crew locker (two blocks tall), one per crew member."""
        return self.tall(u, v, 0, CREW_LOCKER, facing, nbt=storage_nbt(items))

    def vending(self, u, v, facing, lit):
        return self.tall(u, v, 0, VENDING, facing, lit=lit)

    def poster(self, u, v, h, name, wall):
        """Two-block-tall wall poster; both halves need the wall behind them."""
        du, dv = LOCAL_OFF[wall]
        for hh in (h, h + 1):
            if self.st.get(self.at(u + du, v + dv, hh)) not in WALL_BLOCKS:
                self.st.error(f"{self.key}: poster {name} at local {(u, v, hh)} has no wall {wall}")
                return False
        return self.tall(u, v, h, name, LOCAL_OPP[wall])

    def chest(self, u, v, h, facing, items=()):
        """Supply cabinet along a wall."""
        return self.put(u, v, h, SUPPLY_CABINET, {"facing": self.wdir(facing)}, storage_nbt(items))

    def cabinet(self, u, v, h, facing, items=()):
        return self.chest(u, v, h, facing, items)

    def crate(self, u, v, h, items=()):
        return self.put(u, v, h, CARGO_CRATE, None, storage_nbt(items))

    def light(self, u, v, name=CEILING_LIGHT):
        h = self.height - 1
        return self.put(u, v, h, name, {"lit": "true"})

    def lights_grid(self, us, vs, name=CEILING_LIGHT):
        for u in us:
            for v in vs:
                if self.free(u, v, self.height - 1):
                    self.light(u, v, name)

    def carpet(self, color, us, vs):
        for u in us:
            for v in vs:
                if self.free(u, v, 0) and self.st.get(self.st.below(self.at(u, v))) in FULL_CUBES:
                    self.put(u, v, 0, carpet_id(color))

    def trim(self, u, v, h, axis_local):
        """Chrome trim block used as rail / duct; axis given in local terms ('u', 'v' or 'y')."""
        if axis_local == "y":
            axis = "y"
        else:
            d = self.right if axis_local == "u" else self.back
            axis = "x" if DIRS[d][0] else "z"
        return self.put(u, v, h, CHROME, {"axis": axis})

    def window(self, us, hs, side="back", block=WINDOW):
        """Glazes the hull behind the room boundary on `side` (all hull layers out to space)."""
        for u in us:
            for h in hs:
                self.st.glaze(self, u, h, side, block)

    def sign(self, u, v, h, wall, lines):
        du, dv = LOCAL_OFF[wall]
        return self.st.wall_sign(self.at(u, v, h), self.wdir(LOCAL_OPP[wall]), lines, self.at(u + du, v + dv, h))


def storage_nbt(items):
    """Block entity of the station storage blocks (27 slots)."""
    assert len(items) <= 27
    stacks = List([Compound({"Slot": Byte(i), "id": Str(item), "count": Int(n)}) for i, (item, n) in enumerate(items)],
                  TAG_COMPOUND)
    return Compound({"id": Str("retrocosmos:storage"), "Items": stacks})


chest_nbt = storage_nbt


def sign_nbt(lines):
    lines = list(lines) + [""] * (4 - len(lines))
    return Compound({
        "id": Str("minecraft:sign"),
        "front_text": Compound({"messages": List([Str(s) for s in lines[:4]], TAG_STRING),
                                "has_glowing_text": Byte(1), "color": Str("black")}),
        "back_text": Compound({"messages": List([Str("")] * 4, TAG_STRING),
                               "has_glowing_text": Byte(0), "color": Str("black")}),
        "is_waxed": Byte(1),
    })


# ----------------------------------------------------------------------------
# Builder
# ----------------------------------------------------------------------------
class Station:
    def __init__(self):
        self.blocks = {}       # (x, y, z) -> (name, props, nbt)
        self.inner = set()     # pressurised cells
        self.region = {}       # pressurised cell -> region key
        self.regions = {}
        self.rooms = {}
        self.lanes = set()     # corridor cells that must stay clear at walking height
        self.errors = []
        self.signs = []

    # -- primitives -------------------------------------------------------
    def error(self, msg):
        self.errors.append(msg)

    def get(self, c):
        b = self.blocks.get(c)
        return b[0] if b else None

    def props(self, c):
        b = self.blocks.get(c)
        return b[1] if b else {}

    def put(self, c, name, props=None, nbt=None):
        self.blocks[c] = (name, dict(props or {}), nbt)

    def seal(self, c, name, props=None):
        """Structural block placed inside a former interior cell (stair fill etc.)."""
        self.put(c, name, props)
        self.inner.discard(c)
        key = self.region.pop(c, None)
        if key:
            self.regions[key].cells.discard(c)

    def mass(self, c):
        if c not in self.blocks:
            self.blocks[c] = (STRUCT, {}, None)

    def add_region(self, reg):
        self.regions[reg.key] = reg
        if isinstance(reg, Room):
            self.rooms[reg.key] = reg
        return reg

    def carve(self, c, key):
        self.blocks[c] = (AIR, {}, None)
        self.inner.add(c)
        old = self.region.get(c)
        if old and old != key:
            self.regions[old].cells.discard(c)
        self.region[c] = key
        self.regions[key].cells.add(c)

    @staticmethod
    def below(c):
        return (c[0], c[1] - 1, c[2])

    @staticmethod
    def above(c):
        return (c[0], c[1] + 1, c[2])

    def is_wall(self, c):
        return self.get(c) in WALL_BLOCKS

    def is_full(self, c):
        return self.get(c) in FULL_CUBES

    def wall_sign(self, c, facing, lines, support=None):
        dx, dz = DIRS[facing]
        support = support or (c[0] - dx, c[1], c[2] - dz)
        if self.get(support) not in WALL_BLOCKS:
            self.error(f"sign {lines} at {c} has no wall ({self.get(support)})")
            return False
        if self.get(c) not in (AIR, None):
            self.error(f"sign {lines} at {c}: cell taken by {self.get(c)}")
            return False
        self.put(c, WALL_SIGN, {"facing": facing, "waterlogged": "false"}, sign_nbt(lines))
        self.signs.append((c, [s for s in lines if s]))
        return True

    def standing_sign(self, c, facing, lines):
        rot = {"south": 0, "west": 4, "north": 8, "east": 12}[facing]
        if self.get(self.below(c)) not in FULL_CUBES:
            self.error(f"standing sign at {c} has nothing below")
        self.put(c, STANDING_SIGN, {"rotation": str(rot), "waterlogged": "false"}, sign_nbt(lines))
        self.signs.append((c, [s for s in lines if s]))

    def door(self, c, facing, hinge="left", name=STATION_DOOR):
        """Hand-opened station door (lower + upper half) on a solid floor."""
        if self.get(self.below(c)) not in FULL_CUBES:
            self.error(f"door at {c} has no floor")
        base = {"facing": facing, "hinge": hinge, "open": "false", "powered": "false"}
        self.put(c, name, dict(base, half="lower"))
        self.put(self.above(c), name, dict(base, half="upper"))

    def wood_door(self, c, facing, hinge="left"):
        self.door(c, facing, hinge, STATION_DOOR)

    def airlock_door(self, c, facing, hinge="left"):
        self.door(c, facing, hinge, AIRLOCK_DOOR)

    def button(self, c, facing):
        dx, dz = DIRS[facing]
        if self.get((c[0] - dx, c[1], c[2] - dz)) not in WALL_BLOCKS:
            self.error(f"button at {c} has no wall")
        self.put(c, BUTTON, {"face": "wall", "facing": facing, "powered": "false"})

    def stairs(self, c, facing, name=QUARTZ_STAIRS):
        self.put(c, name, {"facing": facing, "half": "bottom", "shape": "straight", "waterlogged": "false"})

    def glaze(self, room, u, h, side, block):
        """Replaces the hull cells behind room cell (u, edge, h) in direction `side` by `block` out to space."""
        if side in ("back", "front"):
            v = room.V - 1 if side == "back" else 0
            uu, vv = u, v
        else:
            uu = room.U - 1 if side == "right" else 0
            vv = u        # for side walls the first coordinate is v
        # walk inwards from the far edge until we are inside the room (chamfered corners)
        while not room.inside(uu, vv):
            nu, nv = room.step(uu, vv, LOCAL_OPP[side])
            if not (0 <= nu < room.U and 0 <= nv < room.V):
                return
            uu, vv = nu, nv
        du, dv = LOCAL_OFF[side]
        x, y, z = room.at(uu, vv, h)
        dx, dz = (du * room.rx + dv * room.bx), (du * room.rz + dv * room.bz)
        path = []
        cx, cz = x + dx, z + dz
        for _ in range(4):
            c = (cx, y, cz)
            if c in self.inner:
                return            # a partition, not the hull: no window
            if self.get(c) is None or (self.get(c) == AIR and c not in self.inner):
                break
            path.append(c)
            cx, cz = cx + dx, cz + dz
        else:
            return
        if not path:
            return
        for c in path:
            self.put(c, block)

    # ---------------------------------------------------------------------
    # Massing and carving
    # ---------------------------------------------------------------------
    def build_mass(self):
        # ring: square annulus with chamfered corners
        for x in range(-RING_OUT_HULL, RING_OUT_HULL + 1):
            for z in range(-RING_OUT_HULL, RING_OUT_HULL + 1):
                m = mnorm(x, z)
                s = abs(x) + abs(z)
                if RING_IN_HULL <= m <= RING_OUT_HULL and s <= CHAMFER:
                    edge = m in (RING_IN_HULL, RING_OUT_HULL) or s == CHAMFER
                    for y in range(F - 1, ROOF + 1):
                        if edge and y in (F - 1, ROOF):
                            continue          # rounded edges of the ring's cross-section
                        self.mass((x, y, z))
                elif m < RING_IN_HULL and s >= FAIRING:
                    for y in range(F, ROOF):  # fairings fill the courtyard corners
                        self.mass((x, y, z))
        # hub: octagonal drum
        for x in range(-10, 11):
            for z in range(-10, 11):
                if abs(x) + abs(z) <= 17:
                    for y in range(F - 1, DECK + 1):
                        self.mass((x, y, z))
        # spokes
        for d in HORIZ:
            for t in range(9, RING_IN_HULL + 2):
                for w in range(-3, 4):
                    x, z = self.spoke_xz(d, t, w)
                    for y in range(F - 1, ROOF + 1):
                        if abs(w) == 3 and y in (F - 1, ROOF):
                            continue          # octagonal tube profile
                        self.mass((x, y, z))

    @staticmethod
    def spoke_xz(d, t, w):
        dx, dz = DIRS[d]
        return t * dx - w * dz, t * dz + w * dx

    def carve_spaces(self):
        corr = self.add_region(Region("corridor", "corridor", "corridor", F, "Ring corridor"))
        for x in range(-CORR_OUT, CORR_OUT + 1):
            for z in range(-CORR_OUT, CORR_OUT + 1):
                if CORR_IN <= mnorm(x, z) <= CORR_OUT:
                    for y in range(F + 1, F + 5):
                        self.carve((x, y, z), corr.key)
        # spokes: hub lobby <-> ring corridor
        for d in HORIZ:
            reg = self.add_region(Region("spoke_" + d, "spoke", "corridor", F, f"{d.title()} spoke"))
            for t in range(HUB_IN + 1, RING_IN_HULL + 2):
                end = t in (HUB_IN + 1, HUB_IN + 2, RING_IN_HULL, RING_IN_HULL + 1)
                for w in (-1, 0, 1):
                    x, z = self.spoke_xz(d, t, w)
                    for y in range(F + 1, F + (4 if end else 5)):
                        self.carve((x, y, z), reg.key)
        for room in self.rooms.values():
            for u in range(room.U):
                for v in range(room.V):
                    x, _, z = room.at(u, v)
                    if abs(x) + abs(z) > CHAMFER_IN:
                        continue
                    for h in range(room.height):
                        self.carve(room.at(u, v, h), room.key)
        for room in self.rooms.values():
            for (u0, width, kind) in room.doors:
                for u in range(u0, u0 + width):
                    outside = room.at(u, -3)
                    if self.region.get(outside) is None:
                        self.error(f"{room.key}: door at u={u} does not reach a corridor ({outside})")
                        continue
                    for h in (0, 1):
                        self.carve(room.at(u, -1, h), room.key)
                        self.carve(room.at(u, -2, h), self.region[outside])

    # ---------------------------------------------------------------------
    # Painting: every structure cell gets the material of the space it faces
    # ---------------------------------------------------------------------
    def paint(self):
        for c, (name, _, _) in list(self.blocks.items()):
            if name != STRUCT:
                continue
            x, y, z = c
            up, down = (x, y + 1, z), (x, y - 1, z)
            if up in self.inner:
                reg = self.regions[self.region[up]]
                self.put(c, *self.floor_block(reg, c))
                continue
            if y == DECK and mnorm(x, z) <= 10:
                self.put(c, self.deck_block(x, z))      # the docking deck is the hub roof
                continue
            if down in self.inner:
                reg = self.regions[self.region[down]]
                self.put(c, STYLES[reg.zone]["ceil"])
                continue
            hn = [(x + dx, y, z + dz) for dx, dz in DIRS.values() if (x + dx, y, z + dz) in self.inner]
            if hn:
                keys = sorted({self.region[n] for n in hn}, key=lambda k: (-self.regions[k].priority, k))
                reg = self.regions[keys[0]]
                h = max(0, min(3, y - reg.floor_y - 1))
                name = STYLES[reg.zone]["walls"][h]
                props = {}
                if name == CHROME:
                    mine = [n for n in hn if self.region[n] == reg.key]
                    props = {"axis": "x" if any(n[2] != z for n in mine) else "z"}
                self.put(c, name, props)
                continue
            self.put(c, *self.exterior_block(c))
        # floor grates glow: sea lanterns under them
        for c, (name, _, _) in list(self.blocks.items()):
            if name == GRATE and c[1] == F and mnorm(c[0], c[2]) >= RING_IN_HULL:
                self.put(self.below(c), SEA_LANTERN)

    def floor_block(self, reg, c):
        x, _, z = c
        zone = STYLES[reg.zone]
        if reg.kind == "corridor":
            return (RED if mnorm(x, z) == 25 else LGRAY), {}
        if reg.kind == "spoke":
            return (RED if (x == 0 or z == 0) else LGRAY), {}
        if reg.kind == "lobby":
            r = math.hypot(x, z)
            if 5.5 < r <= 6.5:
                return RED, {}
            if (x == 0 or z == 0) and r > 6.5:
                return RED, {}
            return SQUARTZ, {}
        return zone["floor"], {}

    def outside(self, c):
        return self.get(c) is None or (self.get(c) == AIR and c not in self.inner)

    def exterior_block(self, c):
        x, y, z = c
        nb = [(x + 1, y, z), (x - 1, y, z), (x, y, z + 1), (x, y, z - 1)]
        side = any(self.outside(n) for n in nb)
        top = self.outside((x, y + 1, z))
        bottom = self.outside((x, y - 1, z))
        m = mnorm(x, z)
        if not (side or top or bottom):
            return HULL, {}
        if m >= RING_IN_HULL and y <= ROOF:                    # ring
            corner = abs(x) + abs(z) >= CHAMFER - 1
            if top:
                along = min(abs(x), abs(z))
                if m >= RING_OUT_HULL - 1 or corner:
                    return CHROME, {"axis": "x" if abs(z) >= abs(x) else "z"}
                if BAND_IN + 1 <= m <= BAND_OUT - 1:
                    if along <= 1 or abs(abs(x) - abs(z)) <= 1:
                        return STRIPED, {}
                    return DAYLIGHT, {"inverted": "false", "power": "0"}
                if m in (BAND_IN, BAND_OUT):
                    return ALU, {}
                if m == 25:
                    return CHROME, {"axis": "x" if abs(z) >= abs(x) else "z"}
                return HULL, {}
            if bottom and not side:
                return (TI if m >= RING_OUT_HULL - 1 else HULL), {}
            if corner:
                return STRIPED, {}
            if y == F - 1:
                return TI, {}
            if y == F + 4:
                return RED, {}
            return HULL, {}
        if m <= 10 and y <= DECK:                             # hub drum
            if top and y == DECK:
                return self.deck_block(x, z), {}
            if bottom and not side:
                return ALU, {}
            if y == F - 1:
                return TI, {}
            if y in (F + 4, DECK - 1):
                return RED, {}
            if y == DECK:
                return STRIPED, {}
            return HULL, {}
        if m < RING_IN_HULL and abs(x) + abs(z) >= FAIRING:   # courtyard fairings
            if top:
                return ALU, {}
            return (RED if y == F + 4 else HULL), {}
        if y > DECK:                                          # airlock hut
            if top:
                return CHROME, {"axis": "x"}
            return HULL, {}
        # spokes
        t = m
        if top:
            return (CHROME, {"axis": "z" if abs(x) <= 3 else "x"}) if (x == 0 or z == 0) else (HULL, {})
        if t in (11, 12, 20, 21):
            return STRIPED, {}
        if y == F - 1:
            return TI, {}
        if y == F + 4:
            return RED, {}
        return HULL, {}

    @staticmethod
    def deck_block(x, z):
        """Docking deck markings: hazard-striped edge, red landing circle, red approach lines."""
        r = math.hypot(x, z)
        if mnorm(x, z) >= 10 or abs(x) + abs(z) >= 17:
            return YELLOW if ((x + z) // 2) % 2 else BLACK
        if 3.5 < r <= 4.5:
            return RED
        if (x == 0 or z == 0) and r > 5.5:
            return RED
        return HULL


# ----------------------------------------------------------------------------
# Room list
# ----------------------------------------------------------------------------
FUEL = rc("rocket_fuel_canister")
LOX = rc("liquid_oxygen_canister")
EMPTY_CAN = rc("empty_fuel_canister")

# (key, kind, zone, label, sign lines, interior rect x0 z0 x1 z1, direction from the doorway into the room, doors)
# Doors: (u, width, kind) on the corridor wall, kind = open | birch.
BAND_ROOMS = [
    # DECK A - command (north band, corridor to the south)
    ("observation", "observation", "living", "Observation lounge", ["DECK A", "OBSERVATION", "LOUNGE", ""],
     (-36, -36, -21, -29), "north", [(12, 3, "open")]),
    ("commander", "commander", "living", "Commander's cabin", ["DECK A", "COMMANDER", "QUARTERS", ""],
     (-18, -36, -11, -29), "north", [(4, 1, "birch")]),
    ("bridge", "bridge", "command", "Bridge / Command center", ["- DECK A -", "BRIDGE", "COMMAND CENTER", ""],
     (-8, -36, 8, -29), "north", [(7, 3, "open")]),
    ("radio", "radio", "command", "Radio room", ["DECK A", "RADIO ROOM", "COMMUNICATIONS", ""],
     (11, -36, 26, -29), "north", [(7, 3, "open")]),
    # DECK B - science & engineering (east band, corridor to the west)
    ("machine_shop", "workshop", "tech", "Machine shop", ["DECK B", "MACHINE SHOP", "ENGINEERING", ""],
     (29, -36, 36, -21), "east", [(12, 3, "open")]),
    ("archaeology", "archaeology", "living", "Xeno-archaeology office (Dr. Cooper)",
     ["XENO-", "ARCHAEOLOGY", "DR. H. COOPER", "DECK B"], (29, -18, 36, -11), "east", [(4, 1, "open")]),
    ("laboratory", "laboratory", "tech", "Laboratory", ["- DECK B -", "LABORATORY", "PROPELLANT & AIR", ""],
     (29, -8, 36, 8), "east", [(7, 3, "open")]),
    ("reactor", "reactor", "reactor", "Reactor / power room", ["DECK B", "REACTOR ROOM", "AUTHORIZED", "PERSONNEL ONLY"],
     (29, 11, 36, 26), "east", [(7, 3, "open")]),
    # DECK C - life support (south band, corridor to the north)
    ("hydroponics", "hydroponics", "hydro", "Hydroponics bay", ["DECK C", "HYDROPONICS", "BAY", ""],
     (25, 29, 36, 36), "south", [(10, 2, "open")]),
    ("showroom", "showroom", "shop", "Atomic Home showroom (Betty Palmer)",
     ["ATOMIC HOME", "FURNITURE OF", "TOMORROW", "DECK C"], (11, 29, 22, 36), "south", [(5, 2, "open")]),
    ("mess", "mess", "mess", "Mess hall & galley", ["- DECK C -", "MESS HALL", "& GALLEY", ""],
     (-8, 29, 8, 36), "south", [(7, 3, "open")]),
    ("medical", "medical", "medical", "Medical bay", ["DECK C", "MEDICAL BAY", "SICKBAY", ""],
     (-26, 29, -11, 36), "south", [(7, 3, "open")]),
    # DECK D - habitation (west band, corridor to the east)
    ("recreation", "recreation", "living", "Recreation room", ["DECK D", "RECREATION", "LIBRARY & GAMES", ""],
     (-36, 21, -29, 36), "west", [(12, 3, "open")]),
    ("washroom", "washroom", "wash", "Washroom", ["DECK D", "WASHROOM", "SHOWERS", ""],
     (-36, 11, -29, 18), "west", [(4, 1, "birch")]),
]
CABIN_Z = [(4, 8), (-2, 2), (-8, -4), (-14, -10), (-20, -16), (-26, -22)]
for _i, (_z0, _z1) in enumerate(CABIN_Z):
    BAND_ROOMS.append((f"cabin_{_i + 1}", "cabin", "living", f"Crew cabin {_i + 1}",
                       ["DECK D", f"CREW CABIN {_i + 1}", "2 BERTHS", ""], (-36, _z0, -29, _z1), "west", [(2, 1, "birch")]))

# What each kind of room must contain (checked).  "locker", "poster" and "vending" count whole two-tall pieces.
REQUIRED = {
    "bridge": {CONSOLE: 1, CAPTAIN_CHAIR: 1, CONTROL_PANEL: 4, RADAR_SCOPE: 2, COMPUTER: 6, STAR_CHART: 1, WINDOW: 10},
    "cabin": {"bed": 2, "locker": 2, LAMP: 1, STOOL: 1, PORTHOLE: 1, "wall_clock_or_chart": 1, "carpet": 1, "poster": 1},
    "commander": {"bed": 1, GLOBE: 1, CAPTAIN_CHAIR: 1, "locker": 1, PORTHOLE: 1, TAPE: 2},
    "mess": {"seats": 12, STOVE: 2, SINK: 1, "vending": 2, SUPPLY_CABINET: 1, RADIO: 1, TV: 1, EGG_CHAIR: 2,
             "poster": 2},
    "washroom": {SINK: 2, STATION_DOOR: 2, TINTED_GLASS: 1, "locker": 2},
    "medical": {"bed": 2, BREWING: 1, CONTROL_PANEL: 1, SUPPLY_CABINET: 2, SINK: 1},
    "laboratory": {REFINERY: 1, LIQUEFIER: 1, CHROME: 4, BREWING: 1, SINK: 1, COMPUTER: 4, O2_RACK: 1},
    "hydroponics": {PLANTER: 12, CEILING_LIGHT: 5, COMPOSTER: 1},
    "showroom": {SOFA: 4, TABLE: 2, FLOOR_LAMP: 1, CREW_BUNK: 2, "vending": 1, STOVE: 1, SINK: 1, CONSOLE: 1, TAPE: 3,
                 "poster": 3, GLASS: 8, CHANDELIER: 1},
    "reactor": {REACTOR: 2, CHROME: 8, CONTROL_PANEL: 2, STRIPED: 1, "locker": 3},
    "observation": {TELESCOPE: 1, GLOBE: 1, EGG_CHAIR: 3, WINDOW: 10},
    "storage": {CARGO_CRATE: 8},
    "archaeology": {TAPE: 2, GLOBE: 1, STAR_CHART: 1, CARGO_CRATE: 1, CAPTAIN_CHAIR: 1, "artifact": 5, GLASS: 6,
                    CARTOGRAPHY: 1, LECTERN: 1},
    "workshop": {WORKBENCH: 1, SMITHING: 1, STONECUTTER: 1, STOVE: 1, SUPPLY_CABINET: 2},
    "radio": {RADIO: 3, CONTROL_PANEL: 3, COMPUTER: 3, TAPE: 2},
    "recreation": {TAPE: 6, JUKEBOX: 1, TABLE: 2, SOFA: 2, "poster": 1},
    "eva": {O2_RACK: 4, "locker": 13, SOFA: 2, P_SUIT_CHECK: 2},
    "supply": {CARGO_CRATE: 6},
    "lobby": {SOFA: 2, CONTROL_PANEL: 1, P_FREEDOM: 2, P_VESPER: 2},
}
# Beds, planters and the like only where they belong.
ALLOWED_KINDS = {
    "bed": {"cabin", "commander", "medical", "showroom"},
    PLANTER: {"hydroponics"},
    POTTED_FERN: {"hydroponics"},
    REACTOR: {"reactor"},
}
CABIN_POSTERS = (P_LIFTOFF, P_HOMESTEAD, P_SPACE_POP, P_VESPER, P_FREEDOM, P_LIFTOFF)


class Furnisher:
    """Room furnishing, one method per kind of room, all in room-local coordinates.
    Lighting: ceiling lights roughly every 4-5 blocks; screens, radios and machines mostly switched off."""

    def __init__(self, st):
        self.st = st

    # ------------------------------------------------------------- DECK A
    def bridge(self, r):
        # windscreen above the instrument consoles, full height behind the commander's console
        r.window(range(1, 16), (2, 3), "back")
        r.window(range(7, 10), (1,), "back")
        r.fput(8, 7, 0, CONSOLE, "front")
        r.seat(8, 6, CAPTAIN_CHAIR, "back")
        # two tiers of operator stations: window row (panels on the hull under the windscreen) and a second row
        # whose panels hang on a low console backboard; each station = desk + panel, scope or radio, stool.
        # Aisles run behind both rows (v = 5 and v = 1).
        for side in (range(2, 7), range(10, 15)):
            for i, u in enumerate(side):
                panel = i % 2 == 0
                gear = (RADAR_SCOPE, RADIO)[(i // 2 + (u > 8)) % 2]
                self.st.seal(r.at(u, 4, 0), SQUARTZ)
                self.st.seal(r.at(u, 4, 1), SQUARTZ)
                for v in (7, 3):
                    r.desk(u, v)
                    if panel:
                        r.wall(u, v, 1, CONTROL_PANEL, "back", lit=(v == 7 or i == 2))
                        r.stool(u, v - 1)
                    else:
                        r.item(u, v, 1, gear, lit=(gear == RADAR_SCOPE and v == 7))
        for v in range(1, 7):
            r.fput(0, v, 0, COMPUTER, "right", lit=v % 2 == 1)
            r.fput(16, v, 0, COMPUTER, "left", lit=v % 2 == 0)
        r.wall(3, 0, 2, STAR_CHART, "front")
        r.wall(13, 0, 2, STAR_CHART, "front", lit=False)
        r.wall(8, 0, 2, CLOCK, "front")
        r.carpet("blue", [8], range(0, 6))
        r.lights_grid((4, 12), (1, 5))
        r.light(8, 2)

    def commander(self, r):
        r.window([2, 5], [1], "back", PORTHOLE)
        r.bed(0, 6, "back", "red")                 # berth along the left wall, head at the hull
        r.desk(1, 7, LAMP, mat=DARK_OAK)            # nightstand with reading lamp
        r.desk(4, 7, GLOBE, mat=DARK_OAK)           # writing desk under the porthole
        r.desk(5, 7, RADIO, mat=DARK_OAK, lit=False)
        r.seat(4, 6, CAPTAIN_CHAIR, "back")
        for v in (3, 4, 5):                         # tape / document archive
            r.fput(7, v, 0, TAPE, "left")
            r.fput(7, v, 1, TAPE, "left")
        r.locker(0, 0, "right", [("minecraft:paper", 8), ("minecraft:book", 2)])
        r.seat(2, 3, SOFA, "right")                 # sitting corner
        r.fput(3, 3, 0, TABLE, "front")
        r.seat(4, 3, EGG_CHAIR, "left")
        r.wall(0, 4, 2, STAR_CHART, "left", lit=False)
        r.wall(4, 0, 2, CLOCK, "front")
        r.wall(7, 6, 2, SCONCE, "right")
        r.carpet("red", range(1, 7), range(1, 6))
        r.light(4, 4, CHANDELIER)

    def radio(self, r):
        for k, u0 in enumerate((1, 5, 9, 13)):
            r.desk(u0, 7)
            r.wall(u0, 7, 1, CONTROL_PANEL, "back", lit=k % 2 == 0)
            r.desk(u0 + 1, 7, RADIO, lit=k % 2 == 0)
            r.stool(u0, 6)
        r.window([3, 12], [1], "back", PORTHOLE)
        for u in (7, 8):
            r.fput(u, 3, 0, COMPUTER, "front", lit=u == 7)
            r.fput(u, 4, 0, COMPUTER, "back", lit=u == 8)
        for v in range(1, 6):
            r.fput(15, v, 0, COMPUTER, "left", lit=v % 2 == 1)
        for v in (2, 3, 4):                         # log tapes on the left wall
            r.fput(0, v, 0, TAPE, "right")
        r.wall(0, 3, 2, STAR_CHART, "left")
        r.wall(8, 0, 2, CLOCK, "front")
        r.lights_grid((4, 11), (2, 5))

    # corner rooms are trapezoids: the chamfered hull runs diagonally from (3, 0) to (10, 7)
    def observation(self, r):
        r.window(range(r.U), (1, 2, 3), "back")
        r.window(range(r.V), (1, 2, 3), "left")
        r.fput(9, 5, 0, TELESCOPE, "back")
        for u, kind in ((11, "chair"), (12, "table"), (13, "chair"), (14, "table"), (15, "chair")):
            if kind == "chair":
                r.seat(u, 5, EGG_CHAIR, "back")
            else:
                r.fput(u, 5, 0, TABLE, "back")
        r.seat(6, 1, SOFA, "left")
        r.seat(7, 2, SOFA, "left")
        r.fput(5, 1, 0, TABLE, "left")
        r.trim(10, 2, 0, "y")
        r.item(10, 2, 1, GLOBE, "front")
        r.desk(15, 0, RADIO, facing="left")
        r.desk(15, 1, LAMP, facing="left", lit=False)
        r.stool(14, 1)
        r.wall(15, 3, 2, SCONCE, "right")
        r.wall(15, 7, 2, SCONCE, "right")
        r.wall(13, 0, 2, CLOCK, "front")
        r.carpet("light_blue", range(8, 16), range(3, 7))
        r.light(11, 3, CHANDELIER)
        r.light(7, 2)

    # ------------------------------------------------------------- DECK B
    def machine_shop(self, r):
        r.fput(10, 7, 0, WORKBENCH, "front")
        r.block(11, 7, 0, SMITHING)
        r.desk(12, 7, mat=IRON_BLOCK)
        r.wall(12, 7, 1, CONTROL_PANEL, "back", lit=False)
        r.stool(12, 6)
        r.fput(13, 7, 0, STONECUTTER, "front")
        r.chest(14, 7, 0, "front", [(rc("titanium_plate"), 16), (rc("aluminum_plate"), 16), ("minecraft:iron_ingot", 16)])
        r.chest(15, 7, 0, "front", [(rc("vacuum_tube"), 12), (rc("wiring_harness"), 8), ("minecraft:redstone", 32)])
        # heat-treat ovens along the diagonal hull
        r.fput(6, 3, 0, STOVE, "right", lit=False)
        r.fput(7, 4, 0, STOVE, "right", lit=False)
        r.desk(8, 5, LANTERN, mat=IRON_BLOCK)
        r.wall(8, 5, 2, STAR_CHART, "back", lit=False)
        for u in (10, 11, 12):
            r.desk(u, 3, mat=IRON_BLOCK)
        r.item(11, 3, 1, LANTERN)
        r.stool(11, 2)
        # parts cabinets along the front wall
        for u in range(4, 11):
            r.chest(u, 0, 0, "back", [("minecraft:iron_nugget", 32)])
            r.chest(u, 0, 1, "back", [("minecraft:copper_ingot", 8)])
        for v in (1, 2, 3):
            r.fput(15, v, 0, O2_RACK, "left")
        r.block(15, 5, 0, CARTOGRAPHY)
        r.stool(14, 5)
        r.lights_grid((6, 12), (2, 5))

    def storage(self, r, food=False):
        if food:
            goods = [[("minecraft:bread", 32), ("minecraft:baked_potato", 16)],
                     [("minecraft:cooked_beef", 16), ("minecraft:cooked_chicken", 16)],
                     [("minecraft:apple", 24), ("minecraft:carrot", 24)],
                     [("minecraft:cookie", 32), ("minecraft:pumpkin_pie", 8)],
                     [("minecraft:dried_kelp", 32), ("minecraft:melon_slice", 24)],
                     [("minecraft:wheat", 32), ("minecraft:sugar", 16)],
                     [("minecraft:golden_carrot", 8), ("minecraft:honey_bottle", 4)]]
        else:
            goods = [[(rc("titanium_plate"), 12), (rc("aluminum_ingot"), 16)],
                     [(rc("vacuum_tube"), 16), (rc("wiring_harness"), 8)],
                     [("minecraft:iron_ingot", 24), ("minecraft:copper_ingot", 24)],
                     [("minecraft:redstone", 32), ("minecraft:glowstone_dust", 16)],
                     [(EMPTY_CAN, 8), ("minecraft:bucket", 2)],
                     [("minecraft:torch", 32), ("minecraft:paper", 16)],
                     [(rc("aero_alloy_plate"), 4), (rc("aluminum_plate"), 12)]]
        k = 0
        cells = [(u, v) for u in (0, r.U - 1) for v in range(1, r.V - 1)] + [(u, r.V - 1) for u in range(1, r.U - 1)]
        for u, v in cells:                          # crates stacked two high in runs along the walls
            r.crate(u, v, 0, goods[k % len(goods)])
            r.crate(u, v, 1, goods[(k + 3) % len(goods)])
            k += 1
        r.lights_grid((3,), (2, 5))

    def archaeology(self, r):
        """Dr. H. Cooper's xeno-archaeology office and small museum (8 x 8, door at u = 4 on the corridor wall).
        Visitors stand on the door side (v 0..3); the doctor works behind his desk (v 6)."""
        # wall vitrine on the left: quartz plinth, three artifacts in glass compartments with a glass lid
        for v in range(0, 7):
            r.block(0, v, 0, SQUARTZ)
            r.block(0, v, 2, GLASS)
            if v % 2 == 0:
                r.block(0, v, 1, GLASS)
        r.block(0, 1, 1, V_URN)
        r.block(0, 3, 1, V_GLYPH, {"glyph": "1"})
        r.fput(0, 5, 1, V_SUN_DISC, "right")
        r.wall(1, 0, 2, SCONCE, "front")
        # large pieces on the right wall: a stele and a small altar on the floor, a glyph stone on a pedestal
        r.fput(7, 1, 0, V_STELE, "left")
        r.block(7, 3, 0, V_ALTAR)
        r.trim(7, 5, 0, "y")
        r.block(7, 5, 1, V_GLYPH, {"glyph": "3"})
        r.wall(7, 2, 2, SCONCE, "right")
        r.wall(7, 4, 2, SCONCE, "right", lit=False)
        # the doctor's desk, his chair and the archive behind him
        r.desk(2, 5, GLOBE, mat=DARK_OAK)
        r.desk(3, 5, mat=DARK_OAK)
        r.desk(4, 5, LAMP, mat=DARK_OAK)
        r.desk(5, 5, RADIO, mat=DARK_OAK, lit=False)
        r.seat(4, 6, CAPTAIN_CHAIR, "front")
        for u in (1, 2):
            r.fput(u, 7, 0, TAPE, "front")
            r.fput(u, 7, 1, TAPE, "front")
        r.fput(0, 7, 0, LECTERN, "right", has_book="false", powered="false")
        r.block(6, 7, 0, CARTOGRAPHY)
        r.crate(7, 7, 0, [(rc("glyph_tablet"), 2), ("minecraft:paper", 16), ("minecraft:brush", 1)])
        r.window([4], [1], "back", PORTHOLE)
        r.wall(3, 7, 2, STAR_CHART, "back")
        r.wall(5, 7, 2, CLOCK, "back")
        r.carpet("red", range(2, 6), range(1, 4))
        r.light(3, 2)
        r.light(3, 6)

    def laboratory(self, r):
        for u in (1, 2, 14, 15):
            r.fput(u, 7, 0, O2_RACK, "front")
        r.desk(3, 7)
        r.wall(3, 7, 1, CONTROL_PANEL, "back")
        r.fput(4, 7, 0, REFINERY, "front", lit=False)
        r.desk(5, 7, RADAR_SCOPE)
        r.desk(7, 7, BREWING)
        r.fput(8, 7, 0, SINK, "front")
        r.desk(9, 7, BREWING)
        r.desk(11, 7, RADAR_SCOPE, lit=False)
        r.fput(12, 7, 0, LIQUEFIER, "front", lit=False)
        r.desk(13, 7)
        r.wall(13, 7, 1, CONTROL_PANEL, "back", lit=False)
        for u in (4, 12):
            for h in (1, 2):
                r.trim(u, 7, h, "y")
        for u in range(4, 13):
            r.trim(u, 7, 3, "u")
        for u in (3, 5, 11, 13):
            r.stool(u, 6)
        for u in range(5, 12):
            for v in (3, 4):
                r.desk(u, v, mat=WHITE)
        r.item(6, 4, 1, BREWING)
        r.item(8, 3, 1, LAMP, lit=False)
        r.item(10, 4, 1, RADIO, lit=False)
        r.stool(6, 2)
        r.stool(10, 2)
        for v in range(1, 7):
            r.fput(0, v, 0, COMPUTER, "right", lit=v % 2 == 0)
        r.chest(16, 1, 0, "left", [(EMPTY_CAN, 6), ("minecraft:glass_bottle", 8), ("minecraft:coal", 16)])
        r.chest(16, 2, 0, "left", [("minecraft:redstone", 16), ("minecraft:quartz", 16)])
        r.locker(16, 4, "left")                     # lab coats
        r.locker(16, 5, "left")
        r.wall(16, 3, 2, STAR_CHART, "right", lit=False)
        r.wall(8, 0, 2, CLOCK, "front")
        r.lights_grid((3, 13), (2,))
        r.light(8, 5)
        r.light(8, 1)

    def reactor(self, r):
        for u in range(4, 12):
            r.trim(u, 3, 0, "u")
        for v in range(4, 8):
            r.trim(4, v, 0, "v")
            r.trim(11, v, 0, "v")
        for u in range(5, 11):
            for v in range(4, 8):
                c = r.at(u, v)
                self.st.put(self.st.below(c), GRATE)
                self.st.put(self.st.below(self.st.below(c)), SEA_LANTERN)
        band = [(u, 2) for u in range(3, 13)] + [(u, v) for u in (3, 12) for v in range(3, 8)]
        for u, v in band:
            c = self.st.below(r.at(u, v))
            self.st.put(c, YELLOW if (c[0] + c[2]) % 2 else BLACK)
        for u in (6, 9):
            for h in range(4):
                r.put(u, 5, h, REACTOR, {"lit": "true"})
        self.st.standing_sign(r.at(7, 3, 1), r.wdir("front"), ["DANGER", "REACTOR CORE", "KEEP BEHIND", "THE RAIL"])
        r.desk(0, 2)
        r.wall(0, 2, 1, CONTROL_PANEL, "left")
        r.desk(0, 3, RADAR_SCOPE, facing="right")
        r.desk(0, 4)
        r.wall(0, 4, 1, CONTROL_PANEL, "left", lit=False)
        r.stool(1, 3)
        for v in (1, 2, 3):
            r.fput(15, v, 0, COMPUTER, "left", lit=v == 2)
        r.desk(15, 5)
        r.wall(15, 5, 1, CONTROL_PANEL, "right")
        r.stool(14, 5)
        for u in (1, 2, 3):                         # radiation suit lockers by the door
            r.locker(u, 0, "back")
        r.wall(12, 0, 2, CLOCK, "front")
        r.lights_grid((2, 13), (1, 6))

    # ------------------------------------------------------------- DECK C
    def hydroponics(self, r):
        """12 x 8 corner bay (trapezoid): planter rows with walkways, grow lights, potting counter by the door."""
        rows = [(7, range(10, 12)), (5, range(9, 11)), (4, range(7, 11)), (2, range(5, 10))]   # aisle at u = 11
        for v, us in rows:
            for u in us:
                r.put(u, v, 0, PLANTER, {"lit": "true"})
        for v, us in rows:                          # grow lights over the rows, every other block
            if v == 5:
                continue
            for u in us:
                if (u + v) % 2 == 0 and r.free(u, v, 3):
                    r.light(u, v)
        r.window(range(r.U), (2, 3), "back")
        r.window(range(r.V), (2, 3), "left")
        # potting / tool counter along the corridor wall, left of the door
        r.block(4, 0, 0, COMPOSTER, {"level": "0"})
        r.desk(5, 0, POTTED_FERN)
        r.desk(6, 0, LANTERN)
        r.fput(7, 0, 0, SINK, "back")
        r.chest(8, 0, 0, "back", [("minecraft:bone_meal", 32)])
        r.chest(9, 0, 0, "back", [("minecraft:wheat_seeds", 32), ("minecraft:shears", 1)])
        r.wall(11, 3, 2, CLOCK, "right")

    def showroom(self, r):
        """Betty Palmer's "Atomic Home" furniture showroom, 12 x 8, door u 5..6, display windows on the corridor.
        Front: living room of tomorrow (left window) and a diner booth (right window); back: bedroom set, the
        sales counter with the register, catalogue tapes and Betty's desk, and a kitchen / vending corner."""
        st = self.st
        # shop front: both layers of the corridor wall glazed at eye height, neon signs between door and windows
        for u in (1, 2, 3, 8, 9, 10):
            for h in (1, 2):
                st.put(r.at(u, -1, h), GLASS)
                st.put(r.at(u, -2, h), GLASS)
        for u in (4, 7):
            c = r.at(u, -3, 1)
            if st.get(r.at(u, -2, 1)) in WALL_BLOCKS and st.get(c) == AIR:
                st.put(c, NEON, {"facing": r.wdir("front"), "lit": "true"})
            else:
                st.error(f"showroom neon at {c} has no wall")
        # living room of tomorrow: two-seat sofa, boomerang coffee table, floor lamp, radiogram, Sputnik chandelier
        for u in (1, 2):
            r.seat(u, 3, SOFA, "front")
            r.fput(u, 2, 0, TABLE, "front")
        r.put(0, 3, 0, FLOOR_LAMP, {"lit": "true"})
        r.desk(3, 3, RADIO, mat=DARK_OAK, lit=False)
        r.light(1, 2, CHANDELIER)
        r.carpet("cyan", range(0, 4), range(0, 4))
        r.poster(0, 0, 1, P_LIFTOFF, "left")
        # diner corner: a booth on a checkered floor under a neon sign
        for u in range(8, 12):
            for v in range(0, 4):
                st.put(st.below(r.at(u, v)), CHECKER)
        for v in (2, 3):
            r.seat(8, v, SOFA, "right")
            r.fput(9, v, 0, TABLE, "front")
            r.seat(10, v, SOFA, "left")
        r.wall(11, 2, 2, NEON, "right", lit=False)
        r.poster(11, 0, 1, P_SPACE_POP, "right")
        # bedroom set: crew bunk, nightstand with rocket lamp, locker, star chart, "home sweet home" poster
        r.bunk(1, 7, "left")
        r.desk(2, 7, LAMP, mat=SPRUCE)
        r.locker(3, 7, "front")
        r.wall(0, 6, 2, STAR_CHART, "left", lit=False)
        r.poster(0, 5, 1, P_HOMESTEAD, "left")
        r.carpet("light_blue", range(0, 3), range(5, 7))
        # sales counter with the register, Betty's desk, catalogue tapes on the back wall
        r.desk(4, 5, LAMP)
        r.fput(5, 5, 0, CONSOLE, "front")
        r.desk(6, 5, mat=SQUARTZ)
        r.desk(7, 5, GLOBE, mat=SQUARTZ)
        r.desk(7, 6, RADIO, mat=DARK_OAK, lit=False)       # Betty's desk
        for u in (4, 5, 6):
            r.fput(u, 7, 0, TAPE, "front")
        r.poster(5, 7, 1, P_FREEDOM, "back")
        r.wall(7, 7, 2, CLOCK, "back")
        # kitchen / vending corner: vending machine, stove, sink, a cabinet as the refrigerator
        r.chest(8, 7, 0, "front", [("minecraft:apple", 4)])
        r.fput(9, 7, 0, SINK, "front")
        r.fput(10, 7, 0, STOVE, "front", lit=False)
        r.vending(11, 6, "left", True)
        r.lights_grid((3, 9), (1, 5))

    def mess(self, r):
        r.window(range(1, 16), (1, 2), "back")
        for u0 in (5, 9, 13):                       # diner booths under the window band
            for v in (6, 7):
                r.seat(u0, v, SOFA, "right")
                r.fput(u0 + 1, v, 0, TABLE, "front")
                r.seat(u0 + 2, v, SOFA, "left")
            r.light(u0 + 1, 6, CHANDELIER)
        for u in range(6, 11):                      # the long wardroom table
            r.fput(u, 3, 0, TABLE, "front")
            r.stool(u, 2)
            r.stool(u, 4)
        r.light(8, 3, CHANDELIER)
        # galley along the left wall: food cabinet, two stoves, counter, sink, counter, pantry cabinets
        r.chest(0, 0, 0, "right", [("minecraft:bread", 16), ("minecraft:cooked_beef", 8), ("minecraft:apple", 12)])
        r.fput(0, 1, 0, STOVE, "right", lit=False)
        r.desk(0, 2)
        r.fput(0, 3, 0, SINK, "right")
        r.desk(0, 4)
        r.fput(0, 5, 0, STOVE, "right", lit=False)
        for v in (6, 7):
            r.chest(0, v, 0, "right", [("minecraft:sugar", 16), ("minecraft:wheat", 16)])
            r.chest(0, v, 1, "right", [("minecraft:cocoa_beans", 16)])
        for v in (1, 2, 3, 4):                      # serving counter with diner stools
            r.desk(2, v)
            r.stool(3, v)
        r.wall(2, 0, 2, NEON, "front", lit=False)
        r.vending(16, 0, "left", True)
        r.vending(16, 1, "left", False)
        r.fput(16, 3, 0, TV, "left", lit=True)
        r.desk(16, 4, RADIO, facing="left", lit=False)
        r.seat(13, 3, EGG_CHAIR, "right")
        r.seat(13, 4, EGG_CHAIR, "right")
        r.poster(5, 0, 1, P_SPACE_POP, "front")
        r.poster(12, 0, 1, P_HOMESTEAD, "front")
        r.wall(8, 0, 2, CLOCK, "front")
        r.lights_grid((3, 13), (1,))

    def medical(self, r):
        r.window([10, 13], [1], "back", PORTHOLE)
        r.bed(10, 6, "back", "white")
        r.bed(13, 6, "back", "white")
        r.desk(11, 7)
        r.wall(11, 7, 1, CONTROL_PANEL, "back")
        r.desk(12, 7, LAMP, lit=False)
        r.wall(10, 7, 2, SCONCE, "back")
        r.wall(13, 7, 2, SCONCE, "back", lit=False)
        r.chest(1, 7, 0, "front", [("minecraft:golden_apple", 4), ("minecraft:glistering_melon_slice", 4),
                                   ("minecraft:glass_bottle", 8)])
        r.desk(2, 7, BREWING)
        r.fput(3, 7, 0, SINK, "front")
        r.desk(4, 7)
        r.wall(4, 7, 1, CONTROL_PANEL, "back", lit=False)
        r.chest(5, 7, 0, "front", [("minecraft:paper", 16), ("minecraft:honey_bottle", 6), ("minecraft:milk_bucket", 1)])
        r.bunk(7, 6, "back")                        # examination couch, head at the hull, under the surgery lamp
        r.light(7, 6, CHANDELIER)
        r.desk(6, 6, RADAR_SCOPE, facing="right", lit=False)
        r.stool(6, 5)
        for v in (2, 3, 4, 5):                      # medicine cabinets on the left wall
            r.chest(0, v, 0, "right", [("minecraft:glass_bottle", 4)])
            r.chest(0, v, 1, "right", [("minecraft:paper", 4)])
        r.desk(2, 0, LAMP, facing="back")
        r.desk(3, 0, RADIO, facing="back", lit=False)
        r.seat(2, 1, CAPTAIN_CHAIR, "front")
        for v in (2, 3):
            r.fput(15, v, 0, O2_RACK, "left")
        r.wall(15, 5, 2, STAR_CHART, "right", lit=False)
        r.wall(8, 0, 2, CLOCK, "front")
        r.lights_grid((3, 12), (3,))

    # ------------------------------------------------------------- DECK D
    def cabin(self, r, n):
        rug = ("red", "light_blue", "cyan")[n % 3]
        r.window([1, 3], [1], "back", PORTHOLE)
        r.bunk(1, 7, "left")               # two full-length berths along the hull, heads against the side walls,
        r.bunk(3, 7, "right")              # a porthole above each berth
        r.wall(2, 7, 1, CLOCK, "back")      # clock between the berths
        r.desk(0, 4, LAMP, facing="right", mat=SPRUCE_SLAB, lit=n % 2 == 1)
        r.stool(1, 4)
        r.desk(4, 4, RADIO, facing="left", mat=SPRUCE_SLAB, lit=False)
        r.stool(3, 4)
        r.wall(0, 4, 2, STAR_CHART, "left", lit=False)
        r.wall(4, 4, 2, SCONCE, "right", lit=n % 2 == 0)
        r.locker(0, 0, "right", [("minecraft:paper", 4)])     # one locker per crew member
        r.locker(4, 0, "left", [("minecraft:paper", 4)])
        r.poster(0, 2, 1, CABIN_POSTERS[n - 1], "left")       # a personal poster
        r.carpet(rug, (1, 2, 3), range(1, 7))
        r.light(2, 2)

    def washroom(self, r):
        for u in (2, 5):
            for v in (5, 6, 7):
                for h in (0, 1, 2):
                    self.st.seal(r.at(u, v, h), WHITE)
        for u in (0, 3, 6):
            for h in (0, 1, 2):
                self.st.seal(r.at(u, 5, h), WHITE)
            self.st.seal(r.at(u + 1, 5, 2), WHITE)
            self.st.door(r.at(u + 1, 5), r.wdir("front"), "right")
        for u in (0, 6):                  # showers: drain grate, shower head from the ceiling
            for uu in (u, u + 1):
                for v in (6, 7):
                    self.st.put(self.st.below(r.at(uu, v)), GRATE)
            r.put(u, 7, 3, LIGHTNING_ROD, {"facing": "down", "powered": "false", "waterlogged": "false"})
            r.light(u + 1, 6)
        r.put(4, 7, 0, SQUARTZ_STAIRS, {"facing": r.wdir("back"), "half": "bottom", "shape": "straight",
                                         "waterlogged": "false"})
        for u, sink in ((0, False), (1, True), (2, False), (6, True), (7, False)):
            if sink:
                r.fput(u, 0, 0, SINK, "back")
                self.st.put(r.at(u, -1, 1), TINTED_GLASS)
            else:
                r.desk(u, 0)
        r.locker(0, 2, "right", [("minecraft:white_wool", 8)])    # towel lockers
        r.locker(7, 2, "left", [("minecraft:white_wool", 8)])
        r.wall(7, 3, 2, CLOCK, "right")
        r.light(3, 2)

    def recreation(self, r):
        r.window(range(r.U), (1, 2), "back")
        r.window(range(r.V), (1, 2), "left")
        for v in range(1, 7):                       # library: tape and book archive
            for h in (0, 1, 2):
                r.fput(15, v, h, TAPE, "left")
        r.seat(11, 3, EGG_CHAIR, "right")
        r.fput(12, 3, 0, TABLE, "front")
        r.seat(13, 3, EGG_CHAIR, "left")
        for (tu, tv) in ((6, 1), (9, 2)):           # card tables
            r.fput(tu, tv, 0, TABLE, "front")
            for du, dv in ((-1, 0), (1, 0), (0, 1)):
                r.stool(tu + du, tv + dv)
        for u in (9, 10, 11):
            r.seat(u, 5, SOFA, "back")
        r.fput(10, 6, 0, TABLE, "front")
        r.put(12, 5, 0, FLOOR_LAMP, {"lit": "true"})
        r.block(11, 0, 0, JUKEBOX, {"has_record": "false"})
        r.wall(11, 0, 2, NEON, "front")
        r.wall(10, 0, 2, CLOCK, "front")
        r.poster(7, 0, 1, P_LIFTOFF, "front")
        r.carpet("red", range(8, 13), range(4, 7))
        r.light(10, 3, CHANDELIER)
        r.light(13, 5)
        r.light(7, 2)


# ----------------------------------------------------------------------------
# Station assembly
# ----------------------------------------------------------------------------
class Builder(Station):
    def define_rooms(self):
        for key, kind, zone, label, sign, rect, back, doors in BAND_ROOMS:
            self.add_region(Room(self, key, kind, zone, label, sign, rect, back, doors=doors))
        # hub: lobby (ring level), EVA prep + supply stores (upper level), airlock and stair landing on the deck
        self.add_region(Room(self, "lobby", "lobby", "lobby", "Hub lobby", None, (-8, -8, 8, 8), "north"))
        self.add_region(Room(self, "eva", "eva", "eva", "EVA prep / suit-up room", None, (-8, -8, 0, 8), "west",
                             floor_y=UF))
        self.add_region(Room(self, "supply", "supply", "store", "Supply stores (RP-1 / LOX)", None, (2, -8, 8, 8),
                             "east", floor_y=UF))
        self.add_region(Room(self, "airlock", "airlock", "airlock", "Airlock", None, (-8, -4, -6, -2), "west",
                             floor_y=DECK, height=3))
        self.add_region(Room(self, "landing", "stair", "airlock", "Airlock stair landing", None, (-8, 0, -6, 3), "west",
                             floor_y=DECK, height=3, priority=1))

    def build_hut_mass(self):
        for x in range(-9, -4):
            for z in range(-5, 5):
                for y in range(DECK + 1, DECK + 5):
                    self.mass((x, y, z))

    def carve_hub_links(self):
        # doorway EVA prep -> supply stores
        for z in (-1, 0):
            for y in (UF + 1, UF + 2):
                self.carve((1, y, z), "eva")
        # deck opening above the airlock stair flight
        for x in (-8, -7):
            for z in (2, 3, 4):
                self.carve((x, DECK, z), "landing")
        # inner airlock door between chamber and landing, outer door to the deck
        for y in (DECK + 1, DECK + 2):
            self.carve((-7, y, -1), "airlock")
            self.carve((-5, y, -3), "airlock")
        # opening in the upper floor above the lobby stairs
        for x in (-6, -5, -4):
            for z in (-8, -7):
                self.carve((x, UF, z), "lobby")

    def hub_structure(self):
        """Stairs, railings, doors and buttons of the hub (after painting)."""
        # airlock stairs: deck landing (floor = deck) down to the EVA prep floor, walking south; five steps of one
        # block each, the top step sits in the deck plane
        for i, z in enumerate((1, 2, 3, 4, 5)):
            y = DECK - i
            for x in (-8, -7):
                self.seal((x, y, z), QUARTZ_STAIRS)
                self.stairs((x, y, z), "north")
                for yy in range(UF + 1, y):
                    self.seal((x, yy, z), SQUARTZ)
        for z in (2, 3):
            self.seal((-6, DECK + 1, z), CHROME, {"axis": "z"})
        # lobby stairs: EVA prep floor down to the lobby, walking east along the north wall (top step in the floor)
        for i, x in enumerate((-7, -6, -5, -4, -3)):
            y = UF - i
            for z in (-8, -7):
                self.seal((x, y, z), QUARTZ_STAIRS)
                self.stairs((x, y, z), "west")
                for yy in range(F + 1, y):
                    self.seal((x, yy, z), SQUARTZ)
        for x in (-7, -6, -5, -4, -3):
            self.seal((x, UF + 1, -6), CHROME, {"axis": "x"})
        for z in (-8, -7):
            self.seal((-3, UF + 1, z), CHROME, {"axis": "z"})
        # airlock: outer and inner airlock doors (opened by hand)
        self.airlock_door((-5, DECK + 1, -3), "west")
        self.airlock_door((-7, DECK + 1, -1), "south")

    # ------------------------------------------------------------------ hub rooms
    def furnish_hub(self):
        st = self
        # --- airlock chamber and landing ---
        a = self.rooms["airlock"]
        a.light(1, 1)
        st.wall_sign((-6, DECK + 3, -4), "south", ["AIRLOCK", "CLOSE OUTER", "DOOR BEFORE", "OPENING INNER"])
        st.wall_sign((-4, DECK + 3, -3), "east", ["- DECK H -", "AIRLOCK", "FREEDOM", "STATION"])
        st.put((-7, DECK + 3, 0), CEILING_LIGHT, {"lit": "true"})
        st.wall_sign((-6, DECK + 2, 0), "west", ["", "DOWN TO", "EVA PREP", ""], (-5, DECK + 2, 0))
        # --- EVA prep / suit-up room (u = 8 - z, v = -x) ---
        e = self.rooms["eva"]
        for u in range(1, 8):                      # suit lockers: one per crew member (12 crew + commander)
            e.locker(u, 0, "back", [(LOX, 2)])
        for v in range(1, 7):
            e.locker(0, v, "right", [(LOX, 2)])
        for u in range(2, 7):                      # bench facing the lockers
            e.seat(u, 2, SOFA, "front")
        for u in range(10, 16):                    # oxygen bottle racks on the north part of the partition
            e.fput(u, 0, 0, O2_RACK, "back")
        e.poster(1, 8, 1, P_SUIT_CHECK, "back")    # at the foot of the airlock stairs
        # suit check desk on the west wall: pressure panel, lamp, stool
        e.desk(9, 8)
        e.wall(9, 8, 1, CONTROL_PANEL, "back")
        e.desk(10, 8, LAMP, facing="front")
        e.stool(9, 7)
        e.wall(12, 0, 2, CLOCK, "front")
        st.wall_sign((-8, UF + 3, 6), "east", ["WELCOME ABOARD", "FREEDOM", "STATION", "DECK H - EVA"])
        st.wall_sign((0, UF + 3, -1), "west", ["SUPPLY STORES", "RP-1 FUEL", "LIQUID OXYGEN", ""])
        st.wall_sign((-8, UF + 3, -6), "east", ["STAIRS DOWN", "HUB LOBBY", "SPOKES 1-4", ""])
        e.wall(16, 2, 2, STAR_CHART, "right")
        e.wall(10, 8, 2, SCONCE, "back")
        for u, v in ((3, 4), (8, 4), (12, 3), (3, 7), (13, 6)):
            if e.free(u, v, 3) and self.is_wall(self.above(e.at(u, v, 3))):
                e.light(u, v)
        # --- supply stores (u = z + 8, v = x - 2) ---
        s = self.rooms["supply"]
        fuel = [(FUEL, 16), (FUEL, 16), (FUEL, 16)]
        lox = [(LOX, 16), (LOX, 16), (LOX, 16)]
        runs = {5: fuel, 6: fuel, 7: [(EMPTY_CAN, 16), (FUEL, 8)], 9: [(EMPTY_CAN, 16), (LOX, 8)], 10: lox, 11: lox}
        for u in range(1, 16):                     # cargo crates, two high, along the walls
            items = runs.get(u, [("minecraft:bread", 16), ("minecraft:torch", 16)] if u % 2 else
                             [(rc("titanium_plate"), 8), ("minecraft:iron_ingot", 16)])
            s.crate(u, 6, 0, items)
            s.crate(u, 6, 1, [(EMPTY_CAN, 8)])
        for v in range(0, 6):
            s.crate(0, v, 0, [(rc("aluminum_plate"), 16), (rc("vacuum_tube"), 8)])
            s.crate(0, v, 1, [("minecraft:paper", 8)])
            s.crate(16, v, 0, [("minecraft:cooked_beef", 16), ("minecraft:apple", 16)])
            s.crate(16, v, 1, [("minecraft:bread", 8)])
        for u in range(4, 13):                     # island stack in the middle
            if u in (7, 8):
                continue
            s.crate(u, 3, 0, [("minecraft:torch", 32), (rc("aluminum_ingot"), 16)])
            s.crate(u, 3, 1, [("minecraft:iron_ingot", 8)])
        st.wall_sign((8, UF + 3, -2), "west", ["RP-1", "ROCKET FUEL", "CANISTERS", ""])
        st.wall_sign((8, UF + 3, 2), "west", ["LOX", "LIQUID OXYGEN", "CANISTERS", ""])
        for u, v in ((4, 3), (12, 3)):
            s.light(u, v)
        # --- hub lobby (u = x + 8, v = 8 - z) ---
        lb = self.rooms["lobby"]
        for h in range(4):                                # station axis column
            lb.trim(8, 8, h, "y")
        lb.wall(8, 7, 2, CLOCK, "back")
        lb.wall(8, 9, 2, STAR_CHART, "front")
        # dockmaster's desk on the west wall (u = 0)
        lb.desk(0, 3)
        lb.wall(0, 3, 1, CONTROL_PANEL, "left")
        lb.desk(0, 4, RADAR_SCOPE, facing="right")
        lb.desk(0, 5, RADIO, facing="right", lit=False)
        lb.poster(13, 16, 1, P_FREEDOM, "back")    # above the waiting lounges
        lb.poster(13, 0, 1, P_VESPER, "front")
        lb.seat(1, 4, CAPTAIN_CHAIR, "left")
        st.wall_sign(lb.at(0, 4, 2), "east", ["DOCKING", "CONTROL", "", ""])
        # waiting lounges in the two eastern corners
        for v_sofa, face, v_tab in ((16, "front", 14), (0, "back", 2)):
            for u in (12, 13, 14):
                lb.seat(u, v_sofa, SOFA, face)
                lb.fput(u, v_tab, 0, TABLE, "front")
        lb.seat(16, 14, EGG_CHAIR, "left")
        lb.seat(16, 2, EGG_CHAIR, "left")
        lb.wall(16, 5, 2, SCONCE, "right")
        lb.wall(16, 11, 2, SCONCE, "right")
        lb.wall(4, 0, 2, SCONCE, "front")
        lb.wall(12, 0, 2, SCONCE, "front")
        lb.lights_grid((4, 12), (4, 12))
        lb.light(8, 13)
        lb.light(8, 3)
        # signs above the four spoke doorways
        spoke_signs = {
            "north": ["SPOKE 1 - NORTH", "DECK A", "COMMAND", "BRIDGE - RADIO"],
            "east": ["SPOKE 2 - EAST", "DECK B", "SCIENCE", "LAB - REACTOR"],
            "south": ["SPOKE 3 - SOUTH", "DECK C", "LIFE SUPPORT", "MESS - MEDICAL"],
            "west": ["SPOKE 4 - WEST", "DECK D", "HABITATION", "CREW CABINS"],
        }
        for d, lines in spoke_signs.items():
            dx, dz = DIRS[d]
            st.wall_sign((HUB_IN * dx, F + 4, HUB_IN * dz), OPPOSITE[d], lines)

    # ------------------------------------------------------------------ corridor and spokes
    def corridor_decor(self):
        deck = {"north": ("DECK A", "COMMAND"), "east": ("DECK B", "SCIENCE"),
                "south": ("DECK C", "LIFE SUPPORT"), "west": ("DECK D", "HABITATION")}
        for d in HORIZ:
            dx, dz = DIRS[d]
            # side frame: n = outward normal (d), s = along the side
            def P(t, s, y):
                return (t * dx - s * dz, y, t * dz + s * dx)
            # ceiling lights on the centre line every 4 blocks
            for s in range(-25, 26, 5):
                self.put(P(25, s, F + 4), CEILING_LIGHT, {"lit": "true"})
            # spoke mouth: sign on the lintel, clocks either side
            self.wall_sign(P(CORR_IN, 0, F + 4), d, ["SPOKE " + str(HORIZ.index(d) + 1), "TO HUB", "DOCKING - EVA", ""])
            # emergency oxygen alcoves recessed into the inner wall
            for s in (-12, 12):
                for y in (F + 1, F + 2):
                    self.carve(P(CORR_IN - 1, s, y), "corridor")
                self.put(P(CORR_IN - 1, s, F + 1), O2_RACK, {"facing": d})
                self.wall_sign(P(CORR_IN, s, F + 3), d, ["EMERGENCY", "OXYGEN", "", ""])
            # portholes looking at the hub and spokes
            for s in (-6, 6):
                for t in (RING_IN_HULL, RING_IN_HULL + 1):
                    self.put(P(t, s, F + 2), PORTHOLE)
            # posters on the inner wall between the portholes and alcoves
            for k, s in enumerate((-21, -9, 9, 21)):
                name = (P_LIFTOFF, P_HOMESTEAD, P_SPACE_POP, P_VESPER, P_FREEDOM)[(HORIZ.index(d) * 4 + k) % 5]
                for y, half in ((F + 2, "lower"), (F + 3, "upper")):
                    if self.get(P(CORR_IN - 1, s, y)) not in WALL_BLOCKS:
                        self.error(f"corridor poster at {P(CORR_IN, s, y)} has no wall")
                    self.put(P(CORR_IN, s, y), name, {"facing": d, "half": half})
            # deck name at both ends of the side
            for s in (-17, 17):
                self.wall_sign(P(CORR_IN, s, F + 3), d, [deck[d][0], deck[d][1], "", ""])
            # spoke tube: lights and portholes
            for t in (13, 18):
                self.put(P(t, 0, F + 4), CEILING_LIGHT, {"lit": "true"})
            for t in (14, 18):
                for w in (-2, -3, 2, 3):
                    self.put(P(t, w, F + 2), PORTHOLE)
        # posters on the door wall, on clear stretches between doorways (at least 2 blocks from any door/sign)
        cycle = [P_HOMESTEAD, P_LIFTOFF, P_FREEDOM, P_SPACE_POP, P_VESPER]
        k = 0
        for d in HORIZ:
            dx, dz = DIRS[d]

            def P(t, s, y):
                return (t * dx - s * dz, y, t * dz + s * dx)

            last = -99
            for s in range(-22, 23):
                ok = all(self.get(P(CORR_OUT + 1, ss, y)) in WALL_BLOCKS for ss in range(s - 2, s + 3) for y in (F + 1, F + 2, F + 3)) \
                    and all(self.get(P(CORR_OUT, ss, y)) == AIR for ss in range(s - 1, s + 2) for y in (F + 1, F + 2, F + 3))
                if ok and s - last >= 9:
                    for y, half in ((F + 2, "lower"), (F + 3, "upper")):
                        self.put(P(CORR_OUT, s, y), cycle[k % len(cycle)], {"facing": OPPOSITE[d], "half": half})
                    k += 1
                    last = s
        # lanes: corridor and spoke cells at walking height must stay clear
        for c, key in self.region.items():
            reg = self.regions[key]
            if reg.kind in ("corridor", "spoke") and c[1] in (F + 1, F + 2):
                self.lanes.add(c)
        for d in HORIZ:
            dx, dz = DIRS[d]
            for s in (-12, 12):
                for y in (F + 1, F + 2):
                    self.lanes.discard(((CORR_IN - 1) * dx - s * dz, y, (CORR_IN - 1) * dz + s * dx))

    # ------------------------------------------------------------------ exterior
    def exterior(self):
        # docking pad (plain blocks; the game shapes the 3x3 after placement) and service tower
        for x in (-1, 0, 1):
            for z in (-1, 0, 1):
                self.put((x, DECK, z), LAUNCH_PAD)
        for y in range(DECK, DECK + 8):
            self.put((2, y, 0), TOWER)
        for x, z in ((4, 4), (-4, 4), (4, -4), (-4, -4)):
            self.put((x, DECK, z), SEA_LANTERN)
        # antenna mast on the deck (outside the 5x5 docking column)
        for y in range(DECK + 1, DECK + 7):
            self.put((6, y, -6), CHROME, {"axis": "y"})
        self.put((6, DECK + 7, -6), LIGHTNING_ROD, {"facing": "up", "powered": "false", "waterlogged": "false"})
        for d in HORIZ:
            dx, dz = DIRS[d]
            self.put((6 + dx, DECK + 5, -6 + dz), END_ROD, {"facing": d})
        self.put((6, DECK + 3, -6), SEA_LANTERN)
        # dish under the hub
        self.put((0, F - 2, 0), CHROME, {"axis": "y"})
        for x in range(-4, 5):
            for z in range(-4, 5):
                if 0 < math.hypot(x, z) <= 4.5:
                    self.put((x, F - 3, z), QUARTZ_SLAB, {"type": "top", "waterlogged": "false"})
        self.put((0, F - 3, 0), TI)
        self.put((0, F - 4, 0), END_ROD, {"facing": "down"})
        # radar dish over the bridge, aerial mast over the radio room
        for y in (ROOF + 1, ROOF + 2):
            self.put((0, y, -33), CHROME, {"axis": "y"})
        for dx in range(-2, 3):
            for dz in range(-1, 2):
                if (dx, dz) != (0, 0):
                    self.put((dx, ROOF + 3, -33 + dz), QUARTZ_SLAB, {"type": "bottom", "waterlogged": "false"})
        self.put((0, ROOF + 3, -33), TI)
        self.put((0, ROOF + 4, -33), END_ROD, {"facing": "up"})
        for y in range(ROOF + 1, ROOF + 6):
            self.put((19, y, -33), CHROME, {"axis": "y"})
        self.put((19, ROOF + 6, -33), LIGHTNING_ROD, {"facing": "up", "powered": "false", "waterlogged": "false"})
        for d in ("east", "west"):
            dx, dz = DIRS[d]
            self.put((19 + dx, ROOF + 4, -33), END_ROD, {"facing": d})
        # beacons on the chamfered corners
        for sx in (-1, 1):
            for sz in (-1, 1):
                self.put((30 * sx, ROOF + 1, 30 * sz), SEA_LANTERN)

    # ------------------------------------------------------------------ build
    def build(self):
        self.define_rooms()
        self.build_mass()
        self.build_hut_mass()
        self.carve_spaces()
        self.carve_hub_links()
        self.paint()
        self.hub_structure()
        fn = Furnisher(self)
        for key, room in self.rooms.items():
            if room.kind == "cabin":
                fn.cabin(room, int(key.split("_")[1]))
            elif key == "galley_stores":
                fn.storage(room, food=True)
            elif hasattr(fn, key):
                getattr(fn, key)(room)
        self.room_doors()
        self.furnish_hub()
        self.corridor_decor()
        self.exterior()
        self.finish()
        return self

    def room_doors(self):
        for room in self.rooms.values():
            for (u0, width, kind) in room.doors:
                if kind == "birch":
                    for u in range(u0, u0 + width):
                        self.wood_door(room.at(u, -1), room.wdir("front"))
                if room.sign_lines:
                    mid = u0 + width // 2
                    self.wall_sign(room.at(mid, -3, 2), room.wdir("front"), room.sign_lines)

    # ------------------------------------------------------------------ finishing and checks
    def finish(self):
        for c in self.inner:
            if c not in self.blocks:
                self.blocks[c] = (AIR, {}, None)
        for c, (name, _, _) in self.blocks.items():
            if name == STRUCT:
                self.error(f"unpainted structure at {c}")
        self.fix_stairs()

    def fix_stairs(self):
        def is_st(c):
            return self.get(c) in (QUARTZ_STAIRS, SQUARTZ_STAIRS)
        for c, (name, props, nbt) in list(self.blocks.items()):
            if name not in (QUARTZ_STAIRS, SQUARTZ_STAIRS):
                continue
            f, half = props["facing"], props["half"]
            dx, dz = DIRS[f]
            shape = "straight"

            def can_take(face):
                fx, fz = DIRS[face]
                n = (c[0] + fx, c[1], c[2] + fz)
                return not is_st(n) or self.props(n)["facing"] != f or self.props(n)["half"] != half
            front = (c[0] + dx, c[1], c[2] + dz)
            back = (c[0] - dx, c[1], c[2] - dz)
            done = False
            if is_st(front) and self.props(front)["half"] == half:
                d1 = self.props(front)["facing"]
                if DIRS[d1][0] != 0 if dx == 0 else DIRS[d1][1] != 0:
                    if can_take(OPPOSITE[d1]):
                        shape = "outer_left" if d1 == CCW[f] else "outer_right"
                        done = True
            if not done and is_st(back) and self.props(back)["half"] == half:
                d2 = self.props(back)["facing"]
                if DIRS[d2][0] != 0 if dx == 0 else DIRS[d2][1] != 0:
                    if can_take(d2):
                        shape = "inner_left" if d2 == CCW[f] else "inner_right"
            self.blocks[c] = (name, dict(props, shape=shape), nbt)


# ----------------------------------------------------------------------------
# Checker: the rules the station must obey (raises on any violation)
# ----------------------------------------------------------------------------
def neighbours6(c):
    x, y, z = c
    return [(x + 1, y, z), (x - 1, y, z), (x, y + 1, z), (x, y - 1, z), (x, y, z + 1), (x, y, z - 1)]


class Checker:
    def __init__(self, st):
        self.st = st
        self.problems = []
        self.stats = {}

    def fail(self, msg):
        self.problems.append(msg)

    def run(self):
        st = self.st
        self.problems.extend(st.errors)
        self.supports()
        self.desks_and_seats()
        self.placement_kinds()
        self.lanes()
        self.docking()
        self.airtight()
        self.reachability()
        self.requirements()
        return self.problems

    # -- supports -----------------------------------------------------------
    def supports(self):
        st = self.st
        for c, (name, props, _) in st.blocks.items():
            below, above = st.below(c), st.above(c)
            if name in WALL_DECOR or (name == BUTTON and props.get("face") == "wall"):
                dx, dz = DIRS[props["facing"]]
                back = (c[0] - dx, c[1], c[2] - dz)
                if st.get(back) not in WALL_BLOCKS:
                    self.fail(f"{name} at {c} hangs on {st.get(back)}, not a wall")
            if name in CEILING_HUNG and st.get(above) not in WALL_BLOCKS:
                self.fail(f"{name} at {c} has no ceiling above ({st.get(above)})")
            if name in TALL:
                other = above if props["half"] == "lower" else below
                want = "upper" if props["half"] == "lower" else "lower"
                op = st.props(other)
                if st.get(other) != name or op.get("half") != want or op.get("facing") != props["facing"] \
                        or op.get("lit") != props.get("lit"):
                    self.fail(f"two-tall {name} at {c} has no matching {want} half")
                if props["half"] == "upper" and st.blocks[c][2] is not None:
                    self.fail(f"upper half of {name} at {c} carries block entity data")
                if name in STORAGE_BLOCKS and props["half"] == "lower" and st.blocks[c][2] is None:
                    self.fail(f"{name} at {c} has no storage data")
            if name in (SUPPLY_CABINET, CARGO_CRATE) and st.blocks[c][2] is None:
                self.fail(f"{name} at {c} has no storage data")
            if name in DOORS:
                if props["half"] == "lower":
                    if st.get(below) not in FULL_CUBES:
                        self.fail(f"door at {c} stands on {st.get(below)}")
                    if st.get(above) != name or st.props(above).get("half") != "upper":
                        self.fail(f"door at {c} has no upper half")
                elif st.get(below) != name:
                    self.fail(f"upper door at {c} without lower half")
            if name == CREW_BUNK:
                dx, dz = DIRS[props["facing"]]
                sgn = -1 if props["part"] == "foot" else 1      # head lies behind the foot (against facing)
                other = (c[0] + sgn * dx, c[1], c[2] + sgn * dz)
                if st.get(other) != name or st.props(other).get("part") == props["part"] \
                        or st.props(other).get("facing") != props["facing"]:
                    self.fail(f"crew bunk half at {c} is not paired")
                if st.get(below) not in FULL_CUBES:
                    self.fail(f"crew bunk at {c} stands on {st.get(below)}")
                if props["part"] == "head" and not any(
                        st.get((c[0] + ex, c[1], c[2] + ez)) in WALL_BLOCKS for ex, ez in DIRS.values()):
                    self.fail(f"crew bunk head at {c} is not against a wall")
            if name in BEDS and name != CREW_BUNK:
                if st.get(below) not in FULL_CUBES:
                    self.fail(f"bed at {c} stands on {st.get(below)}")
                dx, dz = DIRS[props["facing"]]
                sgn = 1 if props["part"] == "foot" else -1
                other = (c[0] + sgn * dx, c[1], c[2] + sgn * dz)
                if st.get(other) != name or st.props(other).get("part") == props["part"] \
                        or st.props(other).get("facing") != props["facing"]:
                    self.fail(f"bed half at {c} is not paired")
            if name.endswith("_carpet") and st.get(below) in (None, AIR):
                self.fail(f"carpet at {c} floats")
            if name == LANTERN:
                need = above if props["hanging"] == "true" else below
                if st.get(need) not in FULL_CUBES:
                    self.fail(f"lantern at {c} unsupported")
            if name == STANDING_SIGN and st.get(below) not in FULL_CUBES:
                self.fail(f"standing sign at {c} unsupported")
            if name in (QUARTZ_STAIRS, SQUARTZ_STAIRS) and props["shape"] != "straight":
                self.fail(f"stairs at {c} are not straight ({props['shape']})")
            if name == CHEST and props["type"] != "single":
                self.fail(f"chest at {c} is not single")

    # -- desks, seats, racks ------------------------------------------------------
    def is_desk(self, c):
        name = self.st.get(c)
        if name in DESK_BLOCKS:
            return True
        return name in DESK_SLABS and self.st.props(c).get("type") == "top"

    def desks_and_seats(self):
        st = self.st
        targets = {CONSOLE, TABLE, TV, RADIO, TELESCOPE, COMPUTER, O2_RACK, SMITHING, CARTOGRAPHY, STONECUTTER,
                   VENDING, WORKBENCH, STOVE, SINK, CREW_LOCKER, SUPPLY_CABINET, TAPE} | DESK_BLOCKS | DESK_SLABS
        for c, (name, props, _) in st.blocks.items():
            if name in ON_DESK:
                b = st.below(c)
                if not (self.is_desk(b) or (name == GLOBE and st.get(b) == CHROME)):
                    self.fail(f"{name} at {c} is not standing on a desk ({st.get(b)})")
            if name in ON_PEDESTAL and not (self.is_desk(st.below(c)) or st.get(st.below(c)) == CHROME):
                self.fail(f"artifact {name} at {c} is not on a pedestal ({st.get(st.below(c))})")
            if name == CONTROL_PANEL and not self.is_desk(st.below(c)):
                self.fail(f"control panel at {c} is not above a desk ({st.get(st.below(c))})")
            if name == COMPUTER:
                dx, dz = DIRS[props["facing"]]
                back = (c[0] - dx, c[1], c[2] - dz)
                front = (c[0] + dx, c[1], c[2] + dz)
                if st.get(back) not in WALL_BLOCKS and st.get(back) != COMPUTER:
                    self.fail(f"computer bank at {c} does not stand against a wall ({st.get(back)})")
                if st.get(front) != AIR and st.get(front) not in BEDS and not st.get(front).endswith("_carpet"):
                    self.fail(f"computer bank at {c} has no walkway in front ({st.get(front)})")
            if name in (O2_RACK, VENDING, TV, CONSOLE, REFINERY, LIQUEFIER, STOVE, SINK, CREW_LOCKER, SUPPLY_CABINET,
                        WORKBENCH, TAPE):
                dx, dz = DIRS[props["facing"]]
                back = (c[0] - dx, c[1], c[2] - dz)
                if name != CONSOLE and st.get(back) not in WALL_BLOCKS:
                    self.fail(f"{name} at {c} does not stand with its back to a wall ({st.get(back)})")
                front = (c[0] + dx, c[1], c[2] + dz)
                if name not in (TAPE,) and st.get(front) not in (AIR, CAPTAIN_CHAIR) and not st.get(front).endswith("_carpet"):
                    self.fail(f"{name} at {c} is blocked in front ({st.get(front)})")
            if name in SEATS_FACING:
                dx, dz = DIRS[props["facing"]]
                ok = False
                for k in range(1, 7):
                    for h in (0, 1, 2):
                        t = (c[0] + dx * k, c[1] + h, c[2] + dz * k)
                        n = st.get(t)
                        if (k <= 3 and h <= 1 and (n in targets or self.is_desk(t))) or (n in WINDOWS and h >= 1):
                            ok = True
                if not ok:
                    self.fail(f"{name} at {c} faces nothing ({props['facing']})")
            if name == STOOL:
                if not any(st.get((c[0] + dx, c[1], c[2] + dz)) in targets or self.is_desk((c[0] + dx, c[1], c[2] + dz))
                           for dx, dz in DIRS.values()):
                    self.fail(f"stool at {c} stands next to no desk/table/counter")
            if name in CONTAINERS:
                key = st.region.get(c)
                kind = st.regions[key].kind if key else None
                if kind in ("corridor", "spoke", "lobby", None):
                    self.fail(f"{name} at {c} stands loose in {kind}")
                if not any(st.get((c[0] + dx, c[1], c[2] + dz)) in (WALL_BLOCKS | CONTAINERS) for dx, dz in DIRS.values()) \
                        and st.get(st.below(c)) not in CONTAINERS:
                    self.fail(f"{name} at {c} is not on a run against a wall")

    def placement_kinds(self):
        st = self.st
        for key, room in st.rooms.items():
            for (u0, width, kind) in room.doors:
                c = room.at(u0 + width // 2, -3, 2)
                if st.get(c) != WALL_SIGN:
                    self.fail(f"{key}: no sign over its door at {c}")
        for c, (name, _, _) in st.blocks.items():
            group = "bed" if name in BEDS else name
            if group in ALLOWED_KINDS:
                key = st.region.get(c)
                kind = st.regions[key].kind if key else None
                if kind not in ALLOWED_KINDS[group]:
                    self.fail(f"{name} at {c} does not belong in {kind}")
        # wall decor never hangs on a window: checked in supports (windows are not WALL_BLOCKS)

    # -- corridors are corridors ---------------------------------------------------------
    def lanes(self):
        st = self.st
        bad = 0
        for c in st.lanes:
            n = st.get(c)
            if n == AIR or n in NO_COLLISION_DECOR:
                if n in NO_COLLISION_DECOR and c[1] == F + 1:
                    self.fail(f"{n} at {c} at foot height in a corridor")
                continue
            bad += 1
            self.fail(f"{n} at {c} obstructs a corridor lane")
        self.stats["lane_cells"] = len(st.lanes)
        return bad

    # -- docking column ---------------------------------------------------------
    def docking(self):
        st = self.st
        pads = [(x, z) for x in (-1, 0, 1) for z in (-1, 0, 1) if st.get((x, DECK, z)) == LAUNCH_PAD]
        if len(pads) != 9:
            self.fail(f"launch pad incomplete ({len(pads)}/9)")
        best = 0
        for x in range(-2, 3):
            for z in range(-2, 3):
                if abs(x) != 2 and abs(z) != 2:
                    continue
                h = 0
                while st.get((x, DECK + h, z)) == TOWER:
                    h += 1
                best = max(best, h)
        if best < 6:
            self.fail(f"service tower too short ({best})")
        self.stats["tower"] = best
        for c, (name, _, _) in st.blocks.items():
            if abs(c[0]) <= 2 and abs(c[2]) <= 2 and DECK < c[1] <= DECK + 12 and name != TOWER and name != AIR:
                self.fail(f"{name} at {c} blocks the docking column")
        for x in range(-2, 3):
            for z in range(-2, 3):
                for y in range(DECK + 1, DECK + 12):
                    if (x, y, z) in st.inner:
                        self.fail(f"docking column cell {(x, y, z)} is pressurised")

    # -- pressurised volume ---------------------------------------------------------
    def airtight(self):
        """Flood fill vacuum from outside the bounding box: it must never reach a pressurised cell, and every
        non-solid cell it cannot reach must be pressurised (closed doors count as seals)."""
        st = self.st
        xs = [c[0] for c in st.blocks]
        ys = [c[1] for c in st.blocks]
        zs = [c[2] for c in st.blocks]
        lo = (min(xs) - 1, min(ys) - 1, min(zs) - 1)
        hi = (max(xs) + 1, max(ys) + 1, max(zs) + 1)

        def passable(c):
            n = st.get(c)
            if n is None or n == AIR:
                return True
            if n in DOORS:
                return False
            if n in FULL_CUBES:
                return False
            if n in (QUARTZ_STAIRS, SQUARTZ_STAIRS, LAUNCH_PAD):
                return False
            if n in DESK_SLABS:
                return False
            return True     # furniture, signs, carpets ... do not seal
        seen = {lo}
        q = deque([lo])
        while q:
            c = q.popleft()
            for n in neighbours6(c):
                if not all(lo[i] <= n[i] <= hi[i] for i in range(3)) or n in seen:
                    continue
                if not passable(n):
                    continue
                seen.add(n)
                q.append(n)
        leaks = [c for c in st.inner if c in seen]
        for c in leaks[:20]:
            self.fail(f"pressurised cell {c} ({st.region.get(c)}) is open to vacuum")
        if len(leaks) > 20:
            self.fail(f"... {len(leaks)} leaking cells in total")
        trapped = [c for c, b in st.blocks.items() if b[0] == AIR and c not in seen and c not in st.inner]
        for c in trapped[:20]:
            self.fail(f"enclosed air at {c} is not pressurised")
        self.stats["pressurised_cells"] = len(st.inner)

    # -- circulation ---------------------------------------------------------
    def walkable(self, c):
        """A player (and later an NPC) can stand with its feet in cell c."""
        st = self.st
        if c not in st.inner:
            return False
        feet, head = st.get(c), st.get(st.above(c))
        below = st.below(c)
        soft = lambda n: n == AIR or n in NO_COLLISION_DECOR or (n or "").endswith("_carpet") \
            or n in DOORS
        if not soft(feet) or not (soft(head) or st.above(c) not in st.inner and head == AIR):
            return False
        if head not in (AIR,) and head not in NO_COLLISION_DECOR and head not in DOORS:
            return False
        bn = st.get(below)
        return bn in FULL_CUBES or bn in (QUARTZ_STAIRS, SQUARTZ_STAIRS) or bn in DESK_SLABS

    def reachability(self):
        st = self.st
        start = ARRIVAL
        if not self.walkable(start):
            self.fail(f"arrival {start} is not walkable")
            return
        seen = {start}
        q = deque([start])
        while q:
            c = q.popleft()
            x, y, z = c
            for dx, dz in DIRS.values():
                for dy in (0, 1, -1):
                    n = (x + dx, y + dy, z + dz)
                    if n in seen or not self.walkable(n):
                        continue
                    if dy == 1 and st.get(c[:1] + (y + 2,) + c[2:]) not in (AIR, None) and \
                            st.get((x, y + 2, z)) not in NO_COLLISION_DECOR:
                        continue
                    if dy == 1 and st.get((x + dx, y, z + dz)) not in (QUARTZ_STAIRS, SQUARTZ_STAIRS):
                        continue        # only stairs step up a full block
                    seen.add(n)
                    q.append(n)
        self.reach = seen
        unreached_rooms = []
        for key, reg in st.regions.items():
            if not any(c in seen for c in reg.cells):
                unreached_rooms.append(key)
        for key in unreached_rooms:
            self.fail(f"{key} cannot be reached from the arrival spot")
        # every piece of furniture that is used must be next to a reachable standing spot
        use = SEATS_FACING | CONTAINERS | {STOOL, CONSOLE, VENDING, JUKEBOX, STOVE, SINK, WORKBENCH, TAPE, SMITHING,
                                           STONECUTTER, REFINERY, LIQUEFIER, COMPOSTER, TELESCOPE, COMPUTER, O2_RACK,
                                           TV, PLANTER} | BEDS
        for c, (name, _, _) in st.blocks.items():
            if name not in use:
                continue
            x, y, z = c
            near = [(x + dx, y - k, z + dz) for dx, dz in DIRS.values() for k in range(3)]
            if name in BEDS or name in SEATS_FACING or name == STOOL:
                near.append(st.above(c))
            if name in BEDS:
                dx, dz = DIRS[st.props(c)["facing"]]
                sgn = 1 if st.props(c)["part"] == "foot" else -1
                if name == CREW_BUNK:
                    sgn = -sgn
                o = (x + sgn * dx, y, z + sgn * dz)
                near += [(o[0] + ex, y, o[2] + ez) for ex, ez in DIRS.values()]
            if not any(n in seen for n in near):
                self.fail(f"{name} at {c} cannot be reached")
        self.stats["walkable_reached"] = len(seen)

    # -- room programme ---------------------------------------------------------
    def requirements(self):
        st = self.st
        self.counts = {}
        for key, room in st.rooms.items():
            counts = {}
            for c in room.cells:
                n = st.get(c)
                if n is None:
                    continue
                counts[n] = counts.get(n, 0) + 1
            # windows / portholes belong to the hull around the room
            for c in room.cells:
                for nb in neighbours6(c):
                    if st.get(nb) in WINDOWS and nb not in room.cells:
                        counts.setdefault("_win", set()).add(nb)
            for w in counts.pop("_win", set()):
                counts[st.get(w)] = counts.get(st.get(w), 0) + 1
            for c in room.cells | {st.below(c) for c in room.cells}:
                if st.get(c) in (TINTED_GLASS, STRIPED) and c not in room.cells:
                    counts[st.get(c)] = counts.get(st.get(c), 0) + 1
            for c in [cc for cc in st.blocks if st.get(cc) == TINTED_GLASS]:
                if any(nb in room.cells for nb in neighbours6(c)):
                    counts[TINTED_GLASS] = counts.get(TINTED_GLASS, 0) + 1
            beds = sum(v for k, v in counts.items() if k in BEDS) // 2
            counts["bed"] = beds
            counts["carpet"] = sum(v for k, v in counts.items() if k.endswith("_carpet"))
            counts["seats"] = sum(counts.get(k, 0) for k in (SOFA, STOOL, EGG_CHAIR, CAPTAIN_CHAIR))
            counts["wall_clock_or_chart"] = counts.get(CLOCK, 0) + counts.get(STAR_CHART, 0)
            counts["locker"] = counts.get(CREW_LOCKER, 0) // 2
            counts["artifact"] = sum(v for k, v in counts.items() if k in ARTIFACTS)
            counts["vending"] = counts.get(VENDING, 0) // 2
            counts["poster"] = sum(v for k, v in counts.items() if k in POSTERS) // 2
            self.counts[key] = counts
            for item, need in REQUIRED.get(room.kind, {}).items():
                if counts.get(item, 0) < need:
                    self.fail(f"{key}: needs {need} x {item}, has {counts.get(item, 0)}")
        # supply chests near the docking area
        fuel = lox = 0
        for c, (name, _, nbt) in st.blocks.items():
            if name in STORAGE_BLOCKS and st.region.get(c) == "supply" and nbt is not None:
                for it in nbt["Items"]:
                    if it["id"] == FUEL:
                        fuel += it["count"]
                    if it["id"] == LOX:
                        lox += it["count"]
        if fuel < 16 or lox < 16:
            self.fail(f"supply stores hold {fuel} fuel / {lox} LOX canisters")
        self.stats["supply_fuel"], self.stats["supply_lox"] = fuel, lox


# ----------------------------------------------------------------------------
# Export
# ----------------------------------------------------------------------------
def bounds(st):
    xs = [p[0] for p in st.blocks]
    ys = [p[1] for p in st.blocks]
    zs = [p[2] for p in st.blocks]
    return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))


def pressurized_boxes(st):
    """Greedy decomposition of the interior cell set into inclusive boxes (structure coords)."""
    (ox, oy, oz), _ = bounds(st)
    cells = {(x - ox, y - oy, z - oz) for (x, y, z) in st.inner}
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
    # the boxes must cover exactly the interior
    covered = set()
    for x0, y0, z0, x1, y1, z1 in boxes:
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                for z in range(z0, z1 + 1):
                    covered.add((x, y, z))
    assert covered == cells, "pressurised boxes do not match the interior"
    return boxes


def to_nbt(st):
    (ox, oy, oz), (mx, my, mz) = bounds(st)
    palette_index = {}
    palette = List([], TAG_COMPOUND)
    blocks = List([], TAG_COMPOUND)
    for (x, y, z) in sorted(st.blocks, key=lambda c: (c[1], c[2], c[0])):
        name, props, nbt = st.blocks[(x, y, z)]
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


# NPC anchors (structure-local after normalisation): Dr. Cooper stands behind his desk, facing his visitors.
def npc_anchors(st):
    out = []
    for role, key, (u, v) in (("cooper", "archaeology", (3, 6)), ("decorator", "showroom", (5, 6))):
        room = st.rooms[key]
        pos = room.at(u, v)
        yaw = {"south": 0, "west": 90, "north": 180, "east": 270}[room.wdir("front")]
        out.append((role, pos, yaw, pos))
    return out


def check_npcs(st, checker):
    for role, pos, yaw, home in npc_anchors(st):
        if not (st.get(pos) == AIR and st.get(st.above(pos)) == AIR and st.is_full(st.below(pos))):
            checker.fail(f"npc {role} at {pos}: needs air with two blocks headroom on a solid floor")
        if pos not in getattr(checker, "reach", set()):
            checker.fail(f"npc {role} at {pos} cannot be reached from the arrival spot")


def anchors(st):
    (ox, oy, oz), (mx, my, mz) = bounds(st)
    ax, ay, az = ARRIVAL
    assert ARRIVAL in st.inner and st.get(ARRIVAL) == AIR and st.is_full(st.below(ARRIVAL))
    assert st.get((ax, ay + 1, az)) == AIR and st.get((ax, ay + 2, az)) == AIR
    return {
        "size": [mx - ox + 1, my - oy + 1, mz - oz + 1],
        "pad_center": [0 - ox, DECK - oy, 0 - oz],
        "arrival": [ax - ox, ay - oy, az - oz],
        "pressurized": pressurized_boxes(st),
        "npcs": [{"role": role, "pos": [p[0] - ox, p[1] - oy, p[2] - oz], "yaw": yaw,
                  "home": [h[0] - ox, h[1] - oy, h[2] - oz]} for role, p, yaw, h in npc_anchors(st)],
    }


# ----------------------------------------------------------------------------
# Validation against the mod's registered blockstates and the vanilla schemas above
# ----------------------------------------------------------------------------
def validate(st):
    states_dir = os.path.join(ROOT, "assets", "retrocosmos", "blockstates")
    problems = set()
    pending = set()
    cache = {}
    forbidden = {mc("water"), mc("lava"), mc("sand"), mc("gravel"), mc("anvil"), mc("spawner"), mc("scaffolding")}
    for (name, props, _nbt) in st.blocks.values():
        if name in forbidden or name.endswith("concrete_powder"):
            problems.add(f"{name} is not allowed in the station")
        if name in MOD_SCHEMAS:
            schema = MOD_SCHEMAS[name]
            if set(props) != set(schema) or any(v not in schema[k] for k, v in props.items()):
                problems.add(f"{name}{props}: does not match the fixed schema {schema}")
                continue
            short = name.split(":", 1)[1]
            path = os.path.join(states_dir, short + ".json")
            if not os.path.exists(path):
                pending.add(name)
                continue
            if short not in cache:
                with open(path, encoding="utf-8") as f:
                    cache[short] = json.load(f).get("variants")
            variants = cache[short]
            if variants is None:
                continue
            names = {kv.split("=")[0] for key in variants for kv in key.split(",") if kv}
            if not names <= set(schema) or set(schema) - names - {"powered"}:
                pending.add(name)       # blockstate file not updated to the new properties yet
                continue
            key = ",".join(f"{k}={v}" for k, v in sorted(props.items()) if k in names)
            if key not in variants:
                problems.add(f"{name}[{key}] has no blockstate variant")
            continue
        if name.startswith("retrocosmos:"):
            if name == LAUNCH_PAD and not props:
                continue            # stored plain; the game shapes the 3x3 after placement
            short = name.split(":", 1)[1]
            if short not in cache:
                path = os.path.join(states_dir, short + ".json")
                if not os.path.exists(path):
                    problems.add(f"{name}: no blockstate file")
                    cache[short] = None
                    continue
                with open(path, encoding="utf-8") as f:
                    cache[short] = json.load(f).get("variants")
            variants = cache[short]
            if variants is None:
                continue
            key = ",".join(f"{k}={v}" for k, v in sorted(props.items()))
            if key not in variants:
                problems.add(f"{name}[{key}] has no blockstate variant")
        elif name.startswith("minecraft:"):
            schema = VANILLA_PROPS.get(name)
            if schema is None:
                problems.add(f"{name}: not in the vanilla schema table")
                continue
            if set(props) != set(schema):
                problems.add(f"{name}: properties {sorted(props)} != {sorted(schema)}")
                continue
            for k, v in props.items():
                if v not in schema[k]:
                    problems.add(f"{name}: {k}={v} invalid")
        else:
            problems.add(f"unknown block {name}")
    if pending:
        print("station.py: blockstates not drawn yet, checked against the fixed schemas: " + ", ".join(sorted(pending)))
    if problems:
        raise SystemExit("station.py: invalid block states:\n  " + "\n  ".join(sorted(problems)))


def build_station():
    return Builder().build()


def report(st, checker):
    lines = []
    for key, room in st.rooms.items():
        c = checker.counts.get(key, {})
        interesting = {k.split(":")[1]: v for k, v in sorted(c.items()) if ":" in k and k not in (AIR,)
                       and not k.endswith("_carpet") and v}
        lines.append(f"  {key:14s} {room.label:30s} {room.U}x{room.V}  " +
                     ", ".join(f"{k} {v}" for k, v in interesting.items()))
    return "\n".join(lines)


def generate(verbose=False):
    st = build_station()
    validate(st)
    checker = Checker(st)
    problems = checker.run()
    check_npcs(st, checker)
    problems = checker.problems
    if problems:
        raise SystemExit("station.py: checker found problems:\n  " + "\n  ".join(problems[:200]) +
                         (f"\n  ... {len(problems)} in total" if len(problems) > 200 else ""))
    root = to_nbt(st)
    data = nbt_bytes(root)
    os.makedirs(os.path.dirname(STRUCTURE_FILE), exist_ok=True)
    with gzip.GzipFile(STRUCTURE_FILE, "wb", mtime=0) as f:
        f.write(data)
    with gzip.open(STRUCTURE_FILE, "rb") as f:
        name, back = nbt_parse(f.read())
    assert name == "" and back["DataVersion"] == DATA_VERSION
    assert list(back["size"]) == list(root["size"]) and len(back["blocks"]) == len(root["blocks"])
    assert len(back["palette"]) == len(root["palette"])
    anc = anchors(st)
    write_json(ANCHORS_FILE, anc)
    print(f"freedom_station: size {anc['size']}, {len(root['blocks'])} blocks, {len(root['palette'])} states, "
          f"{len(anc['pressurized'])} pressurized boxes, {len(st.rooms)} rooms, checker OK {checker.stats}")
    if verbose:
        print(report(st, checker))
    return st


if __name__ == "__main__":
    generate(verbose=True)
