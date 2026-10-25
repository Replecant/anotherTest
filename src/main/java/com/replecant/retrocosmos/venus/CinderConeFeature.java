package com.replecant.retrocosmos.venus;

import com.mojang.serialization.Codec;
import net.minecraft.core.BlockPos;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.feature.Feature;
import net.minecraft.world.level.levelgen.feature.FeaturePlaceContext;
import net.minecraft.world.level.levelgen.feature.configurations.NoneFeatureConfiguration;

/**
 * A small smoking volcano: a cone of black volcanic rock with a crater of magma, a little lava pool and
 * fumaroles whose plumes rise above the highlands.
 */
public class CinderConeFeature extends Feature<NoneFeatureConfiguration> {
    public CinderConeFeature(Codec<NoneFeatureConfiguration> codec) {
        super(codec);
    }

    @Override
    public boolean place(FeaturePlaceContext<NoneFeatureConfiguration> context) {
        WorldGenLevel level = context.level();
        RandomSource random = context.random();
        BlockPos origin = context.origin();
        if (!level.getFluidState(origin.below()).isEmpty() || !level.getFluidState(origin).isEmpty()) {
            return false;
        }
        int radius = 5 + random.nextInt(5);
        int height = radius + 4 + random.nextInt(6);
        int crater = Math.max(2, radius / 3);
        int baseY = origin.getY();
        int peak = baseY + height;
        BlockState rock = ModVenus.VENUS_BLACK_ROCK.get().defaultBlockState();
        BlockState magma = Blocks.MAGMA_BLOCK.defaultBlockState();
        BlockState vent = ModVenus.VENUS_FUMAROLE.get().defaultBlockState();
        BlockState lava = Blocks.LAVA.defaultBlockState();
        BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
        int vents = 0;
        for (int dx = -radius - 1; dx <= radius + 1; dx++) {
            for (int dz = -radius - 1; dz <= radius + 1; dz++) {
                double d = Math.sqrt(dx * dx + dz * dz) + random.nextDouble() * 0.7;
                if (d > radius + 0.5) {
                    continue;
                }
                int x = origin.getX() + dx;
                int z = origin.getZ() + dz;
                int ground = level.getHeight(Heightmap.Types.WORLD_SURFACE_WG, x, z) - 1;
                double t = Math.max(0.0, 1.0 - d / (radius + 0.5));
                int top = baseY + (int) Math.round(height * Math.pow(t, 1.15));
                boolean inCrater = d < crater;
                if (inCrater) {
                    top = peak - 2 - (int) Math.round((crater - d) * 1.2);
                }
                int from = Math.min(ground, baseY) - 2;
                for (int y = from; y <= top; y++) {
                    pos.set(x, y, z);
                    boolean surface = y == top;
                    BlockState state = rock;
                    if (inCrater && surface) {
                        if (d < crater - 1.2) {
                            state = lava;
                        } else if (vents < 3 && random.nextInt(3) == 0) {
                            state = vent;
                            vents++;
                        } else {
                            state = magma;
                        }
                    } else if (inCrater && y == top - 1) {
                        state = magma;
                    } else if (!inCrater && y > top - 2 && random.nextInt(14) == 0) {
                        state = magma;
                    }
                    level.setBlock(pos, state, 2);
                }
                // clear whatever was standing on this column (grass, shrubs) above the new surface
                for (int y = top + 1; y <= Math.max(ground, top) + 1; y++) {
                    pos.set(x, y, z);
                    if (!level.getBlockState(pos).isAir()) {
                        level.setBlock(pos, Blocks.AIR.defaultBlockState(), 2);
                    }
                }
            }
        }
        return true;
    }
}
