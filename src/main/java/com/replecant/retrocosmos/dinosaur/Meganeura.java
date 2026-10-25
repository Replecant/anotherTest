package com.replecant.retrocosmos.dinosaur;

import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.FluidTags;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.level.Level;

/** Meganeura: a giant dragonfly. Hovers, then darts off zig-zagging; likes to patrol over water. */
public class Meganeura extends VenusFlier {
    private int hover;

    public Meganeura(EntityType<? extends Meganeura> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Mob.createMobAttributes().add(Attributes.MAX_HEALTH, 4.0);
    }

    @Nullable
    @Override
    protected BlockPos nextWaypoint() {
        if (hover > 0) {
            hover--;
            return blockPosition();
        }
        if (random.nextInt(3) == 0) {
            hover = 15 + random.nextInt(30);  // hang in the air a moment
        }
        int x = getBlockX() + random.nextInt(13) - 6;
        int z = getBlockZ() + random.nextInt(13) - 6;
        int ground = groundAt(x, z);
        BlockPos over = new BlockPos(x, ground, z);
        // patrol low over water, a little higher over land
        int height = level().getFluidState(over.below()).is(FluidTags.WATER) ? 1 + random.nextInt(2) : 2 + random.nextInt(4);
        return new BlockPos(x, ground + height, z);
    }

    @Override
    protected double agility() {
        return hover > 0 ? 0.3 : 0.18;
    }

    @Override
    protected double topSpeed() {
        return hover > 0 ? 0.02 : 0.55;
    }

    @Override
    public int getMaxSpawnClusterSize() {
        return 4;
    }

    @Nullable
    @Override
    protected SoundEvent getAmbientSound() {
        return random.nextInt(3) == 0 ? SoundEvents.BEE_LOOP : null;
    }

    @Override
    protected float getSoundVolume() {
        return 0.25F;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.SILVERFISH_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.SILVERFISH_DEATH;
    }

    @Override
    public float getVoicePitch() {
        return 1.6F + random.nextFloat() * 0.2F;
    }
}
