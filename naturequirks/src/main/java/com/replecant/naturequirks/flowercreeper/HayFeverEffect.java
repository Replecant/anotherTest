package com.replecant.naturequirks.flowercreeper;

import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectCategory;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.phys.Vec3;

/** Hay fever: every so often a big sneeze - the panda's sneeze, a spray of droplets, and a little jolt backwards. */
public class HayFeverEffect extends MobEffect {
    private static final int SNEEZE_EVERY = 30;

    public HayFeverEffect() {
        super(MobEffectCategory.HARMFUL, 0xE8CF4A);
    }

    @Override
    public boolean shouldApplyEffectTickThisTick(int duration, int amplifier) {
        return duration % Math.max(10, SNEEZE_EVERY - amplifier * 8) == 5;
    }

    @Override
    public boolean applyEffectTick(ServerLevel level, LivingEntity entity, int amplifier) {
        sneeze(level, entity);
        return true;
    }

    public static void sneeze(ServerLevel level, LivingEntity entity) {
        Vec3 look = entity.getLookAngle();
        Vec3 nose = entity.getEyePosition().add(look.scale(0.45));
        level.playSound(null, entity.getX(), entity.getY(), entity.getZ(), SoundEvents.PANDA_SNEEZE, entity.getSoundSource(),
                1.0F, 0.9F + entity.getRandom().nextFloat() * 0.3F);
        level.sendParticles(ParticleTypes.SNEEZE, nose.x, nose.y, nose.z, 8, look.x * 0.2, 0.05, look.z * 0.2, 0.05);
        entity.push(-look.x * 0.12, 0.02, -look.z * 0.12);
        entity.hurtMarked = true;
    }
}
