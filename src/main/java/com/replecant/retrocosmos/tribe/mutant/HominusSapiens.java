package com.replecant.retrocosmos.tribe.mutant;

import com.replecant.retrocosmos.tribe.Tribesman;
import javax.annotation.Nullable;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.ai.util.DefaultRandomPos;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

/**
 * Hominus Sapiens: Dr. Oinstein's success - an uplifted hominid with a brain too big for its skull, kept under a
 * glass dome. Fights at range with a ray pistol, keeping its distance; when badly hurt it falls back and radios the
 * rest of Oinstein's forces onto whoever did it.
 */
public class HominusSapiens extends Monster {
    private static final EntityDataAccessor<Boolean> AIMING = SynchedEntityData.defineId(HominusSapiens.class, EntityDataSerializers.BOOLEAN);
    private static final float RETREAT_FRACTION = 0.35F;

    private int retreatTicks;
    private int callCooldown;
    private float aim, aimO;

    public HominusSapiens(EntityType<? extends HominusSapiens> type, Level level) {
        super(type, level);
        this.xpReward = 12;
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 32.0)
                .add(Attributes.ARMOR, 2.0)
                .add(Attributes.ATTACK_DAMAGE, 3.0)
                .add(Attributes.MOVEMENT_SPEED, 0.27)
                .add(Attributes.FOLLOW_RANGE, 32.0);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(1, new RetreatGoal());
        goalSelector.addGoal(2, new BlasterAttackGoal(this));
        goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 0.8));
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
        builder.define(AIMING, false);
    }

    public boolean isAiming() {
        return entityData.get(AIMING);
    }

    void setAiming(boolean aiming) {
        entityData.set(AIMING, aiming);
    }

    boolean isRetreating() {
        return retreatTicks > 0;
    }

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
        if (hurt && isAlive() && source.getEntity() instanceof LivingEntity attacker) {
            if (callCooldown <= 0) {
                // a crackle on its radio: every idle Oinstein mob nearby comes running
                OinsteinForces.rally(level, this, attacker, 24.0);
                level.playSound(null, getX(), getY(), getZ(), SoundEvents.NOTE_BLOCK_BIT.value(), SoundSource.HOSTILE, 1.0F, 0.5F);
                level.playSound(null, getX(), getY(), getZ(), SoundEvents.NOTE_BLOCK_BIT.value(), SoundSource.HOSTILE, 1.0F, 0.8F);
                callCooldown = 100;
            }
            if (getHealth() < getMaxHealth() * RETREAT_FRACTION && retreatTicks <= 0) {
                retreatTicks = 80;
            }
        }
        return hurt;
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (callCooldown > 0) {
            callCooldown--;
        }
        if (retreatTicks > 0) {
            retreatTicks--;
        }
    }

    @Override
    public void tick() {
        super.tick();
        if (level().isClientSide()) {
            aimO = aim;
            aim = Mth.approach(aim, isAiming() ? 1.0F : 0.0F, 0.2F);
        }
    }

    public float aimAmount(float partialTick) {
        return Mth.lerp(partialTick, aimO, aim);
    }

    /** Falls back, away from its attacker, while it has little health left. */
    private class RetreatGoal extends Goal {
        RetreatGoal() {
            setFlags(java.util.EnumSet.of(Flag.MOVE));
        }

        @Override
        public boolean canUse() {
            return retreatTicks > 0 && getTarget() != null;
        }

        @Override
        public void start() {
            setAiming(false);
            flee();
        }

        @Override
        public void tick() {
            if (getNavigation().isDone()) {
                flee();
            }
        }

        private void flee() {
            LivingEntity from = getTarget();
            if (from == null) {
                return;
            }
            Vec3 pos = DefaultRandomPos.getPosAway(HominusSapiens.this, 16, 7, from.position());
            if (pos != null) {
                getNavigation().moveTo(pos.x, pos.y, pos.z, 1.35);
            }
        }
    }

    @Override
    protected SoundEvent getAmbientSound() {
        return SoundEvents.VILLAGER_AMBIENT;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.VILLAGER_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.VILLAGER_DEATH;
    }

    /** A thin, reedy voice - too much brain, too little chest. */
    @Override
    public float getVoicePitch() {
        return 1.35F + (random.nextFloat() - random.nextFloat()) * 0.1F;
    }
}
