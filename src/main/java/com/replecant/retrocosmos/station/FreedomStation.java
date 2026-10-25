package com.replecant.retrocosmos.station;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.block.LaunchPadBlock;
import com.replecant.retrocosmos.registry.ModBlocks;
import java.io.Reader;
import java.util.ArrayList;
import java.util.List;
import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.packs.resources.Resource;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructurePlaceSettings;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate;
import net.minecraft.world.phys.AABB;

/**
 * Freedom Station («Свобода»): an uncrewed Atomic Age station in orbit of Homestead, living in its own
 * "orbit" dimension. It is built from a structure template the first time a rocket heads there.
 * Anchors (docking pad, arrival spot, pressurised compartments) come from data/retrocosmos/station/freedom_station.json.
 */
public final class FreedomStation {
    public static final ResourceKey<Level> DIMENSION = ResourceKey.create(Registries.DIMENSION,
            Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "freedom_station"));
    private static final Identifier STRUCTURE = Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "freedom_station");
    private static final Identifier ANCHORS = Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "station/freedom_station.json");
    /** Height of the structure's lowest layer. */
    private static final int BASE_Y = 96;

    /** Station layout in world coordinates. */
    public record Layout(BlockPos origin, BlockPos padCenter, BlockPos arrival, List<AABB> pressurized) {
        /** Where the rocket's engine block stands: on top of the center pad block. */
        public BlockPos padBase() {
            return padCenter.above();
        }

        public boolean isPressurized(double x, double y, double z) {
            for (AABB box : pressurized) {
                if (box.contains(x, y, z)) {
                    return true;
                }
            }
            return false;
        }
    }

    @Nullable
    private static Layout layout;

    private FreedomStation() {}

    public static boolean isStation(Level level) {
        return level.dimension() == DIMENSION;
    }

    @Nullable
    public static ServerLevel level(MinecraftServer server) {
        return server.getLevel(DIMENSION);
    }

    /** The station layout, read once from the data pack. */
    @Nullable
    public static Layout layout(MinecraftServer server) {
        if (layout == null) {
            try {
                Resource resource = server.getResourceManager().getResource(ANCHORS).orElse(null);
                if (resource == null) {
                    RetroCosmos.LOGGER.error("Retro Cosmos: missing {}", ANCHORS);
                    return null;
                }
                try (Reader reader = resource.openAsReader()) {
                    JsonObject json = JsonParser.parseReader(reader).getAsJsonObject();
                    BlockPos size = pos(json.getAsJsonArray("size"));
                    BlockPos origin = new BlockPos(-size.getX() / 2, BASE_Y, -size.getZ() / 2);
                    List<AABB> boxes = new ArrayList<>();
                    for (var element : json.getAsJsonArray("pressurized")) {
                        JsonArray a = element.getAsJsonArray();
                        boxes.add(new AABB(origin.getX() + a.get(0).getAsInt(), origin.getY() + a.get(1).getAsInt(), origin.getZ() + a.get(2).getAsInt(),
                                origin.getX() + a.get(3).getAsInt() + 1, origin.getY() + a.get(4).getAsInt() + 1, origin.getZ() + a.get(5).getAsInt() + 1));
                    }
                    layout = new Layout(origin, origin.offset(pos(json.getAsJsonArray("pad_center"))),
                            origin.offset(pos(json.getAsJsonArray("arrival"))), List.copyOf(boxes));
                }
            } catch (Exception e) {
                RetroCosmos.LOGGER.error("Retro Cosmos: could not read {}", ANCHORS, e);
                return null;
            }
        }
        return layout;
    }

    private static BlockPos pos(JsonArray a) {
        return new BlockPos(a.get(0).getAsInt(), a.get(1).getAsInt(), a.get(2).getAsInt());
    }

    /** Builds the station in its dimension if that hasn't happened yet. Returns the layout, or null on failure. */
    @Nullable
    public static Layout ensureBuilt(ServerLevel level) {
        Layout layout = layout(level.getServer());
        if (layout == null) {
            return null;
        }
        StationData data = level.getDataStorage().computeIfAbsent(StationData.TYPE);
        if (data.placed()) {
            return layout;
        }
        StructureTemplate template = level.getStructureManager().get(STRUCTURE).orElse(null);
        if (template == null) {
            RetroCosmos.LOGGER.error("Retro Cosmos: missing structure {}", STRUCTURE);
            return null;
        }
        template.placeInWorld(level, layout.origin(), layout.origin(), new StructurePlaceSettings(), level.getRandom(), Block.UPDATE_CLIENTS);
        // the template stores plain pad blocks; give the 3x3 its edge/corner/center look
        for (int dx = -1; dx <= 1; dx++) {
            for (int dz = -1; dz <= 1; dz++) {
                BlockPos p = layout.padCenter().offset(dx, 0, dz);
                BlockState state = level.getBlockState(p);
                if (state.is(ModBlocks.LAUNCH_PAD.get())) {
                    level.setBlock(p, LaunchPadBlock.shapeFor(state, level, p), Block.UPDATE_CLIENTS);
                }
            }
        }
        data.markPlaced();
        RetroCosmos.LOGGER.info("Retro Cosmos: Freedom Station built at {}", layout.origin());
        return layout;
    }

    /** Whether a position counts as vacuum: anywhere in orbit outside the station's pressurised compartments. */
    public static boolean isVacuum(ServerLevel level, double x, double y, double z) {
        if (!isStation(level)) {
            return false;
        }
        Layout layout = layout(level.getServer());
        return layout == null || !layout.isPressurized(x, y, z);
    }
}
