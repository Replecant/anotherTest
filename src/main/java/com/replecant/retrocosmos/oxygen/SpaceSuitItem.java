package com.replecant.retrocosmos.oxygen;

import java.util.function.Consumer;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.TooltipDisplay;

/** The pressure suit chest piece: carries the oxygen tank and shows its charge in the tooltip. */
public class SpaceSuitItem extends Item {
    public SpaceSuitItem(Properties properties) {
        super(properties);
    }

    @Override
    public void appendHoverText(ItemStack stack, TooltipContext context, TooltipDisplay display, Consumer<Component> tooltip, TooltipFlag flag) {
        int seconds = OxygenSystem.oxygen(stack) / 20;
        int percent = OxygenSystem.oxygen(stack) * 100 / OxygenSystem.MAX_OXYGEN;
        ChatFormatting color = percent > 20 ? ChatFormatting.AQUA : percent > 10 ? ChatFormatting.GOLD : ChatFormatting.RED;
        tooltip.accept(Component.translatable("tooltip.retrocosmos.space_suit.oxygen", percent,
                String.format("%d:%02d", seconds / 60, seconds % 60)).withStyle(color));
    }
}
