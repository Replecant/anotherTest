package com.replecant.retrocosmos.npc.quest;

import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.npc.ExpeditionNpcs;
import com.replecant.retrocosmos.tribe.ModTribes;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.replecant.retrocosmos.npc.ExpeditionMember;
import java.io.Reader;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.List;
import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.GlobalPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.DoorBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.DoubleBlockHalf;
import net.minecraft.world.level.levelgen.Heightmap;

/**
 * Where Dr. Oinstein holds the expedition. Generated once per world, the moment Dr. Ross gives it away: placed by
 * the structure code ({@code oinstein.OinsteinPrisonCamp.place}, found by name so either side can land first) some
 * 250-400 blocks from the expedition camp on dry land; if that is missing or fails, a makeshift iron-bar stockade
 * is knocked up instead, so the story can always go on.
 */
public final class PrisonCamps {
    public static final int MIN_DISTANCE = 250;
    public static final int MAX_DISTANCE = 400;
    private static final Identifier LAYOUT = Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "venus_camp/prison_camp.json");

    private PrisonCamps() {}

    /** The prisoner camp (built now if nobody has found it yet), or null if there is no camp to start from. */
    @Nullable
    public static BlockPos ensure(MinecraftServer server, BlockPos near) {
        QuestWorld world = QuestWorld.get(server);
        if (world.prisonCamp != null) {
            return world.prisonCamp;
        }
        GlobalPos camp = CampRaid.camp(server);
        ServerLevel level = camp == null ? null : server.getLevel(camp.dimension());
        if (level == null) {
            return null;
        }
        BlockPos from = camp.pos();
        BlockPos placed = viaStructure(level, from);
        world.prisonStockade = placed == null;
        if (placed == null) {
            placed = stockade(level, from);
        }
        world.prisonCamp = placed;
        world.prisonPopulated = false;
        world.setDirty();
        RetroCosmos.LOGGER.info("Retro Cosmos quest: Dr. Oinstein's prisoner camp is at {}", placed);
        return placed;
    }

    @Nullable
    private static BlockPos viaStructure(ServerLevel level, BlockPos from) {
        try {
            Class<?> api = Class.forName("com.replecant.retrocosmos.oinstein.OinsteinPrisonCamp");
            Method place = api.getMethod("place", ServerLevel.class, BlockPos.class, int.class, int.class);
            Object result = place.invoke(null, level, from, MIN_DISTANCE, MAX_DISTANCE);
            return result instanceof BlockPos pos ? pos : null;
        } catch (ClassNotFoundException | NoSuchMethodException e) {
            RetroCosmos.LOGGER.info("Retro Cosmos quest: no prisoner camp structure in this build, building a stockade");
            return null;
        } catch (ReflectiveOperationException | RuntimeException e) {
            RetroCosmos.LOGGER.warn("Retro Cosmos quest: the prisoner camp could not be placed ({}), building a stockade", e.toString());
            return null;
        }
    }

    /** A dry spot 300-ish blocks out (the biome source answers without generating anything). */
    private static BlockPos site(ServerLevel level, BlockPos from) {
        int start = level.getRandom().nextInt(12);
        for (int r = 300; r <= MAX_DISTANCE; r += 40) {
            for (int i = 0; i < 12; i++) {
                double angle = Math.PI * 2 * ((start + i) % 12) / 12.0;
                int x = from.getX() + (int) Math.round(Math.cos(angle) * r);
                int z = from.getZ() + (int) Math.round(Math.sin(angle) * r);
                var biome = level.getUncachedNoiseBiome(x >> 2, level.getSeaLevel() >> 2, z >> 2);
                String id = biome.unwrapKey().map(k -> k.identifier().getPath()).orElse("");
                if (!id.contains("sea") && !id.contains("ocean") && !id.contains("swamp") && !id.contains("river")) {
                    return new BlockPos(x, 0, z);
                }
            }
        }
        return from.offset(320, 0, 0);
    }

    /** The fallback: a riveted-steel floor, one barred cell with a door, three prisoners inside, two guards outside. */
    static BlockPos stockade(ServerLevel level, BlockPos from) {
        BlockPos column = site(level, from);
        BlockPos c = level.getHeightmapPos(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, column);
        if (c.getY() <= level.getMinY() + 3 || !level.getFluidState(c.below()).isEmpty()) {
            c = new BlockPos(c.getX(), Math.max(level.getSeaLevel() + 1, c.getY()), c.getZ());
        }
        int flags = Block.UPDATE_CLIENTS | Block.UPDATE_SUPPRESS_DROPS;
        BlockState floor = block("oinstein_riveted_steel", Blocks.POLISHED_ANDESITE);
        BlockState bars = Blocks.IRON_BARS.defaultBlockState();
        for (int dx = -5; dx <= 5; dx++) {
            for (int dz = -5; dz <= 5; dz++) {
                for (int y = 0; y <= 6; y++) {
                    level.setBlock(c.offset(dx, y, dz), Blocks.AIR.defaultBlockState(), flags);
                }
                level.setBlock(c.offset(dx, -1, dz), floor, flags);
                for (int y = -2; y >= -8 && level.getBlockState(c.offset(dx, y, dz)).canBeReplaced(); y--) {
                    level.setBlock(c.offset(dx, y, dz), Blocks.COBBLESTONE.defaultBlockState(), flags);
                }
            }
        }
        for (int dx = -3; dx <= 3; dx++) {
            for (int dz = -3; dz <= 3; dz++) {
                boolean wall = Math.abs(dx) == 3 || Math.abs(dz) == 3;
                for (int y = 0; y <= 2 && wall; y++) {
                    level.setBlock(c.offset(dx, y, dz), bars, Block.UPDATE_ALL);
                }
                level.setBlock(c.offset(dx, 3, dz), floor, flags);
            }
        }
        // the cell door (south side)
        BlockState door = Blocks.SPRUCE_DOOR.defaultBlockState().setValue(DoorBlock.FACING, Direction.NORTH);
        level.setBlock(c.offset(0, 0, 3), door.setValue(DoorBlock.HALF, DoubleBlockHalf.LOWER), Block.UPDATE_ALL);
        level.setBlock(c.offset(0, 1, 3), door.setValue(DoorBlock.HALF, DoubleBlockHalf.UPPER), Block.UPDATE_ALL);
        level.setBlock(c.offset(0, 2, 3), floor, flags);
        level.setBlock(c.offset(0, 4, 0), Blocks.LANTERN.defaultBlockState(), flags);
        level.setBlock(c.offset(4, 0, 4), Blocks.LIGHTNING_ROD.defaultBlockState(), flags);
        return c.immutable();
    }

    /**
     * Puts the expedition in its cells. Done the first time a player comes near rather than when the camp is placed:
     * far from every player a chunk's entities are not loaded, and anything spawned there could be lost. The cells
     * come from the structure's data/retrocosmos/venus_camp/prison_camp.json ("captives" of kind
     * "expedition_captive", relative to the template's origin = centre - "center"), or from the stockade layout.
     */
    public static List<ExpeditionMember> populate(ServerLevel level) {
        QuestWorld world = QuestWorld.get(level.getServer());
        List<ExpeditionMember> spawned = new ArrayList<>();
        BlockPos c = world.prisonCamp;
        if (c == null || world.prisonPopulated) {
            return spawned;
        }
        world.prisonPopulated = true;
        world.setDirty();
        JsonObject json = world.prisonStockade ? null : layout(level.getServer());
        if (json != null && json.has("captives") && json.has("center")) {
            BlockPos origin = c.subtract(vec(json.getAsJsonArray("center")));
            for (JsonElement e : json.getAsJsonArray("captives")) {
                JsonObject cap = e.getAsJsonObject();
                String kind = cap.has("kind") ? cap.get("kind").getAsString() : "expedition_captive";
                if (!kind.equals("expedition_captive") || !cap.has("pos")) {
                    continue;
                }
                String role = cap.has("role") ? cap.get("role").getAsString() : ExpeditionNpcs.SCIENTIST;
                float yaw = cap.has("yaw") ? cap.get("yaw").getAsFloat() : 0.0F;
                add(spawned, ExpeditionNpcs.spawnCaptive(level, origin.offset(vec(cap.getAsJsonArray("pos"))), yaw, role));
            }
        } else {
            add(spawned, ExpeditionNpcs.spawnCaptive(level, c.offset(0, 0, 2), 0.0F, ExpeditionNpcs.DOCTOR));
            add(spawned, ExpeditionNpcs.spawnCaptive(level, c.offset(-2, 0, 1), 0.0F, ExpeditionNpcs.GUARD));
            add(spawned, ExpeditionNpcs.spawnCaptive(level, c.offset(2, 0, 1), 0.0F, ExpeditionNpcs.SCIENTIST));
            if (world.prisonStockade) {
                for (BlockPos g : new BlockPos[] {c.offset(-4, 0, 4), c.offset(4, 0, -4)}) {
                    var guard = ModTribes.HOMINID_NOVUS.get().spawn(level, g, EntitySpawnReason.STRUCTURE);
                    if (guard != null) {
                        guard.setPersistenceRequired();
                    }
                }
            }
        }
        RetroCosmos.LOGGER.info("Retro Cosmos quest: {} prisoners in their cells at {}", spawned.size(), c);
        return spawned;
    }

    private static void add(List<ExpeditionMember> list, @Nullable ExpeditionMember m) {
        if (m != null) {
            list.add(m);
        }
    }

    private static BlockPos vec(JsonArray a) {
        return new BlockPos(a.get(0).getAsInt(), a.get(1).getAsInt(), a.get(2).getAsInt());
    }

    @Nullable
    private static JsonObject layout(MinecraftServer server) {
        try {
            var resource = server.getResourceManager().getResource(LAYOUT);
            if (resource.isEmpty()) {
                return null;
            }
            try (Reader reader = resource.get().openAsReader()) {
                return JsonParser.parseReader(reader).getAsJsonObject();
            }
        } catch (Exception e) {
            RetroCosmos.LOGGER.warn("Retro Cosmos quest: could not read the prisoner camp layout: {}", e.toString());
            return null;
        }
    }

    private static BlockState block(String path, Block fallback) {
        return BuiltInRegistries.BLOCK.getOptional(Identifier.fromNamespaceAndPath(RetroCosmos.MODID, path))
                .orElse(fallback).defaultBlockState();
    }
}
