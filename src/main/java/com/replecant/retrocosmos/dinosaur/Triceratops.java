package com.replecant.retrocosmos.dinosaur;

import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.AgeableMob;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.SpawnGroupData;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.BreedGoal;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.FollowParentGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.PanicGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.TemptGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.block.state.BlockState;

/**
 * Triceratops: a horned herbivore, neutral. Leave it be and it grazes with its herd; hit it - or walk up to one
 * of its calves - and it lowers its horns, paws the ground and charges. Calms down again after a while.
 */
public class Triceratops extends Animal implements DinosaurAnimated {
    /** 0 = calm, 1 = pawing the ground before a charge, 2 = charging. */
    private static final EntityDataAccessor<Integer> CHARGE = SynchedEntityData.defineId(Triceratops.class, EntityDataSerializers.INT);
    public static final int CALM = 0;
    public static final int WINDUP = 1;
    public static final int CHARGING = 2;

    private static final int ANGER_TICKS = 20 * 20;
    private static final double CALF_GUARD_RANGE = 5.0;

    private final Smoothed charge = new Smoothed(0.15F);
    private int angerTicks;

    public Triceratops(EntityType<? extends Triceratops> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Animal.createAnimalAttributes()
                .add(Attributes.MAX_HEALTH, 60.0)
                .add(Attributes.MOVEMENT_SPEED, 0.22)
                .add(Attributes.ATTACK_DAMAGE, 8.0)
                .add(Attributes.ATTACK_KNOCKBACK, 1.6)
                .add(Attributes.ARMOR, 6.0)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.6)
                .add(Attributes.STEP_HEIGHT, 1.1)
                .add(Attributes.FOLLOW_RANGE, 24.0);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(1, new TriceratopsChargeGoal(this));
        goalSelector.addGoal(1, new PanicGoal(this, 1.6) {
            @Override
            public boolean canUse() {
                return Triceratops.this.isBaby() && super.canUse();
            }
        });
        goalSelector.addGoal(2, new BreedGoal(this, 1.0));
        goalSelector.addGoal(3, new TemptGoal(this, 1.15, this::isFood, false));
        goalSelector.addGoal(4, new FollowParentGoal(this, 1.15));
        goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 0.85));
        goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 10.0F));
        goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        // the herd rallies when one of them is hurt - the adults, that is; calves stay out of it
        targetSelector.addGoal(1, new HurtByTargetGoal(this) {
            @Override
            protected void alertOther(Mob mob, LivingEntity target) {
                if (!mob.isBaby()) {
                    super.alertOther(mob, target);
                }
            }
        }.setAlertOthers());
        // a player crowding one of the herd's calves gets the horns
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, 10, true, false,
                (target, level) -> !isBaby() && isNearCalf(target)));
    }

    private boolean isNearCalf(LivingEntity target) {
        return !level().getEntitiesOfClass(Triceratops.class, target.getBoundingBox().inflate(CALF_GUARD_RANGE),
                t -> t.isBaby() && t.isAlive() && t.distanceToSqr(this) < 16.0 * 16.0).isEmpty();
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(CHARGE, CALM);
    }

    public int chargeState() {
        return entityData.get(CHARGE);
    }

    void setChargeState(int state) {
        entityData.set(CHARGE, state);
    }

    @Override
    public void setTarget(@Nullable LivingEntity target) {
        if (target != null && getTarget() == null) {
            angerTicks = 0;
        }
        super.setTarget(target);
    }

    @Override
    public void tick() {
        super.tick();
        if (level().isClientSide()) {
            charge.tick(chargeState() != CALM);
        }
    }

    /** Neutral, not vengeful: the anger fades once nobody has hurt it for a while. */
    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (getTarget() != null) {
            angerTicks++;
            boolean recentlyHurt = tickCount - getLastHurtByMobTimestamp() < ANGER_TICKS;
            if (angerTicks > ANGER_TICKS && !recentlyHurt && !isNearCalf(getTarget())) {
                setTarget(null);
                setLastHurtByMob(null);
            }
        }
    }

    @Override
    public float chargeAmount(float partialTick) {
        return charge.get(partialTick);
    }

    @Override
    public boolean isWindingUp() {
        return chargeState() == WINDUP;
    }

    @Override
    public boolean isFood(ItemStack stack) {
        return stack.is(Items.FERN) || stack.is(Items.LARGE_FERN);
    }

    @Nullable
    @Override
    public AgeableMob getBreedOffspring(ServerLevel level, AgeableMob partner) {
        return ModDinosaurs.TRICERATOPS.get().create(level, EntitySpawnReason.BREEDING);
    }

    /** Herds come with calves more often than vanilla animals do. */
    @Nullable
    @Override
    public SpawnGroupData finalizeSpawn(ServerLevelAccessor level, DifficultyInstance difficulty, EntitySpawnReason reason,
                                        @Nullable SpawnGroupData data) {
        if (data == null) {
            data = new AgeableMob.AgeableMobGroupData(0.25F);
        }
        return super.finalizeSpawn(level, difficulty, reason, data);
    }

    @Override
    protected SoundEvent getAmbientSound() {
        return SoundEvents.POLAR_BEAR_AMBIENT;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.POLAR_BEAR_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.POLAR_BEAR_DEATH;
    }

    @Override
    protected void playStepSound(BlockPos pos, BlockState state) {
        playSound(SoundEvents.POLAR_BEAR_STEP, 0.35F, 0.7F);
    }

    @Override
    public float getVoicePitch() {
        return (isBaby() ? 1.3F : 0.7F) + (random.nextFloat() - random.nextFloat()) * 0.08F;
    }
}
