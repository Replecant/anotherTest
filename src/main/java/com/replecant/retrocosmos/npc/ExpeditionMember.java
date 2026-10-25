package com.replecant.retrocosmos.npc;

import com.mojang.serialization.Codec;
import com.replecant.retrocosmos.tribe.Tribesman;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;
import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.util.Mth;
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
import net.minecraft.world.entity.NeutralMob;
import net.minecraft.world.entity.SpawnGroupData;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.LookAtTradingPlayerGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.TradeWithPlayerGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.npc.villager.AbstractVillager;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.trading.MerchantOffer;
import net.minecraft.world.item.trading.MerchantOffers;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;

/**
 * A human member of the Earth expedition - Dr. Cooper, a camp guard or a scientist (see {@link CrewRole}).
 *
 * <p>They never despawn and never drop anything. Players cannot hurt them (they protest in chat; a sneaking
 * creative-mode player can remove one); the jungle can knock them down to their last heart but they always pull
 * through, and they slowly heal. Dr. Cooper trades through the vanilla merchant screen ({@link CooperTrades}).
 * Guards patrol and shoot at threats ({@link GuardCombatGoal}); scientists work at the camp's instruments
 * ({@link CrewWorkGoal}) and run to the guards when something with teeth shows up ({@link CrewFleeGoal}).
 */
public class ExpeditionMember extends AbstractVillager {
    private static final EntityDataAccessor<Integer> DATA_ROLE = SynchedEntityData.defineId(ExpeditionMember.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> DATA_VARIANT = SynchedEntityData.defineId(ExpeditionMember.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Byte> DATA_ACTION = SynchedEntityData.defineId(ExpeditionMember.class, EntityDataSerializers.BYTE);
    private static final EntityDataAccessor<Byte> DATA_WEAPON = SynchedEntityData.defineId(ExpeditionMember.class, EntityDataSerializers.BYTE);

    // arm poses (synced)
    public static final int ACT_NONE = 0;
    public static final int ACT_TYPING = 1;
    public static final int ACT_NOTES = 2;
    public static final int ACT_INSPECT = 3;
    public static final int ACT_AT_EASE = 4;
    public static final int ACT_SALUTE = 5;
    // what a guard has in hand (synced)
    public static final int WEAPON_NONE = 0;
    public static final int WEAPON_PISTOL = 1;
    public static final int WEAPON_BATON = 2;

    public static final float RAY_DAMAGE = 5.0F;
    private static final int RESTOCK_TICKS = 12000;
    private static final int CHAT_RANGE = 7;

    private boolean assigned;
    private int nameIndex;
    @Nullable
    private BlockPos home;
    private int workAction;
    private int saluteTicks;
    @Nullable
    private Player saluting;
    private boolean fleeing;
    private long lastSpoke = -1000;
    private long lastShout = -1000;
    private int chatterCooldown = 400;
    private long lastRestock;
    private int tradesVersion = CooperTrades.VERSION;
    /** "playerUUID|item id" of every relic type a player has brought to Dr. Cooper. */
    private final Set<String> delivered = new LinkedHashSet<>();
    private int lastLine = -1;
    /** Probe/debug counters. */
    int shotsFired;
    int workSessions;

    public ExpeditionMember(EntityType<? extends ExpeditionMember> type, Level level) {
        super(type, level);
        setPersistenceRequired();
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Mob.createMobAttributes()
                .add(Attributes.MAX_HEALTH, 30.0)
                .add(Attributes.MOVEMENT_SPEED, 0.35)
                .add(Attributes.ATTACK_DAMAGE, 5.0)
                .add(Attributes.ATTACK_KNOCKBACK, 0.6)
                .add(Attributes.FOLLOW_RANGE, 24.0)
                .add(Attributes.ARMOR, 0.0);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(1, new TradeWithPlayerGoal(this));
        goalSelector.addGoal(1, new LookAtTradingPlayerGoal(this));
        goalSelector.addGoal(1, new CrewFleeGoal(this));
        goalSelector.addGoal(2, new GuardCombatGoal(this));
        goalSelector.addGoal(3, new CrewWorkGoal(this));
        goalSelector.addGoal(5, new CrewWanderGoal(this));
        goalSelector.addGoal(7, new LookAtPlayerGoal(this, Player.class, 8.0F));
        goalSelector.addGoal(8, new LookAtPlayerGoal(this, ExpeditionMember.class, 6.0F));
        goalSelector.addGoal(9, new RandomLookAroundGoal(this));

        // guards only: whatever bit them (never a player, a tribesman or a colleague), and threats near the post
        targetSelector.addGoal(1, new HurtByTargetGoal(this, Player.class, Tribesman.class, ExpeditionMember.class) {
            @Override
            public boolean canUse() {
                return role() == CrewRole.GUARD && super.canUse();
            }
        });
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Mob.class, 5, true, false,
                (target, level) -> role() == CrewRole.GUARD && isThreat(target) && nearPost(target)));
    }

    /** Hostile things the guards shoot and the scientists run from: monsters, raptors, angry neutrals. */
    public static boolean isThreat(LivingEntity e) {
        if (!(e instanceof Mob mob) || !e.isAlive() || e instanceof Tribesman || e instanceof ExpeditionMember) {
            return false;
        }
        if (mob instanceof NeutralMob neutral && !neutral.isAngry() && !(mob.getTarget() instanceof Player)
                && !(mob.getTarget() instanceof ExpeditionMember)) {
            return false;
        }
        return e instanceof Enemy;
    }

    boolean nearPost(Entity e) {
        double r = role().radius + 10.0;
        return e.distanceToSqr(home().getCenter()) < r * r || distanceToSqr(e) < 16.0 * 16.0;
    }

    // ------------------------------------------------------------------
    // Identity
    // ------------------------------------------------------------------

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(DATA_ROLE, CrewRole.SCIENTIST.ordinal());
        builder.define(DATA_VARIANT, 0);
        builder.define(DATA_ACTION, (byte) 0);
        builder.define(DATA_WEAPON, (byte) 0);
    }

    public CrewRole role() {
        return CrewRole.byId(entityData.get(DATA_ROLE));
    }

    public int variant() {
        return Mth.clamp(entityData.get(DATA_VARIANT), 0, role().variants - 1);
    }

    public int action() {
        return entityData.get(DATA_ACTION);
    }

    public int weapon() {
        return entityData.get(DATA_WEAPON);
    }

    void setWeapon(int weapon) {
        entityData.set(DATA_WEAPON, (byte) weapon);
    }

    public void setRole(CrewRole role) {
        entityData.set(DATA_ROLE, role.ordinal());
        assigned = true;
        applyRoleStats();
        offers = null;
    }

    private void applyRoleStats() {
        CrewRole role = role();
        getAttribute(Attributes.MAX_HEALTH).setBaseValue(role.health);
        getAttribute(Attributes.ARMOR).setBaseValue(role.armor);
        if (getHealth() > getMaxHealth()) {
            setHealth(getMaxHealth());
        }
        if (home != null) {
            setHomeTo(home, role.radius);
        }
    }

    /** The post this crew member returns to. */
    public BlockPos home() {
        return home != null ? home : blockPosition();
    }

    public void setHome(BlockPos pos) {
        home = pos.immutable();
        setHomeTo(home, role().radius);
    }

    private static int nameCount(CrewRole role, int variant) {
        return CrewLines.names(role == CrewRole.SCIENTIST ? role.key + "." + variant : role.key);
    }

    private String nameKey() {
        CrewRole role = role();
        String group = role == CrewRole.SCIENTIST ? role.key + "." + variant() : role.key;
        return "npc.retrocosmos.name." + group + "." + Mth.clamp(nameIndex, 0, Math.max(0, nameCount(role, variant()) - 1));
    }

    /** "Sgt. Rourke". */
    public Component personalName() {
        return Component.translatable(nameKey());
    }

    /**
     * Picks a look and a name nobody else nearby already has (two Dr. Hayes in one camp would be confusing), and
     * puts the name on the (look-at-only) name tag.
     */
    void pickIdentity(ServerLevel level) {
        CrewRole role = role();
        Set<String> taken = new HashSet<>();
        for (ExpeditionMember other : level.getEntitiesOfClass(ExpeditionMember.class, getBoundingBox().inflate(96.0), m -> m != this)) {
            taken.add(other.role().key + "/" + other.variant() + "/" + other.nameIndex);
        }
        Set<Integer> usedLooks = new HashSet<>();
        for (String t : taken) {
            if (t.startsWith(role.key + "/")) {
                usedLooks.add(Integer.parseInt(t.split("/")[1]));
            }
        }
        // best: a look and a name nobody has; then any free name; then anything
        List<int[]> fresh = new ArrayList<>();
        List<int[]> free = new ArrayList<>();
        List<int[]> all = new ArrayList<>();
        for (int v = 0; v < role.variants; v++) {
            for (int n = 0; n < nameCount(role, v); n++) {
                int[] pick = {v, n};
                all.add(pick);
                if (!taken.contains(role.key + "/" + v + "/" + n) && !takenName(taken, role, n)) {
                    free.add(pick);
                    if (!usedLooks.contains(v)) {
                        fresh.add(pick);
                    }
                }
            }
        }
        List<int[]> pool = !fresh.isEmpty() ? fresh : !free.isEmpty() ? free : all;
        int[] pick = pool.isEmpty() ? new int[]{0, 0} : pool.get(random.nextInt(pool.size()));
        entityData.set(DATA_VARIANT, pick[0]);
        nameIndex = pick[1];
        setCustomName(personalName());
        setCustomNameVisible(false);
    }

    /** Guards' names do not depend on their look: a name is taken whatever the variant. */
    private static boolean takenName(Set<String> taken, CrewRole role, int n) {
        if (role != CrewRole.GUARD) {
            return false;
        }
        for (int v = 0; v < role.variants; v++) {
            if (taken.contains(role.key + "/" + v + "/" + n)) {
                return true;
            }
        }
        return false;
    }

    @Override
    protected Component getTypeName() {
        return Component.translatable("entity.retrocosmos.expedition_member." + role().key);
    }

    @Nullable
    @Override
    public SpawnGroupData finalizeSpawn(ServerLevelAccessor level, DifficultyInstance difficulty, EntitySpawnReason reason,
                                        @Nullable SpawnGroupData data) {
        SpawnGroupData result = super.finalizeSpawn(level, difficulty, reason, data);
        setAge(0);  // never a baby
        setLeftHanded(false);
        if (!assigned) {
            setRole(CrewRole.SCIENTIST);
        }
        applyRoleStats();
        setHealth(getMaxHealth());
        setPersistenceRequired();
        if (home == null) {
            setHome(blockPosition());
        }
        if (level instanceof ServerLevel server && !hasCustomName()) {
            pickIdentity(server);
        }
        return result;
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putString("Role", role().key);
        output.putInt("Variant", variant());
        output.putInt("CrewName", nameIndex);
        output.putBoolean("Assigned", assigned);
        if (home != null) {
            output.putIntArray("Post", new int[]{home.getX(), home.getY(), home.getZ()});
        }
        output.putLong("LastRestock", lastRestock);
        output.putInt("LedgerVersion", tradesVersion);
        if (!delivered.isEmpty()) {
            output.store("Delivered", Codec.STRING.listOf(), new ArrayList<>(delivered));
        }
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        input.getString("Role").ifPresent(key -> {
            entityData.set(DATA_ROLE, CrewRole.byKey(key).ordinal());
            assigned = true;
        });
        entityData.set(DATA_VARIANT, Math.max(0, input.getIntOr("Variant", 0)));
        nameIndex = Math.max(0, input.getIntOr("CrewName", 0));
        assigned = assigned || input.getBooleanOr("Assigned", false);
        input.getIntArray("Post").filter(a -> a.length == 3).ifPresent(a -> home = new BlockPos(a[0], a[1], a[2]));
        lastRestock = input.getLongOr("LastRestock", 0L);
        tradesVersion = input.getIntOr("LedgerVersion", 0);
        delivered.clear();
        input.read("Delivered", Codec.STRING.listOf()).ifPresent(delivered::addAll);
        applyRoleStats();
        if (role() == CrewRole.COOPER && tradesVersion != CooperTrades.VERSION) {
            offers = null;  // the ledger changed (new relics, blueprints...): fresh offers
            tradesVersion = CooperTrades.VERSION;
        }
    }

    // ------------------------------------------------------------------
    // Daily life
    // ------------------------------------------------------------------

    /** Busy with something more important than strolling or tinkering. */
    public boolean isBusy() {
        return getTarget() != null || isTrading() || saluteTicks > 0 || fleeing;
    }

    void setFleeing(boolean fleeing) {
        this.fleeing = fleeing;
        if (fleeing) {
            endWork();
        }
    }

    public boolean isFleeing() {
        return fleeing;
    }

    /** Starts working at something: the pose, and what is in hand. */
    void beginWork(WorkKind kind) {
        workAction = kind.action;
        workSessions++;
        ItemStack tool = ItemStack.EMPTY;
        if (kind == WorkKind.DESK) {
            tool = new ItemStack(Items.WRITABLE_BOOK);
        } else if (kind == WorkKind.DISPLAY && role() == CrewRole.COOPER) {
            tool = new ItemStack(Items.BRUSH);
        }
        setItemSlot(EquipmentSlot.MAINHAND, tool);
    }

    void endWork() {
        workAction = ACT_NONE;
        if (!getMainHandItem().isEmpty()) {
            setItemSlot(EquipmentSlot.MAINHAND, ItemStack.EMPTY);
        }
    }

    /** One tick of work at {@code spot}: the odd swing, a sound, a puff of particles. */
    void workTick(BlockPos spot, WorkKind kind) {
        if (!(level() instanceof ServerLevel level)) {
            return;
        }
        if (workAction != kind.action) {
            beginWork(kind);
        }
        double x = spot.getX() + 0.5;
        double y = spot.getY() + kind.lookHeight;
        double z = spot.getZ() + 0.5;
        int r = random.nextInt(120);
        switch (kind) {
            case CONSOLE -> {
                if (r < 4) {
                    swing(random.nextBoolean() ? InteractionHand.MAIN_HAND : InteractionHand.OFF_HAND);
                    playSound(SoundEvents.UI_BUTTON_CLICK.value(), 0.25F, 1.4F + random.nextFloat() * 0.5F);
                } else if (r == 5) {
                    level.sendParticles(ParticleTypes.ELECTRIC_SPARK, x, y, z, 3, 0.25, 0.15, 0.25, 0.02);
                } else if (r == 6) {
                    playSound(SoundEvents.NOTE_BLOCK_BIT.value(), 0.25F, 0.8F + random.nextFloat());
                }
            }
            case SCOPE -> {
                if (r == 0) {
                    level.sendParticles(ParticleTypes.END_ROD, x, y + 0.6, z, 1, 0.1, 0.1, 0.1, 0.01);
                } else if (r < 3) {
                    swing(InteractionHand.MAIN_HAND);
                }
            }
            case LAB -> {
                if (r < 3) {
                    swing(InteractionHand.MAIN_HAND);
                    level.sendParticles(ParticleTypes.SPLASH, x, y, z, 6, 0.2, 0.05, 0.2, 0.05);
                } else if (r == 4) {
                    playSound(SoundEvents.BREWING_STAND_BREW, 0.3F, 1.2F);
                } else if (r == 5) {
                    level.sendParticles(ParticleTypes.BUBBLE_POP, x, y + 0.2, z, 4, 0.2, 0.1, 0.2, 0.0);
                }
            }
            case PLANT -> {
                if (r < 3) {
                    swing(InteractionHand.MAIN_HAND);
                } else if (r == 4) {
                    level.sendParticles(ParticleTypes.HAPPY_VILLAGER, x, y + 0.3, z, 4, 0.3, 0.3, 0.3, 0.0);
                    playSound(SoundEvents.CROP_PLANTED, 0.4F, 1.3F);
                }
            }
            case DESK -> {
                if (r < 2) {
                    playSound(SoundEvents.BOOK_PAGE_TURN, 0.4F, 1.0F + random.nextFloat() * 0.2F);
                } else if (r == 3) {
                    Vec3 head = getEyePosition();
                    level.sendParticles(ParticleTypes.ENCHANT, head.x, head.y + 0.4, head.z, 6, 0.3, 0.2, 0.3, 0.4);
                }
            }
            case DISPLAY -> {
                if (r < 5) {
                    swing(InteractionHand.MAIN_HAND);
                    playSound(SoundEvents.BRUSH_GENERIC, 0.3F, 1.0F);
                } else if (r == 6) {
                    level.sendParticles(ParticleTypes.WHITE_ASH, x, y, z, 6, 0.25, 0.2, 0.25, 0.01);
                }
            }
        }
    }

    @Nullable
    ExpeditionMember nearestGuard(double range) {
        ExpeditionMember best = null;
        double bestDist = range * range;
        for (ExpeditionMember m : level().getEntitiesOfClass(ExpeditionMember.class, getBoundingBox().inflate(range),
                m -> m.role() == CrewRole.GUARD && m.isAlive())) {
            double d = distanceToSqr(m);
            if (d < bestDist) {
                bestDist = d;
                best = m;
            }
        }
        return best;
    }

    /** Something hurt one of the crew: every guard in earshot turns on it. */
    private void callGuards(LivingEntity attacker) {
        for (ExpeditionMember guard : level().getEntitiesOfClass(ExpeditionMember.class, getBoundingBox().inflate(32.0),
                m -> m.role() == CrewRole.GUARD && m.isAlive() && m != this)) {
            if (guard.getTarget() == null || !guard.getTarget().isAlive()) {
                guard.setTarget(attacker);
            }
        }
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (!assigned) {
            setRole(CrewRole.SCIENTIST);
        }
        if (home == null) {
            setHome(blockPosition());
        }
        if (!hasCustomName()) {
            pickIdentity(level);
        }
        long now = level.getGameTime();
        if (tickCount % 40 == 0 && getHealth() < getMaxHealth() && isAlive()) {
            heal(1.0F);
        }
        if (offers != null && !isTrading() && now - lastRestock > RESTOCK_TICKS) {
            offers.forEach(MerchantOffer::resetUses);
            lastRestock = now;
        }
        int action = workAction;
        if (saluteTicks > 0) {
            saluteTicks--;
            action = ACT_SALUTE;
            getNavigation().stop();
            if (saluting != null) {
                getLookControl().setLookAt(saluting);
            }
        } else if (getTarget() != null || fleeing) {
            action = ACT_NONE;
        } else if (action == ACT_NONE && role() != CrewRole.SCIENTIST && getNavigation().isDone() && !isTrading()) {
            action = ACT_AT_EASE;  // hands clasped behind the back
        }
        entityData.set(DATA_ACTION, (byte) action);
        if (role() != CrewRole.GUARD && weapon() != WEAPON_NONE) {
            setWeapon(WEAPON_NONE);
        }
        if (--chatterCooldown <= 0) {
            chatterCooldown = 900 + random.nextInt(1500);
            chatter(level);
        }
    }

    // ------------------------------------------------------------------
    // Talking
    // ------------------------------------------------------------------

    /** "&lt;Sgt. Rourke&gt; Stay inside the perimeter, civilian." - to one player. */
    void say(Player player, String key) {
        player.displayClientMessage(Component.translatable("chat.retrocosmos.npc.say", getName(), Component.translatable(key)), false);
    }

    /** A random line of a group ("guard.talk"), avoiding saying the same line twice in a row. */
    private String line(String group) {
        int n = Math.max(1, CrewLines.count(group));
        int i = random.nextInt(n);
        if (n > 1 && i == lastLine) {
            i = (i + 1) % n;
        }
        lastLine = i;
        return "chat.retrocosmos.npc." + group + "." + i;
    }

    private List<Player> listeners(double range) {
        return level().getEntitiesOfClass(Player.class, getBoundingBox().inflate(range, 6.0, range), p -> !p.isSpectator());
    }

    /** Thinking out loud, now and then, when somebody is close enough to hear. */
    private void chatter(ServerLevel level) {
        if (isBusy() || random.nextInt(3) == 0) {
            return;
        }
        List<Player> near = listeners(CHAT_RANGE);
        if (near.isEmpty() || !claimCrewVoice()) {
            return;
        }
        String key = line(role().key + ".idle");
        near.forEach(p -> say(p, key));
    }

    /**
     * When the crew last said anything out loud, per dimension: one voice at a time, so three guards don't all
     * report the same raptor.
     */
    private static final java.util.Map<net.minecraft.resources.ResourceKey<net.minecraft.world.level.Level>, Long> LAST_CREW_VOICE =
            new java.util.concurrent.ConcurrentHashMap<>();
    private static final int CREW_VOICE_GAP = 300;

    /** Claims the crew's voice for this speaker if nobody spoke recently. */
    private boolean claimCrewVoice() {
        long now = level().getGameTime();
        long last = LAST_CREW_VOICE.getOrDefault(level().dimension(), -CREW_VOICE_GAP - 1L);
        if (now - last < CREW_VOICE_GAP) {
            return false;
        }
        LAST_CREW_VOICE.put(level().dimension(), now);
        return true;
    }

    /** A shout everyone around hears ("flee", "alert", "kill"), at most every 30 seconds per crew member. */
    void shout(String what) {
        long now = level().getGameTime();
        String group = role().key + "." + what;
        if (now - lastShout < 600 || CrewLines.count(group) == 0 || !claimCrewVoice()) {
            return;
        }
        lastShout = now;
        String key = line(group);
        listeners(24.0).forEach(p -> say(p, key));
    }

    private void protest(Player player) {
        long now = level().getGameTime();
        if (now - lastSpoke < 30) {
            return;
        }
        lastSpoke = now;
        say(player, line(role().key + ".protest"));
        getLookControl().setLookAt(player);
        playSound(SoundEvents.PLAYER_ATTACK_NODAMAGE, 0.8F, 1.0F);
    }

    @Override
    public InteractionResult mobInteract(Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (stack.getItem() instanceof CrewSpawnEggItem || stack.is(Items.NAME_TAG) || !isAlive()) {
            return super.mobInteract(player, hand);
        }
        if (level().isClientSide()) {
            return InteractionResult.SUCCESS;
        }
        long now = level().getGameTime();
        if (role() == CrewRole.COOPER) {
            if (isTrading()) {
                return InteractionResult.SUCCESS;
            }
            MerchantOffers offers = getOffers();
            if (offers.isEmpty()) {
                return InteractionResult.CONSUME;
            }
            if (now - lastSpoke > 20 * 8) {
                lastSpoke = now;
                say(player, line("cooper.greet"));
            }
            endWork();
            setTradingPlayer(player);
            openTradingScreen(player, Component.translatable("entity.retrocosmos.expedition_member.trade_title", getName()), 1);
            return InteractionResult.SUCCESS;
        }
        if (now - lastSpoke >= 20) {
            lastSpoke = now;
            getNavigation().stop();
            getLookControl().setLookAt(player);
            if (role() == CrewRole.GUARD) {
                say(player, line("guard.talk"));
                if (getTarget() == null) {
                    saluteTicks = 30;
                    saluting = player;
                }
            } else {
                say(player, line("scientist.lore"));
            }
        }
        return InteractionResult.SUCCESS;
    }

    // ------------------------------------------------------------------
    // Trading (Dr. Cooper)
    // ------------------------------------------------------------------

    @Override
    protected void updateTrades(ServerLevel level) {
        if (offers == null) {
            offers = new MerchantOffers();
        }
        if (role() == CrewRole.COOPER) {
            offers.addAll(CooperTrades.create());
        }
    }

    @Override
    protected void rewardTradeXp(MerchantOffer offer) {
        if (offer.shouldRewardExp()) {
            level().addFreshEntity(new ExperienceOrb(level(), getX(), getY() + 0.5, getZ(), 1 + random.nextInt(3)));
        }
    }

    @Override
    public void notifyTrade(MerchantOffer offer) {
        super.notifyTrade(offer);
        Player player = getTradingPlayer();
        if (player == null) {
            return;
        }
        if (CooperTrades.isCredit(offer.getResult())) {
            // he bought a relic: is it the first of its kind this player has brought him?
            String id = BuiltInRegistries.ITEM.getKey(offer.getCostA().getItem()).getPath();
            if (delivered.add(player.getUUID() + "|" + id)) {
                say(player, "chat.retrocosmos.npc.cooper.first." + (CooperTrades.EXCITING.contains(id) ? id : "generic"));
                playSound(SoundEvents.PLAYER_LEVELUP, 0.6F, 1.3F);
                if (level() instanceof ServerLevel level) {
                    level.sendParticles(ParticleTypes.HAPPY_VILLAGER, getX(), getY() + 2.1, getZ(), 8, 0.4, 0.2, 0.4, 0.0);
                }
                return;
            }
        }
        if (random.nextInt(4) == 0) {
            say(player, line("cooper.thanks"));
        }
    }

    /** Has this player already brought Dr. Cooper this kind of relic? */
    public boolean hasDelivered(Player player, String itemPath) {
        return delivered.contains(player.getUUID() + "|" + itemPath);
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

    @Override
    public boolean canBeLeashed() {
        return false;
    }

    // ------------------------------------------------------------------
    // Harm, death, persistence
    // ------------------------------------------------------------------

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (source.is(DamageTypeTags.BYPASSES_INVULNERABILITY)) {
            return super.hurtServer(level, source, amount);  // /kill, the void
        }
        Entity attacker = source.getEntity();
        if (attacker instanceof Player player) {
            if (player.isCreative() && player.isShiftKeyDown()) {
                return super.hurtServer(level, source, Math.max(amount, getMaxHealth()));  // builders can clear one away
            }
            protest(player);
            return false;
        }
        if (attacker instanceof ExpeditionMember || role() == CrewRole.COOPER) {
            return false;  // no friendly fire; and nothing on Freedom Station is going to hurt the Doctor
        }
        if (attacker instanceof LivingEntity living && !(attacker instanceof Tribesman)) {
            callGuards(living);
        }
        float allowed = getHealth() - 1.0F;  // knocked down to the last heart, never killed by the jungle
        if (allowed <= 0.0F) {
            return false;
        }
        return super.hurtServer(level, source, Math.min(amount, allowed));
    }

    @Override
    public boolean killedEntity(ServerLevel level, LivingEntity victim, DamageSource source) {
        boolean result = super.killedEntity(level, victim, source);
        if (role() == CrewRole.GUARD) {
            lastShout = -1000;
            shout("kill");
        }
        return result;
    }

    @Override
    protected boolean shouldDropLoot(ServerLevel level) {
        return false;
    }

    @Override
    protected void dropCustomDeathLoot(ServerLevel level, DamageSource source, boolean recentlyHit) {
    }

    @Override
    public boolean shouldDropExperience() {
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

    // ------------------------------------------------------------------
    // Sounds: people, not villagers
    // ------------------------------------------------------------------

    @Nullable
    @Override
    protected SoundEvent getAmbientSound() {
        return null;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.PLAYER_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.PLAYER_DEATH;
    }

    @Override
    public SoundEvent getNotifyTradeSound() {
        return SoundEvents.EXPERIENCE_ORB_PICKUP;
    }

    @Override
    protected SoundEvent getTradeUpdatedSound(boolean success) {
        return success ? SoundEvents.BOOK_PAGE_TURN : SoundEvents.DISPENSER_FAIL;
    }

    @Override
    public float getVoicePitch() {
        return 1.0F;
    }

    /** For the probe: what this crew member has been up to. */
    public String debugState() {
        return String.format("%s[%s v%d %s hp=%.0f pos=%.1f,%.1f,%.1f home=%s act=%d weapon=%d target=%s shots=%d work=%d flee=%s]",
                role().key, getName().getString(), variant(), nameKey(), getHealth(), getX(), getY(), getZ(), home().toShortString(),
                action(), weapon(), getTarget() == null ? "-" : EntityType.getKey(getTarget().getType()).getPath(), shotsFired,
                workSessions, fleeing);
    }

    public int deliveredCount() {
        return delivered.size();
    }
}
