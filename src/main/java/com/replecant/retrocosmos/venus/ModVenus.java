package com.replecant.retrocosmos.venus;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import net.minecraft.world.item.Item;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.registries.DeferredItem;

/** Venus blocks and items (registered into the mod's shared deferred registers). */
public final class ModVenus {
    private static final List<DeferredItem<? extends Item>> ITEMS = new ArrayList<>();

    private ModVenus() {}

    /** Called from the mod constructor before the deferred registers are attached. */
    public static void init(IEventBus modEventBus) {
    }

    /** Items for the Venus creative tab, in order. */
    public static List<DeferredItem<? extends Item>> items() {
        return Collections.unmodifiableList(ITEMS);
    }
}
