package com.replecant.retrocosmos.client;

import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.dinosaur.DinosaurClient;
import com.replecant.retrocosmos.flight.RocketEntity;
import com.replecant.retrocosmos.registry.ModEntities;
import com.replecant.retrocosmos.registry.ModMenus;
import com.replecant.retrocosmos.tribe.TribeClient;
import net.minecraft.client.CameraType;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.entity.NoopRenderer;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.common.Mod;
import net.neoforged.neoforge.client.event.CalculateDetachedCameraDistanceEvent;
import net.neoforged.neoforge.client.event.ClientTickEvent;
import net.neoforged.neoforge.client.event.EntityRenderersEvent;
import net.neoforged.neoforge.client.event.RegisterGuiLayersEvent;
import net.neoforged.neoforge.client.event.RegisterMenuScreensEvent;
import net.neoforged.neoforge.client.gui.VanillaGuiLayers;
import net.neoforged.neoforge.common.NeoForge;

/** Client-only entry point: menu screens and the suit telemetry HUD. */
@Mod(value = RetroCosmos.MODID, dist = Dist.CLIENT)
public class RetroCosmosClient {
    public RetroCosmosClient(IEventBus modEventBus) {
        modEventBus.addListener(RetroCosmosClient::registerScreens);
        DinosaurClient.init(modEventBus);
        TribeClient.init(modEventBus);
        modEventBus.addListener(RetroCosmosClient::registerGuiLayers);
        modEventBus.addListener(RetroCosmosClient::registerRenderers);
        NeoForge.EVENT_BUS.addListener(RetroCosmosClient::onClientTick);
        NeoForge.EVENT_BUS.addListener(RetroCosmosClient::onCameraDistance);
    }

    /** Camera the player used before boarding a rocket; restored after leaving it. */
    private static CameraType cameraBeforeFlight;

    /** Pulls the third-person camera back far enough to see the whole nine-block rocket. */
    private static void onCameraDistance(CalculateDetachedCameraDistanceEvent event) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player != null && mc.player.getVehicle() instanceof RocketEntity) {
            event.setDistance(Math.max(event.getDistance(), 14.0F));
        }
    }

    /** Opens the system map whenever the player sits in a rocket that has reached orbit. */
    private static void onClientTick(ClientTickEvent.Post event) {
        Minecraft mc = Minecraft.getInstance();
        boolean inRocket = mc.player != null && mc.player.getVehicle() instanceof RocketEntity;
        if (inRocket && cameraBeforeFlight == null) {
            // boarding: switch to an outside view of the rocket
            cameraBeforeFlight = mc.options.getCameraType();
            mc.options.setCameraType(CameraType.THIRD_PERSON_BACK);
        } else if (!inRocket && cameraBeforeFlight != null) {
            mc.options.setCameraType(cameraBeforeFlight);
            cameraBeforeFlight = null;
        }
        if (mc.player != null && mc.screen == null && mc.player.getVehicle() instanceof RocketEntity rocket
                && rocket.phase() == RocketEntity.PHASE_ORBIT) {
            mc.setScreen(new SystemMapScreen());
        }
    }

    private static void registerRenderers(EntityRenderersEvent.RegisterRenderers event) {
        event.registerEntityRenderer(ModEntities.SEAT.get(), NoopRenderer::new);
        event.registerEntityRenderer(ModEntities.ROCKET.get(), RocketRenderer::new);
    }

    private static void registerGuiLayers(RegisterGuiLayersEvent event) {
        event.registerBelow(VanillaGuiLayers.CROSSHAIR, CockpitLayer.ID, new CockpitLayer());
        event.registerAbove(VanillaGuiLayers.EFFECTS, SuitHudLayer.ID, new SuitHudLayer());
        event.registerAbove(SuitHudLayer.ID, FlightHudLayer.ID, new FlightHudLayer());
    }

    private static void registerScreens(RegisterMenuScreensEvent event) {
        event.register(ModMenus.FUEL_REFINERY.get(), ProcessingScreen::new);
        event.register(ModMenus.AIR_LIQUEFIER.get(), ProcessingScreen::new);
        event.register(ModMenus.MISSION_CONTROL_CONSOLE.get(), ConsoleScreen::new);
    }
}
