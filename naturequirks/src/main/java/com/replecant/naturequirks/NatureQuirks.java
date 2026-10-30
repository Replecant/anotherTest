package com.replecant.naturequirks;

import com.mojang.logging.LogUtils;
import com.replecant.naturequirks.registry.ModTab;
import com.replecant.naturequirks.guardianbee.GuardianBees;
import com.replecant.naturequirks.flowercreeper.FlowerCreepers;
import com.replecant.naturequirks.stonehead.StoneHeads;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.ModContainer;
import net.neoforged.fml.common.Mod;
import org.slf4j.Logger;

/**
 * Nature's Quirks - vanilla-style oddities of the Overworld. Each feature lives in its own package with an
 * {@code init(IEventBus)} that registers its content and adds its items to {@link ModTab}.
 */
@Mod(NatureQuirks.MODID)
public class NatureQuirks {
    public static final String MODID = "naturequirks";
    public static final Logger LOGGER = LogUtils.getLogger();

    public NatureQuirks(IEventBus modEventBus, ModContainer modContainer) {
        ModTab.TABS.register(modEventBus);
        StoneHeads.init(modEventBus);
        FlowerCreepers.init(modEventBus);
        GuardianBees.init(modEventBus);
        LOGGER.info("Nature's Quirks: the Overworld got a little stranger.");
    }
}
