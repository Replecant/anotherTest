package com.replecant.retrocosmos;

import com.mojang.logging.LogUtils;
import com.replecant.retrocosmos.command.RetroCosmosCommands;
import com.replecant.retrocosmos.flight.FlightEvents;
import com.replecant.retrocosmos.network.ModNetwork;
import com.replecant.retrocosmos.oxygen.OxygenSystem;
import com.replecant.retrocosmos.registry.ModAttachments;
import com.replecant.retrocosmos.registry.ModBlockEntities;
import com.replecant.retrocosmos.registry.ModBlocks;
import com.replecant.retrocosmos.registry.ModCreativeTabs;
import com.replecant.retrocosmos.registry.ModDataComponents;
import com.replecant.retrocosmos.registry.ModEntities;
import com.replecant.retrocosmos.registry.ModFurniture;
import com.replecant.retrocosmos.registry.ModItems;
import com.replecant.retrocosmos.registry.ModMenus;
import com.replecant.retrocosmos.station.StationSmokeTest;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.ModContainer;
import net.neoforged.fml.common.Mod;
import net.neoforged.neoforge.common.NeoForge;
import org.slf4j.Logger;

/**
 * Retro Cosmos - a retro-futuristic space travel mod.
 * Stage 1 ("Preparation"): gather resources, refine propellants, build the Liberty I, suit up and run the
 * countdown from the Mission Control console.
 */
@Mod(RetroCosmos.MODID)
public class RetroCosmos {
    public static final String MODID = "retrocosmos";
    public static final Logger LOGGER = LogUtils.getLogger();

    public RetroCosmos(IEventBus modEventBus, ModContainer modContainer) {
        ModFurniture.init();
        ModBlocks.BLOCKS.register(modEventBus);
        ModEntities.ENTITIES.register(modEventBus);
        ModItems.ITEMS.register(modEventBus);
        ModBlockEntities.TYPES.register(modEventBus);
        ModMenus.MENUS.register(modEventBus);
        ModCreativeTabs.TABS.register(modEventBus);
        ModDataComponents.COMPONENTS.register(modEventBus);
        ModAttachments.ATTACHMENTS.register(modEventBus);
        modEventBus.addListener(ModNetwork::register);
        NeoForge.EVENT_BUS.addListener(OxygenSystem::onPlayerTick);
        NeoForge.EVENT_BUS.addListener(FlightEvents::onMount);
        NeoForge.EVENT_BUS.addListener(StationSmokeTest::onServerStarted);
        NeoForge.EVENT_BUS.addListener(RetroCosmosCommands::register);
        LOGGER.info("Retro Cosmos: countdown initiated. Stage 1 - preparation.");
    }
}
