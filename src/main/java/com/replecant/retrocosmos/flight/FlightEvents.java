package com.replecant.retrocosmos.flight;

import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Player;
import net.neoforged.neoforge.event.entity.EntityMountEvent;

/** Keeps the crew strapped in once the engines are lit. */
public final class FlightEvents {
    private FlightEvents() {}

    public static void onMount(EntityMountEvent event) {
        if (event.isDismounting() && event.getEntityBeingMounted() instanceof RocketEntity rocket && !rocket.isRemoved()
                && !rocket.canDisembark()) {
            event.setCanceled(true);
            if (event.getEntityMounting() instanceof Player player && !player.level().isClientSide()) {
                player.displayClientMessage(Component.translatable("message.retrocosmos.flight.strapped_in"), true);
            }
        }
    }
}
