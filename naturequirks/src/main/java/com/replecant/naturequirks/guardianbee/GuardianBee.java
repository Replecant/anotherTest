package com.replecant.naturequirks.guardianbee;

import java.util.EnumSet;
import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.Difficulty;
import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.SpawnGroupData;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.control.FlyingMoveControl;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.ai.navigation.FlyingPathNavigation;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.entity.animal.FlyingAnimal;
import net.minecraft.world.entity.animal.bee.Bee;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;

/**
 * Guardian Bee: the soldier of a giant hive. It patrols around the spot it was placed (its home), attacks players who
 * come within 16 blocks of home, chases them up to 32 blocks out and then flies back. Its sting hurts and poisons -
 * and, unlike a worker bee, it lives to sting again. It never turns on bees, and when it is attacked (or picks a
 * fight) every bee around joins in.
 */
public class GuardianBee extends Monster implements FlyingAnimal {
    /** Players closer than this to home are intruders. */
    public static final double GUARD_RADIUS = 16.0;
    /** It gives up the chase this far from home. */
    public static final double LEASH = 32.0;
    private static final int STING_INTERVAL = 30;

    @Nullable
    private BlockPos home;
    /** Stings landed (for tests and the curious). */
    private int stings;

    public GuardianBee(EntityType<? extends GuardianBee> type, Level level) {
        super(type, level);
        this.moveControl = new FlyingMoveControl(this, 20, true);
        this.xpReward = 6;
    }

    /**
     * Spawns a guardian bee guarding {@code pos} (the hive agent's hook: hive hearts call this when the hive is
     * disturbed). Returns the bee, or null if it could not be created.
     */
    @Nullable
    public static GuardianBee spawn(ServerLevel level, BlockPos pos) {
        GuardianBee bee = GuardianBees.GUARDIAN_BEE.get().create(level, EntitySpawnReason.MOB_SUMMONED);
        if (bee == null) {
            return null;
        }
        bee.snapTo(pos.getX() + 0.5, pos.getY() + 0.1, pos.getZ() + 0.5, level.getRandom().nextFloat() * 360.0F, 0.0F);
        bee.finalizeSpawn(level, level.getCurrentDifficultyAt(pos), EntitySpawnReason.MOB_SUMMONED, null);
        bee.setHome(pos);
        level.addFreshEntity(bee);
        return bee;
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 20.0)
                .add(Attributes.ARMOR, 4.0)
                .add(Attributes.FLYING_SPEED, 0.7)
                .add(Attributes.MOVEMENT_SPEED, 0.32)
                .add(Attributes.ATTACK_DAMAGE, 4.0)
                .add(Attributes.FOLLOW_RANGE, 40.0);
    }

    @Override
    protected PathNavigation createNavigation(Level level) {
        FlyingPathNavigation nav = new FlyingPathNavigation(this, level);
        nav.setCanOpenDoors(false);
        nav.setCanFloat(false);
        return nav;
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(1, new StingGoal(this));
        goalSelector.addGoal(2, new ReturnHomeGoal(this));
        goalSelector.addGoal(3, new PatrolGoal(this));
        goalSelector.addGoal(4, new LookAtPlayerGoal(this, Player.class, 8.0F));
        goalSelector.addGoal(5, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this).setAlertOthers());
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, 10, true, false,
                (target, level) -> target.distanceToSqr(Vec3.atCenterOf(home())) < GUARD_RADIUS * GUARD_RADIUS));
    }

    public int stings() {
        return stings;
    }

    public BlockPos home() {
        if (home == null) {
            home = blockPosition();
        }
        return home;
    }

    public void setHome(BlockPos pos) {
        home = pos.immutable();
    }

    @Nullable
    @Override
    public SpawnGroupData finalizeSpawn(ServerLevelAccessor level, DifficultyInstance difficulty, EntitySpawnReason reason,
                                        @Nullable SpawnGroupData data) {
        if (home == null) {
            home = blockPosition();
        }
        return super.finalizeSpawn(level, difficulty, reason, data);
    }

    @Override
    public boolean isFlying() {
        return !onGround();
    }

    /** Bees are family: never a target. */
    @Override
    public boolean canAttack(LivingEntity target) {
        return !(target instanceof Bee) && !(target instanceof GuardianBee) && super.canAttack(target);
    }

    @Override
    public void setTarget(@Nullable LivingEntity target) {
        LivingEntity old = getTarget();
        if (target != null && (target instanceof Bee || target instanceof GuardianBee)) {
            return;
        }
        super.setTarget(target);
        if (target != null && target != old) {
            rouseBees(target);
            playSound(SoundEvents.BEE_LOOP_AGGRESSIVE, 0.9F, 0.7F);
        }
    }

    /** Every worker bee nearby joins the fight against {@code enemy}. */
    void rouseBees(LivingEntity enemy) {
        if (!(level() instanceof ServerLevel) || enemy instanceof Player p && (p.isCreative() || p.isSpectator())) {
            return;
        }
        for (Bee bee : level().getEntitiesOfClass(Bee.class, getBoundingBox().inflate(12.0))) {
            if (bee.getTarget() == null) {
                bee.setTarget(enemy);
            }
        }
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        boolean hurt = super.hurtServer(level, source, amount);
        if (hurt && source.getEntity() instanceof LivingEntity attacker && !(attacker instanceof Bee) && !(attacker instanceof GuardianBee)) {
            rouseBees(attacker);
        }
        return hurt;
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        LivingEntity target = getTarget();
        if (target != null && (!target.isAlive() || target.distanceToSqr(Vec3.atCenterOf(home())) > LEASH * LEASH
                || distanceToSqr(Vec3.atCenterOf(home())) > LEASH * LEASH)) {
            setTarget(null);
            setLastHurtByMob(null);
        }
    }

    /** The sting: damage plus poison, and the bee survives it (unlike a worker bee). */
    @Override
    public boolean doHurtTarget(ServerLevel level, Entity target) {
        boolean hit = super.doHurtTarget(level, target);
        if (hit && target instanceof LivingEntity living) {
            Difficulty d = level.getDifficulty();
            int seconds = d == Difficulty.HARD ? 18 : d == Difficulty.NORMAL ? 10 : 5;
            living.addEffect(new MobEffectInstance(MobEffects.POISON, seconds * 20, 0), this);
            playSound(SoundEvents.BEE_STING, 1.0F, 0.75F);
            stings++;
        }
        return hit;
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
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putLong("Home", home().asLong());
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        input.getLong("Home").ifPresent(l -> home = BlockPos.of(l));
    }

    @Override
    protected SoundEvent getAmbientSound() {
        return isAggressive() ? SoundEvents.BEE_LOOP_AGGRESSIVE : SoundEvents.BEE_LOOP;
    }

    @Override
    public int getAmbientSoundInterval() {
        return 50;
    }

    @Override
    protected float getSoundVolume() {
        return 0.6F;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.BEE_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.BEE_DEATH;
    }

    @Override
    public float getVoicePitch() {
        return 0.72F + (random.nextFloat() - random.nextFloat()) * 0.05F;
    }

    /** Melee with a sting every 1.5 s. */
    static final class StingGoal extends MeleeAttackGoal {
        StingGoal(GuardianBee bee) {
            super(bee, 1.4, true);
        }

        @Override
        protected int getAttackInterval() {
            return adjustedTickDelay(STING_INTERVAL);
        }
    }

    /** Fly back to the hive when there's nothing to fight. */
    static final class ReturnHomeGoal extends Goal {
        private final GuardianBee bee;
        private int repath;

        ReturnHomeGoal(GuardianBee bee) {
            this.bee = bee;
            setFlags(EnumSet.of(Flag.MOVE));
        }

        @Override
        public boolean canUse() {
            return bee.getTarget() == null && bee.distanceToSqr(Vec3.atCenterOf(bee.home())) > 10.0 * 10.0;
        }

        @Override
        public boolean canContinueToUse() {
            return bee.getTarget() == null && bee.distanceToSqr(Vec3.atCenterOf(bee.home())) > 4.0 * 4.0;
        }

        @Override
        public void start() {
            repath = 0;
        }

        @Override
        public void tick() {
            if (--repath <= 0) {
                repath = 40;
                BlockPos h = bee.home();
                if (!bee.getNavigation().moveTo(h.getX() + 0.5, h.getY() + 1.0, h.getZ() + 0.5, 1.1)) {
                    bee.getMoveControl().setWantedPosition(h.getX() + 0.5, h.getY() + 1.0, h.getZ() + 0.5, 1.1);
                }
            }
        }
    }

    /** Buzz about near home, like a worker bee near its nest. */
    static final class PatrolGoal extends Goal {
        private final GuardianBee bee;

        PatrolGoal(GuardianBee bee) {
            this.bee = bee;
            setFlags(EnumSet.of(Flag.MOVE));
        }

        @Override
        public boolean canUse() {
            return bee.getTarget() == null && bee.getNavigation().isDone() && bee.getRandom().nextInt(10) == 0;
        }

        @Override
        public boolean canContinueToUse() {
            return bee.getTarget() == null && bee.getNavigation().isInProgress();
        }

        @Override
        public void start() {
            BlockPos h = bee.home();
            for (int i = 0; i < 10; i++) {
                BlockPos p = h.offset(bee.getRandom().nextInt(15) - 7, bee.getRandom().nextInt(6) - 2, bee.getRandom().nextInt(15) - 7);
                if (bee.level().isEmptyBlock(p) && bee.getNavigation().moveTo(p.getX() + 0.5, p.getY() + 0.5, p.getZ() + 0.5, 1.0)) {
                    return;
                }
            }
        }
    }
}
