package com.replecant.retrocosmos.client;

import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.registry.ModMenus;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.common.Mod;
import net.neoforged.neoforge.client.event.RegisterGuiLayersEvent;
import net.neoforged.neoforge.client.event.RegisterMenuScreensEvent;
import net.neoforged.neoforge.client.gui.VanillaGuiLayers;

/** Client-only entry point: menu screens and the suit telemetry HUD. */
@Mod(value = RetroCosmos.MODID, dist = Dist.CLIENT)
public class RetroCosmosClient {
    public RetroCosmosClient(IEventBus modEventBus) {
        modEventBus.addListener(RetroCosmosClient::registerScreens);
        modEventBus.addListener(RetroCosmosClient::registerGuiLayers);
    }

    private static void registerGuiLayers(RegisterGuiLayersEvent event) {
        event.registerAbove(VanillaGuiLayers.EFFECTS, SuitHudLayer.ID, new SuitHudLayer());
    }

    private static void registerScreens(RegisterMenuScreensEvent event) {
        event.register(ModMenus.FUEL_REFINERY.get(), ProcessingScreen::new);
        event.register(ModMenus.AIR_LIQUEFIER.get(), ProcessingScreen::new);
        event.register(ModMenus.MISSION_CONTROL_CONSOLE.get(), ConsoleScreen::new);
    }
}
