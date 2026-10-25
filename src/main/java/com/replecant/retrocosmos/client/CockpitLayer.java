package com.replecant.retrocosmos.client;

import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.flight.RocketEntity;
import net.minecraft.client.DeltaTracker;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.renderer.RenderPipelines;
import net.minecraft.resources.Identifier;
import net.neoforged.neoforge.client.gui.GuiLayer;

/** First-person view from the Liberty I capsule: porthole, bulkhead and dashboard drawn over the world. */
public class CockpitLayer implements GuiLayer {
    public static final Identifier ID = Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "cockpit");
    private static final Identifier TEXTURE = Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "textures/gui/cockpit.png");
    private static final int TEX_W = 480, TEX_H = 270;

    @Override
    public void render(GuiGraphics g, DeltaTracker delta) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player == null || mc.options.hideGui || !mc.options.getCameraType().isFirstPerson()
                || !(mc.player.getVehicle() instanceof RocketEntity)) {
            return;
        }
        g.blit(RenderPipelines.GUI_TEXTURED, TEXTURE, 0, 0, 0, 0, g.guiWidth(), g.guiHeight(), TEX_W, TEX_H, TEX_W, TEX_H);
    }
}
