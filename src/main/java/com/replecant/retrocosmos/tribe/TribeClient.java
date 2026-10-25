package com.replecant.retrocosmos.tribe;

import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.tribe.client.BlasterBoltRenderer;
import com.replecant.retrocosmos.tribe.client.MutantRenderer;
import com.replecant.retrocosmos.tribe.client.NovusModel;
import com.replecant.retrocosmos.tribe.client.SapiensModel;
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

    public static final ModelLayerLocation HOMINID_NOVUS = new ModelLayerLocation(
            Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "hominid_novus"), "main");
    public static final ModelLayerLocation HOMINUS_SAPIENS = new ModelLayerLocation(
            Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "hominus_sapiens"), "main");

    private TribeClient() {}

    public static void init(IEventBus modEventBus) {
        modEventBus.addListener(TribeClient::registerLayers);
        modEventBus.addListener(TribeClient::registerRenderers);
    }

    private static void registerLayers(EntityRenderersEvent.RegisterLayerDefinitions event) {
        event.registerLayerDefinition(TRIBESMAN, TribeGeometry::tribesman);
        event.registerLayerDefinition(HOMINID_NOVUS, TribeGeometry::hominid_novus);
        event.registerLayerDefinition(HOMINUS_SAPIENS, TribeGeometry::hominus_sapiens);
    }

    private static void registerRenderers(EntityRenderersEvent.RegisterRenderers event) {
        event.registerEntityRenderer(ModTribes.TRIBESMAN.get(), TribesmanRenderer::new);
        event.registerEntityRenderer(ModTribes.THROWN_SPEAR.get(), ThrownItemRenderer::new);
        event.registerEntityRenderer(ModTribes.HOMINID_NOVUS.get(), context -> new MutantRenderer<>(context,
                new NovusModel(context.bakeLayer(HOMINID_NOVUS)), 1.1F, "hominid_novus", true, false));
        event.registerEntityRenderer(ModTribes.HOMINUS_SAPIENS.get(), context -> new MutantRenderer<>(context,
                new SapiensModel(context.bakeLayer(HOMINUS_SAPIENS)), 0.5F, "hominus_sapiens", false, true));
        event.registerEntityRenderer(ModTribes.BLASTER_BOLT.get(), BlasterBoltRenderer::new);
    }
}
