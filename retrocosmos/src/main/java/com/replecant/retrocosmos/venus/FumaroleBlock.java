package com.replecant.retrocosmos.venus;

import com.mojang.serialization.MapCodec;
import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.EntityBlock;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;

/**
 * A volcanic vent of glowing black rock. In the open it sends up a tall plume of smoke that can be seen from far
 * away (cinder cones, highlands); under water it makes a hot spring bubble and steam at the surface.
 */
public class FumaroleBlock extends Block implements EntityBlock {
    public static final MapCodec<FumaroleBlock> CODEC = simpleCodec(FumaroleBlock::new);

    public FumaroleBlock(Properties properties) {
        super(properties);
    }

    @Override
    protected MapCodec<? extends Block> codec() {
        return CODEC;
    }

    @Nullable
    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new FumaroleBlockEntity(pos, state);
    }

    @Nullable
    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
        if (!level.isClientSide() || type != ModVenus.FUMAROLE_BE.get()) {
            return null;
        }
        return (l, pos, s, be) -> FumaroleBlockEntity.clientTick(l, pos);
    }
}
