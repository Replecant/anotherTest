package com.replecant.retrocosmos.oxygen;

import com.replecant.retrocosmos.launch.LaunchSite;
import com.replecant.retrocosmos.registry.ModItems;
import java.util.function.Consumer;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.ItemUtils;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.TooltipDisplay;
import net.minecraft.world.level.Level;

/** Liquid oxygen canister: loads the rocket's LOX tank, or (right click in the air) recharges the worn pressure suit. */
public class OxygenCanisterItem extends Item {
    public OxygenCanisterItem(Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResult use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        ItemStack chest = player.getItemBySlot(EquipmentSlot.CHEST);
        if (!chest.is(ModItems.SPACE_SUIT.get())) {
            if (!level.isClientSide()) {
                player.displayClientMessage(Component.translatable("message.retrocosmos.oxygen.need_suit").withStyle(ChatFormatting.YELLOW), true);
            }
            return InteractionResult.FAIL;
        }
        if (OxygenSystem.oxygen(chest) >= OxygenSystem.MAX_OXYGEN) {
            if (!level.isClientSide()) {
                player.displayClientMessage(Component.translatable("message.retrocosmos.oxygen.already_full").withStyle(ChatFormatting.YELLOW), true);
            }
            return InteractionResult.FAIL;
        }
        if (!level.isClientSide()) {
            OxygenSystem.setOxygen(chest, OxygenSystem.MAX_OXYGEN);
            player.setItemInHand(hand, ItemUtils.createFilledResult(stack, player, new ItemStack(ModItems.EMPTY_FUEL_CANISTER.get())));
            level.playSound(null, player.blockPosition(), SoundEvents.BOTTLE_FILL, SoundSource.PLAYERS, 1.0F, 0.7F);
            player.displayClientMessage(Component.translatable("message.retrocosmos.oxygen.refilled").withStyle(ChatFormatting.AQUA), true);
            if (player instanceof ServerPlayer serverPlayer) {
                LaunchSite.award(serverPlayer, "stage1/canned_air", "refilled");
            }
        }
        return InteractionResult.SUCCESS;
    }

    @Override
    public void appendHoverText(ItemStack stack, TooltipContext context, TooltipDisplay display, Consumer<Component> tooltip, TooltipFlag flag) {
        tooltip.accept(Component.translatable("tooltip.retrocosmos.liquid_oxygen_canister").withStyle(ChatFormatting.GRAY));
    }
}
