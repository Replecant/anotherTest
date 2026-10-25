package com.replecant.retrocosmos.tribe;

import com.replecant.retrocosmos.dinosaur.VenusRaptor;
import java.util.List;
import java.util.UUID;
import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.BlockTags;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.AgeableMob;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.ExperienceOrb;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.SpawnGroupData;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.AvoidEntityGoal;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.LookAtTradingPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.MoveTowardsRestrictionGoal;
import net.minecraft.world.entity.ai.goal.PanicGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.TradeWithPlayerGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.npc.villager.AbstractVillager;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.trading.MerchantOffer;
import net.minecraft.world.item.trading.MerchantOffers;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.pathfinder.PathType;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

/**
 * A primitive hominid of the Venus jungle: stooped, shaggy, painted, and - unless you give it a reason - friendly.
 *
 * <p>Right-click to trade (a vanilla merchant screen; see {@link TribeTrades}). Hit one and its whole camp turns on you
 * for a while. Hunters and the chief chase off raptors that come near the camp, everyone celebrates a kill with a
 * dance, and at night the tribe gathers around the camp fire to squat, grunt and dance.
 */
public class Tribesman extends AbstractVillager {
    private static final EntityDataAccessor<Integer> DATA_ROLE = SynchedEntityData.defineId(Tribesman.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> DATA_VARIANT = SynchedEntityData.defineId(Tribesman.class, EntityDataSerializers.INT);
    /** Bit 1: squatting, bit 2: dancing. */
    private static final EntityDataAccessor<Byte> DATA_ACTION = SynchedEntityData.defineId(Tribesman.class, EntityDataSerializers.BYTE);
    public static final int SIT = 1;
    public static final int DANCE = 2;

    public static final int VARIANTS = 3;
    public static final int NAMES = 16;
    static final double CAMP_RADIUS = 24.0;
    private static final int HOME_RADIUS = 18;
    private static final int ANGER_TICKS = 20 * 60;
    private static final int MURDER_ANGER_TICKS = 20 * 60 * 4;
    private static final int RESTOCK_TICKS = 12000;
    private static final int GREET_COOLDOWN = 20 * 8;

    private boolean assigned;
    private int nameIndex;
    @Nullable
    private BlockPos fire;
    private int fireSearchCooldown;
    @Nullable
    private UUID angryAt;
    private long angerUntil;
    private long lastRestock;
    private int danceTicks;
    private int fireAction;
    private long lastGreet;

    // client-side smoothed pose amounts
    private float sit, sitO, dance, danceO;

    public Tribesman(EntityType<? extends Tribesman> type, Level level) {
        super(type, level);
        // they know better than to walk through the camp fire
        setPathfindingMalus(PathType.DAMAGE_FIRE, -1.0F);
        setPathfindingMalus(PathType.DANGER_FIRE, 16.0F);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Mob.createMobAttributes()
                .add(Attributes.MAX_HEALTH, 24.0)
                .add(Attributes.MOVEMENT_SPEED, 0.32)
                .add(Attributes.ATTACK_DAMAGE, 4.0)
                .add(Attributes.ATTACK_KNOCKBACK, 0.4)
                .add(Attributes.FOLLOW_RANGE, 24.0)
                .add(Attributes.ARMOR, 0.0)
                .add(Attributes.STEP_HEIGHT, 1.0);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(1, new TradeWithPlayerGoal(this));
        goalSelector.addGoal(1, new LookAtTradingPlayerGoal(this));
        // the little ones run from raptors and from anything that hurts them
        goalSelector.addGoal(1, new AvoidEntityGoal<>(this, VenusRaptor.class, 12.0F, 0.9, 1.25) {
            @Override
            public boolean canUse() {
                return (isBaby() || (!role().isWarrior() && getTarget() == null)) && super.canUse();
            }
        });
        goalSelector.addGoal(1, new PanicGoal(this, 1.3) {
            @Override
            public boolean canUse() {
                return isBaby() && super.canUse();
            }
        });
        goalSelector.addGoal(1, new SpearThrowGoal(this));
        goalSelector.addGoal(2, new MeleeAttackGoal(this, 1.2, true) {
            @Override
            public boolean canUse() {
                return !isBaby() && super.canUse();
            }
        });
        goalSelector.addGoal(4, new TribeFireGoal(this));
        goalSelector.addGoal(5, new MoveTowardsRestrictionGoal(this, 0.8));
        goalSelector.addGoal(6, new WaterAvoidingRandomStrollGoal(this, 0.6));
        goalSelector.addGoal(7, new LookAtPlayerGoal(this, Player.class, 8.0F));
        goalSelector.addGoal(8, new LookAtPlayerGoal(this, Tribesman.class, 6.0F));
        goalSelector.addGoal(9, new RandomLookAroundGoal(this));

        // a hurt tribesman calls the others; the children stay out of it
        targetSelector.addGoal(1, new HurtByTargetGoal(this) {
            @Override
            public boolean canUse() {
                return !isBaby() && super.canUse();
            }

            @Override
            protected void alertOther(Mob mob, LivingEntity target) {
                if (!mob.isBaby()) {
                    super.alertOther(mob, target);
                }
            }
        }.setAlertOthers());
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, 10, true, false,
                (target, level) -> !isBaby() && isAngryAt(target)));
        // hunters and the chief keep raptors away from the camp
        targetSelector.addGoal(3, new NearestAttackableTargetGoal<>(this, VenusRaptor.class, 10, true, false,
                (target, level) -> !isBaby() && role().isWarrior() && nearCamp(target)));
    }

    // ------------------------------------------------------------------
    // Identity: role, look, name
    // ------------------------------------------------------------------

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(DATA_ROLE, TribeRole.HUNTER.ordinal());
        builder.define(DATA_VARIANT, 0);
        builder.define(DATA_ACTION, (byte) 0);
    }

    public TribeRole role() {
        return TribeRole.byId(entityData.get(DATA_ROLE));
    }

    public int variant() {
        return Mth.clamp(entityData.get(DATA_VARIANT), 0, VARIANTS - 1);
    }

    public void setRole(TribeRole role) {
        entityData.set(DATA_ROLE, role.ordinal());
        assigned = true;
        applyRoleStats();
        offers = null;
    }

    private void applyRoleStats() {
        TribeRole role = role();
        getAttribute(Attributes.MAX_HEALTH).setBaseValue(role.health);
        getAttribute(Attributes.ATTACK_DAMAGE).setBaseValue(role.damage);
        getAttribute(Attributes.ARMOR).setBaseValue(role.armor);
        getAttribute(Attributes.MOVEMENT_SPEED).setBaseValue(role.speed);
        if (getHealth() > getMaxHealth()) {
            setHealth(getMaxHealth());
        }
    }

    /** First time this tribesman exists: pick a role (mostly hunters and gatherers), a fur colour and a name. */
    private void assignRandomly(RandomSource random) {
        int r = random.nextInt(10);
        TribeRole role = r < 4 ? TribeRole.HUNTER : r < 8 ? TribeRole.GATHERER : r < 9 ? TribeRole.SHAMAN : TribeRole.CHIEF;
        if (!assigned) {
            setRole(role);
        }
        entityData.set(DATA_VARIANT, random.nextInt(VARIANTS));
        nameIndex = random.nextInt(NAMES);
    }

    /** "Grok the Hunter". */
    public Component personalName() {
        return Component.translatable("tribe.retrocosmos.name." + nameIndex);
    }

    @Override
    protected Component getTypeName() {
        return Component.translatable(isBaby() ? "entity.retrocosmos.tribesman.child" : "entity.retrocosmos.tribesman." + role().key);
    }

    private Component tradeTitle() {
        return Component.translatable("entity.retrocosmos.tribesman.title", personalName(),
                Component.translatable("entity.retrocosmos.tribesman." + role().key));
    }

    @Nullable
    @Override
    public SpawnGroupData finalizeSpawn(ServerLevelAccessor level, DifficultyInstance difficulty, EntitySpawnReason reason,
                                        @Nullable SpawnGroupData data) {
        SpawnGroupData result = super.finalizeSpawn(level, difficulty, reason, data);
        boolean keepRole = assigned;
        assignRandomly(level.getRandom());
        if (!keepRole) {
            assigned = true;
        }
        applyRoleStats();
        setHealth(getMaxHealth());
        setPersistenceRequired();
        return result;
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putString("Role", role().key);
        output.putInt("Variant", variant());
        output.putInt("TribeName", nameIndex);
        output.putBoolean("Assigned", assigned);
        output.putLong("LastRestock", lastRestock);
        if (fire != null) {
            output.putIntArray("CampFire", new int[]{fire.getX(), fire.getY(), fire.getZ()});
        }
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        input.getString("Role").ifPresent(key -> {
            entityData.set(DATA_ROLE, TribeRole.byKey(key).ordinal());
            assigned = true;
        });
        entityData.set(DATA_VARIANT, Mth.clamp(input.getInt("Variant").orElseGet(() -> random.nextInt(VARIANTS)), 0, VARIANTS - 1));
        nameIndex = Mth.clamp(input.getInt("TribeName").orElseGet(() -> random.nextInt(NAMES)), 0, NAMES - 1);
        assigned = assigned || input.getBooleanOr("Assigned", false);
        lastRestock = input.getLongOr("LastRestock", 0L);
        input.getIntArray("CampFire").filter(a -> a.length == 3).ifPresent(a -> fire = new BlockPos(a[0], a[1], a[2]));
        applyRoleStats();
    }

    // ------------------------------------------------------------------
    // Camp life
    // ------------------------------------------------------------------

    @Nullable
    public BlockPos campFire() {
        return fire;
    }

    boolean nearCamp(Entity e) {
        BlockPos home = fire != null ? fire : hasHome() ? getHomePosition() : blockPosition();
        return e.distanceToSqr(home.getX() + 0.5, home.getY(), home.getZ() + 0.5) < CAMP_RADIUS * CAMP_RADIUS;
    }

    /** Looks for the camp fire nearby; it becomes this tribesman's home. */
    private void findFire(ServerLevel level) {
        BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
        BlockPos origin = blockPosition();
        BlockPos best = null;
        double bestDist = Double.MAX_VALUE;
        for (int dx = -16; dx <= 16; dx++) {
            for (int dz = -16; dz <= 16; dz++) {
                for (int dy = -6; dy <= 6; dy++) {
                    pos.set(origin.getX() + dx, origin.getY() + dy, origin.getZ() + dz);
                    if (level.isLoaded(pos) && level.getBlockState(pos).is(BlockTags.CAMPFIRES)) {
                        double d = pos.distSqr(origin);
                        if (d < bestDist) {
                            bestDist = d;
                            best = pos.immutable();
                        }
                    }
                }
            }
        }
        if (best != null) {
            fire = best;
            setHomeTo(best, HOME_RADIUS);
        } else if (!hasHome()) {
            setHomeTo(origin, HOME_RADIUS);
        }
    }

    void setFireAction(int action) {
        fireAction = action;
    }

    boolean isNight() {
        long time = Math.floorMod(level().getDayTime(), 24000L);
        return level().isDarkOutside() || (time > 13000L && time < 23000L);
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (!assigned) {
            assignRandomly(random);
            assigned = true;
            setPersistenceRequired();
        }
        if (fireSearchCooldown-- <= 0) {
            fireSearchCooldown = fire == null ? 400 : 1200;
            if (fire == null || !level.getBlockState(fire).is(BlockTags.CAMPFIRES)) {
                fire = null;
                findFire(level);
            }
        }
        long now = level.getGameTime();
        if (angryAt != null && now > angerUntil) {
            angryAt = null;
            if (getTarget() instanceof Player) {
                setTarget(null);
            }
        }
        if (offers != null && !isTrading() && now - lastRestock > RESTOCK_TICKS) {
            offers.forEach(MerchantOffer::resetUses);
            lastRestock = now;
        }
        int action = 0;
        if (danceTicks > 0) {
            danceTicks--;
            action = DANCE;
        } else if (getTarget() == null && !isTrading()) {
            action = fireAction;
        }
        if (action != 0 && (getTarget() != null || isTrading())) {
            action = 0;
        }
        if (action == DANCE && role() == TribeRole.SHAMAN && tickCount % 10 == 0) {
            playSound(SoundEvents.NOTE_BLOCK_BASEDRUM.value(), 0.9F, tickCount % 20 == 0 ? 0.7F : 0.9F);
        }
        if (action != 0) {
            getNavigation().stop();
        }
        entityData.set(DATA_ACTION, (byte) action);
    }

    @Override
    public void tick() {
        super.tick();
        if (level().isClientSide()) {
            int action = entityData.get(DATA_ACTION);
            sitO = sit;
            danceO = dance;
            sit = Mth.approach(sit, (action & SIT) != 0 ? 1.0F : 0.0F, 0.12F);
            dance = Mth.approach(dance, (action & DANCE) != 0 ? 1.0F : 0.0F, 0.15F);
        }
    }

    /** Current {@link #SIT} / {@link #DANCE} bits (synced). */
    public int action() {
        return entityData.get(DATA_ACTION);
    }

    public float sitAmount(float partialTick) {
        return Mth.lerp(partialTick, sitO, sit);
    }

    public float danceAmount(float partialTick) {
        return Mth.lerp(partialTick, danceO, dance);
    }

    /** The whole camp whoops and dances when a raptor goes down. */
    private void celebrate(ServerLevel level) {
        for (Tribesman t : level.getEntitiesOfClass(Tribesman.class, getBoundingBox().inflate(CAMP_RADIUS, 8.0, CAMP_RADIUS),
                t -> t.isAlive() && t.getTarget() == null)) {
            t.danceTicks = 60 + t.random.nextInt(60);
        }
        danceTicks = 100;
        playSound(SoundEvents.PIGLIN_CELEBRATE, 1.2F, 0.6F);
    }

    @Override
    public boolean killedEntity(ServerLevel level, LivingEntity victim, DamageSource source) {
        boolean result = super.killedEntity(level, victim, source);
        if (victim instanceof VenusRaptor) {
            setTarget(null);
            celebrate(level);
        }
        return result;
    }

    @Override
    public boolean doHurtTarget(ServerLevel level, Entity target) {
        boolean hit = super.doHurtTarget(level, target);
        if (hit) {
            playSound(role() == TribeRole.CHIEF ? SoundEvents.RAVAGER_ATTACK : SoundEvents.PIGLIN_ANGRY, 0.8F, getVoicePitch());
        }
        return hit;
    }

    // ------------------------------------------------------------------
    // Anger
    // ------------------------------------------------------------------

    public boolean isAngryAt(LivingEntity entity) {
        return angryAt != null && entity.getUUID().equals(angryAt) && level().getGameTime() <= angerUntil;
    }

    private void angerAt(Player player, int ticks) {
        angryAt = player.getUUID();
        angerUntil = Math.max(angerUntil, level().getGameTime() + ticks);
        if (isTrading()) {
            stopTrading();
        }
        fireAction = 0;
        danceTicks = 0;
        if (!isBaby()) {
            setTarget(player);
        }
    }

    /** Hurting one of the tribe makes the whole camp hostile to that player for a while. */
    private void angerTribe(ServerLevel level, Player player, int ticks) {
        if (player.isCreative() || player.isSpectator()) {
            return;
        }
        boolean alreadyAngry = isAngryAt(player);
        List<Tribesman> camp = level.getEntitiesOfClass(Tribesman.class, getBoundingBox().inflate(CAMP_RADIUS, 10.0, CAMP_RADIUS),
                LivingEntity::isAlive);
        for (Tribesman t : camp) {
            t.angerAt(player, ticks);
        }
        if (!alreadyAngry) {
            say(player, "chat.retrocosmos.tribe.angry");
            playSound(SoundEvents.RAVAGER_ROAR, 0.7F, 1.4F);
        }
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (source.is(DamageTypeTags.IS_FIRE) && fire != null && distanceToSqr(fire.getX() + 0.5, fire.getY(), fire.getZ() + 0.5) < 9.0) {
            return false;  // stepping too close to their own fire only singes the fur
        }
        boolean hurt = super.hurtServer(level, source, amount);
        if (hurt && source.getEntity() instanceof Player player) {
            angerTribe(level, player, ANGER_TICKS);
        }
        return hurt;
    }

    @Override
    public void die(DamageSource source) {
        if (level() instanceof ServerLevel level && source.getEntity() instanceof Player player) {
            angerTribe(level, player, MURDER_ANGER_TICKS);
        }
        super.die(source);
    }

    // ------------------------------------------------------------------
    // Trading
    // ------------------------------------------------------------------

    @Override
    public InteractionResult mobInteract(Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (stack.is(ModTribes.TRIBESMAN_SPAWN_EGG.get()) || !isAlive() || isTrading()) {
            return super.mobInteract(player, hand);
        }
        if (isBaby()) {
            if (!level().isClientSide()) {
                setUnhappyCounter(30);
                playSound(SoundEvents.VILLAGER_AMBIENT, 0.6F, 1.6F);
                say(player, "chat.retrocosmos.tribe.child");
            }
            return InteractionResult.SUCCESS;
        }
        if (isAngryAt(player) || getTarget() != null) {
            if (!level().isClientSide()) {
                setUnhappyCounter(40);
                playSound(SoundEvents.PIGLIN_ANGRY, 0.9F, getVoicePitch());
                if (isAngryAt(player)) {
                    say(player, "chat.retrocosmos.tribe.refuse");
                }
            }
            return InteractionResult.SUCCESS;
        }
        if (!level().isClientSide()) {
            MerchantOffers offers = getOffers();
            if (offers.isEmpty()) {
                return InteractionResult.CONSUME;
            }
            boolean masked = player.getItemBySlot(EquipmentSlot.HEAD).is(ModTribes.TRIBAL_MASK.get());
            for (MerchantOffer offer : offers) {
                int cost = offer.getBaseCostA().getCount();
                offer.setSpecialPriceDiff(masked && cost > 1 ? -Math.max(1, cost / 3) : 0);
            }
            greet(player, masked);
            fireAction = 0;
            setTradingPlayer(player);
            openTradingScreen(player, tradeTitle(), 1);
        }
        return InteractionResult.SUCCESS;
    }

    private void greet(Player player, boolean masked) {
        long now = level().getGameTime();
        if (now - lastGreet < GREET_COOLDOWN) {
            return;
        }
        lastGreet = now;
        if (masked) {
            say(player, "chat.retrocosmos.tribe.mask");
        } else if (random.nextBoolean()) {
            say(player, "chat.retrocosmos.tribe." + role().key + "." + random.nextInt(2));
        } else {
            say(player, "chat.retrocosmos.tribe.greet." + random.nextInt(6));
        }
    }

    /** "&lt;Grok&gt; Ugh! Sky-man bring shiny?" - only the player spoken to sees it. */
    void say(Player player, String key) {
        player.displayClientMessage(Component.translatable("chat.retrocosmos.tribe.say", personalName(), Component.translatable(key)), false);
    }

    @Override
    protected void updateTrades(ServerLevel level) {
        if (offers == null) {
            offers = new MerchantOffers();
        }
        offers.addAll(TribeTrades.create(role(), random));
    }

    @Override
    protected void rewardTradeXp(MerchantOffer offer) {
        if (offer.shouldRewardExp()) {
            level().addFreshEntity(new ExperienceOrb(level(), getX(), getY() + 0.5, getZ(), 2 + random.nextInt(4)));
        }
    }

    @Override
    public void notifyTrade(MerchantOffer offer) {
        super.notifyTrade(offer);
        if (getTradingPlayer() != null && random.nextInt(4) == 0) {
            say(getTradingPlayer(), "chat.retrocosmos.tribe.thanks");
        }
    }

    @Override
    public boolean showProgressBar() {
        return false;
    }

    @Nullable
    @Override
    public AgeableMob getBreedOffspring(ServerLevel level, AgeableMob partner) {
        return null;
    }

    // ------------------------------------------------------------------
    // Persistence & sounds
    // ------------------------------------------------------------------

    @Override
    public boolean removeWhenFarAway(double distance) {
        return false;
    }

    @Override
    public boolean requiresCustomPersistence() {
        return true;
    }

    @Override
    protected SoundEvent getAmbientSound() {
        if (isTrading()) {
            return SoundEvents.VILLAGER_TRADE;
        }
        if (getTarget() != null) {
            return SoundEvents.PIGLIN_ANGRY;
        }
        return random.nextInt(3) == 0 ? SoundEvents.PIGLIN_AMBIENT : SoundEvents.VILLAGER_AMBIENT;
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
    public SoundEvent getNotifyTradeSound() {
        return SoundEvents.VILLAGER_YES;
    }

    @Override
    protected SoundEvent getTradeUpdatedSound(boolean success) {
        return success ? SoundEvents.VILLAGER_YES : SoundEvents.VILLAGER_NO;
    }

    /** Deep, gruff grunts; the chief deepest of all, the children squeaky. */
    @Override
    public float getVoicePitch() {
        float base = isBaby() ? 1.35F : role() == TribeRole.CHIEF ? 0.5F : 0.62F;
        return base + (random.nextFloat() - random.nextFloat()) * 0.08F;
    }
}
