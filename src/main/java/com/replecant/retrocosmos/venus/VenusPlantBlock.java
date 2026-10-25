package com.replecant.retrocosmos.venus;

import com.mojang.serialization.MapCodec;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.block.VegetationBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * A small Venus plant (sedge, horsetail, cycad, fire lily, glowcap). Grows on soil-like blocks (#minecraft:dirt);
 * fungi ({@code onStone}) also take root on any solid floor, so they can carpet cave bottoms.
 */
public class VenusPlantBlock extends VegetationBlock {
    private final VoxelShape shape;
    private final boolean onStone;

    public VenusPlantBlock(Properties properties, VoxelShape shape, boolean onStone) {
        super(properties);
        this.shape = shape;
        this.onStone = onStone;
    }

    @Override
    protected MapCodec<? extends VegetationBlock> codec() {
        VoxelShape s = shape;
        boolean stone = onStone;
        return simpleCodec(p -> new VenusPlantBlock(p, s, stone));
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return shape.move(state.getOffset(pos));
    }

    @Override
    protected boolean mayPlaceOn(BlockState state, BlockGetter level, BlockPos pos) {
        return super.mayPlaceOn(state, level, pos) || (onStone && state.isFaceSturdy(level, pos, Direction.UP));
    }
}
