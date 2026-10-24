package com.replecant.retrocosmos.block;

import net.minecraft.util.StringRepresentable;

/** Position of a launch pad block inside a pad slab, used to pick the right edge / corner texture. */
public enum PadPart implements StringRepresentable {
    SINGLE("single"),
    CENTER("center"),
    EDGE("edge"),
    CORNER("corner");

    private final String name;

    PadPart(String name) {
        this.name = name;
    }

    @Override
    public String getSerializedName() {
        return name;
    }
}
