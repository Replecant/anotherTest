package com.replecant.retrocosmos.tribe.client;

import net.minecraft.client.renderer.entity.state.LivingEntityRenderState;

/** What the tribesman model needs to know about the entity this frame. */
public class TribesmanRenderState extends LivingEntityRenderState {
    /** {@link com.replecant.retrocosmos.tribe.TribeRole} ordinal. */
    public int role;
    public int variant;
    /** Squatting by the fire 0..1. */
    public float sit;
    /** Dancing 0..1. */
    public float dance;
    /** Shaking the head "no" (refusing a trade, a child being shy). */
    public boolean unhappy;
    public boolean aggressive;
    /** Melee swing progress 0..1. */
    public float attackAnim;
}
