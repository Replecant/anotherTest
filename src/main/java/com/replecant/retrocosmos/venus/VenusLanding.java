package com.replecant.retrocosmos.venus;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.block.LaunchPadBlock;
import com.replecant.retrocosmos.furniture.FurnitureBlock;
import com.replecant.retrocosmos.registry.ModBlocks;
import com.replecant.retrocosmos.registry.ModFurniture;
import com.replecant.retrocosmos.registry.ModItems;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.Container;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.saveddata.SavedData;
import net.minecraft.world.level.saveddata.SavedDataType;

/**
 * The expedition camp on Venus: a cleared patch of jungle with a 3x3 launch pad, a service tower, floodlights
 * and a supply cabinet with propellant for the trip home. Built the first time a rocket heads to Venus.
 */
public final class VenusLanding {
    /** Clearing radius around the pad and how far up the jungle canopy is cut away. */
    private static final int CLEAR_RADIUS = 5, CLEAR_HEIGHT = 32;

    private VenusLanding() {}

    /** Per-level record of the camp. */
    public static final class CampData extends SavedData {
        static final Codec<CampData> CODEC = RecordCodecBuilder.create(i -> i.group(
                Codec.BOOL.fieldOf("built").forGetter(d -> d.built),
                BlockPos.CODEC.fieldOf("pad").forGetter(d -> d.pad)
        ).apply(i, CampData::new));
        static final SavedDataType<CampData> TYPE = new SavedDataType<>("retrocosmos_venus_camp", CampData::new, CODEC);

        private boolean built;
        private BlockPos pad;

        public CampData() {
            this(false, BlockPos.ZERO);
        }

        private CampData(boolean built, BlockPos pad) {
            this.built = built;
            this.pad = pad;
        }
    }

    /** Returns where the rocket's engine block stands at the camp, building the camp first if needed. */
    public static BlockPos ensureCamp(ServerLevel level) {
        CampData data = level.getDataStorage().computeIfAbsent(CampData.TYPE);
        if (data.built) {
            return data.pad;
        }
        BlockPos land = findLand(level);
        data.built = true;
        data.pad = buildAt(level, land.getX(), land.getZ());
        data.setDirty();
        return data.pad;
    }

    /**
     * Venus is a third ocean: walk an outward spiral from the origin, asking the biome source (cheap, no chunk
     * generation) for the first column that isn't open sea, preferably plains where the camp fits best.
     */
    private static BlockPos findLand(ServerLevel level) {
        BlockPos firstLand = null;
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
                if (id.contains("plains")) {
                    return new BlockPos(x, 0, z);
                }
                if (firstLand == null) {
                    firstLand = new BlockPos(x, 0, z);
                }
            }
            if (firstLand != null && ring >= 8) {
                return firstLand;
            }
        }
        return firstLand != null ? firstLand : BlockPos.ZERO;
    }

    /** Builds a camp on the surface at the given column and returns the rocket's engine position on its pad. */
    public static BlockPos buildAt(ServerLevel level, int x, int z) {
        BlockPos surface = level.getHeightmapPos(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, new BlockPos(x, 0, z));
        if (surface.getY() <= level.getMinY() + 3) {
            // no ground in this column (open void or a deep hole): build the camp on stilts of cobblestone at sea level
            surface = new BlockPos(x, Math.max(level.getSeaLevel(), level.getMinY() + 4), z);
        }
        BlockPos padCenter = surface.below(); // the pad replaces the top layer of ground
        build(level, padCenter);
        RetroCosmos.LOGGER.info("Retro Cosmos: Venus expedition camp built at {}", padCenter);
        return padCenter.above().immutable();
    }

    private static void build(ServerLevel level, BlockPos center) {
        BlockState air = Blocks.AIR.defaultBlockState();
        // clear the jungle above the camp and level the ground with a deck of hull plating
        for (int dx = -CLEAR_RADIUS; dx <= CLEAR_RADIUS; dx++) {
            for (int dz = -CLEAR_RADIUS; dz <= CLEAR_RADIUS; dz++) {
                for (int dy = 1; dy <= CLEAR_HEIGHT; dy++) {
                    BlockPos p = center.offset(dx, dy, dz);
                    if (!level.getBlockState(p).isAir()) {
                        level.setBlock(p, air, Block.UPDATE_CLIENTS);
                    }
                }
                boolean deck = Math.abs(dx) <= 3 && Math.abs(dz) <= 3;
                for (int dy = 0; dy >= -2; dy--) {
                    level.setBlock(center.offset(dx, dy, dz), (dy == 0 && deck ? ModFurniture.HULL_PANEL.get() : Blocks.COBBLESTONE)
                            .defaultBlockState(), Block.UPDATE_CLIENTS);
                }
            }
        }
        // 3x3 pad, then give it its edge/corner/centre look
        for (int dx = -1; dx <= 1; dx++) {
            for (int dz = -1; dz <= 1; dz++) {
                level.setBlock(center.offset(dx, 0, dz), ModBlocks.LAUNCH_PAD.get().defaultBlockState(), Block.UPDATE_CLIENTS);
            }
        }
        for (int dx = -1; dx <= 1; dx++) {
            for (int dz = -1; dz <= 1; dz++) {
                BlockPos p = center.offset(dx, 0, dz);
                level.setBlock(p, LaunchPadBlock.shapeFor(level.getBlockState(p), level, p), Block.UPDATE_CLIENTS);
            }
        }
        // service tower at dx = +2
        for (int dy = 0; dy < 8; dy++) {
            level.setBlock(center.offset(2, dy, 0), ModBlocks.SERVICE_TOWER.get().defaultBlockState(), Block.UPDATE_CLIENTS);
        }
        // floodlights on the deck corners
        for (int[] c : new int[][] {{-3, -3}, {3, -3}, {-3, 3}, {3, 3}}) {
            level.setBlock(center.offset(c[0], 1, c[1]), ModFurniture.ATOMIC_FLOOR_LAMP.get().defaultBlockState()
                    .setValue(FurnitureBlock.LIT, true), Block.UPDATE_CLIENTS);
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
