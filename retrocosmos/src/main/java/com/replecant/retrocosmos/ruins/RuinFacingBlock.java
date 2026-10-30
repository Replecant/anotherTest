package com.replecant.retrocosmos.ruins;

import com.mojang.serialization.MapCodec;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * A carved block with a front face (sun-disc relief, stele). The shape is given for a block facing north
 * or south and turned for east/west.
 */
public class RuinFacingBlock extends HorizontalDirectionalBlock {
    public static final MapCodec<RuinFacingBlock> CODEC = simpleCodec(p -> new RuinFacingBlock(p, Shapes.block()));
    private final VoxelShape shapeNorthSouth;
    private final VoxelShape shapeEastWest;

    public RuinFacingBlock(Properties properties, VoxelShape shape) {
        super(properties);
        this.shapeNorthSouth = shape;
        this.shapeEastWest = turn(shape);
        registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH));
    }

    private static VoxelShape turn(VoxelShape shape) {
        VoxelShape[] out = {Shapes.empty()};
        shape.forAllBoxes((x0, y0, z0, x1, y1, z1) -> out[0] = Shapes.or(out[0], Shapes.box(z0, y0, x0, z1, y1, x1)));
        return out[0];
    }

    @Override
    protected MapCodec<? extends HorizontalDirectionalBlock> codec() {
        return CODEC;
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(FACING);
    }

    @Override
    public BlockState getStateForPlacement(BlockPlaceContext context) {
        return defaultBlockState().setValue(FACING, context.getHorizontalDirection().getOpposite());
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return state.getValue(FACING).getAxis() == Direction.Axis.X ? shapeEastWest : shapeNorthSouth;
    }

    @Override
    protected BlockState rotate(BlockState state, Rotation rotation) {
        return state.setValue(FACING, rotation.rotate(state.getValue(FACING)));
    }
}
