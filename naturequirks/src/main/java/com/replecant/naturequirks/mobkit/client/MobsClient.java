package com.replecant.naturequirks.mobkit.client;

import com.replecant.naturequirks.NatureQuirks;
import com.replecant.naturequirks.flowercreeper.client.FlowerCreeperClient;
import com.replecant.naturequirks.guardianbee.client.GuardianBeeClient;
import com.replecant.naturequirks.stonehead.client.StoneHeadClient;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.common.Mod;

/** Client-only entry point for the mobs (stone head, flower creeper, guardian bee): models and renderers. */
@Mod(value = NatureQuirks.MODID, dist = Dist.CLIENT)
public class MobsClient {
    public MobsClient(IEventBus modEventBus) {
        StoneHeadClient.init(modEventBus);
        FlowerCreeperClient.init(modEventBus);
        GuardianBeeClient.init(modEventBus);
    }
}
