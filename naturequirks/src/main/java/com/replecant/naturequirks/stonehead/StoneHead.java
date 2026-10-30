package com.replecant.naturequirks.stonehead;

import javax.annotation.Nullable;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.tags.ItemTags;
import net.minecraft.util.Mth;
import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.damagesource.DamageTypes;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.SpawnGroupData;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.control.BodyRotationControl;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;

/**
 * Stone Head: a great carved head of mossy stone, half buried in a beach. It never moves - only its eyes, and very
 * slowly its head, follow you. Hand it something and it takes one, chews it with a grinding of stone for a few
 * seconds, and spits out a Geode; for a while afterwards it is too full and only grumbles. Swords and arrows barely
 * scratch it; it takes a pickaxe.
 */
public class StoneHead extends PathfinderMob {
    private static final EntityDataAccessor<Boolean> CHEWING = SynchedEntityData.defineId(StoneHead.class, EntityDataSerializers.BOOLEAN);
    private static final EntityDataAccessor<Integer> GRUMBLES = SynchedEntityData.defineId(StoneHead.class, EntityDataSerializers.INT);
    public static final int CHEW_TICKS = 60;
    public static final int COOLDOWN_TICKS = 600;
    public static final int GRUMBLE_TICKS = 24;
    /** Loot luck of a geode chewed from a delicacy. */
    public static final int DELICACY_LUCK = 2;

    private int chewTicks;
    private int cooldown;
    private int mealLuck;
    /** The last geode it spat (for tests). */
    @Nullable
    private ItemEntity lastSpat;
    private int chewClient;
    private int grumbleClient;

    public StoneHead(EntityType<? extends StoneHead> type, Level level) {
        super(type, level);
        this.xpReward = 0;
    }

    public static AttributeSupplier.Builder createAttributes() {
        return PathfinderMob.createMobAttributes()
                .add(Attributes.MAX_HEALTH, 100.0)
                .add(Attributes.ARMOR, 8.0)
                .add(Attributes.MOVEMENT_SPEED, 0.0)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.EXPLOSION_KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 12.0);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(1, new LookAtPlayerGoal(this, Player.class, 10.0F, 1.0F));
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(CHEWING, false);
        builder.define(GRUMBLES, 0);
    }

    /** The body is carved in place: only the head turns. */
    @Override
    protected BodyRotationControl createBodyControl() {
        return new BodyRotationControl(this) {
            @Override
            public void clientTick() {
            }
        };
    }

    @Override
    public int getMaxHeadYRot() {
        return 35;
    }

    @Override
    public int getHeadRotSpeed() {
        return 3;
    }

    // --- an immovable statue ---------------------------------------------------------------------

    @Override
    public boolean isPushable() {
        return false;
    }

    @Override
    public void push(Entity entity) {
    }

    @Override
    public void push(double x, double y, double z) {
    }

    @Override
    public boolean isPushedByFluid() {
        return false;
    }

    @Override
    public boolean removeWhenFarAway(double distance) {
        return false;
    }

    @Override
    public boolean requiresCustomPersistence() {
        return true;
    }

    @Override
    public boolean canBeAffected(MobEffectInstance effect) {
        return false;
    }

    @Nullable
    @Override
    public SpawnGroupData finalizeSpawn(ServerLevelAccessor level, DifficultyInstance difficulty, EntitySpawnReason reason,
                                        @Nullable SpawnGroupData data) {
        setPersistenceRequired();
        // carved facing one of the eight winds
        float yaw = Math.round(getYRot() / 45.0F) * 45.0F;
        setYRot(yaw);
        yBodyRot = yaw;
        yHeadRot = yaw;
        return super.finalizeSpawn(level, difficulty, reason, data);
    }

    // --- only pickaxes really hurt it --------------------------------------------------------------

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (source.is(DamageTypeTags.BYPASSES_INVULNERABILITY)) {
            return super.hurtServer(level, source, amount);
        }
        if (source.is(DamageTypeTags.IS_FIRE) || source.is(DamageTypeTags.IS_DROWNING) || source.is(DamageTypeTags.IS_FALL)
                || source.is(DamageTypeTags.IS_FREEZING) || source.is(DamageTypes.IN_WALL) || source.is(DamageTypes.CACTUS)
                || source.is(DamageTypes.SWEET_BERRY_BUSH) || source.is(DamageTypes.MAGIC) || source.is(DamageTypes.WITHER)) {
            return false;
        }
        boolean pickaxe = source.getDirectEntity() instanceof LivingEntity attacker && attacker.getMainHandItem().is(ItemTags.PICKAXES);
        float dealt;
        if (pickaxe) {
            dealt = amount * 1.5F;
        } else if (source.is(DamageTypeTags.IS_EXPLOSION)) {
            dealt = amount * 0.25F;
        } else {
            dealt = amount * 0.1F;
            playSound(SoundEvents.STONE_HIT, 1.0F, 1.4F);
        }
        Vec3 at = source.getSourcePosition() != null ? source.getSourcePosition() : position();
        level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.MOSSY_COBBLESTONE.defaultBlockState()),
                getX() + (at.x - getX()) * 0.3, getY() + 1.2, getZ() + (at.z - getZ()) * 0.3, pickaxe ? 10 : 4, 0.3, 0.4, 0.3, 0.05);
        return super.hurtServer(level, source, dealt);
    }

    @Override
    public void die(DamageSource source) {
        super.die(source);
        if (level() instanceof ServerLevel server) {
            server.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.MOSSY_COBBLESTONE.defaultBlockState()),
                    getX(), getY() + 1.1, getZ(), 60, 0.6, 0.9, 0.6, 0.1);
            playSound(SoundEvents.STONE_BREAK, 1.5F, 0.6F);
        }
    }

    // --- feeding -----------------------------------------------------------------------------------

    @Override
    protected InteractionResult mobInteract(Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (stack.isEmpty()) {
            return super.mobInteract(player, hand);
        }
        if (level().isClientSide()) {
            return InteractionResult.SUCCESS;
        }
        if (!feed(stack, player)) {
            grumble();
        }
        return InteractionResult.SUCCESS;
    }

    /** Takes one of the offered item and starts chewing; false if it is still chewing or too full. */
    public boolean feed(ItemStack offered, @Nullable LivingEntity by) {
        if (chewTicks > 0 || cooldown > 0 || offered.isEmpty()) {
            return false;
        }
        mealLuck = offered.is(StoneHeads.DELICACIES) ? DELICACY_LUCK : 0;
        if (by != null) {
            offered.consume(1, by);
        } else {
            offered.shrink(1);
        }
        chewTicks = CHEW_TICKS;
        entityData.set(CHEWING, true);
        playSound(SoundEvents.STONE_PLACE, 1.0F, 0.6F);
        return true;
    }

    @Nullable
    public ItemEntity lastSpat() {
        return lastSpat;
    }

    public boolean isChewing() {
        return entityData.get(CHEWING);
    }

    public int cooldown() {
        return cooldown;
    }

    private void grumble() {
        entityData.set(GRUMBLES, entityData.get(GRUMBLES) + 1);
        playSound(SoundEvents.VILLAGER_NO, 1.2F, 0.42F);
        playSound(SoundEvents.GRINDSTONE_USE, 0.4F, 0.5F);
    }

    /** Facing of the head (the mouth points this way). */
    private Vec3 facing() {
        float yaw = yHeadRot * Mth.DEG_TO_RAD;
        return new Vec3(-Mth.sin(yaw), 0.0, Mth.cos(yaw));
    }

    private Vec3 mouth() {
        return position().add(facing().scale(0.72)).add(0.0, 0.72, 0.0);
    }

    @Override
    public void tick() {
        super.tick();
        if (level() instanceof ServerLevel server) {
            if (cooldown > 0) {
                cooldown--;
            }
            if (chewTicks > 0) {
                chewTicks--;
                if (chewTicks % 10 == 5) {
                    playSound(SoundEvents.GRINDSTONE_USE, 0.8F, 0.45F + random.nextFloat() * 0.15F);
                    Vec3 m = mouth();
                    server.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.STONE.defaultBlockState()),
                            m.x, m.y, m.z, 6, 0.2, 0.08, 0.2, 0.05);
                }
                if (chewTicks == 0) {
                    spit(server);
                }
            }
        } else {
            chewClient = isChewing() ? chewClient + 1 : 0;
            if (grumbleClient > 0) {
                grumbleClient--;
            }
        }
    }

    /** Out comes a geode, with a satisfied ptoo. */
    private void spit(ServerLevel server) {
        Vec3 m = mouth();
        Vec3 dir = facing();
        ItemEntity geode = new ItemEntity(server, m.x, m.y, m.z, GeodeItem.create(mealLuck));
        geode.setDeltaMovement(dir.x * 0.28, 0.22, dir.z * 0.28);
        geode.setDefaultPickUpDelay();
        server.addFreshEntity(geode);
        lastSpat = geode;
        playSound(SoundEvents.LLAMA_SPIT, 1.2F, 0.55F);
        playSound(SoundEvents.STONE_HIT, 1.0F, 0.7F);
        server.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.STONE.defaultBlockState()), m.x, m.y, m.z,
                10, 0.15, 0.1, 0.15, 0.12);
        cooldown = COOLDOWN_TICKS;
        mealLuck = 0;
        entityData.set(CHEWING, false);
    }

    @Override
    public void onSyncedDataUpdated(EntityDataAccessor<?> key) {
        super.onSyncedDataUpdated(key);
        if (GRUMBLES.equals(key) && level().isClientSide()) {
            grumbleClient = GRUMBLE_TICKS;
        }
    }

    /** Ticks into the current chew (0 = not chewing), for the jaw animation. */
    public float chewTime(float partialTick) {
        return chewClient > 0 ? chewClient + partialTick : 0.0F;
    }

    /** Ticks left of the current grumble (a slow head shake). */
    public float grumbleTime(float partialTick) {
        return grumbleClient > 0 ? grumbleClient - partialTick : 0.0F;
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putInt("ChewTicks", chewTicks);
        output.putInt("Cooldown", cooldown);
        output.putInt("MealLuck", mealLuck);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        chewTicks = input.getIntOr("ChewTicks", 0);
        cooldown = input.getIntOr("Cooldown", 0);
        mealLuck = input.getIntOr("MealLuck", 0);
        entityData.set(CHEWING, chewTicks > 0);
    }

    @Nullable
    @Override
    protected SoundEvent getAmbientSound() {
        return null;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.STONE_HIT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.STONE_BREAK;
    }

    @Override
    protected void playStepSound(net.minecraft.core.BlockPos pos, BlockState state) {
    }

    @Override
    public float getVoicePitch() {
        return 0.6F + (random.nextFloat() - random.nextFloat()) * 0.05F;
    }
}
