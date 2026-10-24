package com.replecant.retrocosmos.block;

import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockBehaviour;

/** A reinforced steel platform with hazard stripes. Rockets must stand on one to pass the pre-flight check. */
public class LaunchPadBlock extends Block {
    public LaunchPadBlock(BlockBehaviour.Properties properties) {
        super(properties);
    }
}
