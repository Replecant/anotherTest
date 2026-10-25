package com.replecant.retrocosmos.command;

import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.builder.LiteralArgumentBuilder;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import com.replecant.retrocosmos.flight.HomePad;
import com.replecant.retrocosmos.flight.RocketEntity;
import com.replecant.retrocosmos.oxygen.OxygenSystem;
import com.replecant.retrocosmos.registry.ModAttachments;
import com.replecant.retrocosmos.registry.ModItems;
import com.replecant.retrocosmos.station.FreedomStation;
import com.replecant.retrocosmos.venus.Venus;
import com.replecant.retrocosmos.venus.VenusLanding;
import net.minecraft.ChatFormatting;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.arguments.EntityArgument;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.portal.TeleportTransition;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.event.RegisterCommandsEvent;

/**
 * <pre>
 * /retrocosmos oxygen on|off [player]      - airless-environment simulation (test toggle, permission level 2)
 * /retrocosmos oxygen set &lt;seconds&gt; [player] - set the worn suit's oxygen
 * /retrocosmos hud on|off                  - suit telemetry HUD
 * /retrocosmos tp station|earth|venus [player] - teleport to Freedom Station / to the player's home pad (level 2)
 * /retrocosmos station rebuild             - wipe and rebuild Freedom Station from the current design (level 2)
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

        LiteralArgumentBuilder<CommandSourceStack> tp = Commands.literal("tp")
                .requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS));
        for (String target : new String[] {RocketEntity.FREEDOM_STATION, "station", RocketEntity.EARTH, "home", RocketEntity.VENUS}) {
            tp.then(Commands.literal(target)
                    .executes(ctx -> teleport(ctx, ctx.getSource().getPlayerOrException(), target))
                    .then(Commands.argument("player", EntityArgument.player())
                            .executes(ctx -> teleport(ctx, EntityArgument.getPlayer(ctx, "player"), target))));
        }

        LiteralArgumentBuilder<CommandSourceStack> station = Commands.literal("station")
                .requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                .then(Commands.literal("rebuild").executes(RetroCosmosCommands::rebuildStation));

        event.getDispatcher().register(Commands.literal("retrocosmos").then(oxygen).then(hud).then(tp).then(station));
    }

    private static int setAirless(CommandContext<CommandSourceStack> ctx, ServerPlayer player, boolean airless) {
        OxygenSystem.setSettings(player, OxygenSystem.settings(player).withAirless(airless));
        player.displayClientMessage(Component.translatable(airless ? "message.retrocosmos.oxygen.airless_on" : "message.retrocosmos.oxygen.airless_off")
                .withStyle(airless ? ChatFormatting.RED : ChatFormatting.GREEN), false);
        if (airless && player.isCreative()) {
            player.displayClientMessage(Component.translatable("message.retrocosmos.oxygen.creative").withStyle(ChatFormatting.YELLOW), false);
        }
        ctx.getSource().sendSuccess(() -> Component.translatable("command.retrocosmos.oxygen.toggled", player.getName(),
                Component.translatable(airless ? "command.retrocosmos.on" : "command.retrocosmos.off")), true);
        return 1;
    }

    private static int teleport(CommandContext<CommandSourceStack> ctx, ServerPlayer player, String target) {
        MinecraftServer server = ctx.getSource().getServer();
        boolean toStation = target.equals(RocketEntity.FREEDOM_STATION) || target.equals("station");
        if (target.equals(RocketEntity.VENUS)) {
            ServerLevel venus = server.getLevel(Venus.DIMENSION);
            if (venus == null) {
                ctx.getSource().sendFailure(Component.translatable("command.retrocosmos.tp.no_venus"));
                return 0;
            }
            if (player.isPassenger()) {
                player.stopRiding();
            }
            BlockPos camp = VenusLanding.ensureCamp(venus);
            player.teleport(new TeleportTransition(venus, Vec3.atBottomCenterOf(camp.offset(0, 0, 2)), Vec3.ZERO,
                    player.getYRot(), player.getXRot(), TeleportTransition.DO_NOTHING));
            ctx.getSource().sendSuccess(() -> Component.translatable("command.retrocosmos.tp.venus", player.getName()), true);
            return 1;
        }
        if (player.isPassenger()) {
            player.stopRiding();
        }
        ServerLevel level;
        Vec3 pos;
        if (toStation) {
            level = FreedomStation.level(server);
            FreedomStation.Layout layout = level == null ? null : FreedomStation.ensureBuilt(level);
            if (layout == null) {
                ctx.getSource().sendFailure(Component.translatable("command.retrocosmos.tp.no_station"));
                return 0;
            }
            pos = Vec3.atBottomCenterOf(layout.arrival().above());
        } else {
            level = server.overworld();
            HomePad home = player.getData(ModAttachments.HOME_PAD);
            BlockPos base = home.known() ? home.pos().offset(2, 0, 0)
                    : level.getHeightmapPos(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, BlockPos.ZERO);
            pos = Vec3.atBottomCenterOf(base);
        }
        player.teleport(new TeleportTransition(level, pos, Vec3.ZERO, player.getYRot(), player.getXRot(), TeleportTransition.DO_NOTHING));
        ctx.getSource().sendSuccess(() -> Component.translatable(toStation ? "command.retrocosmos.tp.station" : "command.retrocosmos.tp.home",
                player.getName()), true);
        return 1;
    }

    private static int rebuildStation(CommandContext<CommandSourceStack> ctx) {
        ServerLevel level = FreedomStation.level(ctx.getSource().getServer());
        FreedomStation.Layout layout = level == null ? null : FreedomStation.rebuild(level);
        if (layout == null) {
            ctx.getSource().sendFailure(Component.translatable("command.retrocosmos.tp.no_station"));
            return 0;
        }
        ctx.getSource().sendSuccess(() -> Component.translatable("command.retrocosmos.station.rebuilt"), true);
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
