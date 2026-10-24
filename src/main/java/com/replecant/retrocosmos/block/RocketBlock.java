package com.replecant.retrocosmos.block;

import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.registry.ModBlocks;
import com.replecant.retrocosmos.registry.ModItems;
import javax.annotation.Nullable;
import net.minecraft.ChatFormatting;
import net.minecraft.advancements.AdvancementHolder;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.EquipmentSlot;
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
 * The "Zarya-1" rocket: a three block tall structure (bottom / middle / top).
 * <ul>
 *     <li>Right click with a rocket fuel canister to fuel it up.</li>
 *     <li>Right click with an empty hand to run the pre-flight checklist.</li>
 * </ul>
 * The actual flight to other planets arrives in stage 2.
 */
public class RocketBlock extends Block {
    public static final EnumProperty<RocketPart> PART = EnumProperty.create("part", RocketPart.class);
    public static final int MAX_FUEL = 4;
    public static final IntegerProperty FUEL = IntegerProperty.create("fuel", 0, MAX_FUEL);

    private static final VoxelShape SHAPE_BOTTOM = Shapes.or(
            Block.box(3, 3, 3, 13, 16, 13),
            Block.box(5, 0, 5, 11, 3, 11),
            Block.box(0, 0, 7, 16, 9, 9),
            Block.box(7, 0, 0, 9, 9, 16));
    private static final VoxelShape SHAPE_MIDDLE = Block.box(3, 0, 3, 13, 16, 13);
    private static final VoxelShape SHAPE_TOP = Shapes.or(
            Block.box(4, 0, 4, 12, 6, 12),
            Block.box(5, 6, 5, 11, 11, 11),
            Block.box(6, 11, 6, 10, 14, 10),
            Block.box(7.5, 14, 7.5, 8.5, 16, 8.5));

    private static final Identifier READY_ADVANCEMENT = Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "stage1/ready_for_launch");

    public RocketBlock(BlockBehaviour.Properties properties) {
        super(properties);
        registerDefaultState(stateDefinition.any().setValue(PART, RocketPart.BOTTOM).setValue(FUEL, 0));
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(PART, FUEL);
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return switch (state.getValue(PART)) {
            case BOTTOM -> SHAPE_BOTTOM;
            case MIDDLE -> SHAPE_MIDDLE;
            case TOP -> SHAPE_TOP;
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
        if (pos.getY() + 2 > level.getMaxY()) {
            return null;
        }
        if (!level.getBlockState(pos.above()).canBeReplaced(context) || !level.getBlockState(pos.above(2)).canBeReplaced(context)) {
            return null;
        }
        return defaultBlockState();
    }

    @Override
    public void setPlacedBy(Level level, BlockPos pos, BlockState state, @Nullable LivingEntity placer, ItemStack stack) {
        level.setBlock(pos.above(), state.setValue(PART, RocketPart.MIDDLE), Block.UPDATE_ALL);
        level.setBlock(pos.above(2), state.setValue(PART, RocketPart.TOP), Block.UPDATE_ALL);
    }

    @Override
    protected BlockState updateShape(BlockState state, LevelReader level, ScheduledTickAccess ticks, BlockPos pos,
                                     Direction direction, BlockPos neighborPos, BlockState neighborState, RandomSource random) {
        RocketPart part = state.getValue(PART);
        boolean needsBelow = part != RocketPart.BOTTOM;
        boolean needsAbove = part != RocketPart.TOP;
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
        if (!level.isClientSide() && state.getValue(PART) != RocketPart.BOTTOM) {
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

    private void setFuel(Level level, BlockPos base, int fuel) {
        for (int i = 0; i < 3; i++) {
            BlockPos p = base.above(i);
            BlockState s = level.getBlockState(p);
            if (s.is(this)) {
                level.setBlock(p, s.setValue(FUEL, fuel), Block.UPDATE_CLIENTS);
            }
        }
    }

    // ------------------------------------------------------------------
    // Interaction
    // ------------------------------------------------------------------

    @Override
    protected InteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos, Player player,
                                          InteractionHand hand, BlockHitResult hit) {
        if (!stack.is(ModItems.ROCKET_FUEL_CANISTER.get())) {
            return InteractionResult.TRY_WITH_EMPTY_HAND;
        }
        int fuel = state.getValue(FUEL);
        if (fuel >= MAX_FUEL) {
            if (!level.isClientSide()) {
                player.displayClientMessage(Component.translatable("message.retrocosmos.rocket.fuel_full").withStyle(ChatFormatting.YELLOW), true);
            }
            return InteractionResult.FAIL;
        }
        if (!level.isClientSide()) {
            setFuel(level, basePos(state, pos), fuel + 1);
            player.setItemInHand(hand, ItemUtils.createFilledResult(stack, player, new ItemStack(ModItems.EMPTY_FUEL_CANISTER.get())));
            level.playSound(null, pos, SoundEvents.BUCKET_EMPTY_LAVA, SoundSource.BLOCKS, 1.0F, 0.8F);
            player.displayClientMessage(Component.translatable("message.retrocosmos.rocket.fueled", fuel + 1, MAX_FUEL)
                    .withStyle(ChatFormatting.GOLD), true);
        }
        return InteractionResult.SUCCESS;
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (level.isClientSide()) {
            return InteractionResult.SUCCESS;
        }
        BlockPos base = basePos(state, pos);
        boolean onPad = level.getBlockState(base.below()).is(ModBlocks.LAUNCH_PAD.get());
        int fuel = state.getValue(FUEL);
        boolean fueled = fuel >= MAX_FUEL;
        boolean suited = player.getItemBySlot(EquipmentSlot.HEAD).is(ModItems.SPACE_HELMET.get())
                && player.getItemBySlot(EquipmentSlot.CHEST).is(ModItems.SPACE_SUIT.get())
                && player.getItemBySlot(EquipmentSlot.LEGS).is(ModItems.SPACE_LEGGINGS.get())
                && player.getItemBySlot(EquipmentSlot.FEET).is(ModItems.SPACE_BOOTS.get());

        player.displayClientMessage(Component.translatable("message.retrocosmos.checklist.title")
                .withStyle(ChatFormatting.AQUA, ChatFormatting.BOLD), false);
        player.displayClientMessage(check(onPad, Component.translatable("message.retrocosmos.checklist.pad")), false);
        player.displayClientMessage(check(fueled, Component.translatable("message.retrocosmos.checklist.fuel", fuel, MAX_FUEL)), false);
        player.displayClientMessage(check(suited, Component.translatable("message.retrocosmos.checklist.suit")), false);

        if (onPad && fueled && suited) {
            player.displayClientMessage(Component.translatable("message.retrocosmos.checklist.ready").withStyle(ChatFormatting.GREEN), false);
            player.displayClientMessage(Component.translatable("message.retrocosmos.checklist.stage2").withStyle(ChatFormatting.GRAY, ChatFormatting.ITALIC), false);
            level.playSound(null, base, SoundEvents.BEACON_ACTIVATE, SoundSource.BLOCKS, 1.0F, 1.2F);
            if (level instanceof ServerLevel serverLevel) {
                serverLevel.sendParticles(ParticleTypes.CAMPFIRE_COSY_SMOKE,
                        base.getX() + 0.5, base.getY() + 0.2, base.getZ() + 0.5, 20, 0.6, 0.1, 0.6, 0.02);
                if (player instanceof ServerPlayer serverPlayer) {
                    AdvancementHolder advancement = serverLevel.getServer().getAdvancements().get(READY_ADVANCEMENT);
                    if (advancement != null) {
                        serverPlayer.getAdvancements().award(advancement, "checklist_passed");
                    }
                }
            }
        } else {
            player.displayClientMessage(Component.translatable("message.retrocosmos.checklist.not_ready").withStyle(ChatFormatting.RED), false);
            level.playSound(null, base, SoundEvents.NOTE_BLOCK_BASS.value(), SoundSource.BLOCKS, 1.0F, 0.5F);
        }
        return InteractionResult.SUCCESS;
    }

    private static Component check(boolean ok, Component text) {
        return Component.literal(ok ? " [✔] " : " [✘] ")
                .withStyle(ok ? ChatFormatting.GREEN : ChatFormatting.RED)
                .append(text.copy().withStyle(ChatFormatting.WHITE));
    }
}
