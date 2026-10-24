package com.replecant.retrocosmos.client;

import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.flight.RocketEntity;
import net.minecraft.client.DeltaTracker;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.client.renderer.RenderPipelines;
import net.minecraft.resources.Identifier;
import net.neoforged.neoforge.client.gui.GuiLayer;

/** Top-centre flight telemetry panel shown while riding the rocket: phase, altitude, velocity, mission clock, propellant. */
public class FlightHudLayer implements GuiLayer {
    public static final Identifier ID = Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "flight_telemetry");
    private static final Identifier PANEL = Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "textures/gui/flight_hud.png");
    private static final Identifier BAR = Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "textures/gui/flight_hud_bar.png");
    private static final int W = 160, H = 40, BAR_W = 148, BAR_H = 6;

    private static final int INK = 0xFF24201F;
    private static final int GREEN = 0xFF5CFF8A;
    private static final int AMBER = 0xFFFFC14D;
    private static final int RED = 0xFFFF5A4D;

    @Override
    public void render(GuiGraphics g, DeltaTracker delta) {
        Minecraft mc = Minecraft.getInstance();
        LocalPlayer player = mc.player;
        if (player == null || mc.options.hideGui || !(player.getVehicle() instanceof RocketEntity rocket)) {
            return;
        }
        Font font = mc.font;
        int x = (g.guiWidth() - W) / 2;
        int y = 4;
        g.blit(RenderPipelines.GUI_TEXTURED, PANEL, x, y, 0, 0, W, H, W, H);

        int phase = rocket.phase();
        String phaseName = TextFit.str("gui.retrocosmos.flight.phase." + switch (phase) {
            case RocketEntity.PHASE_PAD -> "pad";
            case RocketEntity.PHASE_ASCENT -> "ascent";
            case RocketEntity.PHASE_ORBIT -> "orbit";
            default -> "descent";
        });
        String title = TextFit.fit(font, TextFit.str("gui.retrocosmos.flight.title", phaseName), W - 16);
        g.drawString(font, title, x + (W - font.width(title)) / 2, y + 1, INK, false);

        int altitude = (int) Math.max(0, rocket.getY() - rocket.padY());
        int velocity = (int) Math.round((rocket.getY() - rocket.yo) * 20);
        String clock;
        int ticks = rocket.phaseTicks();
        if (phase == RocketEntity.PHASE_PAD) {
            int left = Math.max(0, (RocketEntity.PAD_COUNTDOWN - ticks + 19) / 20);
            clock = String.format("T-%02d", left);
        } else {
            int s = ticks / 20;
            clock = String.format("T+%02d:%02d", s / 60, s % 60);
        }
        String alt = TextFit.str("gui.retrocosmos.flight.alt", altitude);
        String vel = TextFit.str("gui.retrocosmos.flight.vel", velocity);
        int half = (W - 16) / 2;
        g.drawString(font, TextFit.fit(font, alt, half), x + 8, y + 12, GREEN, false);
        g.drawString(font, TextFit.fit(font, vel, half), x + 8 + half, y + 12, GREEN, false);
        g.drawString(font, clock, x + 8, y + 21, phase == RocketEntity.PHASE_PAD ? AMBER : GREEN, false);

        float fuel = rocket.propellant();
        String fuelText = TextFit.str("gui.retrocosmos.flight.fuel", Math.round(fuel * 100));
        g.drawString(font, fuelText, TextFit.rightX(font, fuelText, x + W - 8), y + 21, fuel < 0.25F ? RED : AMBER, false);
        int filled = Math.round(BAR_W * fuel);
        if (filled > 0) {
            g.blit(RenderPipelines.GUI_TEXTURED, BAR, x + 6, y + 30, 0, 0, filled, BAR_H, BAR_W, BAR_H);
        }
    }
}
