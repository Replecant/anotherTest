package com.replecant.retrocosmos.npc.client;

import net.minecraft.client.gui.Font;
import net.minecraft.network.chat.Component;

/** Small text helpers for the dialogue terminal and the objective HUD. */
final class TermText {
    private TermText() {}

    static String str(String key, Object... args) {
        return Component.translatable(key, args).getString();
    }

    /** {@code text} cut down (with an ellipsis) to fit {@code width} pixels. */
    static String fit(Font font, String text, int width) {
        if (font.width(text) <= width) {
            return text;
        }
        String dots = "...";
        return font.plainSubstrByWidth(text, Math.max(0, width - font.width(dots))) + dots;
    }
}
