package com.replecant.retrocosmos.tribe;

import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.tribe.client.TribeGeometry;
import com.replecant.retrocosmos.tribe.client.TribesmanRenderer;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.renderer.entity.ThrownItemRenderer;
import net.minecraft.resources.Identifier;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.client.event.EntityRenderersEvent;

/** Client side of the tribes: model layers and renderers. */
public final class TribeClient {
    public static final ModelLayerLocation TRIBESMAN = new ModelLayerLocation(
            Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "tribesman"), "main");

    private TribeClient() {}

    public static void init(IEventBus modEventBus) {
        modEventBus.addListener(TribeClient::registerLayers);
        modEventBus.addListener(TribeClient::registerRenderers);
    }

    private static void registerLayers(EntityRenderersEvent.RegisterLayerDefinitions event) {
        event.registerLayerDefinition(TRIBESMAN, TribeGeometry::tribesman);
    }

    private static void registerRenderers(EntityRenderersEvent.RegisterRenderers event) {
        event.registerEntityRenderer(ModTribes.TRIBESMAN.get(), TribesmanRenderer::new);
        event.registerEntityRenderer(ModTribes.THROWN_SPEAR.get(), ThrownItemRenderer::new);
    }
}
