package com.replecant.retrocosmos.tribe.boss;

import com.replecant.retrocosmos.launch.LaunchSite;
import com.replecant.retrocosmos.oinstein.OinsteinBossAnchorBlockEntity;
import com.replecant.retrocosmos.tribe.ModTribes;
import com.replecant.retrocosmos.tribe.Tribesman;
import com.replecant.retrocosmos.tribe.mutant.OinsteinForces;
import java.util.ArrayList;
import java.util.EnumSet;
import java.util.List;
import javax.annotation.Nullable;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ColorParticleOption;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.network.Filterable;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.util.Mth;
import net.minecraft.world.BossEvent;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.component.WrittenBookContent;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;

/**
 * Phase two: Dr. Oinstein after the serum - Homo Novus, a 3-block mutant with the doctor's face, his cracked
 * goggles and a brain swollen out of its skull into a cracked glass flask. Fast and furious: a crouch-and-leap
 * slam (the landing spot is marked), a grab-and-throw, a psychic scream that slows and sickens everyone near him.
 * At a quarter health he flies into a rage and smashes two specimen tanks - two Hominids Novus join in.
 * Beaten, he leaves his final notes, frees every captive in his lab, and the anchor remembers.
 */
public class HomoNovus extends OinsteinBoss {
    private static final EntityDataAccessor<Integer> ACTION = SynchedEntityData.defineId(HomoNovus.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Boolean> RAGE = SynchedEntityData.defineId(HomoNovus.class, EntityDataSerializers.BOOLEAN);
    public static final int NONE = 0;
    public static final int CROUCH = 1;
    public static final int LEAP = 2;
    public static final int SLAM = 3;
    public static final int GRAB = 4;
    public static final int SCREAM = 5;
    public static final int DEATH_TICKS = 50;
    private static final DustParticleOptions RED = new DustParticleOptions(0xFF2020, 1.6F);
    private static final ColorParticleOption SERUM = ColorParticleOption.create(ParticleTypes.ENTITY_EFFECT, 0xFF5AFF6E);

    private boolean raged;
    private int nextSpecial = 40;
    private final float[] amount = new float[6];
    private final float[] amountO = new float[6];

    public HomoNovus(EntityType<? extends HomoNovus> type, Level level) {
        super(type, level, Component.translatable("bossbar.retrocosmos.homo_novus"), BossEvent.BossBarColor.GREEN);
        this.xpReward = 250;
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 200.0)
                .add(Attributes.ARMOR, 4.0)
                .add(Attributes.ATTACK_DAMAGE, 8.0)
                .add(Attributes.ATTACK_KNOCKBACK, 1.0)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.85)
                .add(Attributes.MOVEMENT_SPEED, 0.3)
                .add(Attributes.FOLLOW_RANGE, 40.0)
                .add(Attributes.STEP_HEIGHT, 1.25);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new ReturnHomeGoal(this));
        goalSelector.addGoal(1, new LeapSlamGoal());
        goalSelector.addGoal(1, new GrabGoal());
        goalSelector.addGoal(1, new ScreamGoal());
        goalSelector.addGoal(2, new MeleeAttackGoal(this, 1.15, true));
        goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 24.0F));
        goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        registerBossTargets();
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(ACTION, NONE);
        builder.define(RAGE, false);
    }

    public int action() {
        return entityData.get(ACTION);
    }

    void setAction(int action) {
        entityData.set(ACTION, action);
    }

    public boolean isRaging() {
        return entityData.get(RAGE);
    }

    @Override
    protected Component speaker() {
        return Component.translatable("entity.retrocosmos.homo_novus").withStyle(ChatFormatting.DARK_GREEN);
    }

    @Override
    protected String tauntGroup() {
        return "homo.taunt";
    }

    @Override
    public void tick() {
        super.tick();
        if (level().isClientSide()) {
            int a = action();
            for (int i = 1; i < amount.length; i++) {
                amountO[i] = amount[i];
                boolean on = a == i;
                float speed = i == SLAM ? (on ? 0.6F : 0.15F) : (on ? 0.2F : 0.2F);
                amount[i] = Mth.approach(amount[i], on ? 1.0F : 0.0F, speed);
            }
        } else if (isRaging() && isAlive() && level() instanceof ServerLevel level && tickCount % 4 == 0) {
            level.sendParticles(RED, getX(), getY() + getBbHeight() * 0.6, getZ(), 2, 0.5, 0.7, 0.5, 0.0);
        }
    }

    /** Client: how far into an action's pose (CROUCH .. SCREAM) he is. */
    public float actionAmount(int action, float pt) {
        return Mth.lerp(pt, amountO[action], amount[action]);
    }

    boolean specialReady() {
        return tickCount >= nextSpecial && onGround();
    }

    void specialDone(int pause) {
        nextSpecial = tickCount + pause;
        setAction(NONE);
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        boolean hurt = super.hurtServer(level, source, amount);
        if (hurt && !raged && isAlive() && getHealth() <= getMaxHealth() * 0.25F) {
            rage(level);
        }
        return hurt;
    }

    /** A quarter health left: red fury, faster and harder - and two specimen tanks smashed open. */
    private void rage(ServerLevel level) {
        raged = true;
        entityData.set(RAGE, true);
        say("homo.rage");
        playSound(SoundEvents.RAVAGER_ROAR, 3.0F, 0.55F);
        level.sendParticles(RED, getX(), getY() + 1.5, getZ(), 60, 1.0, 1.2, 1.0, 0.0);
        level.sendParticles(ParticleTypes.ANGRY_VILLAGER, getX(), getY() + getBbHeight(), getZ(), 6, 0.6, 0.3, 0.6, 0.0);
        getAttribute(Attributes.MOVEMENT_SPEED).setBaseValue(0.34);
        getAttribute(Attributes.ATTACK_DAMAGE).setBaseValue(11.0);
        float yaw = yBodyRot * Mth.DEG_TO_RAD;
        Vec3 left = new Vec3(Mth.cos(yaw), 0, Mth.sin(yaw));
        for (int side = -1; side <= 1; side += 2) {
            Vec3 at = position().add(left.scale(side * 4.0));
            var novus = summon(level, ModTribes.HOMINID_NOVUS.get(), at, 1.5);
            if (novus != null) {
                double x = novus.getX(), y = novus.getY() + 1.2, z = novus.getZ();
                level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.GLASS.defaultBlockState()), x, y, z, 60, 0.7, 1.0, 0.7, 0.3);
                level.sendParticles(SERUM, x, y, z, 30, 0.6, 0.8, 0.6, 1.0);
                level.sendParticles(ParticleTypes.SPLASH, x, y, z, 40, 0.8, 0.6, 0.8, 0.2);
                level.playSound(null, x, y, z, SoundEvents.GLASS_BREAK, getSoundSource(), 2.0F, 0.6F);
                level.playSound(null, x, y, z, SoundEvents.GLASS_BREAK, getSoundSource(), 2.0F, 0.9F);
            }
        }
    }

    @Override
    public boolean doHurtTarget(ServerLevel level, Entity target) {
        boolean hit = super.doHurtTarget(level, target);
        if (hit) {
            playSound(SoundEvents.RAVAGER_ATTACK, 1.2F, 0.85F);
        }
        return hit;
    }

    // ------------------------------------------------------------------
    // Defeat
    // ------------------------------------------------------------------

    @Override
    public void die(DamageSource source) {
        boolean first = !isRemoved() && !dead;
        super.die(source);
        if (first && level() instanceof ServerLevel level) {
            setAction(NONE);
            say("homo.death");
            playSound(SoundEvents.WARDEN_DEATH, 2.5F, 1.1F);
            victory(level, source);
        }
    }

    /** The lab is free: the anchor remembers, the captives walk out cheering, everyone there gets the advancement. */
    private void victory(ServerLevel level, DamageSource source) {
        OinsteinBossAnchorBlockEntity be = anchorEntity();
        if (be != null) {
            be.markDefeated();
        }
        List<ServerPlayer> heroes = level.getPlayers(p -> !p.isSpectator() && p.distanceToSqr(this) < 64.0 * 64.0);
        for (ServerPlayer p : heroes) {
            LaunchSite.award(p, "stage2/a_better_ape", "defeated");
        }
        Player hero = source.getEntity() instanceof Player p ? p : (heroes.isEmpty() ? null : heroes.get(0));
        int spoken = 0;
        for (Tribesman t : level.getEntitiesOfClass(Tribesman.class, getBoundingBox().inflate(64.0), Tribesman::isCaptive)) {
            t.liberate(level, hero, spoken++ < 2);
        }
    }

    @Override
    protected void tickDeath() {
        deathTime++;
        if (level() instanceof ServerLevel level && !isRemoved()) {
            double h = getBbHeight();
            if (deathTime % 2 == 0) {
                level.sendParticles(SERUM, getX(), getY() + h * 0.7, getZ(), 3, 0.6, 0.4, 0.6, 1.0);
                level.sendParticles(ParticleTypes.SMOKE, getX(), getY() + h * 0.5, getZ(), 2, 0.6, 0.5, 0.6, 0.02);
            }
            if (deathTime == 22) {
                // the flask gives way
                level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.GLASS.defaultBlockState()),
                        getX(), getY() + 1.0, getZ(), 40, 0.6, 0.4, 0.6, 0.25);
                level.playSound(null, getX(), getY(), getZ(), SoundEvents.GLASS_BREAK, getSoundSource(), 2.0F, 0.7F);
            }
            if (deathTime >= DEATH_TICKS) {
                level.sendParticles(ParticleTypes.POOF, getX(), getY() + 0.5, getZ(), 40, 1.0, 0.5, 1.0, 0.05);
                level.sendParticles(SERUM, getX(), getY() + 0.5, getZ(), 40, 1.0, 0.5, 1.0, 1.0);
                remove(RemovalReason.KILLED);
            }
        }
    }

    @Override
    protected void dropCustomDeathLoot(ServerLevel level, DamageSource source, boolean recentlyHit) {
        super.dropCustomDeathLoot(level, source, recentlyHit);
        spawnAtLocation(level, finalNotes());
    }

    /** "Final Notes of Dr. Oinstein": a written book, its pages translated on the reader's side. */
    public static ItemStack finalNotes() {
        ItemStack book = new ItemStack(Items.WRITTEN_BOOK);
        List<Filterable<Component>> pages = new ArrayList<>();
        for (int i = 0; i < NOTE_PAGES; i++) {
            pages.add(Filterable.passThrough(Component.translatable("book.retrocosmos.oinstein_notes.page" + i)));
        }
        book.set(DataComponents.WRITTEN_BOOK_CONTENT,
                new WrittenBookContent(Filterable.passThrough("Final Notes"), "Dr. Oinstein", 0, pages, true));
        book.set(DataComponents.CUSTOM_NAME, Component.translatable("item.retrocosmos.oinstein_notes")
                .withStyle(s -> s.withItalic(false).withColor(ChatFormatting.GREEN)));
        book.set(DataComponents.RARITY, Rarity.EPIC);
        return book;
    }

    public static final int NOTE_PAGES = 5;

    // ------------------------------------------------------------------
    // Sounds, save data
    // ------------------------------------------------------------------

    @Override
    protected SoundEvent getAmbientSound() {
        return random.nextInt(3) == 0 ? SoundEvents.WARDEN_AGITATED : SoundEvents.RAVAGER_AMBIENT;
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
        playSound(SoundEvents.RAVAGER_STEP, 0.6F, 0.9F);
    }

    @Override
    public float getVoicePitch() {
        return 0.8F + (random.nextFloat() - random.nextFloat()) * 0.05F;
    }

    @Override
    public int getMaxHeadYRot() {
        return 35;
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putBoolean("Raged", raged);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        raged = input.getBooleanOr("Raged", false);
        entityData.set(RAGE, raged);
    }

    // ------------------------------------------------------------------
    // Shared shockwave
    // ------------------------------------------------------------------

    void shockwave(ServerLevel level, Vec3 c, double range, float damage) {
        BlockState ground = level.getBlockState(BlockPos.containing(c.x, getY() - 0.5, c.z));
        level.playSound(null, c.x, c.y, c.z, SoundEvents.GENERIC_EXPLODE.value(), getSoundSource(), 1.6F, 0.6F);
        level.playSound(null, c.x, c.y, c.z, SoundEvents.MACE_SMASH_GROUND_HEAVY, getSoundSource(), 1.6F, 0.7F);
        for (int ring = 1; ring <= (int) range; ring++) {
            int n = 10 + ring * 6;
            for (int k = 0; k < n; k++) {
                double a = Math.PI * 2 * k / n;
                double px = c.x + Math.cos(a) * ring;
                double pz = c.z + Math.sin(a) * ring;
                if (!ground.isAir()) {
                    level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, ground), px, getY() + 0.1, pz, 2, 0.1, 0.05, 0.1, 0.15);
                }
                level.sendParticles(ParticleTypes.POOF, px, getY() + 0.2, pz, 1, 0.05, 0.05, 0.05, 0.02);
            }
        }
        level.sendParticles(SERUM, c.x, getY() + 0.4, c.z, 20, 1.0, 0.2, 1.0, 1.0);
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, getBoundingBox().inflate(range, 2.0, range),
                e -> e != this && e.isAlive() && !OinsteinForces.isAlly(e))) {
            double dx = e.getX() - c.x;
            double dz = e.getZ() - c.z;
            double dist = Math.max(0.5, Math.sqrt(dx * dx + dz * dz));
            if (dist > range + 0.5 || e.getY() > getY() + 2.0) {
                continue;
            }
            float falloff = (float) Mth.clamp(1.2 - dist / (range + 1.0), 0.35, 1.0);
            if (e.hurtServer(level, damageSources().mobAttack(this), damage * falloff)) {
                double resist = 1.0 - e.getAttributeValue(Attributes.KNOCKBACK_RESISTANCE) * 0.6;
                double kb = 0.9 * falloff * resist;
                Vec3 v = e.getDeltaMovement();
                e.setDeltaMovement(v.x * 0.3 + dx / dist * kb, (0.3 + 0.25 * falloff) * resist, v.z * 0.3 + dz / dist * kb);
                e.hurtMarked = true;
            }
        }
    }

    // ------------------------------------------------------------------
    // Goals
    // ------------------------------------------------------------------

    /**
     * Prey 4.5-16 blocks off: he crouches (0.8 s, a roar), a red ring marks where he will come down, he leaps and
     * lands in a 5-block shockwave. The landing spot is fixed at take-off - keep moving.
     */
    class LeapSlamGoal extends Goal {
        private static final int CROUCH_TICKS = 16;
        private int ticks;
        private int cooldown = 10;
        @Nullable
        private Vec3 landing;
        private boolean finished;

        LeapSlamGoal() {
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK, Flag.JUMP));
        }

        @Override
        public boolean canUse() {
            if (cooldown > 0) {
                cooldown--;
                return false;
            }
            LivingEntity t = getTarget();
            if (t == null || !t.isAlive() || !specialReady()) {
                return false;
            }
            double d2 = distanceToSqr(t);
            return d2 > 4.5 * 4.5 && d2 < 16.0 * 16.0 && getSensing().hasLineOfSight(t) && Math.abs(t.getY() - getY()) < 4.0;
        }

        @Override
        public boolean canContinueToUse() {
            return !finished && ticks < 100 && isAlive();
        }

        @Override
        public void start() {
            ticks = 0;
            finished = false;
            landing = null;
            getNavigation().stop();
            setAction(CROUCH);
            playSound(SoundEvents.RAVAGER_ROAR, 1.6F, 1.1F);
        }

        @Override
        public void stop() {
            specialDone(30);
            cooldown = (raged ? 70 : 110) + random.nextInt(30);
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }

        @Override
        public void tick() {
            ticks++;
            LivingEntity t = getTarget();
            if (!(level() instanceof ServerLevel level)) {
                return;
            }
            if (ticks < CROUCH_TICKS) {
                if (t != null) {
                    getLookControl().setLookAt(t, 30.0F, 30.0F);
                }
                return;
            }
            if (ticks == CROUCH_TICKS) {
                if (t == null) {
                    finished = true;
                    return;
                }
                Vec3 to = t.position().subtract(position());
                double d = Math.sqrt(to.x * to.x + to.z * to.z);
                double reach = Math.min(d, 14.0);
                landing = position().add(to.x / d * reach, 0, to.z / d * reach);
                double vh = reach / 9.6;
                setDeltaMovement(to.x / d * vh, 0.8, to.z / d * vh);
                setAction(LEAP);
                setYRot((float) (Mth.atan2(to.z, to.x) * Mth.RAD_TO_DEG) - 90.0F);
                yBodyRot = getYRot();
                playSound(SoundEvents.RAVAGER_ROAR, 2.0F, 0.8F);
                return;
            }
            if (action() == LEAP) {
                // the landing mark
                if (landing != null && ticks % 2 == 0) {
                    for (int k = 0; k < 16; k++) {
                        double a = Math.PI * 2 * k / 16;
                        level.sendParticles(RED, landing.x + Math.cos(a) * 2.5, landing.y + 0.15, landing.z + Math.sin(a) * 2.5, 1, 0, 0, 0, 0);
                    }
                }
                if ((onGround() && ticks > CROUCH_TICKS + 4) || ticks > CROUCH_TICKS + 50) {
                    setAction(SLAM);
                    shockwave(level, position(), 5.0, 10.0F);
                    landTicks = 0;
                }
                return;
            }
            if (++landTicks > 12) {
                finished = true;
            }
        }

        private int landTicks;
    }

    /** Prey within reach: arms out (0.5 s), and if it is still there he picks it up, shakes it and throws it. */
    class GrabGoal extends Goal {
        private static final int REACH = 10;
        private static final int HOLD = 14;
        private int ticks;
        private int cooldown = 80;
        @Nullable
        private LivingEntity held;

        GrabGoal() {
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            if (cooldown > 0) {
                cooldown--;
                return false;
            }
            LivingEntity t = getTarget();
            return t != null && t.isAlive() && specialReady() && distanceToSqr(t) < 3.0 * 3.0;
        }

        @Override
        public boolean canContinueToUse() {
            return isAlive() && ticks <= REACH + HOLD + 2 && (ticks <= REACH || held != null);
        }

        @Override
        public void start() {
            ticks = 0;
            held = null;
            getNavigation().stop();
            setAction(GRAB);
            playSound(SoundEvents.RAVAGER_ATTACK, 1.2F, 0.6F);
        }

        @Override
        public void stop() {
            held = null;
            specialDone(30);
            cooldown = 140 + random.nextInt(40);
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }

        private Vec3 hand() {
            float yaw = yBodyRot * Mth.DEG_TO_RAD;
            return position().add(-Mth.sin(yaw) * 1.5, 1.9, Mth.cos(yaw) * 1.5);
        }

        @Override
        public void tick() {
            ticks++;
            LivingEntity t = getTarget();
            if (!(level() instanceof ServerLevel level)) {
                return;
            }
            if (ticks <= REACH) {
                if (t != null) {
                    getLookControl().setLookAt(t, 30.0F, 30.0F);
                    lookAt(t, 30.0F, 30.0F);
                }
                if (ticks == REACH) {
                    if (t != null && t.isAlive() && distanceToSqr(t) < 3.6 * 3.6 && getSensing().hasLineOfSight(t)) {
                        held = t;
                        t.hurtServer(level, damageSources().mobAttack(HomoNovus.this), 4.0F);
                        playSound(SoundEvents.PLAYER_ATTACK_KNOCKBACK, 1.2F, 0.6F);
                    } else {
                        ticks = REACH + HOLD + 10;  // whiffed
                    }
                }
                return;
            }
            if (held == null) {
                return;
            }
            if (!held.isAlive()) {
                held = null;
                return;
            }
            Vec3 h = hand().subtract(held.position());
            if (ticks < REACH + HOLD) {
                held.setDeltaMovement(h.scale(0.5));
                held.hurtMarked = true;
                held.resetFallDistance();
            } else {
                float yaw = yBodyRot * Mth.DEG_TO_RAD;
                held.hurtServer(level, damageSources().mobAttack(HomoNovus.this), 5.0F);
                double resist = 1.0 - held.getAttributeValue(Attributes.KNOCKBACK_RESISTANCE) * 0.6;
                held.setDeltaMovement(-Mth.sin(yaw) * 1.5 * resist, 0.65 * resist, Mth.cos(yaw) * 1.5 * resist);
                held.hurtMarked = true;
                playSound(SoundEvents.RAVAGER_ROAR, 1.6F, 1.2F);
                held = null;
            }
        }
    }

    /**
     * Prey within 9 blocks: he clutches his head (1 s, a rising whine and swirling motes - run!), then screams.
     * Everyone within 10 blocks is slowed and sickened.
     */
    class ScreamGoal extends Goal {
        private static final int WINDUP = 20;
        private static final double RANGE = 10.0;
        private int ticks;
        private int cooldown = 120;

        ScreamGoal() {
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK, Flag.JUMP));
        }

        @Override
        public boolean canUse() {
            if (cooldown > 0) {
                cooldown--;
                return false;
            }
            LivingEntity t = getTarget();
            return t != null && t.isAlive() && specialReady() && distanceToSqr(t) < 9.0 * 9.0 && random.nextInt(4) == 0;
        }

        @Override
        public boolean canContinueToUse() {
            return isAlive() && ticks < WINDUP + 16;
        }

        @Override
        public void start() {
            ticks = 0;
            getNavigation().stop();
            setAction(SCREAM);
            playSound(SoundEvents.WARDEN_SONIC_CHARGE, 2.0F, 1.1F);
        }

        @Override
        public void stop() {
            specialDone(40);
            cooldown = (raged ? 140 : 220) + random.nextInt(40);
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }

        @Override
        public void tick() {
            ticks++;
            if (!(level() instanceof ServerLevel level)) {
                return;
            }
            double headY = getY() + getBbHeight() * 0.9;
            if (ticks < WINDUP) {
                level.sendParticles(ParticleTypes.ENCHANT, getX(), headY, getZ(), 8, 1.5, 0.8, 1.5, 0.6);
                level.sendParticles(ParticleTypes.WITCH, getX(), headY, getZ(), 2, 0.4, 0.3, 0.4, 0.0);
                return;
            }
            if (ticks == WINDUP) {
                playSound(SoundEvents.WARDEN_ROAR, 2.5F, 1.4F);
                playSound(SoundEvents.ELDER_GUARDIAN_CURSE, 1.0F, 1.3F);
                for (int k = 0; k < 8; k++) {
                    double a = Math.PI * 2 * k / 8;
                    level.sendParticles(ParticleTypes.SONIC_BOOM, getX() + Math.cos(a) * 3.0, headY - 0.6, getZ() + Math.sin(a) * 3.0, 1, 0, 0, 0, 0);
                }
                for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, getBoundingBox().inflate(RANGE),
                        e -> e != HomoNovus.this && e.isAlive() && !OinsteinForces.isAlly(e) && e.distanceToSqr(HomoNovus.this) < RANGE * RANGE)) {
                    e.hurtServer(level, damageSources().indirectMagic(HomoNovus.this, HomoNovus.this), 2.0F);
                    e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 100, 1), HomoNovus.this);
                    e.addEffect(new MobEffectInstance(MobEffects.NAUSEA, 140, 0), HomoNovus.this);
                }
            }
        }
    }
}
