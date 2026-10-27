package com.replecant.retrocosmos.venus;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.block.LaunchPadBlock;
import com.replecant.retrocosmos.flight.RocketEntity;
import com.replecant.retrocosmos.furniture.FurnitureBlock;
import com.replecant.retrocosmos.npc.NpcAnchor;
import com.replecant.retrocosmos.registry.ModBlocks;
import com.replecant.retrocosmos.registry.ModFurniture;
import com.replecant.retrocosmos.registry.ModItems;
import java.io.Reader;
import java.util.function.Predicate;
import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.Holder;
import net.minecraft.core.HolderSet;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.Container;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructurePlaceSettings;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate;
import net.minecraft.world.level.saveddata.SavedData;
import net.minecraft.world.level.saveddata.SavedDataType;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/**
 * The expedition camp on Venus: a cleared patch of jungle with a 3x3 launch pad, a service tower, floodlights
 * and a supply cabinet with propellant for the trip home. Built the first time a rocket heads to Venus.
 */
public final class VenusLanding {
    /** Clearing radius around the pad and how far up the jungle canopy is cut away. */
    private static final int CLEAR_RADIUS = 5, CLEAR_HEIGHT = 32;
    /**
     * Block flags for building the camp: sync to clients but never drop items. Cutting the jungle away and laying the
     * deck triggers shape updates that would otherwise break the surrounding plants and lianas into loose items.
     */
    private static final int QUIET = Block.UPDATE_CLIENTS | Block.UPDATE_SUPPRESS_DROPS;
    /** Half-extent of the box swept of stray item entities once the camp is built. */
    private static final int SWEEP = 48;
    /** Bump when the camp design changes: older camps are cleared and rebuilt on the next flight there. */
    public static final int VERSION = 2;
    private static final Identifier TEMPLATE = Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "venus_expedition_camp");
    private static final Identifier ANCHORS = Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "venus_camp/expedition_camp.json");

    private VenusLanding() {}

    /** Per-level record of the camp. */
    public static final class CampData extends SavedData {
        static final Codec<CampData> CODEC = RecordCodecBuilder.create(i -> i.group(
                Codec.BOOL.fieldOf("built").forGetter(d -> d.built),
                BlockPos.CODEC.fieldOf("pad").forGetter(d -> d.pad),
                Codec.INT.optionalFieldOf("version", 1).forGetter(d -> d.version)
        ).apply(i, CampData::new));
        static final SavedDataType<CampData> TYPE = new SavedDataType<>("retrocosmos_venus_camp", CampData::new, CODEC);

        private boolean built;
        private BlockPos pad;
        private int version;

        public CampData() {
            this(false, BlockPos.ZERO, 0);
        }

        private CampData(boolean built, BlockPos pad, int version) {
            this.built = built;
            this.pad = pad;
            this.version = version;
        }
    }

    /** The camp's pad if a camp has been built in this level (for keeping wildlife away), else null. */
    @Nullable
    public static BlockPos campPad(ServerLevel level) {
        if (!Venus.isVenus(level)) {
            return null;
        }
        CampData data = level.getDataStorage().computeIfAbsent(CampData.TYPE);
        return data.built ? data.pad : null;
    }

    /** Returns where the rocket's engine block stands at the camp, building the camp first if needed. */
    public static BlockPos ensureCamp(ServerLevel level) {
        CampData data = level.getDataStorage().computeIfAbsent(CampData.TYPE);
        if (data.built && data.version >= VERSION) {
            return data.pad;
        }
        BlockPos land;
        if (data.built) {
            // an older camp stands here: clear it and put the current design in its place
            RetroCosmos.LOGGER.info("Retro Cosmos: replacing the Venus camp v{} with v{}", data.version, VERSION);
            clear(level, data.pad, 24, -4, 40);
            land = data.pad;
        } else {
            land = findLand(level);
        }
        data.built = true;
        data.pad = buildAt(level, land.getX(), land.getZ());
        data.version = VERSION;
        data.setDirty();
        return data.pad;
    }

    /**
     * Tears down the camp and builds it again on a fresh dry, level site (for camps that an older version put on a
     * mountainside). Rockets parked at the old pad move to the new one. Returns the new pad, or null if no camp exists.
     */
    @Nullable
    public static BlockPos relocate(ServerLevel level) {
        CampData data = level.getDataStorage().computeIfAbsent(CampData.TYPE);
        if (!data.built) {
            return null;
        }
        BlockPos old = data.pad;
        var rockets = level.getEntitiesOfClass(RocketEntity.class, new AABB(old).inflate(24, 40, 24));
        clear(level, old, 24, -4, 40, e -> !(e instanceof RocketEntity));
        BlockPos land = findLand(level);
        data.pad = buildAt(level, land.getX(), land.getZ());
        data.version = VERSION;
        data.setDirty();
        Vec3 parked = Vec3.atBottomCenterOf(data.pad);
        rockets.forEach(rocket -> rocket.teleportTo(parked.x, parked.y, parked.z));
        RetroCosmos.LOGGER.info("Retro Cosmos: Venus camp moved from {} to {}", old, data.pad);
        return data.pad;
    }

    private static void clear(ServerLevel level, BlockPos center, int radius, int down, int up) {
        clear(level, center, radius, down, up, e -> true);
    }

    private static void clear(ServerLevel level, BlockPos center, int radius, int down, int up, Predicate<Entity> remove) {
        BlockState air = Blocks.AIR.defaultBlockState();
        for (BlockPos p : BlockPos.betweenClosed(center.offset(-radius, down, -radius), center.offset(radius, up, radius))) {
            if (!level.getBlockState(p).isAir()) {
                level.removeBlockEntity(p);
                level.setBlock(p, air, QUIET);
            }
        }
        level.getEntitiesOfClass(Entity.class, new AABB(center).inflate(radius, up, radius),
                e -> !(e instanceof Player) && remove.test(e)).forEach(Entity::discard);
    }

    /**
     * Venus is a third ocean: walk an outward spiral from the origin for a dry, level site, preferably plains where
     * the camp fits best. Biomes come from the biome source and heights from the noise generator, so nothing has to
     * be generated to judge a candidate.
     */
    private static BlockPos findLand(ServerLevel level) {
        BlockPos flat = null, rough = null, firstLand = null;
        for (int ring = 0; ring <= 64; ring++) {
            int r = ring * 32;
            int steps = Math.max(1, ring * 8);
            for (int i = 0; i < steps; i++) {
                double angle = Math.PI * 2 * i / steps;
                int x = (int) Math.round(Math.cos(angle) * r);
                int z = (int) Math.round(Math.sin(angle) * r);
                var biome = level.getUncachedNoiseBiome(x >> 2, level.getSeaLevel() >> 2, z >> 2);
                String id = biome.unwrapKey().map(k -> k.identifier().getPath()).orElse("");
                if (id.contains("sea") || id.contains("ocean")) {
                    continue;
                }
                int spread = siteSpread(level, x, z);
                if (spread > ROUGH_SITE || structureNear(level, x, z)) {
                    if (firstLand == null && spread != Integer.MAX_VALUE) {
                        firstLand = new BlockPos(x, 0, z);
                    }
                    continue;
                }
                BlockPos site = new BlockPos(x, 0, z);
                if (spread <= FLAT_SITE) {
                    if (id.contains("plains")) {
                        return site;
                    }
                    if (flat == null) {
                        flat = site;
                    }
                } else if (rough == null) {
                    rough = site;
                }
            }
            if (flat != null && ring >= 8) {
                return flat;
            }
            if (rough != null && ring >= 32) {
                return rough;
            }
        }
        if (flat != null) {
            return flat;
        }
        return rough != null ? rough : firstLand != null ? firstLand : BlockPos.ZERO;
    }

    /** Half-width of the area sampled when judging a camp site (the camp is 41 blocks across). */
    private static final int SITE_RADIUS = 22;
    /** Largest height difference across a site that the camp levels without carving a pit or a cliff. */
    private static final int FLAT_SITE = 5;
    /** Accepted only when no flat site turns up after a long search. */
    private static final int ROUGH_SITE = 9;

    /**
     * Height difference of the natural ground across a candidate site, or {@code Integer.MAX_VALUE} when any sample
     * is under water or below sea level. Mountainsides and valleys score high, so the camp is not dug into a hill.
     */
    private static int siteSpread(ServerLevel level, int x, int z) {
        var generator = level.getChunkSource().getGenerator();
        var random = level.getChunkSource().randomState();
        int min = Integer.MAX_VALUE, max = Integer.MIN_VALUE;
        for (int dx = -SITE_RADIUS; dx <= SITE_RADIUS; dx += SITE_RADIUS / 2) {
            for (int dz = -SITE_RADIUS; dz <= SITE_RADIUS; dz += SITE_RADIUS / 2) {
                int ground = generator.getBaseHeight(x + dx, z + dz, Heightmap.Types.OCEAN_FLOOR_WG, level, random);
                int surface = generator.getBaseHeight(x + dx, z + dz, Heightmap.Types.WORLD_SURFACE_WG, level, random);
                if (surface > ground || ground <= level.getSeaLevel()) {
                    return Integer.MAX_VALUE;
                }
                min = Math.min(min, ground);
                max = Math.max(max, ground);
                if (max - min > ROUGH_SITE) {
                    return max - min; // already too rough: spare the remaining noise samples
                }
            }
        }
        return max - min;
    }

    /** Chunks around a candidate site that must be free of ruins and tribal camps. */
    private static final int STRUCTURE_FREE_CHUNKS = 5;

    /**
     * Whether any of the mod's structures (ruins, tribal camps) would generate within a few chunks of a candidate
     * camp site. Uses the structure placement maths, so nothing has to be generated to answer.
     */
    private static boolean structureNear(ServerLevel level, int x, int z) {
        var registry = level.registryAccess().lookupOrThrow(Registries.STRUCTURE);
        var ours = registry.listElements().filter(h -> h.key().identifier().getNamespace().equals(RetroCosmos.MODID))
                .map(h -> (Holder<Structure>) h).toList();
        if (ours.isEmpty()) {
            return false;
        }
        var nearest = level.getChunkSource().getGenerator().findNearestMapStructure(level, HolderSet.direct(ours),
                new BlockPos(x, level.getSeaLevel(), z), STRUCTURE_FREE_CHUNKS, false);
        if (nearest == null) {
            return false;
        }
        BlockPos found = nearest.getFirst();
        int dx = (found.getX() >> 4) - (x >> 4), dz = (found.getZ() >> 4) - (z >> 4);
        return Math.abs(dx) <= STRUCTURE_FREE_CHUNKS && Math.abs(dz) <= STRUCTURE_FREE_CHUNKS;
    }

    /** Builds a camp on the surface at the given column and returns the rocket's engine position on its pad. */
    public static BlockPos buildAt(ServerLevel level, int x, int z) {
        BlockPos surface = level.getHeightmapPos(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, new BlockPos(x, 0, z));
        if (surface.getY() <= level.getMinY() + 3) {
            // no ground in this column (open void or a deep hole): build the camp on stilts of cobblestone at sea level
            surface = new BlockPos(x, Math.max(level.getSeaLevel(), level.getMinY() + 4), z);
        }
        BlockPos padCenter = surface.below(); // the pad replaces the top layer of ground
        BlockPos fromTemplate = placeTemplate(level, surface);
        if (fromTemplate != null) {
            sweepItems(level, fromTemplate);
            RetroCosmos.LOGGER.info("Retro Cosmos: Venus expedition camp built at {}", fromTemplate);
            return fromTemplate.above().immutable();
        }
        build(level, padCenter);
        sweepItems(level, padCenter);
        RetroCosmos.LOGGER.info("Retro Cosmos: Venus expedition camp (fallback) built at {}", padCenter);
        return padCenter.above().immutable();
    }

    /**
     * Places the designed camp template centred on {@code surface} (the first air block above the ground), on a
     * levelled site: the jungle above the footprint is cut away and cobblestone footings fill any dips below it.
     * Returns the pad's centre block, or null when the template or its anchors are missing.
     */
    @Nullable
    private static BlockPos placeTemplate(ServerLevel level, BlockPos surface) {
        StructureTemplate template = level.getStructureManager().get(TEMPLATE).orElse(null);
        JsonObject anchors = readAnchors(level);
        if (template == null || anchors == null) {
            return null;
        }
        BlockPos size = pos(anchors.getAsJsonArray("size"));
        int groundY = anchors.get("ground_y").getAsInt();
        BlockPos origin = new BlockPos(surface.getX() - size.getX() / 2, surface.getY() - 1 - groundY, surface.getZ() - size.getZ() / 2);
        BlockState footing = Blocks.COBBLESTONE.defaultBlockState();
        BlockState air = Blocks.AIR.defaultBlockState();
        for (int x = 0; x < size.getX(); x++) {
            for (int z = 0; z < size.getZ(); z++) {
                // clear above the ground layer (structure plus a margin for the rocket's descent)
                for (int y = groundY + 1; y < size.getY() + CLEAR_HEIGHT; y++) {
                    BlockPos p = origin.offset(x, y, z);
                    if (!level.getBlockState(p).isAir()) {
                        level.setBlock(p, air, QUIET);
                    }
                }
                // footings down to solid ground
                for (int y = groundY; y >= groundY - 16; y--) {
                    BlockPos p = origin.offset(x, y, z);
                    BlockState state = level.getBlockState(p);
                    if (y < groundY && state.isSolidRender()) {
                        break;
                    }
                    level.setBlock(p, footing, QUIET);
                }
            }
        }
        template.placeInWorld(level, origin, origin, new StructurePlaceSettings(), level.getRandom(), QUIET);
        BlockPos padCenter = origin.offset(pos(anchors.getAsJsonArray("pad_center")));
        for (int dx = -1; dx <= 1; dx++) {
            for (int dz = -1; dz <= 1; dz++) {
                BlockPos p = padCenter.offset(dx, 0, dz);
                BlockState state = level.getBlockState(p);
                if (state.is(ModBlocks.LAUNCH_PAD.get())) {
                    level.setBlock(p, LaunchPadBlock.shapeFor(state, level, p), QUIET);
                }
            }
        }
        NpcAnchor.spawnAll(level, NpcAnchor.read(anchors, origin));
        return padCenter;
    }

    /** Removes loose items left around the site (plants and vines knocked off by the levelling). */
    private static void sweepItems(ServerLevel level, BlockPos center) {
        level.getEntitiesOfClass(ItemEntity.class, new AABB(center).inflate(SWEEP)).forEach(Entity::discard);
    }

    @Nullable
    private static JsonObject readAnchors(ServerLevel level) {
        try {
            var resource = level.getServer().getResourceManager().getResource(ANCHORS);
            if (resource.isEmpty()) {
                return null;
            }
            try (Reader reader = resource.get().openAsReader()) {
                return JsonParser.parseReader(reader).getAsJsonObject();
            }
        } catch (Exception e) {
            RetroCosmos.LOGGER.error("Retro Cosmos: could not read {}", ANCHORS, e);
            return null;
        }
    }

    private static BlockPos pos(JsonArray a) {
        return new BlockPos(a.get(0).getAsInt(), a.get(1).getAsInt(), a.get(2).getAsInt());
    }

    private static void build(ServerLevel level, BlockPos center) {
        BlockState air = Blocks.AIR.defaultBlockState();
        // clear the jungle above the camp and level the ground with a deck of hull plating
        for (int dx = -CLEAR_RADIUS; dx <= CLEAR_RADIUS; dx++) {
            for (int dz = -CLEAR_RADIUS; dz <= CLEAR_RADIUS; dz++) {
                for (int dy = 1; dy <= CLEAR_HEIGHT; dy++) {
                    BlockPos p = center.offset(dx, dy, dz);
                    if (!level.getBlockState(p).isAir()) {
                        level.setBlock(p, air, QUIET);
                    }
                }
                boolean deck = Math.abs(dx) <= 3 && Math.abs(dz) <= 3;
                for (int dy = 0; dy >= -2; dy--) {
                    level.setBlock(center.offset(dx, dy, dz), (dy == 0 && deck ? ModFurniture.HULL_PANEL.get() : Blocks.COBBLESTONE)
                            .defaultBlockState(), QUIET);
                }
            }
        }
        // 3x3 pad, then give it its edge/corner/centre look
        for (int dx = -1; dx <= 1; dx++) {
            for (int dz = -1; dz <= 1; dz++) {
                level.setBlock(center.offset(dx, 0, dz), ModBlocks.LAUNCH_PAD.get().defaultBlockState(), QUIET);
            }
        }
        for (int dx = -1; dx <= 1; dx++) {
            for (int dz = -1; dz <= 1; dz++) {
                BlockPos p = center.offset(dx, 0, dz);
                level.setBlock(p, LaunchPadBlock.shapeFor(level.getBlockState(p), level, p), QUIET);
            }
        }
        // service tower at dx = +2
        for (int dy = 0; dy < 8; dy++) {
            level.setBlock(center.offset(2, dy, 0), ModBlocks.SERVICE_TOWER.get().defaultBlockState(), QUIET);
        }
        // floodlights on the deck corners
        for (int[] c : new int[][] {{-3, -3}, {3, -3}, {-3, 3}, {3, 3}}) {
            level.setBlock(center.offset(c[0], 1, c[1]), ModFurniture.ATOMIC_FLOOR_LAMP.get().defaultBlockState()
                    .setValue(FurnitureBlock.LIT, true), QUIET);
        }
        // supply cabinets with propellant for the way home, facing the pad
        BlockPos cabinet = center.offset(-3, 1, 0);
        BlockState cabinetState = ModFurniture.SUPPLY_CABINET.get().defaultBlockState().setValue(FurnitureBlock.FACING, Direction.EAST);
        level.setBlock(cabinet, cabinetState, Block.UPDATE_ALL);
        level.setBlock(cabinet.north(), cabinetState, Block.UPDATE_ALL);
        if (level.getBlockEntity(cabinet) instanceof Container box) {
            box.setItem(0, new ItemStack(ModItems.ROCKET_FUEL_CANISTER.get(), 8));
            box.setItem(1, new ItemStack(ModItems.LIQUID_OXYGEN_CANISTER.get(), 8));
            box.setItem(2, new ItemStack(ModItems.EMPTY_FUEL_CANISTER.get(), 4));
        }
        if (level.getBlockEntity(cabinet.north()) instanceof Container box) {
            box.setItem(0, new ItemStack(net.minecraft.world.item.Items.BREAD, 12));
            box.setItem(1, new ItemStack(net.minecraft.world.item.Items.TORCH, 16));
        }
    }
}
