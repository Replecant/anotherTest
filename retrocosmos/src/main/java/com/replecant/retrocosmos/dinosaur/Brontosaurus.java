package com.replecant.retrocosmos.dinosaur;

import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.AgeableMob;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
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
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

/**
 * Brontosaurus: the classic long-neck. Huge, slow and peaceful; wanders the jungle, stops to graze with its head
 * down at the ground, groans, and shoulders smaller creatures out of its way. Hard to knock about. Breeds on ferns.
 */
public class Brontosaurus extends Animal implements DinosaurAnimated, GrazeGoal.Grazer {
    private static final EntityDataAccessor<Boolean> GRAZING = SynchedEntityData.defineId(Brontosaurus.class, EntityDataSerializers.BOOLEAN);

    private final Smoothed graze = new Smoothed(0.05F);

    public Brontosaurus(EntityType<? extends Brontosaurus> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Animal.createAnimalAttributes()
                .add(Attributes.MAX_HEALTH, 120.0)
                .add(Attributes.MOVEMENT_SPEED, 0.17)
                .add(Attributes.ARMOR, 4.0)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.9)
                .add(Attributes.EXPLOSION_KNOCKBACK_RESISTANCE, 0.8)
                .add(Attributes.STEP_HEIGHT, 1.6)
                .add(Attributes.FOLLOW_RANGE, 20.0);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(1, new PanicGoal(this, 1.5));
        goalSelector.addGoal(2, new BreedGoal(this, 1.0));
        goalSelector.addGoal(3, new TemptGoal(this, 1.1, this::isFood, false));
        goalSelector.addGoal(4, new FollowParentGoal(this, 1.1));
        goalSelector.addGoal(5, new GrazeGoal(this));
        goalSelector.addGoal(6, new WaterAvoidingRandomStrollGoal(this, 0.8));
        goalSelector.addGoal(7, new LookAtPlayerGoal(this, Player.class, 14.0F));
        goalSelector.addGoal(8, new RandomLookAroundGoal(this));
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(GRAZING, false);
    }

    public boolean isGrazing() {
        return entityData.get(GRAZING);
    }

    @Override
    public void setGrazing(boolean grazing) {
        entityData.set(GRAZING, grazing);
    }

    @Override
    public void tick() {
        super.tick();
        if (level().isClientSide()) {
            graze.tick(isGrazing());
        }
    }

    @Override
    public float grazeAmount(float partialTick) {
        return graze.get(partialTick);
    }

    /** Anything smaller that gets under its feet is shouldered aside. */
    @Override
    public void aiStep() {
        super.aiStep();
        if (!level().isClientSide() && isAlive() && !isBaby()) {
            for (Entity other : level().getEntities(this, getBoundingBox().inflate(0.35, 0.0, 0.35),
                    e -> e.isPushable() && !(e instanceof Brontosaurus) && !e.isPassengerOfSameVehicle(this))) {
                Vec3 away = new Vec3(other.getX() - getX(), 0.0, other.getZ() - getZ());
                if (away.lengthSqr() < 1.0E-4) {
                    away = new Vec3(random.nextDouble() - 0.5, 0.0, random.nextDouble() - 0.5);
                }
                away = away.normalize().scale(0.12);
                other.push(away.x, 0.02, away.z);
                other.hurtMarked = true;
            }
        }
    }

    /** Other mobs bump into it without shoving the giant around. */
    @Override
    public boolean isPushable() {
        return false;
    }

    @Override
    public boolean isFood(ItemStack stack) {
        return stack.is(Items.FERN) || stack.is(Items.LARGE_FERN);
    }

    @Nullable
    @Override
    public AgeableMob getBreedOffspring(ServerLevel level, AgeableMob partner) {
        return ModDinosaurs.BRONTOSAURUS.get().create(level, EntitySpawnReason.BREEDING);
    }

    @Override
    public int getAmbientSoundInterval() {
        return 260;
    }

    @Override
    protected SoundEvent getAmbientSound() {
        return random.nextBoolean() ? SoundEvents.CAMEL_AMBIENT : SoundEvents.SNIFFER_IDLE;
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
    protected void playStepSound(BlockPos pos, BlockState state) {
        playSound(SoundEvents.RAVAGER_STEP, isBaby() ? 0.4F : 1.1F, isBaby() ? 0.9F : 0.55F);
    }

    @Override
    protected float getSoundVolume() {
        return isBaby() ? 1.0F : 2.5F;
    }

    @Override
    public float getVoicePitch() {
        return (isBaby() ? 0.9F : 0.45F) + (random.nextFloat() - random.nextFloat()) * 0.06F;
    }

    @Override
    public int getMaxHeadYRot() {
        return 40;
    }
}
