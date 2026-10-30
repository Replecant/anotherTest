package com.replecant.retrocosmos.npc.client;

import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.npc.quest.QuestAttachments;
import com.replecant.retrocosmos.npc.quest.QuestState;
import com.replecant.retrocosmos.oxygen.OxygenSystem;
import net.minecraft.client.DeltaTracker;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.core.GlobalPos;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;
import net.neoforged.neoforge.client.gui.GuiLayer;

/**
 * The current Space Rangers objective in the top-right corner: a small bakelite strip "OBJECTIVE: ..." and, when the
 * place is known, a direction arrow and the distance (or which world it is on). Hidden with /retrocosmos hud off,
 * like the suit telemetry.
 */
public class QuestHudLayer implements GuiLayer {
    public static final Identifier ID = Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "ranger_objective");
    private static final int PLATE = 0xC0141A1C, STRIPE = 0xFF2E9C94, CREAM = 0xFFF0E8D0, AMBER = 0xFFFFC14D;

    @Override
    public void render(GuiGraphics g, DeltaTracker delta) {
        Minecraft mc = Minecraft.getInstance();
        LocalPlayer player = mc.player;
        if (player == null || mc.options.hideGui || mc.screen != null || OxygenSystem.settings(player).hudHidden()) {
            return;
        }
        QuestState state = player.getData(QuestAttachments.RANGER_QUEST);
        if (!state.stage().active()) {
            return;
        }
        Font font = mc.font;
        int maxW = Math.min(200, g.guiWidth() / 3);
        String line = TermText.fit(font, TermText.str("gui.retrocosmos.quest.objective",
                Component.translatable("quest.retrocosmos.objective." + state.stage().key()).getString()), maxW);
        String where = null;
        float arrow = Float.NaN;
        if (state.target().isPresent()) {
            GlobalPos t = state.target().get();
            if (t.dimension() == player.level().dimension()) {
                double dx = t.pos().getX() + 0.5 - player.getX();
                double dz = t.pos().getZ() + 0.5 - player.getZ();
                int dist = (int) Math.round(Math.sqrt(dx * dx + dz * dz));
                where = dist < 12 ? TermText.str("gui.retrocosmos.quest.here") : TermText.str("gui.retrocosmos.quest.distance", dist);
                float yaw = (float) (Mth.atan2(dz, dx) * Mth.RAD_TO_DEG) - 90.0F;
                arrow = Mth.wrapDegrees(yaw - player.getYRot());
            } else {
                String path = t.dimension().identifier().getPath();
                String dim = path.contains("venus") ? "venus" : path.contains("orbit") || path.contains("station") ? "orbit" : "earth";
                where = TermText.str("gui.retrocosmos.quest.dim." + dim);
            }
        }
        int w = Math.max(font.width(line), where == null ? 0 : font.width(where) + 14) + 12;
        int x = g.guiWidth() - w - 6;
        int y = 6;
        int h = where == null ? 14 : 25;
        g.fill(x, y, x + w, y + h, PLATE);
        g.fill(x, y, x + 2, y + h, STRIPE);
        g.drawString(font, line, x + 7, y + 3, CREAM, false);
        if (where != null) {
            int ty = y + 14;
            if (!Float.isNaN(arrow)) {
                drawArrow(g, x + 11, ty + 4, arrow);
                g.drawString(font, where, x + 19, ty, AMBER, false);
            } else {
                g.drawString(font, where, x + 7, ty, AMBER, false);
            }
        }
    }

    /** A little amber arrowhead pointing {@code degrees} clockwise from straight ahead. */
    private static void drawArrow(GuiGraphics g, int cx, int cy, float degrees) {
        var pose = g.pose();
        pose.pushMatrix();
        pose.translate(cx, cy);
        pose.rotate(degrees * Mth.DEG_TO_RAD);
        g.fill(-1, -4, 1, 4, AMBER);
        g.fill(-2, -3, 2, -2, AMBER);
        g.fill(-3, -2, 3, -1, AMBER);
        g.fill(-4, -1, 4, 0, AMBER);
        pose.popMatrix();
    }
}
