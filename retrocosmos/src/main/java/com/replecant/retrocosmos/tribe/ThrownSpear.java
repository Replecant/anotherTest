package com.replecant.retrocosmos.tribe;

import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.projectile.throwableitemprojectile.ThrowableItemProjectile;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.HitResult;

/** A light throwing spear a tribe hunter hurls at something out of reach. Breaks on impact. */
public class ThrownSpear extends ThrowableItemProjectile {
    private static final float DAMAGE = 4.0F;

    public ThrownSpear(EntityType<? extends ThrownSpear> type, Level level) {
        super(type, level);
    }

    public ThrownSpear(Level level, LivingEntity thrower) {
        super(ModTribes.THROWN_SPEAR.get(), thrower, level, new ItemStack(ModTribes.BONE_SPEAR.get()));
    }

    @Override
    protected Item getDefaultItem() {
        return ModTribes.BONE_SPEAR.get();
    }

    @Override
    protected double getDefaultGravity() {
        return 0.04;
    }

    @Override
    protected void onHitEntity(EntityHitResult result) {
        super.onHitEntity(result);
        Entity target = result.getEntity();
        Entity owner = getOwner();
        if (target instanceof Tribesman && owner instanceof Tribesman) {
            return;  // never their own
        }
        if (level() instanceof ServerLevel server) {
            target.hurtServer(server, damageSources().thrown(this, owner), DAMAGE);
        }
    }

    @Override
    protected void onHit(HitResult result) {
        super.onHit(result);
        if (level() instanceof ServerLevel server) {
            server.sendParticles(ParticleTypes.CRIT, getX(), getY(), getZ(), 6, 0.1, 0.1, 0.1, 0.2);
            playSound(SoundEvents.WOOD_BREAK, 0.6F, 1.3F);
            discard();
        }
    }
}
