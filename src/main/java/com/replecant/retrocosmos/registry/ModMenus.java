package com.replecant.retrocosmos.registry;

import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.console.ConsoleMenu;
import com.replecant.retrocosmos.machine.MachineKind;
import com.replecant.retrocosmos.machine.ProcessingMenu;
import net.minecraft.core.registries.Registries;
import net.minecraft.world.inventory.MenuType;
import net.neoforged.neoforge.common.extensions.IMenuTypeExtension;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;

public final class ModMenus {
    public static final DeferredRegister<MenuType<?>> MENUS = DeferredRegister.create(Registries.MENU, RetroCosmos.MODID);

    public static final DeferredHolder<MenuType<?>, MenuType<ProcessingMenu>> FUEL_REFINERY = MENUS.register("fuel_refinery",
            () -> IMenuTypeExtension.create((id, inv, buf) -> new ProcessingMenu(ModMenus.FUEL_REFINERY.get(), id, inv, MachineKind.REFINERY)));
    public static final DeferredHolder<MenuType<?>, MenuType<ProcessingMenu>> AIR_LIQUEFIER = MENUS.register("air_liquefier",
            () -> IMenuTypeExtension.create((id, inv, buf) -> new ProcessingMenu(ModMenus.AIR_LIQUEFIER.get(), id, inv, MachineKind.LIQUEFIER)));
    public static final DeferredHolder<MenuType<?>, MenuType<ConsoleMenu>> MISSION_CONTROL_CONSOLE = MENUS.register("mission_control_console",
            () -> IMenuTypeExtension.create((id, inv, buf) -> new ConsoleMenu(ModMenus.MISSION_CONTROL_CONSOLE.get(), id, inv)));

    private ModMenus() {}
}
