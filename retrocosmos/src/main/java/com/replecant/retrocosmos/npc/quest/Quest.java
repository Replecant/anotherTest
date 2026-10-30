package com.replecant.retrocosmos.npc.quest;

import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.launch.LaunchSite;
import com.replecant.retrocosmos.venus.Venus;
import com.replecant.retrocosmos.venus.VenusLanding;
import java.util.Optional;
import javax.annotation.Nullable;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.GlobalPos;
import net.minecraft.core.Holder;
import net.minecraft.core.HolderSet;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.levelgen.structure.Structure;

/**
 * The Space Rangers storyline: reading and moving a player's stage, the objective's map target, the milestone
 * advancements, and the items the story hands out (looked up by id: blaster, cartridges, badge and the professor's
 * ID card belong to other parts of the mod and may not exist yet - then they are simply skipped).
 */
public final class Quest {
    public static final String BLASTER = "retrocosmos:ranger_blaster";
    public static final String CARTRIDGE = "retrocosmos:energy_cartridge";
    public static final String RANGER_STAR = "retrocosmos:ranger_star";
    public static final String PROFESSOR_ID = "retrocosmos:professor_id";
    public static final String CREDIT = "retrocosmos:space_credit";
    public static final String KEYCARD_A = "retrocosmos:keycard_alpha";
    public static final Identifier TRIBAL_CAMP = Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "tribal_camp");
    public static final Identifier INSTITUTE = Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "oinstein_complex");

    private Quest() {}

    public static QuestState state(Player player) {
        return player.getData(QuestAttachments.RANGER_QUEST);
    }

    public static QuestStage stage(Player player) {
        return state(player).stage();
    }

    /** Moves a player to {@code stage}: new map target, the milestone advancement and a "new objective" line. */
    public static void set(ServerPlayer player, QuestStage stage) {
        set(player, stage, true);
    }

    public static void set(ServerPlayer player, QuestStage stage, boolean announce) {
        QuestStage old = stage(player);
        player.setData(QuestAttachments.RANGER_QUEST, new QuestState(stage, target(player, stage, null, true)));
        if (stage.ordinal() > old.ordinal()) {
            for (QuestStage s : QuestStage.values()) {
                if (s.ordinal() > old.ordinal() && s.ordinal() <= stage.ordinal() && milestone(s) != null) {
                    LaunchSite.award(player, "stage2/" + milestone(s), "done");
                }
            }
        }
        if (announce && stage.active()) {
            player.displayClientMessage(Component.translatable("chat.retrocosmos.quest.new_objective",
                    Component.translatable("quest.retrocosmos.objective." + stage.key())).withStyle(ChatFormatting.AQUA), false);
            player.level().playSound(null, player.blockPosition(), SoundEvents.NOTE_BLOCK_CHIME.value(), SoundSource.PLAYERS, 0.7F, 1.6F);
        }
        RetroCosmos.LOGGER.debug("Retro Cosmos quest: {} {} -> {}", player.getName().getString(), old, stage);
    }

    /** The advancement (stage2/...) earned on reaching a stage. */
    @Nullable
    static String milestone(QuestStage stage) {
        return switch (stage) {
            case GO_TO_VENUS -> "rangers_join";
            case REPORT_TO_CAMP -> "rangers_elder";
            case RESCUE_EXPEDITION -> "rangers_last_words";
            case STORM_INSTITUTE -> "rangers_jailbreak";
            case RETURN_TO_RANGER -> "rangers_institute";
            case COMPLETE -> "rangers_complete";
            default -> null;
        };
    }

    /** Recomputes the HUD target (it may become known later: the camp built, the ranger seen, the camp freed). */
    public static void refreshTarget(ServerPlayer player) {
        refreshTarget(player, false);
    }

    /** {@code search}: also run the (costly) structure searches if the target is still unknown. */
    public static void refreshTarget(ServerPlayer player, boolean search) {
        QuestState state = state(player);
        if (!state.stage().active()) {
            if (state.target().isPresent()) {
                player.setData(QuestAttachments.RANGER_QUEST, state.withTarget(Optional.empty()));
            }
            return;
        }
        Optional<GlobalPos> target = target(player, state.stage(), state.target().orElse(null), search);
        if (!target.equals(state.target())) {
            player.setData(QuestAttachments.RANGER_QUEST, state.withTarget(target));
        }
    }

    /** Where the objective of {@code stage} is, if anyone knows. {@code known}: the current target (kept if still good). */
    static Optional<GlobalPos> target(ServerPlayer player, QuestStage stage, @Nullable GlobalPos known, boolean search) {
        var server = player.level().getServer();
        if (server == null) {
            return Optional.empty();
        }
        QuestWorld world = QuestWorld.get(server);
        GlobalPos camp = CampRaid.camp(server);
        ServerLevel venus = camp == null ? server.getLevel(Venus.DIMENSION) : server.getLevel(camp.dimension());
        BlockPos pad = camp == null ? null : camp.pos();
        GlobalPos found = switch (stage) {
            case GO_TO_VENUS, REPORT_TO_CAMP -> camp;
            case FIND_ELDER -> known != null && known.dimension() == Venus.DIMENSION ? known
                    : search ? nearestStructure(venus, TRIBAL_CAMP, pad != null ? pad : player.blockPosition(), 48) : null;
            case RESCUE_EXPEDITION -> world.expeditionFreed() || world.prisonCamp() == null || venus == null ? camp
                    : GlobalPos.of(venus.dimension(), world.prisonCamp());
            case STORM_INSTITUTE -> world.institute != null || search ? institute(venus, world, pad) : known;
            case RETURN_TO_RANGER -> world.ranger();
            default -> null;
        };
        return Optional.ofNullable(found);
    }

    /** Dr. Oinstein's Institute, located once with the structure placement maths and then remembered. */
    @Nullable
    static GlobalPos institute(@Nullable ServerLevel venus, QuestWorld world, @Nullable BlockPos from) {
        if (venus == null) {
            return null;
        }
        if (world.institute != null) {
            return GlobalPos.of(venus.dimension(), world.institute);
        }
        GlobalPos found = nearestStructure(venus, INSTITUTE, from != null ? from : BlockPos.ZERO, 100);
        if (found != null) {
            world.institute = found.pos();
            world.setDirty();
        }
        return found;
    }

    @Nullable
    static GlobalPos nearestStructure(@Nullable ServerLevel level, Identifier id, BlockPos from, int radiusChunks) {
        if (level == null) {
            return null;
        }
        try {
            var registry = level.registryAccess().lookupOrThrow(Registries.STRUCTURE);
            Optional<Holder.Reference<Structure>> holder = registry.get(ResourceKey.create(Registries.STRUCTURE, id));
            if (holder.isEmpty()) {
                return null;
            }
            var nearest = level.getChunkSource().getGenerator().findNearestMapStructure(level, HolderSet.direct(holder.get()),
                    from, radiusChunks, false);
            return nearest == null ? null : GlobalPos.of(level.dimension(), nearest.getFirst());
        } catch (RuntimeException e) {
            RetroCosmos.LOGGER.warn("Retro Cosmos quest: structure search for {} gave up: {}", id, e.toString());
            return null;
        }
    }

    // ------------------------------------------------------------------
    // Items by id
    // ------------------------------------------------------------------

    @Nullable
    static Item item(String id) {
        Item item = BuiltInRegistries.ITEM.getOptional(Identifier.parse(id)).orElse(Items.AIR);
        return item == Items.AIR ? null : item;
    }

    /** Gives {@code count} of an item (dropped at the player's feet if the inventory is full); false if it doesn't exist. */
    static boolean give(ServerPlayer player, String id, int count) {
        Item item = item(id);
        if (item == null) {
            RetroCosmos.LOGGER.info("Retro Cosmos quest: no item {} in this build, skipping the gift", id);
            return false;
        }
        int left = count;
        while (left > 0) {
            int n = Math.min(left, item.getDefaultMaxStackSize());
            ItemStack stack = new ItemStack(item, n);
            if (!player.getInventory().add(stack) && !stack.isEmpty()) {
                player.drop(stack, false);
            }
            left -= n;
        }
        return true;
    }

    public static boolean has(Player player, String id) {
        Item item = item(id);
        return item != null && player.getInventory().contains(new ItemStack(item));
    }

    /** Takes one of an item from the player's inventory; false if they have none. */
    static boolean takeOne(Player player, String id) {
        Item item = item(id);
        if (item == null) {
            return false;
        }
        var inv = player.getInventory();
        for (int i = 0; i < inv.getContainerSize(); i++) {
            ItemStack stack = inv.getItem(i);
            if (stack.is(item)) {
                stack.shrink(1);
                inv.setChanged();
                return true;
            }
        }
        return false;
    }
}
