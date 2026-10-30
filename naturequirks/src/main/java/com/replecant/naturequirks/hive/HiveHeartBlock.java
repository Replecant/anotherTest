package com.replecant.naturequirks.hive;

import com.mojang.serialization.MapCodec;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;

/**
 * The Hive Heart: the pulsing amber core of a giant hive. While it stands, breaking the hive near it or striking its
 * bees calls guardian bees out of it ({@link HiveHeartBlockEntity#alarm}); broken, it yields royal jelly and the hive
 * falls quiet.
 */
public class HiveHeartBlock extends BaseEntityBlock {
    public static final MapCodec<HiveHeartBlock> CODEC = simpleCodec(HiveHeartBlock::new);

    public HiveHeartBlock(Properties properties) {
        super(properties);
    }

    @Override
    protected MapCodec<? extends BaseEntityBlock> codec() {
        return CODEC;
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new HiveHeartBlockEntity(pos, state);
    }

    @Override
    protected RenderShape getRenderShape(BlockState state) {
        return RenderShape.MODEL;
    }

    @Override
    public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
        if (random.nextInt(3) == 0) {
            level.addParticle(ParticleTypes.WAX_ON, pos.getX() + random.nextDouble(), pos.getY() + 1.05,
                    pos.getZ() + random.nextDouble(), 0.0, 0.02, 0.0);
        }
        if (random.nextInt(6) == 0) {
            level.addParticle(ParticleTypes.DRIPPING_HONEY, pos.getX() + 0.2 + random.nextDouble() * 0.6, pos.getY() - 0.05,
                    pos.getZ() + 0.2 + random.nextDouble() * 0.6, 0.0, 0.0, 0.0);
        }
    }
}
