package com.replecant.retrocosmos.npc.quest;

import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.npc.CrewRole;
import com.replecant.retrocosmos.npc.ExpeditionMember;
import com.replecant.retrocosmos.tribe.Tribesman;
import com.replecant.retrocosmos.venus.Venus;
import com.replecant.retrocosmos.venus.VenusLanding;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import javax.annotation.Nullable;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSetSubtitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitleTextPacket;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.Entity;

/**
 * Who says what to whom in the Space Rangers storyline, and what happens when an answer is picked. Everything is
 * server-side: {@link #open} decides whether an NPC has story content for a player right now and sends the exchange
 * to the dialogue terminal; {@link #choose} checks the answer really was on offer and acts on it.
 */
public final class QuestDialogues {
    private static final int RANGER_BLUE = 0xFF3A6EA5;
    private static final int CAMP_TEAL = 0xFF2E9C94;
    private static final int TRIBE_AMBER = 0xFFB8742A;
    private static final int DOCTOR_RED = 0xFFB03A3A;
    private static final double TALK_RANGE = 8.0;

    /** What each player was last offered: only those answers are accepted back. */
    private record Pending(int entityId, String dialogueId, Set<String> actions) {}

    private static final Map<UUID, Pending> PENDING = new HashMap<>();

    private QuestDialogues() {}

    // ------------------------------------------------------------------
    // Building and sending exchanges
    // ------------------------------------------------------------------

    private static Component text(String id, Object... args) {
        return Component.translatable("dialogue.retrocosmos." + id, args);
    }

    private static Dialogue.Option option(String action) {
        return new Dialogue.Option(action, Component.translatable("dialogue.retrocosmos.option." + action));
    }

    private static Component title(CrewRole role) {
        return Component.translatable("npc.retrocosmos.title." + role.key);
    }

    static String coords(BlockPos pos) {
        return pos.getX() + ", " + pos.getZ();
    }

    /** Sends an exchange and remembers which answers it offered. */
    static Dialogue show(ServerPlayer player, int entityId, String id, Component speaker, Component role, Component body,
                         int accent, String... actions) {
        List<Dialogue.Option> options = new ArrayList<>();
        for (String action : actions) {
            options.add(option(action));
        }
        Dialogue dialogue = new Dialogue(id, speaker, role, body, options, accent);
        PENDING.put(player.getUUID(), new Pending(entityId, id, new HashSet<>(List.of(actions))));
        QuestNetwork.send(player, entityId, dialogue);
        LAST.put(player.getUUID(), dialogue);
        return dialogue;
    }

    /** The last exchange sent to each player (for the probe and /retrocosmos quest status). */
    static final Map<UUID, Dialogue> LAST = new HashMap<>();

    @Nullable
    public static Dialogue last(ServerPlayer player) {
        return LAST.get(player.getUUID());
    }

    /**
     * Right-click on a crew member: opens their story exchange for this player if they have one now, else returns
     * false (and the crew member trades or chats as usual).
     */
    public static boolean open(ServerPlayer player, ExpeditionMember npc) {
        var server = player.level().getServer();
        if (server == null) {
            return false;
        }
        QuestStage stage = Quest.stage(player);
        QuestWorld world = QuestWorld.get(server);
        int id = npc.getId();
        Component name = npc.getName();
        switch (npc.role()) {
            case RANGER -> {
                Component role = title(CrewRole.RANGER);
                if (stage == QuestStage.NONE) {
                    show(player, id, "ranger.recruit", name, role, text("ranger.recruit"), RANGER_BLUE, "join", "decline");
                    return true;
                }
                boolean card = Quest.has(player, Quest.PROFESSOR_ID);
                if (stage == QuestStage.RETURN_TO_RANGER || (stage.between(QuestStage.GO_TO_VENUS, QuestStage.STORM_INSTITUTE) && card)) {
                    if (card) {
                        show(player, id, "ranger.turn_in", name, role, text("ranger.turn_in"), RANGER_BLUE, "turn_in", "later");
                    } else if (world.cardTurnedIn) {
                        show(player, id, "ranger.report", name, role, text("ranger.report"), RANGER_BLUE, "report");
                    } else {
                        show(player, id, "ranger.waiting", name, role, text("ranger.waiting"), RANGER_BLUE, "ok");
                    }
                    return true;
                }
                return false;
            }
            case LIAISON -> {
                Component role = title(CrewRole.LIAISON);
                if (stage == QuestStage.GO_TO_VENUS) {
                    show(player, id, "liaison.contact", name, role, text("liaison.contact"), CAMP_TEAL, "find_elder", "later");
                    return true;
                }
                if (stage == QuestStage.FIND_ELDER) {
                    show(player, id, "liaison.reminder", name, role, text("liaison.reminder"), CAMP_TEAL, "ok");
                    return true;
                }
                if (stage.between(QuestStage.REPORT_TO_CAMP, QuestStage.RESCUE_EXPEDITION) && world.campRestored) {
                    show(player, id, "liaison.returned", name, role, text("liaison.returned"), CAMP_TEAL, "to_vale");
                    return true;
                }
                return false;
            }
            case DOCTOR -> {
                Component role = Component.translatable("npc.retrocosmos.title.doctor." + npc.variant());
                if (npc.variant() == 0 && npc.isDying() && stage.between(QuestStage.GO_TO_VENUS, QuestStage.REPORT_TO_CAMP)) {
                    BlockPos camp = PrisonCamps.ensure(server, npc.blockPosition());
                    Component body = camp != null ? text("ross.last_words", coords(camp)) : text("ross.last_words.lost");
                    show(player, id, "ross.last_words", name, role, body, DOCTOR_RED, "rescue");
                    return true;
                }
                if (npc.variant() == 1 && !npc.isCaptive()) {
                    if (stage.between(QuestStage.GO_TO_VENUS, QuestStage.RESCUE_EXPEDITION)) {
                        var institute = Quest.institute(server.getLevel(Venus.DIMENSION), world, npc.blockPosition());
                        Component body = institute != null ? text("vale.briefing", coords(institute.pos())) : text("vale.briefing.unknown");
                        show(player, id, "vale.briefing", name, role, body, DOCTOR_RED, "take_card");
                        return true;
                    }
                    if (stage == QuestStage.STORM_INSTITUTE) {
                        if (world.bossDefeated) {
                            show(player, id, "vale.boss_done", name, role, text("vale.boss_done"), DOCTOR_RED, "report_back");
                            return true;
                        }
                        if (!Quest.has(player, Quest.KEYCARD_A)) {
                            show(player, id, "vale.card_again", name, role, text("vale.card_again"), DOCTOR_RED, "take_card");
                            return true;
                        }
                    }
                }
                return false;
            }
            default -> {
                return false;
            }
        }
    }

    /** A tribal chief is the elder: while the player looks for him, a plain right-click talks instead of trading. */
    public static boolean openElder(ServerPlayer player, Tribesman chief) {
        if (Quest.stage(player) != QuestStage.FIND_ELDER || chief.isCaptive()) {
            return false;
        }
        show(player, chief.getId(), "elder.talk", chief.personalName(), Component.translatable("npc.retrocosmos.title.elder"),
                text("elder.talk"), TRIBE_AMBER, "promise");
        return true;
    }

    /** The note Dr. Ross left on the lectern, for whoever comes to the ruined camp after him. */
    public static boolean openNote(ServerPlayer player, BlockPos lectern) {
        var server = player.level().getServer();
        if (server == null || !Quest.stage(player).between(QuestStage.GO_TO_VENUS, QuestStage.REPORT_TO_CAMP)) {
            return false;
        }
        BlockPos camp = PrisonCamps.ensure(server, lectern);
        Component body = camp != null ? text("note.last_words", coords(camp)) : text("ross.last_words.lost");
        show(player, -1, "note.last_words", Component.translatable("npc.retrocosmos.name.doctor.0.0"),
                Component.translatable("npc.retrocosmos.title.note"), body, DOCTOR_RED, "rescue");
        return true;
    }

    // ------------------------------------------------------------------
    // Answers
    // ------------------------------------------------------------------

    /** The player picked {@code action}; acts on it if it really was on offer. Returns whether anything happened. */
    public static boolean choose(ServerPlayer player, int entityId, String dialogueId, String action) {
        Pending pending = PENDING.get(player.getUUID());
        if (pending == null || pending.entityId() != entityId || !pending.dialogueId().equals(dialogueId)
                || !pending.actions().contains(action)) {
            return false;
        }
        PENDING.remove(player.getUUID());
        Entity speaker = entityId >= 0 ? player.level().getEntity(entityId) : null;
        if (entityId >= 0 && (speaker == null || speaker.distanceToSqr(player) > TALK_RANGE * TALK_RANGE * 4)) {
            return false;  // walked away (or the speaker is gone): the answer no longer reaches them
        }
        var server = player.level().getServer();
        QuestWorld world = QuestWorld.get(server);
        ExpeditionMember npc = speaker instanceof ExpeditionMember m ? m : null;
        switch (dialogueId + "/" + action) {
            case "ranger.recruit/join" -> {
                Quest.give(player, Quest.BLASTER, 1);
                Quest.give(player, Quest.CARTRIDGE, 32);
                Quest.set(player, QuestStage.GO_TO_VENUS);
                player.level().playSound(null, player.blockPosition(), SoundEvents.PLAYER_LEVELUP, SoundSource.PLAYERS, 0.8F, 1.2F);
                if (npc != null) {
                    show(player, entityId, "ranger.briefing", npc.getName(), title(CrewRole.RANGER), text("ranger.briefing"),
                            RANGER_BLUE, "venus_ok");
                }
            }
            case "ranger.recruit/decline" -> player.displayClientMessage(Component.translatable("chat.retrocosmos.npc.say",
                    speaker != null ? speaker.getName() : Component.empty(), Component.translatable("dialogue.retrocosmos.ranger.declined")), false);
            case "ranger.turn_in/turn_in" -> {
                if (Quest.takeOne(player, Quest.PROFESSOR_ID)) {
                    world.cardTurnedIn = true;
                    world.setDirty();
                    reward(player);
                }
            }
            case "ranger.report/report" -> reward(player);
            case "liaison.contact/find_elder" -> Quest.set(player, QuestStage.FIND_ELDER);
            case "liaison.returned/to_vale" -> Quest.set(player, QuestStage.RESCUE_EXPEDITION);
            case "elder.talk/promise" -> Quest.set(player, QuestStage.REPORT_TO_CAMP);
            case "ross.last_words/rescue", "note.last_words/rescue" -> {
                Quest.set(player, QuestStage.RESCUE_EXPEDITION);
                if (npc != null && npc.isDying()) {
                    npc.breatheLast();
                }
            }
            case "vale.briefing/take_card" -> {
                Quest.give(player, Quest.KEYCARD_A, 1);
                Quest.set(player, QuestStage.STORM_INSTITUTE);
                if (npc != null && !CampRaid.atCamp(server, npc.blockPosition())) {
                    npc.leave();  // off back to the expedition camp
                }
            }
            case "vale.card_again/take_card" -> Quest.give(player, Quest.KEYCARD_A, 1);
            case "vale.boss_done/report_back" -> Quest.set(player, QuestStage.RETURN_TO_RANGER);
            default -> {
                return false;  // "later", "ok", "venus_ok": nothing to do
            }
        }
        return true;
    }

    /** Sworn in: credits, cartridges, the star, the title - and the whole server hears of it. */
    static void reward(ServerPlayer player) {
        Quest.give(player, Quest.CREDIT, 48);
        Quest.give(player, Quest.CARTRIDGE, 32);
        Quest.give(player, Quest.RANGER_STAR, 1);
        Quest.set(player, QuestStage.COMPLETE, false);
        player.connection.send(new ClientboundSetTitleTextPacket(Component.translatable("title.retrocosmos.space_ranger")
                .withStyle(ChatFormatting.GOLD, ChatFormatting.BOLD)));
        player.connection.send(new ClientboundSetSubtitleTextPacket(Component.translatable("title.retrocosmos.space_ranger.subtitle")
                .withStyle(ChatFormatting.AQUA)));
        Component news = Component.translatable("chat.retrocosmos.quest.sworn_in", player.getDisplayName()).withStyle(ChatFormatting.GOLD);
        player.level().getServer().getPlayerList().broadcastSystemMessage(news, false);
        player.level().playSound(null, player.blockPosition(), SoundEvents.UI_TOAST_CHALLENGE_COMPLETE, SoundSource.PLAYERS, 1.0F, 1.0F);
        RetroCosmos.LOGGER.info("Retro Cosmos quest: {} is a Space Ranger", player.getName().getString());
    }

    static void forget(ServerPlayer player) {
        PENDING.remove(player.getUUID());
    }

    /** For checks: is this level the one the camp stands in. */
    static boolean onVenus(ServerLevel level) {
        return level.dimension() == Venus.DIMENSION && VenusLanding.campPad(level) != null;
    }
}
