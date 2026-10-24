package com.replecant.retrocosmos.registry;

import com.mojang.serialization.Codec;
import com.replecant.retrocosmos.RetroCosmos;
import net.minecraft.core.component.DataComponentType;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.codec.ByteBufCodecs;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;

public final class ModDataComponents {
    public static final DeferredRegister<DataComponentType<?>> COMPONENTS = DeferredRegister.create(Registries.DATA_COMPONENT_TYPE, RetroCosmos.MODID);

    /** Oxygen left in a pressure suit's backpack tank, in ticks. Absent means a factory-fresh, full tank. */
    public static final DeferredHolder<DataComponentType<?>, DataComponentType<Integer>> OXYGEN = COMPONENTS.register("oxygen",
            () -> DataComponentType.<Integer>builder().persistent(Codec.INT).networkSynchronized(ByteBufCodecs.VAR_INT).build());

    private ModDataComponents() {}
}
