package com.replecant.retrocosmos.tribe;

import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.tribe.boss.client.BossRenderer;
import com.replecant.retrocosmos.tribe.boss.client.DoctorModel;
import com.replecant.retrocosmos.tribe.boss.client.HomoNovusModel;
import com.replecant.retrocosmos.tribe.boss.client.StriderModel;
import com.replecant.retrocosmos.tribe.client.BlasterBoltRenderer;
import com.replecant.retrocosmos.tribe.client.MutantRenderer;
import com.replecant.retrocosmos.tribe.client.NovusModel;
import com.replecant.retrocosmos.tribe.client.SapiensModel;
import com.replecant.retrocosmos.tribe.client.TribeGeometry;
import com.replecant.retrocosmos.tribe.client.TribesmanRenderer;
import com.replecant.retrocosmos.tribe.ranger.RangerBlasterItem;
import net.minecraft.client.Minecraft;
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

    public static final ModelLayerLocation OINSTEIN_STRIDER = new ModelLayerLocation(
            Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "oinstein_strider"), "main");
    public static final ModelLayerLocation DR_OINSTEIN = new ModelLayerLocation(
            Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "dr_oinstein"), "main");
    public static final ModelLayerLocation HOMO_NOVUS = new ModelLayerLocation(
            Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "homo_novus"), "main");

    private TribeClient() {}

    public static void init(IEventBus modEventBus) {
        RangerBlasterItem.clientClock = () -> {
            var level = Minecraft.getInstance().level;
            return level == null ? 0L : level.getGameTime();
        };
        modEventBus.addListener(TribeClient::registerLayers);
        modEventBus.addListener(TribeClient::registerRenderers);
    }

    private static void registerLayers(EntityRenderersEvent.RegisterLayerDefinitions event) {
        event.registerLayerDefinition(TRIBESMAN, TribeGeometry::tribesman);
        event.registerLayerDefinition(HOMINID_NOVUS, TribeGeometry::hominid_novus);
        event.registerLayerDefinition(HOMINUS_SAPIENS, TribeGeometry::hominus_sapiens);
        event.registerLayerDefinition(OINSTEIN_STRIDER, TribeGeometry::oinstein_strider);
        event.registerLayerDefinition(DR_OINSTEIN, TribeGeometry::dr_oinstein);
        event.registerLayerDefinition(HOMO_NOVUS, TribeGeometry::homo_novus);
    }

    private static void registerRenderers(EntityRenderersEvent.RegisterRenderers event) {
        event.registerEntityRenderer(ModTribes.TRIBESMAN.get(), TribesmanRenderer::new);
        event.registerEntityRenderer(ModTribes.THROWN_SPEAR.get(), ThrownItemRenderer::new);
        event.registerEntityRenderer(ModTribes.HOMINID_NOVUS.get(), context -> new MutantRenderer<>(context,
                new NovusModel(context.bakeLayer(HOMINID_NOVUS)), 1.1F, "hominid_novus", true, false));
        event.registerEntityRenderer(ModTribes.HOMINUS_SAPIENS.get(), context -> new MutantRenderer<>(context,
                new SapiensModel(context.bakeLayer(HOMINUS_SAPIENS)), 0.5F, "hominus_sapiens", false, true));
        event.registerEntityRenderer(ModTribes.BLASTER_BOLT.get(), BlasterBoltRenderer::new);
        event.registerEntityRenderer(ModTribes.RANGER_BOLT.get(), context -> new BlasterBoltRenderer(context, BlasterBoltRenderer.RANGER_TEXTURE));
        event.registerEntityRenderer(ModTribes.OINSTEIN_STRIDER.get(), context -> new BossRenderer<>(context,
                new StriderModel(context.bakeLayer(OINSTEIN_STRIDER)), 1.6F, "oinstein_strider", true));
        event.registerEntityRenderer(ModTribes.DR_OINSTEIN.get(), context -> new BossRenderer<>(context,
                new DoctorModel(context.bakeLayer(DR_OINSTEIN)), 0.5F, "dr_oinstein", false));
        event.registerEntityRenderer(ModTribes.HOMO_NOVUS.get(), context -> new BossRenderer<>(context,
                new HomoNovusModel(context.bakeLayer(HOMO_NOVUS)), 1.1F, "homo_novus", true));
    }
}
