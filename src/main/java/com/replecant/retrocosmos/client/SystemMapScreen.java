package com.replecant.retrocosmos.client;

import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.network.ReturnToEarthPayload;
import java.util.List;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.screens.PauseScreen;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.input.KeyEvent;
import net.minecraft.client.input.MouseButtonEvent;
import net.minecraft.client.renderer.RenderPipelines;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;
import net.neoforged.neoforge.client.network.ClientPacketDistributor;
import org.lwjgl.glfw.GLFW;

/**
 * The orbital chart the crew sees once the Liberty I reaches orbit: a Googie orrery of the solar system.
 * Every destination beyond Earth is locked for now; the only way out is "Return to Earth".
 */
public class SystemMapScreen extends Screen {
    private static final String DIR = "textures/gui/system_map/";
    private static final Identifier FRAME = tex("frame");
    private static final Identifier SELECTION = tex("selection");
    private static final Identifier LOCK = tex("lock");
    private static final Identifier BUTTON = tex("button");
    private static final Identifier MOON = tex("moon");
    private static final int W = 320, H = 200;
    private static final int MAP_X = 8, MAP_Y = 22, MAP_W = 208, MAP_H = 170;
    private static final int INFO_X = 222, INFO_Y = 22, INFO_W = 90;
    private static final int BTN_X = 227, BTN_Y = 170, BTN_W = 80, BTN_H = 16;

    private static final int NAVY = 0xFF2A3E76;
    private static final int PHOSPHOR = 0xFF5CFF8A;
    private static final int PHOSPHOR_DIM = 0xFF2E8A4A;
    private static final int AMBER = 0xFFFFC14D;
    private static final int RED = 0xFFFF5A4D;
    private static final int ORBIT = 0xFF283A6E;
    private static final int LABEL = 0xFFC8D0F0;
    private static final int BTN_TEXT = 0xFFFFF4E0;
    private static final int BTN_TEXT_OFF = 0xFF3A3838;

    /** A body on the chart. Radius in chart pixels, period in ticks per orbit, sprite size. */
    private record Body(String id, int radius, float period, float phase, int w, int h, boolean home) {
        Identifier texture() {
            return tex(id);
        }
    }

    private static final List<Body> BODIES = List.of(
            new Body("mercury", 20, 900, 0.3F, 10, 10, false),
            new Body("venus", 30, 1600, 2.1F, 12, 12, false),
            new Body("earth", 42, 2400, 4.0F, 14, 14, true),
            new Body("mars", 54, 3600, 5.2F, 12, 12, false),
            new Body("jupiter", 68, 6000, 1.0F, 24, 24, false),
            new Body("saturn", 80, 8400, 3.0F, 28, 16, false));

    private int left, top;
    private int ticks;
    private Body selected = BODIES.get(2);

    public SystemMapScreen() {
        super(Component.translatable("gui.retrocosmos.map.title"));
    }

    private static Identifier tex(String name) {
        return Identifier.fromNamespaceAndPath(RetroCosmos.MODID, DIR + name + ".png");
    }

    @Override
    protected void init() {
        left = (width - W) / 2;
        top = (height - H) / 2;
    }

    @Override
    public void tick() {
        ticks++;
    }

    @Override
    public boolean isPauseScreen() {
        return false;
    }

    @Override
    public boolean shouldCloseOnEsc() {
        return false;
    }

    @Override
    public boolean keyPressed(KeyEvent event) {
        if (event.key() == GLFW.GLFW_KEY_ESCAPE && minecraft != null) {
            // the map comes back by itself once the pause menu is closed
            minecraft.setScreen(new PauseScreen(true));
            return true;
        }
        return super.keyPressed(event);
    }

    private int[] position(Body body, float partialTick) {
        float angle = body.phase() + (ticks + partialTick) / body.period() * Mth.TWO_PI;
        int cx = left + MAP_X + MAP_W / 2;
        int cy = top + MAP_Y + MAP_H / 2;
        return new int[] {cx + Math.round(Mth.cos(angle) * body.radius()), cy + Math.round(Mth.sin(angle) * body.radius())};
    }

    @Override
    public void render(GuiGraphics g, int mouseX, int mouseY, float partialTick) {
        super.render(g, mouseX, mouseY, partialTick);
        g.blit(RenderPipelines.GUI_TEXTURED, FRAME, left, top, 0, 0, W, H, W, H);

        String title = TextFit.fit(font, getTitle().getString(), W - 24);
        g.drawString(font, title, left + (W - font.width(title)) / 2, top + 8, NAVY, false);

        int cx = left + MAP_X + MAP_W / 2;
        int cy = top + MAP_Y + MAP_H / 2;
        g.enableScissor(left + MAP_X, top + MAP_Y, left + MAP_X + MAP_W, top + MAP_Y + MAP_H);
        for (Body body : BODIES) {
            ring(g, cx, cy, body.radius(), body == selected ? 0xFF3C5498 : ORBIT);
        }
        g.blit(RenderPipelines.GUI_TEXTURED, tex("sun"), cx - 16, cy - 16, 0, 0, 32, 32, 32, 32);

        Body hovered = null;
        for (Body body : BODIES) {
            int[] p = position(body, partialTick);
            g.blit(RenderPipelines.GUI_TEXTURED, body.texture(), p[0] - body.w() / 2, p[1] - body.h() / 2, 0, 0,
                    body.w(), body.h(), body.w(), body.h());
            if (body.home()) {
                float moonAngle = (ticks + partialTick) / 200F * Mth.TWO_PI;
                int mx = p[0] + Math.round(Mth.cos(moonAngle) * 11) - 3;
                int my = p[1] + Math.round(Mth.sin(moonAngle) * 11) - 3;
                g.blit(RenderPipelines.GUI_TEXTURED, MOON, mx, my, 0, 0, 6, 6, 6, 6);
            } else {
                g.blit(RenderPipelines.GUI_TEXTURED, LOCK, p[0] + body.w() / 2 - 2, p[1] - body.h() / 2 - 6, 0, 0, 7, 9, 7, 9);
            }
            if (Math.abs(mouseX - p[0]) <= body.w() / 2 + 3 && Math.abs(mouseY - p[1]) <= body.h() / 2 + 3) {
                hovered = body;
            }
        }
        int[] sel = position(selected, partialTick);
        g.blit(RenderPipelines.GUI_TEXTURED, SELECTION, sel[0] - 12, sel[1] - 12, 0, 0, 24, 24, 24, 24);
        if (hovered != null) {
            int[] p = position(hovered, partialTick);
            String name = TextFit.str("gui.retrocosmos.map.body." + hovered.id());
            g.drawString(font, name, p[0] - font.width(name) / 2, p[1] + hovered.h() / 2 + 3, hovered == selected ? AMBER : LABEL, false);
        }
        g.disableScissor();

        renderInfo(g);
        renderButton(g, mouseX, mouseY);
    }

    private void ring(GuiGraphics g, int cx, int cy, int r, int color) {
        int steps = Math.max(24, r * 4);
        for (int i = 0; i < steps; i++) {
            // dotted ring: every other step
            if (i % 2 == 1) {
                continue;
            }
            float a = i / (float) steps * Mth.TWO_PI;
            int x = cx + Math.round(Mth.cos(a) * r);
            int y = cy + Math.round(Mth.sin(a) * r);
            g.fill(x, y, x + 1, y + 1, color);
        }
    }

    private void renderInfo(GuiGraphics g) {
        int x = left + INFO_X + 4;
        int y = top + INFO_Y + 5;
        int w = INFO_W - 8;
        String key = "gui.retrocosmos.map.body." + selected.id();
        g.drawString(font, TextFit.fit(font, TextFit.str(key), w), x, y, PHOSPHOR, false);
        y += 11;
        boolean home = selected.home();
        String status = TextFit.str(home ? "gui.retrocosmos.map.status.home" : "gui.retrocosmos.map.status.locked");
        g.drawString(font, TextFit.fit(font, status, w), x, y, home ? AMBER : RED, false);
        y += 14;
        for (int line = 0; line < 4; line++) {
            String text = TextFit.str(key + ".line" + line);
            g.drawString(font, TextFit.fit(font, text, w), x, y, PHOSPHOR_DIM, false);
            y += 10;
        }
        y += 4;
        if (!home) {
            for (net.minecraft.util.FormattedCharSequence seq : font.split(Component.translatable("gui.retrocosmos.map.locked_hint"), w)) {
                g.drawString(font, seq, x, y, PHOSPHOR_DIM, false);
                y += 10;
            }
        } else {
            for (net.minecraft.util.FormattedCharSequence seq : font.split(Component.translatable("gui.retrocosmos.map.home_hint"), w)) {
                g.drawString(font, seq, x, y, PHOSPHOR, false);
                y += 10;
            }
        }
    }

    private boolean overButton(double mouseX, double mouseY) {
        return mouseX >= left + BTN_X && mouseX < left + BTN_X + BTN_W && mouseY >= top + BTN_Y && mouseY < top + BTN_Y + BTN_H;
    }

    private void renderButton(GuiGraphics g, int mouseX, int mouseY) {
        boolean enabled = selected.home();
        int v = !enabled ? 32 : overButton(mouseX, mouseY) ? 16 : 0;
        g.blit(RenderPipelines.GUI_TEXTURED, BUTTON, left + BTN_X, top + BTN_Y, 0, v, BTN_W, BTN_H, BTN_W, 48);
        String label = TextFit.fit(font, TextFit.str("gui.retrocosmos.map.return"), BTN_W - 8);
        g.drawString(font, label, left + BTN_X + (BTN_W - font.width(label)) / 2, top + BTN_Y + 4,
                enabled ? BTN_TEXT : BTN_TEXT_OFF, false);
    }

    @Override
    public boolean mouseClicked(MouseButtonEvent event, boolean doubleClick) {
        double mx = event.x(), my = event.y();
        if (overButton(mx, my) && selected.home()) {
            ClientPacketDistributor.sendToServer(ReturnToEarthPayload.INSTANCE);
            if (minecraft != null) {
                minecraft.getSoundManager().play(net.minecraft.client.resources.sounds.SimpleSoundInstance.forUI(
                        net.minecraft.sounds.SoundEvents.UI_BUTTON_CLICK, 1.0F));
            }
            onClose();
            return true;
        }
        for (Body body : BODIES) {
            int[] p = position(body, 0);
            if (Math.abs(mx - p[0]) <= body.w() / 2 + 3 && Math.abs(my - p[1]) <= body.h() / 2 + 3) {
                selected = body;
                return true;
            }
        }
        return super.mouseClicked(event, doubleClick);
    }
}
