package com.replecant.naturequirks.flowercreeper.client;

import net.minecraft.client.renderer.entity.state.LivingEntityRenderState;

public class FlowerCreeperRenderState extends LivingEntityRenderState {
    /** The fuse, 0 -> 1 (as CreeperRenderState.swelling). */
    public float swelling;
    /** Which flowers grow on this one (from its UUID, so it never changes). */
    public long flowerSeed;
}
