package com.replecant.retrocosmos.oinstein;

import com.mojang.serialization.MapCodec;
import com.replecant.retrocosmos.tribe.ModTribes;
import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * Dr. Oinstein's boss anchor: an invisible, unbreakable, walk-through marker in the middle of his arena. When a
 * survival player comes within 20 blocks it brings out the Atomic Strider (unless the doctor is already beaten or
 * about). Selectable only while holding it, like a light block. See {@link OinsteinBossAnchorBlockEntity}.
 */
public class OinsteinBossAnchorBlock extends BaseEntityBlock {
    public static final MapCodec<OinsteinBossAnchorBlock> CODEC = simpleCodec(OinsteinBossAnchorBlock::new);

    public OinsteinBossAnchorBlock(Properties properties) {
        super(properties);
    }

    @Override
    protected MapCodec<? extends BaseEntityBlock> codec() {
        return CODEC;
    }

    @Override
    protected RenderShape getRenderShape(BlockState state) {
        return RenderShape.INVISIBLE;
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return context.isHoldingItem(asItem()) ? Shapes.block() : Shapes.empty();
    }

    @Override
    protected VoxelShape getCollisionShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return Shapes.empty();
    }

    @Override
    protected boolean propagatesSkylightDown(BlockState state) {
        return true;
    }

    @Override
    protected float getShadeBrightness(BlockState state, BlockGetter level, BlockPos pos) {
        return 1.0F;
    }

    @Nullable
    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new OinsteinBossAnchorBlockEntity(pos, state);
    }

    @Nullable
    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
        if (level.isClientSide() || type != ModTribes.OINSTEIN_BOSS_ANCHOR_BE.get()) {
            return null;
        }
        return (l, pos, s, be) -> ((OinsteinBossAnchorBlockEntity) be).serverTick(l);
    }
}
