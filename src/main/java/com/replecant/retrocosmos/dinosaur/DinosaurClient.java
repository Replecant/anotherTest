package com.replecant.retrocosmos.dinosaur;

import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.dinosaur.client.BrontosaurusModel;
import com.replecant.retrocosmos.dinosaur.client.DinoGeometry;
import com.replecant.retrocosmos.dinosaur.client.DinosaurRenderer;
import com.replecant.retrocosmos.dinosaur.client.RaptorModel;
import com.replecant.retrocosmos.dinosaur.client.TriceratopsModel;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.resources.Identifier;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.client.event.EntityRenderersEvent;

/** Client side of the dinosaurs: model layers and renderers. */
public final class DinosaurClient {
    public static final ModelLayerLocation RAPTOR = layer("raptor");
    public static final ModelLayerLocation BRONTOSAURUS = layer("brontosaurus");
    public static final ModelLayerLocation TRICERATOPS = layer("triceratops");

    private DinosaurClient() {}

    public static void init(IEventBus modEventBus) {
        modEventBus.addListener(DinosaurClient::registerLayers);
        modEventBus.addListener(DinosaurClient::registerRenderers);
    }

    private static ModelLayerLocation layer(String name) {
        return new ModelLayerLocation(Identifier.fromNamespaceAndPath(RetroCosmos.MODID, name), "main");
    }

    private static void registerLayers(EntityRenderersEvent.RegisterLayerDefinitions event) {
        event.registerLayerDefinition(RAPTOR, DinoGeometry::raptor);
        event.registerLayerDefinition(BRONTOSAURUS, DinoGeometry::brontosaurus);
        event.registerLayerDefinition(TRICERATOPS, DinoGeometry::triceratops);
    }

    private static void registerRenderers(EntityRenderersEvent.RegisterRenderers event) {
        event.registerEntityRenderer(ModDinosaurs.RAPTOR.get(),
                context -> new DinosaurRenderer<>(context, new RaptorModel(context.bakeLayer(RAPTOR)), 0.6F, "raptor", 0.6));
        event.registerEntityRenderer(ModDinosaurs.BRONTOSAURUS.get(),
                context -> new DinosaurRenderer<>(context, new BrontosaurusModel(context.bakeLayer(BRONTOSAURUS)), 2.0F, "brontosaurus", 3.5));
        event.registerEntityRenderer(ModDinosaurs.TRICERATOPS.get(),
                context -> new DinosaurRenderer<>(context, new TriceratopsModel(context.bakeLayer(TRICERATOPS)), 1.1F, "triceratops", 1.2));
    }
}
