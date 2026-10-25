package com.replecant.retrocosmos.dinosaur;

import com.replecant.retrocosmos.registry.ModEntities;
import com.replecant.retrocosmos.registry.ModItems;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.entity.SpawnPlacementTypes;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.item.CreativeModeTabs;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.SpawnEggItem;
import net.minecraft.world.level.levelgen.Heightmap;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.event.BuildCreativeModeTabContentsEvent;
import net.neoforged.neoforge.event.entity.EntityAttributeCreationEvent;
import net.neoforged.neoforge.event.entity.RegisterSpawnPlacementsEvent;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredItem;

/** The dinosaurs of Venus: entity types, attributes, spawn rules and spawn eggs. */
public final class ModDinosaurs {
    private static final List<DeferredItem<? extends Item>> ITEMS = new ArrayList<>();

    /** Venus Raptor: a fast, leaping pack hunter, about as tall as a man's chest. */
    public static final DeferredHolder<EntityType<?>, EntityType<VenusRaptor>> RAPTOR = ModEntities.ENTITIES.register("raptor",
            id -> EntityType.Builder.of(VenusRaptor::new, MobCategory.MONSTER)
                    .sized(1.0F, 1.4F)
                    .eyeHeight(1.15F)
                    .clientTrackingRange(10)
                    .build(ResourceKey.create(Registries.ENTITY_TYPE, id)));

    /** Brontosaurus: the gentle five-block giant of the Venus jungle. */
    public static final DeferredHolder<EntityType<?>, EntityType<Brontosaurus>> BRONTOSAURUS = ModEntities.ENTITIES.register("brontosaurus",
            id -> EntityType.Builder.of(Brontosaurus::new, MobCategory.CREATURE)
                    .sized(2.8F, 4.4F)
                    .eyeHeight(4.0F)
                    .clientTrackingRange(12)
                    .build(ResourceKey.create(Registries.ENTITY_TYPE, id)));

    /** Triceratops: a horned herbivore that minds its own business - until provoked. */
    public static final DeferredHolder<EntityType<?>, EntityType<Triceratops>> TRICERATOPS = ModEntities.ENTITIES.register("triceratops",
            id -> EntityType.Builder.of(Triceratops::new, MobCategory.CREATURE)
                    .sized(1.8F, 1.9F)
                    .eyeHeight(1.3F)
                    .clientTrackingRange(10)
                    .build(ResourceKey.create(Registries.ENTITY_TYPE, id)));

    public static final DeferredItem<SpawnEggItem> RAPTOR_SPAWN_EGG = egg("raptor_spawn_egg", RAPTOR);
    public static final DeferredItem<SpawnEggItem> BRONTOSAURUS_SPAWN_EGG = egg("brontosaurus_spawn_egg", BRONTOSAURUS);
    public static final DeferredItem<SpawnEggItem> TRICERATOPS_SPAWN_EGG = egg("triceratops_spawn_egg", TRICERATOPS);

    private ModDinosaurs() {}

    /** Called from the mod constructor before the deferred registers are attached. */
    public static void init(IEventBus modEventBus) {
        modEventBus.addListener(ModDinosaurs::createAttributes);
        modEventBus.addListener(ModDinosaurs::registerSpawnPlacements);
        modEventBus.addListener(ModDinosaurs::addToVanillaTabs);
    }

    /** Spawn eggs etc. for the Venus creative tab, in order. */
    public static List<DeferredItem<? extends Item>> items() {
        return Collections.unmodifiableList(ITEMS);
    }

    private static DeferredItem<SpawnEggItem> egg(String name, DeferredHolder<EntityType<?>, ? extends EntityType<? extends Mob>> type) {
        DeferredItem<SpawnEggItem> item = ModItems.ITEMS.registerItem(name, SpawnEggItem::new, p -> p.spawnEgg(type.get()));
        ITEMS.add(item);
        return item;
    }

    /** Besides the Venus tab, the eggs also sit with the vanilla spawn eggs. */
    private static void addToVanillaTabs(BuildCreativeModeTabContentsEvent event) {
        if (event.getTabKey() == CreativeModeTabs.SPAWN_EGGS) {
            ITEMS.forEach(item -> event.accept(item.get()));
        }
    }

    private static void createAttributes(EntityAttributeCreationEvent event) {
        event.put(RAPTOR.get(), VenusRaptor.createAttributes().build());
        event.put(BRONTOSAURUS.get(), Brontosaurus.createAttributes().build());
        event.put(TRICERATOPS.get(), Triceratops.createAttributes().build());
    }

    /** On the ground, under the jungle canopy; Venus is dim, so light level does not matter. */
    private static void registerSpawnPlacements(RegisterSpawnPlacementsEvent event) {
        event.register(RAPTOR.get(), SpawnPlacementTypes.ON_GROUND, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
                Monster::checkAnyLightMonsterSpawnRules, RegisterSpawnPlacementsEvent.Operation.REPLACE);
        event.register(BRONTOSAURUS.get(), SpawnPlacementTypes.ON_GROUND, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
                Mob::checkMobSpawnRules, RegisterSpawnPlacementsEvent.Operation.REPLACE);
        event.register(TRICERATOPS.get(), SpawnPlacementTypes.ON_GROUND, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
                Mob::checkMobSpawnRules, RegisterSpawnPlacementsEvent.Operation.REPLACE);
    }
}
