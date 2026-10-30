package com.replecant.retrocosmos.tribe.boss;

import com.replecant.retrocosmos.oinstein.ModOinstein;
import com.replecant.retrocosmos.oinstein.OinsteinBossAnchorBlockEntity;
import com.replecant.retrocosmos.tribe.Tribesman;
import com.replecant.retrocosmos.tribe.mutant.OinsteinForces;
import java.util.EnumSet;
import java.util.List;
import javax.annotation.Nullable;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSetSubtitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitlesAnimationPacket;
import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.world.BossEvent;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.damagesource.DamageTypes;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;

/**
 * Dr. Oinstein in any of his three shapes (the Atomic Strider, the doctor himself, Homo Novus). What they share:
 * the boss bar, the arena anchor and home leash, the encounter reset when everyone leaves, the immunities, the
 * chat lines - and that nothing of Oinstein's ever hurts Oinstein.
 */
public abstract class OinsteinBoss extends Monster {
    /** Beyond this from home he gives up the chase and walks back; beyond LEASH_HARD he is simply back. */
    public static final double LEASH = 28.0;
    public static final double LEASH_HARD = 40.0;
    /** No player within this of home for RESET_TICKS: the encounter resets. */
    public static final double PRESENCE = 48.0;
    public static final int RESET_TICKS = 600;
    /** Who hears him. */
    public static final double VOICE = 40.0;
    /** Persistent-data flag on everything he summons (cleaned up when the encounter resets). */
    public static final String SUMMON_KEY = "retrocosmos.oinstein_summon";

    protected final ServerBossEvent bossEvent;
    @Nullable
    private BlockPos anchor;
    @Nullable
    private Vec3 home;
    private int lonelyTicks;
    private int nextTaunt = 200;
    private int lastTaunt = -1;

    protected OinsteinBoss(EntityType<? extends OinsteinBoss> type, Level level, Component barName, BossEvent.BossBarColor color) {
        super(type, level);
        this.bossEvent = new ServerBossEvent(barName, color, BossEvent.BossBarOverlay.NOTCHED_10);
        this.bossEvent.setDarkenScreen(false);
        setPersistenceRequired();
    }

    // ------------------------------------------------------------------
    // Anchor, home, leash, reset
    // ------------------------------------------------------------------

    public void setAnchor(@Nullable BlockPos anchor) {
        this.anchor = anchor == null ? null : anchor.immutable();
        if (anchor != null) {
            home = Vec3.atBottomCenterOf(anchor);
        }
    }

    @Nullable
    public BlockPos anchor() {
        return anchor;
    }

    public Vec3 home() {
        if (home == null) {
            home = position();
        }
        return home;
    }

    @Nullable
    protected OinsteinBossAnchorBlockEntity anchorEntity() {
        if (anchor == null || !level().isLoaded(anchor)) {
            return null;
        }
        return level().getBlockEntity(anchor) instanceof OinsteinBossAnchorBlockEntity be ? be : null;
    }

    /** Hands the fight over to the next shape: same place, same anchor and home, same target. */
    protected void becomeNext(ServerLevel level, OinsteinBoss next) {
        next.snapTo(getX(), getY(), getZ(), getYRot(), 0.0F);
        next.setYHeadRot(getYHeadRot());
        next.yBodyRot = yBodyRot;
        next.anchor = anchor;
        next.home = home();
        if (getTarget() != null && getTarget().isAlive()) {
            next.setTarget(getTarget());
        }
        level.addFreshEntity(next);
        OinsteinBossAnchorBlockEntity be = anchorEntity();
        if (be != null) {
            be.setBoss(next.getUUID());
        }
        discard();
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        bossEvent.setProgress(barProgress());
        Vec3 h = home();
        double d2 = distanceToSqr(h);
        if (d2 > LEASH_HARD * LEASH_HARD) {
            // dragged or lured out of his lab: back home in a flash of light
            level.sendParticles(ParticleTypes.REVERSE_PORTAL, getX(), getY(1.0) * 0.5 + getY() * 0.5, getZ(), 30, 0.6, 1.0, 0.6, 0.1);
            teleportTo(h.x, h.y, h.z);
            getNavigation().stop();
            level.playSound(null, h.x, h.y, h.z, SoundEvents.ENDERMAN_TELEPORT, getSoundSource(), 1.0F, 0.6F);
        }
        if (getTarget() != null && !canAttack(getTarget())) {
            setTarget(null);
        }
        if (tickCount % 20 == 0) {
            boolean present = false;
            for (ServerPlayer p : level.players()) {
                if (!p.isSpectator() && p.isAlive() && p.distanceToSqr(h) < PRESENCE * PRESENCE) {
                    present = true;
                    break;
                }
            }
            lonelyTicks = present ? 0 : lonelyTicks + 20;
            if (lonelyTicks >= RESET_TICKS) {
                resetEncounter(level);
                return;
            }
        }
        if (getTarget() != null && --nextTaunt <= 0) {
            nextTaunt = 300 + random.nextInt(240);
            taunt(tauntGroup(), tauntCount());
        }
    }

    /** Everyone left: the boss and his summons go, the anchor will bring phase one back at full health. */
    public void resetEncounter(ServerLevel level) {
        OinsteinBossAnchorBlockEntity be = anchorEntity();
        if (be != null) {
            be.reset();
        }
        Vec3 h = home();
        for (Mob mob : level.getEntitiesOfClass(Mob.class, getBoundingBox().inflate(64.0),
                m -> m.getPersistentData().getBooleanOr(SUMMON_KEY, false))) {
            mob.discard();
        }
        level.sendParticles(ParticleTypes.REVERSE_PORTAL, h.x, h.y + 1.0, h.z, 20, 0.5, 1.0, 0.5, 0.05);
        discard();
    }

    protected float barProgress() {
        return getHealth() / getMaxHealth();
    }

    public boolean withinLeash(LivingEntity target) {
        return target.distanceToSqr(home()) < (LEASH + 6.0) * (LEASH + 6.0);
    }

    // ------------------------------------------------------------------
    // Targets and damage
    // ------------------------------------------------------------------

    protected void registerBossTargets() {
        targetSelector.addGoal(1, new HurtByTargetGoal(this) {
            @Override
            public boolean canUse() {
                return !OinsteinForces.isAlly(mob.getLastHurtByMob()) && super.canUse();
            }
        });
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, 10, true, false,
                (target, level) -> OinsteinForces.isEnemy(target)));
        targetSelector.addGoal(3, new NearestAttackableTargetGoal<>(this, Tribesman.class, 10, true, false,
                (target, level) -> OinsteinForces.isEnemy(target)));
    }

    @Override
    public boolean canAttack(LivingEntity target) {
        return !OinsteinForces.isAlly(target) && withinLeash(target) && super.canAttack(target);
    }

    @Override
    public void setTarget(@Nullable LivingEntity target) {
        super.setTarget(target != null && OinsteinForces.isAlly(target) ? null : target);
    }

    /** Falls, water, walls, his own laser fences and his own creatures cannot touch him. */
    protected boolean shrugsOff(DamageSource source) {
        return source.is(DamageTypeTags.IS_FALL) || source.is(DamageTypeTags.IS_DROWNING) || source.is(DamageTypes.IN_WALL)
                || source.is(DamageTypes.CRAMMING) || source.is(DamageTypes.FLY_INTO_WALL) || source.is(ModOinstein.LASER_DAMAGE)
                || OinsteinForces.isAlly(source.getEntity());
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (shrugsOff(source) && !source.is(DamageTypeTags.BYPASSES_INVULNERABILITY)) {
            return false;
        }
        boolean hurt = super.hurtServer(level, source, amount);
        if (hurt && source.getEntity() instanceof LivingEntity attacker) {
            OinsteinForces.rally(level, this, attacker, 24.0);
        }
        return hurt;
    }

    @Override
    public boolean removeWhenFarAway(double distance) {
        return false;
    }

    @Override
    public boolean canBeLeashed() {
        return false;
    }

    @Override
    public boolean isPushable() {
        return false;
    }

    @Override
    protected boolean canRide(Entity vehicle) {
        return false;
    }

    // ------------------------------------------------------------------
    // Boss bar
    // ------------------------------------------------------------------

    @Override
    public void startSeenByPlayer(ServerPlayer player) {
        super.startSeenByPlayer(player);
        bossEvent.addPlayer(player);
    }

    @Override
    public void stopSeenByPlayer(ServerPlayer player) {
        super.stopSeenByPlayer(player);
        bossEvent.removePlayer(player);
    }

    @Override
    public void remove(RemovalReason reason) {
        bossEvent.removeAllPlayers();
        super.remove(reason);
    }

    // ------------------------------------------------------------------
    // Voice
    // ------------------------------------------------------------------

    /** Who is talking (the name in front of his chat lines). */
    protected Component speaker() {
        return Component.translatable("entity.retrocosmos.dr_oinstein").withStyle(ChatFormatting.GREEN);
    }

    protected String tauntGroup() {
        return "strider.taunt";
    }

    protected int tauntCount() {
        return 6;
    }

    protected List<ServerPlayer> listeners(ServerLevel level, double range) {
        return level.getPlayers(p -> p.distanceToSqr(this) < range * range);
    }

    /** One line, {@code chat.retrocosmos.oinstein.<key>}, to every player within earshot. */
    public void say(String key) {
        if (!(level() instanceof ServerLevel level)) {
            return;
        }
        Component line = Component.translatable("chat.retrocosmos.oinstein.say", speaker(),
                Component.translatable("chat.retrocosmos.oinstein." + key).withStyle(ChatFormatting.YELLOW));
        for (ServerPlayer p : listeners(level, VOICE)) {
            p.sendSystemMessage(line);
        }
    }

    /** A random line of a group ({@code <group>.0 .. <group>.<count-1>}), never the same one twice running. */
    public void taunt(String group, int count) {
        int i = random.nextInt(count);
        if (i == lastTaunt && count > 1) {
            i = (i + 1) % count;
        }
        lastTaunt = i;
        nextTaunt = Math.max(nextTaunt, 160);
        say(group + "." + i);
    }

    /** A big on-screen title for every player within range. */
    protected void title(ServerLevel level, Component title, Component subtitle, double range) {
        for (ServerPlayer p : listeners(level, range)) {
            p.connection.send(new ClientboundSetTitlesAnimationPacket(6, 50, 16));
            p.connection.send(new ClientboundSetSubtitleTextPacket(subtitle));
            p.connection.send(new ClientboundSetTitleTextPacket(title));
        }
    }

    @Override
    public boolean killedEntity(ServerLevel level, LivingEntity victim, DamageSource source) {
        if (victim instanceof Player) {
            say("kill." + random.nextInt(3));
        }
        return super.killedEntity(level, victim, source);
    }

    // ------------------------------------------------------------------
    // Summons
    // ------------------------------------------------------------------

    /** Spawns one of his creatures on free ground near {@code around}, marked as a summon, on his target. */
    @Nullable
    protected <T extends Mob> T summon(ServerLevel level, EntityType<T> type, Vec3 around, double radius) {
        BlockPos at = findGround(level, type, around, radius);
        T mob = type.spawn(level, at, EntitySpawnReason.MOB_SUMMONED);
        if (mob != null) {
            mob.getPersistentData().putBoolean(SUMMON_KEY, true);
            mob.setPersistenceRequired();
            if (getTarget() != null) {
                mob.setTarget(getTarget());
            }
        }
        return mob;
    }

    private BlockPos findGround(ServerLevel level, EntityType<?> type, Vec3 around, double radius) {
        for (int attempt = 0; attempt < 16; attempt++) {
            double a = random.nextDouble() * Math.PI * 2.0;
            double r = radius * (0.6 + random.nextDouble() * 0.4);
            BlockPos column = BlockPos.containing(around.x + Math.cos(a) * r, around.y, around.z + Math.sin(a) * r);
            for (int dy = 2; dy >= -3; dy--) {
                BlockPos p = column.above(dy);
                BlockPos below = p.below();
                if (level.getBlockState(below).isFaceSturdy(level, below, Direction.UP)
                        && level.noCollision(type.getSpawnAABB(p.getX() + 0.5, p.getY(), p.getZ() + 0.5))) {
                    return p;
                }
            }
        }
        return BlockPos.containing(around);
    }

    // ------------------------------------------------------------------
    // Save data
    // ------------------------------------------------------------------

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        if (anchor != null) {
            output.store("Anchor", BlockPos.CODEC, anchor);
        }
        if (home != null) {
            output.store("Home", Vec3.CODEC, home);
        }
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        anchor = input.read("Anchor", BlockPos.CODEC).orElse(null);
        home = input.read("Home", Vec3.CODEC).orElse(null);
    }

    // ------------------------------------------------------------------
    // Shared goals
    // ------------------------------------------------------------------

    /** Walks back to the middle of his lab when he has no one to fight, or strayed past the leash. */
    protected static class ReturnHomeGoal extends Goal {
        private final OinsteinBoss boss;

        public ReturnHomeGoal(OinsteinBoss boss) {
            this.boss = boss;
            setFlags(EnumSet.of(Flag.MOVE));
        }

        private double limit() {
            return boss.getTarget() == null ? 6.0 : LEASH;
        }

        @Override
        public boolean canUse() {
            return boss.distanceToSqr(boss.home()) > limit() * limit();
        }

        @Override
        public boolean canContinueToUse() {
            return boss.distanceToSqr(boss.home()) > 3.0 * 3.0 && !boss.getNavigation().isDone();
        }

        @Override
        public void start() {
            Vec3 h = boss.home();
            boss.getNavigation().moveTo(h.x, h.y, h.z, 1.1);
        }
    }
}
