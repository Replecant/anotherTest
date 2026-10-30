package com.replecant.retrocosmos.dinosaur;

import java.util.EnumSet;
import java.util.List;
import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ItemParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.ItemTags;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.AgeableMob;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.AvoidEntityGoal;
import net.minecraft.world.entity.ai.goal.BreedGoal;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.FollowParentGoal;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;

/**
 * Compsognathus: chicken-sized, skittish, and a scavenger at heart. A flock scatters from anyone who runs at it,
 * snaps up dropped meat and seeds, and - like the zombified piglins - turns on whoever hurts one of them. It will
 * also gang up on a player who is badly wounded.
 */
public class Compsognathus extends Animal implements DinosaurAnimated {
    public Compsognathus(EntityType<? extends Compsognathus> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Animal.createAnimalAttributes()
                .add(Attributes.MAX_HEALTH, 6.0)
                .add(Attributes.MOVEMENT_SPEED, 0.32)
                .add(Attributes.ATTACK_DAMAGE, 1.5)
                .add(Attributes.FOLLOW_RANGE, 16.0);
    }

    private static boolean isWounded(LivingEntity e) {
        return e.getHealth() < e.getMaxHealth() * 0.5F;
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(1, new MeleeAttackGoal(this, 1.4, true));
        // a running or sprinting player sends the whole flock scattering (unless they smell blood)
        goalSelector.addGoal(2, new AvoidEntityGoal<>(this, Player.class, 9.0F, 1.5, 1.8,
                p -> getTarget() == null && !isWounded(p) && (p.isSprinting() || p.getDeltaMovement().horizontalDistanceSqr() > 0.02)));
        goalSelector.addGoal(3, new BreedGoal(this, 1.0));
        goalSelector.addGoal(4, new ScavengeGoal(this));
        goalSelector.addGoal(5, new FollowParentGoal(this, 1.2));
        goalSelector.addGoal(6, new WaterAvoidingRandomStrollGoal(this, 1.0));
        goalSelector.addGoal(7, new LookAtPlayerGoal(this, Player.class, 6.0F));
        goalSelector.addGoal(8, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this).setAlertOthers());
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, 10, true, false,
                (target, level) -> !isBaby() && isWounded(target)));
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        // the mob loses interest once the wounded player has healed up
        if (getTarget() instanceof Player p && !isWounded(p) && tickCount - getLastHurtByMobTimestamp() > 200) {
            setTarget(null);
        }
    }

    static boolean isFoodItem(ItemStack stack) {
        return stack.is(ItemTags.MEAT) || stack.is(ItemTags.CHICKEN_FOOD);
    }

    @Override
    public boolean isFood(ItemStack stack) {
        return stack.is(ItemTags.CHICKEN_FOOD);
    }

    @Nullable
    @Override
    public AgeableMob getBreedOffspring(ServerLevel level, AgeableMob partner) {
        return ModDinosaurs.COMPSOGNATHUS.get().create(level, EntitySpawnReason.BREEDING);
    }

    @Override
    public int getMaxSpawnClusterSize() {
        return 6;
    }

    @Override
    protected SoundEvent getAmbientSound() {
        return SoundEvents.PARROT_AMBIENT;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.FOX_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.FOX_DEATH;
    }

    @Override
    protected void playStepSound(BlockPos pos, BlockState state) {
        playSound(SoundEvents.CHICKEN_STEP, 0.12F, 1.4F);
    }

    @Override
    public float getVoicePitch() {
        return 1.6F + (random.nextFloat() - random.nextFloat()) * 0.15F;
    }

    /** Spot a dropped scrap of meat or a seed, dash over and gobble it. */
    static final class ScavengeGoal extends Goal {
        private final Compsognathus compy;
        @Nullable
        private ItemEntity food;

        ScavengeGoal(Compsognathus compy) {
            this.compy = compy;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            if (compy.getTarget() != null || compy.getRandom().nextInt(reducedTickDelay(10)) != 0) {
                return false;
            }
            List<ItemEntity> items = compy.level().getEntitiesOfClass(ItemEntity.class, compy.getBoundingBox().inflate(8.0, 3.0, 8.0),
                    e -> e.isAlive() && isFoodItem(e.getItem()));
            food = items.isEmpty() ? null : items.get(0);
            return food != null;
        }

        @Override
        public boolean canContinueToUse() {
            return food != null && food.isAlive() && compy.getTarget() == null;
        }

        @Override
        public void stop() {
            food = null;
        }

        @Override
        public void tick() {
            if (food == null) {
                return;
            }
            compy.getLookControl().setLookAt(food, 30.0F, 30.0F);
            if (compy.distanceToSqr(food) > 1.4) {
                compy.getNavigation().moveTo(food, 1.3);
            } else if (compy.level() instanceof ServerLevel level) {
                ItemStack stack = food.getItem();
                level.sendParticles(new ItemParticleOption(ParticleTypes.ITEM, stack.copyWithCount(1)), food.getX(), food.getY() + 0.2,
                        food.getZ(), 6, 0.1, 0.1, 0.1, 0.05);
                compy.playSound(SoundEvents.FOX_EAT, 0.6F, 1.6F);
                compy.heal(2.0F);
                stack.shrink(1);
                if (stack.isEmpty()) {
                    food.discard();
                } else {
                    food.setItem(stack);
                }
                food = null;
            }
        }
    }
}
