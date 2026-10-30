package com.replecant.retrocosmos.oinstein;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.venus.VenusLanding;
import java.io.Reader;
import java.util.ArrayList;
import java.util.List;
import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructurePlaceSettings;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate;
import net.minecraft.world.phys.AABB;

/**
 * Dr. Oinstein's prisoner camp for the captured Earth expedition, built at runtime when the story needs it (the
 * NPC quest calls {@link #place} by reflection). The design is the template {@code oinstein/oinstein_prison_camp}
 * with its anchors {@code data/retrocosmos/venus_camp/prison_camp.json} (tools/oinstein.py): a fenced compound,
 * two watchtowers, a cell block of eight lever-worked iron cell doors, the interrogation hut, the barracks and the
 * depot of confiscated gear, with its garrison (six of Oinstein's forces) in the template.
 *
 * <p>{@code place} picks dry, fairly flat land {@code minDistance..maxDistance} blocks from {@code near}, away from
 * the expedition camp and the mod's structures, levels the 41 x 41 site like the expedition camp (cut away above the
 * ground layer, footings below, quiet block flags, loose items swept) and places the template without rotation. It
 * does NOT spawn the prisoners: far from every player their entity sections are not loaded, so the quest code
 * populates the camp when a player first comes near - origin = centre - {@code "center"}, one
 * {@code ExpeditionNpcs.spawnCaptive(level, origin + pos, yaw, role)} per {@code captives} entry of kind
 * {@code expedition_captive}; each stands within two blocks of its lever-worked cell door. Returns the camp centre
 * (origin + {@code "center"}: the block above the middle of the ground layer), or null.
 */
public final class OinsteinPrisonCamp {
    private static final Identifier ANCHORS = Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "venus_camp/prison_camp.json");
    private static final Identifier TEMPLATE = Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "oinstein/oinstein_prison_camp");
    private static final int QUIET = Block.UPDATE_CLIENTS | Block.UPDATE_SUPPRESS_DROPS;
    /** How far above the template the jungle is cut away, and how deep footings may reach. */
    private static final int CLEAR_ABOVE = 24, FOOTING_DEPTH = 16;
    /** Margin round the footprint cleared of plants and trees (so no canopy hangs into the fence). */
    private static final int MARGIN = 2;
    /** No expedition camp within this many blocks of the prison camp's centre. */
    private static final int CAMP_DISTANCE = 64;
    /** No structure of the mod within this many chunks. */
    private static final int STRUCTURE_FREE_CHUNKS = 3;
    private static final int MAX_RELIEF = 6;

    private OinsteinPrisonCamp() {}

    /**
     * Builds the prisoner camp on dry land {@code minDistance..maxDistance} blocks (horizontally) from {@code near}
     * (no prisoners - see the class comment). Returns the camp's centre, or null if no site was found or data is missing.
     */
    @Nullable
    public static BlockPos place(ServerLevel level, BlockPos near, int minDistance, int maxDistance) {
        StructureTemplate template = level.getStructureManager().get(TEMPLATE).orElse(null);
        JsonObject anchors = readAnchors(level);
        if (template == null || anchors == null) {
            RetroCosmos.LOGGER.error("Retro Cosmos: prison camp template or anchors missing");
            return null;
        }
        BlockPos size = pos(anchors.getAsJsonArray("size"));
        int groundY = anchors.get("ground_y").getAsInt();
        long t0 = System.nanoTime();
        int lo = Math.max(0, minDistance), hi = Math.max(lo + 16, maxDistance);
        Site site = findSite(level, near, lo, hi, size, 2 * MAX_RELIEF);
        if (site == null) {                 // nothing dry and flat enough: look further out, and take rougher ground
            site = findSite(level, near, hi, 2 * hi, size, 4 * MAX_RELIEF);
        }
        long t1 = System.nanoTime();
        if (site == null) {
            RetroCosmos.LOGGER.warn("Retro Cosmos: no dry site for the prison camp {}..{} blocks from {}", minDistance, maxDistance, near);
            return null;
        }
        BlockPos origin = new BlockPos(site.x - size.getX() / 2, site.ground - groundY, site.z - size.getZ() / 2);
        level(level, origin, size, groundY);
        template.placeInWorld(level, origin, origin, new StructurePlaceSettings().setFinalizeEntities(true), level.getRandom(), QUIET);
        level.getEntitiesOfClass(ItemEntity.class, new AABB(origin).expandTowards(size.getX(), size.getY() + CLEAR_ABOVE, size.getZ())
                .inflate(16)).forEach(Entity::discard);
        BlockPos center = origin.offset(pos(anchors.getAsJsonArray("center")));
        RetroCosmos.LOGGER.info("Retro Cosmos: Oinstein prison camp built at {} (origin {}, relief {}; site search {} ms, building {} ms)",
                center, origin, site.relief, (t1 - t0) / 1000000, (System.nanoTime() - t1) / 1000000);
        return center;
    }

    /** World positions of the captive anchors of a camp whose template origin is {@code origin}: role, pos, yaw, door. */
    public static List<Anchor> anchors(ServerLevel level, BlockPos origin) {
        List<Anchor> out = new ArrayList<>();
        JsonObject anchors = readAnchors(level);
        if (anchors == null) {
            return out;
        }
        for (JsonElement e : anchors.getAsJsonArray("captives")) {
            JsonObject a = e.getAsJsonObject();
            out.add(new Anchor(a.get("role").getAsString(), a.has("name") ? a.get("name").getAsString() : null,
                    origin.offset(pos(a.getAsJsonArray("pos"))), a.get("yaw").getAsFloat(),
                    origin.offset(pos(a.getAsJsonArray("cell_door"))), origin.offset(pos(a.getAsJsonArray("lever")))));
        }
        return out;
    }

    /** A prisoner's anchor in the world: where they stand, which way they face, their cell door and its lever. */
    public record Anchor(String role, @Nullable String name, BlockPos pos, float yaw, BlockPos cellDoor, BlockPos lever) {}

    private record Site(int x, int z, int ground, int relief) {}

    /**
     * Candidate centres on rings between the two distances, scored by the world-gen height maps (cheap: nothing is
     * generated): every sample of the footprint must be dry land above sea level; the flattest site wins, the first
     * one with little relief is taken at once.
     */
    @Nullable
    private static Site findSite(ServerLevel level, BlockPos near, int minDist, int maxDist, BlockPos size, int maxRelief) {
        ChunkGenerator gen = level.getChunkSource().getGenerator();
        var randomState = level.getChunkSource().randomState();
        BlockPos camp = VenusLanding.campPad(level);
        RandomSource rnd = RandomSource.create(level.getSeed() ^ near.asLong());
        int half = size.getX() / 2 + MARGIN;
        Site best = null;
        int rings = Math.max(1, (maxDist - minDist) / 24 + 1);
        for (int ring = 0; ring < rings; ring++) {
            int r = minDist + (maxDist - minDist) * ring / Math.max(1, rings - 1);
            int steps = Math.max(8, (int) (2 * Math.PI * r / 32));
            double phase = rnd.nextDouble() * Math.PI * 2;
            for (int i = 0; i < steps; i++) {
                double a = phase + Math.PI * 2 * i / steps;
                int x = near.getX() + (int) Math.round(Math.cos(a) * r);
                int z = near.getZ() + (int) Math.round(Math.sin(a) * r);
                if (camp != null && Math.abs(camp.getX() - x) < CAMP_DISTANCE && Math.abs(camp.getZ() - z) < CAMP_DISTANCE) {
                    continue;
                }
                String biome = level.getUncachedNoiseBiome(x >> 2, level.getSeaLevel() >> 2, z >> 2).unwrapKey()
                        .map(k -> k.identifier().getPath()).orElse("");
                if (biome.contains("sea") || biome.contains("ocean")) {
                    continue;                   // a cheap first look: open water
                }
                if (structureNear(level, x, z)) {
                    continue;
                }
                int lo = Integer.MAX_VALUE, hi = Integer.MIN_VALUE;
                List<Integer> heights = new ArrayList<>();
                boolean dry = true;
                for (int[] o : samples(half)) {         // the centre and the corners first: most sites fail there
                    int floor = gen.getFirstOccupiedHeight(x + o[0], z + o[1], Heightmap.Types.OCEAN_FLOOR_WG, level, randomState);
                    lo = Math.min(lo, floor);
                    hi = Math.max(hi, floor);
                    if (floor <= gen.getSeaLevel() || hi - lo > maxRelief
                            || gen.getFirstOccupiedHeight(x + o[0], z + o[1], Heightmap.Types.WORLD_SURFACE_WG, level, randomState) > floor) {
                        dry = false;
                        break;
                    }
                    heights.add(floor);
                }
                if (!dry) {
                    continue;
                }
                heights.sort(Integer::compare);
                Site site = new Site(x, z, heights.get(heights.size() / 2) - 1, hi - lo);
                if (best == null || site.relief < best.relief) {
                    best = site;
                }
                if (site.relief <= MAX_RELIEF / 2) {
                    return refine(level, site, size);
                }
            }
        }
        return best == null ? null : refine(level, best, size);
    }

    /** Footprint samples (a 5 x 5 grid), the centre and the corners first. */
    private static List<int[]> samples(int half) {
        List<int[]> out = new ArrayList<>(List.of(new int[] {0, 0}, new int[] {-half, -half}, new int[] {half, -half},
                new int[] {-half, half}, new int[] {half, half}));
        for (int dx = -half; dx <= half; dx += half / 2) {
            for (int dz = -half; dz <= half; dz += half / 2) {
                if (!((dx == 0 && dz == 0) || (Math.abs(dx) == half && Math.abs(dz) == half))) {
                    out.add(new int[] {dx, dz});
                }
            }
        }
        return out;
    }

    /** With the chunks generated, the real ground (trees and features included) decides the site's level. */
    private static Site refine(ServerLevel level, Site site, BlockPos size) {
        int half = size.getX() / 2;
        List<Integer> heights = new ArrayList<>();
        for (int dx = -half; dx <= half; dx += 5) {
            for (int dz = -half; dz <= half; dz += 5) {
                heights.add(level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, site.x + dx, site.z + dz) - 1);
            }
        }
        heights.sort(Integer::compare);
        return new Site(site.x, site.z, Math.max(level.getSeaLevel() + 1, heights.get(heights.size() / 2)), site.relief);
    }

    /** Cuts the jungle away above the ground layer (and a margin round it) and fills footings under it. */
    private static void level(ServerLevel level, BlockPos origin, BlockPos size, int groundY) {
        BlockState air = Blocks.AIR.defaultBlockState();
        BlockState footing = Blocks.COBBLESTONE.defaultBlockState();
        for (int x = -MARGIN; x < size.getX() + MARGIN; x++) {
            for (int z = -MARGIN; z < size.getZ() + MARGIN; z++) {
                boolean inside = x >= 0 && z >= 0 && x < size.getX() && z < size.getZ();
                for (int y = groundY + 1; y < size.getY() + CLEAR_ABOVE; y++) {
                    BlockPos p = origin.offset(x, y, z);
                    BlockState s = level.getBlockState(p);
                    if (!s.isAir() && (inside || !s.isSolidRender() || !s.getFluidState().isEmpty())) {
                        level.removeBlockEntity(p);
                        level.setBlock(p, air, QUIET);
                    }
                }
                if (!inside) {
                    continue;
                }
                for (int y = groundY; y >= groundY - FOOTING_DEPTH; y--) {
                    BlockPos p = origin.offset(x, y, z);
                    BlockState state = level.getBlockState(p);
                    if (y < groundY && state.isSolidRender() && state.getFluidState().isEmpty()) {
                        break;
                    }
                    level.setBlock(p, footing, QUIET);
                }
            }
        }
    }

    /**
     * Whether one of the mod's structure sets (ruins, camps, outposts, the Institute) may place a structure within a
     * few chunks - the placement maths only (no biome checks, nothing generated), so it errs on the safe side.
     */
    private static boolean structureNear(ServerLevel level, int x, int z) {
        var state = level.getChunkSource().getGeneratorState();
        return level.registryAccess().lookupOrThrow(Registries.STRUCTURE_SET).listElements()
                .filter(h -> h.key().identifier().getNamespace().equals(RetroCosmos.MODID))
                .anyMatch(h -> state.hasStructureChunkInRange(h, x >> 4, z >> 4, STRUCTURE_FREE_CHUNKS));
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
}
