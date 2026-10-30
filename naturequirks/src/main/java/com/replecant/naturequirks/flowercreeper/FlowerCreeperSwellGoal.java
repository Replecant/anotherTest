package com.replecant.naturequirks.flowercreeper;

import java.util.EnumSet;
import javax.annotation.Nullable;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.goal.Goal;

/** The vanilla creeper's SwellGoal: start the fuse within 3 blocks of the target, defuse past 7 or out of sight. */
public class FlowerCreeperSwellGoal extends Goal {
    private final FlowerCreeper creeper;
    @Nullable
    private LivingEntity target;

    public FlowerCreeperSwellGoal(FlowerCreeper creeper) {
        this.creeper = creeper;
        setFlags(EnumSet.of(Flag.MOVE));
    }

    @Override
    public boolean canUse() {
        LivingEntity t = creeper.getTarget();
        return creeper.getSwellDir() > 0 || t != null && creeper.distanceToSqr(t) < 9.0;
    }

    @Override
    public void start() {
        creeper.getNavigation().stop();
        target = creeper.getTarget();
    }

    @Override
    public void stop() {
        target = null;
    }

    @Override
    public boolean requiresUpdateEveryTick() {
        return true;
    }

    @Override
    public void tick() {
        if (target == null || creeper.distanceToSqr(target) > 49.0 || !creeper.getSensing().hasLineOfSight(target)) {
            creeper.setSwellDir(-1);
        } else {
            creeper.setSwellDir(1);
        }
    }
}
