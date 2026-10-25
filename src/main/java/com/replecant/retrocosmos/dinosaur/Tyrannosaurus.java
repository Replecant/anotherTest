package com.replecant.retrocosmos.dinosaur;

import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.BossEvent;
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
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;

/**
 * Tyrannosaurus: the rare apex predator of Venus. Five and a half blocks of bad temper that hunts people,
 * triceratops and brontosaurs alike. Roars when it picks a victim, charges, bites hard (14) and sweeps its tail at
 * anything that gets behind it. The ground shakes under its feet. Worth it: a fang and the great skull itself.
 */
public class Tyrannosaurus extends Monster implements DinosaurAnimated {
    private static final EntityDataAccessor<Boolean> ROARING = SynchedEntityData.defineId(Tyrannosaurus.class, EntityDataSerializers.BOOLEAN);
    private static final EntityDataAccessor<Boolean> SWEEPING = SynchedEntityData.defineId(Tyrannosaurus.class, EntityDataSerializers.BOOLEAN);
    private static final int ROAR_TICKS = 36;
    private static final double BOSS_BAR_RANGE = 48.0;

    private final Smoothed roar = new Smoothed(0.12F);
    private final Smoothed sweep = new Smoothed(0.25F);
    private final ServerBossEvent bossBar = new ServerBossEvent(getDisplayName(), BossEvent.BossBarColor.RED, BossEvent.BossBarOverlay.NOTCHED_10);
    private int roarTicks;
    int sweepTicks;
    int sweepCooldown;

    public Tyrannosaurus(EntityType<? extends Tyrannosaurus> type, Level level) {
        super(type, level);
        this.xpReward = 60;
        bossBar.setVisible(false);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 200.0)
                .add(Attributes.MOVEMENT_SPEED, 0.23)
                .add(Attributes.ATTACK_DAMAGE, 14.0)
                .add(Attributes.ATTACK_KNOCKBACK, 1.5)
                .add(Attributes.ARMOR, 10.0)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.EXPLOSION_KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 40.0)
                .add(Attributes.STEP_HEIGHT, 1.6);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(1, new TyrannosaurusTailSweepGoal(this));
        goalSelector.addGoal(2, new MeleeAttackGoal(this, 1.55, true));
        goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 0.6));
        goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 16.0F));
        goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this, Tyrannosaurus.class));
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
        // big game: herbivores are hunted too, though less eagerly than people
        targetSelector.addGoal(3, new NearestAttackableTargetGoal<>(this, Triceratops.class, 120, true, false, null));
        targetSelector.addGoal(3, new NearestAttackableTargetGoal<>(this, Brontosaurus.class, 160, true, false, null));
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(ROARING, false);
        builder.define(SWEEPING, false);
    }

    void setSweeping(boolean sweeping) {
        entityData.set(SWEEPING, sweeping);
    }

    /** A new victim gets a roar first: it stands, throws its head up and bellows. */
    @Override
    public void setTarget(@Nullable LivingEntity target) {
        LivingEntity previous = getTarget();
        super.setTarget(target);
        if (target != null && previous == null && !level().isClientSide()) {
            roarTicks = ROAR_TICKS;
            entityData.set(ROARING, true);
            playSound(SoundEvents.RAVAGER_ROAR, 4.0F, 0.5F);
            playSound(SoundEvents.WARDEN_ROAR, 2.5F, 0.85F);
        }
    }

    @Override
    public void tick() {
        super.tick();
        if (level().isClientSide()) {
            roar.tick(entityData.get(ROARING));
            sweep.tick(entityData.get(SWEEPING));
        }
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (roarTicks > 0) {
            roarTicks--;
            getNavigation().stop();
            if (roarTicks == 0) {
                entityData.set(ROARING, false);
            }
        }
        if (sweepCooldown > 0) {
            sweepCooldown--;
        }
        bossBar.setProgress(getHealth() / getMaxHealth());
        if (tickCount % 10 == 0) {
            updateBossBar(level);
        }
    }

    /** The health bar shows to everyone nearby while it is hunting a player. */
    private void updateBossBar(ServerLevel level) {
        boolean hunting = getTarget() instanceof Player && isAlive();
        bossBar.setVisible(hunting);
        if (!hunting) {
            bossBar.removeAllPlayers();
            return;
        }
        for (ServerPlayer player : level.players()) {
            boolean near = player.distanceToSqr(this) < BOSS_BAR_RANGE * BOSS_BAR_RANGE && !player.isSpectator();
            if (near && !bossBar.getPlayers().contains(player)) {
                bossBar.addPlayer(player);
            } else if (!near && bossBar.getPlayers().contains(player)) {
                bossBar.removePlayer(player);
            }
        }
    }

    @Override
    public void stopSeenByPlayer(ServerPlayer player) {
        super.stopSeenByPlayer(player);
        bossBar.removePlayer(player);
    }

    @Override
    public void remove(RemovalReason reason) {
        bossBar.removeAllPlayers();
        super.remove(reason);
    }

    @Override
    public float roarAmount(float partialTick) {
        return roar.get(partialTick);
    }

    @Override
    public float sweepAmount(float partialTick) {
        return sweep.get(partialTick);
    }

    /** The head sits far in front of the hitbox, so the bite reaches further than a normal mob's. */
    @Override
    protected AABB getAttackBoundingBox(double range) {
        return super.getAttackBoundingBox(range).inflate(1.6, 0.0, 1.6);
    }

    @Override
    public boolean doHurtTarget(ServerLevel level, Entity target) {
        boolean hit = super.doHurtTarget(level, target);
        if (hit) {
            playSound(SoundEvents.RAVAGER_ATTACK, 1.6F, 0.55F);
        }
        return hit;
    }

    /** Thud: a heavy footfall, a puff of whatever it stands on (and, for nearby players, a camera shake). */
    @Override
    protected void playStepSound(BlockPos pos, BlockState state) {
        playSound(SoundEvents.RAVAGER_STEP, 2.0F, 0.45F);
        playSound(SoundEvents.WARDEN_STEP, 1.5F, 0.6F);
        if (level() instanceof ServerLevel server && !state.isAir()) {
            server.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, state), getX(), getY() + 0.1, getZ(),
                    14, 1.2, 0.05, 1.2, 0.15);
        }
    }

    @Override
    public float getWalkTargetValue(BlockPos pos, LevelReader level) {
        return 0.0F;
    }

    @Override
    public int getMaxSpawnClusterSize() {
        return 1;
    }

    @Override
    public int getAmbientSoundInterval() {
        return 240;
    }

    @Override
    protected SoundEvent getAmbientSound() {
        return SoundEvents.RAVAGER_AMBIENT;
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
    protected float getSoundVolume() {
        return 3.0F;
    }

    @Override
    public float getVoicePitch() {
        return 0.5F + (random.nextFloat() - random.nextFloat()) * 0.05F;
    }
}
