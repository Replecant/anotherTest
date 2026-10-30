package com.replecant.retrocosmos.station;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.neoforged.neoforge.event.entity.player.PlayerEvent;
import net.neoforged.neoforge.event.level.BlockEvent;

/** Freedom Station is protected: players who aren't in creative mode can't take it apart. */
public final class StationProtection {
    private StationProtection() {}

    private static boolean protectedFor(Player player, Level level) {
        return FreedomStation.isStation(level) && !player.isCreative() && !player.isSpectator();
    }

    public static void onBreak(BlockEvent.BreakEvent event) {
        Player player = event.getPlayer();
        if (player != null && protectedFor(player, player.level())) {
            event.setCanceled(true);
            player.displayClientMessage(Component.translatable("message.retrocosmos.station.protected").withStyle(ChatFormatting.RED), true);
        }
    }

    /** No mining progress either, so blocks don't even start to crack. */
    public static void onBreakSpeed(PlayerEvent.BreakSpeed event) {
        if (protectedFor(event.getEntity(), event.getEntity().level())) {
            event.setNewSpeed(0.0F);
        }
    }
}
