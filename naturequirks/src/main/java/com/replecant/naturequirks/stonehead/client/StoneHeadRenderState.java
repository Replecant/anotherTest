package com.replecant.naturequirks.stonehead.client;

import net.minecraft.client.renderer.entity.state.LivingEntityRenderState;

public class StoneHeadRenderState extends LivingEntityRenderState {
    /** Ticks into the current chew, 0 when not chewing. */
    public float chew;
    /** Ticks left of a grumble (head shake), 0 when calm. */
    public float grumble;
}
