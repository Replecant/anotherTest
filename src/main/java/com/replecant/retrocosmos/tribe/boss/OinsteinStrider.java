package com.replecant.retrocosmos.tribe.boss;

import com.replecant.retrocosmos.dinosaur.robot.ModRobots;
import com.replecant.retrocosmos.registry.ModSounds;
import com.replecant.retrocosmos.tribe.ModTribes;
import com.replecant.retrocosmos.tribe.mutant.BlasterBolt;
import com.replecant.retrocosmos.tribe.mutant.OinsteinForces;
import java.util.EnumSet;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ItemParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.util.Mth;
import net.minecraft.world.BossEvent;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;

/**
 * Phase one: Dr. Oinstein at the controls of his Atomic Strider, a 4.5-block chrome chicken-walker. It keeps its
 * distance and fires three-bolt volleys from its twin cannons (the muzzles crackle for a second first - the tell),
 * stomps anyone who gets under it, and at three quarters health drops two atomic sentries. At zero it does not die:
 * it staggers, sparks, blows apart (no block damage) and throws the doctor out onto the floor.
 */
public class OinsteinStrider extends OinsteinBoss {
    private static final EntityDataAccessor<Integer> CHARGE = SynchedEntityData.defineId(OinsteinStrider.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> STOMP = SynchedEntityData.defineId(OinsteinStrider.class, EntityDataSerializers.INT);
    public static final int STOMP_NONE = 0;
    public static final int STOMP_RAISE = 1;
    public static final int STOMP_IMPACT = 2;
    /** Ticks from zero health to the explosion. */
    public static final int WRECK_TICKS = 30;
    static final int CHARGE_TICKS = 24;

    private boolean sentries;
    private float charge, chargeO, raise, raiseO, impact, impactO;

    public OinsteinStrider(EntityType<? extends OinsteinStrider> type, Level level) {
        super(type, level, Component.translatable("bossbar.retrocosmos.oinstein_strider"), BossEvent.BossBarColor.YELLOW);
        this.xpReward = 0;
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 200.0)
                .add(Attributes.ARMOR, 6.0)
                .add(Attributes.ATTACK_DAMAGE, 8.0)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.EXPLOSION_KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.MOVEMENT_SPEED, 0.22)
                .add(Attributes.FOLLOW_RANGE, 40.0)
                .add(Attributes.STEP_HEIGHT, 1.6);
    }

    /** The anchor's spawn: phase one at full health in the middle of the arena. */
    public static OinsteinStrider spawnAt(ServerLevel level, BlockPos anchor) {
        OinsteinStrider strider = ModTribes.OINSTEIN_STRIDER.get().create(level, EntitySpawnReason.TRIGGERED);
        if (strider == null) {
            return null;
        }
        strider.snapTo(anchor.getX() + 0.5, anchor.getY(), anchor.getZ() + 0.5, level.getRandom().nextFloat() * 360.0F, 0.0F);
        strider.setAnchor(anchor);
        level.addFreshEntity(strider);
        level.playSound(null, anchor, SoundEvents.BEACON_ACTIVATE, strider.getSoundSource(), 2.0F, 0.6F);
        return strider;
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new ReturnHomeGoal(this));
        goalSelector.addGoal(1, new StompGoal());
        goalSelector.addGoal(2, new VolleyGoal());
        goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 24.0F));
        goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        registerBossTargets();
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(CHARGE, 0);
        builder.define(STOMP, STOMP_NONE);
    }

    public boolean isCharging() {
        return entityData.get(CHARGE) > 0;
    }

    public int stompState() {
        return entityData.get(STOMP);
    }

    @Override
    public void tick() {
        super.tick();
        if (level().isClientSide()) {
            chargeO = charge;
            raiseO = raise;
            impactO = impact;
            charge = Mth.approach(charge, isCharging() ? 1.0F : 0.0F, isCharging() ? 1.0F / CHARGE_TICKS : 0.25F);
            int s = stompState();
            raise = Mth.approach(raise, s == STOMP_RAISE ? 1.0F : 0.0F, s == STOMP_RAISE ? 0.08F : 0.4F);
            impact = Mth.approach(impact, s == STOMP_IMPACT ? 1.0F : 0.0F, s == STOMP_IMPACT ? 0.5F : 0.1F);
        }
    }

    public float chargeAmount(float pt) {
        return Mth.lerp(pt, chargeO, charge);
    }

    public float raiseAmount(float pt) {
        return Mth.lerp(pt, raiseO, raise);
    }

    public float impactAmount(float pt) {
        return Mth.lerp(pt, impactO, impact);
    }

    /** 0 while it fights, rising to 1 as it falls apart. */
    public float wreckAmount(float pt) {
        return deathTime <= 0 ? 0.0F : Math.min(1.0F, (deathTime + pt) / WRECK_TICKS);
    }

    @Override
    public void setTarget(LivingEntity target) {
        boolean first = getTarget() == null && target != null;
        super.setTarget(target);
        if (first && getTarget() != null && !level().isClientSide() && tickCount > 5) {
            taunt("strider.intro", 3);
        }
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        boolean hurt = super.hurtServer(level, source, amount);
        if (hurt && !sentries && isAlive() && getHealth() <= getMaxHealth() * 0.75F) {
            deploySentries(level);
        }
        return hurt;
    }

    private void deploySentries(ServerLevel level) {
        sentries = true;
        say("strider.sentries");
        float yaw = yBodyRot * Mth.DEG_TO_RAD;
        Vec3 left = new Vec3(Mth.cos(yaw), 0, Mth.sin(yaw));
        for (int side = -1; side <= 1; side += 2) {
            Vec3 at = position().add(left.scale(side * 3.5));
            var sentry = summon(level, ModRobots.ATOMIC_SENTRY.get(), at, 1.5);
            if (sentry != null) {
                level.sendParticles(ParticleTypes.CLOUD, sentry.getX(), sentry.getY() + 0.5, sentry.getZ(), 12, 0.3, 0.3, 0.3, 0.05);
                level.sendParticles(ParticleTypes.ELECTRIC_SPARK, sentry.getX(), sentry.getY() + 0.8, sentry.getZ(), 10, 0.3, 0.3, 0.3, 0.2);
            }
        }
        playSound(SoundEvents.DISPENSER_LAUNCH, 2.0F, 0.6F);
        playSound(SoundEvents.PISTON_EXTEND, 2.0F, 0.7F);
    }

    // ------------------------------------------------------------------
    // The wreck (zero health -> the doctor tumbles out)
    // ------------------------------------------------------------------

    @Override
    public void die(DamageSource source) {
        // no death, no loot: the machine breaks down and the fight goes on
        if (level() instanceof ServerLevel level && deathTime == 0) {
            bossEvent.setName(Component.translatable("bossbar.retrocosmos.oinstein_strider.critical"));
            bossEvent.setProgress(0.0F);
            say("strider.wreck");
            level.playSound(null, getX(), getY(), getZ(), SoundEvents.IRON_GOLEM_DEATH, getSoundSource(), 2.5F, 0.5F);
            entityData.set(CHARGE, 0);
            entityData.set(STOMP, STOMP_NONE);
        }
    }

    @Override
    protected void tickDeath() {
        deathTime++;
        if (!(level() instanceof ServerLevel level) || isRemoved()) {
            return;
        }
        double top = getY() + 3.2;
        level.sendParticles(ParticleTypes.ELECTRIC_SPARK, getX(), top, getZ(), 4, 1.1, 0.8, 1.1, 0.25);
        level.sendParticles(ParticleTypes.LARGE_SMOKE, getX(), top, getZ(), 2, 0.8, 0.6, 0.8, 0.02);
        if (deathTime % 6 == 0) {
            double px = getX() + (random.nextDouble() - 0.5) * 2.2;
            double pz = getZ() + (random.nextDouble() - 0.5) * 2.2;
            double py = getY() + 1.5 + random.nextDouble() * 2.5;
            level.sendParticles(ParticleTypes.EXPLOSION, px, py, pz, 1, 0.0, 0.0, 0.0, 0.0);
            level.playSound(null, px, py, pz, SoundEvents.GENERIC_EXPLODE.value(), getSoundSource(), 0.8F, 1.3F + random.nextFloat() * 0.3F);
        }
        if (deathTime % 10 == 1) {
            level.playSound(null, getX(), getY(), getZ(), SoundEvents.NOTE_BLOCK_BIT.value(), getSoundSource(), 1.5F, 0.6F);
        }
        if (deathTime >= WRECK_TICKS) {
            blowApart(level);
        }
    }

    private void blowApart(ServerLevel level) {
        double cy = getY() + 2.6;
        level.sendParticles(ParticleTypes.EXPLOSION_EMITTER, getX(), cy, getZ(), 1, 0.0, 0.0, 0.0, 0.0);
        level.sendParticles(ParticleTypes.FLAME, getX(), cy, getZ(), 40, 1.0, 1.0, 1.0, 0.15);
        level.sendParticles(ParticleTypes.LARGE_SMOKE, getX(), cy, getZ(), 40, 1.2, 1.2, 1.2, 0.08);
        BlockState steel = Blocks.IRON_BLOCK.defaultBlockState();
        level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, steel), getX(), cy, getZ(), 120, 1.2, 1.4, 1.2, 0.6);
        level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.GLASS.defaultBlockState()), getX(), getY() + 3.6, getZ(),
                60, 0.6, 0.5, 0.6, 0.4);
        level.sendParticles(new ItemParticleOption(ParticleTypes.ITEM, new ItemStack(Items.IRON_INGOT)), getX(), cy, getZ(),
                30, 0.8, 0.8, 0.8, 0.35);
        level.playSound(null, getX(), cy, getZ(), SoundEvents.GENERIC_EXPLODE.value(), getSoundSource(), 4.0F, 0.7F);
        level.playSound(null, getX(), cy, getZ(), SoundEvents.ANVIL_DESTROY, getSoundSource(), 2.0F, 0.6F);
        // the blast throws everyone back a little - and hurts no one
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, getBoundingBox().inflate(6.0),
                e -> e != this && e.isAlive() && !OinsteinForces.isAlly(e))) {
            Vec3 away = e.position().subtract(position()).multiply(1, 0, 1);
            double len = Math.max(0.5, away.length());
            e.setDeltaMovement(away.x / len * 0.9, 0.45, away.z / len * 0.9);
            e.hurtMarked = true;
        }
        DrOinstein doctor = ModTribes.DR_OINSTEIN.get().create(level, EntitySpawnReason.TRIGGERED);
        if (doctor != null) {
            float yaw = yBodyRot * Mth.DEG_TO_RAD;
            becomeNext(level, doctor);
            doctor.setPos(getX(), getY() + 2.4, getZ());
            // tumbling out of the cockpit, forwards and up
            doctor.setDeltaMovement(-Mth.sin(yaw) * 0.35, 0.55, Mth.cos(yaw) * 0.35);
        } else {
            discard();
        }
    }

    // ------------------------------------------------------------------
    // Sounds, save data
    // ------------------------------------------------------------------

    @Override
    protected SoundEvent getAmbientSound() {
        return SoundEvents.BEACON_AMBIENT;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.IRON_GOLEM_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return null;
    }

    @Override
    protected void playStepSound(BlockPos pos, BlockState state) {
        playSound(SoundEvents.IRON_GOLEM_STEP, 1.4F, 0.55F);
        playSound(SoundEvents.PISTON_CONTRACT, 0.35F, 1.4F);
    }

    @Override
    public float getVoicePitch() {
        return 0.8F;
    }

    @Override
    public int getMaxHeadYRot() {
        return 50;
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putBoolean("Sentries", sentries);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        sentries = input.getBooleanOr("Sentries", false);
    }

    /** Muzzle of the left (+1) or right (-1) cannon, in the world. */
    Vec3 muzzle(int side) {
        float yaw = yBodyRot * Mth.DEG_TO_RAD;
        Vec3 fwd = new Vec3(-Mth.sin(yaw), 0, Mth.cos(yaw));
        Vec3 left = new Vec3(Mth.cos(yaw), 0, Mth.sin(yaw));
        return position().add(fwd.scale(1.25)).add(left.scale(side * 0.95)).add(0, 2.75, 0);
    }

    // ------------------------------------------------------------------
    // Goals
    // ------------------------------------------------------------------

    /**
     * Keeps 8-14 blocks off, sidestepping; every 2.5-3.5 s charges both cannons for 1.2 s (crackling muzzles and a
     * rising hum) and fires three bolts at where the target is - strafe and they miss.
     */
    class VolleyGoal extends Goal {
        private int cooldown = 40;
        private int ticks = -1;
        private int seeTime;
        private int strafeTime;
        private boolean strafeLeft;

        VolleyGoal() {
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            LivingEntity t = getTarget();
            return t != null && t.isAlive();
        }

        @Override
        public void stop() {
            entityData.set(CHARGE, 0);
            ticks = -1;
            getMoveControl().strafe(0.0F, 0.0F);
            getNavigation().stop();
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }

        @Override
        public void tick() {
            LivingEntity t = getTarget();
            if (t == null || !(level() instanceof ServerLevel level)) {
                return;
            }
            double d2 = distanceToSqr(t);
            boolean sees = getSensing().hasLineOfSight(t);
            seeTime = sees ? seeTime + 1 : 0;
            getLookControl().setLookAt(t, 30.0F, 30.0F);
            if (ticks < 0) {
                // positioning
                if (d2 > 14.0 * 14.0 || !sees) {
                    getNavigation().moveTo(t, 1.0);
                    getMoveControl().strafe(0.0F, 0.0F);
                } else {
                    getNavigation().stop();
                    if (++strafeTime > 50 && random.nextFloat() < 0.05F) {
                        strafeLeft = !strafeLeft;
                        strafeTime = 0;
                    }
                    float back = d2 < 8.0 * 8.0 ? -0.45F : 0.0F;
                    getMoveControl().strafe(back, strafeLeft ? 0.35F : -0.35F);
                    lookAt(t, 30.0F, 30.0F);
                }
                if (--cooldown <= 0 && sees && seeTime > 10 && d2 < 32.0 * 32.0) {
                    ticks = 0;
                    entityData.set(CHARGE, 1);
                    playSound(SoundEvents.BEACON_POWER_SELECT, 2.0F, 1.6F);
                    playSound(SoundEvents.BEACON_ACTIVATE, 1.2F, 1.9F);
                }
                return;
            }
            // charging, then firing: stand and aim
            ticks++;
            getNavigation().stop();
            getMoveControl().strafe(0.0F, 0.0F);
            lookAt(t, 30.0F, 30.0F);
            if (ticks < CHARGE_TICKS) {
                for (int side = -1; side <= 1; side += 2) {
                    Vec3 m = muzzle(side);
                    level.sendParticles(ParticleTypes.ELECTRIC_SPARK, m.x, m.y, m.z, 2, 0.12, 0.12, 0.12, 0.05);
                }
                return;
            }
            int shot = (ticks - CHARGE_TICKS) / 6;
            if ((ticks - CHARGE_TICKS) % 6 == 0 && shot < 3) {
                entityData.set(CHARGE, 0);
                fireBolt(level, t, shot % 2 == 0 ? 1 : -1);
            }
            if (shot >= 3) {
                ticks = -1;
                cooldown = 50 + random.nextInt(20);
            }
        }

        private void fireBolt(ServerLevel level, LivingEntity t, int side) {
            Vec3 m = muzzle(side);
            Vec3 aim = new Vec3(t.getX(), t.getY(0.55), t.getZ()).subtract(m);
            BlasterBolt bolt = new BlasterBolt(ModTribes.BLASTER_BOLT.get(), level);
            bolt.setOwner(OinsteinStrider.this);
            bolt.setPos(m.x, m.y, m.z);
            bolt.shoot(aim.x, aim.y, aim.z, BlasterBolt.SPEED, 1.6F);
            level.addFreshEntity(bolt);
            level.playSound(null, m.x, m.y, m.z, ModSounds.BLASTER_SHOT.get(), getSoundSource(), 2.0F, 0.75F + random.nextFloat() * 0.1F);
            level.sendParticles(ParticleTypes.END_ROD, m.x, m.y, m.z, 3, 0.05, 0.05, 0.05, 0.05);
        }
    }

    /** Someone under its feet: one leg goes up (0.9 s, servos whining), then down - a shockwave ring of 5 blocks. */
    class StompGoal extends Goal {
        private static final int WINDUP = 18;
        private static final int RECOVER = 12;
        private static final double RANGE = 5.0;
        private int cooldown = 30;
        private int ticks;

        StompGoal() {
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK, Flag.JUMP));
        }

        @Override
        public boolean canUse() {
            if (cooldown > 0) {
                cooldown--;
                return false;
            }
            LivingEntity t = getTarget();
            return t != null && t.isAlive() && onGround() && distanceToSqr(t) < 4.5 * 4.5;
        }

        @Override
        public boolean canContinueToUse() {
            return ticks < WINDUP + RECOVER && isAlive();
        }

        @Override
        public void start() {
            ticks = 0;
            getNavigation().stop();
            getMoveControl().strafe(0.0F, 0.0F);
            entityData.set(CHARGE, 0);
            entityData.set(STOMP, STOMP_RAISE);
            playSound(SoundEvents.PISTON_EXTEND, 2.0F, 0.5F);
            playSound(SoundEvents.IRON_GOLEM_ATTACK, 2.0F, 0.6F);
        }

        @Override
        public void stop() {
            entityData.set(STOMP, STOMP_NONE);
            cooldown = 80 + random.nextInt(30);
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }

        @Override
        public void tick() {
            ticks++;
            if (ticks == WINDUP) {
                entityData.set(STOMP, STOMP_IMPACT);
                stomp();
            }
        }

        private void stomp() {
            if (!(level() instanceof ServerLevel level)) {
                return;
            }
            float yaw = yBodyRot * Mth.DEG_TO_RAD;
            Vec3 c = position().add(-Mth.sin(yaw) * 0.6, 0, Mth.cos(yaw) * 0.6);
            BlockState ground = level.getBlockState(BlockPos.containing(c.x, getY() - 0.5, c.z));
            level.playSound(null, c.x, c.y, c.z, SoundEvents.GENERIC_EXPLODE.value(), getSoundSource(), 1.6F, 0.5F);
            level.playSound(null, c.x, c.y, c.z, SoundEvents.ANVIL_LAND, getSoundSource(), 1.6F, 0.5F);
            for (int ring = 1; ring <= 5; ring++) {
                int n = 10 + ring * 6;
                for (int k = 0; k < n; k++) {
                    double a = Math.PI * 2 * k / n;
                    double px = c.x + Math.cos(a) * ring;
                    double pz = c.z + Math.sin(a) * ring;
                    if (!ground.isAir()) {
                        level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, ground), px, getY() + 0.1, pz, 2, 0.1, 0.05, 0.1, 0.15);
                    }
                    level.sendParticles(ParticleTypes.POOF, px, getY() + 0.2, pz, 1, 0.05, 0.05, 0.05, 0.02);
                }
            }
            for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, getBoundingBox().inflate(RANGE, 2.0, RANGE),
                    e -> e != OinsteinStrider.this && e.isAlive() && !OinsteinForces.isAlly(e))) {
                double dx = e.getX() - c.x;
                double dz = e.getZ() - c.z;
                double dist = Math.max(0.5, Math.sqrt(dx * dx + dz * dz));
                if (dist > RANGE + 0.5 || e.getY() > getY() + 2.0) {
                    continue;  // jump it, or be out of reach
                }
                float falloff = (float) Mth.clamp(1.2 - dist / (RANGE + 1.0), 0.35, 1.0);
                if (e.hurtServer(level, damageSources().mobAttack(OinsteinStrider.this), 9.0F * falloff)) {
                    double resist = 1.0 - e.getAttributeValue(Attributes.KNOCKBACK_RESISTANCE) * 0.6;
                    double kb = 1.0 * falloff * resist;
                    Vec3 v = e.getDeltaMovement();
                    e.setDeltaMovement(v.x * 0.3 + dx / dist * kb, (0.3 + 0.2 * falloff) * resist, v.z * 0.3 + dz / dist * kb);
                    e.hurtMarked = true;
                }
            }
        }
    }
}
