package com.replecant.retrocosmos.furniture;

import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.SimpleMenuProvider;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerLevelAccess;
import net.minecraft.world.inventory.CraftingMenu;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;

/** The station work bench: a crafting table in Atomic Age enamel. */
public class WorkbenchBlock extends FurnitureBlock {
    public static WorkbenchBlock create(BlockBehaviour.Properties properties, FurnitureSpec spec) {
        return construct(() -> new WorkbenchBlock(properties, spec), spec);
    }

    protected WorkbenchBlock(BlockBehaviour.Properties properties, FurnitureSpec spec) {
        super(properties, spec);
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (!level.isClientSide()) {
            ContainerLevelAccess access = ContainerLevelAccess.create(level, pos);
            player.openMenu(new SimpleMenuProvider((id, inventory, p) -> new CraftingMenu(id, inventory, access) {
                @Override
                public boolean stillValid(Player viewer) {
                    return AbstractContainerMenu.stillValid(access, viewer, WorkbenchBlock.this);
                }
            }, Component.translatable("container.crafting")));
        }
        return InteractionResult.SUCCESS;
    }
}
