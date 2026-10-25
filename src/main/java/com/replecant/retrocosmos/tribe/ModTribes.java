package com.replecant.retrocosmos.tribe;

import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.registry.ModEntities;
import com.replecant.retrocosmos.registry.ModItems;
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
import net.neoforged.bus.api.IEventBus;
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

    private ModTribes() {}

    /** Called from the mod constructor before the deferred registers are attached. */
    public static void init(IEventBus modEventBus) {
        modEventBus.addListener(ModTribes::createAttributes);
        modEventBus.addListener(ModTribes::addToVanillaTabs);
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
        } else if (event.getTabKey() == CreativeModeTabs.COMBAT) {
            event.accept(BONE_SPEAR.get());
        }
    }

    private static void createAttributes(EntityAttributeCreationEvent event) {
        event.put(TRIBESMAN.get(), Tribesman.createAttributes().build());
    }
}
