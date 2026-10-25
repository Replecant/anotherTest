package com.replecant.retrocosmos.dinosaur;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import net.minecraft.world.item.Item;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.registries.DeferredItem;

/** The dinosaurs of Venus: entity types, attributes, spawn rules and spawn eggs. */
public final class ModDinosaurs {
    private static final List<DeferredItem<? extends Item>> ITEMS = new ArrayList<>();

    private ModDinosaurs() {}

    /** Called from the mod constructor before the deferred registers are attached. */
    public static void init(IEventBus modEventBus) {
    }

    /** Spawn eggs etc. for the Venus creative tab, in order. */
    public static List<DeferredItem<? extends Item>> items() {
        return Collections.unmodifiableList(ITEMS);
    }
}
