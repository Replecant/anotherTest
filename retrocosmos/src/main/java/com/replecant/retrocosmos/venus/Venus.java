package com.replecant.retrocosmos.venus;

import com.replecant.retrocosmos.RetroCosmos;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.level.Level;

/** Venus: a steaming jungle world under eternal amber clouds, roamed by dinosaurs (1950s pulp style). */
public final class Venus {
    public static final ResourceKey<Level> DIMENSION = ResourceKey.create(Registries.DIMENSION,
            Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "venus"));

    private Venus() {}

    public static boolean isVenus(Level level) {
        return level.dimension() == DIMENSION;
    }
}
