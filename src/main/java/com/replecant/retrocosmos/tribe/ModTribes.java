package com.replecant.retrocosmos.tribe;

import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.oinstein.OinsteinBossAnchorBlock;
import com.replecant.retrocosmos.oinstein.OinsteinBossAnchorBlockEntity;
import com.replecant.retrocosmos.registry.ModBlocks;
import com.replecant.retrocosmos.registry.ModEntities;
import com.replecant.retrocosmos.registry.ModItems;
import com.replecant.retrocosmos.tribe.boss.DrOinstein;
import com.replecant.retrocosmos.tribe.boss.HomoNovus;
import com.replecant.retrocosmos.tribe.boss.OinsteinStrider;
import java.util.Set;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.PushReaction;
import net.neoforged.neoforge.registries.DeferredBlock;
import net.neoforged.neoforge.registries.DeferredRegister;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.function.Function;
import java.util.function.UnaryOperator;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.BlockTags;
import net.minecraft.tags.TagKey;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.food.FoodProperties;
import net.minecraft.world.item.CreativeModeTabs;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.SpawnEggItem;
import net.minecraft.world.item.ToolMaterial;
import net.minecraft.world.item.component.Consumables;
import net.minecraft.world.item.consume_effects.ApplyStatusEffectsConsumeEffect;
import net.minecraft.world.item.equipment.EquipmentAsset;
import net.minecraft.world.item.equipment.EquipmentAssets;
import net.minecraft.world.item.equipment.Equippable;
import com.replecant.retrocosmos.tribe.mutant.BlasterBolt;
import com.replecant.retrocosmos.tribe.mutant.HominidNovus;
import com.replecant.retrocosmos.tribe.mutant.HominusSapiens;
import com.replecant.retrocosmos.tribe.mutant.RayBlasterItem;
import net.minecraft.world.entity.SpawnPlacementTypes;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.level.levelgen.Heightmap;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.event.entity.RegisterSpawnPlacementsEvent;
import net.neoforged.neoforge.event.BuildCreativeModeTabContentsEvent;
import net.neoforged.neoforge.event.entity.EntityAttributeCreationEvent;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredItem;

/** The primitive hominid tribes of Venus: entities, trades, items and camps. */
public final class ModTribes {
    private static final List<DeferredItem<? extends Item>> ITEMS = new ArrayList<>();

    /** A Venus tribesman (hunter, gatherer, shaman or chief - see {@link TribeRole}). */
    public static final DeferredHolder<EntityType<?>, EntityType<Tribesman>> TRIBESMAN = ModEntities.ENTITIES.register("tribesman",
            id -> EntityType.Builder.of(Tribesman::new, MobCategory.MISC)
                    .sized(0.7F, 1.8F)
                    .eyeHeight(1.5F)
                    .clientTrackingRange(10)
                    .build(ResourceKey.create(Registries.ENTITY_TYPE, id)));

    /** A hunter's thrown spear. */
    public static final DeferredHolder<EntityType<?>, EntityType<ThrownSpear>> THROWN_SPEAR = ModEntities.ENTITIES.register("thrown_spear",
            id -> EntityType.Builder.<ThrownSpear>of(ThrownSpear::new, MobCategory.MISC)
                    .sized(0.3F, 0.3F)
                    .noSummon()
                    .clientTrackingRange(6)
                    .updateInterval(10)
                    .build(ResourceKey.create(Registries.ENTITY_TYPE, id)));

    // ---- Dr. Oinstein's mutant hominids (faction tag: OinsteinForces.TAG = #retrocosmos:oinstein_forces) ----
    /** Hominid Novus: the 2.6-block brute in the control collar. */
    public static final DeferredHolder<EntityType<?>, EntityType<HominidNovus>> HOMINID_NOVUS = ModEntities.ENTITIES.register("hominid_novus",
            id -> EntityType.Builder.of(HominidNovus::new, MobCategory.MONSTER)
                    .sized(1.4F, 2.6F)
                    .eyeHeight(2.0F)
                    .clientTrackingRange(10)
                    .build(ResourceKey.create(Registries.ENTITY_TYPE, id)));
    /** Hominus Sapiens: the brain under glass with the ray pistol. */
    public static final DeferredHolder<EntityType<?>, EntityType<HominusSapiens>> HOMINUS_SAPIENS = ModEntities.ENTITIES.register("hominus_sapiens",
            id -> EntityType.Builder.of(HominusSapiens::new, MobCategory.MONSTER)
                    .sized(0.6F, 1.8F)
                    .eyeHeight(1.45F)
                    .clientTrackingRange(10)
                    .build(ResourceKey.create(Registries.ENTITY_TYPE, id)));
    /** The glowing ray-gun bolt (fired by the Sapiens and by the player's ray blaster). */
    public static final DeferredHolder<EntityType<?>, EntityType<BlasterBolt>> BLASTER_BOLT = ModEntities.ENTITIES.register("blaster_bolt",
            id -> EntityType.Builder.<BlasterBolt>of(BlasterBolt::new, MobCategory.MISC)
                    .sized(0.25F, 0.25F)
                    .noSummon()
                    .clientTrackingRange(8)
                    .updateInterval(2)
                    .build(ResourceKey.create(Registries.ENTITY_TYPE, id)));

    // ---- Dr. Oinstein himself, the Venus boss (not in #oinstein_forces; his summons are) ----
    /** Phase one: the Atomic Strider walker with the doctor in the cockpit. */
    public static final DeferredHolder<EntityType<?>, EntityType<OinsteinStrider>> OINSTEIN_STRIDER = ModEntities.ENTITIES.register("oinstein_strider",
            id -> EntityType.Builder.of(OinsteinStrider::new, MobCategory.MONSTER)
                    .sized(2.2F, 4.4F)
                    .eyeHeight(3.6F)
                    .clientTrackingRange(12)
                    .build(ResourceKey.create(Registries.ENTITY_TYPE, id)));
    /** The transition: the doctor on foot, thrown out of the wreck, injecting the serum (scripted, invulnerable). */
    public static final DeferredHolder<EntityType<?>, EntityType<DrOinstein>> DR_OINSTEIN = ModEntities.ENTITIES.register("dr_oinstein",
            id -> EntityType.Builder.of(DrOinstein::new, MobCategory.MONSTER)
                    .sized(0.6F, 1.95F)
                    .eyeHeight(1.62F)
                    .clientTrackingRange(12)
                    .build(ResourceKey.create(Registries.ENTITY_TYPE, id)));
    /** Phase two: Homo Novus. */
    public static final DeferredHolder<EntityType<?>, EntityType<HomoNovus>> HOMO_NOVUS = ModEntities.ENTITIES.register("homo_novus",
            id -> EntityType.Builder.of(HomoNovus::new, MobCategory.MONSTER)
                    .sized(1.3F, 3.1F)
                    .eyeHeight(2.6F)
                    .clientTrackingRange(12)
                    .build(ResourceKey.create(Registries.ENTITY_TYPE, id)));

    public static final DeferredRegister<BlockEntityType<?>> BLOCK_ENTITIES =
            DeferredRegister.create(Registries.BLOCK_ENTITY_TYPE, RetroCosmos.MODID);
    /** The arena marker that brings the boss out (see {@link OinsteinBossAnchorBlockEntity}). */
    public static final DeferredBlock<OinsteinBossAnchorBlock> OINSTEIN_BOSS_ANCHOR = ModBlocks.BLOCKS.register("oinstein_boss_anchor",
            id -> new OinsteinBossAnchorBlock(BlockBehaviour.Properties.of().setId(ResourceKey.create(Registries.BLOCK, id))
                    .strength(-1.0F, 3600000.0F).noLootTable().noCollision().noOcclusion().pushReaction(PushReaction.BLOCK)
                    .sound(SoundType.METAL).isValidSpawn((state, level, pos, type) -> false)));
    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<OinsteinBossAnchorBlockEntity>> OINSTEIN_BOSS_ANCHOR_BE =
            BLOCK_ENTITIES.register("oinstein_boss_anchor",
                    () -> new BlockEntityType<>(OinsteinBossAnchorBlockEntity::new, Set.of(OINSTEIN_BOSS_ANCHOR.get())));

    public static final TagKey<Item> REPAIRS_BONE_SPEAR = TagKey.create(Registries.ITEM,
            Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "repairs_bone_spear"));
    /** Bone & flint: about as good as stone, a little tougher. */
    public static final ToolMaterial BONE = new ToolMaterial(BlockTags.INCORRECT_FOR_STONE_TOOL, 190, 4.0F, 1.0F, 12, REPAIRS_BONE_SPEAR);
    public static final ResourceKey<EquipmentAsset> TRIBAL_MASK_ASSET = ResourceKey.create(EquipmentAssets.ROOT_ID,
            Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "tribal_mask"));

    // ---- Venus trade goods ----
    public static final DeferredItem<Item> VENUS_AMBER = item("venus_amber", Item::new, p -> p.rarity(Rarity.UNCOMMON));
    public static final DeferredItem<Item> RAPTOR_TOOTH = item("raptor_tooth", Item::new, UnaryOperator.identity());
    public static final DeferredItem<Item> FERN_FIBER = item("fern_fiber", Item::new, UnaryOperator.identity());
    public static final DeferredItem<Item> DINO_HIDE = item("dino_hide", Item::new, UnaryOperator.identity());
    public static final DeferredItem<Item> GLOWCAP_TEA = item("glowcap_tea", Item::new, p -> p.stacksTo(16)
            .usingConvertsTo(Items.BOWL)
            .food(new FoodProperties.Builder().nutrition(4).saturationModifier(0.6F).alwaysEdible().build(),
                    Consumables.defaultDrink().onConsume(new ApplyStatusEffectsConsumeEffect(List.of(
                            new MobEffectInstance(MobEffects.NIGHT_VISION, 20 * 90),
                            new MobEffectInstance(MobEffects.REGENERATION, 20 * 5)))).build()));
    public static final DeferredItem<Item> BONE_SPEAR = item("bone_spear", Item::new,
            p -> p.spear(BONE, 0.75F, 0.82F, 0.7F, 4.5F, 10.0F, 9.0F, 5.1F, 13.75F, 4.6F));
    /** A painted wooden spirit mask, worn on the head. Tribesfolk give a wearer better prices. */
    public static final DeferredItem<Item> TRIBAL_MASK = item("tribal_mask", Item::new, p -> p.stacksTo(1).rarity(Rarity.UNCOMMON)
            .component(DataComponents.EQUIPPABLE, Equippable.builder(EquipmentSlot.HEAD)
                    .setEquipSound(SoundEvents.ARMOR_EQUIP_LEATHER)
                    .setAsset(TRIBAL_MASK_ASSET)
                    .setDamageOnHurt(false)
                    .build()));
    public static final DeferredItem<ShamanCharmItem> SHAMAN_CHARM = item("shaman_charm", ShamanCharmItem::new,
            p -> p.stacksTo(16).rarity(Rarity.UNCOMMON).component(DataComponents.ENCHANTMENT_GLINT_OVERRIDE, true));

    public static final DeferredItem<SpawnEggItem> TRIBESMAN_SPAWN_EGG = item("tribesman_spawn_egg", SpawnEggItem::new,
            p -> p.spawnEgg(TRIBESMAN.get()));

    // ---- Oinstein loot ----
    /** The steel collar off a Hominid Novus - a curio for Dr. Cooper. */
    public static final DeferredItem<Item> CONTROL_COLLAR = item("control_collar", Item::new, p -> p.stacksTo(16).rarity(Rarity.UNCOMMON));
    /** A Hominus Sapiens' brain dome, brain and all - a curio for Dr. Cooper. */
    public static final DeferredItem<Item> BRAIN_FLASK = item("brain_flask", Item::new, p -> p.stacksTo(16).rarity(Rarity.RARE));
    /** The Sapiens' ray pistol: fires blaster bolts, 120 shots, repaired with redstone. */
    public static final DeferredItem<RayBlasterItem> RAY_BLASTER = item("ray_blaster", RayBlasterItem::new,
            p -> p.durability(120).repairable(Items.REDSTONE).rarity(Rarity.RARE));
    public static final DeferredItem<SpawnEggItem> HOMINID_NOVUS_SPAWN_EGG = item("hominid_novus_spawn_egg", SpawnEggItem::new,
            p -> p.spawnEgg(HOMINID_NOVUS.get()));
    public static final DeferredItem<SpawnEggItem> HOMINUS_SAPIENS_SPAWN_EGG = item("hominus_sapiens_spawn_egg", SpawnEggItem::new,
            p -> p.spawnEgg(HOMINUS_SAPIENS.get()));

    // ---- the boss ----
    public static final DeferredItem<SpawnEggItem> OINSTEIN_STRIDER_SPAWN_EGG = item("oinstein_strider_spawn_egg", SpawnEggItem::new,
            p -> p.spawnEgg(OINSTEIN_STRIDER.get()));
    public static final DeferredItem<SpawnEggItem> HOMO_NOVUS_SPAWN_EGG = item("homo_novus_spawn_egg", SpawnEggItem::new,
            p -> p.spawnEgg(HOMO_NOVUS.get()));
    public static final DeferredItem<BlockItem> OINSTEIN_BOSS_ANCHOR_ITEM = item("oinstein_boss_anchor",
            p -> new BlockItem(OINSTEIN_BOSS_ANCHOR.get(), p), p -> p.useBlockDescriptionPrefix().rarity(Rarity.EPIC));

    private ModTribes() {}

    /** Called from the mod constructor before the deferred registers are attached. */
    public static void init(IEventBus modEventBus) {
        BLOCK_ENTITIES.register(modEventBus);
        modEventBus.addListener(ModTribes::createAttributes);
        modEventBus.addListener(ModTribes::addToVanillaTabs);
        modEventBus.addListener(ModTribes::registerSpawnPlacements);
    }

    /** Items for the Venus creative tab, in order. */
    public static List<DeferredItem<? extends Item>> items() {
        return Collections.unmodifiableList(ITEMS);
    }

    private static <I extends Item> DeferredItem<I> item(String name, Function<Item.Properties, I> factory,
                                                        UnaryOperator<Item.Properties> props) {
        DeferredItem<I> item = ModItems.ITEMS.register(name, id -> factory.apply(props.apply(
                new Item.Properties().setId(ResourceKey.create(Registries.ITEM, id)))));
        ITEMS.add(item);
        return item;
    }

    private static void addToVanillaTabs(BuildCreativeModeTabContentsEvent event) {
        if (event.getTabKey() == CreativeModeTabs.SPAWN_EGGS) {
            event.accept(TRIBESMAN_SPAWN_EGG.get());
            event.accept(HOMINID_NOVUS_SPAWN_EGG.get());
            event.accept(HOMINUS_SAPIENS_SPAWN_EGG.get());
            event.accept(OINSTEIN_STRIDER_SPAWN_EGG.get());
            event.accept(HOMO_NOVUS_SPAWN_EGG.get());
        } else if (event.getTabKey() == CreativeModeTabs.COMBAT) {
            event.accept(BONE_SPEAR.get());
            event.accept(RAY_BLASTER.get());
        }
    }

    private static void createAttributes(EntityAttributeCreationEvent event) {
        event.put(TRIBESMAN.get(), Tribesman.createAttributes().build());
        event.put(HOMINID_NOVUS.get(), HominidNovus.createAttributes().build());
        event.put(HOMINUS_SAPIENS.get(), HominusSapiens.createAttributes().build());
        event.put(OINSTEIN_STRIDER.get(), OinsteinStrider.createAttributes().build());
        event.put(DR_OINSTEIN.get(), DrOinstein.createAttributes().build());
        event.put(HOMO_NOVUS.get(), HomoNovus.createAttributes().build());
    }

    /** No natural biome spawns; these rules apply to the outposts' structure spawn overrides. Labs are lit, so any light. */
    private static void registerSpawnPlacements(RegisterSpawnPlacementsEvent event) {
        event.register(HOMINID_NOVUS.get(), SpawnPlacementTypes.ON_GROUND, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
                com.replecant.retrocosmos.oinstein.OinsteinSpawns::check, RegisterSpawnPlacementsEvent.Operation.REPLACE);
        event.register(HOMINUS_SAPIENS.get(), SpawnPlacementTypes.ON_GROUND, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
                com.replecant.retrocosmos.oinstein.OinsteinSpawns::check, RegisterSpawnPlacementsEvent.Operation.REPLACE);
    }
}
