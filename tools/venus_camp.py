"""Venus expedition camp ("VENUS BASE ONE") - a 1950s Earth expedition camp in the Venusian jungle.

Writes a vanilla structure template (data/retrocosmos/structure/venus_expedition_camp.nbt) and its anchors
(data/retrocosmos/venus_camp/expedition_camp.json): size, ground_y (the solid ground layer the game sets on the
levelled terrain), pad_center and the crew's NPC anchors.  Re-uses the NBT writer, block ids and the blockstate
validation of station.py.

Plan (structure-local X east, Z south, Y up; the camp centre is the origin before normalisation, ground at y 0):

    * Palisade of spruce posts around the camp (max-norm 17) with a gated arch in the south, floodlights on the
      corner and gate posts.  A packed-mud main street runs from the gate north to the launch pad, a cross street
      east-west in front of the tents.
    * North: launch pad on a hull deck (3x3 pad, service tower at dx = +2), the supply cache lean-to (RP-1, LOX,
      rations, empty canisters), fuel drums, the generator shed (portable reactor) and the watchtower.
    * West: the white command tent (radio station, map table, computers, the leader's cot) with the radio mast,
      and the flagpole of the Interplanetary Exploration Agency.  South-west: two olive bunk tents (8 berths).
    * East: the field laboratory under a striped awning (instruments, sink, workbench, lectern, hydroponic
      planters next to a test plot of Venusian plants, a telescope); south-east: iron-bar specimen pens and the
      mess awning with a long table and the camp kitchen.
    * NPC anchors: 3 guards (gate, watchtower, west perimeter), 4 scientists (radio, lab, hydroponics, pens).
"""
import gzip
import json
import math
import os
from collections import deque

import station as S
from station import AIR, mc, rc, nbt_bytes, nbt_parse, storage_nbt, sign_nbt
from gen_resources import DATA, write_json

STRUCTURE_FILE = os.path.join(DATA, "structure", "venus_expedition_camp.nbt")
ANCHORS_FILE = os.path.join(DATA, "venus_camp", "expedition_camp.json")

R = 20               # footprint half size (41 x 41)
GROUND = 0           # ground layer (structure-local y after normalisation is the same: nothing is built below)
WALL_R = 17          # palisade ring (max-norm)
PAD = (0, -10)       # launch pad centre (x, z)
MAX_HEIGHT = 20

# ----------------------------------------------------------------------------- blocks
W_WHITE, W_GREEN, W_LGRAY, W_RED = (mc(c + "_wool") for c in ("white", "green", "light_gray", "red"))
WOOLS = {W_WHITE, W_GREEN, W_LGRAY, W_RED}
LOG = mc("spruce_log")
PLANKS = S.SPRUCE
SLAB = S.SPRUCE_SLAB
FENCE = mc("spruce_fence")
GATE = mc("spruce_fence_gate")
BARS = mc("iron_bars")
LADDER = mc("ladder")
BANNER = mc("blue_wall_banner")
PACKED_MUD = mc("packed_mud")
V_SOIL, V_MOSS, V_MUD = rc("venus_soil"), rc("venus_moss"), rc("venus_mud")
PLANTS = [rc(n) for n in ("venus_sedge", "venus_horsetail", "venus_fire_lily", "venus_glowcap", "venus_cycad")]
SEDGE, HORSETAIL, FIRE_LILY, GLOWCAP, CYCAD = PLANTS
DIRT_TAG = {V_SOIL, V_MOSS, V_MUD}
FLOOD = S.FLOOR_LAMP

_B = ("true", "false")
S.VANILLA_PROPS.update({
    W_WHITE: {}, W_GREEN: {}, W_LGRAY: {}, W_RED: {}, PACKED_MUD: {},
    LOG: {"axis": ("x", "y", "z")},
    FENCE: {"north": _B, "east": _B, "south": _B, "west": _B, "waterlogged": _B},
    BARS: {"north": _B, "east": _B, "south": _B, "west": _B, "waterlogged": _B},
    GATE: {"facing": S.HORIZ, "in_wall": _B, "open": _B, "powered": _B},
    LADDER: {"facing": S.HORIZ, "waterlogged": _B},
    BANNER: {"facing": S.HORIZ},
    mc("campfire"): {"facing": S.HORIZ, "lit": _B, "signal_fire": _B, "waterlogged": _B},
})

# full opaque cubes that carry wall decor, lights, posters and count as walls
WALLS = S.WALL_BLOCKS | WOOLS | {LOG, PLANKS, PACKED_MUD, V_SOIL, V_MOSS, V_MUD}
# blocks with a full sturdy face on every side (fence / bar connections, supports)
STURDY = S.FULL_CUBES | WALLS | {S.LAUNCH_PAD, S.TOWER, S.BARREL, S.CRAFTING}
GROUND_OK = STURDY
WORK_BLOCKS = {S.RADAR_SCOPE, S.COMPUTER, S.CONTROL_PANEL, S.SINK, S.WORKBENCH, S.PLANTER, S.TELESCOPE, S.O2_RACK,
               S.BREWING, S.LECTERN, S.CAULDRON, S.COMPOSTER, S.CARTOGRAPHY, S.RADIO}
FUEL, LOX, EMPTY_CAN = S.FUEL, S.LOX, S.EMPTY_CAN
DIRS = S.DIRS
OPP = S.OPPOSITE
YAW = {"south": 0, "west": 90, "north": 180, "east": 270}


def banner_nbt():
    """Flag of the (fictional) Interplanetary Exploration Agency: white globe on blue with a red border."""
    pats = S.List([S.Compound({"color": S.Str("white"), "pattern": S.Str("minecraft:globe")}),
                   S.Compound({"color": S.Str("red"), "pattern": S.Str("minecraft:border")})], S.TAG_COMPOUND)
    return S.Compound({"id": S.Str("minecraft:banner"), "patterns": pats})


class Camp:
    def __init__(self):
        self.blocks = {}
        self.errors = []
        self.npcs = []          # (role, pos, yaw, home)
        self.zones = {}         # name -> (x0, z0, x1, z1) for previews / report
        self.supply_cells = set()

    # -- primitives ---------------------------------------------------------------
    def get(self, c):
        b = self.blocks.get(c)
        return b[0] if b else None

    def props(self, c):
        b = self.blocks.get(c)
        return b[1] if b else {}

    def put(self, c, name, props=None, nbt=None):
        self.blocks[c] = (name, dict(props or {}), nbt)

    def error(self, msg):
        self.errors.append(msg)

    def free(self, c):
        return self.get(c) in (None, AIR)

    def place(self, c, name, props=None, nbt=None):
        """Furniture / fittings: the cell must be free."""
        if not self.free(c):
            self.error(f"cannot place {name} at {c}: {self.get(c)}")
            return
        self.put(c, name, props, nbt)

    def fac(self, c, name, facing, lit=None, **extra):
        props = {"facing": facing}
        if lit is not None:
            props["lit"] = "true" if lit else "false"
        props.update(extra)
        self.place(c, name, props)

    def wall(self, c, name, facing, lit=None):
        """Wall decor hanging on the block behind it (opposite of facing)."""
        dx, dz = DIRS[facing]
        back = (c[0] - dx, c[1], c[2] - dz)
        if self.get(back) not in WALLS:
            self.error(f"{name} at {c} has no wall behind ({self.get(back)})")
        props = {"facing": facing}
        if lit is not None:
            props["lit"] = "true" if lit else "false"
        self.place(c, name, props)

    def desk(self, c, top=None, facing="north", lit=True):
        self.place(c, SLAB, {"type": "top", "waterlogged": "false"})
        if top is None:
            return
        up = (c[0], c[1] + 1, c[2])
        if top == S.BREWING:
            self.place(up, top, {"has_bottle_0": "true", "has_bottle_1": "true", "has_bottle_2": "false"})
        elif top in (S.GLOBE, S.TELESCOPE):
            self.fac(up, top, facing)
        elif top == S.LANTERN:
            self.place(up, top, {"hanging": "false", "waterlogged": "false"})
        else:
            self.fac(up, top, facing, lit=lit)

    def stool(self, c):
        self.place(c, S.STOOL)

    def tall(self, c, name, facing, lit=None, nbt=None):
        props = {"facing": facing}
        if lit is not None:
            props["lit"] = "true" if lit else "false"
        up = (c[0], c[1] + 1, c[2])
        self.place(c, name, dict(props, half="lower"), nbt)
        self.place(up, name, dict(props, half="upper"))

    def poster(self, c, name, facing):
        self.tall(c, name, facing)

    def locker(self, c, facing, items=()):
        self.tall(c, S.CREW_LOCKER, facing, nbt=storage_nbt(items))

    def bunk(self, foot, toward_head):
        """Crew bunk: facing = direction the foot end faces; the head lies one block behind the foot."""
        dx, dz = DIRS[toward_head]
        head = (foot[0] + dx, foot[1], foot[2] + dz)
        f = OPP[toward_head]
        self.place(foot, S.CREW_BUNK, {"facing": f, "part": "foot"})
        self.place(head, S.CREW_BUNK, {"facing": f, "part": "head"})

    def cabinet(self, c, facing, items):
        self.place(c, S.SUPPLY_CABINET, {"facing": facing}, storage_nbt(items))

    def crate(self, c, items):
        self.place(c, S.CARGO_CRATE, None, storage_nbt(items))

    def lantern_hanging(self, c):
        self.place(c, S.LANTERN, {"hanging": "true", "waterlogged": "false"})

    def sign(self, c, facing, lines):
        dx, dz = DIRS[facing]
        if self.get((c[0] - dx, c[1], c[2] - dz)) not in WALLS:
            self.error(f"sign {lines} at {c} has no wall")
        self.place(c, S.WALL_SIGN, {"facing": facing, "waterlogged": "false"}, sign_nbt(lines))

    def standing_sign(self, c, facing, lines):
        rot = {"south": 0, "west": 4, "north": 8, "east": 12}[facing]
        self.place(c, S.STANDING_SIGN, {"rotation": str(rot), "waterlogged": "false"}, sign_nbt(lines))

    def log(self, c, axis="y"):
        self.put(c, LOG, {"axis": axis})

    def npc(self, role, pos, facing):
        self.npcs.append((role, pos, YAW[facing], pos))

    # ------------------------------------------------------------------ structures
    def tent(self, xc, k, z0, z1, canvas, ridge, door_end, door_half):
        """A-frame tent along z: side walls 2 high at |dx| = k, roof steps up to the ridge at xc, gable walls at
        both ends, a doorway (|dx| <= door_half, 2 high) in the `door_end` gable.  Plank floor."""
        for z in range(z0, z1 + 1):
            for d in range(-k, k + 1):
                x = xc + d
                self.put((x, GROUND, z), PLANKS)
                if abs(d) == k:
                    for y in (1, 2):
                        self.put((x, y, z), canvas)
                    continue
                roof = 2 + (k - abs(d))
                self.put((x, roof, z), ridge if d == 0 else canvas)
                if z in (z0, z1):
                    for y in range(1, roof):
                        door = z == door_end and abs(d) <= door_half and y <= 2
                        if not door:
                            self.put((x, y, z), canvas)

    def awning(self, x0, z0, x1, z1, y, colors=(W_RED, W_WHITE)):
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                self.put((x, y, z), colors[(x - x0) % 2])

    # ------------------------------------------------------------------ layout
    def build(self):
        self.ground()
        self.palisade()
        self.launch_pad()
        self.supply_cache()
        self.generator_shed()
        self.watchtower()
        self.command_tent()
        self.radio_mast_and_flag()
        self.bunk_tents()
        self.field_lab()
        self.specimen_pens()
        self.mess()
        self.scenery()
        self.connections()
        return self

    def ground(self):
        for x in range(-R, R + 1):
            for z in range(-R, R + 1):
                m = max(abs(x), abs(z))
                self.put((x, GROUND, z), V_MOSS if m > WALL_R else V_SOIL)
        for z in range(-5, R + 1):                  # main street, gate -> pad
            for x in (-1, 0, 1):
                self.put((x, GROUND, z), PACKED_MUD)
        for x in range(-16, 17):                    # cross street in front of the tents and the lab
            for z in (5, 6):
                self.put((x, GROUND, z), PACKED_MUD)

    def palisade(self):
        for x in range(-WALL_R, WALL_R + 1):
            for z in range(-WALL_R, WALL_R + 1):
                if max(abs(x), abs(z)) != WALL_R or (z == WALL_R and abs(x) <= 1):
                    continue
                top = 4 if (x + z) % 2 == 0 else 3
                if z == WALL_R and abs(x) == 2:
                    top = 4
                for y in range(1, top + 1):
                    self.log((x, y, z))
                corner = abs(x) == WALL_R and abs(z) == WALL_R
                mid = (x == 0 or z == 0) and not (z == WALL_R)
                if corner or mid:
                    self.place((x, top + 1, z), FLOOD, {"lit": "true"})
        # gate: open fence gates under an arch, floodlights and the camp sign
        for x in (-1, 0, 1):
            self.place((x, 1, WALL_R), GATE, {"facing": "south", "in_wall": "false", "open": "true", "powered": "false"})
        for x in range(-2, 3):
            self.log((x, 5, WALL_R), "x")
        for x in (-2, 2):
            self.place((x, 6, WALL_R), FLOOD, {"lit": "true"})
        self.sign((0, 5, WALL_R + 1), "south", ["EARTH", "EXPEDITION", "VENUS BASE ONE", "I.E.A. 1958"])
        self.sign((0, 5, WALL_R - 1), "north", ["VENUS BASE ONE", "", "SIGN OUT AT", "THE GATE"])
        self.npc("guard", (0, 1, WALL_R - 2), "south")
        self.npc("guard", (-16, 1, 8), "west")
        self.zones["Gate"] = (-2, 16, 2, 18)

    def launch_pad(self):
        px, pz = PAD
        for x in range(px - 4, px + 5):
            for z in range(pz - 4, pz + 5):
                dx, dz = x - px, z - pz
                r = math.hypot(dx, dz)
                if max(abs(dx), abs(dz)) == 4:
                    name = S.YELLOW if ((x + z) // 2) % 2 else S.BLACK
                elif 2.5 < r <= 3.5:
                    name = S.RED
                else:
                    name = S.HULL
                self.put((x, GROUND, z), name)
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                self.put((px + dx, GROUND, pz + dz), S.LAUNCH_PAD)        # plain; the game shapes the 3x3
        for y in range(GROUND, GROUND + 8):
            self.put((px + 2, y, pz), S.TOWER)
        for x, z in ((px - 4, pz - 4), (px + 4, pz - 4), (px - 4, pz + 4), (px + 4, pz + 4)):
            self.place((x, 1, z), FLOOD, {"lit": "true"})
        self.standing_sign((px - 3, 1, pz + 5), "south", ["LAUNCH PAD", "KEEP CLEAR", "DURING", "LANDING"])
        self.zones["Launch pad"] = (px - 4, pz - 4, px + 4, pz + 4)

    def supply_cache(self):
        x0, x1, z0, z1 = -10, -6, -14, -9
        for z in range(z0, z1 + 1):
            for x in range(x0, x1 + 1):
                self.put((x, GROUND, z), PLANKS)
                self.put((x, 4, z), W_GREEN)                # tarp
            for y in (1, 2, 3):
                self.put((x0, y, z), PLANKS)                 # back wall
        for z in (z0, z1):
            for y in (1, 2, 3):
                self.log((x1, y, z))
        self.cabinet((-9, 1, -13), "east", [(FUEL, 16), (FUEL, 16), (EMPTY_CAN, 8)])
        self.cabinet((-9, 1, -12), "east", [(LOX, 16), (LOX, 16), (EMPTY_CAN, 8)])
        self.crate((-9, 1, -11), [("minecraft:bread", 32), ("minecraft:cooked_beef", 16), ("minecraft:apple", 16),
                                  ("minecraft:dried_kelp", 32)])
        self.crate((-9, 2, -11), [("minecraft:baked_potato", 16), ("minecraft:cookie", 16)])
        self.crate((-9, 1, -10), [(EMPTY_CAN, 16), (EMPTY_CAN, 16), ("minecraft:bucket", 2)])
        self.crate((-9, 2, -10), [(FUEL, 8), (LOX, 8)])
        self.crate((-9, 1, -14), [("minecraft:torch", 32), ("minecraft:lantern", 4)])
        self.sign((-9, 3, -12), "east", ["SUPPLY CACHE", "RP-1 - LOX", "RATIONS", "SIGN THE LOG"])
        for c in ((-9, 1, -13), (-9, 1, -12), (-9, 1, -11), (-9, 2, -11), (-9, 1, -10), (-9, 2, -10), (-9, 1, -14)):
            self.supply_cells.add(c)
        # fuel drums
        for c in ((-8, 1, -7), (-7, 1, -7), (-8, 1, -6), (-8, 2, -7)):
            self.place(c, S.BARREL, {"facing": "up", "open": "false"})
        self.zones["Supply cache"] = (x0, z0, x1, z1)

    def generator_shed(self):
        x0, x1, z0, z1 = -16, -12, -16, -12
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                edge = x in (x0, x1) or z in (z0, z1)
                self.put((x, GROUND, z), S.STRIPED if not edge else S.HULL)
                self.put((x, 4, z), S.HULL)
                if edge:
                    for y in (1, 2, 3):
                        self.put((x, y, z), S.ALU if y != 3 else S.STRIPED)
        door = (x1, 1, -14)
        self.put(door, AIR)
        self.put((x1, 2, -14), AIR)
        self.place(door, S.STATION_DOOR, {"facing": "east", "half": "lower", "hinge": "left", "open": "false",
                                          "powered": "false"})
        self.place((x1, 2, -14), S.STATION_DOOR, {"facing": "east", "half": "upper", "hinge": "left", "open": "false",
                                                  "powered": "false"})
        for y in (1, 2):
            self.place((-14, y, -14), S.REACTOR, {"lit": "true"})
        self.place((-14, 3, -14), S.CHROME, {"axis": "y"})
        for y in (5, 6, 7):
            self.put((-14, y, -14), S.CHROME, {"axis": "y"})          # exhaust stack through the roof
        self.put((-14, 4, -14), S.CHROME, {"axis": "y"})
        self.desk((-15, 1, -13))
        self.wall((-15, 2, -13), S.CONTROL_PANEL, "east", lit=True)
        self.place((-13, 3, -15), S.CEILING_LIGHT, {"lit": "true"})
        self.sign((x1 + 1, 3, -14), "east", ["GENERATOR", "DANGER", "HIGH VOLTAGE", ""])
        self.zones["Generator"] = (x0, z0, x1, z1)

    def watchtower(self):
        x0, x1, z0, z1 = 12, 15, -16, -13
        for x, z in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)):
            for y in range(1, 10):
                self.log((x, y, z))
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                if (x, z) in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)):
                    continue
                self.put((x, 7, z), PLANKS)
                if x in (x0, x1) or z in (z0, z1):
                    if (x, z) != (13, z1):
                        self.put((x, 8, z), FENCE, {})
                self.put((x, 10, z), SLAB, {"type": "bottom", "waterlogged": "false"})
        for x, z in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)):
            self.put((x, 10, z), SLAB, {"type": "bottom", "waterlogged": "false"})
        for y in range(1, 8):                       # ladder on the inside of the south-west leg
            self.put((13, y, z1), LADDER, {"facing": "east", "waterlogged": "false"})
        self.place((14, 8, -15), FLOOD, {"lit": "true"})
        self.npc("guard", (13, 1, z1 + 1), "south")
        self.zones["Watchtower"] = (x0, z0, x1, z1)

    def command_tent(self):
        xc, z0, z1 = -12, -4, 4
        self.tent(xc, 3, z0, z1, W_WHITE, W_LGRAY, door_end=z1, door_half=1)
        # radio station at the back gable: radio, radar repeater, panel on the canvas wall
        self.desk((-13, 1, -3), S.RADAR_SCOPE, "south")
        self.desk((-12, 1, -3), S.RADIO, "south")
        self.desk((-11, 1, -3))
        self.wall((-11, 2, -3), S.CONTROL_PANEL, "south", lit=True)
        self.stool((-13, 1, -2))
        self.npc("scientist", (-12, 1, -2), "north")
        # computers on the east wall, map table in the middle, leader's cot and footlocker on the west wall
        self.fac((-10, 1, -1), S.COMPUTER, "west", lit=True)
        self.fac((-10, 1, 0), S.COMPUTER, "west", lit=False)
        self.place((-12, 1, 1), S.CARTOGRAPHY)
        self.stool((-11, 1, 1))
        self.bunk((-14, 1, 2), "south")
        self.locker((-14, 1, 1), "east", [("minecraft:paper", 16), ("minecraft:map", 2)])
        self.poster((-14, 1, -1), S.P_LIFTOFF, "east")
        for z in (-2, 2):
            self.lantern_hanging((xc, 4, z))
        self.sign((xc, 3, z1 + 1), "south", ["COMMAND", "& RADIO", "", ""])
        self.zones["Command tent"] = (xc - 3, z0, xc + 3, z1)

    def radio_mast_and_flag(self):
        mx, mz = -7, -3
        for x in (mx - 1, mx, mx + 1):
            for z in (mz - 1, mz, mz + 1):
                self.put((x, GROUND, z), S.GRAY)
        for y in range(1, 16):
            self.put((mx, y, mz), S.CHROME, {"axis": "y"})
        self.put((mx, 16, mz), S.LIGHTNING_ROD, {"facing": "up", "powered": "false", "waterlogged": "false"})
        for d in S.HORIZ:
            dx, dz = DIRS[d]
            self.put((mx + dx, 13, mz + dz), S.END_ROD, {"facing": d})
        for d in ("east", "west"):
            dx, dz = DIRS[d]
            self.put((mx + dx, 10, mz + dz), S.END_ROD, {"facing": d})
        self.put((mx, 11, mz), S.SEA_LANTERN)
        # flagpole on the corner of the main street
        fx, fz = -3, 3
        self.put((fx, GROUND, fz), S.GRAY)
        for y in range(1, 10):
            self.put((fx, y, fz), S.CHROME, {"axis": "y"})
        self.put((fx, 10, fz), S.LIGHTNING_ROD, {"facing": "up", "powered": "false", "waterlogged": "false"})
        self.place((fx + 1, 9, fz), BANNER, {"facing": "east"}, banner_nbt())
        self.zones["Radio mast"] = (mx - 1, mz - 1, mx + 1, mz + 1)

    def bunk_tents(self):
        for i, xc in enumerate((-13, -7)):
            z0, z1 = 9, 15
            self.tent(xc, 2, z0, z1, W_GREEN, W_GREEN, door_end=z0, door_half=0)
            for side, face in ((-1, "east"), (1, "west")):
                x = xc + side
                self.bunk((x, 1, 11), "north")      # head against the entrance gable
                self.bunk((x, 1, 13), "south")      # head against the back gable
                self.locker((x, 1, 12), face, [("minecraft:bread", 4)])
            self.lantern_hanging((xc, 3, 12))
            self.poster((xc, 1, 14), (S.P_HOMESTEAD, S.P_SPACE_POP)[i], "north")
            for z in (10, 11, 12, 13):
                self.place((xc, 1, z), S.carpet_id("red" if i else "light_blue"))
            self.zones[f"Bunk tent {i + 1}"] = (xc - 2, z0, xc + 2, z1)

    def field_lab(self):
        x0, x1, z0, z1 = 5, 15, -4, 3
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                self.put((x, GROUND, z), PLANKS)
        for z in range(z0, z1 + 1):
            for y in (1, 2, 3):
                self.put((x1, y, z), PLANKS)                 # back wall
        for x in range(x0, x1):
            for y in (1, 2, 3):
                self.put((x, y, z0), PLANKS)                 # side wall
        for x in (x0, 10):
            for y in (1, 2, 3):
                self.log((x, y, z1))
        self.awning(x0, z0, x1, z1, 4)
        # instruments along the back wall
        self.fac((14, 1, -3), S.COMPUTER, "west", lit=True)
        self.fac((14, 1, -2), S.COMPUTER, "west", lit=False)
        self.desk((14, 1, -1))
        self.wall((14, 2, -1), S.CONTROL_PANEL, "west", lit=True)
        self.desk((14, 1, 0), S.RADAR_SCOPE, "west")
        self.fac((14, 1, 1), S.SINK, "west")
        self.fac((14, 1, 2), S.O2_RACK, "west")
        self.poster((14, 1, 3), S.P_SUIT_CHECK, "west")
        # benches along the side wall: microscopes (brewing stands), specimen bath, notes, workbench, compost
        self.desk((6, 1, -3), S.BREWING)
        self.place((7, 1, -3), S.CAULDRON)
        self.desk((8, 1, -3), S.LAMP, "south", lit=False)
        self.fac((9, 1, -3), S.LECTERN, "south", has_book="false", powered="false")
        self.fac((10, 1, -3), S.WORKBENCH, "south")
        self.place((11, 1, -3), S.COMPOSTER, {"level": "0"})
        self.cabinet((12, 1, -3), "south", [("minecraft:glass_bottle", 16), ("minecraft:paper", 16), ("minecraft:shears", 1)])
        self.stool((6, 1, -2))
        self.stool((8, 1, -2))
        self.npc("scientist", (10, 1, -2), "north")
        # hydroponic planters with grow lights, test plot of Venusian plants in front of them
        for x in range(7, 12):
            self.place((x, 1, 0), S.PLANTER, {"lit": "true"})
            self.put((x, GROUND, 2), V_SOIL)
            self.place((x, 1, 2), (FIRE_LILY, SEDGE, GLOWCAP, HORSETAIL, FIRE_LILY)[x - 7])
        for x in (7, 9, 11):
            self.place((x, 3, 0), S.CEILING_LIGHT, {"lit": "true"})
        self.npc("scientist", (9, 1, 1), "north")
        self.fac((6, 1, 2), S.TELESCOPE, "south")
        self.sign((x0, 3, z1 + 1), "south", ["FIELD", "LABORATORY", "", ""])
        self.zones["Field lab"] = (x0, z0, x1, z1)

    def specimen_pens(self):
        x0, x1, z0, z1 = 11, 15, 8, 16
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                ring = x in (x0, x1) or z in (z0, 12, z1)
                if ring:
                    for y in (1, 2):
                        self.put((x, y, z), BARS, {})
        pen1 = [FIRE_LILY, GLOWCAP, None, GLOWCAP, None, FIRE_LILY, None, FIRE_LILY, GLOWCAP]
        pen2 = [HORSETAIL, SEDGE, CYCAD, None, HORSETAIL, SEDGE, CYCAD, None, HORSETAIL]
        for k, (x, z) in enumerate((x, z) for z in (9, 10, 11) for x in (12, 13, 14)):
            if pen1[k]:
                self.place((x, 1, z), pen1[k])
        for k, (x, z) in enumerate((x, z) for z in (13, 14, 15) for x in (12, 13, 14)):
            if pen2[k]:
                self.place((x, 1, z), pen2[k])
        self.fac((9, 1, 10), S.LECTERN, "east", has_book="false", powered="false")
        self.standing_sign((9, 1, 13), "east", ["SPECIMEN", "PENS", "DO NOT FEED", "THE FLORA"])
        self.npc("scientist", (10, 1, 11), "east")
        self.zones["Specimen pens"] = (x0, z0, x1, z1)

    def mess(self):
        x0, x1, z0, z1 = 2, 8, 9, 15
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                self.put((x, GROUND, z), PLANKS)
            for y in (1, 2):
                self.put((x, y, z1), PLANKS)                 # kitchen wall
        for x, z in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)):
            for y in (1, 2, 3):
                self.log((x, y, z))
        self.awning(x0, z0, x1, z1, 4, (W_GREEN, W_WHITE))
        for x in (4, 5, 6):
            self.fac((x, 1, 11), S.TABLE, "north")
            self.stool((x, 1, 10))
            self.stool((x, 1, 12))
        self.stool((3, 1, 11))
        self.stool((7, 1, 11))
        self.fac((3, 1, 14), S.STOVE, "north", lit=False)
        self.fac((4, 1, 14), S.SINK, "north")
        self.cabinet((5, 1, 14), "north", [("minecraft:bread", 16), ("minecraft:cooked_chicken", 8), ("minecraft:apple", 8)])
        self.desk((6, 1, 14), S.RADIO, "north", lit=True)
        self.place((7, 1, 14), S.BARREL, {"facing": "up", "open": "false"})
        self.poster((8, 1, 14), S.P_VESPER, "north")
        self.lantern_hanging((5, 3, 11))
        self.sign((x0, 3, z0 - 1), "north", ["MESS", "", "", ""])
        self.zones["Mess"] = (x0, z0, x1, z1)

    def scenery(self):
        # side roads to every entrance (only where the ground is still bare soil)
        roads = [(x, -5) for x in range(-13, 14)] + [(-11, z) for z in range(-14, -5)] + [(13, z) for z in range(-12, -5)]
        roads += [(x, z) for x in (-13, -7) for z in (7, 8)] + [(x, 7) for x in range(9, 12)]
        for x, z in roads:
            if self.get((x, GROUND, z)) == V_SOIL:
                self.put((x, GROUND, z), PACKED_MUD)
        for x, z in ((-4, -2), (-5, -1), (3, 8), (-16, 3), (16, -8), (15, 7), (-3, 13)):       # puddles
            if self.get((x, GROUND, z)) == V_SOIL and self.free((x, 1, z)):
                self.put((x, GROUND, z), V_MUD)
        # campfire with log benches between the pad and the lab - the crew's evening spot
        self.place((3, 1, -1), mc("campfire"), {"facing": "north", "lit": "true", "signal_fire": "false",
                                               "waterlogged": "false"})
        self.log((3, 1, -3), "x")
        self.log((3, 1, 1), "x")
        # equipment yard north of the pad: crates stacked against the palisade, spare oxygen racks
        for x, h in ((-4, 2), (-3, 1), (5, 2), (6, 1)):
            for y in range(1, h + 1):
                self.crate((x, y, -16), [("minecraft:iron_ingot", 8)])
        for x in (8, 9, 10):
            self.fac((x, 1, -16), S.O2_RACK, "south")
        # floodlights at the crossroads and Venusian plants outside the palisade
        self.place((2, 1, 4), FLOOD, {"lit": "true"})
        self.place((-4, 1, 7), FLOOD, {"lit": "true"})
        k = 0
        for x in range(-R, R + 1):
            for z in range(-R, R + 1):
                if max(abs(x), abs(z)) >= WALL_R + 2 and (x * 7 + z * 13) % 5 == 0 and abs(x) > 2:
                    self.place((x, 1, z), PLANTS[k % len(PLANTS)])
                    k += 1

    # ------------------------------------------------------------------ connections (fences, bars)
    def connections(self):
        for c, (name, props, nbt) in list(self.blocks.items()):
            if name not in (FENCE, BARS):
                continue
            p = {"waterlogged": "false"}
            for d, (dx, dz) in DIRS.items():
                n = (c[0] + dx, c[1], c[2] + dz)
                nn = self.get(n)
                if name == FENCE:
                    conn = nn == FENCE or nn in STURDY or (nn == GATE and self.gate_faces(n, d))
                else:
                    conn = nn == BARS or nn in STURDY
                p[d] = "true" if conn else "false"
            self.blocks[c] = (name, p, nbt)

    def gate_faces(self, gate, d):
        f = self.props(gate)["facing"]
        return (DIRS[f][0] == 0) == (DIRS[d][0] != 0)


# ----------------------------------------------------------------------------- checker
class CampChecker:
    def __init__(self, camp):
        self.c = camp
        self.problems = list(camp.errors)
        self.stats = {}

    def fail(self, m):
        self.problems.append(m)

    def run(self):
        c = self.c
        self.footprint()
        self.supports()
        self.connections()
        self.furniture()
        self.pad()
        self.supply()
        self.npcs()
        return self.problems

    def footprint(self):
        c = self.c
        xs = [p[0] for p in c.blocks]
        ys = [p[1] for p in c.blocks]
        zs = [p[2] for p in c.blocks]
        if max(xs) - min(xs) + 1 > 41 or max(zs) - min(zs) + 1 > 41:
            self.fail("footprint larger than 41 x 41")
        if max(ys) - min(ys) + 1 > MAX_HEIGHT:
            self.fail(f"camp is {max(ys) - min(ys) + 1} tall")
        if min(ys) != GROUND:
            self.fail("blocks below the ground layer")
        for x in range(-R, R + 1):
            for z in range(-R, R + 1):
                if c.get((x, GROUND, z)) not in GROUND_OK:
                    self.fail(f"ground layer at {(x, z)} is {c.get((x, GROUND, z))}")
        forbidden = {mc("sand"), mc("gravel"), mc("red_sand"), mc("anvil"), mc("water"), mc("lava"), mc("spawner"),
                     mc("scaffolding"), mc("pointed_dripstone")}
        for p, (n, _, _) in c.blocks.items():
            if n in forbidden or n.endswith("concrete_powder"):
                self.fail(f"{n} at {p} is not allowed")

    def supports(self):
        c = self.c
        for p, (n, pr, nbt) in c.blocks.items():
            x, y, z = p
            below, above = (x, y - 1, z), (x, y + 1, z)
            if n in S.WALL_DECOR or n in (S.WALL_SIGN, BANNER):
                dx, dz = DIRS[pr["facing"]]
                if c.get((x - dx, y, z - dz)) not in WALLS:
                    self.fail(f"{n} at {p} hangs on {c.get((x - dx, y, z - dz))}")
            if n == LADDER:
                dx, dz = DIRS[pr["facing"]]
                if c.get((x - dx, y, z - dz)) not in STURDY:
                    self.fail(f"ladder at {p} has no support")
            if n in S.CEILING_HUNG and c.get(above) not in WALLS:
                self.fail(f"{n} at {p} has no ceiling")
            if n == S.LANTERN:
                need = above if pr["hanging"] == "true" else below
                if c.get(need) not in STURDY:
                    self.fail(f"lantern at {p} unsupported")
            if n == S.STANDING_SIGN and c.get(below) not in STURDY:
                self.fail(f"standing sign at {p} unsupported")
            if n.endswith("_carpet") and c.get(below) in (None, AIR):
                self.fail(f"carpet at {p} floats")
            if n in PLANTS and c.get(below) not in DIRT_TAG:
                self.fail(f"{n} at {p} is not planted in soil ({c.get(below)})")
            if n in S.DOORS:
                other = above if pr["half"] == "lower" else below
                if c.get(other) != n or c.props(other).get("half") == pr["half"]:
                    self.fail(f"door at {p} not paired")
                if pr["half"] == "lower" and c.get(below) not in STURDY:
                    self.fail(f"door at {p} stands on {c.get(below)}")
            if n in S.TALL:
                other = above if pr["half"] == "lower" else below
                op = c.props(other)
                if c.get(other) != n or op.get("half") == pr["half"] or op.get("facing") != pr["facing"] \
                        or op.get("lit") != pr.get("lit"):
                    self.fail(f"two-tall {n} at {p} not paired")
                if pr["half"] == "upper" and nbt is not None:
                    self.fail(f"upper {n} at {p} carries data")
            if n == S.CREW_BUNK:
                dx, dz = DIRS[pr["facing"]]
                sgn = -1 if pr["part"] == "foot" else 1
                o = (x + sgn * dx, y, z + sgn * dz)
                if c.get(o) != n or c.props(o).get("part") == pr["part"] or c.props(o).get("facing") != pr["facing"]:
                    self.fail(f"bunk at {p} not paired")
                if c.get(below) not in STURDY:
                    self.fail(f"bunk at {p} on {c.get(below)}")
                if pr["part"] == "head" and not any(c.get((x + ex, y, z + ez)) in WALLS for ex, ez in DIRS.values()):
                    self.fail(f"bunk head at {p} not against a wall")
            if n in (S.SUPPLY_CABINET, S.CARGO_CRATE) and nbt is None:
                self.fail(f"{n} at {p} without storage data")

    def connections(self):
        c = self.c
        for p, (n, pr, _) in c.blocks.items():
            if n not in (FENCE, BARS):
                continue
            for d, (dx, dz) in DIRS.items():
                nn = c.get((p[0] + dx, p[1], p[2] + dz))
                if nn not in (None, AIR, FENCE, BARS, GATE) and nn not in STURDY and nn not in PLANTS \
                        and nn not in (FLOOD, LADDER):
                    self.fail(f"{n} at {p} touches {nn}: connection not certain")

    def furniture(self):
        c = self.c
        desk = lambda q: c.get(q) in S.DESK_BLOCKS or (c.get(q) in S.DESK_SLABS and c.props(q).get("type") == "top")
        targets = {S.TABLE, S.CARTOGRAPHY, S.COMPUTER, S.CONSOLE} | S.DESK_BLOCKS
        for p, (n, pr, _) in c.blocks.items():
            x, y, z = p
            if n in S.ON_DESK and pr.get("hanging") != "true" and not desk((x, y - 1, z)):
                self.fail(f"{n} at {p} is not on a desk")
            if n == S.CONTROL_PANEL and not desk((x, y - 1, z)):
                self.fail(f"control panel at {p} not above a desk")
            if n == S.STOOL and not any(c.get((x + dx, y, z + dz)) in targets or desk((x + dx, y, z + dz))
                                        for dx, dz in DIRS.values()):
                self.fail(f"stool at {p} next to nothing")
            if n in (S.COMPUTER, S.SINK, S.STOVE, S.O2_RACK, S.SUPPLY_CABINET):
                dx, dz = DIRS[pr["facing"]]
                if c.get((x - dx, y, z - dz)) not in WALLS:
                    self.fail(f"{n} at {p} has no wall behind")

    def pad(self):
        c = self.c
        px, pz = PAD
        if sum(c.get((px + dx, GROUND, pz + dz)) == S.LAUNCH_PAD for dx in (-1, 0, 1) for dz in (-1, 0, 1)) != 9:
            self.fail("launch pad incomplete")
        h = 0
        while c.get((px + 2, GROUND + h, pz)) == S.TOWER:
            h += 1
        if h < 6:
            self.fail(f"tower {h}")
        for (x, y, z), (n, _, _) in c.blocks.items():
            if abs(x - px) <= 2 and abs(z - pz) <= 2 and GROUND < y <= GROUND + 12 and n not in (S.TOWER, AIR):
                self.fail(f"{n} at {(x, y, z)} blocks the landing column")
        self.stats["tower"] = h

    def supply(self):
        tot = {}
        for p in self.c.supply_cells:
            nbt = self.c.blocks[p][2]
            for it in nbt["Items"]:
                tot[str(it["id"])] = tot.get(str(it["id"]), 0) + int(it["count"])
        need = {FUEL: 8, LOX: 8, EMPTY_CAN: 1}
        for k, v in need.items():
            if tot.get(k, 0) < v:
                self.fail(f"supply cache holds {tot.get(k, 0)} {k}")
        if not any(k.startswith("minecraft:") and k not in ("minecraft:bucket", "minecraft:torch") for k in tot):
            self.fail("supply cache holds no food")
        self.stats["cache_fuel"], self.stats["cache_lox"] = tot.get(FUEL, 0), tot.get(LOX, 0)

    def walkable(self, p):
        c = self.c
        soft = lambda n: n in (None, AIR) or n in S.NO_COLLISION_DECOR or (n or "").endswith("_carpet") \
            or n in PLANTS or n == LADDER or (n == GATE and c.props(p).get("open") == "true") or n in S.DOORS
        x, y, z = p
        if not soft(c.get(p)) or not soft(c.get((x, y + 1, z))):
            return False
        if c.get(p) == GATE and c.props(p).get("open") != "true":
            return False
        b = c.get((x, y - 1, z))
        return b in STURDY or (b in S.DESK_SLABS and c.props((x, y - 1, z)).get("type") == "top") or b == LADDER

    def npcs(self):
        c = self.c
        start = (0, 1, R)
        seen = {start}
        q = deque([start])
        while q:
            x, y, z = q.popleft()
            for dx, dz in DIRS.values():
                for dy in (0, 1, -1):
                    n = (x + dx, y + dy, z + dz)
                    if n in seen or not (-R <= n[0] <= R and -R <= n[2] <= R and 1 <= n[1] < MAX_HEIGHT):
                        continue
                    if not self.walkable(n):
                        continue
                    if dy == 1 and c.get((x, y + 2, z)) not in (None, AIR):
                        continue
                    seen.add(n)
                    q.append(n)
            if c.get((x, y, z)) == LADDER:          # climbing
                for dy in (1, -1):
                    n = (x, y + dy, z)
                    if n not in seen and (c.get(n) == LADDER or self.walkable(n)):
                        seen.add(n)
                        q.append(n)
        self.stats["reachable_cells"] = len(seen)
        roles = {}
        for role, pos, yaw, home in c.npcs:
            roles[role] = roles.get(role, 0) + 1
            x, y, z = pos
            if not (c.free(pos) and c.free((x, y + 1, z)) and c.get((x, y - 1, z)) in STURDY):
                self.fail(f"npc {role} at {pos}: needs air, 2 headroom and a solid floor")
            if pos not in seen:
                self.fail(f"npc {role} at {pos} cannot be reached from the gate")
            if role == "scientist":
                work = sum(1 for p, b in c.blocks.items() if b[0] in WORK_BLOCKS and math.dist(p, pos) <= 12)
                if work < 3:
                    self.fail(f"scientist at {pos} has only {work} work blocks around")
        if roles.get("guard", 0) != 3 or not 3 <= roles.get("scientist", 0) <= 4:
            self.fail(f"npc roles {roles}")
        for p, (n, _, _) in c.blocks.items():
            if n in (S.CREW_LOCKER, S.SUPPLY_CABINET, S.CARGO_CRATE, S.STOVE, S.SINK, S.COMPUTER, S.WORKBENCH,
                     S.RADAR_SCOPE, S.LECTERN, S.CARTOGRAPHY, S.TELESCOPE, S.PLANTER) and c.props(p).get("half") != "upper":
                x, y, z = p
                if not any((x + dx, y - k, z + dz) in seen for dx, dz in DIRS.values() for k in range(3)):
                    self.fail(f"{n} at {p} cannot be reached")


# ----------------------------------------------------------------------------- export
def build_camp():
    return Camp().build()


def anchors(camp):
    (ox, oy, oz), (mx, my, mz) = S.bounds(camp)
    loc = lambda p: [p[0] - ox, p[1] - oy, p[2] - oz]
    return {
        "size": [mx - ox + 1, my - oy + 1, mz - oz + 1],
        "ground_y": GROUND - oy,
        "pad_center": loc((PAD[0], GROUND, PAD[1])),
        "npcs": [{"role": role, "pos": loc(pos), "yaw": yaw, "home": loc(home)} for role, pos, yaw, home in camp.npcs],
    }


def generate(verbose=False):
    camp = build_camp()
    S.validate(camp)
    checker = CampChecker(camp)
    problems = checker.run()
    if problems:
        raise SystemExit("venus_camp.py: checker found problems:\n  " + "\n  ".join(problems[:200]))
    root = S.to_nbt(camp)
    data = nbt_bytes(root)
    os.makedirs(os.path.dirname(STRUCTURE_FILE), exist_ok=True)
    with gzip.GzipFile(STRUCTURE_FILE, "wb", mtime=0) as f:
        f.write(data)
    with gzip.open(STRUCTURE_FILE, "rb") as f:
        name, back = nbt_parse(f.read())
    assert name == "" and len(back["blocks"]) == len(root["blocks"])
    anc = anchors(camp)
    write_json(ANCHORS_FILE, anc)
    print(f"venus_expedition_camp: size {anc['size']}, ground_y {anc['ground_y']}, pad {anc['pad_center']}, "
          f"{len(root['blocks'])} blocks, {len(root['palette'])} states, {len(anc['npcs'])} npcs, checker OK {checker.stats}")
    return camp


if __name__ == "__main__":
    generate(verbose=True)
