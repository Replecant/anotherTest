package com.replecant.retrocosmos.venus;

import com.mojang.serialization.Codec;
import java.util.HashSet;
import java.util.Set;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.feature.Feature;
import net.minecraft.world.level.levelgen.feature.FeaturePlaceContext;
import net.minecraft.world.level.levelgen.feature.configurations.NoneFeatureConfiguration;

/**
 * A steaming hot spring: a bowl of water in a basin and rim of black volcanic rock, with a fumarole or two on the
 * rim. Replaces vanilla {@code minecraft:lake} for water: that feature asks for the biome of every surface cell of
 * its 16x16 area (to freeze cold lakes), and the biome lookup's fuzzy sampling can reach two chunks away from the
 * origin chunk - outside the 3x3 chunk region a feature may touch - which crashes world generation with "Requested
 * chunk unavailable during world generation". This feature never reads or writes beyond the origin chunk +-7 blocks.
 */
public class HotSpringFeature extends Feature<NoneFeatureConfiguration> {
    /** Furthest horizontal offset from the origin that is ever read or written. */
    public static final int REACH = 7;
    private static final int MAX_RADIUS = 4;

    public HotSpringFeature(Codec<NoneFeatureConfiguration> codec) {
        super(codec);
    }

    @Override
    public boolean place(FeaturePlaceContext<NoneFeatureConfiguration> context) {
        WorldGenLevel level = context.level();
        RandomSource random = context.random();
        BlockPos origin = context.origin();
        double rx = 2.2 + random.nextDouble() * (MAX_RADIUS - 2.2);
        double rz = 2.2 + random.nextDouble() * (MAX_RADIUS - 2.2);
        int r = MAX_RADIUS + 1;
        // the ground under the pool and its rim must be fairly level, dry land
        int low = Integer.MAX_VALUE;
        int high = Integer.MIN_VALUE;
        for (int dx = -r; dx <= r; dx++) {
            for (int dz = -r; dz <= r; dz++) {
                if (inside(dx, dz, rx + 1, rz + 1)) {
                    int top = level.getHeight(Heightmap.Types.WORLD_SURFACE_WG, origin.getX() + dx, origin.getZ() + dz) - 1;
                    low = Math.min(low, top);
                    high = Math.max(high, top);
                    if (!level.getFluidState(new BlockPos(origin.getX() + dx, top, origin.getZ() + dz)).isEmpty()) {
                        return false;
                    }
                }
            }
        }
        if (high - low > 3 || low <= level.getMinY() + 8) {
            return false;
        }
        int surface = low;
        BlockState water = Blocks.WATER.defaultBlockState();
        BlockState rock = ModVenus.VENUS_BLACK_ROCK.get().defaultBlockState();
        BlockState air = Blocks.AIR.defaultBlockState();
        Set<BlockPos> pool = new HashSet<>();
        for (int dx = -r; dx <= r; dx++) {
            for (int dz = -r; dz <= r; dz++) {
                double e = sq(dx / rx) + sq(dz / rz);
                if (e < 1.0) {
                    int depth = 1 + (int) Math.round(2.2 * (1.0 - e));
                    for (int k = 0; k < depth; k++) {
                        pool.add(new BlockPos(origin.getX() + dx, surface - k, origin.getZ() + dz));
                    }
                }
            }
        }
        BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
        for (int dx = -r; dx <= r; dx++) {
            for (int dz = -r; dz <= r; dz++) {
                int x = origin.getX() + dx;
                int z = origin.getZ() + dz;
                boolean inPool = sq(dx / rx) + sq(dz / rz) < 1.0;
                boolean onRim = !inPool && inside(dx, dz, rx + 1, rz + 1);
                if (!inPool && !onRim) {
                    continue;
                }
                // shave the ground above the water line (and above the rim) so the spring sits in a dip
                for (int y = surface + 1; y <= high + 1; y++) {
                    if (!level.getBlockState(pos.set(x, y, z)).isAir()) {
                        level.setBlock(pos, air, Block.UPDATE_CLIENTS);
                    }
                }
                if (onRim) {
                    BlockState top = random.nextInt(6) == 0 ? ModVenus.VENUS_FUMAROLE.get().defaultBlockState() : rock;
                    level.setBlock(pos.set(x, surface, z), top, Block.UPDATE_CLIENTS);
                }
            }
        }
        // the basin: every pool cell is walled and floored with rock unless already in the pool
        for (BlockPos p : pool) {
            for (Direction d : new Direction[] {Direction.NORTH, Direction.SOUTH, Direction.EAST, Direction.WEST, Direction.DOWN}) {
                BlockPos n = p.relative(d);
                if (!pool.contains(n) && (d == Direction.DOWN || !level.getBlockState(n).isSolid()
                        || random.nextInt(3) == 0)) {
                    level.setBlock(n, rock, Block.UPDATE_CLIENTS);
                }
            }
        }
        for (BlockPos p : pool) {
            level.setBlock(p, water, Block.UPDATE_CLIENTS);
        }
        BlockPos bottom = origin.atY(surface - 3);
        if (pool.contains(bottom.above()) && random.nextBoolean()) {
            level.setBlock(bottom, Blocks.MAGMA_BLOCK.defaultBlockState(), Block.UPDATE_CLIENTS);
        }
        return true;
    }

    private static boolean inside(int dx, int dz, double rx, double rz) {
        return sq(dx / rx) + sq(dz / rz) < 1.0;
    }

    private static double sq(double v) {
        return v * v;
    }
}
