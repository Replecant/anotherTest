package com.replecant.naturequirks.flowercreeper.client;

import com.replecant.naturequirks.flowercreeper.FlowerCreepers;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.client.event.EntityRenderersEvent;

public final class FlowerCreeperClient {
    private FlowerCreeperClient() {}

    public static void init(IEventBus modEventBus) {
        modEventBus.addListener((EntityRenderersEvent.RegisterLayerDefinitions event) ->
                event.registerLayerDefinition(FlowerCreeperRenderer.LAYER, FlowerCreeperGeometry::create));
        modEventBus.addListener((EntityRenderersEvent.RegisterRenderers event) ->
                event.registerEntityRenderer(FlowerCreepers.FLOWER_CREEPER.get(), FlowerCreeperRenderer::new));
    }
}
