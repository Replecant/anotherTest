package com.replecant.naturequirks.hive;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;

/** Comb heavy with honey: drips of honey fall from its underside, like from a full bee nest. */
public class DrippingCombBlock extends Block {
    public DrippingCombBlock(Properties properties) {
        super(properties);
    }

    @Override
    public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
        if (random.nextInt(4) != 0) {
            return;
        }
        BlockPos below = pos.below();
        BlockState under = level.getBlockState(below);
        if (under.isFaceSturdy(level, below, Direction.UP) || !under.getFluidState().isEmpty()) {
            return;
        }
        double x = pos.getX() + 0.15 + random.nextDouble() * 0.7;
        double z = pos.getZ() + 0.15 + random.nextDouble() * 0.7;
        level.addParticle(ParticleTypes.DRIPPING_HONEY, x, pos.getY() - 0.05, z, 0.0, 0.0, 0.0);
    }
}
