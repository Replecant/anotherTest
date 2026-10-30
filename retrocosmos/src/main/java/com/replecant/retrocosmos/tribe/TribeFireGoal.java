package com.replecant.retrocosmos.tribe;

import java.util.EnumSet;
import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.tags.BlockTags;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.phys.Vec3;

/**
 * Camp-fire time: at night (and now and then by day) a tribesman walks over to the camp fire, squats down facing
 * the flames, or - the shaman always, the others sometimes - dances around it.
 */
public class TribeFireGoal extends Goal {
    private final Tribesman mob;
    @Nullable
    private Vec3 spot;
    private int stayTicks;
    private int walkTicks;
    private boolean dancing;

    public TribeFireGoal(Tribesman mob) {
        this.mob = mob;
        setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
    }

    private boolean ready() {
        return mob.campFire() != null && !mob.isCaptive() && mob.getTarget() == null && !mob.isTrading() && !mob.isPassenger() && mob.isAlive();
    }

    @Override
    public boolean canUse() {
        if (!ready()) {
            return false;
        }
        int chance = mob.isNight() ? 40 : 700;
        return mob.getRandom().nextInt(reducedTickDelay(chance)) == 0;
    }

    @Override
    public boolean canContinueToUse() {
        return ready() && stayTicks > 0 && walkTicks < 400
                && mob.level().getBlockState(mob.campFire()).is(BlockTags.CAMPFIRES);
    }

    @Override
    public void start() {
        BlockPos fire = mob.campFire();
        double angle = mob.getRandom().nextDouble() * Math.PI * 2.0;
        double radius = 3.0 + mob.getRandom().nextDouble() * 1.3;
        spot = new Vec3(fire.getX() + 0.5 + Math.cos(angle) * radius, fire.getY(), fire.getZ() + 0.5 + Math.sin(angle) * radius);
        BlockPos ground = BlockPos.containing(spot);
        if (!mob.level().getBlockState(ground).getCollisionShape(mob.level(), ground).isEmpty()) {
            spot = spot.add(0.0, 1.0, 0.0);  // a sunken fire pit: the camp ground is one block up
        }
        boolean night = mob.isNight();
        dancing = mob.role() == TribeRole.SHAMAN ? mob.getRandom().nextInt(4) != 0 : mob.getRandom().nextInt(night ? 3 : 6) == 0;
        stayTicks = (night ? 400 : 160) + mob.getRandom().nextInt(night ? 500 : 200);
        walkTicks = 0;
        mob.getNavigation().moveTo(spot.x, spot.y, spot.z, 0.7);
    }

    @Override
    public void stop() {
        mob.setFireAction(0);
        spot = null;
    }

    @Override
    public boolean requiresUpdateEveryTick() {
        return true;
    }

    @Override
    public void tick() {
        BlockPos fire = mob.campFire();
        if (fire == null || spot == null) {
            return;
        }
        double dx = spot.x - mob.getX();
        double dz = spot.z - mob.getZ();
        double fx0 = fire.getX() + 0.5 - mob.getX();
        double fz0 = fire.getZ() + 0.5 - mob.getZ();
        boolean tooClose = fx0 * fx0 + fz0 * fz0 < 2.3 * 2.3;
        boolean there = dx * dx + dz * dz < 0.9 * 0.9 || (walkTicks > 120 && dx * dx + dz * dz < 2.0 * 2.0 && !tooClose);
        if (!there) {
            walkTicks++;
            mob.setFireAction(0);
            if (mob.getNavigation().isDone()) {
                mob.getNavigation().moveTo(spot.x, spot.y, spot.z, 0.7);
            }
            return;
        }
        stayTicks--;
        mob.getNavigation().stop();
        mob.setFireAction(dancing ? Tribesman.DANCE : Tribesman.SIT);
        // face the flames
        double fx = fire.getX() + 0.5 - mob.getX();
        double fz = fire.getZ() + 0.5 - mob.getZ();
        float yaw = (float) (Mth.atan2(fz, fx) * Mth.RAD_TO_DEG) - 90.0F;
        if (!dancing) {
            mob.setYRot(yaw);
            mob.setYBodyRot(yaw);
            mob.setYHeadRot(yaw);
        }
        mob.getLookControl().setLookAt(fire.getX() + 0.5, fire.getY() + 0.5, fire.getZ() + 0.5);
    }
}
