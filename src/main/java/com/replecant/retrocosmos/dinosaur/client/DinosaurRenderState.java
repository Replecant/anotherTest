package com.replecant.retrocosmos.dinosaur.client;

import net.minecraft.client.renderer.entity.state.LivingEntityRenderState;

/** Render state shared by the three dinosaurs; each model reads the channels it needs. */
public class DinosaurRenderState extends LivingEntityRenderState {
    /** Melee swing progress 0..1 (bite / claw swipe). */
    public float attackAnim;
    public boolean aggressive;
    /** Raptor pounce pose 0..1. */
    public float leap;
    /** Brontosaurus head-down grazing 0..1. */
    public float graze;
    /** Triceratops head-down charge 0..1. */
    public float charge;
    /** Triceratops pawing the ground before a charge. */
    public boolean windup;
}
