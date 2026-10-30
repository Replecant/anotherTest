package com.replecant.retrocosmos.dinosaur;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ColorParticleOption;
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
import net.minecraft.world.entity.AreaEffectCloud;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
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
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

/**
 * Venus Creeper: a walking seed-pod of the Venus jungle. It creeps up on you, hisses, swells - and bursts,
 * blasting a small crater and leaving a lingering cloud of poisonous, nauseating spores.
 */
public class VenusCreeper extends Monster implements DinosaurAnimated {
    private static final EntityDataAccessor<Integer> SWELL_DIR = SynchedEntityData.defineId(VenusCreeper.class, EntityDataSerializers.INT);
    private static final int MAX_SWELL = 30;
    private static final float BLAST_RADIUS = 2.5F;
    private static final int SPORE_COLOR = 0xFF8CE046;

    private int oldSwell;
    private int swell;

    public VenusCreeper(EntityType<? extends VenusCreeper> type, Level level) {
        super(type, level);
        this.xpReward = 6;
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 22.0)
                .add(Attributes.MOVEMENT_SPEED, 0.25)
                .add(Attributes.FOLLOW_RANGE, 20.0);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(1, new FloatGoal(this));
        goalSelector.addGoal(2, new VenusCreeperSwellGoal(this));
        goalSelector.addGoal(4, new MeleeAttackGoal(this, 1.0, false));
        goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 0.8));
        goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 8.0F));
        goalSelector.addGoal(6, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new NearestAttackableTargetGoal<>(this, Player.class, true));
        targetSelector.addGoal(2, new HurtByTargetGoal(this));
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(SWELL_DIR, -1);
    }

    public int getSwellDir() {
        return entityData.get(SWELL_DIR);
    }

    public void setSwellDir(int dir) {
        entityData.set(SWELL_DIR, dir);
    }

    @Override
    public void tick() {
        if (isAlive()) {
            oldSwell = swell;
            int dir = getSwellDir();
            if (dir > 0 && swell == 0) {
                playSound(SoundEvents.CREEPER_PRIMED, 1.0F, 0.65F);
            }
            swell = Mth.clamp(swell + dir, 0, MAX_SWELL);
            if (swell >= MAX_SWELL) {
                burst();
            }
        }
        super.tick();
    }

    @Override
    public float swellAmount(float partialTick) {
        return Mth.lerp(partialTick, (float) oldSwell, (float) swell) / (MAX_SWELL - 2);
    }

    /** The blast itself, then the spore cloud that hangs over the crater. */
    private void burst() {
        if (!(level() instanceof ServerLevel server)) {
            return;
        }
        dead = true;
        server.explode(this, getX(), getY(), getZ(), BLAST_RADIUS, Level.ExplosionInteraction.MOB);
        AreaEffectCloud cloud = new AreaEffectCloud(server, getX(), getY() + 0.2, getZ());
        cloud.setRadius(3.5F);
        cloud.setRadiusOnUse(-0.4F);
        cloud.setWaitTime(5);
        cloud.setDuration(180);
        cloud.setRadiusPerTick(-cloud.getRadius() / cloud.getDuration());
        cloud.setCustomParticle(ColorParticleOption.create(ParticleTypes.ENTITY_EFFECT, SPORE_COLOR));
        cloud.addEffect(new MobEffectInstance(MobEffects.POISON, 120, 0));
        cloud.addEffect(new MobEffectInstance(MobEffects.NAUSEA, 180, 0));
        server.addFreshEntity(cloud);
        server.sendParticles(ParticleTypes.SPORE_BLOSSOM_AIR, getX(), getY() + 1.2, getZ(), 80, 1.6, 1.0, 1.6, 0.02);
        server.sendParticles(ParticleTypes.HAPPY_VILLAGER, getX(), getY() + 1.0, getZ(), 20, 1.2, 0.8, 1.2, 0.05);
        discard();
    }

    /** Creepers don't bite: getting close is all the attack it needs. */
    @Override
    public boolean doHurtTarget(ServerLevel level, Entity target) {
        return true;
    }

    @Override
    public boolean causeFallDamage(double distance, float multiplier, DamageSource source) {
        boolean hurt = super.causeFallDamage(distance, multiplier, source);
        swell = Math.min(swell + (int) (distance * 1.5), MAX_SWELL - 5);
        return hurt;
    }

    @Override
    public float getWalkTargetValue(BlockPos pos, LevelReader level) {
        return 0.0F;
    }

    @Override
    public int getMaxSpawnClusterSize() {
        return 1;
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putInt("Swell", swell);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        swell = input.getIntOr("Swell", 0);
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.CREEPER_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.CREEPER_DEATH;
    }

    @Override
    protected void playStepSound(BlockPos pos, BlockState state) {
        playSound(SoundEvents.AZALEA_LEAVES_STEP, 0.3F, 0.8F);
    }

    @Override
    public float getVoicePitch() {
        return 0.75F + (random.nextFloat() - random.nextFloat()) * 0.1F;
    }
}
