package com.replecant.retrocosmos.block;

import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockBehaviour;

/**
 * Red and white umbilical gantry lattice. A column of at least {@link #MIN_HEIGHT} tower blocks standing
 * right next to the 3x3 launch pad is required for the pre-flight check.
 */
public class ServiceTowerBlock extends Block {
    public static final int MIN_HEIGHT = 3;

    public ServiceTowerBlock(BlockBehaviour.Properties properties) {
        super(properties);
    }
}
