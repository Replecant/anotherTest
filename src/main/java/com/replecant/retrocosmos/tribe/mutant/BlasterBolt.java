package com.replecant.retrocosmos.tribe.mutant;

import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.tribe.ModTribes;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.damagesource.DamageType;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.projectile.ThrowableProjectile;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

/** A glowing ray-gun bolt: flies straight and fast, zaps the first thing it hits, sets nothing on fire. */
public class BlasterBolt extends ThrowableProjectile {
    public static final ResourceKey<DamageType> BLASTER = ResourceKey.create(Registries.DAMAGE_TYPE,
            Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "blaster"));
    public static final float DAMAGE = 6.0F;
    public static final float SPEED = 2.2F;
    private static final int LIFETIME = 40;

    public BlasterBolt(EntityType<? extends BlasterBolt> type, Level level) {
        super(type, level);
    }

    /** A bolt leaving the shooter's muzzle along its view (or towards a target). */
    public static BlasterBolt fire(LivingEntity shooter, Vec3 direction, float inaccuracy) {
        BlasterBolt bolt = new BlasterBolt(ModTribes.BLASTER_BOLT.get(), shooter.level());
        bolt.setOwner(shooter);
        Vec3 side = direction.cross(new Vec3(0, 1, 0)).normalize().scale(-0.35);
        bolt.setPos(shooter.getX() + side.x + direction.x * 0.6, shooter.getEyeY() - 0.35 + direction.y * 0.6,
                shooter.getZ() + side.z + direction.z * 0.6);
        bolt.shoot(direction.x, direction.y, direction.z, SPEED, inaccuracy);
        shooter.level().addFreshEntity(bolt);
        shooter.level().playSound(null, shooter.getX(), shooter.getY(), shooter.getZ(), SoundEvents.FIREWORK_ROCKET_BLAST,
                SoundSource.HOSTILE, 0.8F, 1.9F + shooter.getRandom().nextFloat() * 0.2F);
        shooter.level().playSound(null, shooter.getX(), shooter.getY(), shooter.getZ(), SoundEvents.BEACON_POWER_SELECT,
                SoundSource.HOSTILE, 0.5F, 2.0F);
        return bolt;
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
    }

    @Override
    protected double getDefaultGravity() {
        return 0.0;
    }

    @Override
    public void tick() {
        super.tick();
        if (level() instanceof ServerLevel server) {
            if (tickCount > LIFETIME) {
                discard();
                return;
            }
            if (tickCount % 2 == 0) {
                server.sendParticles(ParticleTypes.ELECTRIC_SPARK, getX(), getY(), getZ(), 1, 0.02, 0.02, 0.02, 0.0);
            }
        }
    }

    @Override
    protected boolean canHitEntity(Entity entity) {
        // Oinstein's own bolts pass through his creatures
        if (OinsteinForces.isForce(getOwner()) && OinsteinForces.isForce(entity)) {
            return false;
        }
        return super.canHitEntity(entity);
    }

    @Override
    protected void onHitEntity(EntityHitResult result) {
        super.onHitEntity(result);
        if (level() instanceof ServerLevel server) {
            Entity owner = getOwner();
            result.getEntity().hurtServer(server, damageSources().source(BLASTER, this, owner != null ? owner : this), DAMAGE);
        }
    }

    @Override
    protected void onHit(HitResult result) {
        super.onHit(result);
        if (level() instanceof ServerLevel server) {
            Vec3 p = result.getLocation();
            server.sendParticles(ParticleTypes.ELECTRIC_SPARK, p.x, p.y, p.z, 12, 0.15, 0.15, 0.15, 0.25);
            server.sendParticles(ParticleTypes.END_ROD, p.x, p.y, p.z, 4, 0.05, 0.05, 0.05, 0.08);
            server.playSound(null, p.x, p.y, p.z, SoundEvents.FIREWORK_ROCKET_TWINKLE, SoundSource.HOSTILE, 0.6F, 1.8F);
            discard();
        }
    }
}
