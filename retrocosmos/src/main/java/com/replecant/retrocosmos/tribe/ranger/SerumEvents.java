package com.replecant.retrocosmos.tribe.ranger;

import com.replecant.retrocosmos.RetroCosmos;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.tick.PlayerTickEvent;

/** The serums' side effects: once a second, a player whose serum has worn off gets the bill. */
@EventBusSubscriber(modid = RetroCosmos.MODID)
public final class SerumEvents {
    private SerumEvents() {}

    @SubscribeEvent
    public static void onPlayerTick(PlayerTickEvent.Post event) {
        if (event.getEntity() instanceof ServerPlayer player && player.tickCount % 20 == 0) {
            applyDue(player, player.level().getGameTime());
        }
    }

    /** Applies a pending side effect if its time has come; true if one was applied. */
    public static boolean applyDue(ServerPlayer player, long now) {
        var data = player.getPersistentData();
        String id = data.getStringOr(SerumItem.AFTER_KEY, "");
        if (id.isEmpty() || now < data.getLongOr(SerumItem.AFTER_AT_KEY, 0L)) {
            return false;
        }
        data.remove(SerumItem.AFTER_KEY);
        data.remove(SerumItem.AFTER_AT_KEY);
        Serum serum = Serum.byId(id);
        if (serum == null || !player.isAlive()) {
            return false;
        }
        player.addEffect(SerumItem.afterEffect(serum));
        player.displayClientMessage(Component.translatable("item.retrocosmos.serum.wears_off").withStyle(ChatFormatting.DARK_GREEN), true);
        return true;
    }
}
