package com.replecant.retrocosmos.block;

import com.replecant.retrocosmos.launch.LaunchSite;
import com.replecant.retrocosmos.registry.ModItems;
import javax.annotation.Nullable;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.ItemUtils;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.ScheduledTickAccess;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.EnumProperty;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * The "Liberty I" rocket - sleek raygun-gothic silhouette, chrome needle, red swept fins - a nine block tall
 * structure standing on the centre of a 3x3 launch pad. The models extend past the centre column (the hull is
 * 1.5 blocks wide, the fins span the full 3x3 pad); collision stays inside the centre column.
 * <ul>
 *     <li>Right click with an RP-1 kerosene canister to load fuel, with a liquid oxygen canister to load oxidizer.</li>
 *     <li>Right click with an empty hand to run the pre-flight checklist (3x3 pad, service tower, propellants, suit).</li>
 * </ul>
 * The countdown itself is run from the Mission Control console; the actual flight arrives in stage 2.
 */
public class RocketBlock extends Block {
    public static final EnumProperty<RocketPart> PART = EnumProperty.create("part", RocketPart.class);
    public static final int MAX_FUEL = 4;
    public static final IntegerProperty FUEL = IntegerProperty.create("fuel", 0, MAX_FUEL);
    public static final IntegerProperty OXIDIZER = IntegerProperty.create("oxidizer", 0, MAX_FUEL);

    // Collision stays inside the centre column; the visual hull is wider (see tools/gen_resources.py).
    private static final VoxelShape SHAPE_FULL = Shapes.block();
    private static final VoxelShape SHAPE_SHOULDER = Shapes.or(Block.box(0, 0, 0, 16, 6, 16), Block.box(1, 6, 1, 15, 16, 15));
    private static final VoxelShape SHAPE_CONE = Shapes.or(Block.box(1, 0, 1, 15, 6, 15), Block.box(3, 6, 3, 13, 12, 13), Block.box(5, 12, 5, 11, 16, 11));
    private static final VoxelShape SHAPE_NEEDLE = Shapes.or(Block.box(5, 0, 5, 11, 5, 11), Block.box(6.5, 5, 6.5, 9.5, 10, 9.5), Block.box(7.5, 10, 7.5, 8.5, 16, 8.5));

    public RocketBlock(BlockBehaviour.Properties properties) {
        super(properties);
        registerDefaultState(stateDefinition.any().setValue(PART, RocketPart.ENGINE).setValue(FUEL, 0).setValue(OXIDIZER, 0));
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(PART, FUEL, OXIDIZER);
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return switch (state.getValue(PART)) {
            case SHOULDER -> SHAPE_SHOULDER;
            case CONE -> SHAPE_CONE;
            case NEEDLE -> SHAPE_NEEDLE;
            default -> SHAPE_FULL;
        };
    }

    // ------------------------------------------------------------------
    // Multi-block placement / removal
    // ------------------------------------------------------------------

    @Nullable
    @Override
    public BlockState getStateForPlacement(BlockPlaceContext context) {
        BlockPos pos = context.getClickedPos();
        Level level = context.getLevel();
        if (pos.getY() + RocketPart.HEIGHT - 1 > level.getMaxY()) {
            return null;
        }
        for (int i = 1; i < RocketPart.HEIGHT; i++) {
            if (!level.getBlockState(pos.above(i)).canBeReplaced(context)) {
                return null;
            }
        }
        return defaultBlockState();
    }

    @Override
    public void setPlacedBy(Level level, BlockPos pos, BlockState state, @Nullable LivingEntity placer, ItemStack stack) {
        for (int i = 1; i < RocketPart.HEIGHT; i++) {
            level.setBlock(pos.above(i), state.setValue(PART, RocketPart.byOffset(i)), Block.UPDATE_ALL);
        }
    }

    @Override
    protected BlockState updateShape(BlockState state, LevelReader level, ScheduledTickAccess ticks, BlockPos pos,
                                     Direction direction, BlockPos neighborPos, BlockState neighborState, RandomSource random) {
        RocketPart part = state.getValue(PART);
        boolean needsBelow = !part.isBase();
        boolean needsAbove = !part.isTop();
        if (direction == Direction.DOWN && needsBelow && !isPart(neighborState, part.offset() - 1)) {
            return Blocks.AIR.defaultBlockState();
        }
        if (direction == Direction.UP && needsAbove && !isPart(neighborState, part.offset() + 1)) {
            return Blocks.AIR.defaultBlockState();
        }
        return super.updateShape(state, level, ticks, pos, direction, neighborPos, neighborState, random);
    }

    private boolean isPart(BlockState state, int offset) {
        return state.is(this) && state.getValue(PART).offset() == offset;
    }

    @Override
    public BlockState playerWillDestroy(Level level, BlockPos pos, BlockState state, Player player) {
        // Only the bottom part drops the rocket item, so when a player breaks an upper part
        // we break the base "properly" (with drops in survival) and let the rest collapse.
        if (!level.isClientSide() && !state.getValue(PART).isBase()) {
            BlockPos base = basePos(state, pos);
            BlockState baseState = level.getBlockState(base);
            if (baseState.is(this)) {
                if (!player.isCreative()) {
                    Block.dropResources(baseState, level, base, null, player, player.getMainHandItem());
                }
                level.setBlock(base, Blocks.AIR.defaultBlockState(), Block.UPDATE_ALL | Block.UPDATE_SUPPRESS_DROPS);
            }
        }
        return super.playerWillDestroy(level, pos, state, player);
    }

    private static BlockPos basePos(BlockState state, BlockPos pos) {
        return pos.below(state.getValue(PART).offset());
    }

    private void setTank(Level level, BlockPos base, IntegerProperty tank, int amount) {
        for (int i = 0; i < RocketPart.HEIGHT; i++) {
            BlockPos p = base.above(i);
            BlockState s = level.getBlockState(p);
            if (s.is(this)) {
                level.setBlock(p, s.setValue(tank, amount), Block.UPDATE_CLIENTS);
            }
        }
    }

    // ------------------------------------------------------------------
    // Interaction
    // ------------------------------------------------------------------

    @Override
    protected InteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos, Player player,
                                          InteractionHand hand, BlockHitResult hit) {
        IntegerProperty tank;
        String key;
        if (stack.is(ModItems.ROCKET_FUEL_CANISTER.get())) {
            tank = FUEL;
            key = "message.retrocosmos.rocket.fueled";
        } else if (stack.is(ModItems.LIQUID_OXYGEN_CANISTER.get())) {
            tank = OXIDIZER;
            key = "message.retrocosmos.rocket.oxidized";
        } else {
            return InteractionResult.TRY_WITH_EMPTY_HAND;
        }
        int amount = state.getValue(tank);
        if (amount >= MAX_FUEL) {
            if (!level.isClientSide()) {
                player.displayClientMessage(Component.translatable("message.retrocosmos.rocket.fuel_full").withStyle(ChatFormatting.YELLOW), true);
            }
            return InteractionResult.FAIL;
        }
        if (!level.isClientSide()) {
            setTank(level, basePos(state, pos), tank, amount + 1);
            player.setItemInHand(hand, ItemUtils.createFilledResult(stack, player, new ItemStack(ModItems.EMPTY_FUEL_CANISTER.get())));
            level.playSound(null, pos, tank == FUEL ? SoundEvents.BUCKET_EMPTY_LAVA : SoundEvents.BUCKET_EMPTY, SoundSource.BLOCKS, 1.0F, 0.8F);
            player.displayClientMessage(Component.translatable(key, amount + 1, MAX_FUEL).withStyle(ChatFormatting.GOLD), true);
        }
        return InteractionResult.SUCCESS;
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (level.isClientSide()) {
            return InteractionResult.SUCCESS;
        }
        BlockPos base = basePos(state, pos);
        LaunchSite.Status status = LaunchSite.inspect(level, base);
        LaunchSite.sendChecklist(player, status);

        if (status.go(LaunchSite.suitBits(player))) {
            player.displayClientMessage(Component.translatable("message.retrocosmos.checklist.go_to_console").withStyle(ChatFormatting.GRAY, ChatFormatting.ITALIC), false);
            level.playSound(null, base, SoundEvents.BEACON_ACTIVATE, SoundSource.BLOCKS, 1.0F, 1.2F);
            if (level instanceof ServerLevel serverLevel) {
                serverLevel.sendParticles(ParticleTypes.CAMPFIRE_COSY_SMOKE,
                        base.getX() + 0.5, base.getY() + 0.2, base.getZ() + 0.5, 20, 0.6, 0.1, 0.6, 0.02);
                if (player instanceof ServerPlayer serverPlayer) {
                    LaunchSite.award(serverPlayer, "stage1/ready_for_launch", "checklist_passed");
                }
            }
        } else {
            level.playSound(null, base, SoundEvents.NOTE_BLOCK_BASS.value(), SoundSource.BLOCKS, 1.0F, 0.5F);
        }
        return InteractionResult.SUCCESS;
    }
}
