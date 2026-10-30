package com.replecant.retrocosmos.tribe.boss.client;

import net.minecraft.client.renderer.entity.state.LivingEntityRenderState;

/** Render state of Dr. Oinstein's three shapes; each model reads its own channels. */
public class BossRenderState extends LivingEntityRenderState {
    public float attackAnim;
    public boolean aggressive;
    /** Strider: cannons charging 0..1, stomp leg raised 0..1, stomp impact 0..1, falling apart 0..1. */
    public float charge;
    public float raise;
    public float impact;
    public float wreck;
    /** Doctor: lying after the fall 0..1, syringe at his neck 0..1, the shout 0..1, serum convulsions 0..1. */
    public float fallen;
    public float inject;
    public float shout;
    public float shake;
    public boolean syringe;
    /** Homo Novus: action poses 0..1, raging. */
    public float crouch;
    public float leap;
    public float slam;
    public float grab;
    public float scream;
    public boolean rage;
}
