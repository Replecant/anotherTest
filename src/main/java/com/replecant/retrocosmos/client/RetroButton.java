package com.replecant.retrocosmos.client;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.AbstractButton;
import net.minecraft.client.gui.narration.NarrationElementOutput;
import net.minecraft.client.input.InputWithModifiers;
import net.minecraft.network.chat.Component;

/** Chunky bakelite push button with a coloured cap, drawn with plain fills (no sprites needed). */
public class RetroButton extends AbstractButton {
    private final int color;
    private final Runnable action;

    public RetroButton(int x, int y, int width, int height, Component message, int color, Runnable action) {
        super(x, y, width, height, message);
        this.color = color;
        this.action = action;
    }

    @Override
    public void onPress(InputWithModifiers input) {
        action.run();
    }

    @Override
    protected void renderContents(GuiGraphics graphics, int mouseX, int mouseY, float partialTick) {
        int x0 = getX(), y0 = getY(), x1 = getRight(), y1 = getBottom();
        int cap = active ? color : 0xFF6E6A66;
        boolean hot = active && isHoveredOrFocused();
        graphics.fill(x0, y0, x1, y1, 0xFF1C1A1A);                       // bakelite bezel
        graphics.fill(x0 + 1, y0 + 1, x1 - 1, y1 - 1, hot ? lighten(cap, 40) : cap);
        graphics.fill(x0 + 1, y0 + 1, x1 - 1, y0 + 3, 0x66FFFFFF);        // top gloss
        graphics.fill(x0 + 1, y1 - 3, x1 - 1, y1 - 1, 0x55000000);        // bottom shade
        Font font = Minecraft.getInstance().font;
        String label = TextFit.fit(font, getMessage().getString(), getWidth() - 6);
        graphics.drawString(font, label, x0 + (getWidth() - font.width(label)) / 2, y0 + (getHeight() - 8) / 2,
                active ? 0xFFFFFFFF : 0xFFBBBBBB, true);
    }

    private static int lighten(int argb, int amount) {
        int r = Math.min(255, ((argb >> 16) & 0xFF) + amount);
        int g = Math.min(255, ((argb >> 8) & 0xFF) + amount);
        int b = Math.min(255, (argb & 0xFF) + amount);
        return (argb & 0xFF000000) | (r << 16) | (g << 8) | b;
    }

    @Override
    protected void updateWidgetNarration(NarrationElementOutput output) {
        defaultButtonNarrationText(output);
    }
}
