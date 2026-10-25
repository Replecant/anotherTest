package com.replecant.retrocosmos.tribe.mutant;

import java.util.EnumSet;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.phys.Vec3;

/**
 * The Sapiens' gunfight: keeps 8-14 blocks from its target, circle-strafes, and fires a blaster bolt every ~2
 * seconds while it has a clear line of fire. Backs off when the target closes in.
 */
public class BlasterAttackGoal extends Goal {
    private static final double MIN = 8.0;
    private static final double MAX = 14.0;
    private static final int INTERVAL = 40;

    private final HominusSapiens mob;
    private int shotTimer = 20;
    private int seeTime;
    private boolean strafeLeft;
    private int strafeTimer;

    public BlasterAttackGoal(HominusSapiens mob) {
        this.mob = mob;
        setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
    }

    @Override
    public boolean canUse() {
        LivingEntity target = mob.getTarget();
        return target != null && target.isAlive() && !mob.isRetreating();
    }

    @Override
    public boolean canContinueToUse() {
        return canUse();
    }

    @Override
    public void start() {
        mob.setAggressive(true);
    }

    @Override
    public void stop() {
        mob.setAggressive(false);
        mob.setAiming(false);
        mob.getMoveControl().strafe(0, 0);
        seeTime = 0;
    }

    @Override
    public boolean requiresUpdateEveryTick() {
        return true;
    }

    @Override
    public void tick() {
        LivingEntity target = mob.getTarget();
        if (target == null) {
            return;
        }
        double d = mob.distanceTo(target);
        boolean sees = mob.getSensing().hasLineOfSight(target);
        seeTime = sees ? seeTime + 1 : Math.min(0, seeTime - 1);
        if (!sees || d > MAX + 4) {
            mob.getNavigation().moveTo(target, 1.0);  // close in to firing range
        } else {
            mob.getNavigation().stop();
            if (++strafeTimer > 30 && mob.getRandom().nextFloat() < 0.15F) {
                strafeLeft = !strafeLeft;
                strafeTimer = 0;
            }
            float forward = d > MAX ? 0.5F : d < MIN ? -0.6F : 0.0F;
            mob.getMoveControl().strafe(forward, strafeLeft ? 0.45F : -0.45F);
            mob.lookAt(target, 30.0F, 30.0F);
        }
        mob.getLookControl().setLookAt(target, 30.0F, 30.0F);
        mob.setAiming(sees && d < MAX + 4);
        if (--shotTimer <= 0 && sees && seeTime > 5 && d < MAX + 4) {
            Vec3 aim = new Vec3(target.getX() - mob.getX(), target.getY(0.5) - (mob.getEyeY() - 0.35), target.getZ() - mob.getZ());
            BlasterBolt.fire(mob, aim, 2.0F);
            mob.swing(net.minecraft.world.InteractionHand.MAIN_HAND);
            shotTimer = INTERVAL + mob.getRandom().nextInt(10) - 5;
        }
    }
}
