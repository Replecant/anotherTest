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
        int left = x + 6;
        int right = x + CRT_W - 6;

        g.fill(x, y, x + CRT_W, y + CRT_H, CRT_BG);

        // header: title on the left, mission clock right-aligned; the clock loses its prefix, then the title shrinks
        String clock = String.format("MET %02d:%02d", (tick / 20 / 60) % 60, (tick / 20) % 60);
        String header = TextFit.str("gui.retrocosmos.console.header");
        if (font.width(header) + font.width(clock) + 8 > right - left) {
            clock = clock.substring(4);
        }
        int clockX = TextFit.rightX(font, clock, right);
        g.drawString(font, TextFit.fit(font, header, clockX - 6 - left), left, y + 5, PHOSPHOR, false);
        g.drawString(font, clock, clockX, y + 5, PHOSPHOR_DIM, false);
        g.hLine(x + 4, x + CRT_W - 5, y + 15, PHOSPHOR_DIM);

        // readout table: label column as wide as the widest label, GO / NO-GO column right-aligned
        String goText = TextFit.str("gui.retrocosmos.console.go");
        String noGoText = TextFit.str("gui.retrocosmos.console.no_go_short");
        int flagW = Math.max(font.width(goText), font.width(noGoText));
        int flagX = right - flagW;
        String[] labels = {
                TextFit.str("gui.retrocosmos.console.vehicle"), TextFit.str("gui.retrocosmos.console.pad"),
                TextFit.str("gui.retrocosmos.console.tower"), TextFit.str("gui.retrocosmos.console.fuel"),
                TextFit.str("gui.retrocosmos.console.oxidizer"), TextFit.str("gui.retrocosmos.console.suit")};
        int labelW = 0;
        for (String l : labels) {
            labelW = Math.max(labelW, font.width(l));
        }
        labelW = Math.min(labelW, 96);
        int valueX = left + labelW + 6;
        int valueW = flagX - 6 - valueX;

        int ry = y + 20;
        String vehicle = found
                ? TextFit.str("gui.retrocosmos.console.vehicle_on_pad", (int) Math.round(Math.sqrt(
                        (double) menu.get(ConsoleMenu.DATA_DX) * menu.get(ConsoleMenu.DATA_DX) + (double) menu.get(ConsoleMenu.DATA_DZ) * menu.get(ConsoleMenu.DATA_DZ))))
                : TextFit.str("gui.retrocosmos.console.vehicle_missing");
        row(g, left, labelW, valueX, valueW, flagX, ry, labels[0], vehicle, found, goText, noGoText);
        row(g, left, labelW, valueX, valueW, flagX, ry + 11, labels[1], pad + " / " + LaunchSite.PAD_SIZE, padOk, goText, noGoText);
        row(g, left, labelW, valueX, valueW, flagX, ry + 22, labels[2], tower + " / " + ServiceTowerBlock.MIN_HEIGHT, towerOk, goText, noGoText);
        gauge(g, left, labelW, valueX, right, ry + 33, labels[3], fuel, RocketBlock.MAX_FUEL, fuelOk ? PHOSPHOR : AMBER);
        gauge(g, left, labelW, valueX, right, ry + 44, labels[4], ox, RocketBlock.MAX_FUEL, oxOk ? PHOSPHOR : 0xFF7FD4FF);

        // suit lamps
        g.drawString(font, TextFit.fit(font, labels[5], labelW), left, ry + 55, PHOSPHOR_DIM, false);
        String[] pieces = {"H", "C", "L", "B"};
        int lampW = Math.min(18, Math.max(10, (right - valueX) / 4));
        for (int i = 0; i < 4; i++) {
            boolean on = (suit & (1 << i)) != 0;
            int lx = valueX + i * lampW;
            g.fill(lx, ry + 54, lx + lampW - 4, ry + 64, on ? PHOSPHOR : 0xFF3A1E1E);
            g.drawString(font, pieces[i], lx + (lampW - 4 - font.width(pieces[i])) / 2, ry + 55, on ? CRT_BG : RED, false);
        }

        // GO / NO-GO board: six equal cells across the tube
        int by = y + 90;
        g.hLine(x + 4, x + CRT_W - 5, by - 3, PHOSPHOR_DIM);
        String[] cells = {"VEH", "PAD", "TWR", "RP1", "LOX", "SUIT"};
        boolean[] states = {found, padOk, towerOk, fuelOk, oxOk, suitOk};
        int cellW = (CRT_W - 12) / cells.length;
        for (int i = 0; i < cells.length; i++) {
            int lx = left + i * cellW;
            boolean ok = states[i];
            g.fill(lx, by, lx + cellW - 3, by + 18, ok ? 0xFF104020 : (blink ? 0xFF501818 : 0xFF301010));
            int cx = lx + (cellW - 3) / 2;
            g.drawCenteredString(font, cells[i], cx, by + 2, ok ? PHOSPHOR : RED);
            g.drawCenteredString(font, ok ? "GO" : "NO", cx, by + 10, ok ? PHOSPHOR : RED);
        }

        // status line (always fitted to the tube width)
        int sy = by + 24;
        String status;
        int statusColor;
        if (countdown >= 0) {
            int seconds = (countdown + 19) / 20;
            g.fill(x + 4, sy - 2, x + CRT_W - 4, sy + 14, blink ? 0xFF402008 : 0xFF2A1404);
            status = TextFit.str("gui.retrocosmos.console.counting", String.format("T-%02d", seconds));
            statusColor = AMBER;
        } else if (allGo) {
            status = TextFit.str("gui.retrocosmos.console.all_go");
            statusColor = PHOSPHOR;
        } else if (lastCheck == ConsoleBlockEntity.CHECK_NO_GO) {
            status = TextFit.str("gui.retrocosmos.console.no_go");
            statusColor = blink ? RED : AMBER;
        } else {
            status = TextFit.str("gui.retrocosmos.console.standby");
            statusColor = PHOSPHOR_DIM;
        }
        status = TextFit.fit(font, status, CRT_W - 12);
        g.drawString(font, status, x + (CRT_W - font.width(status)) / 2, sy + 3, statusColor, false);

        // scanlines and a soft vignette over everything on the tube
        for (int sl = y; sl < y + CRT_H; sl += 2) {
            g.fill(x, sl, x + CRT_W, sl + 1, 0x28000000);
        }
        g.fill(x, y, x + CRT_W, y + 2, 0x40000000);
        g.fill(x, y + CRT_H - 2, x + CRT_W, y + CRT_H, 0x40000000);
        g.fill(x, y, x + 2, y + CRT_H, 0x40000000);
        g.fill(x + CRT_W - 2, y, x + CRT_W, y + CRT_H, 0x40000000);
    }

    private void row(GuiGraphics g, int left, int labelW, int valueX, int valueW, int flagX, int y,
                     String label, String value, boolean ok, String goText, String noGoText) {
        g.drawString(font, TextFit.fit(font, label, labelW), left, y, PHOSPHOR_DIM, false);
        g.drawString(font, TextFit.fit(font, value, valueW), valueX, y, ok ? PHOSPHOR : AMBER, false);
        String flag = ok ? goText : noGoText;
        int rightEdge = flagX + Math.max(font.width(goText), font.width(noGoText));
        g.drawString(font, flag, TextFit.rightX(font, flag, rightEdge), y, ok ? PHOSPHOR : RED, false);
    }

    private void gauge(GuiGraphics g, int left, int labelW, int valueX, int right, int y, String label, int value, int max, int color) {
        g.drawString(font, TextFit.fit(font, label, labelW), left, y, PHOSPHOR_DIM, false);
        String txt = value + "/" + max;
        int txtX = TextFit.rightX(font, txt, right);
        int gw = Math.max(20, Math.min(70, txtX - 6 - valueX));
        g.fill(valueX, y + 1, valueX + gw, y + 8, 0xFF143020);
        g.fill(valueX + 1, y + 2, valueX + 1 + (gw - 2) * value / max, y + 7, color);
        for (int i = 1; i < max; i++) {
            g.fill(valueX + gw * i / max, y + 1, valueX + gw * i / max + 1, y + 8, CRT_BG);
        }
        g.drawString(font, txt, txtX, y, color, false);
    }
}
