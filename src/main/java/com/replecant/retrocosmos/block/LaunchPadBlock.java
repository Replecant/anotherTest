package com.replecant.retrocosmos.block;

import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.util.RandomSource;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.ScheduledTickAccess;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.EnumProperty;

/**
 * Reinforced steel launch pad slab. Nine of them form a 3x3 "Launch Complex"; the rocket stands on the
 * centre block. Each block picks its look (single / centre / edge / corner) from its horizontal neighbours,
 * so the slab reads as one big pad with hazard stripes only along the outer rim.
 */
public class LaunchPadBlock extends Block {
    public static final EnumProperty<PadPart> PART = EnumProperty.create("part", PadPart.class);
    public static final EnumProperty<Direction> FACING = BlockStateProperties.HORIZONTAL_FACING;

    public LaunchPadBlock(BlockBehaviour.Properties properties) {
        super(properties);
        registerDefaultState(stateDefinition.any().setValue(PART, PadPart.SINGLE).setValue(FACING, Direction.NORTH));
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(PART, FACING);
    }

    @Nullable
    @Override
    public BlockState getStateForPlacement(BlockPlaceContext context) {
        return shapeFor(defaultBlockState(), context.getLevel(), context.getClickedPos());
    }

    @Override
    protected BlockState updateShape(BlockState state, LevelReader level, ScheduledTickAccess ticks, BlockPos pos,
                                     Direction direction, BlockPos neighborPos, BlockState neighborState, RandomSource random) {
        if (direction.getAxis().isHorizontal()) {
            return shapeFor(state, level, pos);
        }
        return super.updateShape(state, level, ticks, pos, direction, neighborPos, neighborState, random);
    }

    private static boolean isPad(BlockGetter level, BlockPos pos) {
        return level.getBlockState(pos).getBlock() instanceof LaunchPadBlock;
    }

    public static BlockState shapeFor(BlockState state, BlockGetter level, BlockPos pos) {
        boolean n = isPad(level, pos.north());
        boolean s = isPad(level, pos.south());
        boolean e = isPad(level, pos.east());
        boolean w = isPad(level, pos.west());
        int missing = (n ? 0 : 1) + (s ? 0 : 1) + (e ? 0 : 1) + (w ? 0 : 1);
        if (missing == 0) {
            return state.setValue(PART, PadPart.CENTER).setValue(FACING, Direction.NORTH);
        }
        if (missing == 1) {
            Direction open = !n ? Direction.NORTH : !s ? Direction.SOUTH : !e ? Direction.EAST : Direction.WEST;
            return state.setValue(PART, PadPart.EDGE).setValue(FACING, open);
        }
        if (missing == 2 && (n != s)) {
            // Corner: the default corner model has stripes on its north and west sides (a north-west corner).
            Direction facing = !n ? (!w ? Direction.NORTH : Direction.EAST) : (!e ? Direction.SOUTH : Direction.WEST);
            return state.setValue(PART, PadPart.CORNER).setValue(FACING, facing);
        }
        return state.setValue(PART, PadPart.SINGLE).setValue(FACING, Direction.NORTH);
    }

    /** Number of launch pad blocks in the 3x3 square centred on {@code center}. */
    public static int countPad(BlockGetter level, BlockPos center) {
        int count = 0;
        for (int dx = -1; dx <= 1; dx++) {
            for (int dz = -1; dz <= 1; dz++) {
                if (isPad(level, center.offset(dx, 0, dz))) {
                    count++;
                }
            }
        }
        return count;
    }
}
