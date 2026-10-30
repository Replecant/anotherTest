package com.replecant.naturequirks.stonehead.client;

import com.replecant.naturequirks.stonehead.StoneHeads;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.client.event.EntityRenderersEvent;

public final class StoneHeadClient {
    private StoneHeadClient() {}

    public static void init(IEventBus modEventBus) {
        modEventBus.addListener((EntityRenderersEvent.RegisterLayerDefinitions event) ->
                event.registerLayerDefinition(StoneHeadRenderer.LAYER, StoneHeadGeometry::create));
        modEventBus.addListener((EntityRenderersEvent.RegisterRenderers event) ->
                event.registerEntityRenderer(StoneHeads.STONE_HEAD.get(), StoneHeadRenderer::new));
    }
}
