package com.replecant.retrocosmos.dinosaur;

import java.util.EnumSet;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.goal.Goal;

/**
 * The triceratops charge: stop and paw the ground with the head down, then thunder straight at the target.
 * A hit tosses the victim away; afterwards the beast trots off, turns, and - if still angry - goes again.
 */
public class TriceratopsChargeGoal extends Goal {
    private static final int WINDUP_TICKS = 24;
    private static final int MAX_RUSH_TICKS = 70;
    private static final int RECOVER_TICKS = 40;
    private static final double RUSH_SPEED = 2.4;

    private final Triceratops trike;
    private int phase;
    private int ticks;

    public TriceratopsChargeGoal(Triceratops trike) {
        this.trike = trike;
        setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK, Flag.JUMP));
    }

    @Override
    public boolean canUse() {
        LivingEntity target = trike.getTarget();
        return !trike.isBaby() && target != null && target.isAlive() && trike.distanceToSqr(target) < 24.0 * 24.0;
    }

    @Override
    public boolean canContinueToUse() {
        return canUse();
    }

    @Override
    public boolean requiresUpdateEveryTick() {
        return true;
    }

    @Override
    public void start() {
        enter(Triceratops.WINDUP);
    }

    @Override
    public void stop() {
        trike.setChargeState(Triceratops.CALM);
        trike.getNavigation().stop();
        phase = Triceratops.CALM;
    }

    private void enter(int newPhase) {
        phase = newPhase;
        ticks = 0;
        trike.setChargeState(newPhase == Triceratops.CHARGING || newPhase == Triceratops.WINDUP ? newPhase : Triceratops.CALM);
        if (newPhase == Triceratops.WINDUP) {
            trike.getNavigation().stop();
            trike.playSound(SoundEvents.POLAR_BEAR_WARNING, 1.4F, 0.65F);
        } else if (newPhase == Triceratops.CHARGING) {
            trike.playSound(SoundEvents.RAVAGER_ROAR, 1.0F, 1.35F);
        }
    }

    @Override
    public void tick() {
        LivingEntity target = trike.getTarget();
        if (target == null) {
            return;
        }
        ticks++;
        trike.getLookControl().setLookAt(target, 30.0F, 30.0F);
        switch (phase) {
            case Triceratops.WINDUP -> {
                trike.getNavigation().stop();
                if (ticks >= WINDUP_TICKS) {
                    enter(Triceratops.CHARGING);
                }
            }
            case Triceratops.CHARGING -> {
                if (ticks % 4 == 1) {
                    trike.getNavigation().moveTo(target, RUSH_SPEED);
                }
                if (trike.getBoundingBox().inflate(0.6).intersects(target.getBoundingBox())) {
                    gore(target);
                    enter(-1);
                } else if (ticks > MAX_RUSH_TICKS || trike.getNavigation().isDone() && ticks > 10) {
                    enter(-1);
                }
            }
            default -> {
                // recovering: amble away a few blocks, then square up again
                if (ticks == 1) {
                    double dx = trike.getX() - target.getX();
                    double dz = trike.getZ() - target.getZ();
                    double len = Math.max(0.1, Math.sqrt(dx * dx + dz * dz));
                    trike.getNavigation().moveTo(trike.getX() + dx / len * 6.0, trike.getY(), trike.getZ() + dz / len * 6.0, 1.1);
                }
                if (ticks >= RECOVER_TICKS) {
                    enter(Triceratops.WINDUP);
                }
            }
        }
    }

    private void gore(LivingEntity target) {
        trike.swing(InteractionHand.MAIN_HAND);
        if (trike.level() instanceof ServerLevel level && trike.doHurtTarget(level, target)) {
            trike.playSound(SoundEvents.GOAT_RAM_IMPACT, 1.2F, 0.7F);
            target.push(0.0, 0.35, 0.0);
            target.hurtMarked = true;
        }
    }
}
