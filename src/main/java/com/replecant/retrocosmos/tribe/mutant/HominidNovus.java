package com.replecant.retrocosmos.tribe.mutant;

import com.replecant.retrocosmos.tribe.Tribesman;
import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.util.Mth;
import net.minecraft.world.damagesource.DamageSource;
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

/**
 * Hominid Novus: a tribesman pumped full of Dr. Oinstein's serum until it outgrew any cage but his collar. Lumbers
 * about on its knuckles, breaks into a charge when its prey is close, swats with fists like girders and every few
 * seconds rears up and slams the ground, throwing everyone around it into the air.
 */
public class HominidNovus extends Monster {
    /** 0 = normal, 1 = rearing up for a slam, 2 = fists in the ground (impact). */
    private static final EntityDataAccessor<Integer> SLAM = SynchedEntityData.defineId(HominidNovus.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Boolean> CHARGING = SynchedEntityData.defineId(HominidNovus.class, EntityDataSerializers.BOOLEAN);
    public static final int SLAM_NONE = 0;
    public static final int SLAM_REAR = 1;
    public static final int SLAM_IMPACT = 2;

    private float rear, rearO, impact, impactO;

    public HominidNovus(EntityType<? extends HominidNovus> type, Level level) {
        super(type, level);
        this.xpReward = 20;
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 70.0)
                .add(Attributes.ARMOR, 6.0)
                .add(Attributes.ATTACK_DAMAGE, 11.0)
                .add(Attributes.ATTACK_KNOCKBACK, 1.6)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.8)
                .add(Attributes.MOVEMENT_SPEED, 0.22)
                .add(Attributes.FOLLOW_RANGE, 32.0)
                .add(Attributes.STEP_HEIGHT, 1.1);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(1, new NovusSlamGoal(this));
        goalSelector.addGoal(2, new MeleeAttackGoal(this, 1.0, true) {
            @Override
            public void tick() {
                super.tick();
                LivingEntity target = mob.getTarget();
                boolean charge = target != null && mob.distanceToSqr(target) < 10.0 * 10.0 && mob.distanceToSqr(target) > 2.5 * 2.5;
                mob.getNavigation().setSpeedModifier(charge ? 1.75 : 1.0);
                setCharging(charge);
            }

            @Override
            public void stop() {
                super.stop();
                setCharging(false);
            }
        });
        goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 0.7));
        goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 12.0F));
        goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this));
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
        targetSelector.addGoal(3, new NearestAttackableTargetGoal<>(this, Tribesman.class, 10, true, false,
                (target, level) -> OinsteinForces.isEnemy(target)));
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(SLAM, SLAM_NONE);
        builder.define(CHARGING, false);
    }

    public int slamState() {
        return entityData.get(SLAM);
    }

    void setSlamState(int state) {
        entityData.set(SLAM, state);
    }

    public boolean isCharging() {
        return entityData.get(CHARGING);
    }

    void setCharging(boolean charging) {
        entityData.set(CHARGING, charging);
    }

    /** Oinstein's creatures never turn on each other. */
    @Override
    public boolean canAttack(LivingEntity target) {
        return !OinsteinForces.isForce(target) && super.canAttack(target);
    }

    @Override
    public void setTarget(@Nullable LivingEntity target) {
        super.setTarget(target != null && OinsteinForces.isForce(target) ? null : target);
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (OinsteinForces.isForce(source.getEntity())) {
            return false;
        }
        boolean hurt = super.hurtServer(level, source, amount);
        if (hurt && source.getEntity() instanceof LivingEntity attacker) {
            OinsteinForces.rally(level, this, attacker, 16.0);
        }
        return hurt;
    }

    @Override
    public void tick() {
        super.tick();
        if (level().isClientSide()) {
            rearO = rear;
            impactO = impact;
            int s = slamState();
            rear = Mth.approach(rear, s == SLAM_REAR ? 1.0F : 0.0F, s == SLAM_REAR ? 0.12F : 0.35F);
            impact = Mth.approach(impact, s == SLAM_IMPACT ? 1.0F : 0.0F, s == SLAM_IMPACT ? 0.6F : 0.12F);
        }
    }

    public float rearAmount(float partialTick) {
        return Mth.lerp(partialTick, rearO, rear);
    }

    public float impactAmount(float partialTick) {
        return Mth.lerp(partialTick, impactO, impact);
    }

    @Override
    public boolean doHurtTarget(ServerLevel level, Entity target) {
        boolean hit = super.doHurtTarget(level, target);
        if (hit) {
            playSound(SoundEvents.RAVAGER_ATTACK, 1.0F, 0.7F + random.nextFloat() * 0.1F);
            target.setDeltaMovement(target.getDeltaMovement().add(0.0, 0.25, 0.0));
        }
        return hit;
    }

    @Override
    protected SoundEvent getAmbientSound() {
        return random.nextInt(3) == 0 ? SoundEvents.POLAR_BEAR_WARNING : SoundEvents.RAVAGER_AMBIENT;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.RAVAGER_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.RAVAGER_DEATH;
    }

    @Override
    protected void playStepSound(BlockPos pos, BlockState state) {
        playSound(SoundEvents.RAVAGER_STEP, 0.5F, 0.8F);
    }

    @Override
    public float getVoicePitch() {
        return 0.72F + (random.nextFloat() - random.nextFloat()) * 0.08F;
    }

    @Override
    public int getMaxHeadYRot() {
        return 30;
    }
}
