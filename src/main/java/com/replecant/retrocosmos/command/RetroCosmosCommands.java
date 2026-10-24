package com.replecant.retrocosmos.command;

import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.builder.LiteralArgumentBuilder;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import com.replecant.retrocosmos.oxygen.OxygenSystem;
import com.replecant.retrocosmos.registry.ModItems;
import net.minecraft.ChatFormatting;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.arguments.EntityArgument;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.item.ItemStack;
import net.neoforged.neoforge.event.RegisterCommandsEvent;

/**
 * <pre>
 * /retrocosmos oxygen on|off [player]      - airless-environment simulation (test toggle, permission level 2)
 * /retrocosmos oxygen set &lt;seconds&gt; [player] - set the worn suit's oxygen
 * /retrocosmos hud on|off                  - suit telemetry HUD
 * </pre>
 */
public final class RetroCosmosCommands {
    private RetroCosmosCommands() {}

    public static void register(RegisterCommandsEvent event) {
        LiteralArgumentBuilder<CommandSourceStack> oxygen = Commands.literal("oxygen")
                .requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                .then(Commands.literal("on")
                        .executes(ctx -> setAirless(ctx, ctx.getSource().getPlayerOrException(), true))
                        .then(Commands.argument("player", EntityArgument.player())
                                .executes(ctx -> setAirless(ctx, EntityArgument.getPlayer(ctx, "player"), true))))
                .then(Commands.literal("off")
                        .executes(ctx -> setAirless(ctx, ctx.getSource().getPlayerOrException(), false))
                        .then(Commands.argument("player", EntityArgument.player())
                                .executes(ctx -> setAirless(ctx, EntityArgument.getPlayer(ctx, "player"), false))))
                .then(Commands.literal("set")
                        .then(Commands.argument("seconds", IntegerArgumentType.integer(0, OxygenSystem.MAX_OXYGEN / 20))
                                .executes(ctx -> setOxygen(ctx, ctx.getSource().getPlayerOrException(), IntegerArgumentType.getInteger(ctx, "seconds")))
                                .then(Commands.argument("player", EntityArgument.player())
                                        .executes(ctx -> setOxygen(ctx, EntityArgument.getPlayer(ctx, "player"), IntegerArgumentType.getInteger(ctx, "seconds"))))));

        LiteralArgumentBuilder<CommandSourceStack> hud = Commands.literal("hud")
                .then(Commands.literal("on").executes(ctx -> setHud(ctx, true)))
                .then(Commands.literal("off").executes(ctx -> setHud(ctx, false)));

        event.getDispatcher().register(Commands.literal("retrocosmos").then(oxygen).then(hud));
    }

    private static int setAirless(CommandContext<CommandSourceStack> ctx, ServerPlayer player, boolean airless) {
        OxygenSystem.setSettings(player, OxygenSystem.settings(player).withAirless(airless));
        player.displayClientMessage(Component.translatable(airless ? "message.retrocosmos.oxygen.airless_on" : "message.retrocosmos.oxygen.airless_off")
                .withStyle(airless ? ChatFormatting.RED : ChatFormatting.GREEN), false);
        ctx.getSource().sendSuccess(() -> Component.translatable("command.retrocosmos.oxygen.toggled", player.getName(),
                Component.translatable(airless ? "command.retrocosmos.on" : "command.retrocosmos.off")), true);
        return 1;
    }

    private static int setOxygen(CommandContext<CommandSourceStack> ctx, ServerPlayer player, int seconds) throws CommandSyntaxException {
        ItemStack chest = player.getItemBySlot(EquipmentSlot.CHEST);
        if (!chest.is(ModItems.SPACE_SUIT.get())) {
            ctx.getSource().sendFailure(Component.translatable("command.retrocosmos.oxygen.no_suit", player.getName()));
            return 0;
        }
        OxygenSystem.setOxygen(chest, seconds * 20);
        ctx.getSource().sendSuccess(() -> Component.translatable("command.retrocosmos.oxygen.set", player.getName(), seconds), true);
        return 1;
    }

    private static int setHud(CommandContext<CommandSourceStack> ctx, boolean shown) throws CommandSyntaxException {
        ServerPlayer player = ctx.getSource().getPlayerOrException();
        OxygenSystem.setSettings(player, OxygenSystem.settings(player).withHudHidden(!shown));
        ctx.getSource().sendSuccess(() -> Component.translatable("command.retrocosmos.hud",
                Component.translatable(shown ? "command.retrocosmos.on" : "command.retrocosmos.off")), false);
        return 1;
    }
}
