package com.replecant.retrocosmos.dinosaur;

import com.replecant.retrocosmos.registry.ModBlocks;
import com.replecant.retrocosmos.registry.ModEntities;
import com.replecant.retrocosmos.registry.ModItems;
import com.replecant.retrocosmos.venus.VenusLanding;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.FluidTags;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.entity.SpawnPlacementTypes;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.CreativeModeTabs;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.SpawnEggItem;
import net.minecraft.world.item.ToolMaterial;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.material.MapColor;
import net.minecraft.world.phys.AABB;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.event.BuildCreativeModeTabContentsEvent;
import net.neoforged.neoforge.event.entity.EntityAttributeCreationEvent;
import net.neoforged.neoforge.event.entity.RegisterSpawnPlacementsEvent;
import net.neoforged.neoforge.registries.DeferredBlock;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredItem;

/** The dinosaurs of Venus: entity types, attributes, spawn rules and spawn eggs. */
public final class ModDinosaurs {
    private static final List<DeferredItem<? extends Item>> ITEMS = new ArrayList<>();
    private static final List<DeferredItem<? extends Item>> EGGS = new ArrayList<>();

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

    /** Venus Creeper: a walking seed-pod that bursts into a cloud of poison spores. */
    public static final DeferredHolder<EntityType<?>, EntityType<VenusCreeper>> VENUS_CREEPER = ModEntities.ENTITIES.register("venus_creeper",
            id -> EntityType.Builder.of(VenusCreeper::new, MobCategory.MONSTER)
                    .sized(0.6F, 1.7F)
                    .clientTrackingRange(8)
                    .build(ResourceKey.create(Registries.ENTITY_TYPE, id)));

    /** Pteranodon: roosts on the tops of the giant trees and circles over the jungle. */
    public static final DeferredHolder<EntityType<?>, EntityType<Pteranodon>> PTERANODON = ModEntities.ENTITIES.register("pteranodon",
            id -> EntityType.Builder.of(Pteranodon::new, MobCategory.CREATURE)
                    .sized(1.2F, 0.9F)
                    .eyeHeight(0.6F)
                    .clientTrackingRange(10)
                    .build(ResourceKey.create(Registries.ENTITY_TYPE, id)));

    /** Tyrannosaurus: the rare apex predator. */
    public static final DeferredHolder<EntityType<?>, EntityType<Tyrannosaurus>> TYRANNOSAURUS = ModEntities.ENTITIES.register("tyrannosaurus",
            id -> EntityType.Builder.of(Tyrannosaurus::new, MobCategory.MONSTER)
                    .sized(2.8F, 5.2F)
                    .eyeHeight(4.6F)
                    .clientTrackingRange(16)
                    .build(ResourceKey.create(Registries.ENTITY_TYPE, id)));

    /** Plesiosaur: the long-necked sea monster of the steaming sea. */
    public static final DeferredHolder<EntityType<?>, EntityType<Plesiosaur>> PLESIOSAUR = ModEntities.ENTITIES.register("plesiosaur",
            id -> EntityType.Builder.of(Plesiosaur::new, MobCategory.WATER_CREATURE)
                    .sized(2.4F, 1.4F)
                    .eyeHeight(1.0F)
                    .clientTrackingRange(12)
                    .build(ResourceKey.create(Registries.ENTITY_TYPE, id)));

    /** Meganeura: giant dragonflies over the swamp and jungle (ambient). */
    public static final DeferredHolder<EntityType<?>, EntityType<Meganeura>> MEGANEURA = ModEntities.ENTITIES.register("meganeura",
            id -> EntityType.Builder.of(Meganeura::new, MobCategory.AMBIENT)
                    .sized(0.6F, 0.3F)
                    .clientTrackingRange(5)
                    .build(ResourceKey.create(Registries.ENTITY_TYPE, id)));

    /** Compsognathus: skittish chicken-sized scavengers. */
    public static final DeferredHolder<EntityType<?>, EntityType<Compsognathus>> COMPSOGNATHUS = ModEntities.ENTITIES.register("compsognathus",
            id -> EntityType.Builder.of(Compsognathus::new, MobCategory.CREATURE)
                    .sized(0.4F, 0.7F)
                    .eyeHeight(0.6F)
                    .clientTrackingRange(8)
                    .build(ResourceKey.create(Registries.ENTITY_TYPE, id)));

    /** Spore moth: glowing moths of the glowcap hollows (ambient). */
    public static final DeferredHolder<EntityType<?>, EntityType<SporeMoth>> SPORE_MOTH = ModEntities.ENTITIES.register("spore_moth",
            id -> EntityType.Builder.of(SporeMoth::new, MobCategory.AMBIENT)
                    .sized(0.5F, 0.4F)
                    .clientTrackingRange(5)
                    .build(ResourceKey.create(Registries.ENTITY_TYPE, id)));

    /** Ankylosaurus: the armoured tank of the highlands. */
    public static final DeferredHolder<EntityType<?>, EntityType<Ankylosaurus>> ANKYLOSAURUS = ModEntities.ENTITIES.register("ankylosaurus",
            id -> EntityType.Builder.of(Ankylosaurus::new, MobCategory.CREATURE)
                    .sized(1.5F, 1.3F)
                    .eyeHeight(0.9F)
                    .clientTrackingRange(10)
                    .build(ResourceKey.create(Registries.ENTITY_TYPE, id)));

    /** Deinosuchus: the giant ambush crocodile of the fern swamp. */
    public static final DeferredHolder<EntityType<?>, EntityType<Deinosuchus>> DEINOSUCHUS = ModEntities.ENTITIES.register("deinosuchus",
            id -> EntityType.Builder.of(Deinosuchus::new, MobCategory.MONSTER)
                    .sized(1.5F, 0.85F)
                    .eyeHeight(0.6F)
                    .clientTrackingRange(10)
                    .build(ResourceKey.create(Registries.ENTITY_TYPE, id)));

    // ---- curios the expedition can sell ----
    public static final DeferredItem<Item> PLESIOSAUR_TOOTH = item(ModItems.ITEMS.registerItem("plesiosaur_tooth",
            Item::new, p -> p.rarity(Rarity.UNCOMMON)));
    public static final DeferredItem<Item> DEINOSUCHUS_TOOTH = item(ModItems.ITEMS.registerItem("deinosuchus_tooth",
            Item::new, p -> p.rarity(Rarity.UNCOMMON)));
    public static final DeferredItem<Item> ANKYLOSAURUS_PLATE = item(ModItems.ITEMS.registerItem("ankylosaurus_plate",
            Item::new, p -> p.rarity(Rarity.UNCOMMON)));

    // ---- the tyrant's trophies ----
    public static final DeferredBlock<TyrannosaurusSkullBlock> TYRANNOSAURUS_SKULL = ModBlocks.BLOCKS.register("tyrannosaurus_skull",
            id -> new TyrannosaurusSkullBlock(BlockBehaviour.Properties.of().setId(ResourceKey.create(Registries.BLOCK, id))
                    .mapColor(MapColor.SAND).strength(1.5F).sound(SoundType.BONE_BLOCK).noOcclusion()));
    public static final DeferredItem<BlockItem> TYRANNOSAURUS_SKULL_ITEM = item(ModItems.ITEMS.registerItem("tyrannosaurus_skull",
            p -> new BlockItem(TYRANNOSAURUS_SKULL.get(), p), p -> p.useBlockDescriptionPrefix().rarity(Rarity.EPIC)));
    /** A rare, valuable trophy - traders pay well for it. */
    public static final DeferredItem<Item> TYRANNOSAURUS_FANG = item(ModItems.ITEMS.registerItem("tyrannosaurus_fang",
            Item::new, p -> p.rarity(Rarity.RARE)));
    public static final DeferredItem<Item> FANG_DAGGER = item(ModItems.ITEMS.registerItem("fang_dagger",
            Item::new, p -> p.sword(ToolMaterial.IRON, 3.5F, -2.0F).rarity(Rarity.UNCOMMON)));

    public static final DeferredItem<SpawnEggItem> RAPTOR_SPAWN_EGG = egg("raptor_spawn_egg", RAPTOR);
    public static final DeferredItem<SpawnEggItem> BRONTOSAURUS_SPAWN_EGG = egg("brontosaurus_spawn_egg", BRONTOSAURUS);
    public static final DeferredItem<SpawnEggItem> TRICERATOPS_SPAWN_EGG = egg("triceratops_spawn_egg", TRICERATOPS);
    public static final DeferredItem<SpawnEggItem> VENUS_CREEPER_SPAWN_EGG = egg("venus_creeper_spawn_egg", VENUS_CREEPER);
    public static final DeferredItem<SpawnEggItem> PTERANODON_SPAWN_EGG = egg("pteranodon_spawn_egg", PTERANODON);
    public static final DeferredItem<SpawnEggItem> TYRANNOSAURUS_SPAWN_EGG = egg("tyrannosaurus_spawn_egg", TYRANNOSAURUS);
    public static final DeferredItem<SpawnEggItem> PLESIOSAUR_SPAWN_EGG = egg("plesiosaur_spawn_egg", PLESIOSAUR);
    public static final DeferredItem<SpawnEggItem> MEGANEURA_SPAWN_EGG = egg("meganeura_spawn_egg", MEGANEURA);
    public static final DeferredItem<SpawnEggItem> COMPSOGNATHUS_SPAWN_EGG = egg("compsognathus_spawn_egg", COMPSOGNATHUS);
    public static final DeferredItem<SpawnEggItem> SPORE_MOTH_SPAWN_EGG = egg("spore_moth_spawn_egg", SPORE_MOTH);
    public static final DeferredItem<SpawnEggItem> ANKYLOSAURUS_SPAWN_EGG = egg("ankylosaurus_spawn_egg", ANKYLOSAURUS);
    public static final DeferredItem<SpawnEggItem> DEINOSUCHUS_SPAWN_EGG = egg("deinosuchus_spawn_egg", DEINOSUCHUS);

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
        DeferredItem<SpawnEggItem> item = item(ModItems.ITEMS.registerItem(name, SpawnEggItem::new, p -> p.spawnEgg(type.get())));
        EGGS.add(item);
        return item;
    }

    private static <I extends Item> DeferredItem<I> item(DeferredItem<I> item) {
        ITEMS.add(item);
        return item;
    }

    /** Besides the Venus tab, the eggs also sit with the vanilla spawn eggs. */
    private static void addToVanillaTabs(BuildCreativeModeTabContentsEvent event) {
        if (event.getTabKey() == CreativeModeTabs.SPAWN_EGGS) {
            EGGS.forEach(item -> event.accept(item.get()));
        }
    }

    private static void createAttributes(EntityAttributeCreationEvent event) {
        event.put(RAPTOR.get(), VenusRaptor.createAttributes().build());
        event.put(BRONTOSAURUS.get(), Brontosaurus.createAttributes().build());
        event.put(TRICERATOPS.get(), Triceratops.createAttributes().build());
        event.put(VENUS_CREEPER.get(), VenusCreeper.createAttributes().build());
        event.put(PTERANODON.get(), Pteranodon.createAttributes().build());
        event.put(TYRANNOSAURUS.get(), Tyrannosaurus.createAttributes().build());
        event.put(PLESIOSAUR.get(), Plesiosaur.createAttributes().build());
        event.put(MEGANEURA.get(), Meganeura.createAttributes().build());
        event.put(COMPSOGNATHUS.get(), Compsognathus.createAttributes().build());
        event.put(SPORE_MOTH.get(), SporeMoth.createAttributes().build());
        event.put(ANKYLOSAURUS.get(), Ankylosaurus.createAttributes().build());
        event.put(DEINOSUCHUS.get(), Deinosuchus.createAttributes().build());
    }

    /** On the ground, under the jungle canopy; Venus is dim, so light level does not matter. */
    private static void registerSpawnPlacements(RegisterSpawnPlacementsEvent event) {
        event.register(RAPTOR.get(), SpawnPlacementTypes.ON_GROUND, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
                ModDinosaurs::checkRaptorSpawn, RegisterSpawnPlacementsEvent.Operation.REPLACE);
        event.register(BRONTOSAURUS.get(), SpawnPlacementTypes.ON_GROUND, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
                (type, level, reason, pos, random) -> Mob.checkMobSpawnRules(type, level, reason, pos, random)
                        && awayFromPeople(level, reason, pos), RegisterSpawnPlacementsEvent.Operation.REPLACE);
        event.register(TRICERATOPS.get(), SpawnPlacementTypes.ON_GROUND, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
                (type, level, reason, pos, random) -> Mob.checkMobSpawnRules(type, level, reason, pos, random)
                        && awayFromPeople(level, reason, pos), RegisterSpawnPlacementsEvent.Operation.REPLACE);
        event.register(VENUS_CREEPER.get(), SpawnPlacementTypes.ON_GROUND, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
                (type, level, reason, pos, random) -> checkRareMonster(type, level, reason, pos, random, VenusCreeper.class,
                        CREEPER_CHANCE, CREEPERS_NEARBY_MAX, CREEPER_DENSITY_RANGE), RegisterSpawnPlacementsEvent.Operation.REPLACE);
        event.register(TYRANNOSAURUS.get(), SpawnPlacementTypes.ON_GROUND, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
                ModDinosaurs::checkTyrannosaurusSpawn,
                RegisterSpawnPlacementsEvent.Operation.REPLACE);
        // leaves count for MOTION_BLOCKING: chunk-generation spawns land right on top of the canopy
        event.register(PTERANODON.get(), SpawnPlacementTypes.NO_RESTRICTIONS, Heightmap.Types.MOTION_BLOCKING,
                ModDinosaurs::checkPteranodonSpawn, RegisterSpawnPlacementsEvent.Operation.REPLACE);
        // the sea monster wants open, deep water
        event.register(PLESIOSAUR.get(), SpawnPlacementTypes.IN_WATER, Heightmap.Types.OCEAN_FLOOR,
                (type, level, reason, pos, random) -> waterDepth(level, pos) >= PLESIO_MIN_DEPTH && awayFromPeople(level, reason, pos)
                        && (!natural(reason) || nearbyCount(level, pos, Plesiosaur.class, 64) < 3),
                RegisterSpawnPlacementsEvent.Operation.REPLACE);
        // the swamp crocodile only ever spawns in water, so it can't crowd the land with monsters
        event.register(DEINOSUCHUS.get(), SpawnPlacementTypes.IN_WATER, Heightmap.Types.OCEAN_FLOOR,
                (type, level, reason, pos, random) -> waterDepth(level, pos) >= 2 && awayFromPeople(level, reason, pos)
                        && (!natural(reason) || random.nextInt(CROC_CHANCE) == 0
                        && nearbyCount(level, pos, Deinosuchus.class, CROC_DENSITY_RANGE) < CROCS_NEARBY_MAX),
                RegisterSpawnPlacementsEvent.Operation.REPLACE);
        event.register(COMPSOGNATHUS.get(), SpawnPlacementTypes.ON_GROUND, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
                (type, level, reason, pos, random) -> Mob.checkMobSpawnRules(type, level, reason, pos, random)
                        && awayFromPeople(level, reason, pos), RegisterSpawnPlacementsEvent.Operation.REPLACE);
        event.register(ANKYLOSAURUS.get(), SpawnPlacementTypes.ON_GROUND, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
                (type, level, reason, pos, random) -> Mob.checkMobSpawnRules(type, level, reason, pos, random)
                        && awayFromPeople(level, reason, pos), RegisterSpawnPlacementsEvent.Operation.REPLACE);
        // small ambient life: anywhere open and not underground, any light level
        event.register(MEGANEURA.get(), SpawnPlacementTypes.ON_GROUND, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
                (type, level, reason, pos, random) -> ambientOk(level, reason, pos, 8), RegisterSpawnPlacementsEvent.Operation.REPLACE);
        event.register(SPORE_MOTH.get(), SpawnPlacementTypes.ON_GROUND, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
                (type, level, reason, pos, random) -> ambientOk(level, reason, pos, 10), RegisterSpawnPlacementsEvent.Operation.REPLACE);
    }

    private static final int PLESIO_MIN_DEPTH = 6;
    private static final int CROC_CHANCE = 6, CROCS_NEARBY_MAX = 2, CROC_DENSITY_RANGE = 48;

    private static boolean natural(EntitySpawnReason reason) {
        return reason == EntitySpawnReason.NATURAL || reason == EntitySpawnReason.CHUNK_GENERATION;
    }

    private static int nearbyCount(ServerLevelAccessor level, BlockPos pos, Class<? extends Entity> kind, int range) {
        return level.getEntitiesOfClass(kind, new AABB(pos).inflate(range)).size();
    }

    /** Depth of the water column at pos (0 if pos isn't water), counted up and down from pos. */
    private static int waterDepth(ServerLevelAccessor level, BlockPos pos) {
        if (!level.getFluidState(pos).is(FluidTags.WATER)) {
            return 0;
        }
        int depth = 1;
        BlockPos.MutableBlockPos p = pos.mutable();
        while (depth < 24 && level.getFluidState(p.move(0, -1, 0)).is(FluidTags.WATER)) {
            depth++;
        }
        p.set(pos);
        while (depth < 24 && level.getFluidState(p.move(0, 1, 0)).is(FluidTags.WATER)) {
            depth++;
        }
        return depth;
    }

    /** Ambient fliers: on the surface (open sky above), not too many of them about. */
    private static boolean ambientOk(ServerLevelAccessor level, EntitySpawnReason reason, BlockPos pos, int maxNearby) {
        if (!natural(reason)) {
            return true;
        }
        return level.canSeeSky(pos) && level.getFluidState(pos).isEmpty()
                && nearbyCount(level, pos, VenusFlier.class, 32) < maxNearby;
    }

    private static final int CREEPER_CHANCE = 6, CREEPERS_NEARBY_MAX = 2, CREEPER_DENSITY_RANGE = 56;
    /**
     * The tyrant is a once-in-an-expedition sight: long odds, never two in the same stretch of jungle, never near
     * people, and at most one natural spawn per level every quarter of an hour.
     */
    private static final int REX_CHANCE = 20, REX_DENSITY_RANGE = 160, REX_PEOPLE_RANGE = 96;
    private static final long REX_COOLDOWN = 20L * 60 * 15;
    private static final Map<ResourceKey<Level>, Long> LAST_REX_SPAWN = new ConcurrentHashMap<>();

    private static boolean checkTyrannosaurusSpawn(EntityType<Tyrannosaurus> type, ServerLevelAccessor level, EntitySpawnReason reason,
                                                   BlockPos pos, RandomSource random) {
        if (reason != EntitySpawnReason.NATURAL && reason != EntitySpawnReason.CHUNK_GENERATION) {
            return Monster.checkAnyLightMonsterSpawnRules(type, level, reason, pos, random);
        }
        ServerLevel server = level.getLevel();
        long now = server.getGameTime();
        Long last = LAST_REX_SPAWN.get(server.dimension());
        if (last == null || now < last) {
            LAST_REX_SPAWN.put(server.dimension(), now);  // the clock starts when the level is first visited
            return false;
        }
        if (now - last < REX_COOLDOWN) {
            return false;
        }
        if (!checkRareMonster(type, level, reason, pos, random, Tyrannosaurus.class, REX_CHANCE, 1, REX_DENSITY_RANGE)
                || !awayFromPeople(level, reason, pos, REX_PEOPLE_RANGE)) {
            return false;
        }
        LAST_REX_SPAWN.put(server.dimension(), now);
        return true;
    }
    private static final int PTERO_CHANCE = 3, PTEROS_NEARBY_MAX = 4, PTERO_DENSITY_RANGE = 48;

    private static <T extends Monster> boolean checkRareMonster(EntityType<T> type, ServerLevelAccessor level, EntitySpawnReason reason,
                                                              BlockPos pos, RandomSource random, Class<? extends Monster> kind,
                                                              int chance, int nearbyMax, int range) {
        if (!Monster.checkAnyLightMonsterSpawnRules(type, level, reason, pos, random) || !awayFromPeople(level, reason, pos)) {
            return false;
        }
        if (reason == EntitySpawnReason.NATURAL || reason == EntitySpawnReason.CHUNK_GENERATION) {
            if (random.nextInt(chance) != 0) {
                return false;
            }
            return level.getEntitiesOfClass(kind, new AABB(pos).inflate(range)).size() < nearbyMax;
        }
        return true;
    }

    /** Only on top of the canopy: leaves or logs below, open air here, high above the jungle floor. */
    private static boolean checkPteranodonSpawn(EntityType<Pteranodon> type, ServerLevelAccessor level, EntitySpawnReason reason,
                                                BlockPos pos, RandomSource random) {
        if (reason != EntitySpawnReason.NATURAL && reason != EntitySpawnReason.CHUNK_GENERATION) {
            return true;
        }
        if (!Pteranodon.isCanopy(level.getBlockState(pos.below())) || !level.getBlockState(pos).isAir()
                || !level.getBlockState(pos.above()).isAir() || !awayFromPeople(level, reason, pos)) {
            return false;
        }
        int floor = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, pos.getX(), pos.getZ());
        if (pos.getY() - floor < 6 && !level.getBlockState(pos.below()).is(net.minecraft.tags.BlockTags.LEAVES)) {
            return false;
        }
        if (random.nextInt(PTERO_CHANCE) != 0) {
            return false;
        }
        return level.getEntitiesOfClass(Pteranodon.class, new AABB(pos).inflate(PTERO_DENSITY_RANGE)).size() < PTEROS_NEARBY_MAX;
    }

    /** Raptor packs are the only monsters on Venus, so without limits they would fill the whole monster cap. */
    private static final int RAPTOR_CHANCE = 6, RAPTORS_NEARBY_MAX = 4, RAPTOR_DENSITY_RANGE = 48;

    private static boolean checkRaptorSpawn(EntityType<VenusRaptor> type, ServerLevelAccessor level, EntitySpawnReason reason,
                                            BlockPos pos, RandomSource random) {
        if (!Monster.checkAnyLightMonsterSpawnRules(type, level, reason, pos, random) || !awayFromPeople(level, reason, pos)) {
            return false;
        }
        if (reason == EntitySpawnReason.NATURAL) {
            if (random.nextInt(RAPTOR_CHANCE) != 0) {
                return false;
            }
            int nearby = level.getEntitiesOfClass(VenusRaptor.class, new AABB(pos).inflate(RAPTOR_DENSITY_RANGE)).size();
            return nearby < RAPTORS_NEARBY_MAX;
        }
        return true;
    }

    /** Natural spawns keep clear of the expedition camp and of anyone living on Venus (crew, tribes). */
    private static boolean awayFromPeople(ServerLevelAccessor level, EntitySpawnReason reason, BlockPos pos) {
        return awayFromPeople(level, reason, pos, 40);
    }

    private static boolean awayFromPeople(ServerLevelAccessor level, EntitySpawnReason reason, BlockPos pos, int range) {
        if (reason != EntitySpawnReason.NATURAL && reason != EntitySpawnReason.CHUNK_GENERATION) {
            return true;
        }
        BlockPos camp = VenusLanding.campPad(level.getLevel());
        int campRange = Math.max(56, range);
        if (camp != null && camp.distSqr(pos) < (double) campRange * campRange) {
            return false;
        }
        return level.getEntitiesOfClass(net.minecraft.world.entity.npc.villager.AbstractVillager.class, new AABB(pos).inflate(range)).isEmpty();
    }
}
