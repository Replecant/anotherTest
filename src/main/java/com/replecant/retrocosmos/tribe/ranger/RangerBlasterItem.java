package com.replecant.retrocosmos.tribe.ranger;

import com.replecant.retrocosmos.tribe.ModTribes;
import com.replecant.retrocosmos.tribe.mutant.BlasterBolt;
import java.util.function.Consumer;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.stats.Stats;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.TooltipDisplay;
import net.minecraft.world.level.Level;

/**
 * The Space Rangers' sidearm: chrome, blue fins, a star on the grip. Right-click fires a blue bolt (7 damage) and
 * uses up one energy cartridge from anywhere in the inventory (free in creative). Empty: a dry click and a note on
 * the action bar. Never wears out.
 */
public class RangerBlasterItem extends Item {
    public static final int COOLDOWN = 8;

    public RangerBlasterItem(Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResult use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (!player.hasInfiniteMaterials() && !takeCartridge(player, true)) {
            if (!level.isClientSide()) {
                level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.DISPENSER_FAIL, SoundSource.PLAYERS, 0.8F, 1.7F);
                player.displayClientMessage(Component.translatable("item.retrocosmos.ranger_blaster.empty").withStyle(ChatFormatting.RED), true);
            }
            player.getCooldowns().addCooldown(stack, COOLDOWN);
            return InteractionResult.FAIL;
        }
        if (level instanceof ServerLevel) {
            if (!player.hasInfiniteMaterials()) {
                takeCartridge(player, false);
            }
            BlasterBolt.launch(new RangerBolt(ModTribes.RANGER_BOLT.get(), level), player, player.getLookAngle(), 0.2F, 1.25F);
            player.awardStat(Stats.ITEM_USED.get(this));
        }
        player.getCooldowns().addCooldown(stack, COOLDOWN);
        return InteractionResult.SUCCESS;
    }

    /** Finds (simulate) or uses up one energy cartridge anywhere in the player's inventory. */
    public static boolean takeCartridge(Player player, boolean simulate) {
        Inventory inv = player.getInventory();
        for (int i = 0; i < inv.getContainerSize(); i++) {
            ItemStack s = inv.getItem(i);
            if (s.is(ModTribes.ENERGY_CARTRIDGE.get())) {
                if (!simulate) {
                    s.shrink(1);
                }
                return true;
            }
        }
        return false;
    }

    /** How many cartridges the player carries. */
    public static int cartridges(Player player) {
        Inventory inv = player.getInventory();
        int n = 0;
        for (int i = 0; i < inv.getContainerSize(); i++) {
            ItemStack s = inv.getItem(i);
            if (s.is(ModTribes.ENERGY_CARTRIDGE.get())) {
                n += s.getCount();
            }
        }
        return n;
    }

    @Override
    public void appendHoverText(ItemStack stack, TooltipContext context, TooltipDisplay display, Consumer<Component> tooltip, TooltipFlag flag) {
        tooltip.accept(Component.translatable("item.retrocosmos.ranger_blaster.desc").withStyle(ChatFormatting.GRAY));
    }
}
