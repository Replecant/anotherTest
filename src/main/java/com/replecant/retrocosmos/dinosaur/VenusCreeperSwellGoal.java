package com.replecant.retrocosmos.dinosaur;

import java.util.EnumSet;
import javax.annotation.Nullable;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.goal.Goal;

/** Like the vanilla creeper: stop next to the target and light the fuse; back off and the fuse goes out. */
public class VenusCreeperSwellGoal extends Goal {
    private final VenusCreeper creeper;
    @Nullable
    private LivingEntity target;

    public VenusCreeperSwellGoal(VenusCreeper creeper) {
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
