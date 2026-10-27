package com.replecant.retrocosmos.npc.quest;

import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.builder.LiteralArgumentBuilder;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import java.util.Arrays;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.commands.arguments.EntityArgument;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.neoforged.neoforge.event.RegisterCommandsEvent;

/**
 * <pre>
 * /retrocosmos quest status [player]        - stage, objective, target (anyone, for themselves; level 2 for others)
 * /retrocosmos quest set &lt;stage&gt; [player]   - jump to a stage (level 2)
 * /retrocosmos quest reset [player]         - back to the start (level 2)
 * /retrocosmos quest worldreset             - forget the raid, the prisoner camp, the rescue, the boss (level 2)
 * </pre>
 * Registered as its own tree under /retrocosmos (brigadier merges it with the mod's other subcommands).
 */
public final class QuestCommands {
    private QuestCommands() {}

    public static void register(RegisterCommandsEvent event) {
        String[] stages = Arrays.stream(QuestStage.values()).map(QuestStage::key).toArray(String[]::new);
        LiteralArgumentBuilder<CommandSourceStack> quest = Commands.literal("quest")
                .then(Commands.literal("status")
                        .executes(ctx -> status(ctx, ctx.getSource().getPlayerOrException()))
                        .then(Commands.argument("player", EntityArgument.player())
                                .requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                                .executes(ctx -> status(ctx, EntityArgument.getPlayer(ctx, "player")))))
                .then(Commands.literal("set")
                        .requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                        .then(Commands.argument("stage", StringArgumentType.word())
                                .suggests((ctx, builder) -> SharedSuggestionProvider.suggest(stages, builder))
                                .executes(ctx -> set(ctx, ctx.getSource().getPlayerOrException()))
                                .then(Commands.argument("player", EntityArgument.player())
                                        .executes(ctx -> set(ctx, EntityArgument.getPlayer(ctx, "player"))))))
                .then(Commands.literal("reset")
                        .requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                        .executes(ctx -> reset(ctx, ctx.getSource().getPlayerOrException()))
                        .then(Commands.argument("player", EntityArgument.player())
                                .executes(ctx -> reset(ctx, EntityArgument.getPlayer(ctx, "player")))))
                .then(Commands.literal("worldreset")
                        .requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                        .executes(QuestCommands::worldReset));
        event.getDispatcher().register(Commands.literal("retrocosmos").then(quest));
    }

    private static int status(CommandContext<CommandSourceStack> ctx, ServerPlayer player) {
        QuestState state = Quest.state(player);
        Component target = state.target()
                .<Component>map(t -> Component.literal(t.dimension().identifier() + " " + t.pos().toShortString()))
                .orElse(Component.translatable("command.retrocosmos.quest.no_target"));
        ctx.getSource().sendSuccess(() -> Component.translatable("command.retrocosmos.quest.status", player.getName(),
                state.stage().key(), Component.translatable("quest.retrocosmos.objective." + state.stage().key()), target), false);
        return state.stage().ordinal();
    }

    private static int set(CommandContext<CommandSourceStack> ctx, ServerPlayer player) throws CommandSyntaxException {
        QuestStage stage = QuestStage.byKey(StringArgumentType.getString(ctx, "stage"));
        if (stage == null) {
            ctx.getSource().sendFailure(Component.translatable("command.retrocosmos.quest.bad_stage", StringArgumentType.getString(ctx, "stage")));
            return 0;
        }
        Quest.set(player, stage);
        ctx.getSource().sendSuccess(() -> Component.translatable("command.retrocosmos.quest.set", player.getName(), stage.key()), true);
        return 1;
    }

    private static int reset(CommandContext<CommandSourceStack> ctx, ServerPlayer player) {
        player.setData(QuestAttachments.RANGER_QUEST, QuestState.NONE);
        QuestDialogues.forget(player);
        ctx.getSource().sendSuccess(() -> Component.translatable("command.retrocosmos.quest.reset", player.getName()), true);
        return 1;
    }

    private static int worldReset(CommandContext<CommandSourceStack> ctx) {
        QuestWorld.get(ctx.getSource().getServer()).clear();
        ctx.getSource().sendSuccess(() -> Component.translatable("command.retrocosmos.quest.worldreset"), true);
        return 1;
    }
}
