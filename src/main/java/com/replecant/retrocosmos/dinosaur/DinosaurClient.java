package com.replecant.retrocosmos.dinosaur;

import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.dinosaur.client.AnkylosaurusModel;
import com.replecant.retrocosmos.dinosaur.client.BrontosaurusModel;
import com.replecant.retrocosmos.dinosaur.client.CompsognathusModel;
import com.replecant.retrocosmos.dinosaur.client.DeinosuchusModel;
import com.replecant.retrocosmos.dinosaur.client.DinoGeometry;
import com.replecant.retrocosmos.dinosaur.client.DinosaurRenderState;
import com.replecant.retrocosmos.dinosaur.client.DinosaurRenderer;
import com.replecant.retrocosmos.dinosaur.client.MeganeuraModel;
import com.replecant.retrocosmos.dinosaur.client.PlesiosaurModel;
import com.replecant.retrocosmos.dinosaur.client.PteranodonModel;
import com.replecant.retrocosmos.dinosaur.client.RaptorModel;
import com.replecant.retrocosmos.dinosaur.client.SporeMothModel;
import com.replecant.retrocosmos.dinosaur.client.TriceratopsModel;
import com.replecant.retrocosmos.dinosaur.client.TyrannosaurusModel;
import com.replecant.retrocosmos.dinosaur.client.VenusCreeperModel;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.renderer.entity.layers.EyesLayer;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.client.event.EntityRenderersEvent;
import net.neoforged.neoforge.client.event.ViewportEvent;
import net.neoforged.neoforge.common.NeoForge;

/** Client side of the dinosaurs: model layers, renderers, and the ground shaking under a tyrannosaurus. */
public final class DinosaurClient {
    public static final ModelLayerLocation RAPTOR = layer("raptor");
    public static final ModelLayerLocation BRONTOSAURUS = layer("brontosaurus");
    public static final ModelLayerLocation TRICERATOPS = layer("triceratops");
    public static final ModelLayerLocation VENUS_CREEPER = layer("venus_creeper");
    public static final ModelLayerLocation PTERANODON = layer("pteranodon");
    public static final ModelLayerLocation TYRANNOSAURUS = layer("tyrannosaurus");
    public static final ModelLayerLocation PLESIOSAUR = layer("plesiosaur");
    public static final ModelLayerLocation MEGANEURA = layer("meganeura");
    public static final ModelLayerLocation COMPSOGNATHUS = layer("compsognathus");
    public static final ModelLayerLocation SPORE_MOTH = layer("spore_moth");
    public static final ModelLayerLocation ANKYLOSAURUS = layer("ankylosaurus");
    public static final ModelLayerLocation DEINOSUCHUS = layer("deinosuchus");

    private static final RenderType CREEPER_GLOW = glow("venus_creeper");
    private static final RenderType MOTH_GLOW = glow("spore_moth");
    /** How far away a tyrannosaurus' footfalls can still be felt. */
    private static final double SHAKE_RANGE = 28.0;

    private DinosaurClient() {}

    public static void init(IEventBus modEventBus) {
        modEventBus.addListener(DinosaurClient::registerLayers);
        modEventBus.addListener(DinosaurClient::registerRenderers);
        NeoForge.EVENT_BUS.addListener(DinosaurClient::shakeCamera);
        com.replecant.retrocosmos.dinosaur.robot.client.RobotClient.init(modEventBus);
    }

    public static RenderType glow(String name) {
        return RenderTypes.eyes(Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "textures/entity/dinosaur/" + name + "_glow.png"));
    }

    /** Adds a full-bright overlay (eyes, spore bulb, wing spots) that glows in the dark. */
    public static <T extends net.minecraft.world.entity.Mob & DinosaurAnimated> DinosaurRenderer<T> glowing(DinosaurRenderer<T> renderer,
                                                                                                            RenderType glow) {
        renderer.addLayer(new EyesLayer<DinosaurRenderState, EntityModel<DinosaurRenderState>>(renderer) {
            @Override
            public RenderType renderType() {
                return glow;
            }
        });
        return renderer;
    }

    private static ModelLayerLocation layer(String name) {
        return new ModelLayerLocation(Identifier.fromNamespaceAndPath(RetroCosmos.MODID, name), "main");
    }

    private static void registerLayers(EntityRenderersEvent.RegisterLayerDefinitions event) {
        event.registerLayerDefinition(RAPTOR, DinoGeometry::raptor);
        event.registerLayerDefinition(BRONTOSAURUS, DinoGeometry::brontosaurus);
        event.registerLayerDefinition(TRICERATOPS, DinoGeometry::triceratops);
        event.registerLayerDefinition(VENUS_CREEPER, DinoGeometry::venus_creeper);
        event.registerLayerDefinition(PTERANODON, DinoGeometry::pteranodon);
        event.registerLayerDefinition(TYRANNOSAURUS, DinoGeometry::tyrannosaurus);
        event.registerLayerDefinition(PLESIOSAUR, DinoGeometry::plesiosaur);
        event.registerLayerDefinition(MEGANEURA, DinoGeometry::meganeura);
        event.registerLayerDefinition(COMPSOGNATHUS, DinoGeometry::compsognathus);
        event.registerLayerDefinition(SPORE_MOTH, DinoGeometry::spore_moth);
        event.registerLayerDefinition(ANKYLOSAURUS, DinoGeometry::ankylosaurus);
        event.registerLayerDefinition(DEINOSUCHUS, DinoGeometry::deinosuchus);
    }

    private static void registerRenderers(EntityRenderersEvent.RegisterRenderers event) {
        event.registerEntityRenderer(ModDinosaurs.RAPTOR.get(),
                context -> new DinosaurRenderer<>(context, new RaptorModel(context.bakeLayer(RAPTOR)), 0.6F, "raptor", 0.6));
        event.registerEntityRenderer(ModDinosaurs.BRONTOSAURUS.get(),
                context -> new DinosaurRenderer<>(context, new BrontosaurusModel(context.bakeLayer(BRONTOSAURUS)), 2.0F, "brontosaurus", 3.5));
        event.registerEntityRenderer(ModDinosaurs.TRICERATOPS.get(),
                context -> new DinosaurRenderer<>(context, new TriceratopsModel(context.bakeLayer(TRICERATOPS)), 1.1F, "triceratops", 1.2));
        // the creeper's spore bulb and eyes, and the moth's wing spots, glow in the dark jungle
        event.registerEntityRenderer(ModDinosaurs.VENUS_CREEPER.get(), context -> glowing(new DinosaurRenderer<>(context,
                new VenusCreeperModel(context.bakeLayer(VENUS_CREEPER)), 0.5F, "venus_creeper", 0.3), CREEPER_GLOW));
        event.registerEntityRenderer(ModDinosaurs.SPORE_MOTH.get(), context -> glowing(new DinosaurRenderer<>(context,
                new SporeMothModel(context.bakeLayer(SPORE_MOTH)), 0.15F, "spore_moth", 0.3), MOTH_GLOW));
        event.registerEntityRenderer(ModDinosaurs.PLESIOSAUR.get(),
                context -> new DinosaurRenderer<>(context, new PlesiosaurModel(context.bakeLayer(PLESIOSAUR)), 1.2F, "plesiosaur", 5.0));
        event.registerEntityRenderer(ModDinosaurs.MEGANEURA.get(),
                context -> new DinosaurRenderer<>(context, new MeganeuraModel(context.bakeLayer(MEGANEURA)), 0.15F, "meganeura", 0.4));
        event.registerEntityRenderer(ModDinosaurs.COMPSOGNATHUS.get(),
                context -> new DinosaurRenderer<>(context, new CompsognathusModel(context.bakeLayer(COMPSOGNATHUS)), 0.3F, "compsognathus", 0.6));
        event.registerEntityRenderer(ModDinosaurs.ANKYLOSAURUS.get(),
                context -> new DinosaurRenderer<>(context, new AnkylosaurusModel(context.bakeLayer(ANKYLOSAURUS)), 1.0F, "ankylosaurus", 1.2));
        event.registerEntityRenderer(ModDinosaurs.DEINOSUCHUS.get(),
                context -> new DinosaurRenderer<>(context, new DeinosuchusModel(context.bakeLayer(DEINOSUCHUS)), 0.9F, "deinosuchus", 2.0));
        event.registerEntityRenderer(ModDinosaurs.PTERANODON.get(),
                context -> new DinosaurRenderer<>(context, new PteranodonModel(context.bakeLayer(PTERANODON)), 0.6F, "pteranodon", 1.6));
        event.registerEntityRenderer(ModDinosaurs.TYRANNOSAURUS.get(),
                context -> new DinosaurRenderer<>(context, new TyrannosaurusModel(context.bakeLayer(TYRANNOSAURUS)), 2.2F, "tyrannosaurus", 4.5));
    }

    /** Each tyrannosaurus footfall jolts the camera of anyone close by. */
    private static void shakeCamera(ViewportEvent.ComputeCameraAngles event) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.level == null || mc.player == null || mc.isPaused()) {
            return;
        }
        float partial = (float) event.getPartialTick();
        double strongest = 0.0;
        for (Tyrannosaurus rex : mc.level.getEntitiesOfClass(Tyrannosaurus.class, mc.player.getBoundingBox().inflate(SHAKE_RANGE))) {
            float speed = rex.walkAnimation.speed(partial);
            if (speed < 0.05F) {
                continue;
            }
            float step = Math.abs(Mth.cos(rex.walkAnimation.position(partial) * 0.35F));
            double falloff = 1.0 - Math.min(1.0, rex.distanceTo(mc.player) / SHAKE_RANGE);
            strongest = Math.max(strongest, Math.pow(step, 14.0) * Math.min(1.0F, speed * 1.6F) * falloff);
        }
        if (strongest > 0.01) {
            float time = mc.player.tickCount + partial;
            event.setPitch(event.getPitch() + (float) (strongest * 1.6 * Mth.sin(time * 2.9F)));
            event.setRoll(event.getRoll() + (float) (strongest * 1.1 * Mth.sin(time * 2.1F)));
        }
    }
}
