package com.replecant.retrocosmos.venus;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.tags.FluidTags;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;

/** Client-side particle emitter of {@link FumaroleBlock} (a block entity so the plume shows from a distance). */
public class FumaroleBlockEntity extends BlockEntity {
    public FumaroleBlockEntity(BlockPos pos, BlockState state) {
        super(ModVenus.FUMAROLE_BE.get(), pos, state);
    }

    static void clientTick(Level level, BlockPos pos) {
        RandomSource random = level.getRandom();
        BlockPos above = pos.above();
        double x = pos.getX() + 0.5 + (random.nextDouble() - 0.5) * 0.5;
        double z = pos.getZ() + 0.5 + (random.nextDouble() - 0.5) * 0.5;
        if (level.getFluidState(above).is(FluidTags.WATER)) {
            // hot spring: bubbles rise through the water, steam curls off the surface
            if (random.nextInt(3) == 0) {
                level.addParticle(ParticleTypes.BUBBLE_COLUMN_UP, x, pos.getY() + 1.05, z, 0.0, 0.04, 0.0);
            }
            if (random.nextInt(10) == 0) {
                BlockPos.MutableBlockPos cursor = above.mutable();
                for (int i = 0; i < 12 && level.getFluidState(cursor).is(FluidTags.WATER); i++) {
                    cursor.move(0, 1, 0);
                }
                if (level.getBlockState(cursor).isAir()) {
                    level.addAlwaysVisibleParticle(ParticleTypes.CAMPFIRE_COSY_SMOKE, true,
                            x + random.nextDouble() - 0.5, cursor.getY() + 0.1, z + random.nextDouble() - 0.5, 0.0, 0.03, 0.0);
                }
            }
        } else if (level.getBlockState(above).isAir()) {
            // open vent: a tall, slow plume of volcanic smoke
            if (random.nextInt(9) == 0) {
                level.addAlwaysVisibleParticle(ParticleTypes.CAMPFIRE_SIGNAL_SMOKE, true,
                        x, pos.getY() + 1.1, z, 0.0, 0.07, 0.0);
            }
            if (random.nextInt(40) == 0) {
                level.addParticle(ParticleTypes.LAVA, x, pos.getY() + 1.0, z, 0.0, 0.0, 0.0);
            }
        }
    }
}
