package com.replecant.retrocosmos.furniture;

import com.mojang.serialization.MapCodec;
import com.replecant.retrocosmos.registry.ModEntities;
import java.util.Map;
import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.level.block.state.properties.EnumProperty;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * Generic Atomic Age furniture block: optional facing, wall mounting, on/off switch with light, and seating.
 * <p>
 * Minecraft builds the state definition inside the Block constructor, before subclass fields are set,
 * so the spec is passed through a thread-local while the constructor runs.
 */
public class FurnitureBlock extends Block {
    public static final EnumProperty<Direction> FACING = BlockStateProperties.HORIZONTAL_FACING;
    public static final BooleanProperty LIT = BlockStateProperties.LIT;

    private static final ThreadLocal<FurnitureSpec> CONSTRUCTING = new ThreadLocal<>();

    private final FurnitureSpec spec;
    private final Map<Direction, VoxelShape> shapes;

    public static FurnitureBlock create(BlockBehaviour.Properties properties, FurnitureSpec spec) {
        CONSTRUCTING.set(spec);
        try {
            return new FurnitureBlock(properties, spec);
        } finally {
            CONSTRUCTING.remove();
        }
    }

    protected FurnitureBlock(BlockBehaviour.Properties properties, FurnitureSpec spec) {
        super(properties);
        this.spec = spec;
        this.shapes = Shapes.rotateHorizontal(spec.shape());
        BlockState state = stateDefinition.any();
        if (spec.facing()) {
            state = state.setValue(FACING, Direction.NORTH);
        }
        if (spec.toggleable()) {
            state = state.setValue(LIT, Boolean.FALSE);
        }
        registerDefaultState(state);
    }

    public FurnitureSpec spec() {
        return spec;
    }

    @Override
    protected MapCodec<? extends Block> codec() {
        FurnitureSpec s = spec;
        return BlockBehaviour.simpleCodec(p -> create(p, s));
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        FurnitureSpec s = spec != null ? spec : CONSTRUCTING.get();
        if (s.facing()) {
            builder.add(FACING);
        }
        if (s.toggleable()) {
            builder.add(LIT);
        }
    }

    /** Light level for a state; used by the block properties. */
    public static int lightLevel(BlockState state, int lightOn) {
        return state.hasProperty(LIT) && state.getValue(LIT) ? lightOn : 0;
    }

    // ------------------------------------------------------------------ placement

    @Nullable
    @Override
    public BlockState getStateForPlacement(BlockPlaceContext context) {
        BlockState state = defaultBlockState();
        if (!spec.facing()) {
            return state;
        }
        if (spec.wall()) {
            Direction face = context.getClickedFace();
            if (face.getAxis().isHorizontal()) {
                state = state.setValue(FACING, face);
                return canSurvive(state, context.getLevel(), context.getClickedPos()) ? state : null;
            }
            for (Direction dir : context.getNearestLookingDirections()) {
                if (dir.getAxis().isHorizontal()) {
                    BlockState candidate = state.setValue(FACING, dir.getOpposite());
                    if (canSurvive(candidate, context.getLevel(), context.getClickedPos())) {
                        return candidate;
                    }
                }
            }
            return null;
        }
        return state.setValue(FACING, context.getHorizontalDirection().getOpposite());
    }

    @Override
    protected boolean canSurvive(BlockState state, LevelReader level, BlockPos pos) {
        if (!spec.wall()) {
            return true;
        }
        Direction back = state.getValue(FACING).getOpposite();
        BlockPos wall = pos.relative(back);
        return level.getBlockState(wall).isFaceSturdy(level, wall, back.getOpposite());
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return spec.facing() ? shapes.get(state.getValue(FACING)) : spec.shape();
    }

    // ------------------------------------------------------------------ interaction

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (spec.toggleable()) {
            if (!level.isClientSide()) {
                boolean on = !state.getValue(LIT);
                level.setBlock(pos, state.setValue(LIT, on), Block.UPDATE_ALL);
                if (spec.toggleSound() != null) {
                    level.playSound(null, pos, spec.toggleSound().value(), SoundSource.BLOCKS, 0.6F, on ? 1.2F : 0.8F);
                } else {
                    level.playSound(null, pos, SoundEvents.LEVER_CLICK, SoundSource.BLOCKS, 0.4F, on ? 0.7F : 0.5F);
                }
            }
            return InteractionResult.SUCCESS;
        }
        if (spec.isSeat()) {
            if (level.isClientSide()) {
                return InteractionResult.SUCCESS;
            }
            if (player.isPassenger() || player.isShiftKeyDown()) {
                return InteractionResult.PASS;
            }
            if (!level.getEntitiesOfClass(SeatEntity.class, new AABB(pos)).isEmpty()) {
                return InteractionResult.FAIL;
            }
            SeatEntity seat = new SeatEntity(ModEntities.SEAT.get(), level);
            seat.setPos(pos.getX() + 0.5, pos.getY() + spec.seatHeight() / 16.0, pos.getZ() + 0.5);
            if (spec.facing()) {
                seat.setYRot(state.getValue(FACING).toYRot());
            }
            level.addFreshEntity(seat);
            player.startRiding(seat);
            return InteractionResult.SUCCESS;
        }
        return InteractionResult.PASS;
    }
}
