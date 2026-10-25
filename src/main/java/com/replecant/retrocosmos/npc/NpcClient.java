package com.replecant.retrocosmos.npc;

import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.npc.client.CrewGeometry;
import com.replecant.retrocosmos.npc.client.CrewRenderer;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.resources.Identifier;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.client.event.EntityRenderersEvent;

/** Client side of the expedition crew: renderers and model layers. */
public final class NpcClient {
    public static final ModelLayerLocation CREW = new ModelLayerLocation(
            Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "expedition_member"), "main");
    public static final ModelLayerLocation CREW_GEAR = new ModelLayerLocation(
            Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "expedition_member"), "gear");

    private NpcClient() {}

    public static void init(IEventBus modEventBus) {
        modEventBus.addListener(NpcClient::registerLayers);
        modEventBus.addListener(NpcClient::registerRenderers);
    }

    private static void registerLayers(EntityRenderersEvent.RegisterLayerDefinitions event) {
        event.registerLayerDefinition(CREW, CrewGeometry::skin);
        event.registerLayerDefinition(CREW_GEAR, CrewGeometry::gear);
    }

    private static void registerRenderers(EntityRenderersEvent.RegisterRenderers event) {
        event.registerEntityRenderer(ExpeditionNpcs.EXPEDITION_MEMBER.get(), CrewRenderer::new);
    }
}
