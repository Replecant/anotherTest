package com.replecant.retrocosmos.dinosaur;

import java.util.EnumSet;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.animal.Animal;

/** A grazer (brontosaurus, ankylosaurus) stops, lowers its head to the ground and munches for a while. */
public class GrazeGoal extends Goal {
    /** A mob that shows its grazing to the client (usually through a synced flag). */
    public interface Grazer {
        void setGrazing(boolean grazing);
    }

    private final Animal bronto;
    private final Grazer grazer;
    private int ticks;

    public <T extends Animal & Grazer> GrazeGoal(T bronto) {
        this.bronto = bronto;
        this.grazer = bronto;
        setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK, Flag.JUMP));
    }

    @Override
    public boolean canUse() {
        return bronto.onGround() && !bronto.isInWater()
                && bronto.getRandom().nextInt(reducedTickDelay(bronto.isBaby() ? 200 : 260)) == 0;
    }

    @Override
    public boolean canContinueToUse() {
        return ticks > 0 && bronto.onGround();
    }

    @Override
    public void start() {
        ticks = adjustedTickDelay(110 + bronto.getRandom().nextInt(90));
        bronto.getNavigation().stop();
        grazer.setGrazing(true);
    }

    @Override
    public void stop() {
        grazer.setGrazing(false);
    }

    @Override
    public boolean requiresUpdateEveryTick() {
        return true;
    }

    @Override
    public void tick() {
        ticks--;
        if (ticks % 30 == 0) {
            bronto.playSound(SoundEvents.SNIFFER_EAT, 1.2F, 0.6F);
            if (bronto.getHealth() < bronto.getMaxHealth()) {
                bronto.heal(1.0F);
            }
        }
    }
}
