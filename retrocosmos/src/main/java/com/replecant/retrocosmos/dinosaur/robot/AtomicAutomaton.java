package com.replecant.retrocosmos.dinosaur.robot;

import com.replecant.retrocosmos.dinosaur.DinosaurAnimated;
import com.replecant.retrocosmos.tribe.Tribesman;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.util.Mth;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

/**
 * Atomic Automaton: Dr. Oinstein's walking strong-arm, a 1950s picture-show robot. Slow but relentless; punches
 * hard (12) and every third blow is a smoking, crackling power fist. Short-circuits in water.
 */
public class AtomicAutomaton extends Monster implements DinosaurAnimated {
    private static final EntityDataAccessor<Integer> POWER = SynchedEntityData.defineId(AtomicAutomaton.class, EntityDataSerializers.INT);
    static final int POWER_TICKS = 16;
    private static final int POWER_EVERY = 3;

    private int hits;
    private int powerClient;
    private int powerClientO;

    public AtomicAutomaton(EntityType<? extends AtomicAutomaton> type, Level level) {
        super(type, level);
        this.xpReward = 20;
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 80.0)
                .add(Attributes.MOVEMENT_SPEED, 0.18)
                .add(Attributes.ATTACK_DAMAGE, 12.0)
                .add(Attributes.ATTACK_KNOCKBACK, 1.8)
                .add(Attributes.ARMOR, 12.0)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.9)
                .add(Attributes.FOLLOW_RANGE, 32.0)
                .add(Attributes.STEP_HEIGHT, 1.0);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(2, new MeleeAttackGoal(this, 1.25, true));
        goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 0.7));
        goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 12.0F));
        goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this));
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
        targetSelector.addGoal(3, new NearestAttackableTargetGoal<>(this, Tribesman.class, true));
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(POWER, 0);
    }

    @Override
    public boolean canAttack(LivingEntity target) {
        return !OinsteinForces.isMember(target) && super.canAttack(target);
    }

    /** Every third blow is the power fist: half again the damage, a huge knock, smoke and sparks. */
    @Override
    public boolean doHurtTarget(ServerLevel level, Entity target) {
        hits++;
        if (hits % POWER_EVERY != 0 || !(target instanceof LivingEntity living)) {
            boolean hit = super.doHurtTarget(level, target);
            if (hit) {
                playSound(SoundEvents.IRON_GOLEM_ATTACK, 1.0F, 0.7F);
            }
            return hit;
        }
        entityData.set(POWER, entityData.get(POWER) + 1);
        float damage = (float) getAttributeValue(Attributes.ATTACK_DAMAGE) * 1.5F;
        boolean hit = living.hurtServer(level, damageSources().mobAttack(this), damage);
        if (hit) {
            Vec3 away = living.position().subtract(position()).multiply(1.0, 0.0, 1.0).normalize();
            living.knockback(2.6, -away.x, -away.z);
            living.push(0.0, 0.45, 0.0);
            living.hurtMarked = true;
            setLastHurtMob(living);
        }
        Vec3 fist = position().add(Vec3.directionFromRotation(0.0F, getYRot()).scale(1.2)).add(0.0, 1.2, 0.0);
        level.sendParticles(ParticleTypes.LARGE_SMOKE, fist.x, fist.y, fist.z, 12, 0.3, 0.3, 0.3, 0.03);
        level.sendParticles(ParticleTypes.ELECTRIC_SPARK, fist.x, fist.y, fist.z, 30, 0.4, 0.4, 0.4, 0.5);
        playSound(SoundEvents.GENERIC_EXPLODE.value(), 0.7F, 1.7F);
        playSound(SoundEvents.ANVIL_LAND, 0.6F, 0.6F);
        return hit;
    }

    @Override
    public void onSyncedDataUpdated(EntityDataAccessor<?> key) {
        super.onSyncedDataUpdated(key);
        if (POWER.equals(key) && level().isClientSide()) {
            powerClient = POWER_TICKS;
            powerClientO = POWER_TICKS;
        }
    }

    @Override
    public void tick() {
        super.tick();
        if (level().isClientSide()) {
            powerClientO = powerClient;
            if (powerClient > 0) {
                powerClient--;
            }
        }
    }

    /** The power fist, 0 -> 1 over the blow. */
    @Override
    public float swingAmount(float partialTick) {
        float left = Mth.lerp(partialTick, powerClientO, powerClient);
        return left <= 0.0F ? 0.0F : 1.0F - left / POWER_TICKS;
    }

    /** Water gets into the works: it sparks, fizzes and takes damage while wet. */
    @Override
    public void aiStep() {
        super.aiStep();
        if (level() instanceof ServerLevel level && isInWater() && tickCount % 20 == 0) {
            hurtServer(level, damageSources().generic(), 3.0F);
            level.sendParticles(ParticleTypes.ELECTRIC_SPARK, getX(), getY() + 1.4, getZ(), 15, 0.4, 0.6, 0.4, 0.3);
            playSound(SoundEvents.REDSTONE_TORCH_BURNOUT, 1.0F, 0.8F);
        }
    }

    @Override
    public boolean canBeAffected(MobEffectInstance effect) {
        return !effect.is(MobEffects.POISON) && super.canBeAffected(effect);
    }

    @Override
    public void die(DamageSource source) {
        super.die(source);
        if (level() instanceof ServerLevel level) {
            level.explode(this, getX(), getY() + 1.2, getZ(), 1.2F, Level.ExplosionInteraction.NONE);
            level.sendParticles(ParticleTypes.ELECTRIC_SPARK, getX(), getY() + 1.2, getZ(), 50, 0.5, 0.8, 0.5, 0.4);
        }
    }

    @Override
    protected void playStepSound(BlockPos pos, BlockState state) {
        playSound(SoundEvents.IRON_GOLEM_STEP, 1.2F, 0.55F);
        playSound(SoundEvents.ANVIL_LAND, 0.12F, 1.8F);
    }

    @Override
    protected SoundEvent getAmbientSound() {
        return SoundEvents.BEACON_AMBIENT;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.IRON_GOLEM_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.IRON_GOLEM_DEATH;
    }

    @Override
    public float getVoicePitch() {
        return 0.7F + (random.nextFloat() - random.nextFloat()) * 0.05F;
    }
}
