package com.replecant.retrocosmos.client;

import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.machine.ProcessingMenu;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.client.renderer.RenderPipelines;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.world.entity.player.Inventory;

/** Shared screen of the Fuel Refinery and the Air Liquefier: a cream & turquoise machine panel. */
public class ProcessingScreen extends AbstractContainerScreen<ProcessingMenu> {
    private static final Identifier TEXTURE = Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "textures/gui/machine.png");
    private static final int TEX_SIZE = 256;

    public ProcessingScreen(ProcessingMenu menu, Inventory inventory, Component title) {
        super(menu, inventory, title);
        imageWidth = 176;
        imageHeight = 166;
        inventoryLabelY = imageHeight - 94;
        titleLabelX = 28;
    }

    @Override
    protected void renderBg(GuiGraphics graphics, float partialTick, int mouseX, int mouseY) {
        int x = leftPos;
        int y = topPos;
        graphics.blit(RenderPipelines.GUI_TEXTURED, TEXTURE, x, y, 0, 0, imageWidth, imageHeight, TEX_SIZE, TEX_SIZE);
        // machine-specific emblem (right of the output slot)
        int v = menu.kind().guiVariant * 20;
        graphics.blit(RenderPipelines.GUI_TEXTURED, TEXTURE, x + 140, y + 30, 216, v, 24, 20, TEX_SIZE, TEX_SIZE);
        // burner flame, 14x14 at (176, 0), grows from the bottom
        if (menu.isLit()) {
            int h = menu.burnScaled(13);
            graphics.blit(RenderPipelines.GUI_TEXTURED, TEXTURE, x + 57, y + 36 + 13 - h, 176, 13 - h, 14, h + 1, TEX_SIZE, TEX_SIZE);
        }
        // progress pipe, 24x17 at (176, 14)
        int w = menu.progressScaled(24);
        if (w > 0) {
            graphics.blit(RenderPipelines.GUI_TEXTURED, TEXTURE, x + 79, y + 34, 176, 14, w, 17, TEX_SIZE, TEX_SIZE);
        }
    }
}
