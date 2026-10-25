package com.replecant.retrocosmos.dinosaur;

import java.util.EnumSet;
import net.minecraft.core.BlockPos;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.FluidTags;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MoverType;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.control.SmoothSwimmingLookControl;
import net.minecraft.world.entity.ai.control.SmoothSwimmingMoveControl;
import net.minecraft.world.entity.ai.goal.BreathAirGoal;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.RandomSwimmingGoal;
import net.minecraft.world.entity.ai.goal.TryFindWaterGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.entity.ai.navigation.WaterBoundPathNavigation;
import net.minecraft.world.entity.animal.fish.AbstractFish;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.phys.Vec3;

/**
 * Plesiosaur: the long-necked monster of the steaming sea. Glides through the water on four paddles, comes up to
 * breathe like a dolphin and sometimes rears its four-block neck out of the water to look around. Snaps up fish;
 * leaves people alone - unless hurt, when it bites and rams.
 */
public class Plesiosaur extends PathfinderMob implements DinosaurAnimated {
    private static final EntityDataAccessor<Boolean> PEEKING = SynchedEntityData.defineId(Plesiosaur.class, EntityDataSerializers.BOOLEAN);

    private final Smoothed peek = new Smoothed(0.04F);

    public Plesiosaur(EntityType<? extends Plesiosaur> type, Level level) {
        super(type, level);
        this.moveControl = new SmoothSwimmingMoveControl(this, 85, 10, 0.02F, 0.1F, true);
        this.lookControl = new SmoothSwimmingLookControl(this, 10);
        this.xpReward = 10;
    }

    public static AttributeSupplier.Builder createAttributes() {
        return PathfinderMob.createMobAttributes()
                .add(Attributes.MAX_HEALTH, 60.0)
                .add(Attributes.MOVEMENT_SPEED, 1.0)
                .add(Attributes.ATTACK_DAMAGE, 8.0)
                .add(Attributes.ATTACK_KNOCKBACK, 2.0)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.6)
                .add(Attributes.FOLLOW_RANGE, 24.0);
    }

    @Override
    protected PathNavigation createNavigation(Level level) {
        return new WaterBoundPathNavigation(this, level);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new BreathAirGoal(this));
        goalSelector.addGoal(0, new TryFindWaterGoal(this));
        goalSelector.addGoal(1, new MeleeAttackGoal(this, 1.3, true));
        goalSelector.addGoal(3, new PeekGoal(this));
        goalSelector.addGoal(4, new RandomSwimmingGoal(this, 1.0, 20));
        goalSelector.addGoal(5, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this).setAlertOthers());
        // a snack now and then
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, AbstractFish.class, 60, true, false, null));
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(PEEKING, false);
    }

    void setPeeking(boolean peeking) {
        entityData.set(PEEKING, peeking);
    }

    public boolean isPeeking() {
        return entityData.get(PEEKING);
    }

    @Override
    public void tick() {
        super.tick();
        if (level().isClientSide()) {
            peek.tick(isPeeking());
        }
    }

    /** Fish are quick: snap one up as soon as it is within reach of the jaws. */
    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (getTarget() instanceof AbstractFish fish && fish.isAlive() && distanceTo(fish) < 3.0 && tickCount % 10 == 0) {
            swing(net.minecraft.world.InteractionHand.MAIN_HAND);
            doHurtTarget(level, fish);
        }
    }

    @Override
    public float peekAmount(float partialTick) {
        return peek.get(partialTick);
    }

    /** Air-breather: five minutes under water before it has to come up. */
    @Override
    public int getMaxAirSupply() {
        return 6000;
    }

    @Override
    protected int increaseAirSupply(int air) {
        return getMaxAirSupply();
    }

    /** Swims like the dolphin: straight along the look direction, no sinking. */
    @Override
    protected void travelInWater(Vec3 input, double gravity, boolean falling, double oldY) {
        moveRelative(getSpeed(), input);
        move(MoverType.SELF, getDeltaMovement());
        setDeltaMovement(getDeltaMovement().scale(0.9));
        if (getTarget() == null && !isPeeking()) {
            setDeltaMovement(getDeltaMovement().add(0.0, -0.004, 0.0));
        }
    }

    @Override
    public boolean doHurtTarget(ServerLevel level, Entity target) {
        boolean hit = super.doHurtTarget(level, target);
        if (hit) {
            playSound(SoundEvents.DOLPHIN_ATTACK, 1.2F, 0.55F);
            if (target instanceof AbstractFish) {
                setTarget(null);
                heal(4.0F);
            }
        }
        return hit;
    }

    @Override
    public boolean canBeLeashed() {
        return false;
    }

    @Override
    public int getMaxHeadXRot() {
        return 1;
    }

    @Override
    public int getMaxHeadYRot() {
        return 1;
    }

    @Override
    public float getWalkTargetValue(BlockPos pos, LevelReader level) {
        return level.getFluidState(pos).is(FluidTags.WATER) ? 10.0F : -10.0F;
    }

    @Override
    public int getMaxSpawnClusterSize() {
        return 2;
    }

    @Override
    protected SoundEvent getAmbientSound() {
        return isInWater() ? SoundEvents.DOLPHIN_AMBIENT_WATER : SoundEvents.DOLPHIN_AMBIENT;
    }

    @Override
    public int getAmbientSoundInterval() {
        return 300;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.DOLPHIN_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.DOLPHIN_DEATH;
    }

    @Override
    protected SoundEvent getSwimSound() {
        return SoundEvents.DOLPHIN_SWIM;
    }

    @Override
    public float getVoicePitch() {
        return 0.45F + (random.nextFloat() - random.nextFloat()) * 0.05F;
    }

    /** Swim up to the surface, stop, and hold the neck high out of the water for a while. */
    static final class PeekGoal extends Goal {
        private final Plesiosaur plesio;
        private int ticks;

        PeekGoal(Plesiosaur plesio) {
            this.plesio = plesio;
            setFlags(EnumSet.of(Flag.MOVE, Flag.JUMP));
        }

        @Override
        public boolean canUse() {
            return plesio.getTarget() == null && plesio.isInWater() && plesio.getRandom().nextInt(reducedTickDelay(400)) == 0;
        }

        @Override
        public boolean canContinueToUse() {
            return ticks > 0 && plesio.getTarget() == null && plesio.isInWater();
        }

        @Override
        public void start() {
            ticks = adjustedTickDelay(160 + plesio.getRandom().nextInt(160));
            plesio.getNavigation().stop();
        }

        @Override
        public void stop() {
            plesio.setPeeking(false);
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }

        @Override
        public void tick() {
            ticks--;
            BlockPos head = BlockPos.containing(plesio.getX(), plesio.getY() + plesio.getBbHeight() + 0.2, plesio.getZ());
            boolean atSurface = !plesio.level().getFluidState(head).is(FluidTags.WATER);
            Vec3 v = plesio.getDeltaMovement();
            if (atSurface) {
                // hold position just under the surface, neck up
                plesio.setDeltaMovement(v.x * 0.8, v.y * 0.5, v.z * 0.8);
                plesio.setPeeking(true);
                plesio.setXRot(0.0F);
            } else {
                plesio.setDeltaMovement(v.x * 0.9, Math.min(0.12, v.y + 0.02), v.z * 0.9);
            }
        }
    }
}
