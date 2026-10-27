package com.replecant.retrocosmos.npc.client;

import com.replecant.retrocosmos.client.RetroButton;
import com.replecant.retrocosmos.npc.quest.Dialogue;
import com.replecant.retrocosmos.npc.quest.QuestNetwork;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.input.KeyEvent;
import net.minecraft.client.input.MouseButtonEvent;
import net.minecraft.client.resources.sounds.SimpleSoundInstance;
import net.minecraft.sounds.SoundEvents;
import net.neoforged.neoforge.client.network.ClientPacketDistributor;
import org.lwjgl.glfw.GLFW;

/**
 * The dialogue terminal: a cream bakelite radio-set with a green phosphor screen. A name plate (tinted per speaker)
 * with the role under it, the words typed out letter by letter with a soft teleprinter tick, a blinking cursor,
 * and up to three answer buttons once the text is through. A click (or Space) finishes the typing at once; Esc
 * leaves without answering.
 */
public class DialogueScreen extends Screen {
    private static final int W = 300, H = 178;
    private static final int BAKELITE = 0xFFE6DCC2, BAKELITE_DARK = 0xFFB9AD90, CHROME = 0xFFC9CED6;
    private static final int SCREEN_BG = 0xFF0B1712, PHOSPHOR = 0xFF8CFFB8, PHOSPHOR_DIM = 0xFF3E8E62;
    private static final int[] BUTTON_COLORS = {0xFF2E9C94, 0xFFC8402E, 0xFF5A6E8C};
    private static final int CHARS_PER_TICK = 2;

    private final int entityId;
    private final Dialogue dialogue;
    private final List<String> lines = new ArrayList<>();
    private final List<RetroButton> buttons = new ArrayList<>();
    private int total;
    private int shown;
    private int ticks;
    private int left, top;

    public DialogueScreen(int entityId, Dialogue dialogue) {
        super(dialogue.speaker());
        this.entityId = entityId;
        this.dialogue = dialogue;
    }

    @Override
    protected void init() {
        left = (width - W) / 2;
        top = (height - H) / 2;
        lines.clear();
        for (String paragraph : dialogue.text().getString().split("\n")) {
            if (paragraph.isEmpty()) {
                lines.add("");
                continue;
            }
            for (var line : font.getSplitter().splitLines(paragraph, W - 36, net.minecraft.network.chat.Style.EMPTY)) {
                lines.add(line.getString());
            }
        }
        total = lines.stream().mapToInt(String::length).sum();
        buttons.clear();
        int n = dialogue.options().size();
        int bw = n == 0 ? 0 : Math.min(132, (W - 28 - (n - 1) * 6) / n);
        int x = left + (W - (n * bw + (n - 1) * 6)) / 2;
        for (int i = 0; i < n; i++) {
            Dialogue.Option option = dialogue.options().get(i);
            RetroButton button = new RetroButton(x + i * (bw + 6), top + H - 26, bw, 18, option.label(),
                    BUTTON_COLORS[i % BUTTON_COLORS.length], () -> pick(option));
            button.active = shown >= total;
            buttons.add(addRenderableWidget(button));
        }
    }

    private void pick(Dialogue.Option option) {
        ClientPacketDistributor.sendToServer(new QuestNetwork.Choose(entityId, dialogue.id(), option.action()));
        onClose();
    }

    @Override
    public void tick() {
        ticks++;
        if (shown < total) {
            int before = shown;
            shown = Math.min(total, shown + CHARS_PER_TICK);
            if (minecraft != null && before / 6 != shown / 6) {
                minecraft.getSoundManager().play(SimpleSoundInstance.forUI(SoundEvents.NOTE_BLOCK_HAT.value(), 1.9F, 0.12F));
            }
            if (shown >= total) {
                buttons.forEach(b -> b.active = true);
            }
        }
    }

    private void finishTyping() {
        shown = total;
        buttons.forEach(b -> b.active = true);
    }

    @Override
    public boolean mouseClicked(MouseButtonEvent event, boolean doubleClick) {
        if (shown < total) {
            finishTyping();
            return true;
        }
        return super.mouseClicked(event, doubleClick);
    }

    @Override
    public boolean keyPressed(KeyEvent event) {
        if (shown < total && (event.key() == GLFW.GLFW_KEY_SPACE || event.key() == GLFW.GLFW_KEY_ENTER)) {
            finishTyping();
            return true;
        }
        if (shown >= total && event.key() >= GLFW.GLFW_KEY_1 && event.key() < GLFW.GLFW_KEY_1 + dialogue.options().size()) {
            pick(dialogue.options().get(event.key() - GLFW.GLFW_KEY_1));
            return true;
        }
        return super.keyPressed(event);
    }

    @Override
    public boolean isPauseScreen() {
        return false;
    }

    @Override
    public void renderBackground(GuiGraphics g, int mouseX, int mouseY, float partialTick) {
        super.renderBackground(g, mouseX, mouseY, partialTick);
        int x0 = left, y0 = top, x1 = left + W, y1 = top + H;
        // the radio-set cabinet
        g.fill(x0 - 2, y0 - 2, x1 + 2, y1 + 2, 0xFF1C1A1A);
        g.fill(x0, y0, x1, y1, BAKELITE);
        g.fill(x0, y1 - 6, x1, y1, BAKELITE_DARK);
        g.fill(x0 + 3, y0 + 3, x1 - 3, y0 + 4, 0x66FFFFFF);
        // speaker grille and two knobs down the right-hand side
        for (int gy = y0 + 40; gy < y0 + 100; gy += 4) {
            g.fill(x1 - 16, gy, x1 - 6, gy + 2, BAKELITE_DARK);
        }
        knob(g, x1 - 11, y0 + 116);
        knob(g, x1 - 11, y0 + 132);
        // name plate: chrome rim, the speaker's colour, the name in cream, the role in small turquoise caps
        int px0 = x0 + 8, px1 = x1 - 22;
        g.fill(px0 - 1, y0 + 6, px1 + 1, y0 + 30, CHROME);
        g.fill(px0, y0 + 7, px1, y0 + 29, dialogue.accent());
        g.fill(px0, y0 + 7, px1, y0 + 9, 0x44FFFFFF);
        String name = TermText.fit(font, dialogue.speaker().getString(), px1 - px0 - 10);
        g.drawString(font, name, px0 + 6, y0 + 9, 0xFFFFF4DC, true);
        String role = TermText.fit(font, dialogue.role().getString().toUpperCase(java.util.Locale.ROOT), px1 - px0 - 10);
        g.drawString(font, role, px0 + 6, y0 + 19, 0xFFBFF4EE, false);
        // the screen: phosphor green on near-black, with scan lines
        int sx0 = x0 + 8, sy0 = y0 + 34, sx1 = x1 - 22, sy1 = y1 - 32;
        g.fill(sx0 - 1, sy0 - 1, sx1 + 1, sy1 + 1, 0xFF262420);
        g.fill(sx0, sy0, sx1, sy1, SCREEN_BG);
        int maxLines = (sy1 - sy0 - 6) / 10;
        int budget = shown;
        int first = Math.max(0, visibleLines() - maxLines);  // long speeches scroll up as they are typed
        int y = sy0 + 4;
        int lastX = sx0 + 5, lastY = y;
        for (int i = 0; i < lines.size() && budget >= 0; i++) {
            String line = lines.get(i);
            String part = line.substring(0, Math.min(line.length(), budget));
            budget -= line.length();
            if (i < first) {
                continue;
            }
            g.drawString(font, part, sx0 + 5, y, PHOSPHOR, false);
            lastX = sx0 + 5 + font.width(part);
            lastY = y;
            y += 10;
            if (budget <= 0 && part.length() < line.length()) {
                break;
            }
        }
        if ((ticks / 8) % 2 == 0) {
            g.fill(lastX + 1, lastY, lastX + 6, lastY + 8, PHOSPHOR_DIM);  // the cursor
        }
        for (int sl = sy0; sl < sy1; sl += 2) {
            g.fill(sx0, sl, sx1, sl + 1, 0x22000000);
        }
        if (shown < total) {
            String skip = TermText.str("gui.retrocosmos.dialogue.skip");
            g.drawString(font, skip, x1 - 22 - font.width(skip), y1 - 18, BAKELITE_DARK - 0x303030, false);
        }
    }

    /** How many lines the typing has reached so far. */
    private int visibleLines() {
        int budget = shown, n = 0;
        for (String line : lines) {
            if (budget < 0) {
                break;
            }
            n++;
            budget -= Math.max(1, line.length());
        }
        return n;
    }

    private static void knob(GuiGraphics g, int cx, int cy) {
        g.fill(cx - 5, cy - 5, cx + 5, cy + 5, 0xFF1C1A1A);
        g.fill(cx - 4, cy - 4, cx + 4, cy + 4, 0xFFC8402E);
        g.fill(cx - 1, cy - 4, cx + 1, cy, 0xFFF0E8D0);
    }

    public static void open(int entityId, Dialogue dialogue) {
        net.minecraft.client.Minecraft.getInstance().setScreen(new DialogueScreen(entityId, dialogue));
    }
}
