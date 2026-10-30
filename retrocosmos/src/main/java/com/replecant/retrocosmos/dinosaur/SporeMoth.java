package com.replecant.retrocosmos.dinosaur;

import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LightLayer;

/**
 * Spore moth: a fluffy moth of the glowcap hollows. Drifts in lazy loops, sheds glowing spores, and like every
 * moth can't resist a light - torches, lamps and the glowcaps themselves.
 */
public class SporeMoth extends VenusFlier {
    private static final int LIGHT_SEARCH = 10;
    private double loopAngle;
    /** The light it is currently circling, until it loses interest. */
    @Nullable
    private BlockPos lamp;

    public SporeMoth(EntityType<? extends SporeMoth> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Mob.createMobAttributes().add(Attributes.MAX_HEALTH, 3.0);
    }

    /** Looks around for the brightest block light nearby; circles it if there is one. */
    @Nullable
    private BlockPos findLight() {
        BlockPos best = null;
        int bestLight = 9;
        for (int i = 0; i < 12; i++) {
            BlockPos p = blockPosition().offset(random.nextInt(LIGHT_SEARCH * 2 + 1) - LIGHT_SEARCH,
                    random.nextInt(7) - 3, random.nextInt(LIGHT_SEARCH * 2 + 1) - LIGHT_SEARCH);
            int light = level().getBrightness(LightLayer.BLOCK, p);
            if (light > bestLight && level().isEmptyBlock(p)) {
                bestLight = light;
                best = p;
            }
        }
        return best;
    }

    @Nullable
    @Override
    protected BlockPos nextWaypoint() {
        if (lamp != null && (random.nextInt(20) == 0 || level().getBrightness(LightLayer.BLOCK, lamp) < 8)) {
            lamp = null;
        }
        if (lamp == null && random.nextInt(2) == 0) {
            lamp = findLight();
        }
        BlockPos light = lamp;
        BlockPos centre = light != null ? light : blockPosition();
        loopAngle += 0.9 + random.nextDouble() * 0.6;
        double r = light != null ? 1.5 : 3.0 + random.nextDouble() * 3.0;
        int x = centre.getX() + (int) Math.round(Math.cos(loopAngle) * r);
        int z = centre.getZ() + (int) Math.round(Math.sin(loopAngle) * r);
        int ground = groundAt(x, z);
        int y = light != null ? centre.getY() + random.nextInt(2) : Math.max(ground + 1, Math.min(ground + 6, centre.getY() + random.nextInt(3) - 1));
        return new BlockPos(x, y, z);
    }

    @Override
    protected double agility() {
        return 0.06;
    }

    @Override
    protected double topSpeed() {
        return 0.18;
    }

    @Override
    public void tick() {
        super.tick();
        if (level().isClientSide() && random.nextInt(6) == 0) {
            level().addParticle(ParticleTypes.GLOW, getX() + (random.nextDouble() - 0.5) * 0.4, getY() + 0.1,
                    getZ() + (random.nextDouble() - 0.5) * 0.4, 0.0, -0.01, 0.0);
        }
    }

    @Nullable
    @Override
    protected SoundEvent getAmbientSound() {
        return null;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.BAT_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.BAT_DEATH;
    }

    @Override
    public float getVoicePitch() {
        return 1.5F + random.nextFloat() * 0.2F;
    }
}
