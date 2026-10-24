package com.replecant.retrocosmos;

import com.mojang.logging.LogUtils;
import com.replecant.retrocosmos.registry.ModBlocks;
import com.replecant.retrocosmos.registry.ModCreativeTabs;
import com.replecant.retrocosmos.registry.ModItems;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.ModContainer;
import net.neoforged.fml.common.Mod;
import org.slf4j.Logger;

/**
 * Retro Cosmos - a retro-futuristic space travel mod.
 * Stage 1 ("Preparation"): gather resources, build a rocket, suit up and run the pre-flight check.
 */
@Mod(RetroCosmos.MODID)
public class RetroCosmos {
    public static final String MODID = "retrocosmos";
    public static final Logger LOGGER = LogUtils.getLogger();

    public RetroCosmos(IEventBus modEventBus, ModContainer modContainer) {
        ModBlocks.BLOCKS.register(modEventBus);
        ModItems.ITEMS.register(modEventBus);
        ModCreativeTabs.TABS.register(modEventBus);
        LOGGER.info("Retro Cosmos: countdown initiated. Stage 1 - preparation.");
    }
}
