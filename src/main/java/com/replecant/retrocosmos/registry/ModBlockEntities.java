package com.replecant.retrocosmos.registry;

import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.console.ConsoleBlockEntity;
import com.replecant.retrocosmos.furniture.GalleyStoveBlockEntity;
import com.replecant.retrocosmos.furniture.StorageBlockEntity;
import com.replecant.retrocosmos.machine.MachineKind;
import com.replecant.retrocosmos.machine.ProcessingBlockEntity;
import java.util.Set;
import net.minecraft.core.registries.Registries;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;

public final class ModBlockEntities {
    public static final DeferredRegister<BlockEntityType<?>> TYPES = DeferredRegister.create(Registries.BLOCK_ENTITY_TYPE, RetroCosmos.MODID);

    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<ProcessingBlockEntity>> FUEL_REFINERY = TYPES.register("fuel_refinery",
            () -> new BlockEntityType<>((pos, state) -> new ProcessingBlockEntity(ModBlockEntities.FUEL_REFINERY.get(), pos, state, MachineKind.REFINERY),
                    Set.of(ModBlocks.FUEL_REFINERY.get())));
    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<ProcessingBlockEntity>> AIR_LIQUEFIER = TYPES.register("air_liquefier",
            () -> new BlockEntityType<>((pos, state) -> new ProcessingBlockEntity(ModBlockEntities.AIR_LIQUEFIER.get(), pos, state, MachineKind.LIQUEFIER),
                    Set.of(ModBlocks.AIR_LIQUEFIER.get())));
    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<ConsoleBlockEntity>> MISSION_CONTROL_CONSOLE = TYPES.register("mission_control_console",
            () -> new BlockEntityType<>(ConsoleBlockEntity::new, Set.of(ModBlocks.MISSION_CONTROL_CONSOLE.get())));

    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<StorageBlockEntity>> STORAGE = TYPES.register("storage",
            () -> new BlockEntityType<>(StorageBlockEntity::new, Set.of(ModFurniture.CREW_LOCKER.get(), ModFurniture.CARGO_CRATE.get(),
                    ModFurniture.SUPPLY_CABINET.get())));
    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<GalleyStoveBlockEntity>> GALLEY_STOVE = TYPES.register("galley_stove",
            () -> new BlockEntityType<>(GalleyStoveBlockEntity::new, Set.of(ModFurniture.GALLEY_STOVE.get())));

    private ModBlockEntities() {}
}
