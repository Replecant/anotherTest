package com.replecant.retrocosmos.dinosaur;

import net.minecraft.util.Mth;

/** Client-visible animation channels a dinosaur exposes to its renderer (all smoothed, 0..1). */
public interface DinosaurAnimated {
    default float leapAmount(float partialTick) {
        return 0.0F;
    }

    default float grazeAmount(float partialTick) {
        return 0.0F;
    }

    default float chargeAmount(float partialTick) {
        return 0.0F;
    }

    default boolean isWindingUp() {
        return false;
    }

    /** Venus Creeper fuse, 0 = calm .. 1 = about to burst. */
    default float swellAmount(float partialTick) {
        return 0.0F;
    }

    /** Pteranodon sitting on its perch with folded wings. */
    default float perchAmount(float partialTick) {
        return 0.0F;
    }

    /** Pteranodon stooping on its prey. */
    default float diveAmount(float partialTick) {
        return 0.0F;
    }

    /** Body pitch in flight (radians, nose down positive). */
    default float flightPitch(float partialTick) {
        return 0.0F;
    }

    /** Tyrannosaurus roar. */
    default float roarAmount(float partialTick) {
        return 0.0F;
    }

    /** Plesiosaur holding its neck up out of the water. */
    default float peekAmount(float partialTick) {
        return 0.0F;
    }

    /** Ankylosaurus tail-club swing (0..1 over the swing). */
    default float swingAmount(float partialTick) {
        return 0.0F;
    }

    /** Deinosuchus strike, jaws gaping. */
    default float lungeAmount(float partialTick) {
        return 0.0F;
    }

    /** Tyrannosaurus tail sweep. */
    default float sweepAmount(float partialTick) {
        return 0.0F;
    }

    /** A 0..1 value that eases towards on/off each client tick, interpolated by partial tick. */
    final class Smoothed {
        private float previous;
        private float current;
        private final float step;

        public Smoothed(float step) {
            this.step = step;
        }

        public void tick(boolean on) {
            previous = current;
            current = Mth.approach(current, on ? 1.0F : 0.0F, step);
        }

        public float get(float partialTick) {
            float t = Mth.lerp(partialTick, previous, current);
            return t * t * (3.0F - 2.0F * t);
        }
    }
}
