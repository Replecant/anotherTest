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
import net.minecraft.util.Mth;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.AgeableMob;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.BreedGoal;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.FollowParentGoal;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.TemptGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

/**
 * Ankylosaurus: a walking boulder of the volcanic highlands. Slow, placid, grazing - and armoured like a tank. Hit
 * it and it swings round to bring the great tail club to bear: ten points of damage and a knock that sends you
 * flying. It doesn't chase; it just keeps swinging while you stay within reach.
 */
public class Ankylosaurus extends Animal implements DinosaurAnimated, GrazeGoal.Grazer {
    private static final EntityDataAccessor<Boolean> GRAZING = SynchedEntityData.defineId(Ankylosaurus.class, EntityDataSerializers.BOOLEAN);
    private static final EntityDataAccessor<Integer> SWING = SynchedEntityData.defineId(Ankylosaurus.class, EntityDataSerializers.INT);
    static final int SWING_TICKS = 14;

    private final Smoothed graze = new Smoothed(0.06F);
    private int swingClient;
    private int swingClientO;

    public Ankylosaurus(EntityType<? extends Ankylosaurus> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Animal.createAnimalAttributes()
                .add(Attributes.MAX_HEALTH, 80.0)
                .add(Attributes.MOVEMENT_SPEED, 0.14)
                .add(Attributes.ARMOR, 15.0)
                .add(Attributes.ARMOR_TOUGHNESS, 4.0)
                .add(Attributes.ATTACK_DAMAGE, 10.0)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.85)
                .add(Attributes.STEP_HEIGHT, 1.0)
                .add(Attributes.FOLLOW_RANGE, 12.0);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(1, new TailStrikeGoal(this));
        goalSelector.addGoal(2, new BreedGoal(this, 1.0));
        goalSelector.addGoal(3, new TemptGoal(this, 1.1, this::isFood, false));
        goalSelector.addGoal(4, new FollowParentGoal(this, 1.1));
        goalSelector.addGoal(5, new GrazeGoal(this));
        goalSelector.addGoal(6, new WaterAvoidingRandomStrollGoal(this, 0.8));
        goalSelector.addGoal(7, new LookAtPlayerGoal(this, Player.class, 8.0F));
        goalSelector.addGoal(8, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this));
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(GRAZING, false);
        builder.define(SWING, 0);
    }

    @Override
    public void setGrazing(boolean grazing) {
        entityData.set(GRAZING, grazing);
    }

    void startSwing() {
        entityData.set(SWING, entityData.get(SWING) + 1);
    }

    @Override
    public void tick() {
        super.tick();
        if (level().isClientSide()) {
            graze.tick(entityData.get(GRAZING));
            swingClientO = swingClient;
            if (swingClient > 0) {
                swingClient--;
            }
        }
    }

    @Override
    public void onSyncedDataUpdated(EntityDataAccessor<?> key) {
        super.onSyncedDataUpdated(key);
        if (SWING.equals(key) && level().isClientSide()) {
            swingClient = SWING_TICKS;
            swingClientO = SWING_TICKS;
        }
    }

    @Override
    public float grazeAmount(float partialTick) {
        return graze.get(partialTick);
    }

    /** 0 -> 1 over the swing, then back to 0. */
    @Override
    public float swingAmount(float partialTick) {
        float left = Mth.lerp(partialTick, swingClientO, swingClient);
        return left <= 0.0F ? 0.0F : 1.0F - left / SWING_TICKS;
    }

    /** Calms down a while after the last blow it took. */
    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        LivingEntity t = getTarget();
        if (t != null && (tickCount - getLastHurtByMobTimestamp() > 300 || distanceToSqr(t) > 16.0 * 16.0)) {
            setTarget(null);
        }
    }

    @Override
    public boolean isFood(ItemStack stack) {
        return stack.is(Items.FERN) || stack.is(Items.LARGE_FERN);
    }

    @Nullable
    @Override
    public AgeableMob getBreedOffspring(ServerLevel level, AgeableMob partner) {
        return ModDinosaurs.ANKYLOSAURUS.get().create(level, EntitySpawnReason.BREEDING);
    }

    @Override
    public int getMaxSpawnClusterSize() {
        return 3;
    }

    @Override
    protected SoundEvent getAmbientSound() {
        return SoundEvents.SNIFFER_IDLE;
    }

    @Override
    public int getAmbientSoundInterval() {
        return 240;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.SHIELD_BLOCK.value();
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.RAVAGER_DEATH;
    }

    @Override
    protected void playStepSound(BlockPos pos, BlockState state) {
        playSound(SoundEvents.RAVAGER_STEP, 0.6F, 0.8F);
    }

    @Override
    public float getVoicePitch() {
        return (isBaby() ? 1.2F : 0.8F) + (random.nextFloat() - random.nextFloat()) * 0.06F;
    }

    /** Turn the tail toward whoever is pestering it, then swing the club. */
    static final class TailStrikeGoal extends Goal {
        private static final double REACH = 4.5;
        private static final int COOLDOWN = 40;
        private final Ankylosaurus anky;
        private int ticks;
        private int cooldown;

        TailStrikeGoal(Ankylosaurus anky) {
            this.anky = anky;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            LivingEntity t = anky.getTarget();
            return !anky.isBaby() && t != null && t.isAlive() && anky.distanceToSqr(t) < 8.0 * 8.0;
        }

        @Override
        public void start() {
            ticks = 0;
            anky.getNavigation().stop();
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }

        @Override
        public void tick() {
            LivingEntity target = anky.getTarget();
            if (target == null) {
                return;
            }
            if (cooldown > 0) {
                cooldown--;
            }
            double dx = target.getX() - anky.getX();
            double dz = target.getZ() - anky.getZ();
            double dist = Math.sqrt(dx * dx + dz * dz);
            if (dist > REACH + 1.0) {
                anky.getNavigation().moveTo(target, 0.9);  // shuffle closer, but it's no chaser
                return;
            }
            anky.getNavigation().stop();
            // turn the backside (and the club) toward the target
            float away = (float) (Mth.atan2(dz, dx) * Mth.RAD_TO_DEG) + 90.0F;
            anky.setYRot(Mth.approachDegrees(anky.getYRot(), away, 12.0F));
            anky.yBodyRot = anky.getYRot();
            anky.yHeadRot = anky.getYRot();
            if (ticks > 0) {
                ticks++;
                if (ticks == Ankylosaurus.SWING_TICKS / 2) {
                    strike(target);
                }
                if (ticks >= Ankylosaurus.SWING_TICKS) {
                    ticks = 0;
                    cooldown = COOLDOWN;
                }
            } else if (cooldown <= 0 && Math.abs(Mth.wrapDegrees(anky.getYRot() - away)) < 35.0F) {
                ticks = 1;
                anky.startSwing();
                anky.playSound(SoundEvents.PLAYER_ATTACK_SWEEP, 1.2F, 0.6F);
            }
        }

        private void strike(LivingEntity target) {
            if (!(anky.level() instanceof ServerLevel level) || anky.distanceTo(target) > REACH + target.getBbWidth()) {
                return;
            }
            if (target.hurtServer(level, level.damageSources().mobAttack(anky), (float) anky.getAttributeValue(Attributes.ATTACK_DAMAGE))) {
                Vec3 away = target.position().subtract(anky.position()).multiply(1.0, 0.0, 1.0).normalize();
                target.knockback(2.2, -away.x, -away.z);
                target.push(0.0, 0.35, 0.0);
                target.hurtMarked = true;
                anky.playSound(SoundEvents.GOAT_RAM_IMPACT, 1.4F, 0.6F);
            }
        }
    }
}
