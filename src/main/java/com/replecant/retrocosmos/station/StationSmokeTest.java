package com.replecant.retrocosmos.station;

import com.google.gson.JsonElement;
import com.google.gson.JsonParser;
import com.mojang.serialization.JsonOps;
import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.block.LaunchPadBlock;
import com.replecant.retrocosmos.launch.LaunchSite;
import com.replecant.retrocosmos.registry.ModBlocks;
import java.io.Reader;
import net.minecraft.core.BlockPos;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.RegistryOps;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.dimension.LevelStem;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

/**
 * CI check (enabled with -Dretrocosmos.smokeStation=true on the game test server): builds Freedom Station and
 * verifies the docking pad, the service tower and the anchors, printing "STATION SMOKE OK" or "STATION SMOKE FAIL".
 */
public final class StationSmokeTest {
    private StationSmokeTest() {}

    /** Decodes every data/retrocosmos/dimension/*.json as a LevelStem; returns null when all are fine, else the error. */
    private static String validateDimension(MinecraftServer server) {
        var files = server.getResourceManager().listResources("dimension",
                id -> id.getNamespace().equals(RetroCosmos.MODID) && id.getPath().endsWith(".json"));
        if (files.isEmpty()) {
            return "no dimension definitions found";
        }
        for (var entry : files.entrySet()) {
            try (Reader reader = entry.getValue().openAsReader()) {
                JsonElement json = JsonParser.parseReader(reader);
                var result = LevelStem.CODEC.parse(RegistryOps.create(JsonOps.INSTANCE, server.registryAccess()), json);
                if (result.error().isPresent()) {
                    return entry.getKey() + ": " + result.error().get().message();
                }
                RetroCosmos.LOGGER.info("Retro Cosmos smoke: dimension {} decodes fine", entry.getKey());
            } catch (Exception e) {
                return entry.getKey() + ": " + e;
            }
        }
        return null;
    }

    public static void onServerStarted(ServerStartedEvent event) {
        if (!Boolean.getBoolean("retrocosmos.smokeStation")) {
            return;
        }
        // the game test server only creates its own levels, so decode our dimension definition with the game's
        // own codec to make sure a real world would accept it, and build the station in the test world instead
        ServerLevel level = FreedomStation.level(event.getServer());
        if (level == null) {
            String error = validateDimension(event.getServer());
            if (error != null) {
                RetroCosmos.LOGGER.error("STATION SMOKE FAIL: dimension definition invalid: {}", error);
                return;
            }
            RetroCosmos.LOGGER.info("Retro Cosmos smoke: dimension definition decodes fine, building the station in the test world");
            level = event.getServer().overworld();
        }
        FreedomStation.Layout layout = FreedomStation.ensureBuilt(level);
        if (layout == null) {
            RetroCosmos.LOGGER.error("STATION SMOKE FAIL: station could not be built");
            return;
        }
        int pad = level.getBlockState(layout.padCenter()).is(ModBlocks.LAUNCH_PAD.get()) ? LaunchPadBlock.countPad(level, layout.padCenter()) : 0;
        int tower = LaunchSite.towerHeight(level, layout.padCenter());
        int blocked = 0;
        for (int y = 1; y <= 11; y++) {
            if (!level.getBlockState(layout.padCenter().above(y)).isAir()) {
                blocked++;
            }
        }
        boolean arrivalOk = layout.isPressurized(layout.arrival().getX() + 0.5, layout.arrival().getY() + 1.5, layout.arrival().getZ() + 0.5);
        var problems = new java.util.ArrayList<>(FreedomStation.audit(level, layout));
        // the supply room must actually hold propellant for the trip home (checks the storage block entity data)
        int fuel = 0, lox = 0;
        for (BlockPos p : BlockPos.betweenClosed(layout.origin(), layout.origin().offset(layout.size()).offset(-1, -1, -1))) {
            if (level.getBlockEntity(p) instanceof net.minecraft.world.Container container) {
                for (int i = 0; i < container.getContainerSize(); i++) {
                    var stack = container.getItem(i);
                    if (stack.is(com.replecant.retrocosmos.registry.ModItems.ROCKET_FUEL_CANISTER.get())) {
                        fuel += stack.getCount();
                    } else if (stack.is(com.replecant.retrocosmos.registry.ModItems.LIQUID_OXYGEN_CANISTER.get())) {
                        lox += stack.getCount();
                    }
                }
            }
        }
        RetroCosmos.LOGGER.info("Retro Cosmos smoke: station supplies RP-1={} LOX={}", fuel, lox);
        if (fuel < 16 || lox < 16) {
            problems.add("not enough propellant stored: RP-1 " + fuel + ", LOX " + lox);
        }
        problems.stream().limit(200).forEach(problem -> RetroCosmos.LOGGER.warn("STATION AUDIT {}", problem));
        // the Venus expedition camp builder, exercised in the test world far from the station
        BlockPos camp = com.replecant.retrocosmos.venus.VenusLanding.buildAt(event.getServer().overworld(), 400, 400);
        int campPad = LaunchPadBlock.countPad(event.getServer().overworld(), camp.below());
        int campTower = LaunchSite.towerHeight(event.getServer().overworld(), camp.below());
        RetroCosmos.LOGGER.info("Retro Cosmos smoke: Venus camp pad={}/9 tower={}", campPad, campTower);
        if (campPad < LaunchSite.PAD_SIZE || campTower < 6) {
            problems.add("Venus camp incomplete: pad " + campPad + ", tower " + campTower);
        }
        boolean ok = pad >= LaunchSite.PAD_SIZE && tower >= 6 && blocked == 0 && arrivalOk && problems.isEmpty();
        RetroCosmos.LOGGER.info("STATION SMOKE {}: origin={} pad={}/9 tower={} blockedAbovePad={} arrivalPressurized={} compartments={} auditProblems={}",
                ok ? "OK" : "FAIL", layout.origin(), pad, tower, blocked, arrivalOk, layout.pressurized().size(), problems.size());
    }
}
