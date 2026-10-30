package com.replecant.retrocosmos.dinosaur.client;

import net.minecraft.client.renderer.entity.state.LivingEntityRenderState;

/** Render state shared by all the Venus dinosaurs; each model reads the channels it needs. */
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
    /** Venus Creeper fuse 0..1. */
    public float swell;
    /** Pteranodon: perched with folded wings 0..1, stooping 0..1, nose-down pitch in flight (radians). */
    public float perch;
    public float dive;
    public float flightPitch;
    /** Tyrannosaurus roar and tail sweep 0..1. */
    public float roar;
    public float sweep;
    /** Plesiosaur neck up, ankylosaurus club swing, deinosuchus strike 0..1. */
    public float peek;
    public float swing;
    public float lunge;
}
