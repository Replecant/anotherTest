package com.replecant.retrocosmos.ruins;

import com.mojang.datafixers.util.Pair;
import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.oinstein.AttachedTemplatePiece;
import com.replecant.retrocosmos.oinstein.KeycardReaderBlock;
import com.replecant.retrocosmos.oinstein.LaserBarrierBlock;
import com.replecant.retrocosmos.oinstein.ModOinstein;
import java.util.ArrayDeque;
import java.util.HashSet;
import java.util.Set;
import net.minecraft.core.Direction;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.LecternBlockEntity;
import net.minecraft.world.level.block.entity.RandomizableContainerBlockEntity;
import net.minecraft.world.level.levelgen.structure.StructurePiece;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.common.util.FakePlayer;
import net.neoforged.neoforge.common.util.FakePlayerFactory;
import com.replecant.retrocosmos.venus.Venus;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Vec3i;
import net.minecraft.core.Holder;
import net.minecraft.core.HolderSet;
import net.minecraft.core.SectionPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.entity.SpawnPlacements;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructureStart;
import net.minecraft.world.phys.AABB;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;

/** PROBE ONLY (never committed): water, garrison and vegetation audit of the Venus structures. */
@EventBusSubscriber(modid = RetroCosmos.MODID)
public final class RuinsWorldgenProbe {
    private static final String[] NAMES = {"oinstein_complex", "oinstein_capture_camp", "oinstein_field_lab",
            "oinstein_relay_pylon", "oinstein_checkpoint", "venusian_pyramid", "venusian_ziggurat", "venusian_ruined_village",
            "venusian_shrine", "tribal_camp"};
    private static final List<Object[]> FOUND = new ArrayList<>();
    private static int ticks = -1;

    private RuinsWorldgenProbe() {}

    @SubscribeEvent
    public static void onStarted(ServerStartedEvent event) {
        if (System.getenv("RUIN_PROBE") == null) {
            return;
        }
        MinecraftServer server = event.getServer();
        ServerLevel venus = server.getLevel(Venus.DIMENSION);
        if (venus == null) {
            server.halt(false);
            return;
        }
        for (String name : NAMES) {
            for (int[] origin : new int[][] {{0, 0}, {3000, -2000}}) {
                try {
                    probe(venus, name, origin);
                } catch (Throwable t) {
                    RetroCosmos.LOGGER.error("RUIN PROBE FAIL " + name, t);
                }
                if (name.equals("oinstein_complex")) {
                    break;
                }
            }
        }
        for (int[] c : new int[][] {{0, 0, 150, 400}, {3000, -2000, 100, 300}}) {
            try {
                prison(venus, new BlockPos(c[0], 64, c[1]), c[2], c[3]);
            } catch (Throwable t) {
                RetroCosmos.LOGGER.error("RUIN PRISON FAIL", t);
            }
        }
        spawnRules(venus);
        ticks = 0;
    }

    @SubscribeEvent
    public static void onTick(ServerTickEvent.Post event) {
        if (ticks < 0) {
            return;
        }
        ++ticks;
        if (ticks % 200 == 0) {
            RetroCosmos.LOGGER.info("RUIN TICK {} at {}", ticks, System.currentTimeMillis());
        }
        if (ticks == 900) {       // the prison camps' chunks were left to unload: load them again and count the garrison
            ServerLevel venus = event.getServer().getLevel(Venus.DIMENSION);
            for (BlockPos o : PRISONS) {
                for (int x = o.getX() >> 4; x <= (o.getX() + 40) >> 4; x++) {
                    for (int z = o.getZ() >> 4; z <= (o.getZ() + 40) >> 4; z++) {
                        venus.setChunkForced(x, z, true);
                    }
                }
            }
        }
        if (ticks == 1200) {      // a minute of ticking the forced chunks
            ServerLevel pv = event.getServer().getLevel(Venus.DIMENSION);
            for (BlockPos o : PRISONS) {
                Map<String, Integer> mobs = new TreeMap<>();
                for (Entity e : pv.getEntities((Entity) null, new AABB(o).expandTowards(41, 20, 41), e -> e instanceof net.minecraft.world.entity.Mob)) {
                    mobs.merge(BuiltInRegistries.ENTITY_TYPE.getKey(e.getType()).getPath(), 1, Integer::sum);
                }
                RetroCosmos.LOGGER.info("RUIN PRISON garrison after reload at {}: {}", o, mobs);
            }
            ServerLevel venus = event.getServer().getLevel(Venus.DIMENSION);
            for (Object[] f : FOUND) {
                census(venus, (String) f[0], (BoundingBox) f[1], "after 1 min");
            }
            if (LAB_BOX[0] != null) {
                labCensus(venus, LAB_BOX[0], "after 1 min");
            }
            spawnRules(venus);
            RetroCosmos.LOGGER.info("RUIN PROBE DONE");
            event.getServer().halt(false);
        }
    }

    private static void probe(ServerLevel level, String name, int[] origin) {
        Holder<Structure> holder = level.registryAccess().lookupOrThrow(Registries.STRUCTURE).getOrThrow(
                ResourceKey.create(Registries.STRUCTURE, Identifier.fromNamespaceAndPath(RetroCosmos.MODID, name)));
        Pair<BlockPos, Holder<Structure>> found = level.getChunkSource().getGenerator().findNearestMapStructure(level,
                HolderSet.direct(holder), new BlockPos(origin[0], 64, origin[1]), 50, false);
        if (found == null) {
            RetroCosmos.LOGGER.info("RUIN AUDIT {} none near {},{}", name, origin[0], origin[1]);
            return;
        }
        BlockPos pos = found.getFirst();
        StructureStart start = level.structureManager().getStartForStructure(SectionPos.of(pos), holder.value(), level.getChunk(pos));
        if (start == null || !start.isValid()) {
            RetroCosmos.LOGGER.info("RUIN AUDIT {} at {} no valid start", name, pos);
            return;
        }
        BoundingBox box = start.getPieces().get(0).getBoundingBox();
        boolean oin = name.startsWith("oinstein");
        for (int x = (box.minX() >> 4) - 1; x <= (box.maxX() >> 4) + 1; x++) {
            for (int z = (box.minZ() >> 4) - 1; z <= (box.maxZ() >> 4) + 1; z++) {
                level.getChunk(x, z);
                if (oin && x >= box.minX() >> 4 && x <= box.maxX() >> 4 && z >= box.minZ() >> 4 && z <= box.maxZ() >> 4) {
                    level.setChunkForced(x, z, true);
                }
            }
        }
        int columns = 0, wet = 0, plantsBad = 0, plants = 0;
        Map<String, Integer> badOn = new TreeMap<>();
        BlockPos.MutableBlockPos p = new BlockPos.MutableBlockPos();
        for (int x = box.minX(); x <= box.maxX(); x++) {
            for (int z = box.minZ(); z <= box.maxZ(); z++) {
                columns++;
                int top = level.getHeight(Heightmap.Types.WORLD_SURFACE, x, z);
                if (!level.getFluidState(p.set(x, top - 1, z)).isEmpty()) {
                    wet++;
                }
                for (int y = box.minY(); y <= Math.min(top, box.maxY() + 2); y++) {
                    BlockState s = level.getBlockState(p.set(x, y, z));
                    String id = BuiltInRegistries.BLOCK.getKey(s.getBlock()).getPath();
                    if (id.startsWith("venus_") && (id.contains("sedge") || id.contains("horsetail") || id.contains("cycad")
                            || id.contains("lily") || id.contains("fern") || id.equals("venus_glowcap") || id.contains("glowstalk"))) {
                        if (id.endsWith("fern") || id.contains("glowstalk")) {
                            BlockState below = level.getBlockState(p.set(x, y - 1, z));
                            if (below.is(s.getBlock())) {
                                continue;       // upper half
                            }
                        }
                        plants++;
                        BlockState below = level.getBlockState(p.set(x, y - 1, z));
                        if (!below.is(BlockTags.DIRT) && !below.is(com.replecant.retrocosmos.venus.VenusPlantBlock.ROCK_FLOOR)) {
                            plantsBad++;
                            badOn.merge(BuiltInRegistries.BLOCK.getKey(below.getBlock()).getPath(), 1, Integer::sum);
                        }
                    }
                }
            }
        }
        RetroCosmos.LOGGER.info("RUIN AUDIT {} at {} box={} rot={} surface water columns {}/{} plants {} on non-ground {} {}",
                name, pos, box, start.getPieces().get(0).getRotation(), wet, columns, plants, plantsBad, badOn);
        if (oin) {
            FOUND.add(new Object[] {name, box});
            containers(level, name, box);
        }
        if (name.equals("oinstein_complex")) {
            try {
                lab(level, start);
            } catch (Throwable t) {
                RetroCosmos.LOGGER.error("RUIN LAB FAIL", t);
            }
            try {
                readers(level, box);
            } catch (Throwable t) {
                RetroCosmos.LOGGER.error("RUIN READER FAIL", t);
            }
        }
    }

    /** Loot containers by table, lecterns with books, keycard readers by level. */
    private static void containers(ServerLevel level, String name, BoundingBox box) {
        Map<String, Integer> tables = new TreeMap<>();
        int lecterns = 0, readers = 0;
        BlockPos.MutableBlockPos p = new BlockPos.MutableBlockPos();
        for (int x = box.minX(); x <= box.maxX(); x++) {
            for (int z = box.minZ(); z <= box.maxZ(); z++) {
                for (int y = box.minY(); y <= box.maxY(); y++) {
                    BlockEntity be = level.getBlockEntity(p.set(x, y, z));
                    if (be instanceof RandomizableContainerBlockEntity rc && rc.getLootTable() != null) {
                        tables.merge(rc.getLootTable().identifier().getPath().replace("chests/", ""), 1, Integer::sum);
                    } else if (be instanceof LecternBlockEntity lec && lec.hasBook()) {
                        lecterns++;
                    }
                    if (level.getBlockState(p).getBlock() instanceof KeycardReaderBlock) {
                        readers++;
                    }
                    String fid = BuiltInRegistries.BLOCK.getKey(level.getBlockState(p).getBlock()).getPath();
                    if (fid.contains("poster") || fid.equals("control_panel") || fid.equals("wall_sconce")) {
                        tables.merge("~wall:" + fid, 1, Integer::sum);
                    }
                }
            }
        }
        RetroCosmos.LOGGER.info("RUIN LOOT {} {} lecterns(with book) {} readers {} containers {}", name, box.getCenter(), lecterns,
                readers, tables);
    }

    /** The lower laboratory: its piece, the anchor marker, the arena's size, the shell (a flood fill from the anchor
     * may only meet the template's own air and the stair opening above), fluids, plants and the garrison. */
    private static void lab(ServerLevel level, StructureStart start) {
        AttachedTemplatePiece lab = null;
        for (StructurePiece piece : start.getPieces()) {
            if (piece instanceof AttachedTemplatePiece a) {
                lab = a;
            }
        }
        if (lab == null) {
            RetroCosmos.LOGGER.info("RUIN LAB missing! pieces={}", start.getPieces().size());
            return;
        }
        BoundingBox box = lab.getBoundingBox();
        for (int x = (box.minX() >> 4); x <= (box.maxX() >> 4); x++) {
            for (int z = (box.minZ() >> 4); z <= (box.maxZ() >> 4); z++) {
                level.getChunk(x, z);
                level.setChunkForced(x, z, true);
            }
        }
        Map<String, BlockPos> markers = lab.markers();
        BlockPos anchor = markers.get(AttachedTemplatePiece.BOSS_ANCHOR_MARKER);
        RetroCosmos.LOGGER.info("RUIN LAB piece {} box={} rot={} templatePos={} markers={} anchor block={} start piece box={}",
                lab.templateId(), box, lab.getRotation(), lab.templatePosition(), markers,
                anchor == null ? "?" : BuiltInRegistries.BLOCK.getKey(level.getBlockState(anchor).getBlock()) + " be="
                        + (level.getBlockEntity(anchor) == null ? "none" : level.getBlockEntity(anchor).getType()),
                start.getPieces().get(0).getBoundingBox());
        // the arena: scan lines through the hall (template-local: anchor + offsets, see tools/oinstein.py)
        BlockPos p0 = lab.toWorld(new BlockPos(15, 10, 5));       // Institute (10, -21, 8): under the north catwalk
        Vec3i dx = lab.toWorld(new BlockPos(16, 10, 5)).subtract(p0);
        Vec3i dz = lab.toWorld(new BlockPos(15, 10, 6)).subtract(p0);
        int w = run(level, p0, dx) + run(level, p0, new Vec3i(-dx.getX(), 0, -dx.getZ())) + 1;
        int d = run(level, p0, dz) + run(level, p0, new Vec3i(-dz.getX(), 0, -dz.getZ())) + 1;
        BlockPos floor = lab.toWorld(new BlockPos(15, 2, 24));    // the walk level at Institute (10, -29, 27)
        int h = run(level, floor, new Vec3i(0, 1, 0)) + 1;
        RetroCosmos.LOGGER.info("RUIN LAB arena {} x {} x {} high (scan at {})", w, d, h, p0);
        // the shell
        Set<BlockPos> templateAir = new HashSet<>();
        for (StructureTemplate.StructureBlockInfo info : lab.blocks(Blocks.AIR)) {
            templateAir.add(info.pos());
        }
        templateAir.addAll(markers.values());
        ArrayDeque<BlockPos> todo = new ArrayDeque<>();
        Set<BlockPos> seen = new HashSet<>();
        if (anchor != null) {
            todo.add(anchor);
            seen.add(anchor);
        }
        int foreignAir = 0, fluids = 0, above = 0, outside = 0;
        Map<String, Integer> foreign = new TreeMap<>();
        while (!todo.isEmpty() && seen.size() < 600000) {
            BlockPos c = todo.poll();
            BlockState st = level.getBlockState(c);
            if (!level.getFluidState(c).isEmpty()) {
                fluids++;
                foreign.merge("fluid:" + BuiltInRegistries.BLOCK.getKey(st.getBlock()).getPath() + "@" + c.toShortString(), 1, Integer::sum);
            }
            if (st.isAir() && !templateAir.contains(c)) {
                foreignAir++;
                if (foreign.size() < 12) {
                    foreign.merge("air@" + c.toShortString(), 1, Integer::sum);
                }
            }
            for (Direction dir : Direction.values()) {
                BlockPos n = c.relative(dir);
                if (seen.contains(n)) {
                    continue;
                }
                BlockState ns = level.getBlockState(n);
                if (ns.isCollisionShapeFullBlock(level, n) && level.getFluidState(n).isEmpty()) {
                    continue;
                }
                if (!box.isInside(n)) {
                    if (n.getY() > box.maxY()) {
                        above++;
                    } else {
                        outside++;
                    }
                    seen.add(n);
                    continue;
                }
                seen.add(n);
                todo.add(n);
            }
        }
        RetroCosmos.LOGGER.info("RUIN LAB shell: flood {} cells, template air {}, foreign air {}, fluids {}, open above {}, "
                + "leaks out of the box {} {}", seen.size(), templateAir.size(), foreignAir, fluids, above, outside, foreign);
        int plants = 0, nonAir = 0;
        Map<String, Integer> inAir = new TreeMap<>();
        for (BlockPos c : templateAir) {        // what stands where the template put air: plants, stone, fluids
            BlockState st = level.getBlockState(c);
            if (!st.isAir()) {
                nonAir++;
                inAir.merge(BuiltInRegistries.BLOCK.getKey(st.getBlock()).getPath(), 1, Integer::sum);
                if (BuiltInRegistries.BLOCK.getKey(st.getBlock()).getPath().startsWith("venus_")) {
                    plants++;
                }
            }
        }
        RetroCosmos.LOGGER.info("RUIN LAB inside the shell: plants {}, non-air in template air {} {}", plants, nonAir, inAir);
        containers(level, "oinstein_lower_lab", box);
        labCensus(level, box, "at start");
        LAB_BOX[0] = box;
    }

    private static final BoundingBox[] LAB_BOX = new BoundingBox[1];
    private static final List<BlockPos> PRISONS = new ArrayList<>();

    private static void labCensus(ServerLevel level, BoundingBox box, String when) {
        Map<String, Integer> mobs = new TreeMap<>();
        for (Entity e : level.getEntities((Entity) null, AABB.of(box), e -> e.getType().is(ModOinstein.FORCES)
                || e.getType().getDescriptionId().contains("tribesman"))) {
            mobs.merge(BuiltInRegistries.ENTITY_TYPE.getKey(e.getType()).getPath() + (e.isAlive() ? "" : "(dead)"), 1, Integer::sum);
        }
        RetroCosmos.LOGGER.info("RUIN CENSUS oinstein_lower_lab {} (lab box only): {}", when, mobs);
    }

    private static int run(ServerLevel level, BlockPos from, Vec3i step) {
        int n = 0;
        BlockPos p = from;
        while (n < 80) {
            p = p.offset(step);
            if (level.getBlockState(p).isCollisionShapeFullBlock(level, p)) {
                return n;
            }
            n++;
        }
        return n;
    }

    /** The keycard readers of the Institute: a wrong card must not open a barrier, the right one must. */
    private static void readers(ServerLevel level, BoundingBox box) {
        Map<KeycardReaderBlock.Clearance, BlockPos> found = new TreeMap<>();
        BlockPos.MutableBlockPos p = new BlockPos.MutableBlockPos();
        for (int x = box.minX(); x <= box.maxX(); x++) {
            for (int z = box.minZ(); z <= box.maxZ(); z++) {
                for (int y = box.minY(); y <= box.maxY(); y++) {
                    BlockState st = level.getBlockState(p.set(x, y, z));
                    if (st.getBlock() instanceof KeycardReaderBlock) {
                        found.put(st.getValue(KeycardReaderBlock.LEVEL), p.immutable());
                    }
                }
            }
        }
        FakePlayer fake = FakePlayerFactory.getMinecraft(level);
        ItemStack[] cards = {new ItemStack(ModOinstein.KEYCARD_ALPHA.get()), new ItemStack(ModOinstein.KEYCARD_BETA.get()),
                new ItemStack(ModOinstein.KEYCARD_GAMMA.get())};
        for (Map.Entry<KeycardReaderBlock.Clearance, BlockPos> e : found.entrySet()) {
            BlockPos r = e.getValue();
            int lv = e.getKey().ordinal();
            BlockPos barrier = KeycardReaderBlock.findGuardedBarrier(level, r).orElse(null);
            int before = powered(level, r);
            BlockHitResult hit = new BlockHitResult(Vec3.atCenterOf(r), level.getBlockState(r).getValue(KeycardReaderBlock.FACING), r, false);
            fake.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
            InteractionResult empty = level.getBlockState(r).useWithoutItem(level, fake, hit);
            int afterEmpty = powered(level, r);
            ItemStack wrong = cards[(lv + 1) % 3].copy();
            fake.setItemInHand(InteractionHand.MAIN_HAND, wrong);
            InteractionResult wr = level.getBlockState(r).useItemOn(wrong, level, fake, InteractionHand.MAIN_HAND, hit);
            int afterWrong = powered(level, r);
            String statusWrong = level.getBlockState(r).getValue(KeycardReaderBlock.STATUS).getSerializedName();
            ItemStack right = cards[lv].copy();
            fake.setItemInHand(InteractionHand.MAIN_HAND, right);
            InteractionResult rr = level.getBlockState(r).useItemOn(right, level, fake, InteractionHand.MAIN_HAND, hit);
            int afterRight = powered(level, r);
            String statusRight = level.getBlockState(r).getValue(KeycardReaderBlock.STATUS).getSerializedName();
            RetroCosmos.LOGGER.info("RUIN READER {} at {} facing {} guards {}: powered barrier blocks {} -> empty hand {} ({}) -> wrong card "
                    + "{} ({}, {}) -> right card {} ({}, {}); card kept: {}", e.getKey(), r,
                    level.getBlockState(r).getValue(KeycardReaderBlock.FACING), barrier, before, afterEmpty, empty, afterWrong, wr,
                    statusWrong, afterRight, rr, statusRight, fake.getMainHandItem());
        }
        RetroCosmos.LOGGER.info("RUIN READERS found {}", found.keySet());
    }

    /** The prisoner camp: place it, audit every block (canSurvive / shape update), water, items, mobs; pull every lever. */
    private static void prison(ServerLevel level, BlockPos near, int min, int max) {
        long t0 = System.currentTimeMillis();
        BlockPos center = com.replecant.retrocosmos.oinstein.OinsteinPrisonCamp.place(level, near, min, max);
        if (center == null) {
            RetroCosmos.LOGGER.info("RUIN PRISON none near {}", near);
            return;
        }
        BlockPos origin = center.offset(-20, -1, -20);
        PRISONS.add(origin);
        int dist = (int) Math.sqrt(Math.pow(center.getX() - near.getX(), 2) + Math.pow(center.getZ() - near.getZ(), 2));
        int problems = 0, blocks = 0, water = 0;
        Map<String, Integer> bad = new TreeMap<>();
        for (BlockPos p : BlockPos.betweenClosed(origin, origin.offset(40, 18, 40))) {
            BlockState st = level.getBlockState(p);
            if (!level.getFluidState(p).isEmpty() && p.getY() > origin.getY()) {
                water++;
            }
            if (st.isAir()) {
                continue;
            }
            blocks++;
            String id = BuiltInRegistries.BLOCK.getKey(st.getBlock()).getPath();
            if (!st.canSurvive(level, p)) {
                problems++;
                bad.merge("survive:" + id, 1, Integer::sum);
            } else {
                BlockState upd = net.minecraft.world.level.block.Block.updateFromNeighbourShapes(st, level, p);
                if (upd != st) {
                    problems++;
                    bad.merge("shape:" + id + "->" + BuiltInRegistries.BLOCK.getKey(upd.getBlock()).getPath(), 1, Integer::sum);
                }
            }
        }
        int items = level.getEntitiesOfClass(net.minecraft.world.entity.item.ItemEntity.class, new AABB(center).inflate(60)).size();
        Map<String, Integer> mobs = new TreeMap<>();
        for (Entity e : level.getEntities((Entity) null, new AABB(origin).expandTowards(41, 20, 41), e -> e instanceof net.minecraft.world.entity.Mob)) {
            mobs.merge(BuiltInRegistries.ENTITY_TYPE.getKey(e.getType()).getPath(), 1, Integer::sum);
        }
        FakePlayer fake = FakePlayerFactory.getMinecraft(level);
        int opened = 0, cells = 0, near2 = 0;
        StringBuilder roles = new StringBuilder();
        for (var a : com.replecant.retrocosmos.oinstein.OinsteinPrisonCamp.anchors(level, origin)) {
            cells++;
            roles.append(a.role()).append(a.name() != null ? "(" + a.name() + ")" : "").append(' ');
            if (a.pos().distManhattan(a.cellDoor()) <= 2 || Math.max(Math.abs(a.pos().getX() - a.cellDoor().getX()),
                    Math.abs(a.pos().getZ() - a.cellDoor().getZ())) <= 2) {
                near2++;
            }
            BlockState door = level.getBlockState(a.cellDoor());
            boolean closed = door.hasProperty(net.minecraft.world.level.block.DoorBlock.OPEN) && !door.getValue(net.minecraft.world.level.block.DoorBlock.OPEN);
            BlockState lever = level.getBlockState(a.lever());
            lever.useWithoutItem(level, fake, new BlockHitResult(Vec3.atCenterOf(a.lever()), Direction.UP, a.lever(), false));
            BlockState after = level.getBlockState(a.cellDoor());
            boolean open = after.hasProperty(net.minecraft.world.level.block.DoorBlock.OPEN) && after.getValue(net.minecraft.world.level.block.DoorBlock.OPEN);
            if (closed && open) {
                opened++;
            }
        }
        RetroCosmos.LOGGER.info("RUIN PRISON at {} ({} blocks from {}, {} ms): blocks {}, problems {} {}, water {}, loose items {}, "
                + "mobs {}, prisoners {} [{}] next to their door {}, cells opened by their lever {}/{}", center, dist, near,
                System.currentTimeMillis() - t0, blocks, problems, bad, water, items, mobs, cells, roles.toString().trim(), near2, opened, cells);
    }

    /** Powered barrier and emitter blocks within the reader's range. */
    private static int powered(ServerLevel level, BlockPos r) {
        int n = 0;
        int R = KeycardReaderBlock.RANGE + 6;
        for (BlockPos p : BlockPos.betweenClosed(r.offset(-R, -R, -R), r.offset(R, R, R))) {
            BlockState st = level.getBlockState(p);
            if (st.hasProperty(LaserBarrierBlock.POWERED) && (st.getBlock() instanceof LaserBarrierBlock
                    || st.getBlock() instanceof com.replecant.retrocosmos.oinstein.LaserEmitterBlock) && st.getValue(LaserBarrierBlock.POWERED)) {
                n++;
            }
        }
        return n;
    }

    private static void census(ServerLevel level, String name, BoundingBox box, String when) {
        Map<String, Integer> mobs = new TreeMap<>();
        for (Entity e : level.getEntities((Entity) null, new AABB(box.minX() - 8, box.minY() - 8, box.minZ() - 8, box.maxX() + 9,
                box.maxY() + 12, box.maxZ() + 9), e -> e.getType().is(ModOinstein.FORCES) || e.getType().getDescriptionId().contains("tribesman"))) {
            mobs.merge(BuiltInRegistries.ENTITY_TYPE.getKey(e.getType()).getPath() + (e.isAlive() ? "" : "(dead)"), 1, Integer::sum);
        }
        RetroCosmos.LOGGER.info("RUIN CENSUS {} {} at {}: {}", name, when, box.getCenter(), mobs);
    }

    /** What the structure spawn lists hold and how often the shared Oinstein spawn rule lets a natural spawn through. */
    private static void spawnRules(ServerLevel level) {
        for (Object[] f : FOUND) {
            BoundingBox box = (BoundingBox) f[1];
            BlockPos c = box.getCenter();
            BlockPos pos = level.getHeightmapPos(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, c);
            var list = level.getChunkSource().getGenerator().getMobsAt(level.getBiome(pos), level.structureManager(),
                    MobCategory.MONSTER, pos);
            StringBuilder sb = new StringBuilder();
            list.unwrap().forEach(d -> sb.append(BuiltInRegistries.ENTITY_TYPE.getKey(d.value().type()).getPath()).append(' '));
            int pass = 0, tries = 400;
            EntityType<?> novus = BuiltInRegistries.ENTITY_TYPE.getValue(Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "hominid_novus"));
            for (int i = 0; i < tries; i++) {
                if (SpawnPlacements.checkSpawnRules(novus, level, EntitySpawnReason.NATURAL, pos, level.getRandom())) {
                    pass++;
                }
            }
            RetroCosmos.LOGGER.info("RUIN SPAWNS {} monster list at {}: [{}] novus natural rule pass {}/{}", f[0], pos, sb, pass, tries);
        }
    }
}
