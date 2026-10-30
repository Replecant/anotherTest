package com.replecant.retrocosmos.tribe;

import java.util.EnumSet;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.goal.Goal;

/** Hunters hurl a spear at an enemy that is out of reach (6-16 blocks, in plain sight), then close in. */
public class SpearThrowGoal extends Goal {
    private final Tribesman mob;
    private int cooldown;
    private int aimTicks;

    public SpearThrowGoal(Tribesman mob) {
        this.mob = mob;
        setFlags(EnumSet.of(Flag.LOOK));
    }

    @Override
    public boolean canUse() {
        if (cooldown > 0) {
            cooldown--;
            return false;
        }
        LivingEntity target = mob.getTarget();
        if (mob.isBaby() || mob.role() != TribeRole.HUNTER || target == null || !target.isAlive()) {
            return false;
        }
        double d = mob.distanceToSqr(target);
        return d > 6.0 * 6.0 && d < 16.0 * 16.0 && mob.getSensing().hasLineOfSight(target);
    }

    @Override
    public boolean canContinueToUse() {
        LivingEntity target = mob.getTarget();
        return aimTicks > 0 && target != null && target.isAlive();
    }

    @Override
    public void start() {
        aimTicks = 12;
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
        mob.getLookControl().setLookAt(target, 30.0F, 30.0F);
        if (--aimTicks > 0) {
            return;
        }
        ThrownSpear spear = new ThrownSpear(mob.level(), mob);
        double dx = target.getX() - mob.getX();
        double dy = target.getY(0.4) - spear.getY();
        double dz = target.getZ() - mob.getZ();
        double flat = Math.sqrt(dx * dx + dz * dz);
        spear.shoot(dx, dy + flat * 0.12, dz, 1.35F, 5.0F);
        mob.level().addFreshEntity(spear);
        mob.swing(InteractionHand.MAIN_HAND);
        mob.playSound(SoundEvents.SNOWBALL_THROW, 1.0F, 0.5F);
        mob.playSound(SoundEvents.PIGLIN_ANGRY, 0.8F, mob.getVoicePitch());
        cooldown = reducedTickDelay(70 + mob.getRandom().nextInt(50));
    }

    @Override
    public void stop() {
        aimTicks = 0;
        if (cooldown <= 0) {
            cooldown = reducedTickDelay(40);
        }
    }
}
