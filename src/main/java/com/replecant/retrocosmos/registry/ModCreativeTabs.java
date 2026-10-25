package com.replecant.retrocosmos.registry;

import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.dinosaur.ModDinosaurs;
import com.replecant.retrocosmos.venus.ModVenus;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.ItemStack;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredItem;
import net.neoforged.neoforge.registries.DeferredRegister;

public final class ModCreativeTabs {
    public static final DeferredRegister<CreativeModeTab> TABS = DeferredRegister.create(Registries.CREATIVE_MODE_TAB, RetroCosmos.MODID);

    public static final DeferredHolder<CreativeModeTab, CreativeModeTab> MAIN = TABS.register("main", () -> CreativeModeTab.builder()
            .title(Component.translatable("itemGroup.retrocosmos.main"))
            .icon(() -> new ItemStack(ModItems.ROCKET.get()))
            .displayItems((params, output) -> {
                for (DeferredItem<?> item : new DeferredItem<?>[] {
                        ModItems.BAUXITE_ORE, ModItems.DEEPSLATE_BAUXITE_ORE, ModItems.TITANIUM_ORE, ModItems.DEEPSLATE_TITANIUM_ORE,
                        ModItems.OIL_SHALE,
                        ModItems.RAW_ALUMINUM, ModItems.RAW_TITANIUM, ModItems.ALUMINUM_INGOT, ModItems.TITANIUM_INGOT,
                        ModItems.ALUMINUM_PLATE, ModItems.TITANIUM_PLATE, ModItems.ALUMINUM_BLOCK, ModItems.TITANIUM_BLOCK,
                        ModItems.AERO_ALLOY_BLEND, ModItems.AERO_ALLOY_INGOT, ModItems.AERO_ALLOY_PLATE,
                        ModItems.VACUUM_TUBE, ModItems.WIRING_HARNESS, ModItems.GUIDANCE_COMPUTER,
                        ModItems.HEAT_SHIELD, ModItems.NOSE_CONE, ModItems.HULL_SEGMENT, ModItems.FUEL_TANK, ModItems.ROCKET_FIN,
                        ModItems.COMBUSTION_CHAMBER, ModItems.ENGINE_NOZZLE, ModItems.TURBOPUMP, ModItems.ROCKET_ENGINE,
                        ModItems.AIRFRAME,
                        ModItems.EMPTY_FUEL_CANISTER, ModItems.ROCKET_FUEL_CANISTER, ModItems.LIQUID_OXYGEN_CANISTER,
                        ModItems.FUEL_REFINERY, ModItems.AIR_LIQUEFIER,
                        ModItems.SPACE_HELMET, ModItems.SPACE_SUIT, ModItems.SPACE_LEGGINGS, ModItems.SPACE_BOOTS,
                        ModItems.LAUNCH_PAD, ModItems.SERVICE_TOWER, ModItems.MISSION_CONTROL_CONSOLE, ModItems.ROCKET}) {
                    output.accept(item.get());
                }
            })
            .build());

    public static final DeferredHolder<CreativeModeTab, CreativeModeTab> HOME = TABS.register("home", () -> CreativeModeTab.builder()
            .title(Component.translatable("itemGroup.retrocosmos.home"))
            .icon(() -> new ItemStack(ModFurniture.ATOMIC_TV.get()))
            .withTabsBefore(MAIN.getKey())
            .displayItems((params, output) -> ModFurniture.items().forEach(item -> output.accept(item.get())))
            .build());

    public static final DeferredHolder<CreativeModeTab, CreativeModeTab> STATION = TABS.register("station", () -> CreativeModeTab.builder()
            .title(Component.translatable("itemGroup.retrocosmos.station"))
            .icon(() -> new ItemStack(ModFurniture.CONTROL_PANEL.get()))
            .withTabsBefore(HOME.getKey())
            .displayItems((params, output) -> ModFurniture.stationItems().forEach(item -> output.accept(item.get())))
            .build());

    public static final DeferredHolder<CreativeModeTab, CreativeModeTab> VENUS = TABS.register("venus", () -> CreativeModeTab.builder()
            .title(Component.translatable("itemGroup.retrocosmos.venus"))
            .icon(() -> new ItemStack(ModItems.ROCKET.get()))
            .withTabsBefore(STATION.getKey())
            .displayItems((params, output) -> {
                ModVenus.items().forEach(item -> output.accept(item.get()));
                ModDinosaurs.items().forEach(item -> output.accept(item.get()));
            })
            .build());

    private ModCreativeTabs() {}
}
