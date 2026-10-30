package com.replecant.retrocosmos.furniture;

import com.replecant.retrocosmos.registry.ModBlockEntities;
import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.EntityBlock;
import net.minecraft.world.level.block.entity.AbstractFurnaceBlockEntity;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;

/** Galley oven: cooks food like a smoker; its window glows while it works ({@code lit} is driven by the oven). */
public class GalleyStoveBlock extends FurnitureBlock implements EntityBlock {
    public static GalleyStoveBlock create(BlockBehaviour.Properties properties, FurnitureSpec spec) {
        return construct(() -> new GalleyStoveBlock(properties, spec), spec);
    }

    protected GalleyStoveBlock(BlockBehaviour.Properties properties, FurnitureSpec spec) {
        super(properties, spec);
    }

    @Nullable
    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new GalleyStoveBlockEntity(pos, state);
    }

    @Nullable
    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
        if (!(level instanceof ServerLevel) || type != ModBlockEntities.GALLEY_STOVE.get()) {
            return null;
        }
        return (l, pos, s, be) -> AbstractFurnaceBlockEntity.serverTick((ServerLevel) l, pos, s, (AbstractFurnaceBlockEntity) be);
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (!level.isClientSide() && level.getBlockEntity(pos) instanceof GalleyStoveBlockEntity stove) {
            player.openMenu(stove);
        }
        return InteractionResult.SUCCESS;
    }
}
