package com.replecant.retrocosmos.npc;

import com.replecant.retrocosmos.npc.CooperTrades.Deal;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.world.item.trading.MerchantOffer;

/**
 * The Space Rangers' quartermaster's list, kept by Captain Morrow: energy cartridges for the ranger blaster, sold
 * to sworn-in rangers for Space Credits. The cartridges are the tribes agent's item, looked up by id, so the list
 * is simply empty until it exists. Bump {@link #VERSION} when the list changes.
 */
public final class RangerTrades {
    public static final int VERSION = 1;

    private RangerTrades() {}

    public static final List<Deal> REQUISITIONS = List.of(
            CooperTrades.sells(2, "retrocosmos:energy_cartridge", 16, 32),
            CooperTrades.sells(7, "retrocosmos:energy_cartridge", 64, 16));

    public static List<MerchantOffer> create() {
        List<MerchantOffer> offers = new ArrayList<>();
        for (Deal deal : REQUISITIONS) {
            deal.offer().ifPresent(offers::add);
        }
        return offers;
    }
}
