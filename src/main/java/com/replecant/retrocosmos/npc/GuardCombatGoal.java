package com.replecant.retrocosmos.npc;

import java.util.EnumSet;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.phys.Vec3;

/**
 * A guard deals with a threat: from range with the ray pistol (an instant crackling beam), up close with the stun
 * baton. Gives up a chase that leads too far from the post.
 */
public class GuardCombatGoal extends Goal {
    private static final double PISTOL_RANGE = 18.0;
    private static final double BATON_RANGE = 2.6;
    private static final double LEASH = 28.0;
    /** Cherry-red beam. */
    private static final DustParticleOptions BEAM = new DustParticleOptions(0xFF3A3A, 0.9F);
    private static final DustParticleOptions BEAM_CORE = new DustParticleOptions(0xFFE0E0, 0.5F);

    private final ExpeditionMember guard;
    private int shotCooldown;
    private int meleeCooldown;

    public GuardCombatGoal(ExpeditionMember guard) {
        this.guard = guard;
        setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
    }

    @Override
    public boolean canUse() {
        LivingEntity target = guard.getTarget();
        return guard.role() == CrewRole.GUARD && target != null && target.isAlive() && guard.canAttack(target);
    }

    @Override
    public boolean canContinueToUse() {
        LivingEntity target = guard.getTarget();
        if (!canUse() || target == null) {
            return false;
        }
        if (target.distanceToSqr(guard.home().getCenter()) > LEASH * LEASH) {
            guard.setTarget(null);  // not leaving the camp unguarded for one lizard
            return false;
        }
        return true;
    }

    @Override
    public void start() {
        guard.setAggressive(true);
        shotCooldown = 8;
        meleeCooldown = 0;
        guard.shout("alert");
    }

    @Override
    public void stop() {
        guard.setAggressive(false);
        guard.setWeapon(ExpeditionMember.WEAPON_NONE);
        guard.getNavigation().stop();
    }

    @Override
    public boolean requiresUpdateEveryTick() {
        return true;
    }

    @Override
    public void tick() {
        LivingEntity target = guard.getTarget();
        if (target == null || !(guard.level() instanceof ServerLevel level)) {
            return;
        }
        guard.getLookControl().setLookAt(target, 30.0F, 30.0F);
        double d2 = guard.distanceToSqr(target);
        boolean see = guard.getSensing().hasLineOfSight(target);
        shotCooldown = Math.max(0, shotCooldown - 1);
        meleeCooldown = Math.max(0, meleeCooldown - 1);
        double reach = BATON_RANGE + target.getBbWidth() * 0.5;
        if (d2 <= reach * reach) {
            guard.setWeapon(ExpeditionMember.WEAPON_BATON);
            guard.getNavigation().stop();
            if (meleeCooldown == 0 && see) {
                meleeCooldown = 20;
                stun(level, target);
            }
        } else {
            guard.setWeapon(ExpeditionMember.WEAPON_PISTOL);
            if (see && d2 < PISTOL_RANGE * PISTOL_RANGE) {
                guard.getNavigation().stop();
                if (shotCooldown == 0) {
                    shotCooldown = 22 + guard.getRandom().nextInt(12);
                    fire(level, target);
                }
            } else if (guard.getNavigation().isDone() || guard.tickCount % 10 == 0) {
                guard.getNavigation().moveTo(target, 0.9);
            }
        }
    }

    /** The ray pistol: an instant beam of red light from the muzzle to the target. */
    void fire(ServerLevel level, LivingEntity target) {
        Vec3 eye = guard.getEyePosition();
        Vec3 to = target.getBoundingBox().getCenter();
        Vec3 dir = to.subtract(eye).normalize();
        Vec3 right = new Vec3(-dir.z, 0.0, dir.x).normalize();
        Vec3 from = eye.add(dir.scale(0.7)).add(right.scale(0.36)).add(0.0, -0.3, 0.0);
        boolean hit = guard.getRandom().nextFloat() < 0.85F;
        if (!hit) {
            to = to.add((guard.getRandom().nextDouble() - 0.5) * 1.6, guard.getRandom().nextDouble() * 0.8, (guard.getRandom().nextDouble() - 0.5) * 1.6);
        }
        Vec3 path = to.subtract(from);
        double len = path.length();
        int steps = Math.max(2, (int) (len / 0.3));
        for (int i = 0; i <= steps; i++) {
            Vec3 p = from.add(path.scale(i / (double) steps));
            level.sendParticles(BEAM, p.x, p.y, p.z, 1, 0.0, 0.0, 0.0, 0.0);
            if (i % 2 == 0) {
                level.sendParticles(BEAM_CORE, p.x, p.y, p.z, 1, 0.0, 0.0, 0.0, 0.0);
            }
        }
        level.sendParticles(ParticleTypes.ELECTRIC_SPARK, from.x, from.y, from.z, 3, 0.05, 0.05, 0.05, 0.05);
        guard.playSound(SoundEvents.BEACON_POWER_SELECT, 0.7F, 1.9F + guard.getRandom().nextFloat() * 0.1F);
        guard.playSound(SoundEvents.FIRECHARGE_USE, 0.35F, 1.8F);
        guard.swing(InteractionHand.MAIN_HAND);
        if (hit) {
            level.sendParticles(ParticleTypes.ELECTRIC_SPARK, to.x, to.y, to.z, 10, 0.2, 0.25, 0.2, 0.08);
            level.sendParticles(ParticleTypes.CRIT, to.x, to.y, to.z, 4, 0.2, 0.2, 0.2, 0.1);
            target.hurtServer(level, guard.damageSources().mobAttack(guard), ExpeditionMember.RAY_DAMAGE);
        } else {
            level.sendParticles(ParticleTypes.SMOKE, to.x, to.y, to.z, 3, 0.1, 0.1, 0.1, 0.01);
        }
        guard.shotsFired++;
    }

    /** The stun baton: a crack of blue sparks, damage, knockback and a few seconds of dazed slowness. */
    private void stun(ServerLevel level, LivingEntity target) {
        guard.swing(InteractionHand.MAIN_HAND);
        if (guard.doHurtTarget(level, target)) {
            target.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 50, 3), guard);
            Vec3 c = target.getBoundingBox().getCenter();
            level.sendParticles(ParticleTypes.ELECTRIC_SPARK, c.x, c.y, c.z, 16, 0.3, 0.4, 0.3, 0.12);
            guard.playSound(SoundEvents.BEACON_DEACTIVATE, 0.6F, 2.0F);
        }
    }
}
