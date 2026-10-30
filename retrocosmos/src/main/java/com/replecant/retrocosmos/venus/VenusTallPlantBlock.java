package com.replecant.retrocosmos.venus;

import com.mojang.serialization.MapCodec;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.block.DoublePlantBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/** A two-block-tall Venus plant (tree fern, giant fern, glowstalk). */
public class VenusTallPlantBlock extends DoublePlantBlock {
    private final VoxelShape shape;
    private final boolean onStone;

    public VenusTallPlantBlock(Properties properties, VoxelShape shape, boolean onStone) {
        super(properties);
        this.shape = shape;
        this.onStone = onStone;
    }

    @Override
    public MapCodec<? extends DoublePlantBlock> codec() {
        VoxelShape s = shape;
        boolean stone = onStone;
        return simpleCodec(p -> new VenusTallPlantBlock(p, s, stone));
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return shape.move(state.getOffset(pos));
    }

    @Override
    protected boolean mayPlaceOn(BlockState state, BlockGetter level, BlockPos pos) {
        return super.mayPlaceOn(state, level, pos) || (onStone && state.is(VenusPlantBlock.ROCK_FLOOR));
    }
}
