package com.replecant.retrocosmos.tribe.client;

import net.minecraft.client.renderer.entity.state.LivingEntityRenderState;

/** Render state of Dr. Oinstein's mutants; each model reads the channels it needs. */
public class MutantRenderState extends LivingEntityRenderState {
    public float attackAnim;
    public boolean aggressive;
    /** Novus: rearing up for a slam 0..1, the slam impact 0..1, charging. */
    public float rear;
    public float impact;
    public boolean charging;
    /** Novus: the collar lamp is lit this frame. */
    public boolean lampOn;
    /** Sapiens: blaster levelled 0..1. */
    public float aim;
}
