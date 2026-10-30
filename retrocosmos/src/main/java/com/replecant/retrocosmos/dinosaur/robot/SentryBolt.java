package com.replecant.retrocosmos.dinosaur.robot;

import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.projectile.hurtingprojectile.AbstractHurtingProjectile;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

/** The atomic sentry's blaster bolt: a fast straight streak of red energy. Never burns, never hits Oinstein's own. */
public class SentryBolt extends AbstractHurtingProjectile {
    private static final float DAMAGE = 5.0F;
    private static final double SPEED = 1.1;
    private static final int LIFETIME = 50;

    public SentryBolt(EntityType<? extends SentryBolt> type, Level level) {
        super(type, level);
        this.accelerationPower = 0.0;
    }

    public SentryBolt(Level level, LivingEntity owner, Vec3 direction) {
        super(ModRobots.SENTRY_BOLT.get(), owner, direction, level);
        this.accelerationPower = 0.0;
        setDeltaMovement(direction.normalize().scale(SPEED));
    }

    @Override
    public void tick() {
        super.tick();
        if (!level().isClientSide() && tickCount > LIFETIME) {
            discard();
        }
    }

    @Override
    protected boolean canHitEntity(Entity target) {
        return super.canHitEntity(target) && !OinsteinForces.isMember(target);
    }

    @Override
    protected void onHitEntity(EntityHitResult result) {
        super.onHitEntity(result);
        if (level() instanceof ServerLevel level) {
            Entity owner = getOwner();
            result.getEntity().hurtServer(level, damageSources().mobProjectile(this, owner instanceof LivingEntity l ? l : null), DAMAGE);
        }
    }

    @Override
    protected void onHitBlock(BlockHitResult result) {
        super.onHitBlock(result);
    }

    @Override
    protected void onHit(HitResult result) {
        super.onHit(result);
        if (level() instanceof ServerLevel level) {
            level.sendParticles(ParticleTypes.ELECTRIC_SPARK, getX(), getY(), getZ(), 8, 0.1, 0.1, 0.1, 0.15);
            playSound(SoundEvents.REDSTONE_TORCH_BURNOUT, 0.4F, 1.8F);
            discard();
        }
    }

    @Override
    protected boolean shouldBurn() {
        return false;
    }

    @Override
    protected float getInertia() {
        return 1.0F;
    }

    @Override
    protected float getLiquidInertia() {
        return 0.9F;
    }

    @Override
    protected ParticleOptions getTrailParticle() {
        return ParticleTypes.ELECTRIC_SPARK;
    }

    @Override
    public boolean isPickable() {
        return false;
    }
}
