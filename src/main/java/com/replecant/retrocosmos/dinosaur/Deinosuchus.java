package com.replecant.retrocosmos.dinosaur;

import java.util.EnumSet;
import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.FluidTags;
import net.minecraft.util.Mth;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.MoverType;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.control.SmoothSwimmingLookControl;
import net.minecraft.world.entity.ai.control.SmoothSwimmingMoveControl;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.RandomSwimmingGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.ai.navigation.AmphibiousPathNavigation;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.pathfinder.PathType;
import net.minecraft.world.phys.Vec3;

/**
 * Deinosuchus: the four-block crocodile of the fern swamp, an ambush predator. It lies in the water with only its
 * eyes and nostrils showing; anything that comes to the water's edge - or swims - within reach gets a lunge, a
 * crushing bite and a drag toward the water. On land it is slow and soon slides back in; it never hunts inland.
 */
public class Deinosuchus extends Monster implements DinosaurAnimated {
    private static final EntityDataAccessor<Integer> LUNGE = SynchedEntityData.defineId(Deinosuchus.class, EntityDataSerializers.INT);
    static final int LUNGE_TICKS = 12;
    /** How far from the water a victim may stand and still be grabbed. */
    static final int SHORE_REACH = 4;

    private int lungeClient;
    private int lungeClientO;
    int landTicks;

    public Deinosuchus(EntityType<? extends Deinosuchus> type, Level level) {
        super(type, level);
        this.moveControl = new SmoothSwimmingMoveControl(this, 85, 10, 0.12F, 0.35F, false);
        this.lookControl = new SmoothSwimmingLookControl(this, 20);
        this.xpReward = 12;
        setPathfindingMalus(PathType.WATER, 0.0F);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 70.0)
                .add(Attributes.MOVEMENT_SPEED, 0.6)
                .add(Attributes.ATTACK_DAMAGE, 12.0)
                .add(Attributes.ARMOR, 8.0)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.7)
                .add(Attributes.FOLLOW_RANGE, 16.0)
                .add(Attributes.STEP_HEIGHT, 1.0);
    }

    @Override
    protected PathNavigation createNavigation(Level level) {
        return new AmphibiousPathNavigation(this, level);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(1, new AmbushGoal(this));
        goalSelector.addGoal(2, new ReturnToWaterGoal(this));
        goalSelector.addGoal(5, new RandomSwimmingGoal(this, 0.6, 160));
        targetSelector.addGoal(1, new HurtByTargetGoal(this));
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, LivingEntity.class, 5, true, false,
                (target, level) -> canAmbush(target)));
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(LUNGE, 0);
    }

    /** Water within reach of a position (the victim is at, or near, the water's edge). */
    boolean nearWater(BlockPos pos, int radius) {
        Level level = level();
        for (BlockPos p : BlockPos.betweenClosed(pos.offset(-radius, -2, -radius), pos.offset(radius, 1, radius))) {
            if (level.getFluidState(p).is(FluidTags.WATER)) {
                return true;
            }
        }
        return false;
    }

    /** Players and animals at the water's edge or swimming nearby, while it lies in wait in the water. */
    boolean canAmbush(LivingEntity target) {
        if (!isInWater() || target instanceof Deinosuchus || !(target instanceof Player || target instanceof Animal)) {
            return false;
        }
        return distanceToSqr(target) < 7.0 * 7.0 && (target.isInWater() || nearWater(target.blockPosition(), SHORE_REACH));
    }

    void startLunge() {
        entityData.set(LUNGE, entityData.get(LUNGE) + 1);
    }

    @Override
    public void onSyncedDataUpdated(EntityDataAccessor<?> key) {
        super.onSyncedDataUpdated(key);
        if (LUNGE.equals(key) && level().isClientSide()) {
            lungeClient = LUNGE_TICKS;
            lungeClientO = LUNGE_TICKS;
        }
    }

    @Override
    public float lungeAmount(float partialTick) {
        float left = Mth.lerp(partialTick, lungeClientO, lungeClient);
        return left <= 0.0F ? 0.0F : Mth.sin((1.0F - left / LUNGE_TICKS) * Mth.PI);
    }

    @Override
    public void tick() {
        super.tick();
        if (level().isClientSide()) {
            lungeClientO = lungeClient;
            if (lungeClient > 0) {
                lungeClient--;
            }
        }
    }

    @Override
    public void aiStep() {
        super.aiStep();
        if (level().isClientSide()) {
            return;
        }
        landTicks = isInWater() ? 0 : landTicks + 1;
        if (isInWater() && getTarget() == null) {
            // lurk: float so that just the eyes and nostrils break the surface
            BlockPos.MutableBlockPos p = blockPosition().mutable();
            int up = 0;
            while (up < 8 && level().getFluidState(p.above()).is(FluidTags.WATER)) {
                p.move(0, 1, 0);
                up++;
            }
            double surface = p.getY() + level().getFluidState(p).getHeight(level(), p);
            double want = surface - 0.42;  // eye height is 0.6: eyes and nostrils just break the surface
            Vec3 v = getDeltaMovement();
            setDeltaMovement(v.x * 0.9, Mth.clamp((want - getY()) * 0.2, -0.06, 0.06), v.z * 0.9);
        }
    }

    @Override
    protected void travelInWater(Vec3 input, double gravity, boolean falling, double oldY) {
        moveRelative(getSpeed(), input);
        move(MoverType.SELF, getDeltaMovement());
        setDeltaMovement(getDeltaMovement().scale(0.9));
    }

    @Override
    public boolean canBreatheUnderwater() {
        return true;
    }

    @Override
    public float getWalkTargetValue(BlockPos pos, LevelReader level) {
        return level.getFluidState(pos).is(FluidTags.WATER) ? 10.0F : 0.0F;
    }

    @Override
    public int getMaxSpawnClusterSize() {
        return 1;
    }

    @Override
    protected SoundEvent getAmbientSound() {
        return isInWater() ? null : SoundEvents.HOGLIN_AMBIENT;
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
        playSound(SoundEvents.TURTLE_SHAMBLE, 0.5F, 0.6F);
    }

    @Override
    public float getVoicePitch() {
        return 0.5F + (random.nextFloat() - random.nextFloat()) * 0.05F;
    }

    /** Close in under water, then burst out: lunge, bite, hold and drag the victim back toward the water. */
    static final class AmbushGoal extends Goal {
        private static final double LUNGE_RANGE = 3.5;
        private final Deinosuchus croc;
        private int cooldown;
        private int lunging;
        private int holding;

        AmbushGoal(Deinosuchus croc) {
            this.croc = croc;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        private boolean targetInReach(LivingEntity t) {
            return t.isAlive() && croc.distanceToSqr(t) < 12.0 * 12.0
                    && (t.isInWater() || croc.nearWater(t.blockPosition(), SHORE_REACH)) && croc.landTicks < 60;
        }

        @Override
        public boolean canUse() {
            LivingEntity t = croc.getTarget();
            return t != null && targetInReach(t);
        }

        @Override
        public boolean canContinueToUse() {
            LivingEntity t = croc.getTarget();
            boolean ok = t != null && targetInReach(t);
            if (!ok && t != null && holding <= 0) {
                croc.setTarget(null);  // it never chases inland
            }
            return ok || holding > 0;
        }

        @Override
        public void stop() {
            lunging = holding = 0;
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }

        @Override
        public void tick() {
            LivingEntity target = croc.getTarget();
            if (target == null) {
                holding = 0;
                return;
            }
            croc.getLookControl().setLookAt(target, 30.0F, 30.0F);
            if (cooldown > 0) {
                cooldown--;
            }
            if (holding > 0) {
                // the drag: pull the victim toward the jaws and the water
                holding--;
                Vec3 pull = croc.position().subtract(target.position()).normalize().scale(0.12);
                target.setDeltaMovement(target.getDeltaMovement().multiply(0.5, 1.0, 0.5).add(pull.x, 0.0, pull.z));
                target.hurtMarked = true;
                return;
            }
            double dist = croc.distanceTo(target);
            if (lunging > 0) {
                lunging--;
                if (croc.getBoundingBox().inflate(0.6).intersects(target.getBoundingBox()) && croc.level() instanceof ServerLevel level) {
                    if (croc.doHurtTarget(level, target)) {
                        croc.playSound(SoundEvents.EVOKER_FANGS_ATTACK, 1.4F, 0.6F);
                        target.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 50, 3), croc);
                        holding = 20;
                    }
                    lunging = 0;
                    cooldown = 30;
                }
                return;
            }
            if (dist < LUNGE_RANGE && cooldown <= 0) {
                Vec3 dir = target.position().subtract(croc.position()).normalize();
                croc.setDeltaMovement(dir.x * 0.9, 0.25 + Math.max(0.0, dir.y) * 0.4, dir.z * 0.9);
                croc.startLunge();
                croc.playSound(SoundEvents.GENERIC_SPLASH, 1.0F, 0.8F);
                lunging = 10;
            } else {
                croc.getNavigation().moveTo(target, croc.isInWater() ? 1.6 : 0.8);
            }
        }
    }

    /** Out of the water with nothing to bite: back in, to the nearest water around. */
    static final class ReturnToWaterGoal extends Goal {
        private final Deinosuchus croc;
        @Nullable
        private BlockPos water;

        ReturnToWaterGoal(Deinosuchus croc) {
            this.croc = croc;
            setFlags(EnumSet.of(Flag.MOVE));
        }

        @Override
        public boolean canUse() {
            if (croc.isInWater() || croc.getTarget() != null && croc.landTicks < 60) {
                return false;
            }
            water = null;
            for (int i = 0; i < 40 && water == null; i++) {
                BlockPos p = croc.blockPosition().offset(croc.getRandom().nextInt(25) - 12, croc.getRandom().nextInt(7) - 4,
                        croc.getRandom().nextInt(25) - 12);
                if (croc.level().getFluidState(p).is(FluidTags.WATER)) {
                    water = p;
                }
            }
            return water != null;
        }

        @Override
        public boolean canContinueToUse() {
            return water != null && !croc.isInWater() && !croc.getNavigation().isDone();
        }

        @Override
        public void start() {
            if (water != null) {
                croc.getNavigation().moveTo(water.getX() + 0.5, water.getY(), water.getZ() + 0.5, 1.0);
            }
        }
    }
}
