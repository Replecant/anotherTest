package com.replecant.retrocosmos.npc.quest;

import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.npc.CrewRole;
import com.replecant.retrocosmos.npc.ExpeditionMember;
import com.replecant.retrocosmos.tribe.TribeRole;
import com.replecant.retrocosmos.tribe.Tribesman;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.GlobalPos;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.entity.living.LivingDeathEvent;
import net.neoforged.neoforge.event.entity.player.PlayerEvent;
import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent;
import net.neoforged.neoforge.event.tick.PlayerTickEvent;

/**
 * What moves the Space Rangers storyline along outside the dialogues: coming back to the camp (the raid, the
 * restoration, Dr. Hale for older camps), talking to a tribal chief, reading Dr. Ross's note, freeing Dr. Vale and
 * defeating Homo Novus. Also the public hooks for other parts of the mod.
 */
public final class QuestEvents {
    public static final Identifier HOMO_NOVUS = Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "homo_novus");
    private static final Map<UUID, Long> LAST_HINT = new HashMap<>();

    private QuestEvents() {}

    /** Called from ExpeditionNpcs.init: attachments, payloads, game events, the quest command. */
    public static void init(IEventBus modEventBus) {
        QuestAttachments.ATTACHMENTS.register(modEventBus);
        modEventBus.addListener(QuestNetwork::register);
        NeoForge.EVENT_BUS.addListener(QuestEvents::onPlayerTick);
        NeoForge.EVENT_BUS.addListener(QuestEvents::onEntityInteract);
        NeoForge.EVENT_BUS.addListener(QuestEvents::onRightClickBlock);
        NeoForge.EVENT_BUS.addListener(QuestEvents::onLivingDeath);
        NeoForge.EVENT_BUS.addListener(QuestEvents::onLogin);
        NeoForge.EVENT_BUS.addListener(QuestCommands::register);
    }

    private static void onLogin(PlayerEvent.PlayerLoggedInEvent event) {
        if (event.getEntity() instanceof ServerPlayer player) {
            Quest.refreshTarget(player, true);
        }
    }

    private static void onPlayerTick(PlayerTickEvent.Post event) {
        if (event.getEntity() instanceof ServerPlayer player && player.tickCount % 20 == 0 && !player.isSpectator()) {
            tick(player);
        }
    }

    /** Once a second per player: the camp's fortunes, hints, the HUD target. */
    public static void tick(ServerPlayer player) {
        MinecraftServer server = player.level().getServer();
        if (server == null) {
            return;
        }
        QuestStage stage = Quest.stage(player);
        GlobalPos camp = CampRaid.camp(server);
        if (camp != null && player.level().dimension() == camp.dimension() && player.level() instanceof ServerLevel level) {
            QuestWorld world = QuestWorld.get(server);
            double d2 = player.distanceToSqr(Vec3.atCenterOf(camp.pos()));
            if (d2 < 64 * 64) {
                if (stage == QuestStage.REPORT_TO_CAMP && !world.campAttacked && d2 < CampRaid.TRIGGER_RANGE * CampRaid.TRIGGER_RANGE) {
                    CampRaid.attack(level, camp.pos(), player);
                } else if (world.campAttacked && world.expeditionFreed && !world.campRestored) {
                    CampRaid.restore(level, camp.pos());
                }
                if (!world.campInRuins() && player.tickCount % 100 == 0) {
                    CampRaid.ensureLiaison(level, camp.pos());
                }
                if (world.campInRuins() && world.rossGone && world.lectern != null
                        && stage.between(QuestStage.GO_TO_VENUS, QuestStage.REPORT_TO_CAMP)) {
                    long now = level.getGameTime();
                    if (now - LAST_HINT.getOrDefault(player.getUUID(), -10000L) > 20 * 120) {
                        LAST_HINT.put(player.getUUID(), now);
                        player.displayClientMessage(Component.translatable("chat.retrocosmos.quest.ruins_hint").withStyle(ChatFormatting.GRAY), false);
                    }
                }
            }
        }
        if (camp != null && player.level().dimension() == camp.dimension() && player.level() instanceof ServerLevel level) {
            QuestWorld world = QuestWorld.get(server);
            if (world.prisonCamp != null && !world.prisonPopulated
                    && player.distanceToSqr(Vec3.atCenterOf(world.prisonCamp)) < 48 * 48) {
                PrisonCamps.populate(level);
            }
        }
        if (player.tickCount % 100 == 0) {
            Quest.refreshTarget(player, player.tickCount % 1200 == 0);
        }
    }

    /** A tribal chief is the tribe's elder: while the player seeks him, a plain right-click talks, a sneak-click trades. */
    private static void onEntityInteract(PlayerInteractEvent.EntityInteract event) {
        Player player = event.getEntity();
        if (!(event.getTarget() instanceof Tribesman chief) || chief.role() != TribeRole.CHIEF || chief.isBaby() || chief.isCaptive()
                || player.isShiftKeyDown() || Quest.stage(player) != QuestStage.FIND_ELDER) {
            return;
        }
        if (event.getHand() == InteractionHand.MAIN_HAND && player instanceof ServerPlayer sp) {
            QuestDialogues.openElder(sp, chief);
        }
        event.setCancellationResult(InteractionResult.SUCCESS);
        event.setCanceled(true);
    }

    /** Dr. Ross's note on the lectern in the ruined camp tells a latecomer where the expedition was taken. */
    private static void onRightClickBlock(PlayerInteractEvent.RightClickBlock event) {
        if (!(event.getEntity() instanceof ServerPlayer player) || event.getHand() != InteractionHand.MAIN_HAND) {
            return;
        }
        QuestWorld world = QuestWorld.get(player.level().getServer());
        if (world.lectern != null && world.lectern.equals(event.getPos()) && !player.isShiftKeyDown()
                && QuestDialogues.openNote(player, event.getPos())) {
            event.setCancellationResult(InteractionResult.SUCCESS);
            event.setCanceled(true);
        }
    }

    private static void onLivingDeath(LivingDeathEvent event) {
        if (event.getEntity().level() instanceof ServerLevel level && EntityType.getKey(event.getEntity().getType()).equals(HOMO_NOVUS)) {
            onOinsteinDefeated(level, event.getEntity().blockPosition());
        }
    }

    // ------------------------------------------------------------------
    // Hooks
    // ------------------------------------------------------------------

    /**
     * Homo Novus (Dr. Oinstein's last form) is beaten at {@code pos}: everyone storming the Institute within 64 blocks
     * reports back to the rangers next. Safe to call more than once.
     */
    public static void onOinsteinDefeated(ServerLevel level, BlockPos pos) {
        defeat(level, pos, level.getPlayers(p -> !p.isSpectator() && p.distanceToSqr(Vec3.atCenterOf(pos)) < 64.0 * 64.0));
    }

    static void defeat(ServerLevel level, BlockPos pos, java.util.List<ServerPlayer> heroes) {
        QuestWorld world = QuestWorld.get(level.getServer());
        if (!world.bossDefeated) {
            world.bossDefeated = true;
            world.setDirty();
        }
        for (ServerPlayer p : heroes) {
            if (Quest.stage(p).between(QuestStage.GO_TO_VENUS, QuestStage.STORM_INSTITUTE)) {
                Quest.set(p, QuestStage.RETURN_TO_RANGER);
            }
        }
    }

    /**
     * A captive walked out of an open cell. For Dr. Vale: the expedition is free (the camp will be put right) and he
     * briefs his rescuer on the Institute; returns true when he opened that briefing (and so stays to talk).
     */
    public static boolean onCaptiveFreed(ServerLevel level, ExpeditionMember freed, Player player) {
        if (freed.role() != CrewRole.DOCTOR || freed.variant() != 1) {
            return false;
        }
        QuestWorld world = QuestWorld.get(level.getServer());
        if (!world.expeditionFreed) {
            world.expeditionFreed = true;
            world.setDirty();
            RetroCosmos.LOGGER.info("Retro Cosmos quest: Dr. Vale is free - the expedition goes home");
            for (ServerPlayer p : level.getServer().getPlayerList().getPlayers()) {
                if (Quest.stage(p) == QuestStage.RESCUE_EXPEDITION) {
                    Quest.refreshTarget(p);
                }
            }
        }
        return player instanceof ServerPlayer sp && QuestDialogues.open(sp, freed);
    }

    /** Captain Morrow reports where his office is (the RETURN_TO_RANGER target). */
    public static void rangerAt(ServerLevel level, ExpeditionMember ranger) {
        QuestWorld world = QuestWorld.get(level.getServer());
        GlobalPos here = GlobalPos.of(level.dimension(), ranger.blockPosition());
        if (!here.equals(world.ranger)) {
            world.ranger = here;
            world.setDirty();
        }
    }
}
