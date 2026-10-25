package com.replecant.retrocosmos.furniture;

import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.EntityBlock;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.DoubleBlockHalf;
import net.minecraft.world.phys.BlockHitResult;

/** Lockers, crates and cabinets: furniture with a 27-slot inventory (held by the lower half of tall pieces). */
public class StorageFurnitureBlock extends FurnitureBlock implements EntityBlock {
    public static StorageFurnitureBlock create(BlockBehaviour.Properties properties, FurnitureSpec spec) {
        return construct(() -> new StorageFurnitureBlock(properties, spec), spec);
    }

    protected StorageFurnitureBlock(BlockBehaviour.Properties properties, FurnitureSpec spec) {
        super(properties, spec);
    }

    @Nullable
    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        if (spec().tall() && state.getValue(HALF) == DoubleBlockHalf.UPPER) {
            return null;
        }
        return new StorageBlockEntity(pos, state);
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (!level.isClientSide() && level.getBlockEntity(basePos(state, pos)) instanceof StorageBlockEntity storage) {
            player.openMenu(storage);
        }
        return InteractionResult.SUCCESS;
    }
}
