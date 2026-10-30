package com.replecant.naturequirks.flowercreeper;

import com.replecant.naturequirks.NatureQuirks;
import com.replecant.naturequirks.registry.ModTab;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.entity.SpawnPlacementTypes;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.item.SpawnEggItem;
import net.minecraft.world.level.levelgen.Heightmap;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.event.entity.EntityAttributeCreationEvent;
import net.neoforged.neoforge.event.entity.RegisterSpawnPlacementsEvent;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredItem;
import net.neoforged.neoforge.registries.DeferredRegister;

/** The flower creeper: entity type, spawn egg, the hay-fever effect of its pollen, spawn rules. */
public final class FlowerCreepers {
    public static final DeferredRegister<EntityType<?>> ENTITIES = DeferredRegister.create(Registries.ENTITY_TYPE, NatureQuirks.MODID);
    public static final DeferredRegister.Items ITEMS = DeferredRegister.createItems(NatureQuirks.MODID);
    public static final DeferredRegister<MobEffect> EFFECTS = DeferredRegister.create(Registries.MOB_EFFECT, NatureQuirks.MODID);

    /** Exactly the vanilla creeper's size. */
    public static final DeferredHolder<EntityType<?>, EntityType<FlowerCreeper>> FLOWER_CREEPER = ENTITIES.register("flower_creeper",
            id -> EntityType.Builder.of(FlowerCreeper::new, MobCategory.MONSTER)
                    .sized(0.6F, 1.7F)
                    .clientTrackingRange(8)
                    .build(ResourceKey.create(Registries.ENTITY_TYPE, id)));

    public static final DeferredItem<SpawnEggItem> FLOWER_CREEPER_SPAWN_EGG = ITEMS.registerItem("flower_creeper_spawn_egg",
            SpawnEggItem::new, p -> p.spawnEgg(FLOWER_CREEPER.get()));

    /** Sneezing fits from the pollen cloud. */
    public static final DeferredHolder<MobEffect, HayFeverEffect> HAY_FEVER = EFFECTS.register("hay_fever", HayFeverEffect::new);

    private FlowerCreepers() {}

    public static void init(IEventBus modEventBus) {
        ENTITIES.register(modEventBus);
        ITEMS.register(modEventBus);
        EFFECTS.register(modEventBus);
        modEventBus.addListener(FlowerCreepers::attributes);
        modEventBus.addListener(FlowerCreepers::spawnPlacements);
        ModTab.add(FLOWER_CREEPER_SPAWN_EGG);
    }

    private static void attributes(EntityAttributeCreationEvent event) {
        event.put(FLOWER_CREEPER.get(), FlowerCreeper.createAttributes().build());
    }

    /** Like a creeper: dark places only (the flowery biomes are picked by the biome modifier). */
    private static void spawnPlacements(RegisterSpawnPlacementsEvent event) {
        event.register(FLOWER_CREEPER.get(), SpawnPlacementTypes.ON_GROUND, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
                Monster::checkMonsterSpawnRules, RegisterSpawnPlacementsEvent.Operation.REPLACE);
    }
}
