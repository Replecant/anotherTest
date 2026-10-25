package com.replecant.retrocosmos.client;

import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.launch.LaunchSite;
import com.replecant.retrocosmos.oxygen.OxygenSystem;
import com.replecant.retrocosmos.oxygen.SuitSettings;
import com.replecant.retrocosmos.registry.ModItems;
import net.minecraft.client.DeltaTracker;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.client.renderer.RenderPipelines;
import net.minecraft.resources.Identifier;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.item.ItemStack;
import net.neoforged.neoforge.client.gui.GuiLayer;

/**
 * "Suit telemetry" panel: a bakelite plate in the top-left corner with the oxygen gauge, time left,
 * suit integrity lamps and some flavour readouts. Shown while the suit is worn or the airless simulation
 * is on; hidden with /retrocosmos hud off. Every string is measured so nothing overlaps in any language.
 */
public class SuitHudLayer implements GuiLayer {
    public static final Identifier ID = Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "suit_telemetry");
    private static final Identifier TEXTURE = Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "textures/gui/hud.png");
    private static final int TEX_W = 160, TEX_H = 64;
    // sprite sheet layout (see gui_hud() in tools/gen_resources.py)
    private static final int PANEL_W = 140, PANEL_H = 46, GAUGE_W = 100, GAUGE_H = 10;
    private static final int PAD = 10;                 // inner left margin
    private static final int INNER_RIGHT = PANEL_W - 8; // inner right edge

    private static final int INK = 0xFF24201F;
    private static final int CREAM = 0xFFF0E8D0;
    private static final int GREEN = 0xFF5CFF8A;
    private static final int AMBER = 0xFFFFC14D;
    private static final int RED = 0xFFFF5A4D;
    private static final int TEAL = 0xFF48BEB6;

    @Override
    public void render(GuiGraphics g, DeltaTracker delta) {
        Minecraft mc = Minecraft.getInstance();
        LocalPlayer player = mc.player;
        if (player == null || mc.options.hideGui) {
            return;
        }
        SuitSettings settings = OxygenSystem.settings(player);
        boolean airless = OxygenSystem.isAirless(player);
        ItemStack chest = player.getItemBySlot(EquipmentSlot.CHEST);
        boolean hasChest = chest.is(ModItems.SPACE_SUIT.get());
        if (settings.hudHidden() || (!airless && !hasChest)) {
            return;
        }
        Font font = mc.font;
        int ticks = mc.gui.getGuiTicks();
        boolean blink = (ticks / 8) % 2 == 0;
        int suit = LaunchSite.suitBits(player);
        int o2 = hasChest ? OxygenSystem.oxygen(chest) : 0;
        float frac = o2 / (float) OxygenSystem.MAX_OXYGEN;
        int seconds = o2 / 20;
        int color = frac > 0.2F ? GREEN : frac > 0.1F ? AMBER : RED;
        boolean creative = player.isCreative();
        boolean warning = airless && !creative && (frac <= 0.2F || suit != LaunchSite.SUIT_FULL);

        int x = 6;
        int y = 6;
        g.blit(RenderPipelines.GUI_TEXTURED, TEXTURE, x, y, 0, 0, PANEL_W, PANEL_H, TEX_W, TEX_H);

        // label strip: title left, environment tag right-aligned, title truncated to the space left
        String env = TextFit.str(airless ? "gui.retrocosmos.hud.vacuum" : "gui.retrocosmos.hud.atmosphere");
        int envX = TextFit.rightX(font, env, x + PANEL_W - 11);
        g.drawString(font, env, envX, y + 3, airless ? 0xFFC82828 : 0xFF287870, false);
        g.drawString(font, TextFit.fit(font, TextFit.str("gui.retrocosmos.hud.title"), envX - 4 - (x + 11)), x + 11, y + 3, INK, false);

        // oxygen gauge
        int gx = x + PAD;
        int gy = y + 14;
        g.blit(RenderPipelines.GUI_TEXTURED, TEXTURE, gx, gy, 0, 48, GAUGE_W, GAUGE_H, TEX_W, TEX_H);
        int fill = Math.round((GAUGE_W - 3) * frac);
        if (fill > 0) {
            g.fill(gx + 1, gy + 4, gx + 1 + fill, gy + 9, (warning && blink) ? 0xFFFFFFFF : color);
        }
        String pct = Math.round(frac * 100) + "%";
        g.drawString(font, pct, TextFit.rightX(font, pct, x + INNER_RIGHT), gy + 1, color, false);

        // suit integrity lamps H C L B, right-aligned on the O2 line
        String[] pieces = {"H", "C", "L", "B"};
        int lampW = 10;
        int lampsX = x + INNER_RIGHT - 4 * lampW + 2;
        for (int i = 0; i < 4; i++) {
            boolean on = (suit & (1 << i)) != 0;
            int lx = lampsX + i * lampW;
            g.fill(lx, y + 25, lx + 8, y + 35, on ? TEAL : (blink ? 0xFF7A2424 : 0xFF4A1C1C));
            // font.width() includes the 1px trailing spacing, so centre on the visible glyph width
            g.drawString(font, pieces[i], lx + (8 - (font.width(pieces[i]) - 1) + 1) / 2, y + 26, on ? INK : RED, false);
        }
        String o2Text = TextFit.str("gui.retrocosmos.hud.o2", String.format("%d:%02d", seconds / 60, seconds % 60));
        g.drawString(font, TextFit.fit(font, o2Text, lampsX - 4 - gx), gx, y + 26, hasChest ? color : RED, false);

        // flavour readouts, warning lamp right-aligned
        int lamp = !hasChest || frac <= 0.1F ? 2 : frac <= 0.2F ? 1 : 0;
        if (lamp > 0 && !blink) {
            lamp = 0;
        }
        int lampX = x + INNER_RIGHT - 8;
        g.blit(RenderPipelines.GUI_TEXTURED, TEXTURE, lampX, y + 36, 104 + lamp * 8, 48, 8, 8, TEX_W, TEX_H);
        double wobble = Math.sin(ticks / 25.0);
        String flavour = airless
                ? String.format("P %.1f psi  T %+d°C", suit == LaunchSite.SUIT_FULL ? 3.5 + wobble * 0.1 : 0.0, (int) (21 + wobble * 2))
                : String.format("P 14.7 psi  T %+d°C", (int) (21 + wobble * 2));
        g.drawString(font, TextFit.fit(font, flavour, lampX - 4 - gx), gx, y + 36, CREAM, false);

        // alerts under the panel
        if (airless && creative) {
            g.drawString(font, TextFit.str("gui.retrocosmos.hud.creative"), x + 2, y + PANEL_H + 3, AMBER, true);
        } else if (warning && blink) {
            String alert = TextFit.str(suit != LaunchSite.SUIT_FULL ? "gui.retrocosmos.hud.suit_breach" : "gui.retrocosmos.hud.o2_low");
            g.drawString(font, alert, x + 2, y + PANEL_H + 3, RED, true);
        }
    }
}
