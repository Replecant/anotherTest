package com.replecant.retrocosmos.npc;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;

/**
 * Where a crew member stands in a structure, read from its anchor JSON:
 * {@code "npcs": [{"role": "guard", "pos": [x, y, z], "yaw": 90, "home": [x, y, z]}]} (structure-local, home optional).
 */
public record NpcAnchor(String role, BlockPos pos, float yaw, BlockPos home) {
    public static List<NpcAnchor> read(JsonObject json, BlockPos origin) {
        List<NpcAnchor> anchors = new ArrayList<>();
        if (!json.has("npcs")) {
            return anchors;
        }
        for (JsonElement element : json.getAsJsonArray("npcs")) {
            JsonObject npc = element.getAsJsonObject();
            BlockPos pos = origin.offset(pos(npc.getAsJsonArray("pos")));
            BlockPos home = npc.has("home") ? origin.offset(pos(npc.getAsJsonArray("home"))) : pos;
            float yaw = npc.has("yaw") ? npc.get("yaw").getAsFloat() : 0.0F;
            anchors.add(new NpcAnchor(npc.get("role").getAsString(), pos, yaw, home));
        }
        return anchors;
    }

    private static BlockPos pos(JsonArray a) {
        return new BlockPos(a.get(0).getAsInt(), a.get(1).getAsInt(), a.get(2).getAsInt());
    }

    public static void spawnAll(ServerLevel level, List<NpcAnchor> anchors) {
        for (NpcAnchor anchor : anchors) {
            ExpeditionNpcs.spawn(level, anchor.pos(), anchor.yaw(), anchor.role(), anchor.home());
        }
    }
}
