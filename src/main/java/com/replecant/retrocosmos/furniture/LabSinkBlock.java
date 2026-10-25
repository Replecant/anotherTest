package com.replecant.retrocosmos.furniture;

import net.minecraft.core.BlockPos;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.ItemUtils;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.alchemy.PotionContents;
import net.minecraft.world.item.alchemy.Potions;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;

/** Stainless station sink: fills glass bottles and buckets from the recycled water supply. */
public class LabSinkBlock extends FurnitureBlock {
    public static LabSinkBlock create(BlockBehaviour.Properties properties, FurnitureSpec spec) {
        return construct(() -> new LabSinkBlock(properties, spec), spec);
    }

    protected LabSinkBlock(BlockBehaviour.Properties properties, FurnitureSpec spec) {
        super(properties, spec);
    }

    @Override
    protected InteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos, Player player,
                                          InteractionHand hand, BlockHitResult hit) {
        ItemStack filled;
        if (stack.is(Items.GLASS_BOTTLE)) {
            filled = PotionContents.createItemStack(Items.POTION, Potions.WATER);
        } else if (stack.is(Items.BUCKET)) {
            filled = new ItemStack(Items.WATER_BUCKET);
        } else {
            return InteractionResult.TRY_WITH_EMPTY_HAND;
        }
        if (!level.isClientSide()) {
            player.setItemInHand(hand, ItemUtils.createFilledResult(stack, player, filled));
            level.playSound(null, pos, stack.is(Items.BUCKET) ? SoundEvents.BUCKET_FILL : SoundEvents.BOTTLE_FILL, SoundSource.BLOCKS, 1.0F, 1.0F);
        }
        return InteractionResult.SUCCESS;
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (!level.isClientSide()) {
            level.playSound(null, pos, SoundEvents.BUCKET_EMPTY, SoundSource.BLOCKS, 0.5F, 1.4F);
        }
        return InteractionResult.SUCCESS;
    }
}
