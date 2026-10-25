package com.replecant.retrocosmos.dinosaur.robot;

import com.replecant.retrocosmos.dinosaur.DinosaurAnimated;
import com.replecant.retrocosmos.tribe.Tribesman;
import java.util.EnumSet;
import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.util.Mth;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;

/**
 * Atomic Sentry: Dr. Oinstein's hovering guard drone. It floats two to four blocks up near its post, bobbing and
 * sweeping its red eye about; anyone not of the Doctor's making who comes into view gets an alarm beep and a
 * stream of blaster bolts. It never leaves its post. Dies in a pop of sparks.
 */
public class AtomicSentry extends Monster implements DinosaurAnimated {
    static final double SIGHT = 20.0;
    /** How far it may drift from its post. */
    private static final double LEASH = 6.0;

    @Nullable
    private BlockPos post;
    @Nullable
    private Vec3 hoverPoint;

    public AtomicSentry(EntityType<? extends AtomicSentry> type, Level level) {
        super(type, level);
        setNoGravity(true);
        this.xpReward = 10;
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 24.0)
                .add(Attributes.ARMOR, 4.0)
                .add(Attributes.MOVEMENT_SPEED, 0.2)
                .add(Attributes.FLYING_SPEED, 0.3)
                .add(Attributes.FOLLOW_RANGE, SIGHT);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(1, new FireGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this));
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
        targetSelector.addGoal(3, new NearestAttackableTargetGoal<>(this, Tribesman.class, true));
    }

    /** Never turns on the Doctor's other creatures, even after friendly fire. */
    @Override
    public boolean canAttack(LivingEntity target) {
        return !OinsteinForces.isMember(target) && super.canAttack(target);
    }

    BlockPos post() {
        if (post == null) {
            post = blockPosition();
        }
        return post;
    }

    /** Ground under its post (scans down so it works in caves and labs too, not just under open sky). */
    private int floorBelow(BlockPos from) {
        BlockPos.MutableBlockPos p = from.mutable();
        for (int i = 0; i < 12 && p.getY() > level().getMinY(); i++) {
            if (!level().getBlockState(p.below()).getCollisionShape(level(), p.below()).isEmpty()) {
                return p.getY();
            }
            p.move(0, -1, 0);
        }
        return from.getY() - 3;
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        BlockPos home = post();
        if (hoverPoint == null || position().distanceToSqr(hoverPoint) < 0.5 || random.nextInt(120) == 0) {
            double r = getTarget() == null ? LEASH - 1.0 : 1.5;
            double x = home.getX() + 0.5 + (random.nextDouble() * 2 - 1) * r;
            double z = home.getZ() + 0.5 + (random.nextDouble() * 2 - 1) * r;
            int floor = floorBelow(BlockPos.containing(x, home.getY() + 2, z));
            hoverPoint = new Vec3(x, floor + 2.0 + random.nextDouble() * 2.0, z);
        }
        // drift toward the hover point, never beyond the leash; bob gently
        Vec3 to = hoverPoint.subtract(position());
        Vec3 fromHome = position().subtract(Vec3.atBottomCenterOf(home)).multiply(1, 0, 1);
        if (fromHome.length() > LEASH) {
            to = to.add(fromHome.normalize().scale(-1.0));
        }
        double len = Math.max(0.01, to.length());
        double speed = 0.06;
        Vec3 v = getDeltaMovement();
        Vec3 want = to.scale(Math.min(speed, len) / len);
        setDeltaMovement(v.add((want.x - v.x) * 0.1, (want.y - v.y) * 0.1 + Mth.sin(tickCount * 0.12F) * 0.003, (want.z - v.z) * 0.1));
        if (getTarget() == null) {
            // the scan: the eye sweeps from side to side, the saucer slowly turns
            setYRot(getYRot() + 0.6F);
            yBodyRot = getYRot();
            yHeadRot = yBodyRot + Mth.sin(tickCount * 0.04F) * 70.0F;
        }
    }

    @Override
    public float getVoicePitch() {
        return 1.5F + (random.nextFloat() - random.nextFloat()) * 0.1F;
    }

    @Override
    public boolean canBeAffected(MobEffectInstance effect) {
        return !effect.is(MobEffects.POISON) && super.canBeAffected(effect);
    }

    @Override
    public boolean canBreatheUnderwater() {
        return true;
    }

    @Override
    public boolean causeFallDamage(double distance, float multiplier, DamageSource source) {
        return false;
    }

    @Override
    public int getMaxHeadYRot() {
        return 90;
    }

    /** A pop and a shower of sparks - no damage to the Doctor's walls. */
    @Override
    public void die(DamageSource source) {
        super.die(source);
        if (level() instanceof ServerLevel level) {
            level.explode(this, getX(), getY() + 0.4, getZ(), 1.0F, Level.ExplosionInteraction.NONE);
            level.sendParticles(ParticleTypes.ELECTRIC_SPARK, getX(), getY() + 0.4, getZ(), 40, 0.4, 0.4, 0.4, 0.4);
            level.sendParticles(ParticleTypes.LARGE_SMOKE, getX(), getY() + 0.4, getZ(), 8, 0.3, 0.3, 0.3, 0.02);
        }
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putLong("Post", post().asLong());
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        input.getLong("Post").ifPresent(l -> post = BlockPos.of(l));
        setNoGravity(true);
    }

    @Override
    protected SoundEvent getAmbientSound() {
        return SoundEvents.BEACON_AMBIENT;
    }

    @Override
    protected float getSoundVolume() {
        return 0.6F;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.IRON_GOLEM_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.IRON_GOLEM_DEATH;
    }

    /** Lock on, beep the alarm, and fire a bolt every second and a half while the target is in view. */
    static final class FireGoal extends Goal {
        private static final int COOLDOWN = 30;
        private final AtomicSentry sentry;
        private int cooldown;
        private int beep;

        FireGoal(AtomicSentry sentry) {
            this.sentry = sentry;
            setFlags(EnumSet.of(Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            LivingEntity t = sentry.getTarget();
            return t != null && t.isAlive() && sentry.distanceToSqr(t) < SIGHT * SIGHT;
        }

        @Override
        public void start() {
            sentry.setAggressive(true);
            cooldown = 15;
            beep = 0;
        }

        @Override
        public void stop() {
            sentry.setAggressive(false);
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }

        @Override
        public void tick() {
            LivingEntity target = sentry.getTarget();
            if (target == null) {
                return;
            }
            sentry.getLookControl().setLookAt(target, 40.0F, 40.0F);
            double dx = target.getX() - sentry.getX();
            double dz = target.getZ() - sentry.getZ();
            float yaw = (float) (Mth.atan2(dz, dx) * Mth.RAD_TO_DEG) - 90.0F;
            sentry.setYRot(Mth.approachDegrees(sentry.getYRot(), yaw, 8.0F));
            sentry.yBodyRot = sentry.getYRot();
            if (--beep <= 0) {
                sentry.playSound(SoundEvents.NOTE_BLOCK_BIT.value(), 1.6F, 1.9F);
                beep = 40;
            }
            if (--cooldown <= 0 && sentry.getSensing().hasLineOfSight(target)) {
                cooldown = COOLDOWN;
                Vec3 eye = sentry.position().add(0.0, 0.35, 0.0);
                Vec3 dir = target.getEyePosition().subtract(0.0, 0.3, 0.0).subtract(eye).normalize();
                SentryBolt bolt = new SentryBolt(sentry.level(), sentry, dir);
                bolt.setPos(eye.add(dir.scale(0.9)));
                sentry.level().addFreshEntity(bolt);
                sentry.playSound(SoundEvents.BLAZE_SHOOT, 1.0F, 1.9F);
            }
        }
    }
}
