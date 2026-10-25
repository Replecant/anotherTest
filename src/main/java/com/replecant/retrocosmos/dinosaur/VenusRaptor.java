package com.replecant.retrocosmos.dinosaur;

import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.LeapAtTargetGoal;
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
import net.minecraft.world.level.pathfinder.PathType;

/**
 * Venus Raptor: a hostile pack hunter. Fast, leaps at its prey, and when one raptor picks a target the rest of
 * the pack joins in. Hates water and paths around it.
 */
public class VenusRaptor extends Monster implements DinosaurAnimated {
    private static final double PACK_RANGE = 16.0;

    private final Smoothed leap = new Smoothed(0.25F);

    public VenusRaptor(EntityType<? extends VenusRaptor> type, Level level) {
        super(type, level);
        this.xpReward = 8;
        setPathfindingMalus(PathType.WATER, -1.0F);
        setPathfindingMalus(PathType.WATER_BORDER, 8.0F);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 24.0)
                .add(Attributes.MOVEMENT_SPEED, 0.34)
                .add(Attributes.ATTACK_DAMAGE, 5.0)
                .add(Attributes.ARMOR, 2.0)
                .add(Attributes.FOLLOW_RANGE, 32.0)
                .add(Attributes.STEP_HEIGHT, 1.0)
                .add(Attributes.SAFE_FALL_DISTANCE, 6.0);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(1, new LeapAtTargetGoal(this, 0.45F));
        goalSelector.addGoal(2, new MeleeAttackGoal(this, 1.35, true));
        goalSelector.addGoal(4, new RaptorPackGoal(this));
        goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 0.85));
        goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 12.0F));
        goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this).setAlertOthers());
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    /** One raptor spotting prey calls the whole pack. */
    @Override
    public void setTarget(@Nullable LivingEntity target) {
        LivingEntity previous = getTarget();
        super.setTarget(target);
        if (target != null && previous == null && level() instanceof ServerLevel && !(target instanceof VenusRaptor)) {
            playSound(SoundEvents.HOGLIN_ANGRY, 1.2F, 1.55F + random.nextFloat() * 0.2F);
            for (VenusRaptor other : level().getEntitiesOfClass(VenusRaptor.class, getBoundingBox().inflate(PACK_RANGE, 6.0, PACK_RANGE),
                    r -> r != this && r.isAlive() && r.getTarget() == null)) {
                other.setTarget(target);
            }
        }
    }

    @Override
    public void tick() {
        super.tick();
        if (level().isClientSide()) {
            leap.tick(!onGround() && !isInWater() && !isPassenger() && getDeltaMovement().y > -0.6);
        }
    }

    @Override
    public float leapAmount(float partialTick) {
        return leap.get(partialTick);
    }

    @Override
    public boolean doHurtTarget(ServerLevel level, Entity target) {
        boolean hit = super.doHurtTarget(level, target);
        if (hit) {
            playSound(SoundEvents.RAVAGER_ATTACK, 0.8F, 1.7F + random.nextFloat() * 0.2F);
        }
        return hit;
    }

    /** Raptors roam the jungle by day; no preference for dark spots like ordinary monsters. */
    @Override
    public float getWalkTargetValue(BlockPos pos, LevelReader level) {
        return 0.0F;
    }

    @Override
    public int getMaxSpawnClusterSize() {
        return 4;
    }

    @Override
    protected SoundEvent getAmbientSound() {
        return SoundEvents.HOGLIN_AMBIENT;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.HOGLIN_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.HOGLIN_DEATH;
    }

    @Override
    protected void playStepSound(BlockPos pos, BlockState state) {
        playSound(SoundEvents.HOGLIN_STEP, 0.12F, 1.6F);
    }

    @Override
    public float getVoicePitch() {
        return 1.45F + (random.nextFloat() - random.nextFloat()) * 0.15F;
    }
}
