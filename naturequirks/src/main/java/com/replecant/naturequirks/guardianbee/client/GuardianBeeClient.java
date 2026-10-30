package com.replecant.naturequirks.guardianbee.client;

import com.replecant.naturequirks.guardianbee.GuardianBees;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.client.event.EntityRenderersEvent;

public final class GuardianBeeClient {
    private GuardianBeeClient() {}

    public static void init(IEventBus modEventBus) {
        modEventBus.addListener((EntityRenderersEvent.RegisterLayerDefinitions event) ->
                event.registerLayerDefinition(GuardianBeeRenderer.LAYER, GuardianBeeGeometry::create));
        modEventBus.addListener((EntityRenderersEvent.RegisterRenderers event) ->
                event.registerEntityRenderer(GuardianBees.GUARDIAN_BEE.get(), GuardianBeeRenderer::new));
    }
}
