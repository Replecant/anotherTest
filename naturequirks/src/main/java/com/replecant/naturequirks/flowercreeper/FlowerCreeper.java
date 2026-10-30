package com.replecant.naturequirks.flowercreeper;

import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.BlockTags;
import net.minecraft.tags.ItemTags;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.AreaEffectCloud;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.AvoidEntityGoal;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.animal.feline.Cat;
import net.minecraft.world.entity.animal.feline.Ocelot;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/**
 * Flower Creeper: a creeper that took root in a meadow. It stalks, hisses and swells like any creeper - and then
 * bursts into bloom: a soft pop that knocks you back and stings a little, a cloud of pollen that sets you sneezing,
 * and a ring of fresh flowers on the grass. Not a single block is broken.
 */
public class FlowerCreeper extends Monster {
    private static final EntityDataAccessor<Integer> SWELL_DIR = SynchedEntityData.defineId(FlowerCreeper.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Boolean> IGNITED = SynchedEntityData.defineId(FlowerCreeper.class, EntityDataSerializers.BOOLEAN);
    /** Same fuse as a vanilla creeper. */
    static final int MAX_SWELL = 30;
    /** The pop reaches this far (blocks); damage falls off to nothing at the edge. */
    private static final double POP_RADIUS = 5.0;
    /** Point-blank damage: about half of what a creeper deals at a block or two. */
    private static final float POP_DAMAGE = 11.0F;
    private static final int FLOWER_RANGE = 4;
    private static final DustParticleOptions POLLEN = new DustParticleOptions(0xF2D43A, 1.6F);
    private static final DustParticleOptions POLLEN_FINE = new DustParticleOptions(0xFFE98A, 0.9F);
    private static final List<Block> FLOWERS = List.of(Blocks.POPPY, Blocks.DANDELION, Blocks.CORNFLOWER, Blocks.ALLIUM,
            Blocks.OXEYE_DAISY, Blocks.AZURE_BLUET, Blocks.RED_TULIP, Blocks.ORANGE_TULIP, Blocks.PINK_TULIP, Blocks.WHITE_TULIP,
            Blocks.LILY_OF_THE_VALLEY);

    private int oldSwell;
    private int swell;
    /** Flowers planted by the last burst (for tests). */
    private int lastFlowersPlaced = -1;

    public FlowerCreeper(EntityType<? extends FlowerCreeper> type, Level level) {
        super(type, level);
        this.xpReward = 5;
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Monster.createMonsterAttributes().add(Attributes.MOVEMENT_SPEED, 0.25);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(1, new FloatGoal(this));
        goalSelector.addGoal(2, new FlowerCreeperSwellGoal(this));
        goalSelector.addGoal(3, new AvoidEntityGoal<>(this, Ocelot.class, 6.0F, 1.0, 1.2));
        goalSelector.addGoal(3, new AvoidEntityGoal<>(this, Cat.class, 6.0F, 1.0, 1.2));
        goalSelector.addGoal(4, new MeleeAttackGoal(this, 1.0, false));
        goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 0.8));
        goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 8.0F));
        goalSelector.addGoal(6, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new NearestAttackableTargetGoal<>(this, Player.class, true));
        targetSelector.addGoal(2, new HurtByTargetGoal(this));
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(SWELL_DIR, -1);
        builder.define(IGNITED, false);
    }

    public int getSwellDir() {
        return entityData.get(SWELL_DIR);
    }

    public void setSwellDir(int dir) {
        entityData.set(SWELL_DIR, dir);
    }

    /** How many flowers the burst planted (-1 before it burst). */
    public int lastFlowersPlaced() {
        return lastFlowersPlaced;
    }

    public boolean isIgnited() {
        return entityData.get(IGNITED);
    }

    public void ignite() {
        entityData.set(IGNITED, true);
    }

    /** 0 -> 1 over the fuse, like Creeper.getSwelling. */
    public float getSwelling(float partialTick) {
        return Mth.lerp(partialTick, (float) oldSwell, (float) swell) / (MAX_SWELL - 2);
    }

    @Override
    public void tick() {
        if (isAlive()) {
            oldSwell = swell;
            if (isIgnited()) {
                setSwellDir(1);
            }
            int dir = getSwellDir();
            if (dir > 0 && swell == 0) {
                playSound(SoundEvents.CREEPER_PRIMED, 1.0F, 0.5F);
                gameEvent(net.minecraft.world.level.gameevent.GameEvent.PRIME_FUSE);
            }
            swell = Mth.clamp(swell + dir, 0, MAX_SWELL);
            if (swell >= MAX_SWELL) {
                bloom();
            }
        }
        super.tick();
    }

    /** Flint and steel lights the fuse, as with any creeper. */
    @Override
    protected InteractionResult mobInteract(Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (stack.is(ItemTags.CREEPER_IGNITERS)) {
            SoundEvent sound = stack.is(net.minecraft.world.item.Items.FIRE_CHARGE) ? SoundEvents.FIRECHARGE_USE : SoundEvents.FLINTANDSTEEL_USE;
            level().playSound(player, getX(), getY(), getZ(), sound, getSoundSource(), 1.0F, random.nextFloat() * 0.4F + 0.8F);
            if (!level().isClientSide()) {
                ignite();
                if (!stack.isDamageableItem()) {
                    stack.shrink(1);
                } else {
                    stack.hurtAndBreak(1, player, hand == InteractionHand.MAIN_HAND
                            ? net.minecraft.world.entity.EquipmentSlot.MAINHAND : net.minecraft.world.entity.EquipmentSlot.OFFHAND);
                }
            }
            return InteractionResult.SUCCESS;
        }
        return super.mobInteract(player, hand);
    }

    /** The burst: pop and knockback, pollen, a pollen cloud, and flowers - no block damage at all. */
    public void bloom() {
        if (!(level() instanceof ServerLevel server)) {
            return;
        }
        dead = true;
        double x = getX();
        double y = getY();
        double z = getZ();
        server.playSound(null, x, y, z, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 0.7F, 1.7F);
        server.playSound(null, x, y, z, SoundEvents.AZALEA_LEAVES_BREAK, SoundSource.HOSTILE, 1.5F, 0.8F);
        server.playSound(null, x, y, z, SoundEvents.BEE_POLLINATE, SoundSource.HOSTILE, 1.2F, 0.7F);
        server.sendParticles(ParticleTypes.EXPLOSION, x, y + 0.8, z, 1, 0.0, 0.0, 0.0, 0.0);
        server.sendParticles(POLLEN, x, y + 1.0, z, 140, 1.9, 1.1, 1.9, 0.0);
        server.sendParticles(POLLEN_FINE, x, y + 1.4, z, 80, 2.6, 1.4, 2.6, 0.0);
        server.sendParticles(ParticleTypes.FALLING_NECTAR, x, y + 1.6, z, 40, 2.0, 0.8, 2.0, 0.0);
        server.sendParticles(ParticleTypes.CHERRY_LEAVES, x, y + 1.2, z, 30, 1.5, 0.8, 1.5, 0.0);
        for (int i = 0; i < 4; i++) {
            server.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, FLOWERS.get(random.nextInt(4)).defaultBlockState()),
                    x, y + 1.0, z, 12, 1.0, 0.7, 1.0, 0.15);
        }
        pop(server);
        lastFlowersPlaced = plantFlowers(server);
        for (int i = 1 + random.nextInt(2); i > 0; i--) {
            spawnAtLocation(server, new ItemStack(FLOWERS.get(random.nextInt(FLOWERS.size()))));
        }
        AreaEffectCloud cloud = new AreaEffectCloud(server, x, y + 0.2, z);
        cloud.setRadius(3.2F);
        cloud.setRadiusOnUse(-0.3F);
        cloud.setWaitTime(4);
        cloud.setDuration(120);
        cloud.setRadiusPerTick(-3.2F / 120);
        cloud.setCustomParticle(POLLEN);
        cloud.addEffect(new MobEffectInstance(FlowerCreepers.HAY_FEVER, 160, 0));
        cloud.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60, 0));
        server.addFreshEntity(cloud);
        discard();
    }

    /** Damage and knockback falling off with distance; no blocks are touched. */
    private void pop(ServerLevel server) {
        DamageSource source = damageSources().explosion(this, this);
        for (LivingEntity e : server.getEntitiesOfClass(LivingEntity.class, new AABB(blockPosition()).inflate(POP_RADIUS), e -> e != this)) {
            double d = e.distanceTo(this);
            if (d > POP_RADIUS) {
                continue;
            }
            double falloff = 1.0 - d / POP_RADIUS;
            e.hurtServer(server, source, (float) (POP_DAMAGE * falloff));
            Vec3 away = e.position().subtract(position()).add(0, 0.5, 0);
            away = away.lengthSqr() < 1.0E-4 ? new Vec3(0, 1, 0) : away.normalize();
            double kb = 1.3 * falloff * (1.0 - e.getAttributeValue(Attributes.EXPLOSION_KNOCKBACK_RESISTANCE));
            e.push(away.x * kb, 0.25 + away.y * kb * 0.5, away.z * kb);
            e.hurtMarked = true;
        }
    }

    /** Fresh flowers on open grass and dirt around the burst - only where a flower could grow. */
    private int plantFlowers(ServerLevel server) {
        BlockPos origin = blockPosition();
        int placed = 0;
        int wanted = 7 + random.nextInt(5);
        for (int attempt = 0; attempt < 48 && placed < wanted; attempt++) {
            int dx = random.nextInt(FLOWER_RANGE * 2 + 1) - FLOWER_RANGE;
            int dz = random.nextInt(FLOWER_RANGE * 2 + 1) - FLOWER_RANGE;
            if (dx * dx + dz * dz > FLOWER_RANGE * FLOWER_RANGE) {
                continue;
            }
            BlockPos.MutableBlockPos p = origin.offset(dx, 3, dz).mutable();
            for (int dy = 0; dy < 7; dy++, p.move(0, -1, 0)) {
                BlockState here = server.getBlockState(p);
                BlockState below = server.getBlockState(p.below());
                if (!here.isAir()) {
                    continue;
                }
                if (!below.is(BlockTags.DIRT)) {
                    continue;
                }
                BlockState flower = FLOWERS.get(random.nextInt(FLOWERS.size())).defaultBlockState();
                if (flower.canSurvive(server, p)) {
                    server.setBlock(p, flower, Block.UPDATE_ALL);
                    server.sendParticles(ParticleTypes.HAPPY_VILLAGER, p.getX() + 0.5, p.getY() + 0.4, p.getZ() + 0.5, 3, 0.25, 0.2, 0.25, 0.0);
                    placed++;
                }
                break;
            }
        }
        return placed;
    }

    /** Creepers don't bite: getting close is all the attack it needs. */
    @Override
    public boolean doHurtTarget(ServerLevel level, Entity target) {
        return true;
    }

    @Override
    public boolean causeFallDamage(double distance, float multiplier, DamageSource source) {
        boolean hurt = super.causeFallDamage(distance, multiplier, source);
        swell = Math.min(swell + (int) (distance * 1.5), MAX_SWELL - 5);
        return hurt;
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putShort("Fuse", (short) MAX_SWELL);
        output.putBoolean("ignited", isIgnited());
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        entityData.set(IGNITED, input.getBooleanOr("ignited", false));
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.CREEPER_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.CREEPER_DEATH;
    }

    @Override
    protected void playStepSound(BlockPos pos, BlockState state) {
        super.playStepSound(pos, state);
        if (random.nextInt(3) == 0) {
            playSound(SoundEvents.AZALEA_LEAVES_STEP, 0.25F, 1.1F);
        }
    }
}
