package com.replecant.retrocosmos.oinstein;

import com.mojang.serialization.MapCodec;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.InsideBlockEffectApplier;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.level.block.state.properties.EnumProperty;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * Dr. Oinstein's laser barrier: a sheet of red beams strung between {@link LaserEmitterBlock} posts. While
 * {@code powered} it is solid (a thin pane you cannot pass), glows, hums and burns and throws back whatever touches
 * it. Unbreakable; a future controller switches it off by clearing {@code powered} (see {@link #setPowered}).
 */
public class LaserBarrierBlock extends Block {
    public static final MapCodec<LaserBarrierBlock> CODEC = simpleCodec(LaserBarrierBlock::new);
    public static final EnumProperty<Direction.Axis> AXIS = BlockStateProperties.HORIZONTAL_AXIS;
    public static final BooleanProperty POWERED = BlockStateProperties.POWERED;
    public static final float DAMAGE = 4.0F;
    private static final VoxelShape PLANE_X = Block.box(0, 0, 6.5, 16, 16, 9.5);
    private static final VoxelShape PLANE_Z = Block.box(6.5, 0, 0, 9.5, 16, 16);
    private static final DustParticleOptions RED = new DustParticleOptions(0xFF2A1A, 0.8F);

    public LaserBarrierBlock(Properties properties) {
        super(properties);
        registerDefaultState(stateDefinition.any().setValue(AXIS, Direction.Axis.X).setValue(POWERED, true));
    }

    @Override
    protected MapCodec<? extends Block> codec() {
        return CODEC;
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(AXIS, POWERED);
    }

    @Override
    public BlockState getStateForPlacement(BlockPlaceContext context) {
        return defaultBlockState().setValue(AXIS, context.getHorizontalDirection().getClockWise().getAxis());
    }

    private static VoxelShape plane(BlockState state) {
        return state.getValue(AXIS) == Direction.Axis.X ? PLANE_X : PLANE_Z;
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return state.getValue(POWERED) ? plane(state) : Shapes.empty();
    }

    @Override
    protected VoxelShape getCollisionShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return state.getValue(POWERED) ? plane(state) : Shapes.empty();
    }

    @Override
    protected boolean propagatesSkylightDown(BlockState state) {
        return true;
    }

    @Override
    protected boolean skipRendering(BlockState state, BlockState adjacent, Direction direction) {
        return adjacent.is(this) || super.skipRendering(state, adjacent, direction);
    }

    @Override
    protected BlockState rotate(BlockState state, Rotation rotation) {
        if (rotation == Rotation.CLOCKWISE_90 || rotation == Rotation.COUNTERCLOCKWISE_90) {
            return state.setValue(AXIS, state.getValue(AXIS) == Direction.Axis.X ? Direction.Axis.Z : Direction.Axis.X);
        }
        return state;
    }

    @Override
    protected void entityInside(BlockState state, Level level, BlockPos pos, Entity entity, InsideBlockEffectApplier effects,
                                boolean intersects) {
        if (!state.getValue(POWERED) || !(level instanceof ServerLevel server) || !(entity instanceof LivingEntity living)
                || entity.getType().is(ModOinstein.FORCES)) {
            return;                         // Dr. Oinstein's own forces are keyed to the barrier: it only stops them
        }
        if (living.hurtServer(server, server.damageSources().source(ModOinstein.LASER_DAMAGE), DAMAGE)) {
            double d = state.getValue(AXIS) == Direction.Axis.X ? entity.getZ() - (pos.getZ() + 0.5)
                    : entity.getX() - (pos.getX() + 0.5);
            double s = d >= 0 ? 1.0 : -1.0;
            if (state.getValue(AXIS) == Direction.Axis.X) {
                entity.push(0.0, 0.3, 0.9 * s);
            } else {
                entity.push(0.9 * s, 0.3, 0.0);
            }
            entity.hurtMarked = true;
            level.playSound(null, pos, SoundEvents.BEACON_DEACTIVATE, SoundSource.BLOCKS, 0.8F, 1.8F);
        }
    }

    @Override
    public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
        if (!state.getValue(POWERED)) {
            return;
        }
        if (random.nextInt(3) == 0) {
            boolean x = state.getValue(AXIS) == Direction.Axis.X;
            double a = random.nextDouble();
            level.addParticle(RED, pos.getX() + (x ? a : 0.5), pos.getY() + random.nextDouble(), pos.getZ() + (x ? 0.5 : a),
                    0, 0, 0);
        }
        if (random.nextInt(60) == 0) {
            level.playLocalSound(pos, SoundEvents.BEACON_AMBIENT, SoundSource.BLOCKS, 0.35F, 1.7F, false);
        }
    }

    /** Switches every connected barrier block (and its emitters) on or off - for a future control console. */
    public static void setPowered(Level level, BlockPos start, boolean on) {
        java.util.ArrayDeque<BlockPos> todo = new java.util.ArrayDeque<>();
        java.util.Set<BlockPos> seen = new java.util.HashSet<>();
        todo.add(start);
        while (!todo.isEmpty() && seen.size() < 4096) {
            BlockPos p = todo.poll();
            if (!seen.add(p)) {
                continue;
            }
            BlockState s = level.getBlockState(p);
            if (s.getBlock() instanceof LaserBarrierBlock || s.getBlock() instanceof LaserEmitterBlock) {
                if (s.getValue(POWERED) != on) {
                    level.setBlock(p, s.setValue(POWERED, on), Block.UPDATE_ALL);
                }
                for (Direction d : Direction.values()) {
                    todo.add(p.relative(d));
                }
            }
        }
    }
}
