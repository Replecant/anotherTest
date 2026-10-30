package com.replecant.naturequirks.registry;

import com.replecant.naturequirks.NatureQuirks;
import java.util.ArrayList;
import java.util.List;
import java.util.function.Supplier;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.ItemLike;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;

/** The mod's creative tab. Features add their items with {@link #add} while they register. */
public final class ModTab {
    public static final DeferredRegister<CreativeModeTab> TABS = DeferredRegister.create(Registries.CREATIVE_MODE_TAB, NatureQuirks.MODID);
    private static final List<Supplier<? extends ItemLike>> ENTRIES = new ArrayList<>();
    /** Item shown on the tab; a feature may replace it during init. */
    public static Supplier<? extends ItemLike> icon = () -> Items.HONEYCOMB;

    public static final DeferredHolder<CreativeModeTab, CreativeModeTab> MAIN = TABS.register("main", () -> CreativeModeTab.builder()
            .title(Component.translatable("itemGroup." + NatureQuirks.MODID))
            .icon(() -> new ItemStack(icon.get()))
            .displayItems((params, output) -> ENTRIES.forEach(e -> output.accept(e.get())))
            .build());

    private ModTab() {}

    public static void add(Supplier<? extends ItemLike> item) {
        ENTRIES.add(item);
    }
}
