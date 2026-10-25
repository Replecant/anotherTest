package com.replecant.retrocosmos.dinosaur;

import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.BlockTags;
import net.minecraft.util.Mth;
import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.SpawnGroupData;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.control.MoveControl;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.ai.navigation.FlyingPathNavigation;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;

/**
 * Pteranodon: a leather-winged flier that roosts on the very tops of the giant Venus trees and wheels over the
 * jungle. It ignores people on the ground, but climb up to its roost - or hit it - and it screeches and stoops on
 * you, pecking and buffeting, before it flaps back to its perch.
 */
public class Pteranodon extends PathfinderMob implements DinosaurAnimated {
    private static final EntityDataAccessor<Boolean> PERCHED = SynchedEntityData.defineId(Pteranodon.class, EntityDataSerializers.BOOLEAN);
    private static final EntityDataAccessor<Boolean> DIVING = SynchedEntityData.defineId(Pteranodon.class, EntityDataSerializers.BOOLEAN);
    /** How close (blocks) an intruder up in the canopy may come to the roost. */
    static final double TERRITORY = 8.0;
    /** A roost has to be at least this far above the jungle floor. */
    private static final int MIN_PERCH_HEIGHT = 7;

    private final Smoothed perch = new Smoothed(0.08F);
    private final Smoothed dive = new Smoothed(0.15F);
    private float pitch;
    private float pitchO;
    /** Centre of its home range: the last roost. */
    @Nullable
    private BlockPos anchor;
    int flightTicks;
    private int perchTicks;
    private int perchDuration = 800;

    public Pteranodon(EntityType<? extends Pteranodon> type, Level level) {
        super(type, level);
        this.moveControl = new FlightControl(this);
        this.xpReward = 5;
        setNoGravity(true);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return PathfinderMob.createMobAttributes()
                .add(Attributes.MAX_HEALTH, 20.0)
                .add(Attributes.MOVEMENT_SPEED, 0.3)
                .add(Attributes.FLYING_SPEED, 0.6)
                .add(Attributes.ATTACK_DAMAGE, 4.0)
                .add(Attributes.ATTACK_KNOCKBACK, 1.2)
                .add(Attributes.FOLLOW_RANGE, 32.0);
    }

    @Override
    protected PathNavigation createNavigation(Level level) {
        return new FlyingPathNavigation(this, level);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(1, new PteranodonGoals.Stoop(this));
        goalSelector.addGoal(3, new PteranodonGoals.Roost(this));
        goalSelector.addGoal(5, new PteranodonGoals.Circle(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this).setAlertOthers());
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, 10, false, false,
                (target, level) -> isIntruder(target)));
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(PERCHED, false);
        builder.define(DIVING, false);
    }

    public boolean isPerched() {
        return entityData.get(PERCHED);
    }

    void setDiving(boolean diving) {
        entityData.set(DIVING, diving);
    }

    /** Settles on the block below (folding the wings) or takes off from it. */
    void setPerched(boolean perched) {
        entityData.set(PERCHED, perched);
        if (perched) {
            setNoGravity(false);
            setDeltaMovement(Vec3.ZERO);
            getNavigation().stop();
            perchTicks = 0;
            perchDuration = 600 + random.nextInt(1400);
            anchor = blockPosition();
        } else {
            setNoGravity(true);
            flightTicks = 0;
            setDeltaMovement(getDeltaMovement().add(0.0, 0.45, 0.0));
            playSound(SoundEvents.PHANTOM_FLAP, 1.0F, 0.7F);
        }
    }

    BlockPos anchor() {
        if (anchor == null) {
            anchor = blockPosition();
        }
        return anchor;
    }

    void setAnchor(BlockPos pos) {
        anchor = pos;
    }

    static boolean isCanopy(BlockState state) {
        return state.is(BlockTags.LEAVES) || state.is(BlockTags.LOGS);
    }

    /** A player up in the treetops, near the roost. People down on the jungle floor are ignored. */
    private boolean isIntruder(LivingEntity target) {
        BlockPos home = anchor();
        return target.distanceToSqr(Vec3.atCenterOf(home)) < TERRITORY * TERRITORY && target.getY() > home.getY() - 4.0;
    }

    /** Height of the canopy top above the jungle floor at this column (0 if it isn't canopy). */
    int canopyHeight(BlockPos top) {
        Level level = level();
        if (!isCanopy(level.getBlockState(top))) {
            return 0;
        }
        BlockPos.MutableBlockPos p = top.mutable();
        int depth = 0;
        while (depth < 48 && p.getY() > level.getMinY()) {
            p.move(0, -1, 0);
            BlockState s = level.getBlockState(p);
            if (!s.isAir() && !isCanopy(s) && s.isSolid()) {
                return depth;
            }
            depth++;
        }
        return depth;
    }

    /** Looks for a high treetop to sit on: leaves or logs with open air above, well above the floor. */
    @Nullable
    BlockPos findPerch(BlockPos around, int radius) {
        BlockPos best = null;
        for (int i = 0; i < 40; i++) {
            int x = around.getX() + random.nextInt(radius * 2 + 1) - radius;
            int z = around.getZ() + random.nextInt(radius * 2 + 1) - radius;
            if (!level().hasChunkAt(new BlockPos(x, around.getY(), z))) {
                continue;
            }
            int top = level().getHeight(Heightmap.Types.MOTION_BLOCKING, x, z);
            BlockPos below = new BlockPos(x, top - 1, z);
            if (canopyHeight(below) >= MIN_PERCH_HEIGHT && (best == null || below.getY() > best.getY())) {
                best = below;
            }
        }
        return best;
    }

    @Override
    public void tick() {
        super.tick();
        if (level().isClientSide()) {
            perch.tick(isPerched());
            dive.tick(entityData.get(DIVING));
            pitchO = pitch;
            double dx = getX() - xo;
            double dz = getZ() - zo;
            double dy = getY() - yo;
            float wanted = isPerched() ? 0.0F : (float) Mth.clamp(-Mth.atan2(dy, Math.sqrt(dx * dx + dz * dz) + 0.05), -0.9, 1.2);
            pitch += (wanted - pitch) * 0.2F;
        }
    }

    @Override
    public void aiStep() {
        super.aiStep();
        if (level().isClientSide()) {
            return;
        }
        if (isPerched()) {
            perchTicks++;
            setDeltaMovement(0.0, getDeltaMovement().y, 0.0);
            boolean roostGone = onGround() && !isCanopy(level().getBlockState(blockPosition().below()));
            if (roostGone || perchTicks > perchDuration && getTarget() == null || isInWater()) {
                setPerched(false);
            }
        } else {
            flightTicks++;
            if (onGround()) {
                if (getTarget() == null && canopyHeight(blockPosition().below()) >= MIN_PERCH_HEIGHT - 2) {
                    setPerched(true);
                } else {
                    // never walks: bounced off the ground, flap back up
                    setDeltaMovement(getDeltaMovement().add(0.0, 0.3, 0.0));
                }
            }
            if (flightTicks % 18 == 0) {
                playSound(SoundEvents.PHANTOM_FLAP, 0.5F, 0.8F + random.nextFloat() * 0.2F);
            }
        }
    }

    @Override
    public float perchAmount(float partialTick) {
        return perch.get(partialTick);
    }

    @Override
    public float diveAmount(float partialTick) {
        return dive.get(partialTick);
    }

    @Override
    public float flightPitch(float partialTick) {
        return Mth.lerp(partialTick, pitchO, pitch);
    }

    @Override
    public boolean doHurtTarget(ServerLevel level, Entity target) {
        boolean hit = super.doHurtTarget(level, target);
        if (hit) {
            playSound(SoundEvents.PHANTOM_BITE, 1.0F, 0.8F);
        }
        return hit;
    }

    @Override
    public void setTarget(@Nullable LivingEntity target) {
        if (target != null && getTarget() == null) {
            playSound(SoundEvents.PHANTOM_SWOOP, 1.6F, 0.75F);
        }
        super.setTarget(target);
    }

    @Override
    public boolean causeFallDamage(double distance, float multiplier, DamageSource source) {
        return false;
    }

    @Override
    public boolean removeWhenFarAway(double distance) {
        return false;
    }

    @Override
    public int getMaxSpawnClusterSize() {
        return 3;
    }

    @Nullable
    @Override
    public SpawnGroupData finalizeSpawn(ServerLevelAccessor level, DifficultyInstance difficulty, EntitySpawnReason reason,
                                        @Nullable SpawnGroupData data) {
        anchor = blockPosition();
        if (isCanopy(level.getBlockState(blockPosition().below()))) {
            setPerched(true);
        }
        return super.finalizeSpawn(level, difficulty, reason, data);
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putBoolean("Perched", isPerched());
        output.putLong("Roost", anchor().asLong());
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        entityData.set(PERCHED, input.getBooleanOr("Perched", false));
        input.getLong("Roost").ifPresent(l -> anchor = BlockPos.of(l));
        setNoGravity(!isPerched());
    }

    @Override
    protected SoundEvent getAmbientSound() {
        return SoundEvents.PHANTOM_AMBIENT;
    }

    @Override
    public int getAmbientSoundInterval() {
        return 200;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.PHANTOM_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.PHANTOM_DEATH;
    }

    @Override
    public float getVoicePitch() {
        return 0.75F + (random.nextFloat() - random.nextFloat()) * 0.1F;
    }

    /** Steers straight at the wanted point (like the vex): fliers over an open canopy need no path. */
    static class FlightControl extends MoveControl {
        private final Pteranodon ptero;

        FlightControl(Pteranodon ptero) {
            super(ptero);
            this.ptero = ptero;
        }

        @Override
        public void tick() {
            if (ptero.isPerched()) {
                operation = Operation.WAIT;
                return;
            }
            if (operation == Operation.MOVE_TO) {
                Vec3 to = new Vec3(wantedX - ptero.getX(), wantedY - ptero.getY(), wantedZ - ptero.getZ());
                double len = to.length();
                if (len < 0.6) {
                    operation = Operation.WAIT;
                    ptero.setDeltaMovement(ptero.getDeltaMovement().scale(0.6));
                } else {
                    ptero.setDeltaMovement(ptero.getDeltaMovement().add(to.scale(speedModifier * 0.05 / len)));
                    Vec3 v = ptero.getDeltaMovement();
                    if (v.horizontalDistanceSqr() > 1.0E-4) {
                        float yaw = (float) (Mth.atan2(v.z, v.x) * Mth.RAD_TO_DEG) - 90.0F;
                        ptero.setYRot(rotlerp(ptero.getYRot(), yaw, 12.0F));
                        ptero.yBodyRot = ptero.getYRot();
                    }
                }
            } else {
                // gliding: hold height, bleed off speed slowly
                Vec3 v = ptero.getDeltaMovement();
                ptero.setDeltaMovement(v.x * 0.98, v.y * 0.8, v.z * 0.98);
            }
        }
    }
}
