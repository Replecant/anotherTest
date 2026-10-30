package com.replecant.retrocosmos.tribe.ranger;

import java.util.function.Consumer;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.TooltipDisplay;

/**
 * Dr. Oinstein's battered research notebook: the catalyst of every serum recipe. It goes into the crafting grid
 * and comes back out (its own crafting remainder) - the knowledge is not used up.
 */
public class OinsteinNotesItem extends Item {
    public OinsteinNotesItem(Properties properties) {
        super(properties);
    }

    @Override
    public ItemStack getCraftingRemainder(ItemStack stack) {
        return stack.copyWithCount(1);
    }

    @Override
    public void appendHoverText(ItemStack stack, TooltipContext context, TooltipDisplay display, Consumer<Component> tooltip, TooltipFlag flag) {
        tooltip.accept(Component.translatable("item.retrocosmos.oinstein_notes.desc").withStyle(ChatFormatting.GREEN));
        tooltip.accept(Component.translatable("item.retrocosmos.oinstein_notes.lore").withStyle(ChatFormatting.DARK_GRAY, ChatFormatting.ITALIC));
    }
}
