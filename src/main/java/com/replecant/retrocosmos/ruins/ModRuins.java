package com.replecant.retrocosmos.ruins;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import net.minecraft.world.item.Item;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.registries.DeferredItem;

/** Ancient Venusian ruins: carved stone blocks, artifacts and the structures' Java pieces. */
public final class ModRuins {
    private static final List<DeferredItem<? extends Item>> ITEMS = new ArrayList<>();

    private ModRuins() {}

    /** Called from the mod constructor before the deferred registers are attached. */
    public static void init(IEventBus modEventBus) {
    }

    /** Items for the Venus creative tab, in order. */
    public static List<DeferredItem<? extends Item>> items() {
        return Collections.unmodifiableList(ITEMS);
    }
}
