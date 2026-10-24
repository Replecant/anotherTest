package com.replecant.retrocosmos.client;

import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.block.RocketBlock;
import com.replecant.retrocosmos.block.ServiceTowerBlock;
import com.replecant.retrocosmos.console.ConsoleBlockEntity;
import com.replecant.retrocosmos.console.ConsoleMenu;
import com.replecant.retrocosmos.launch.LaunchSite;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.client.renderer.RenderPipelines;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.world.entity.player.Inventory;

/**
 * Mission Control: a Googie cabinet with a green phosphor CRT. Everything on the tube is drawn with
 * fills and text so it stays crisp; the cabinet, bezel and lamps come from the generated texture.
 */
public class ConsoleScreen extends AbstractContainerScreen<ConsoleMenu> {
    private static final Identifier TEXTURE = Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "textures/gui/console.png");
    private static final int TEX_SIZE = 256;

    // CRT viewport inside the bezel (relative to leftPos / topPos)
    private static final int CRT_X = 14, CRT_Y = 16, CRT_W = 204, CRT_H = 132;

    private static final int PHOSPHOR = 0xFF5CFF8A;
    private static final int PHOSPHOR_DIM = 0xFF2E8A4A;
    private static final int AMBER = 0xFFFFC14D;
    private static final int RED = 0xFFFF5A4D;
    private static final int CRT_BG = 0xFF0A1A10;

    private int tick;

    public ConsoleScreen(ConsoleMenu menu, Inventory inventory, Component title) {
        super(menu, inventory, title);
        imageWidth = 232;
        imageHeight = 200;
    }

    @Override
    protected void init() {
        super.init();
        int bx = leftPos + 18;
        int by = topPos + 162;
        addRenderableWidget(new RetroButton(bx, by, 64, 22, Component.translatable("gui.retrocosmos.console.run_check"),
                0xFF3FB8B0, () -> press(ConsoleBlockEntity.BUTTON_CHECK)));
        addRenderableWidget(new RetroButton(bx + 70, by, 64, 22, Component.translatable("gui.retrocosmos.console.countdown"),
                0xFFD8342E, () -> press(ConsoleBlockEntity.BUTTON_COUNTDOWN)));
        addRenderableWidget(new RetroButton(bx + 140, by, 56, 22, Component.translatable("gui.retrocosmos.console.abort"),
                0xFFE8A23A, () -> press(ConsoleBlockEntity.BUTTON_ABORT)));
    }

    private void press(int button) {
        if (minecraft != null && minecraft.gameMode != null) {
            minecraft.gameMode.handleInventoryButtonClick(menu.containerId, button);
        }
    }

    @Override
    protected void containerTick() {
        super.containerTick();
        tick++;
    }

    @Override
    protected void renderLabels(GuiGraphics graphics, int mouseX, int mouseY) {
        // the CRT carries its own header; no vanilla labels
    }

    @Override
    protected void renderBg(GuiGraphics graphics, float partialTick, int mouseX, int mouseY) {
        int x = leftPos;
        int y = topPos;
        graphics.blit(RenderPipelines.GUI_TEXTURED, TEXTURE, x, y, 0, 0, imageWidth, imageHeight, TEX_SIZE, TEX_SIZE);
        drawCrt(graphics, x + CRT_X, y + CRT_Y);
    }

    private void drawCrt(GuiGraphics g, int x, int y) {
        boolean found = menu.get(ConsoleMenu.DATA_FOUND) == 1;
        int fuel = menu.get(ConsoleMenu.DATA_FUEL);
        int ox = menu.get(ConsoleMenu.DATA_OXIDIZER);
        int pad = menu.get(ConsoleMenu.DATA_PAD);
        int tower = menu.get(ConsoleMenu.DATA_TOWER);
        int suit = menu.get(ConsoleMenu.DATA_SUIT);
        int countdown = menu.get(ConsoleMenu.DATA_COUNTDOWN);
        int lastCheck = menu.get(ConsoleMenu.DATA_LAST_CHECK);
        boolean padOk = pad >= LaunchSite.PAD_SIZE;
        boolean towerOk = tower >= ServiceTowerBlock.MIN_HEIGHT;
        boolean fuelOk = fuel >= RocketBlock.MAX_FUEL;
        boolean oxOk = ox >= RocketBlock.MAX_FUEL;
        boolean suitOk = suit == LaunchSite.SUIT_FULL;
        boolean allGo = found && padOk && towerOk && fuelOk && oxOk && suitOk;
        boolean blink = (tick / 10) % 2 == 0;

        g.fill(x, y, x + CRT_W, y + CRT_H, CRT_BG);

        // header
        g.drawString(font, Component.translatable("gui.retrocosmos.console.header"), x + 6, y + 5, PHOSPHOR, false);
        String clock = String.format("%02d:%02d", (tick / 20 / 60) % 60, (tick / 20) % 60);
        g.drawString(font, "MET " + clock, x + CRT_W - 6 - font.width("MET " + clock), y + 5, PHOSPHOR_DIM, false);
        g.hLine(x + 4, x + CRT_W - 5, y + 15, PHOSPHOR_DIM);

        // readouts
        int ry = y + 20;
        String vehicle;
        if (found) {
            int dx = menu.get(ConsoleMenu.DATA_DX), dz = menu.get(ConsoleMenu.DATA_DZ);
            vehicle = Component.translatable("gui.retrocosmos.console.vehicle_on_pad", (int) Math.round(Math.sqrt(dx * dx + dz * dz))).getString();
        } else {
            vehicle = Component.translatable("gui.retrocosmos.console.vehicle_missing").getString();
        }
        row(g, x, ry, Component.translatable("gui.retrocosmos.console.vehicle").getString(), vehicle, found);
        row(g, x, ry + 11, Component.translatable("gui.retrocosmos.console.pad").getString(), pad + " / " + LaunchSite.PAD_SIZE, padOk);
        row(g, x, ry + 22, Component.translatable("gui.retrocosmos.console.tower").getString(), tower + " / " + ServiceTowerBlock.MIN_HEIGHT, towerOk);
        gauge(g, x, ry + 33, Component.translatable("gui.retrocosmos.console.fuel").getString(), fuel, RocketBlock.MAX_FUEL, fuelOk ? PHOSPHOR : AMBER);
        gauge(g, x, ry + 44, Component.translatable("gui.retrocosmos.console.oxidizer").getString(), ox, RocketBlock.MAX_FUEL, oxOk ? PHOSPHOR : 0xFF7FD4FF);

        // suit lamps
        g.drawString(font, Component.translatable("gui.retrocosmos.console.suit").getString(), x + 6, ry + 55, PHOSPHOR_DIM, false);
        String[] pieces = {"H", "C", "L", "B"};
        for (int i = 0; i < 4; i++) {
            boolean on = (suit & (1 << i)) != 0;
            int lx = x + 96 + i * 18;
            g.fill(lx, ry + 54, lx + 14, ry + 64, on ? PHOSPHOR : 0xFF3A1E1E);
            g.drawString(font, pieces[i], lx + 4, ry + 55, on ? CRT_BG : RED, false);
        }

        // GO / NO-GO board
        int by = y + 90;
        g.hLine(x + 4, x + CRT_W - 5, by - 3, PHOSPHOR_DIM);
        String[] labels = {"VEH", "PAD", "TWR", "RP1", "LOX", "SUIT"};
        boolean[] states = {found, padOk, towerOk, fuelOk, oxOk, suitOk};
        for (int i = 0; i < labels.length; i++) {
            int lx = x + 6 + i * 33;
            boolean ok = states[i];
            g.fill(lx, by, lx + 30, by + 18, ok ? 0xFF104020 : (blink ? 0xFF501818 : 0xFF301010));
            g.drawCenteredString(font, labels[i], lx + 15, by + 2, ok ? PHOSPHOR : RED);
            g.drawCenteredString(font, ok ? "GO" : "NO", lx + 15, by + 10, ok ? PHOSPHOR : RED);
        }

        // status line
        int sy = by + 24;
        if (countdown >= 0) {
            int seconds = (countdown + 19) / 20;
            String t = String.format("T-%02d", seconds);
            g.fill(x + 4, sy - 2, x + CRT_W - 4, sy + 14, blink ? 0xFF402008 : 0xFF2A1404);
            g.drawCenteredString(font, Component.translatable("gui.retrocosmos.console.counting", t).getString(), x + CRT_W / 2, sy + 3, AMBER);
        } else if (allGo) {
            g.drawCenteredString(font, Component.translatable("gui.retrocosmos.console.all_go").getString(), x + CRT_W / 2, sy + 3, PHOSPHOR);
        } else if (lastCheck == ConsoleBlockEntity.CHECK_NO_GO) {
            g.drawCenteredString(font, Component.translatable("gui.retrocosmos.console.no_go").getString(), x + CRT_W / 2, sy + 3, blink ? RED : AMBER);
        } else {
            g.drawCenteredString(font, Component.translatable("gui.retrocosmos.console.standby").getString(), x + CRT_W / 2, sy + 3, PHOSPHOR_DIM);
        }

        // scanlines and a soft vignette over everything on the tube
        for (int sl = y; sl < y + CRT_H; sl += 2) {
            g.fill(x, sl, x + CRT_W, sl + 1, 0x28000000);
        }
        g.fill(x, y, x + CRT_W, y + 2, 0x40000000);
        g.fill(x, y + CRT_H - 2, x + CRT_W, y + CRT_H, 0x40000000);
        g.fill(x, y, x + 2, y + CRT_H, 0x40000000);
        g.fill(x + CRT_W - 2, y, x + CRT_W, y + CRT_H, 0x40000000);
    }

    private void row(GuiGraphics g, int x, int y, String label, String value, boolean ok) {
        g.drawString(font, label, x + 6, y, PHOSPHOR_DIM, false);
        g.drawString(font, value, x + 96, y, ok ? PHOSPHOR : AMBER, false);
        g.drawString(font, ok ? "GO" : "NO-GO", x + CRT_W - 6 - font.width(ok ? "GO" : "NO-GO"), y, ok ? PHOSPHOR : RED, false);
    }

    private void gauge(GuiGraphics g, int x, int y, String label, int value, int max, int color) {
        g.drawString(font, label, x + 6, y, PHOSPHOR_DIM, false);
        int gx = x + 96, gw = 70;
        g.fill(gx, y + 1, gx + gw, y + 8, 0xFF143020);
        g.fill(gx + 1, y + 2, gx + 1 + (gw - 2) * value / max, y + 7, color);
        for (int i = 1; i < max; i++) {
            g.fill(gx + gw * i / max, y + 1, gx + gw * i / max + 1, y + 8, CRT_BG);
        }
        String txt = value + "/" + max;
        g.drawString(font, txt, x + CRT_W - 6 - font.width(txt), y, color, false);
    }
}
