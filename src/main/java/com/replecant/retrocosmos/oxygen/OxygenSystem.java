package com.replecant.retrocosmos.oxygen;

import com.replecant.retrocosmos.launch.LaunchSite;
import com.replecant.retrocosmos.registry.ModAttachments;
import com.replecant.retrocosmos.registry.ModBlocks;
import com.replecant.retrocosmos.registry.ModDataComponents;
import com.replecant.retrocosmos.registry.ModItems;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.neoforge.event.tick.PlayerTickEvent;

/**
 * Life support. The pressure suit's chest piece carries an oxygen tank ({@link ModDataComponents#OXYGEN}, ticks).
 * While a player's "airless" simulation is on (see the /retrocosmos oxygen command; planets arrive in stage 2)
 * the tank drains one second per second, refills near life-support equipment (Mission Control console,
 * air liquefier) and, when empty or when the suit is incomplete, the astronaut suffocates.
 */
public final class OxygenSystem {
    /** 300 seconds of air. */
    public static final int MAX_OXYGEN = 300 * 20;
    private static final int LIFE_SUPPORT_RANGE = 2;
    private static final int[] WARNINGS_SECONDS = {60, 30, 10};

    private OxygenSystem() {}

    public static SuitSettings settings(Player player) {
        return player.getData(ModAttachments.SUIT_SETTINGS);
    }

    public static void setSettings(Player player, SuitSettings settings) {
        player.setData(ModAttachments.SUIT_SETTINGS, settings);
    }

    /** Oxygen in the given chest piece, in ticks (a fresh suit is full). */
    public static int oxygen(ItemStack chest) {
        if (!chest.is(ModItems.SPACE_SUIT.get())) {
            return 0;
        }
        Integer stored = chest.get(ModDataComponents.OXYGEN.get());
        return stored == null ? MAX_OXYGEN : Math.max(0, Math.min(MAX_OXYGEN, stored));
    }

    public static void setOxygen(ItemStack chest, int ticks) {
        chest.set(ModDataComponents.OXYGEN.get(), Math.max(0, Math.min(MAX_OXYGEN, ticks)));
    }

    public static boolean wearingSuit(Player player) {
        return LaunchSite.suitBits(player) == LaunchSite.SUIT_FULL;
    }

    public static void onPlayerTick(PlayerTickEvent.Post event) {
        if (!(event.getEntity() instanceof ServerPlayer player) || !(player.level() instanceof ServerLevel level)) {
            return;
        }
        if (player.isCreative() || player.isSpectator() || player.isDeadOrDying()) {
            return;
        }
        if (!settings(player).airless()) {
            return;
        }
        if (player.tickCount % 20 != 0) {
            return;
        }
        ItemStack chest = player.getItemBySlot(EquipmentSlot.CHEST);
        boolean suited = wearingSuit(player);
        int o2 = suited ? oxygen(chest) : 0;

        if (suited && nearLifeSupport(level, player.blockPosition())) {
            if (o2 < MAX_OXYGEN) {
                setOxygen(chest, o2 + 20 * 5);
                if (o2 + 100 >= MAX_OXYGEN) {
                    player.displayClientMessage(Component.translatable("message.retrocosmos.oxygen.recharged").withStyle(ChatFormatting.AQUA), true);
                }
            }
            return;
        }
        if (suited && o2 > 0) {
            int left = o2 - 20;
            setOxygen(chest, left);
            for (int warn : WARNINGS_SECONDS) {
                if (left == warn * 20) {
                    player.displayClientMessage(Component.translatable("message.retrocosmos.oxygen.low", warn)
                            .withStyle(warn <= 10 ? ChatFormatting.RED : ChatFormatting.GOLD), true);
                    level.playSound(null, player.blockPosition(), SoundEvents.NOTE_BLOCK_BELL.value(), SoundSource.PLAYERS, 1.0F, warn <= 10 ? 0.6F : 1.0F);
                }
            }
            if (left <= 10 * 20 && left % 40 == 0) {
                level.playSound(null, player.blockPosition(), SoundEvents.NOTE_BLOCK_BIT.value(), SoundSource.PLAYERS, 0.6F, 1.8F);
            }
            return;
        }
        // no air: suffocate like drowning
        player.hurtServer(level, player.damageSources().drown(), 2.0F);
        level.playSound(null, player.blockPosition(), SoundEvents.PLAYER_HURT_DROWN, SoundSource.PLAYERS, 1.0F, 0.8F);
        player.displayClientMessage(Component.translatable(suited ? "message.retrocosmos.oxygen.empty" : "message.retrocosmos.oxygen.no_suit")
                .withStyle(ChatFormatting.RED, ChatFormatting.BOLD), true);
    }

    /** True next to a Mission Control console or an air liquefier (umbilical hook-up). */
    public static boolean nearLifeSupport(ServerLevel level, BlockPos center) {
        BlockPos.MutableBlockPos cursor = new BlockPos.MutableBlockPos();
        for (int dx = -LIFE_SUPPORT_RANGE; dx <= LIFE_SUPPORT_RANGE; dx++) {
            for (int dy = -1; dy <= LIFE_SUPPORT_RANGE; dy++) {
                for (int dz = -LIFE_SUPPORT_RANGE; dz <= LIFE_SUPPORT_RANGE; dz++) {
                    cursor.set(center.getX() + dx, center.getY() + dy, center.getZ() + dz);
                    BlockState state = level.getBlockState(cursor);
                    if (state.is(ModBlocks.MISSION_CONTROL_CONSOLE.get()) || state.is(ModBlocks.AIR_LIQUEFIER.get())) {
                        return true;
                    }
                }
            }
        }
        return false;
    }
}
