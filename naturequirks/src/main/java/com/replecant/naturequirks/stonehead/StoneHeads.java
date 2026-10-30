package com.replecant.naturequirks.stonehead;

import com.mojang.serialization.Codec;
import com.replecant.naturequirks.NatureQuirks;
import com.replecant.naturequirks.registry.ModTab;
import net.minecraft.core.component.DataComponentType;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.tags.BlockTags;
import net.minecraft.tags.TagKey;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.entity.SpawnPlacementTypes;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.SpawnEggItem;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.event.entity.EntityAttributeCreationEvent;
import net.neoforged.neoforge.event.entity.RegisterSpawnPlacementsEvent;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredItem;
import net.neoforged.neoforge.registries.DeferredRegister;

/** The stone heads of the beaches and the geodes they chew things into. */
public final class StoneHeads {
    public static final DeferredRegister<EntityType<?>> ENTITIES = DeferredRegister.create(Registries.ENTITY_TYPE, NatureQuirks.MODID);
    public static final DeferredRegister.Items ITEMS = DeferredRegister.createItems(NatureQuirks.MODID);
    public static final DeferredRegister<DataComponentType<?>> COMPONENTS = DeferredRegister.create(Registries.DATA_COMPONENT_TYPE, NatureQuirks.MODID);

    /** Items a stone head especially enjoys: gems, ingots, ores, amethyst. They make luckier geodes. */
    public static final TagKey<Item> DELICACIES = TagKey.create(Registries.ITEM,
            Identifier.fromNamespaceAndPath(NatureQuirks.MODID, "stone_head_delicacies"));

    public static final DeferredHolder<EntityType<?>, EntityType<StoneHead>> STONE_HEAD = ENTITIES.register("stone_head",
            id -> EntityType.Builder.of(StoneHead::new, MobCategory.CREATURE)
                    .sized(1.4F, 2.2F)
                    .eyeHeight(1.45F)
                    .fireImmune()
                    .clientTrackingRange(10)
                    .build(ResourceKey.create(Registries.ENTITY_TYPE, id)));

    /** Loot luck baked into a geode by what the head was fed (0 = an ordinary geode). */
    public static final DeferredHolder<DataComponentType<?>, DataComponentType<Integer>> GEODE_LUCK = COMPONENTS.register("geode_luck",
            () -> DataComponentType.<Integer>builder().persistent(Codec.INT).networkSynchronized(ByteBufCodecs.VAR_INT).build());

    public static final DeferredItem<GeodeItem> GEODE = ITEMS.registerItem("geode", GeodeItem::new, p -> p.stacksTo(64));
    public static final DeferredItem<SpawnEggItem> STONE_HEAD_SPAWN_EGG = ITEMS.registerItem("stone_head_spawn_egg",
            SpawnEggItem::new, p -> p.spawnEgg(STONE_HEAD.get()));

    private StoneHeads() {}

    public static void init(IEventBus modEventBus) {
        ENTITIES.register(modEventBus);
        ITEMS.register(modEventBus);
        COMPONENTS.register(modEventBus);
        modEventBus.addListener(StoneHeads::attributes);
        modEventBus.addListener(StoneHeads::spawnPlacements);
        ModTab.add(GEODE);
        ModTab.add(STONE_HEAD_SPAWN_EGG);
    }

    private static void attributes(EntityAttributeCreationEvent event) {
        event.put(STONE_HEAD.get(), StoneHead.createAttributes().build());
    }

    /** On sand, gravel or bare rock by the sea; even where the biome allows one, only now and then. */
    private static void spawnPlacements(RegisterSpawnPlacementsEvent event) {
        event.register(STONE_HEAD.get(), SpawnPlacementTypes.ON_GROUND, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
                (type, level, reason, pos, random) -> {
                    BlockState below = level.getBlockState(pos.below());
                    boolean ground = below.is(BlockTags.SAND) || below.is(Blocks.GRAVEL) || below.is(BlockTags.BASE_STONE_OVERWORLD);
                    boolean natural = reason == EntitySpawnReason.NATURAL || reason == EntitySpawnReason.CHUNK_GENERATION;
                    return ground && level.getBlockState(pos).getFluidState().isEmpty() && (!natural || random.nextInt(3) == 0);
                }, RegisterSpawnPlacementsEvent.Operation.REPLACE);
    }
}
