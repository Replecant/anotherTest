package com.replecant.retrocosmos.registry;

import com.replecant.retrocosmos.RetroCosmos;
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
                        ModItems.RAW_ALUMINUM, ModItems.RAW_TITANIUM, ModItems.ALUMINUM_INGOT, ModItems.TITANIUM_INGOT,
                        ModItems.ALUMINUM_PLATE, ModItems.TITANIUM_PLATE, ModItems.ALUMINUM_BLOCK, ModItems.TITANIUM_BLOCK,
                        ModItems.VACUUM_TUBE, ModItems.GUIDANCE_COMPUTER,
                        ModItems.NOSE_CONE, ModItems.HULL_SEGMENT, ModItems.ROCKET_FIN, ModItems.ROCKET_ENGINE,
                        ModItems.EMPTY_FUEL_CANISTER, ModItems.ROCKET_FUEL_CANISTER,
                        ModItems.SPACE_HELMET, ModItems.SPACE_SUIT, ModItems.SPACE_LEGGINGS, ModItems.SPACE_BOOTS,
                        ModItems.LAUNCH_PAD, ModItems.ROCKET}) {
                    output.accept(item.get());
                }
            })
            .build());

    private ModCreativeTabs() {}
}
