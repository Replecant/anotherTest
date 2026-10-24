package com.replecant.retrocosmos.registry;

import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.oxygen.OxygenCanisterItem;
import com.replecant.retrocosmos.oxygen.SpaceSuitItem;
import java.util.Map;
import java.util.function.Function;
import java.util.function.UnaryOperator;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.TagKey;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.equipment.ArmorMaterial;
import net.minecraft.world.item.equipment.ArmorType;
import net.minecraft.world.item.equipment.EquipmentAsset;
import net.minecraft.world.item.equipment.EquipmentAssets;
import net.minecraft.world.level.block.Block;
import net.neoforged.neoforge.registries.DeferredBlock;
import net.neoforged.neoforge.registries.DeferredItem;
import net.neoforged.neoforge.registries.DeferredRegister;

public final class ModItems {
    public static final DeferredRegister.Items ITEMS = DeferredRegister.createItems(RetroCosmos.MODID);

    // --- Space suit material ---
    public static final TagKey<Item> REPAIRS_SPACE_SUIT = TagKey.create(Registries.ITEM,
            Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "repairs_space_suit"));
    public static final ResourceKey<EquipmentAsset> SPACE_SUIT_ASSET = ResourceKey.create(EquipmentAssets.ROOT_ID,
            Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "space_suit"));
    public static final ArmorMaterial SPACE_SUIT_MATERIAL = new ArmorMaterial(
            28,
            Map.of(ArmorType.BOOTS, 2, ArmorType.LEGGINGS, 5, ArmorType.CHESTPLATE, 6, ArmorType.HELMET, 2, ArmorType.BODY, 5),
            12,
            SoundEvents.ARMOR_EQUIP_IRON,
            1.0F,
            0.05F,
            REPAIRS_SPACE_SUIT,
            SPACE_SUIT_ASSET);

    // --- Raw resources ---
    public static final DeferredItem<Item> RAW_ALUMINUM = simple("raw_aluminum");
    public static final DeferredItem<Item> RAW_TITANIUM = simple("raw_titanium");
    public static final DeferredItem<Item> ALUMINUM_INGOT = simple("aluminum_ingot");
    public static final DeferredItem<Item> TITANIUM_INGOT = simple("titanium_ingot");
    public static final DeferredItem<Item> ALUMINUM_PLATE = simple("aluminum_plate");
    public static final DeferredItem<Item> TITANIUM_PLATE = simple("titanium_plate");
    public static final DeferredItem<Item> AERO_ALLOY_BLEND = simple("aero_alloy_blend");
    public static final DeferredItem<Item> AERO_ALLOY_INGOT = simple("aero_alloy_ingot");
    public static final DeferredItem<Item> AERO_ALLOY_PLATE = simple("aero_alloy_plate");

    // --- Retro electronics ---
    public static final DeferredItem<Item> VACUUM_TUBE = simple("vacuum_tube");
    public static final DeferredItem<Item> WIRING_HARNESS = simple("wiring_harness");
    public static final DeferredItem<Item> GUIDANCE_COMPUTER = register("guidance_computer", Item::new, p -> p.rarity(Rarity.UNCOMMON));

    // --- Rocket parts ---
    public static final DeferredItem<Item> NOSE_CONE = simple("nose_cone");
    public static final DeferredItem<Item> HULL_SEGMENT = simple("hull_segment");
    public static final DeferredItem<Item> ROCKET_FIN = simple("rocket_fin");
    public static final DeferredItem<Item> HEAT_SHIELD = simple("heat_shield");
    public static final DeferredItem<Item> FUEL_TANK = simple("fuel_tank");
    public static final DeferredItem<Item> COMBUSTION_CHAMBER = simple("combustion_chamber");
    public static final DeferredItem<Item> ENGINE_NOZZLE = simple("engine_nozzle");
    public static final DeferredItem<Item> TURBOPUMP = simple("turbopump");
    public static final DeferredItem<Item> ROCKET_ENGINE = register("rocket_engine", Item::new, p -> p.rarity(Rarity.UNCOMMON));
    public static final DeferredItem<Item> AIRFRAME = register("airframe", Item::new, p -> p.rarity(Rarity.UNCOMMON).stacksTo(1));
    public static final DeferredItem<Item> EMPTY_FUEL_CANISTER = simple("empty_fuel_canister");
    public static final DeferredItem<Item> ROCKET_FUEL_CANISTER = register("rocket_fuel_canister", Item::new, p -> p.stacksTo(16));
    public static final DeferredItem<Item> LIQUID_OXYGEN_CANISTER = register("liquid_oxygen_canister", OxygenCanisterItem::new, p -> p.stacksTo(16));

    // --- Space suit ---
    public static final DeferredItem<Item> SPACE_HELMET = register("space_helmet", Item::new,
            p -> p.humanoidArmor(SPACE_SUIT_MATERIAL, ArmorType.HELMET));
    public static final DeferredItem<Item> SPACE_SUIT = register("space_suit", SpaceSuitItem::new,
            p -> p.humanoidArmor(SPACE_SUIT_MATERIAL, ArmorType.CHESTPLATE));
    public static final DeferredItem<Item> SPACE_LEGGINGS = register("space_leggings", Item::new,
            p -> p.humanoidArmor(SPACE_SUIT_MATERIAL, ArmorType.LEGGINGS));
    public static final DeferredItem<Item> SPACE_BOOTS = register("space_boots", Item::new,
            p -> p.humanoidArmor(SPACE_SUIT_MATERIAL, ArmorType.BOOTS));

    // --- Block items ---
    public static final DeferredItem<BlockItem> BAUXITE_ORE = block(ModBlocks.BAUXITE_ORE, UnaryOperator.identity());
    public static final DeferredItem<BlockItem> DEEPSLATE_BAUXITE_ORE = block(ModBlocks.DEEPSLATE_BAUXITE_ORE, UnaryOperator.identity());
    public static final DeferredItem<BlockItem> TITANIUM_ORE = block(ModBlocks.TITANIUM_ORE, UnaryOperator.identity());
    public static final DeferredItem<BlockItem> DEEPSLATE_TITANIUM_ORE = block(ModBlocks.DEEPSLATE_TITANIUM_ORE, UnaryOperator.identity());
    public static final DeferredItem<BlockItem> ALUMINUM_BLOCK = block(ModBlocks.ALUMINUM_BLOCK, UnaryOperator.identity());
    public static final DeferredItem<BlockItem> TITANIUM_BLOCK = block(ModBlocks.TITANIUM_BLOCK, UnaryOperator.identity());
    public static final DeferredItem<BlockItem> OIL_SHALE = block(ModBlocks.OIL_SHALE, UnaryOperator.identity());
    public static final DeferredItem<BlockItem> LAUNCH_PAD = block(ModBlocks.LAUNCH_PAD, UnaryOperator.identity());
    public static final DeferredItem<BlockItem> SERVICE_TOWER = block(ModBlocks.SERVICE_TOWER, UnaryOperator.identity());
    public static final DeferredItem<BlockItem> FUEL_REFINERY = block(ModBlocks.FUEL_REFINERY, UnaryOperator.identity());
    public static final DeferredItem<BlockItem> AIR_LIQUEFIER = block(ModBlocks.AIR_LIQUEFIER, UnaryOperator.identity());
    public static final DeferredItem<BlockItem> MISSION_CONTROL_CONSOLE = block(ModBlocks.MISSION_CONTROL_CONSOLE, p -> p.rarity(Rarity.UNCOMMON));
    public static final DeferredItem<BlockItem> ROCKET = block(ModBlocks.ROCKET, p -> p.stacksTo(1).rarity(Rarity.RARE));

    private static DeferredItem<Item> simple(String name) {
        return register(name, Item::new, UnaryOperator.identity());
    }

    private static <I extends Item> DeferredItem<I> register(String name, Function<Item.Properties, I> factory,
                                                            UnaryOperator<Item.Properties> props) {
        return ITEMS.register(name, id -> factory.apply(props.apply(
                new Item.Properties().setId(ResourceKey.create(Registries.ITEM, id)))));
    }

    private static DeferredItem<BlockItem> block(DeferredBlock<? extends Block> block, UnaryOperator<Item.Properties> props) {
        return register(block.getId().getPath(), p -> new BlockItem(block.get(), p), p -> props.apply(p.useBlockDescriptionPrefix()));
    }

    private ModItems() {}
}
