package com.replecant.retrocosmos.oinstein;

import com.mojang.serialization.MapCodec;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

/** A crackling Tesla coil (decor) or a brain in a jar: small lab pieces with a fixed shape and some particles. */
public class TeslaCoilBlock extends Block {
    public static final MapCodec<TeslaCoilBlock> CODEC = simpleCodec(p -> new TeslaCoilBlock(p, Shapes.block(), true));
    private final VoxelShape shape;
    private final boolean sparks;

    public TeslaCoilBlock(Properties properties, VoxelShape shape, boolean sparks) {
        super(properties);
        this.shape = shape;
        this.sparks = sparks;
    }

    @Override
    protected MapCodec<? extends Block> codec() {
        return CODEC;
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return shape;
    }

    @Override
    public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
        if (sparks) {
            for (int i = 0; i < 2; i++) {
                level.addParticle(ParticleTypes.ELECTRIC_SPARK, pos.getX() + 0.5 + (random.nextDouble() - 0.5) * 0.9,
                        pos.getY() + 0.85 + random.nextDouble() * 0.4, pos.getZ() + 0.5 + (random.nextDouble() - 0.5) * 0.9,
                        (random.nextDouble() - 0.5) * 0.2, 0.05, (random.nextDouble() - 0.5) * 0.2);
            }
            if (random.nextInt(40) == 0) {
                level.playLocalSound(pos, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.BLOCKS, 0.4F, 1.9F, false);
            }
        } else if (random.nextInt(4) == 0) {
            level.addParticle(ParticleTypes.BUBBLE_POP, pos.getX() + 0.35 + random.nextDouble() * 0.3, pos.getY() + 0.7,
                    pos.getZ() + 0.35 + random.nextDouble() * 0.3, 0, 0.02, 0);
        }
    }
}
