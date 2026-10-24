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
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.item.ItemStack;
import net.neoforged.neoforge.client.gui.GuiLayer;

/**
 * "Suit telemetry" panel: a bakelite plate in the top-left corner with the oxygen gauge, time left,
 * suit integrity lamps and some flavour readouts. Shown while the suit is worn or the airless simulation
 * is on; hidden with /retrocosmos hud off.
 */
public class SuitHudLayer implements GuiLayer {
    public static final Identifier ID = Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "suit_telemetry");
    private static final Identifier TEXTURE = Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "textures/gui/hud.png");
    private static final int TEX = 128;

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
        ItemStack chest = player.getItemBySlot(EquipmentSlot.CHEST);
        boolean hasChest = chest.is(ModItems.SPACE_SUIT.get());
        if (settings.hudHidden() || (!settings.airless() && !hasChest)) {
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
        boolean warning = settings.airless() && (frac <= 0.2F || suit != LaunchSite.SUIT_FULL);

        int x = 6;
        int y = 6;
        g.blit(RenderPipelines.GUI_TEXTURED, TEXTURE, x, y, 0, 0, 120, 46, TEX, TEX);
        g.drawString(font, Component.translatable("gui.retrocosmos.hud.title"), x + 11, y + 3, INK, false);
        String env = Component.translatable(settings.airless() ? "gui.retrocosmos.hud.vacuum" : "gui.retrocosmos.hud.atmosphere").getString();
        g.drawString(font, env, x + 108 - font.width(env), y + 3, settings.airless() ? 0xFFC82828 : 0xFF287870, false);

        // oxygen gauge
        int gx = x + 10;
        int gy = y + 14;
        g.blit(RenderPipelines.GUI_TEXTURED, TEXTURE, gx, gy, 0, 48, 100, 10, TEX, TEX);
        int fill = Math.round(97 * frac);
        int barColor = (warning && blink) ? 0xFFFFFFFF : color;
        if (fill > 0) {
            g.fill(gx + 1, gy + 4, gx + 1 + fill, gy + 9, barColor);
        }

        // readouts
        String o2Text = String.format("O2 %d%% %d:%02d", Math.round(frac * 100), seconds / 60, seconds % 60);
        g.drawString(font, o2Text, x + 10, y + 26, hasChest ? color : RED, false);
        double wobble = Math.sin(ticks / 25.0);
        String flavour = settings.airless()
                ? String.format("P %.1fpsi T%+dC", suit == LaunchSite.SUIT_FULL ? 3.5 + wobble * 0.1 : 0.0, (int) (21 + wobble * 2))
                : String.format("P 14.7psi T%+dC", (int) (21 + wobble * 2));
        g.drawString(font, flavour, x + 10, y + 36, CREAM, false);

        // suit integrity lamps H C L B
        String[] pieces = {"H", "C", "L", "B"};
        for (int i = 0; i < 4; i++) {
            boolean on = (suit & (1 << i)) != 0;
            int lx = x + 86 + i * 7;
            g.fill(lx, y + 26, lx + 6, y + 34, on ? TEAL : (blink ? 0xFF7A2424 : 0xFF4A1C1C));
            g.drawString(font, pieces[i], lx + 1, y + 26, on ? INK : RED, false);
        }
        // warning lamp (off / amber / red)
        int lamp = !hasChest || frac <= 0.1F ? 2 : frac <= 0.2F ? 1 : 0;
        if (lamp > 0 && !blink) {
            lamp = 0;
        }
        g.blit(RenderPipelines.GUI_TEXTURED, TEXTURE, x + 108, y + 36, 104 + lamp * 8, 48, 8, 8, TEX, TEX);
        if (warning && blink) {
            String alert = Component.translatable(suit != LaunchSite.SUIT_FULL ? "gui.retrocosmos.hud.suit_breach" : "gui.retrocosmos.hud.o2_low").getString();
            g.drawString(font, alert, x + 4, y + 48, RED, true);
        }
    }
}
