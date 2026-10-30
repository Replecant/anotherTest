package com.replecant.retrocosmos.dinosaur.robot;

import com.replecant.retrocosmos.registry.ModEntities;
import com.replecant.retrocosmos.registry.ModItems;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.item.CreativeModeTabs;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.SpawnEggItem;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.event.BuildCreativeModeTabContentsEvent;
import net.neoforged.neoforge.event.entity.EntityAttributeCreationEvent;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredItem;

/** Dr. Oinstein's atomic robots: the hovering sentry, the walking automaton, the blaster bolt and their loot. */
public final class ModRobots {
    private static final List<DeferredItem<? extends Item>> ITEMS = new ArrayList<>();

    public static final DeferredHolder<EntityType<?>, EntityType<AtomicSentry>> ATOMIC_SENTRY = ModEntities.ENTITIES.register("atomic_sentry",
            id -> EntityType.Builder.of(AtomicSentry::new, MobCategory.MONSTER)
                    .sized(0.9F, 0.9F)
                    .eyeHeight(0.6F)
                    .fireImmune()
                    .clientTrackingRange(10)
                    .build(ResourceKey.create(Registries.ENTITY_TYPE, id)));

    public static final DeferredHolder<EntityType<?>, EntityType<AtomicAutomaton>> ATOMIC_AUTOMATON = ModEntities.ENTITIES.register("atomic_automaton",
            id -> EntityType.Builder.of(AtomicAutomaton::new, MobCategory.MONSTER)
                    .sized(1.2F, 2.4F)
                    .eyeHeight(2.1F)
                    .clientTrackingRange(10)
                    .build(ResourceKey.create(Registries.ENTITY_TYPE, id)));

    public static final DeferredHolder<EntityType<?>, EntityType<SentryBolt>> SENTRY_BOLT = ModEntities.ENTITIES.register("sentry_bolt",
            id -> EntityType.Builder.<SentryBolt>of(SentryBolt::new, MobCategory.MISC)
                    .sized(0.3125F, 0.3125F)
                    .noLootTable()
                    .clientTrackingRange(6)
                    .updateInterval(2)
                    .build(ResourceKey.create(Registries.ENTITY_TYPE, id)));

    /** Wreckage of a robot: four of them melt down to an iron ingot. */
    public static final DeferredItem<Item> ATOMIC_SCRAP = item(ModItems.ITEMS.registerItem("atomic_scrap", Item::new, p -> p));
    /** The glowing heart of one of the Doctor's machines - rare and valuable. */
    public static final DeferredItem<Item> ATOMIC_CORE = item(ModItems.ITEMS.registerItem("atomic_core", Item::new,
            p -> p.rarity(Rarity.RARE)));

    public static final DeferredItem<SpawnEggItem> ATOMIC_SENTRY_SPAWN_EGG = item(ModItems.ITEMS.registerItem("atomic_sentry_spawn_egg",
            SpawnEggItem::new, p -> p.spawnEgg(ATOMIC_SENTRY.get())));
    public static final DeferredItem<SpawnEggItem> ATOMIC_AUTOMATON_SPAWN_EGG = item(ModItems.ITEMS.registerItem("atomic_automaton_spawn_egg",
            SpawnEggItem::new, p -> p.spawnEgg(ATOMIC_AUTOMATON.get())));

    private ModRobots() {}

    /** Called from ModDinosaurs.init (mod constructor), before the deferred registers are attached. */
    public static void init(IEventBus modEventBus) {
        modEventBus.addListener(ModRobots::createAttributes);
        modEventBus.addListener(ModRobots::addToVanillaTabs);
    }

    /** Scrap, core and the eggs, for the Venus creative tab. */
    public static List<DeferredItem<? extends Item>> items() {
        return Collections.unmodifiableList(ITEMS);
    }

    private static <I extends Item> DeferredItem<I> item(DeferredItem<I> item) {
        ITEMS.add(item);
        return item;
    }

    private static void createAttributes(EntityAttributeCreationEvent event) {
        event.put(ATOMIC_SENTRY.get(), AtomicSentry.createAttributes().build());
        event.put(ATOMIC_AUTOMATON.get(), AtomicAutomaton.createAttributes().build());
    }

    private static void addToVanillaTabs(BuildCreativeModeTabContentsEvent event) {
        if (event.getTabKey() == CreativeModeTabs.SPAWN_EGGS) {
            event.accept(ATOMIC_SENTRY_SPAWN_EGG.get());
            event.accept(ATOMIC_AUTOMATON_SPAWN_EGG.get());
        }
    }
}
