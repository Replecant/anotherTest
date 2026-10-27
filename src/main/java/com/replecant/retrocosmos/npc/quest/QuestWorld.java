package com.replecant.retrocosmos.npc.quest;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.core.GlobalPos;
import net.minecraft.server.MinecraftServer;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.saveddata.SavedData;
import net.minecraft.world.level.saveddata.SavedDataType;

/**
 * The world-wide, once-only events of the Space Rangers storyline (kept with the overworld's saved data): the raid on
 * the expedition camp, the prisoner camp's location, the expedition's rescue, the boss. Every player who reaches a
 * stage after somebody else already lived through it still finds what they need (a note, a returned doctor...).
 */
public final class QuestWorld extends SavedData {
    /** A block the raid scorched or wrecked, and what stood there before (for tidying up after the rescue). */
    public record Scorch(BlockPos pos, BlockState original) {
        static final Codec<Scorch> CODEC = RecordCodecBuilder.create(i -> i.group(
                BlockPos.CODEC.fieldOf("pos").forGetter(Scorch::pos),
                BlockState.CODEC.fieldOf("was").forGetter(Scorch::original)
        ).apply(i, Scorch::new));
    }

    static final Codec<QuestWorld> CODEC = RecordCodecBuilder.create(i -> i.group(
            Codec.BOOL.optionalFieldOf("camp_attacked", false).forGetter(d -> d.campAttacked),
            Codec.BOOL.optionalFieldOf("camp_restored", false).forGetter(d -> d.campRestored),
            Codec.BOOL.optionalFieldOf("ross_gone", false).forGetter(d -> d.rossGone),
            Codec.BOOL.optionalFieldOf("expedition_freed", false).forGetter(d -> d.expeditionFreed),
            Codec.BOOL.optionalFieldOf("boss_defeated", false).forGetter(d -> d.bossDefeated),
            Scorch.CODEC.listOf().optionalFieldOf("scorch", List.of()).forGetter(d -> d.scorch),
            BlockPos.CODEC.optionalFieldOf("lectern").forGetter(d -> Optional.ofNullable(d.lectern)),
            BlockPos.CODEC.optionalFieldOf("prison_camp").forGetter(d -> Optional.ofNullable(d.prisonCamp)),
            BlockPos.CODEC.optionalFieldOf("institute").forGetter(d -> Optional.ofNullable(d.institute)),
            GlobalPos.CODEC.optionalFieldOf("ranger").forGetter(d -> Optional.ofNullable(d.ranger)),
            Codec.LONG.optionalFieldOf("attacked_at", 0L).forGetter(d -> d.attackedAt),
            Codec.BOOL.optionalFieldOf("card_turned_in", false).forGetter(d -> d.cardTurnedIn),
            Codec.BOOL.optionalFieldOf("prison_populated", false).forGetter(d -> d.prisonPopulated),
            Codec.BOOL.optionalFieldOf("prison_stockade", false).forGetter(d -> d.prisonStockade)
    ).apply(i, QuestWorld::new));

    static final SavedDataType<QuestWorld> TYPE = new SavedDataType<>("retrocosmos_ranger_quest", QuestWorld::new, CODEC);

    boolean campAttacked;
    boolean campRestored;
    boolean rossGone;
    boolean expeditionFreed;
    boolean bossDefeated;
    final List<Scorch> scorch = new ArrayList<>();
    @Nullable
    BlockPos lectern;
    @Nullable
    BlockPos prisonCamp;
    @Nullable
    BlockPos institute;
    @Nullable
    GlobalPos ranger;
    long attackedAt;
    /** Somebody has handed Professor Oinstein's ID card to the rangers. */
    boolean cardTurnedIn;
    /** The prisoners have been put in their cells (done when a player first comes near: see PrisonCamps.populate). */
    boolean prisonPopulated;
    /** The prisoner camp is the makeshift stockade, not the designed structure. */
    boolean prisonStockade;

    public QuestWorld() {}

    private QuestWorld(boolean campAttacked, boolean campRestored, boolean rossGone, boolean expeditionFreed, boolean bossDefeated,
                       List<Scorch> scorch, Optional<BlockPos> lectern, Optional<BlockPos> prisonCamp, Optional<BlockPos> institute,
                       Optional<GlobalPos> ranger, long attackedAt, boolean cardTurnedIn, boolean prisonPopulated,
                       boolean prisonStockade) {
        this.campAttacked = campAttacked;
        this.campRestored = campRestored;
        this.rossGone = rossGone;
        this.expeditionFreed = expeditionFreed;
        this.bossDefeated = bossDefeated;
        this.scorch.addAll(scorch);
        this.lectern = lectern.orElse(null);
        this.prisonCamp = prisonCamp.orElse(null);
        this.institute = institute.orElse(null);
        this.ranger = ranger.orElse(null);
        this.attackedAt = attackedAt;
        this.cardTurnedIn = cardTurnedIn;
        this.prisonPopulated = prisonPopulated;
        this.prisonStockade = prisonStockade;
    }

    public static QuestWorld get(MinecraftServer server) {
        return server.overworld().getDataStorage().computeIfAbsent(TYPE);
    }

    /** The camp has been raided and its crew taken, and nobody has brought them back yet. */
    public boolean campInRuins() {
        return campAttacked && !campRestored;
    }

    public boolean campAttacked() {
        return campAttacked;
    }

    public boolean expeditionFreed() {
        return expeditionFreed;
    }

    public boolean bossDefeated() {
        return bossDefeated;
    }

    @Nullable
    public BlockPos prisonCamp() {
        return prisonCamp;
    }

    @Nullable
    public GlobalPos ranger() {
        return ranger;
    }

    /** Forgets every world event (for /retrocosmos quest worldreset and tests). */
    void clear() {
        campAttacked = campRestored = rossGone = expeditionFreed = bossDefeated = cardTurnedIn = prisonPopulated = prisonStockade = false;
        scorch.clear();
        lectern = prisonCamp = institute = null;
        attackedAt = 0;
        setDirty();
    }

    String describe() {
        return "attacked=" + campAttacked + " restored=" + campRestored + " rossGone=" + rossGone + " freed=" + expeditionFreed
                + " boss=" + bossDefeated + " scorch=" + scorch.size() + " lectern=" + lectern + " prison=" + prisonCamp
                + " institute=" + institute + " ranger=" + ranger + " cardIn=" + cardTurnedIn + " populated=" + prisonPopulated + " stockade=" + prisonStockade;
    }
}
