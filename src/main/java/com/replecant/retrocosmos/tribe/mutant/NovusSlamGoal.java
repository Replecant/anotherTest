package com.replecant.retrocosmos.tribe.mutant;

import java.util.EnumSet;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

/**
 * The Novus' ground slam: when its prey is close, it rears up for a moment (a roar - the tell), then drives both
 * fists into the ground. Everything within a few blocks that is not one of Oinstein's own takes damage and is thrown
 * up and away. At most every ~6 seconds.
 */
public class NovusSlamGoal extends Goal {
    static final double RANGE = 4.5;
    private static final int COOLDOWN = 120;
    private static final int WINDUP = 16;
    private static final int RECOVER = 14;
    private static final float DAMAGE = 7.0F;

    private final HominidNovus mob;
    private int cooldown = 40;
    private int ticks;

    public NovusSlamGoal(HominidNovus mob) {
        this.mob = mob;
        setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK, Flag.JUMP));
    }

    @Override
    public boolean canUse() {
        if (cooldown > 0) {
            cooldown--;
            return false;
        }
        LivingEntity target = mob.getTarget();
        return target != null && target.isAlive() && mob.onGround() && mob.distanceToSqr(target) < RANGE * RANGE;
    }

    @Override
    public boolean canContinueToUse() {
        return ticks < WINDUP + RECOVER && mob.isAlive();
    }

    @Override
    public void start() {
        ticks = 0;
        mob.getNavigation().stop();
        mob.setSlamState(HominidNovus.SLAM_REAR);
        mob.playSound(SoundEvents.RAVAGER_ROAR, 1.6F, 0.75F);
    }

    @Override
    public void stop() {
        mob.setSlamState(HominidNovus.SLAM_NONE);
        cooldown = COOLDOWN + mob.getRandom().nextInt(30);
    }

    @Override
    public boolean requiresUpdateEveryTick() {
        return true;
    }

    @Override
    public void tick() {
        ticks++;
        LivingEntity target = mob.getTarget();
        if (target != null && ticks < WINDUP) {
            mob.getLookControl().setLookAt(target, 30.0F, 30.0F);
        }
        if (ticks == WINDUP) {
            mob.setSlamState(HominidNovus.SLAM_IMPACT);
            slam();
        }
    }

    private void slam() {
        if (!(mob.level() instanceof ServerLevel level)) {
            return;
        }
        Vec3 c = mob.position().add(mob.getLookAngle().multiply(1.2, 0, 1.2));
        BlockState ground = level.getBlockState(BlockPos.containing(c.x, mob.getY() - 0.5, c.z));
        level.playSound(null, c.x, c.y, c.z, SoundEvents.GENERIC_EXPLODE.value(), mob.getSoundSource(), 1.2F, 0.6F);
        level.playSound(null, c.x, c.y, c.z, SoundEvents.MACE_SMASH_GROUND_HEAVY, mob.getSoundSource(), 1.4F, 0.8F);
        // a ring of dust and debris rolling outwards
        for (int ring = 1; ring <= 4; ring++) {
            int n = 10 + ring * 6;
            for (int k = 0; k < n; k++) {
                double a = Math.PI * 2 * k / n;
                double r = ring * 1.1;
                double px = c.x + Math.cos(a) * r;
                double pz = c.z + Math.sin(a) * r;
                if (!ground.isAir()) {
                    level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, ground), px, mob.getY() + 0.1, pz, 2, 0.1, 0.05, 0.1, 0.15);
                }
                level.sendParticles(ParticleTypes.POOF, px, mob.getY() + 0.2, pz, 1, 0.05, 0.05, 0.05, 0.02);
            }
        }
        level.sendParticles(ParticleTypes.EXPLOSION, c.x, mob.getY() + 0.3, c.z, 2, 0.4, 0.1, 0.4, 0.0);
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, mob.getBoundingBox().inflate(RANGE, 2.0, RANGE),
                e -> e != mob && e.isAlive() && !OinsteinForces.isForce(e))) {
            double dx = e.getX() - c.x;
            double dz = e.getZ() - c.z;
            double dist = Math.max(0.5, Math.sqrt(dx * dx + dz * dz));
            if (dist > RANGE + 0.5) {
                continue;
            }
            float falloff = (float) Mth.clamp(1.2 - dist / (RANGE + 1.0), 0.35, 1.0);
            if (e.hurtServer(level, mob.damageSources().mobAttack(mob), DAMAGE * falloff)) {
                double resist = 1.0 - e.getAttributeValue(net.minecraft.world.entity.ai.attributes.Attributes.KNOCKBACK_RESISTANCE) * 0.6;
                double kb = 0.8 * falloff * resist;
                // thrown up about two blocks and away from the impact (replaces, not adds to, the hit's knockback)
                Vec3 v = e.getDeltaMovement();
                e.setDeltaMovement(v.x * 0.3 + dx / dist * kb, (0.3 + 0.25 * falloff) * resist, v.z * 0.3 + dz / dist * kb);
                e.hurtMarked = true;
            }
        }
    }
}
