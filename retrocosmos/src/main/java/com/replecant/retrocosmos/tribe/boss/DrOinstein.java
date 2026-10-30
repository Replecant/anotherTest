package com.replecant.retrocosmos.tribe.boss;

import com.replecant.retrocosmos.tribe.ModTribes;
import net.minecraft.ChatFormatting;
import net.minecraft.core.particles.ColorParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.util.Mth;
import net.minecraft.world.BossEvent;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

/**
 * The scripted transition: Dr. Oinstein, thrown out of his wrecked walker, picks himself up, complains about his
 * beautiful machine, pulls out the last syringe of serum and jabs it into his neck. Heartbeats, green fumes, he
 * swells - "I AM HOMO NOVUS!" - and phase two begins. Nothing can hurt him while it plays (about five seconds).
 */
public class DrOinstein extends OinsteinBoss {
    private static final EntityDataAccessor<Integer> SCRIPT = SynchedEntityData.defineId(DrOinstein.class, EntityDataSerializers.INT);
    /** Script beats, in ticks. */
    public static final int LINE_BROKE = 18;
    public static final int STAND_END = 26;
    public static final int SYRINGE = 34;
    public static final int INJECT = 44;
    public static final int GROW_END = 84;
    public static final int SHOUT = 86;
    public static final int END = 98;
    public static final float FINAL_SCALE = 1.55F;
    private static final int[] HEARTBEATS = {INJECT + 2, 56, 65, 72, 77, 81, 84, 87, 90, 93};
    private static final ColorParticleOption SERUM = ColorParticleOption.create(ParticleTypes.ENTITY_EFFECT, 0xFF5AFF6E);

    public DrOinstein(EntityType<? extends DrOinstein> type, Level level) {
        super(type, level, Component.translatable("bossbar.retrocosmos.dr_oinstein"), BossEvent.BossBarColor.GREEN);
        this.xpReward = 0;
        setInvulnerable(true);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 40.0)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.MOVEMENT_SPEED, 0.2)
                .add(Attributes.FOLLOW_RANGE, 40.0);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(1, new LookAtPlayerGoal(this, Player.class, 24.0F, 1.0F));
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(SCRIPT, 0);
    }

    public int script() {
        return entityData.get(SCRIPT);
    }

    @Override
    protected float barProgress() {
        return Mth.clamp(script() / (float) END, 0.0F, 1.0F);
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        // only /kill and the void get through
        return source.is(DamageTypeTags.BYPASSES_INVULNERABILITY) && super.hurtServer(level, source, amount);
    }

    @Override
    public void tick() {
        super.tick();
        if (!(level() instanceof ServerLevel level) || !isAlive()) {
            return;
        }
        int s = script() + 1;
        entityData.set(SCRIPT, s);
        if (s < STAND_END) {
            getNavigation().stop();
        }
        if (s == LINE_BROKE) {
            say("doctor.broke");
            playSound(SoundEvents.VILLAGER_HURT, 1.2F, 0.7F);
        } else if (s == SYRINGE) {
            say("doctor.serum");
            playSound(SoundEvents.BOTTLE_FILL, 1.0F, 1.4F);
        } else if (s == INJECT) {
            say("doctor.inject");
            playSound(SoundEvents.BEE_STING, 1.5F, 0.6F);
            level.sendParticles(SERUM, getX(), getY() + 1.5, getZ(), 30, 0.3, 0.3, 0.3, 1.0);
        } else if (s == SHOUT) {
            title(level, Component.translatable("title.retrocosmos.homo_novus").withStyle(ChatFormatting.GREEN, ChatFormatting.BOLD),
                    Component.translatable("title.retrocosmos.homo_novus.subtitle").withStyle(ChatFormatting.GRAY), PRESENCE);
            say("doctor.shout");
            playSound(SoundEvents.RAVAGER_ROAR, 3.0F, 0.6F);
            playSound(SoundEvents.WARDEN_ROAR, 2.0F, 1.2F);
        }
        for (int beat : HEARTBEATS) {
            if (s == beat) {
                level.playSound(null, getX(), getY(), getZ(), SoundEvents.WARDEN_HEARTBEAT, getSoundSource(), 2.5F, 1.0F);
            }
        }
        if (s > INJECT) {
            double h = getBbHeight();
            level.sendParticles(SERUM, getX(), getY() + h * 0.6, getZ(), 2, 0.3, h * 0.3, 0.3, 1.0);
            if (s % 3 == 0) {
                level.sendParticles(ParticleTypes.HAPPY_VILLAGER, getX(), getY() + h * 0.5, getZ(), 2, 0.4, h * 0.3, 0.4, 0.0);
            }
        }
        if (s > INJECT && s <= GROW_END) {
            float g = (s - INJECT) / (float) (GROW_END - INJECT);
            // he swells in fits and starts, with the heartbeat
            float eased = g * g * (3.0F - 2.0F * g);
            getAttribute(Attributes.SCALE).setBaseValue(1.0F + (FINAL_SCALE - 1.0F) * eased);
        }
        if (s >= END) {
            transform(level);
        }
    }

    private void transform(ServerLevel level) {
        double h = getBbHeight();
        level.sendParticles(SERUM, getX(), getY() + h * 0.5, getZ(), 80, 0.8, h * 0.4, 0.8, 1.0);
        level.sendParticles(ParticleTypes.EXPLOSION, getX(), getY() + h * 0.5, getZ(), 3, 0.4, 0.6, 0.4, 0.0);
        level.sendParticles(ParticleTypes.CLOUD, getX(), getY() + 0.3, getZ(), 30, 0.8, 0.2, 0.8, 0.08);
        level.playSound(null, getX(), getY(), getZ(), SoundEvents.ZOMBIE_VILLAGER_CURE, getSoundSource(), 2.0F, 0.5F);
        HomoNovus novus = ModTribes.HOMO_NOVUS.get().create(level, EntitySpawnReason.TRIGGERED);
        if (novus == null) {
            discard();
            return;
        }
        becomeNext(level, novus);
        novus.say("homo.awake");
    }

    // he is never really out of the fight: the encounter reset still applies, the rest of the base AI does not matter

    @Override
    protected SoundEvent getAmbientSound() {
        return null;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.VILLAGER_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.VILLAGER_DEATH;
    }

    @Override
    public float getVoicePitch() {
        return 0.85F;
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putInt("Script", script());
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        entityData.set(SCRIPT, input.getIntOr("Script", 0));
    }

    // ---- render helpers (client) ----

    /** 1 lying on his back after the fall, 0 standing. */
    public float fallenAmount(float pt) {
        float s = script() + pt;
        if (s < LINE_BROKE) {
            return 1.0F;
        }
        return 1.0F - Mth.clamp((s - LINE_BROKE) / (STAND_END - LINE_BROKE), 0.0F, 1.0F);
    }

    /** The syringe at his neck. */
    public float injectAmount(float pt) {
        float s = script() + pt;
        if (s < SYRINGE) {
            return 0.0F;
        }
        float in = Mth.clamp((s - SYRINGE) / (INJECT - SYRINGE), 0.0F, 1.0F);
        float out = Mth.clamp((s - (GROW_END - 14)) / 10.0F, 0.0F, 1.0F);
        return in * (1.0F - out);
    }

    /** Arms flung out, head back. */
    public float shoutAmount(float pt) {
        float s = script() + pt;
        return Mth.clamp((s - (SHOUT - 6)) / 6.0F, 0.0F, 1.0F);
    }

    /** Convulsions while the serum works. */
    public float shakeAmount(float pt) {
        float s = script() + pt;
        return s > INJECT && s < END ? Math.min(1.0F, (s - INJECT) / 20.0F) : 0.0F;
    }

    public boolean holdsSyringe() {
        int s = script();
        return s >= SYRINGE - 2 && s < GROW_END - 4;
    }
}
