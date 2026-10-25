package com.replecant.retrocosmos.dinosaur.robot.client;

import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.dinosaur.DinosaurClient;
import com.replecant.retrocosmos.dinosaur.client.DinoGeometry;
import com.replecant.retrocosmos.dinosaur.client.DinosaurRenderer;
import com.replecant.retrocosmos.dinosaur.robot.ModRobots;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.resources.Identifier;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.client.event.EntityRenderersEvent;

/** Client side of Dr. Oinstein's robots: model layers, renderers with their glowing eyes and cores, the bolt. */
public final class RobotClient {
    public static final ModelLayerLocation ATOMIC_SENTRY = layer("atomic_sentry");
    public static final ModelLayerLocation ATOMIC_AUTOMATON = layer("atomic_automaton");
    private static final RenderType SENTRY_GLOW = DinosaurClient.glow("atomic_sentry");
    private static final RenderType AUTOMATON_GLOW = DinosaurClient.glow("atomic_automaton");

    private RobotClient() {}

    public static void init(IEventBus modEventBus) {
        modEventBus.addListener(RobotClient::registerLayers);
        modEventBus.addListener(RobotClient::registerRenderers);
    }

    private static ModelLayerLocation layer(String name) {
        return new ModelLayerLocation(Identifier.fromNamespaceAndPath(RetroCosmos.MODID, name), "main");
    }

    private static void registerLayers(EntityRenderersEvent.RegisterLayerDefinitions event) {
        event.registerLayerDefinition(ATOMIC_SENTRY, DinoGeometry::atomic_sentry);
        event.registerLayerDefinition(ATOMIC_AUTOMATON, DinoGeometry::atomic_automaton);
    }

    private static void registerRenderers(EntityRenderersEvent.RegisterRenderers event) {
        event.registerEntityRenderer(ModRobots.ATOMIC_SENTRY.get(), context -> DinosaurClient.glowing(new DinosaurRenderer<>(context,
                new AtomicSentryModel(context.bakeLayer(ATOMIC_SENTRY)), 0.5F, "atomic_sentry", 0.4), SENTRY_GLOW));
        event.registerEntityRenderer(ModRobots.ATOMIC_AUTOMATON.get(), context -> DinosaurClient.glowing(new DinosaurRenderer<>(context,
                new AtomicAutomatonModel(context.bakeLayer(ATOMIC_AUTOMATON)), 0.8F, "atomic_automaton", 0.3), AUTOMATON_GLOW));
        event.registerEntityRenderer(ModRobots.SENTRY_BOLT.get(), SentryBoltRenderer::new);
    }
}
