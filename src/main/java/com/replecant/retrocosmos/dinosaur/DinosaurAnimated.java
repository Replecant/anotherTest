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
