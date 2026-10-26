package com.replecant.retrocosmos.oinstein;

import com.mojang.serialization.MapCodec;
import java.util.Optional;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.util.StringRepresentable;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.EnumProperty;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * The keycard reader beside each laser barrier of the Oinstein Institute: a wall panel with a card slot, a lamp and its
 * clearance {@link #LEVEL} (a / b / c). Swiping the matching {@link KeycardItem} (held in either hand) turns the lamp
 * green for good and switches the barrier grid it guards off ({@link #unlock}); a wrong card or an empty hand flashes
 * it red, buzzes and names the card needed. Unbreakable, like the barrier.
 *
 * <p>The guarded barrier is the nearest {@link LaserBarrierBlock} or {@link LaserEmitterBlock} within {@link #RANGE}
 * blocks; {@link LaserBarrierBlock#setPowered} then switches the whole connected grid.
 */
public class KeycardReaderBlock extends HorizontalDirectionalBlock {
    public static final MapCodec<KeycardReaderBlock> CODEC = simpleCodec(KeycardReaderBlock::new);
    public static final EnumProperty<Clearance> LEVEL = EnumProperty.create("level", Clearance.class);
    public static final EnumProperty<Status> STATUS = EnumProperty.create("status", Status.class);
    /** How far from the reader the guarded barrier may stand. */
    public static final int RANGE = 6;
    private static final VoxelShape NORTH = Block.box(3, 1, 14, 13, 15, 16);
    private static final VoxelShape SOUTH = Block.box(3, 1, 0, 13, 15, 2);
    private static final VoxelShape EAST = Block.box(0, 1, 3, 2, 15, 13);
    private static final VoxelShape WEST = Block.box(14, 1, 3, 16, 15, 13);

    public enum Clearance implements StringRepresentable {
        A("a", "keycard_alpha", ChatFormatting.RED),
        B("b", "keycard_beta", ChatFormatting.BLUE),
        C("c", "keycard_gamma", ChatFormatting.GREEN);

        private final String name;
        private final String card;
        private final ChatFormatting color;

        Clearance(String name, String card, ChatFormatting color) {
            this.name = name;
            this.card = card;
            this.color = color;
        }

        @Override
        public String getSerializedName() {
            return name;
        }

        /** The item id path of the card of this level ("keycard_alpha" ...). */
        public String card() {
            return card;
        }

        public Component cardName() {
            return Component.translatable("item.retrocosmos." + card).withStyle(color);
        }
    }

    public enum Status implements StringRepresentable {
        LOCKED("locked"), DENIED("denied"), GRANTED("granted");

        private final String name;

        Status(String name) {
            this.name = name;
        }

        @Override
        public String getSerializedName() {
            return name;
        }
    }

    public KeycardReaderBlock(Properties properties) {
        super(properties);
        registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH).setValue(LEVEL, Clearance.A)
                .setValue(STATUS, Status.LOCKED));
    }

    @Override
    protected MapCodec<? extends HorizontalDirectionalBlock> codec() {
        return CODEC;
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(FACING, LEVEL, STATUS);
    }

    @Override
    public BlockState getStateForPlacement(BlockPlaceContext context) {
        Direction face = context.getClickedFace();
        return defaultBlockState().setValue(FACING, face.getAxis().isHorizontal() ? face
                : context.getHorizontalDirection().getOpposite());
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return switch (state.getValue(FACING)) {
            case SOUTH -> SOUTH;
            case EAST -> EAST;
            case WEST -> WEST;
            default -> NORTH;
        };
    }

    @Override
    protected InteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos, Player player,
                                          InteractionHand hand, BlockHitResult hit) {
        return swipe(state, level, pos, player);
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        return swipe(state, level, pos, player);
    }

    private InteractionResult swipe(BlockState state, Level level, BlockPos pos, Player player) {
        if (level.isClientSide()) {
            return InteractionResult.SUCCESS;
        }
        Clearance need = state.getValue(LEVEL);
        if (state.getValue(STATUS) == Status.GRANTED) {
            unlock(level, pos);                               // idempotent: keeps the grid off
            player.displayClientMessage(Component.translatable("message.retrocosmos.keycard.open")
                    .withStyle(ChatFormatting.GREEN), true);
            return InteractionResult.SUCCESS;
        }
        if (holds(player, need)) {
            level.setBlock(pos, state.setValue(STATUS, Status.GRANTED), Block.UPDATE_ALL);
            unlock(level, pos);
            level.playSound(null, pos, SoundEvents.NOTE_BLOCK_CHIME.value(), SoundSource.BLOCKS, 1.0F, 1.6F);
            level.playSound(null, pos, SoundEvents.NOTE_BLOCK_BELL.value(), SoundSource.BLOCKS, 0.8F, 2.0F);
            if (level instanceof ServerLevel server) {
                server.sendParticles(ParticleTypes.HAPPY_VILLAGER, pos.getX() + 0.5, pos.getY() + 0.6, pos.getZ() + 0.5,
                        6, 0.25, 0.25, 0.25, 0.0);
            }
            player.displayClientMessage(Component.translatable("message.retrocosmos.keycard.granted")
                    .withStyle(ChatFormatting.GREEN), true);
        } else {
            level.setBlock(pos, state.setValue(STATUS, Status.DENIED), Block.UPDATE_ALL);
            level.scheduleTick(pos, this, 16);
            level.playSound(null, pos, SoundEvents.NOTE_BLOCK_BASS.value(), SoundSource.BLOCKS, 1.0F, 0.5F);
            level.playSound(null, pos, SoundEvents.NOTE_BLOCK_DIDGERIDOO.value(), SoundSource.BLOCKS, 0.7F, 0.6F);
            player.displayClientMessage(Component.translatable("message.retrocosmos.keycard.required", need.cardName())
                    .withStyle(ChatFormatting.RED), true);
        }
        return InteractionResult.SUCCESS;
    }

    private static boolean holds(Player player, Clearance need) {
        return KeycardItem.clearanceOf(player.getMainHandItem()).filter(c -> c == need).isPresent()
                || KeycardItem.clearanceOf(player.getOffhandItem()).filter(c -> c == need).isPresent();
    }

    @Override
    protected void tick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
        if (state.getValue(STATUS) == Status.DENIED) {
            level.setBlock(pos, state.setValue(STATUS, Status.LOCKED), Block.UPDATE_ALL);
        }
    }

    /** The barrier or emitter nearest to the reader (within {@link #RANGE}): a block of the grid it guards. */
    public static Optional<BlockPos> findGuardedBarrier(BlockGetter level, BlockPos reader) {
        BlockPos best = null;
        double bestDist = Double.MAX_VALUE;
        for (BlockPos p : BlockPos.betweenClosed(reader.offset(-RANGE, -RANGE, -RANGE), reader.offset(RANGE, RANGE, RANGE))) {
            Block block = level.getBlockState(p).getBlock();
            if (block instanceof LaserBarrierBlock || block instanceof LaserEmitterBlock) {
                double d = p.distSqr(reader);
                if (d < bestDist) {
                    bestDist = d;
                    best = p.immutable();
                }
            }
        }
        return Optional.ofNullable(best);
    }

    /** Switches the barrier grid next to the reader at {@code reader} off (for good); false if there is none. */
    public static boolean unlock(Level level, BlockPos reader) {
        Optional<BlockPos> barrier = findGuardedBarrier(level, reader);
        barrier.ifPresent(p -> {
            if (level.getBlockState(p).getValue(LaserBarrierBlock.POWERED)) {
                level.playSound(null, p, SoundEvents.BEACON_DEACTIVATE, SoundSource.BLOCKS, 1.0F, 0.8F);
            }
            LaserBarrierBlock.setPowered(level, p, false);
        });
        return barrier.isPresent();
    }
}
