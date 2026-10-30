package com.replecant.naturequirks.guardianbee;

import com.replecant.naturequirks.NatureQuirks;
import com.replecant.naturequirks.registry.ModTab;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.item.SpawnEggItem;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.event.entity.EntityAttributeCreationEvent;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredItem;
import net.neoforged.neoforge.registries.DeferredRegister;

/**
 * The guardian bee: the soldier of the giant hives. It has no natural spawns - hives place it (as structure entities)
 * or call {@link GuardianBee#spawn}.
 */
public final class GuardianBees {
    public static final DeferredRegister<EntityType<?>> ENTITIES = DeferredRegister.create(Registries.ENTITY_TYPE, NatureQuirks.MODID);
    public static final DeferredRegister.Items ITEMS = DeferredRegister.createItems(NatureQuirks.MODID);

    /** 1.4x a vanilla bee (0.7 x 0.6). */
    public static final DeferredHolder<EntityType<?>, EntityType<GuardianBee>> GUARDIAN_BEE = ENTITIES.register("guardian_bee",
            id -> EntityType.Builder.of(GuardianBee::new, MobCategory.MONSTER)
                    .sized(0.98F, 0.84F)
                    .eyeHeight(0.42F)
                    .clientTrackingRange(8)
                    .build(ResourceKey.create(Registries.ENTITY_TYPE, id)));

    public static final DeferredItem<SpawnEggItem> GUARDIAN_BEE_SPAWN_EGG = ITEMS.registerItem("guardian_bee_spawn_egg",
            SpawnEggItem::new, p -> p.spawnEgg(GUARDIAN_BEE.get()));

    private GuardianBees() {}

    public static void init(IEventBus modEventBus) {
        ENTITIES.register(modEventBus);
        ITEMS.register(modEventBus);
        modEventBus.addListener((EntityAttributeCreationEvent event) ->
                event.put(GUARDIAN_BEE.get(), GuardianBee.createAttributes().build()));
        ModTab.add(GUARDIAN_BEE_SPAWN_EGG);
    }
}
