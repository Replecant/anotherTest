package com.replecant.retrocosmos.client;

import net.minecraft.client.gui.Font;
import net.minecraft.network.chat.Component;

/** Small layout helpers so that translated strings never overlap: measure, right-align, truncate. */
final class TextFit {
    private TextFit() {}

    static String str(String key, Object... args) {
        return Component.translatable(key, args).getString();
    }

    /** Truncates {@code text} (with a trailing "…") so that it fits into {@code maxWidth} pixels. */
    static String fit(Font font, String text, int maxWidth) {
        if (maxWidth <= 0) {
            return "";
        }
        if (font.width(text) <= maxWidth) {
            return text;
        }
        int ellipsis = font.width("…");
        String cut = font.plainSubstrByWidth(text, Math.max(0, maxWidth - ellipsis));
        return cut.isEmpty() ? "" : cut.strip() + "…";
    }

    /** X at which {@code text} must start to end at {@code right}. */
    static int rightX(Font font, String text, int right) {
        return right - font.width(text);
    }
}
