package com.replecant.retrocosmos.tribe.ranger;

import com.replecant.retrocosmos.registry.ModDataComponents;
import com.replecant.retrocosmos.tribe.ModTribes;
import com.replecant.retrocosmos.tribe.mutant.BlasterBolt;
import java.util.function.Consumer;
import java.util.function.LongSupplier;
import net.minecraft.ChatFormatting;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.stats.Stats;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.TooltipDisplay;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

/**
 * The Space Rangers' sidearm: chrome, blue fins, a star on the grip. Right-click fires a blue bolt (7 damage) and
 * uses up one energy cartridge from anywhere in the inventory (free in creative). Empty: a dry click and a note on
 * the action bar. Never wears out, but it heats up: {@link BlasterHeat#MAX} rapid shots overheat it and it locks up for
 * a few seconds in a puff of steam. The item bar shows the heat, green to red.
 */
public class RangerBlasterItem extends Item {
    public static final int COOLDOWN = 8;
    /** Game time for the heat gauge on the client (set by the client setup; the server never draws item bars). */
    public static LongSupplier clientClock = () -> 0L;

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
            long now = level.getGameTime();
            BlasterHeat heat = heat(stack).fire(now);
            if (heat.heat() >= BlasterHeat.MAX) {
                overheat(level, player, stack, now);
                return InteractionResult.SUCCESS;
            }
            stack.set(ModDataComponents.BLASTER_HEAT.get(), heat);
        }
        player.getCooldowns().addCooldown(stack, COOLDOWN);
        return InteractionResult.SUCCESS;
    }

    public static BlasterHeat heat(ItemStack stack) {
        return stack.getOrDefault(ModDataComponents.BLASTER_HEAT.get(), BlasterHeat.COLD);
    }

    /** Locks the blaster up until it has cooled from full: steam, a hiss and a warning on the action bar. */
    private static void overheat(Level level, Player player, ItemStack stack, long now) {
        // full heat that starts cooling at once, so the gauge drains over the lock-up
        stack.set(ModDataComponents.BLASTER_HEAT.get(), new BlasterHeat(BlasterHeat.MAX, now - BlasterHeat.GRACE));
        player.getCooldowns().addCooldown(stack, BlasterHeat.OVERHEAT_TICKS - BlasterHeat.GRACE);
        level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.FIRE_EXTINGUISH, SoundSource.PLAYERS, 0.7F, 1.3F);
        if (level instanceof ServerLevel server) {
            Vec3 muzzle = player.getEyePosition().add(player.getLookAngle().scale(0.8)).subtract(0, 0.3, 0);
            server.sendParticles(ParticleTypes.CLOUD, muzzle.x, muzzle.y, muzzle.z, 8, 0.1, 0.1, 0.1, 0.02);
        }
        player.displayClientMessage(Component.translatable("item.retrocosmos.ranger_blaster.overheat").withStyle(ChatFormatting.GOLD), true);
    }

    /** The heat changes with every shot; that must not make the pistol bob as if it had just been drawn. */
    @Override
    public boolean shouldCauseReequipAnimation(ItemStack oldStack, ItemStack newStack, boolean slotChanged) {
        return slotChanged || !oldStack.is(newStack.getItem());
    }

    @Override
    public boolean isBarVisible(ItemStack stack) {
        return heat(stack).at(clientClock.getAsLong()) > 0;
    }

    @Override
    public int getBarWidth(ItemStack stack) {
        return Math.round(13.0F * heat(stack).at(clientClock.getAsLong()) / BlasterHeat.MAX);
    }

    @Override
    public int getBarColor(ItemStack stack) {
        float hot = (float) heat(stack).at(clientClock.getAsLong()) / BlasterHeat.MAX;
        return Mth.hsvToRgb((1.0F - hot) / 3.0F, 1.0F, 1.0F);
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
        tooltip.accept(Component.translatable("item.retrocosmos.ranger_blaster.heat_desc", BlasterHeat.MAX).withStyle(ChatFormatting.GRAY));
    }
}
